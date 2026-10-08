"""SteelPlan · Planta 3D retrospectiva: estado de la planta por día, what-if y búsqueda de escenarios.

Todo se lee de `data/steelser.db` (tablas `sim_*`, SIMULADAS): la vista 3D reproduce cómo se ejecutaron los
proyectos y permite probar decisiones de gestión evaluadas con QRF + Monte Carlo. No escribe en la BD.
Las rutas se registran desde server.py con `registrar(...)` para compartir sesión, permisos y motor.
"""
import json
import sqlite3
import threading
from datetime import date

import numpy as np
import pandas as pd
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from dss.c3_montecarlo import Proyecto
from dss.crp_engine import WEEKMASK
from dss.retrospectivo import Retro, desplazar
from dss.simulador_planta import ETAPAS, a_idx, de_idx, etapas_de_lotes
from dss.whatif import Palanca, NOMBRES, buscar, evaluar, multiplicadores, sensibilidad

ETAPA_PROCESOS = dict(ETAPAS)
NOMBRE_ETAPA = {'HABILITADO': 'Habilitado', 'DOBLEZ': 'Doblez (externo)', 'ARMADO': 'Armado', 'SOLDEO': 'Soldeo',
                'LIMPIEZA': 'Limpieza y liberación', 'PINTURA': 'Granallado y pintura', 'DESPACHO': 'Despacho a obra'}
AVISO = ('Datos SIMULADOS (retrospectivo): el modelo de horas se entrena con el escenario M2 y la planta es una '
         'plantilla funcional, no un plano medido.')


class PalancaIn(BaseModel):
    tipo: str = Field(pattern='^(personas|turno2|horas_extra|expeditar)$')
    proceso: int = Field(ge=0, le=12)
    valor: int = Field(default=1, ge=1, le=6)


class EscenarioIn(BaseModel):
    mundo: int = 2
    pid: int
    palancas: list[PalancaIn] = []
    fecha_objetivo: str | None = None
    R: int = Field(default=800, ge=100, le=3000)


class SugerirIn(BaseModel):
    mundo: int = 2
    pid: int
    fecha_objetivo: str | None = None
    R: int = Field(default=600, ge=200, le=2000)


class _Cache:
    """Retro por mundo (se construyen una vez)."""
    _retro = {}
    _lock = threading.Lock()

    @classmethod
    def retro(cls, hist_path, mundo):
        with cls._lock:
            if mundo not in cls._retro:
                con = sqlite3.connect(hist_path, check_same_thread=False)
                cls._retro[mundo] = Retro(con, mundo)
            return cls._retro[mundo]


def _df(con, sql, params=()):
    return pd.read_sql(sql, con, params=params)


def _existe(con):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE name='sim_planta_elemento'").fetchone()) and \
        con.execute('SELECT COUNT(*) FROM sim_planta_elemento').fetchone()[0] > 0


def _palancas(lst):
    return [Palanca(p.tipo, p.proceso, p.valor) for p in lst]


