"""SteelPlan · Programación automática de la cartera (v3.1).

- `POST /api/programacion/proponer`: calcula un plan para todos los proyectos en curso (dss/programador.py) y lo
  guarda como PROPUESTO. Nada cambia en la planta hasta que alguien lo aprueba.
- `POST /api/programacion/{id}/aprobar`: el plan pasa a APROBADO (el anterior queda REEMPLAZADO); opcionalmente
  aplica los movimientos de preventivos aceptados.
- `POST /api/programacion/simular`: "¿cabe este proyecto nuevo en julio?"; no guarda nada.
- Readaptación: una huella del estado de la planta (proyectos, tareo, piezas, paradas, preventivos) dice si el plan
  quedó desactualizado; un hilo en segundo plano propone uno nuevo solo cuando cambia, y cada noche.

Las rutas se registran desde server.py con `registrar(...)`; los datos de cada proyecto (avance, modelo) los da
`cartera(con)` del servidor para no duplicar lógica.
"""
import hashlib
import json
import threading
import time
from datetime import date, datetime, timedelta

import numpy as np
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from dss.c3_montecarlo import Proyecto
from dss.crp_engine import WEEKMASK
from dss.mantenimiento import dias_de_frecuencia, proximo_vencimiento
from dss.programador import REGLAS, ProyectoPlan, diferencias, meta_a_fecha, proponer

APRUEBAN = ('jefe_taller',)
PROPONEN = ('jefe_taller', 'cotizador', 'mantenimiento')
R_PLAN = 200
_lock = threading.Lock()


class PropuestaIn(BaseModel):
    regla: str = 'penalidad'
    motivo: str = 'manual'


class AprobarIn(BaseModel):
    mover_preventivos: list[int] = []        # ids de órdenes cuya fecha propuesta se acepta


class SimularIn(BaseModel):
    tipo: str
    ton: float = Field(gt=0, le=2000)
    inicio: str
    meta: str | None = None                  # 'AAAA-MM' (mes), 'AAAA-MM-DD' o vacío (lo antes posible)
    presupuesto: float = 100000
    pct_planchas: float = 0.2
    piezas_por_t: float = 8.0
    m2_pint_t: float = 14.0
    montaje: bool = False
    alpha: float = Field(0.8, ge=0.5, le=0.99)
    regla: str = 'penalidad'


