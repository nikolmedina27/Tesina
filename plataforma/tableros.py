"""SteelPlan · Tableros fijos (v3.2): Gerencia, Producción, Planta (TV) y Mensual (PDF).

Diseño fijo, sin configuración. No calculan nada nuevo: leen lo que ya producen los demás módulos (plan de la
cartera aprobado, mantenimiento, avance de proyectos, bandeja RFI/NC, histórico) para que cada número coincida
con su vista de detalle. Las rutas se registran desde server.py con `registrar(...)`.
"""
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np
from fastapi import Depends, HTTPException

from dss.crp_engine import WEEKMASK
from dss.mantenimiento import META_DK, indicadores

META_OTD = 0.85


def _mes(s):
    try:
        a, m = (int(x) for x in str(s).split('-')[:2])
        return date(a, m, 1)
    except Exception:
        raise HTTPException(422, 'Mes no válido (AAAA-MM)')


def _fin_mes(d):
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def registrar(app, plat, hist, usuario_actual, activos, semana_actual, bandeja, maquinas_estado):
    """activos(p) → proyectos en curso con avance; semana_actual(p, r) → fila de la semana en curso de un proyecto;
    bandeja(p) → RFI/NC; maquinas_estado(p) → resumen de cada máquina (estado, Dₖ 30 días, preventivos)."""

    def plan_aprobado(p):
        v = p.execute("SELECT * FROM plan_version WHERE estado='APROBADO' ORDER BY id DESC LIMIT 1").fetchone()
        pr = p.execute("SELECT id, creado_en, motivo, avisos FROM plan_version WHERE estado='PROPUESTO' ORDER BY id DESC LIMIT 1").fetchone()
        pendiente = dict(id=pr['id'], creado_en=pr['creado_en'], motivo=pr['motivo'], avisos=json.loads(pr['avisos'] or '[]')) if pr and (not v or pr['id'] > v['id']) else None
        if v:
            return json.loads(v['resultado']), dict(id=v['id'], aprobado_en=v['aprobado_en'], estado='APROBADO'), pendiente
        if pr:                                    # sin plan aprobado todavía: se muestra la propuesta, marcada como tal
            pv = p.execute('SELECT resultado FROM plan_version WHERE id=?', (pr['id'],)).fetchone()
            return json.loads(pv['resultado']), dict(id=pr['id'], aprobado_en=None, estado='PROPUESTO'), pendiente
        return None, None, None

    def entregas(p, h, desde, hasta):
        """Proyectos entregados en [desde, hasta): histórico + los cerrados en la plataforma."""
        out = [dict(codigo=r['codigo_muestra'] or f'N° {r["n_registro"]}', nombre=r['nombre'], cliente=r['cliente'], fin=r['fecha_fin_real'],
                    a_tiempo=(r['dias_retraso'] or 0) <= 0, retraso=max(r['dias_retraso'] or 0, 0), fuente='histórico')
               for r in h.execute('SELECT * FROM proyecto WHERE n_registro IS NOT NULL AND fecha_fin_real>=? AND fecha_fin_real<?', (str(desde), str(hasta)))]
        for r in p.execute("SELECT * FROM proyecto_activo WHERE estado='ENTREGADO' AND fecha_fin_real>=? AND fecha_fin_real<?", (str(desde), str(hasta))):
            lim = date.fromisoformat(r['fecha_comprometida'][:10]) + timedelta(days=r['ampliacion_dias'] or 0) if r['fecha_comprometida'] else None
            ret = (date.fromisoformat(r['fecha_fin_real'][:10]) - lim).days if lim else 0
            out.append(dict(codigo=r['codigo'], nombre=r['nombre'], cliente=r['cliente'], fin=r['fecha_fin_real'], a_tiempo=ret <= 0, retraso=max(ret, 0), fuente='plataforma'))
        return sorted(out, key=lambda x: x['fin'])

    def otd_12_meses(p, h):
        hoy = date.today()
        y, m = hoy.year, hoy.month - 11                            # 12 meses calendario, incluido el actual
        if m <= 0:
            y, m = y - 1, m + 12
        ini = date(y, m, 1)
        e = entregas(p, h, ini, hoy + timedelta(days=1))
        meses, d = [], ini
        while d <= hoy:
            k = d.strftime('%Y-%m')
            x = [z for z in e if z['fin'][:7] == k]
            meses.append(dict(mes=k, entregas=len(x), a_tiempo=sum(z['a_tiempo'] for z in x)))
            d = _fin_mes(d)
        n = len(e)
        return dict(meses=meses, entregas=n, a_tiempo=sum(z['a_tiempo'] for z in e), otd=round(sum(z['a_tiempo'] for z in e) / n, 3) if n else None,
                    retraso_prom=round(float(np.mean([z['retraso'] for z in e])), 2) if n else None, detalle=e[-8:])

    def carga_semanas(res, n_sem=4):
        """Uso de cada máquina por semana (horas planificadas / horas disponibles) según el plan aprobado."""
        if not res or not res.get('carga'):
            return []
        fechas = res['fechas']
        lunes0 = date.fromisoformat(res['hoy']) - timedelta(days=date.fromisoformat(res['hoy']).weekday())
        out = []
        for c in res['carga']:
            sem = defaultdict(lambda: [0.0, 0.0])
            for f, hh, cap in zip(fechas, c['horas'], c['capacidad']):
                k = (date.fromisoformat(f) - lunes0).days // 7
                if 0 <= k < n_sem:
                    sem[k][0] += hh
                    sem[k][1] += cap
            out.append(dict(maquina=c['maquina'], semanas=[dict(desde=str(lunes0 + timedelta(days=7 * k)), uso=round(sem[k][0] / sem[k][1], 3) if sem[k][1] else None,
                                                                horas=round(sem[k][0], 1)) for k in range(n_sem)]))
        return out

    def cuellos(res, dias=10):
        """Máquinas con más carga en los próximos `dias` días laborables del plan aprobado."""
        if not res or not res.get('carga'):
            return []
        out = []
        for c in res['carga']:
            hh, cap = np.array(c['horas'][:dias]), np.array(c['capacidad'][:dias])
            u = np.where(cap > 0.01, hh / np.maximum(cap, 1e-9), 0.0)                 # sin capacidad no es "saturada"
            out.append(dict(maquina=c['maquina'], uso=round(float(hh.sum() / max(cap.sum(), 1e-9)), 3) if cap.sum() > 0.01 else None,
                            dias_saturada=int((u >= 0.95).sum()), dias_sin_capacidad=int((cap <= 0.01).sum())))
        return sorted(out, key=lambda x: -(x['uso'] or 2))

    def riesgo(res):
        if not res:
            return []
        return [dict(codigo=x['codigo'], id=x['id'], prioridad=x['prioridad'], compromiso=x['compromiso'], p50=x['p50'], p80=x['p80'],
                     prob=x['prob_cumplir'], alpha=x['alpha'], penalidad=x['penalidad'],
                     semaforo='n' if x['prob_cumplir'] is None else 'v' if x['prob_cumplir'] >= x['alpha'] else 'a' if x['prob_cumplir'] >= 0.6 else 'r')
                for x in res['proyectos']]

    # ---------------------------------------------------------------- Gerencia
    @app.get('/api/tableros/gerencia')
    def gerencia(u=Depends(usuario_actual), p=Depends(plat), h=Depends(hist)):
        res, ver, pend = plan_aprobado(p)
        maqs = maquinas_estado(p)
        b = bandeja(p)
        act = activos(p)
        en_curso = [a for a in act if a['estado'] == 'EN_CURSO']
        rfi_cli = [x for x in b['filas'] if x['estado'] != 'HECHO' and x['imputable'] == 'Cliente']
        return dict(otd=otd_12_meses(p, h), meta_otd=META_OTD, plan=ver, propuesta_pendiente=pend, proyectos=riesgo(res),
                    penalidad_total=round(sum(x['penalidad'] or 0 for x in (res or {}).get('proyectos', [])), 2),
                    carga=carga_semanas(res), maquinas=[dict(nombre=m['nombre'], dk=m['indicadores_30d']['dk'], estado=m['estado'], semaforo=m['semaforo']) for m in maqs],
                    meta_dk=META_DK, en_curso=len(en_curso), ton_en_curso=round(sum(a['ton'] or 0 for a in en_curso), 1),
                    rfi_cliente=dict(abiertas=len(rfi_cli), dias=b['resumen']['dias_cliente'], dias_steelser=b['resumen']['dias_steelser']),
                    generado=datetime.now().strftime('%Y-%m-%d %H:%M'))

    # ---------------------------------------------------------------- Producción
    def produccion_datos(p):
        res, ver, pend = plan_aprobado(p)
        hoy = date.today()
        lunes = hoy - timedelta(days=hoy.weekday())
        semana = []
        for r in p.execute("SELECT * FROM proyecto_activo WHERE estado='EN_CURSO' ORDER BY id").fetchall():
            f = semana_actual(p, r)
            semana.append(dict(id=r['id'], codigo=r['codigo'], nombre=r['nombre'], **(f or {})))
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M')
        manana = str(hoy + timedelta(days=1))
        paradas_hoy = [dict(x) for x in p.execute('''SELECT pa.id, pa.maquina, pa.inicio, pa.fin, pa.causa, pa.planificada, pa.fin > ? abierta
                                                     FROM parada pa WHERE pa.fin >= ? AND pa.inicio < ? ORDER BY pa.inicio''', (ahora, str(hoy), manana))]
        lim = str(np.busday_offset(np.datetime64(str(hoy), 'D'), 2, roll='forward', weekmask=WEEKMASK))
        prev = [dict(x) for x in p.execute('''SELECT o.id, m.nombre maquina, o.titulo, o.programada_para, o.duracion_h, o.estado, o.programada_para < ? vencida
                                              FROM orden_mantenimiento o JOIN maquina m ON m.id=o.maquina_id
                                              WHERE o.estado IN ('PENDIENTE','EN_CURSO') AND o.programada_para <= ? ORDER BY o.programada_para''', (str(hoy), lim))]
        bloq = [dict(x) for x in p.execute('''SELECT t.id, t.titulo, t.fecha_limite, us.nombre responsable, pa.codigo proyecto FROM tarea t
                                              LEFT JOIN usuario us ON us.id=t.responsable_id LEFT JOIN proyecto_activo pa ON pa.id=t.proyecto_id
                                              WHERE t.tipo='BLOQUEO' AND t.estado!='HECHO' ORDER BY t.prioridad, t.id''')]
        hh_hoy = p.execute('SELECT COALESCE(SUM(hh),0), COUNT(DISTINCT proyecto_id) FROM tareo WHERE fecha=?', (str(hoy),)).fetchone()
        return dict(semana=dict(desde=str(lunes), hasta=str(lunes + timedelta(days=5))), proyectos=semana, cuellos=cuellos(res), paradas_hoy=paradas_hoy,
                    preventivos=prev, bloqueos=bloq, hh_hoy=round(hh_hoy[0], 1), proyectos_con_tareo_hoy=hh_hoy[1], plan=ver, propuesta_pendiente=pend,
                    riesgo=riesgo(res), maquinas=maquinas_estado(p), generado=ahora)

    @app.get('/api/tableros/produccion')
    def produccion(u=Depends(usuario_actual), p=Depends(plat)):
        return produccion_datos(p)

    # ---------------------------------------------------------------- Planta (TV)
    @app.get('/api/tableros/tv')
    def tv(u=Depends(usuario_actual), p=Depends(plat)):
        d = produccion_datos(p)
        avisos = []
        for m in d['maquinas']:
            if m['estado'] == 'PARADA':
                avisos.append(f'{m["nombre"]} parada por falla')
            if m['preventivos_vencidos']:
                avisos.append(f'{m["nombre"]}: preventivo vencido')
        for x in d['riesgo']:
            if x['semaforo'] == 'r':
                avisos.append(f'{x["codigo"]} en riesgo de atraso ({round(100 * x["prob"])} %)')
        for b in d['bloqueos'][:3]:
            avisos.append(f'Bloqueo STL-{b["id"]}: {b["titulo"]}')
        return d | dict(avisos=avisos)

    # ---------------------------------------------------------------- Mensual (PDF)
    @app.get('/api/tableros/mensual')
    def mensual(mes: str = '', u=Depends(usuario_actual), p=Depends(plat), h=Depends(hist)):
        ini = _mes(mes) if mes else date.today().replace(day=1)
        fin = _fin_mes(ini)
        corte = min(fin, date.today() + timedelta(days=1))
        e = entregas(p, h, ini, fin)
        r0 = p.execute('SELECT MIN(inicio) FROM parada').fetchone()[0]
        maqs = []
        for m in p.execute('SELECT * FROM maquina WHERE activa=1 ORDER BY id').fetchall():
            par = [dict(x) for x in p.execute('SELECT * FROM parada WHERE maquina=? AND fin>=? AND inicio<?', (m['nombre'], str(ini), str(corte)))]
            desde = max(str(ini), r0[:10]) if r0 else str(ini)
            i = indicadores(par, desde, str(corte), m['horas_turno'] or 8, m['turnos'] or 1) if r0 and desde < str(corte) else None   # sin registro no hay dato
            prev_prog = p.execute('''SELECT COUNT(*) FROM orden_mantenimiento WHERE maquina_id=? AND tipo='PREVENTIVO' AND programada_para>=? AND programada_para<?''',
                                  (m['id'], str(ini), str(fin))).fetchone()[0]
            prev_hechos = p.execute('''SELECT COUNT(*) FROM orden_mantenimiento WHERE maquina_id=? AND tipo='PREVENTIVO' AND estado='CERRADA'
                                       AND programada_para>=? AND programada_para<?''', (m['id'], str(ini), str(fin))).fetchone()[0]
            maqs.append(dict(nombre=m['nombre'], indicadores=i, preventivos_programados=prev_prog, preventivos_cumplidos=prev_hechos))
        causas = [dict(x) for x in p.execute('''SELECT causa, COUNT(*) n, ROUND(SUM((julianday(MIN(fin, ?))-julianday(MAX(inicio, ?)))*24),1) horas FROM parada
                                                WHERE fin>=? AND inicio<? GROUP BY causa ORDER BY horas DESC''', (str(corte), str(ini), str(ini), str(corte)))]
        hh = [dict(x) for x in p.execute('''SELECT pa.codigo, ROUND(SUM(t.hh),1) hh, COUNT(DISTINCT t.fecha) dias FROM tareo t JOIN proyecto_activo pa ON pa.id=t.proyecto_id
                                            WHERE t.fecha>=? AND t.fecha<? GROUP BY pa.codigo ORDER BY hh DESC''', (str(ini), str(fin)))]
        inc = p.execute('''SELECT COUNT(*) n, SUM(estado='HECHO') cerradas, COALESCE(SUM(CASE WHEN imputable='Cliente' THEN dias_impacto END),0) d_cli,
                           COALESCE(SUM(CASE WHEN imputable='Steelser' THEN dias_impacto END),0) d_ste FROM tarea
                           WHERE tipo IN ('RFI','NO_CONFORMIDAD','CAMBIO_ALCANCE','BLOQUEO') AND date(creado_en,'localtime')>=? AND date(creado_en,'localtime')<?''',
                        (str(ini), str(fin))).fetchone()
        planes = p.execute('''SELECT COUNT(*) total, SUM(estado IN ('APROBADO','REEMPLAZADO')) aprobados FROM plan_version
                              WHERE creado_en>=? AND creado_en<?''', (str(ini), str(fin))).fetchone()
        res, ver, _ = plan_aprobado(p)
        n = len(e)
        return dict(mes=ini.strftime('%Y-%m'), hasta=str(corte - timedelta(days=1)), entregas=e, otd=round(sum(x['a_tiempo'] for x in e) / n, 3) if n else None,
                    meta_otd=META_OTD, meta_dk=META_DK, maquinas=maqs, causas=causas, tareo=hh, incidencias=dict(inc),
                    planes=dict(total=planes['total'] or 0, aprobados=planes['aprobados'] or 0), proyectos=riesgo(res), plan=ver,
                    penalidad_total=round(sum(x['penalidad'] or 0 for x in (res or {}).get('proyectos', [])), 2),
                    registro_desde=r0[:10] if r0 else None, generado=datetime.now().strftime('%Y-%m-%d %H:%M'))