def registrar(app, hist, usuario_actual, requiere, motor, hist_path):
    """Agrega las rutas /api/planta/* a la aplicación."""

    def listo(con):
        if not _existe(con):
            raise HTTPException(503, 'Faltan los datos simulados de la planta: ejecute py -m dss.simulador_planta')

    @app.get('/api/planta/modelo')
    def modelo(u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        el = _df(con, 'SELECT * FROM sim_planta_elemento ORDER BY id')
        el['meta'] = el.meta.map(lambda m: json.loads(m) if m else {})
        return dict(elementos=json.loads(el.to_json(orient='records')), aviso=AVISO,
                    mundos=[dict(id=r[0], nombre=r[1]) for r in con.execute('SELECT id, nombre FROM sim_mundo ORDER BY id')])

    @app.get('/api/planta/proyectos')
    def proyectos(mundo: int = 2, u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        d = _df(con, '''SELECT p.id pid, p.codigo_muestra cod, p.nombre, t.nombre tipo, p.toneladas ton, p.fecha_inicio ini,
                        p.fecha_fin_plan plan, p.fecha_fin_real real, p.dias_retraso retraso
                        FROM proyecto p JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                        WHERE p.en_muestra=1 ORDER BY p.fecha_inicio, p.id''')
        return dict(proyectos=json.loads(d.to_json(orient='records')), aviso=AVISO)

    @app.get('/api/planta/estado')
    def estado(mundo: int = 2, fecha: str = '', pid_esc: int | None = None, palancas: str = '',
               u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        try:
            f = str(np.datetime64(fecha, 'D'))
        except ValueError:
            raise HTTPException(422, 'Fecha no válida (AAAA-MM-DD)')
        esc = None
        if pid_esc and palancas:
            try:
                esc = [Palanca(**x) for x in json.loads(palancas)]
            except Exception:
                raise HTTPException(422, 'Palancas no válidas')
        return _estado(con, hist_path, mundo, f, pid_esc, esc)

    @app.post('/api/planta/escenario')
    def escenario(b: EscenarioIn, u=Depends(requiere('cotizador', 'jefe_taller')), con=Depends(hist)):
        listo(con)
        retro = _Cache.retro(hist_path, b.mundo)
        d, proy, fo = _proyecto(con, retro, b.pid, b.fecha_objetivo)
        cot = motor.get()
        pal = _palancas(b.palancas)
        base = evaluar(cot, proy, [], fo, R=b.R, semilla=b.pid, mtbf=motor.mtbf_sim)
        esc = evaluar(cot, proy, pal, fo, R=b.R, semilla=b.pid, mtbf=motor.mtbf_sim)
        fin_base = retro.replay(b.pid)['fin']
        out = dict(proyecto=b.pid, cod=d.cod, fecha_objetivo=fo, aviso=AVISO, base=_resumen(base), escenario=_resumen(esc),
                   palancas=[p.etiqueta() for p in pal])
        if pal:
            m = multiplicadores(pal, d.crew)
            fin_esc = retro.replay(b.pid, mult=m)['fin']
            real_cf = desplazar(d.fr, fin_esc - fin_base)
            out['contrafactual'] = dict(fecha_real=d.fr, fecha_con_palancas=real_cf, dias_laborables_ahorrados=fin_base - fin_esc,
                                        cumple_real=d.fr <= fo, cumple_con_palancas=real_cf <= fo)
        return out

    @app.post('/api/planta/sugerir')
    def sugerir(b: SugerirIn, u=Depends(requiere('cotizador', 'jefe_taller')), con=Depends(hist)):
        listo(con)
        retro = _Cache.retro(hist_path, b.mundo)
        d, proy, fo = _proyecto(con, retro, b.pid, b.fecha_objetivo)
        ranking, base = buscar(motor.get(), proy, fo, R=b.R, semilla=b.pid, mtbf=motor.mtbf_sim)
        mejores = [e for e in ranking if e.palancas][:3]
        out = []
        for e in mejores:
            r = _resumen(e)
            m = multiplicadores(e.palancas, d.crew)
            fin_esc, fin_base = retro.replay(b.pid, mult=m)['fin'], retro.replay(b.pid)['fin']
            r['palancas_json'] = [dict(tipo=p.tipo, proceso=p.proceso, valor=p.valor) for p in e.palancas]
            r['contrafactual_fin'] = desplazar(d.fr, fin_esc - fin_base)
            out.append(r)
        return dict(proyecto=b.pid, cod=d.cod, fecha_objetivo=fo, base=_resumen(base), sugerencias=out, aviso=AVISO)

    @app.get('/api/planta/sensibilidad')
    def sens(pid: int, mundo: int = 2, fecha_objetivo: str | None = None, u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        retro = _Cache.retro(hist_path, mundo)
        d, proy, fo = _proyecto(con, retro, pid, fecha_objetivo)
        s = sensibilidad(motor.get(), proy, fo, R=400, semilla=pid, mtbf=motor.mtbf_sim)
        return dict(fecha_objetivo=fo, aviso=AVISO, **s)

    @app.get('/api/planta/retro')
    def retro_resultados(cod: int | None = None, u=Depends(usuario_actual), con=Depends(hist)):
        """Resultados del experimento 5 (cómo se hizo vs. qué habría pasado)."""
        if not con.execute("SELECT 1 FROM sqlite_master WHERE name='sim_retro_resultado'").fetchone():
            return dict(disponible=False, aviso=AVISO)
        d = _df(con, 'SELECT * FROM sim_retro_resultado')
        resumen = (d.groupby('politica', sort=False)
                   .agg(otd=('cumple', lambda s: round(100 * s.mean(), 1)), retraso_dias=('tarde', lambda s: round(s.mean(), 2)),
                        penalidad=('penalidad', lambda s: round(s.mean(), 2)), costo=('costo', lambda s: round(s.mean(), 2)),
                        total=('total', lambda s: round(s.mean(), 2)), lead=('lead', lambda s: round(s.mean(), 1)),
                        intervenciones=('intervino', 'sum')).reset_index())
        out = dict(disponible=True, aviso=AVISO, resumen=json.loads(resumen.to_json(orient='records')))
        if cod is not None:
            p = d[d.cod == cod]
            out['proyecto'] = json.loads(p.to_json(orient='records'))
        return out


# ------------------------------------------------------------------ piezas internas
def _proyecto(con, retro, pid, fecha_objetivo):
    if pid not in retro.P.index:
        raise HTTPException(404, 'Proyecto no encontrado en la muestra')
    d = retro.datos(pid)
    fila = retro.df[retro.df.pid == pid].iloc[0]
    proy = Proyecto(tipo=d.tipo, ton=d.ton, inicio=d.ini, presupuesto=100.0, pct_planchas=float(fila.pct_planchas),
                    piezas_por_t=float(fila.piezas_por_t), m2_pintura_t=float(fila.m2_pintura / d.ton),
                    montaje=bool(fila.montaje), id=pid, cuadrilla=d.crew, ext_dias=d.ext_plan)
    return d, proy, (fecha_objetivo or d.fp)


def _resumen(e):
    return dict(prob=round(e.prob, 4), penalidad=round(e.penalidad, 3), costo=round(e.costo, 3), total=round(e.total, 3),
                dias_medios=round(e.dias_medios, 1), fecha_alpha=e.fecha_alpha, palancas=[p.etiqueta() for p in e.palancas])


def _ventanas_escenario(retro, pid, mult):
    """Ventanas (idx de día) de los 13 procesos del proyecto con las palancas aplicadas (replay de la verdad)."""
    d = retro.datos(pid)
    r = retro.replay(pid, mult=mult)
    base = a_idx(str(np.busday_offset(np.datetime64(d.ini, 'D'), 0, roll='forward', weekmask=WEEKMASK)))
    v = {}
    for j in range(13):
        a = base + int(r['ini'][j])
        b = base + int(r['fin_proc'][j]) - 1
        v[j + 1] = (a, max(a, b))
    return v


def _estado(con, hist_path, mundo, fecha, pid_esc, palancas):
    idx = a_idx(fecha)
    elementos = {r['id']: dict(r) for r in con.execute('SELECT id, tipo, nombre, proceso_orden FROM sim_planta_elemento')}
    buffer_id = next(i for i, e in elementos.items() if e['nombre'].startswith('Buffer'))
    patio_id = next(i for i, e in elementos.items() if e['nombre'].startswith('Patio'))
    proy = {r['id']: dict(r) for r in con.execute('''SELECT p.id, p.codigo_muestra cod, p.nombre, p.toneladas ton, p.fecha_inicio ini,
        p.fecha_fin_plan plan, p.fecha_fin_real real FROM proyecto p WHERE p.en_muestra=1''')}
    # estaciones de cada proyecto × proceso (de toda su ejecución)
    est = {}
    for r in con.execute('''SELECT proyecto_id pid, proceso_orden o, estacion_id e FROM sim_asignacion WHERE mundo_id=?
                            GROUP BY 1, 2, 3 ORDER BY 1, 2, 3''', (mundo,)):
        est.setdefault((r['pid'], r['o']), []).append(r['e'])
    asig = [dict(r) for r in con.execute('''SELECT proyecto_id pid, proceso_orden o, estacion_id e, personas, hh FROM sim_asignacion
                                            WHERE mundo_id=? AND fecha=?''', (mundo, fecha))]
    lotes = {(r['proyecto_id'], r['lote']): dict(r) for r in con.execute(
        'SELECT proyecto_id, lote, kg, n_piezas, descripcion FROM sim_lote WHERE mundo_id=?', (mundo,))}
    etapas = {}
    for r in con.execute('''SELECT proyecto_id pid, lote, etapa, orden, f_inicio, f_fin FROM sim_lote_etapa WHERE mundo_id=?
                            ORDER BY 1, 2, orden''', (mundo,)):
        etapas.setdefault((r['pid'], r['lote']), []).append((r['etapa'], r['orden'], a_idx(r['f_inicio']), a_idx(r['f_fin'])))
    esc_info = None
    if pid_esc and palancas is not None and pid_esc in proy:
        retro = _Cache.retro(hist_path, mundo)
        d = retro.datos(pid_esc)
        m = multiplicadores(palancas, d.crew)
        v = _ventanas_escenario(retro, pid_esc, m)
        n = sum(1 for k in lotes if k[0] == pid_esc)
        nuevas, _ = etapas_de_lotes(n, v)
        for k, fases in nuevas.items():
            etapas[(pid_esc, k + 1)] = [(a, b, c, e) for a, b, c, e in fases]
        asig = [x for x in asig if x['pid'] != pid_esc]
        for o in range(1, 14):
            a, b = v[o]
            if a <= idx <= b:
                externo = o in (7, 12)
                n_p = 0 if externo else max(1, int(round(d.crew[o - 1] * m[o - 1])))
                st = est.get((pid_esc, o), [])
                for i, e in enumerate(st):
                    asig.append(dict(pid=pid_esc, o=o, e=e, personas=n_p // len(st) + (1 if i < n_p % len(st) else 0),
                                     hh=float(d.hh_real[o - 1]) / (b - a + 1) / len(st)))
        esc_info = dict(pid=pid_esc, fin=de_idx(max(b for a, b in v.values())), palancas=[p.etiqueta() for p in palancas])
    # cuadrillas nominales (nombres) por proyecto × proceso
    nombres = {}
    for r in con.execute('''SELECT c.proyecto_id pid, c.proceso_orden o, p.id, p.nombre, p.grupo FROM sim_cuadrilla c
                            JOIN sim_personal p ON p.id=c.persona_id WHERE c.mundo_id=? ORDER BY c.proyecto_id, c.proceso_orden, p.id''',
                         (mundo,)):
        nombres.setdefault((r['pid'], r['o']), []).append(dict(id=r['id'], nombre=r['nombre'], grupo=r['grupo']))
    # estaciones del día
    estaciones = {}
    usados = {}
    for a in asig:
        s = estaciones.setdefault(a['e'], dict(id=a['e'], personas=0, hh=0.0, proyectos=[], gente=[]))
        s['personas'] += a['personas']
        s['hh'] += a['hh']
        p = proy[a['pid']]
        s['proyectos'].append(dict(pid=a['pid'], cod=p['cod'], proceso=a['o'], proceso_nombre=NOMBRES[a['o'] - 1],
                                   personas=a['personas'], hh=round(a['hh'], 1)))
        pool = nombres.get((a['pid'], a['o']), [])
        k0 = usados.get((a['pid'], a['o']), 0)
        s['gente'] += pool[k0:k0 + a['personas']]
        usados[(a['pid'], a['o'])] = k0 + a['personas']
    # lotes: estado y ubicación
    lotes_out = []
    activos = set()
    for (pid, lote), info in lotes.items():
        fases = etapas.get((pid, lote))
        if not fases:
            continue
        ini, fin = fases[0][2], fases[-1][3]
        if idx < ini - 6 or idx > fin + 2:
            continue
        activos.add(pid)
        estado_l, etapa, ubic = 'ACOPIO', None, patio_id
        if idx > fin:
            estado_l, etapa, ubic = 'DESPACHADO', fases[-1][0], None
        elif idx >= ini:
            for nombre, orden, a, b in fases:
                if a <= idx <= b:
                    estado_l, etapa = 'EN_PROCESO', nombre
                    st = [e for o in ETAPA_PROCESOS[nombre] for e in est.get((pid, o), [])
                          if any(x['e'] == e and x['pid'] == pid for x in asig)] or \
                         [e for o in ETAPA_PROCESOS[nombre] for e in est.get((pid, o), [])]
                    ubic = st[(lote - 1) % len(st)] if st else buffer_id
                    break
            else:
                prev = max((f for f in fases if f[3] < idx), key=lambda f: f[3])
                sig = next(f for f in fases if f[2] > idx)
                estado_l, etapa = 'EN_COLA', sig[0]
                st = [e for o in ETAPA_PROCESOS[sig[0]] for e in est.get((pid, o), [])]
                ubic = st[(lote - 1) % len(st)] if st else buffer_id
        if estado_l == 'DESPACHADO' and idx > fin + 2:
            continue
        lotes_out.append(dict(pid=pid, cod=proy[pid]['cod'], lote=lote, kg=info['kg'], n_piezas=info['n_piezas'],
                              descripcion=info['descripcion'], estado=estado_l, etapa=etapa,
                              etapa_nombre=NOMBRE_ETAPA.get(etapa), ubicacion=ubic))
    # material en stock
    mats = [dict(r) for r in con.execute('''SELECT m.id, m.proyecto_id pid, p.codigo_muestra cod, m.tipo, m.perfil, m.cantidad, m.kg,
        m.colada, m.certificado, m.ubicacion_id ubicacion, m.f_ingreso, m.f_consumo FROM sim_material_lote m
        JOIN proyecto p ON p.id=m.proyecto_id WHERE m.mundo_id=? AND m.f_ingreso<=? AND m.f_consumo>=?''', (mundo, fecha, fecha))]
    for m in mats:
        m['dias_en_stock'] = max(0, idx - a_idx(m['f_ingreso']))
    # proyectos activos
    act = []
    for pid in sorted(activos | {a['pid'] for a in asig}):
        p = proy[pid]
        ls = [l for l in lotes_out if l['pid'] == pid]
        todos = [k for k in lotes if k[0] == pid]
        kg_tot = sum(lotes[k]['kg'] for k in todos)
        hecho = 0.0
        for k in todos:
            fases = etapas[k]
            if idx > fases[-1][3]:
                hecho += lotes[k]['kg']
            else:
                hecho += lotes[k]['kg'] * sum(1 for f in fases if idx > f[3]) / len(fases)
        act.append(dict(pid=pid, cod=p['cod'], nombre=p['nombre'], ton=p['ton'], ini=p['ini'], plan=p['plan'], real=p['real'],
                        avance=round(hecho / kg_tot, 3) if kg_tot else 0, lotes=len(ls)))
    gente = sum(s['personas'] for s in estaciones.values())
    return dict(fecha=fecha, estaciones=list(estaciones.values()), lotes=lotes_out, material=mats, proyectos=act,
                escenario=esc_info, kpi=dict(proyectos=len(act), personas=gente,
                                             kg_en_proceso=round(sum(l['kg'] for l in lotes_out if l['estado'] == 'EN_PROCESO')),
                                             kg_en_cola=round(sum(l['kg'] for l in lotes_out if l['estado'] == 'EN_COLA')),
                                             stock_kg=round(sum(m['kg'] for m in mats))), aviso=AVISO)