def preventivos_futuros(p, maquinas, horizonte=300):
    """Órdenes preventivas abiertas + las próximas repeticiones de cada plan dentro del horizonte (capacidad que no estará)."""
    hoy = str(date.today())
    out = [dict(r) for r in p.execute('''SELECT o.id, m.nombre maquina, o.programada_para, COALESCE(o.duracion_h, 1) duracion_h, o.titulo, o.plan_id
                                         FROM orden_mantenimiento o JOIN maquina m ON m.id=o.maquina_id
                                         WHERE o.estado IN ('PENDIENTE','EN_CURSO') AND o.programada_para IS NOT NULL''')]
    con_orden = {x['plan_id'] for x in out if x['plan_id']}
    for pl in p.execute('''SELECT pm.*, m.nombre maquina FROM plan_mantenimiento pm JOIN maquina m ON m.id=pm.maquina_id
                           WHERE pm.activo=1 AND m.activa=1''').fetchall():
        pl = dict(pl)
        f = dias_de_frecuencia(pl)
        if not f:
            continue
        ult = p.execute("SELECT MAX(COALESCE(fin, cerrado_en)) FROM orden_mantenimiento WHERE plan_id=? AND estado='CERRADA'", (pl['id'],)).fetchone()[0]
        vence, _ = proximo_vencimiento(pl, ult[:10] if ult else None, hoy)
        k = 1 if pl['id'] in con_orden else 0               # la primera ya está como orden abierta
        d = np.datetime64(vence, 'D')
        limite = np.busday_offset(np.datetime64(hoy, 'D'), horizonte, roll='forward', weekmask=WEEKMASK)
        while True:
            fecha = np.busday_offset(d, k * f, roll='forward', weekmask=WEEKMASK)
            if fecha > limite:
                break
            if not (k == 0 and pl['id'] in con_orden):
                out.append(dict(id=None, maquina=pl['maquina'], programada_para=str(fecha), duracion_h=pl['duracion_h'], titulo=pl['tarea'], plan_id=pl['id']))
            k += 1
    # indisponibilidades conocidas: paradas que siguen abiertas y correctivas en curso (la máquina no está hoy)
    ahora = datetime.now().strftime('%Y-%m-%d %H:%M')
    for pa in p.execute('SELECT id, maquina, inicio, fin, causa FROM parada WHERE fin > ? AND inicio <= ?', (ahora, ahora)).fetchall():
        d = np.datetime64(hoy, 'D')
        while str(d) <= pa['fin'][:10]:
            if np.is_busday(d, weekmask=WEEKMASK):
                out.append(dict(id=None, maquina=pa['maquina'], programada_para=str(d), duracion_h=8.0, titulo=f'Parada en curso: {pa["causa"]}', plan_id=None))
            d += np.timedelta64(1, 'D')
    for o in p.execute('''SELECT o.id, m.nombre maquina, o.titulo FROM orden_mantenimiento o JOIN maquina m ON m.id=o.maquina_id
                          WHERE o.estado='EN_CURSO' AND o.tipo='CORRECTIVO' AND o.parada_id IS NULL''').fetchall():
        out.append(dict(id=None, maquina=o['maquina'], programada_para=hoy, duracion_h=8.0, titulo=f'Correctiva en curso OM-{o["id"]}', plan_id=None))
    return [x for x in out if x['maquina'] in maquinas]


def huella(p):
    """Resumen del estado que afecta al plan; si cambia, el plan aprobado quedó desactualizado."""
    partes = dict(
        proyectos=[tuple(r) for r in p.execute("SELECT id, estado, fecha_comprometida, inicio, ton FROM proyecto_activo WHERE estado IN ('EN_CURSO','PAUSADO') ORDER BY id")],
        tareo=tuple(p.execute('SELECT COUNT(*), ROUND(COALESCE(SUM(hh),0),1) FROM tareo').fetchone()),
        piezas=tuple(p.execute('SELECT COUNT(*), COUNT(f_habilitado)+COUNT(f_armado)+COUNT(f_soldeo)+COUNT(f_liberacion)+COUNT(f_despacho) FROM pieza').fetchone()),
        paradas=tuple(p.execute('SELECT COUNT(*), COALESCE(MAX(id),0) FROM parada').fetchone()),
        preventivos=[tuple(r) for r in p.execute("SELECT id, programada_para, estado FROM orden_mantenimiento WHERE estado IN ('PENDIENTE','EN_CURSO') ORDER BY id")],
        planes=tuple(p.execute('SELECT COUNT(*), COALESCE(SUM(activo),0), COALESCE(SUM(frecuencia_dias),0) FROM plan_mantenimiento').fetchone()),
    )
    texto = json.dumps(partes, default=str, sort_keys=True)
    return hashlib.sha1(texto.encode()).hexdigest()[:16], partes


NOMBRE_PARTE = dict(proyectos='proyectos en curso', tareo='tareo registrado', piezas='avance de piezas', paradas='paradas de máquina',
                    preventivos='órdenes preventivas', planes='plan preventivo')


def registrar(app, plat, usuario_actual, requiere, actividad, motor, cartera, mtbf_actual, maquinas):
    """cartera(con) → lista de ProyectoPlan de los proyectos en curso; mtbf_actual(con) → MTBF por máquina."""

    def ultimo(p, estado):
        r = p.execute('SELECT * FROM plan_version WHERE estado=? ORDER BY id DESC LIMIT 1', (estado,)).fetchone()
        return dict(r) if r else None

    def avisos_de(aprobado, propuesto):
        """Proyectos cuya probabilidad de cumplir cae bajo α o cuyo P80 pasa la fecha comprometida en la propuesta."""
        if not propuesto:
            return []
        antes = {x['codigo']: x for x in (aprobado or {}).get('proyectos', [])}
        out = []
        for x in propuesto['proyectos']:
            if x['prob_cumplir'] is None:
                continue
            a = antes.get(x['codigo'])
            if x['prob_cumplir'] < x['alpha'] and (a is None or a['prob_cumplir'] is None or a['prob_cumplir'] >= x['alpha'] or x['prob_cumplir'] < a['prob_cumplir'] - 0.05):
                out.append(dict(codigo=x['codigo'], prob=x['prob_cumplir'], antes=a['prob_cumplir'] if a else None, compromiso=x['compromiso'], p80=x['p80'],
                                texto=f'{x["codigo"]}: P(cumplir {x["compromiso"]}) = {round(100 * x["prob_cumplir"])} %' + (f' (antes {round(100 * a["prob_cumplir"])} %)' if a and a['prob_cumplir'] is not None else '')))
        return out

    def calcular(p, regla, motivo, u=None):
        with _lock:
            cot = motor.get()
            pp = [x for x in cartera(p) if not x.nuevo]
            res = proponer(cot, pp, str(date.today()), preventivos_futuros(p, maquinas), maquinas, mtbf_actual(p), regla=regla, R=R_PLAN)
            hu, partes = huella(p)
            aprobado = ultimo(p, 'APROBADO')
            ap_res = json.loads(aprobado['resultado']) if aprobado else None
            cambios = diferencias(ap_res, res)
            avisos = avisos_de(ap_res, res)
            p.execute("UPDATE plan_version SET estado='DESCARTADO' WHERE estado='PROPUESTO'")
            vid = p.execute('''INSERT INTO plan_version (motivo, regla, creado_por, huella, resultado, cambios, avisos) VALUES (?,?,?,?,?,?,?)''',
                            (motivo, regla, u['id'] if u else None, json.dumps(dict(id=hu, partes=partes), default=str), json.dumps(res),
                             json.dumps(cambios), json.dumps(avisos))).lastrowid
            for x in res['proyectos']:
                p.execute('INSERT INTO plan_proyecto VALUES (?,?,?,?,?,?,?,?,?)', (vid, x['id'], x['codigo'], x['prioridad'], x['compromiso'], x['p50'], x['p80'],
                                                                                   x['prob_cumplir'], x['penalidad']))
                p.executemany('INSERT INTO plan_linea VALUES (?,?,?,?,?,?,?)', [(vid, x['id'], x['codigo'], pr['proceso'], pr['inicio'], pr['fin'], pr['hh']) for pr in x['procesos']])
            if avisos:
                actividad(p, u or dict(id=None), 'programacion', f'Plan propuesto #{vid}: ' + '; '.join(a['texto'] for a in avisos[:3]))
            p.commit()
            return vid

    def estado_huella(p, version):
        if not version:
            return dict(desactualizado=True, cambios=['todavía no hay un plan'])
        guardada = json.loads(version['huella'] or '{}')
        hu, partes = huella(p)
        if guardada.get('id') == hu:
            return dict(desactualizado=False, cambios=[])
        viejas = guardada.get('partes', {})
        cambio = [NOMBRE_PARTE[k] for k in partes if json.dumps(partes[k], default=str) != json.dumps(viejas.get(k), default=str)]
        return dict(desactualizado=True, cambios=cambio)

    def vista(v):
        if not v:
            return None
        return dict(id=v['id'], creado_en=v['creado_en'], motivo=v['motivo'], regla=v['regla'], estado=v['estado'], aprobado_en=v['aprobado_en'],
                    resultado=json.loads(v['resultado']), cambios=json.loads(v['cambios'] or '[]'), avisos=json.loads(v['avisos'] or '[]'))

    @app.get('/api/programacion')
    def estado(u=Depends(usuario_actual), p=Depends(plat)):
        ap, pr = ultimo(p, 'APROBADO'), ultimo(p, 'PROPUESTO')
        hist = [dict(r) for r in p.execute('''SELECT v.id, v.creado_en, v.motivo, v.regla, v.estado, v.aprobado_en, us.nombre aprobado_por,
                                              (SELECT COUNT(*) FROM json_each(v.cambios)) n_cambios, (SELECT COUNT(*) FROM json_each(v.avisos)) n_avisos
                                              FROM plan_version v LEFT JOIN usuario us ON us.id=v.aprobado_por ORDER BY v.id DESC LIMIT 30''')]
        n_aprob = p.execute("SELECT COUNT(*) FROM plan_version WHERE estado IN ('APROBADO','REEMPLAZADO')").fetchone()[0]
        return dict(aprobado=vista(ap), propuesto=vista(pr), vigencia=estado_huella(p, ap), propuesta_vigente=estado_huella(p, pr) if pr else None,
                    historial=hist, reprogramaciones=max(0, n_aprob - 1), reglas=list(REGLAS), calculando=_lock.locked())

    @app.post('/api/programacion/proponer')
    def proponer_plan(d: PropuestaIn, u=Depends(requiere(*PROPONEN)), p=Depends(plat)):
        if d.regla not in REGLAS:
            raise HTTPException(422, 'Regla de prioridad no válida')
        vid = calcular(p, d.regla, d.motivo[:60] or 'manual', u)
        return {'id': vid}

    @app.post('/api/programacion/{vid}/aprobar')
    def aprobar(vid: int, d: AprobarIn, u=Depends(requiere(*APRUEBAN)), p=Depends(plat)):
        v = p.execute('SELECT * FROM plan_version WHERE id=?', (vid,)).fetchone()
        if not v or v['estado'] != 'PROPUESTO':
            raise HTTPException(422, 'Solo se aprueba un plan propuesto')
        res = json.loads(v['resultado'])
        sug = {s['orden_id']: s for s in res.get('sugerencias', []) if s.get('orden_id')}
        movidos = []
        for oid in d.mover_preventivos:
            if oid not in sug:
                raise HTTPException(422, f'La orden OM-{oid} no está entre las sugerencias del plan')
            p.execute("UPDATE orden_mantenimiento SET programada_para=? WHERE id=? AND estado='PENDIENTE'", (sug[oid]['a'], oid))
            movidos.append(f'OM-{oid} → {sug[oid]["a"]}')
        p.execute("UPDATE plan_version SET estado='REEMPLAZADO' WHERE estado='APROBADO'")
        hu, partes = huella(p)                    # si se movieron preventivos, el plan aprobado ya los incluye
        p.execute("UPDATE plan_version SET estado='APROBADO', aprobado_por=?, aprobado_en=?, huella=? WHERE id=?",
                  (u['id'], datetime.now().strftime('%Y-%m-%d %H:%M'), json.dumps(dict(id=hu, partes=partes), default=str), vid))
        actividad(p, u, 'programacion', f'Aprobó el plan #{vid} ({len(res["proyectos"])} proyectos)' + (f'; movió {", ".join(movidos)}' if movidos else ''))
        p.commit()
        return {'ok': True}

    @app.post('/api/programacion/{vid}/descartar')
    def descartar(vid: int, u=Depends(requiere(*APRUEBAN)), p=Depends(plat)):
        p.execute("UPDATE plan_version SET estado='DESCARTADO' WHERE id=? AND estado='PROPUESTO'", (vid,))
        p.commit()
        return {'ok': True}

    @app.post('/api/programacion/simular')
    def simular(d: SimularIn, u=Depends(requiere(*PROPONEN)), p=Depends(plat)):
        """Agrega un proyecto hipotético a la cartera y dice si cabe en la meta, cuándo debe empezar a más tardar
        y cómo afecta a los demás. No guarda nada."""
        from dss.datos import TIPOS
        if d.tipo not in TIPOS:
            raise HTTPException(422, 'Tipo de estructura no válido')
        if d.regla not in REGLAS:
            raise HTTPException(422, 'Regla de prioridad no válida')
        try:
            meta = meta_a_fecha(d.meta)
        except Exception:
            raise HTTPException(422, 'Meta no válida: use AAAA-MM o AAAA-MM-DD')
        if meta and meta < d.inicio:
            raise HTTPException(422, 'La meta es anterior al inicio')
        with _lock:
            cot = motor.get()
            base = [x for x in cartera(p) if not x.nuevo]
            nuevo = ProyectoPlan(id=None, codigo='NUEVO', proy=Proyecto(d.tipo, d.ton, d.inicio, d.presupuesto, d.pct_planchas, d.piezas_por_t, d.m2_pint_t, d.montaje),
                                 compromiso=meta, alpha=d.alpha, nuevo=True)
            prev = preventivos_futuros(p, maquinas)
            sin = proponer(cot, base, str(date.today()), prev, maquinas, mtbf_actual(p), regla=d.regla, R=R_PLAN, sugerir_preventivos=False)
            con = proponer(cot, base + [nuevo], str(date.today()), prev, maquinas, mtbf_actual(p), regla=d.regla, R=R_PLAN, sugerir_preventivos=False)
        n = next(x for x in con['proyectos'] if x['nuevo'])
        efecto = diferencias(sin, con)
        return dict(meta=meta, nuevo=n, cabe=None if meta is None else n['prob_cumplir'] >= d.alpha, plan=con,
                    efecto_en_otros=[e for e in efecto if e.get('codigo') != 'NUEVO'])

    @app.get('/api/programacion/ocupacion')
    def ocupacion_aprobada(u=Depends(usuario_actual), p=Depends(plat)):
        o = ocupacion(p)
        return None if o is None else dict(o, frac=o['frac'].round(3).tolist())

    def ocupacion(p, desde=None):
        """Fracción de cada máquina tomada por el plan aprobado, desde `desde` (para el cotizador)."""
        ap = ultimo(p, 'APROBADO')
        if not ap:
            return None
        res = json.loads(ap['resultado'])
        if not res.get('carga'):
            return None
        horas = np.array([c['horas'] for c in res['carga']], float).T            # (dias, 4)
        cap = 8.0
        frac = np.clip(horas / cap, 0, 1)
        if desde:
            k = int(np.busday_count(res['hoy'], str(desde)[:10], weekmask=WEEKMASK)) if str(desde)[:10] >= res['hoy'] else 0
            frac = frac[k:]
        return dict(plan_id=ap['id'], aprobado_en=ap['aprobado_en'], frac=frac)

    # ---------------------------------------------------------------- readaptación automática
    def vigilar():
        """Propone un plan nuevo cuando cambia el estado de la planta (cada 10 min) o cada noche desde las 21 h."""
        time.sleep(60)
        while True:
            try:
                p = next(plat())
                try:
                    pr = ultimo(p, 'PROPUESTO')
                    ap = ultimo(p, 'APROBADO')
                    ref = pr or ap
                    hoy = str(date.today())
                    hay_cartera = p.execute("SELECT COUNT(*) FROM proyecto_activo WHERE estado='EN_CURSO'").fetchone()[0] > 0
                    if hay_cartera and not _lock.locked():
                        if ref is None or estado_huella(p, ref)['desactualizado']:
                            calcular(p, (ap or {}).get('regla', 'penalidad'), 'automático: hubo cambios en la planta')
                        elif datetime.now().hour >= 21 and str(ref['creado_en'])[:10] < hoy:
                            calcular(p, (ap or {}).get('regla', 'penalidad'), 'automático: recálculo nocturno')
                finally:
                    p.close()
            except Exception as e:                       # el vigilante nunca debe tumbar el servidor
                print('programación automática:', e)
            time.sleep(600)

    threading.Thread(target=vigilar, daemon=True, name='programador').start()
    return ocupacion
