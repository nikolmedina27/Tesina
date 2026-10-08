"""SteelPlan · API del gemelo de la planta (datos SIMULADOS): estado hora a hora para la vista 3D.

Lee las tablas `gem_*` de data/steelser.db (las crea scripts/exp6_gemelo.py). Reconstruye la planta en cualquier instante a
partir de la bitácora de estados de los lotes, las operaciones, los movimientos de grúa, los camiones y las paradas. No escribe.
El tiempo `t` está en horas desde 2019-01-01 00:00.
"""
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import Depends, HTTPException

EPOCA = date(2019, 1, 1)
RAIZ = Path(__file__).resolve().parent.parent
AVISO = ('Datos SIMULADOS: gemelo de eventos discretos calibrado a las fechas reales de la Tabla 3; la planta es una plantilla, '
         'el personal es anónimo y las horas, paradas y proveedores son supuestos.')
MAQ = ['Sierra Cinta Kaltenbach', 'Cizalladora Punzonadora Pedimax', 'Mesa CNC', 'Roscadora RIDGID']
ETAPA_NOMBRE = {'ESPERA': 'Esperando material', 'HABILITADO': 'Habilitado', 'MOVIMIENTO': 'En traslado con grúa', 'DOBLEZ': 'Doblez (externo)',
                'ARMADO': 'Armado', 'SOLDEO': 'Soldeo', 'RETRABAJO': 'Retrabajo de soldeo', 'LIMPIEZA': 'Limpieza e inspección',
                'LISTO_PINTURA': 'Listo para pintura', 'PINTURA': 'En granallado y pintura (externo)', 'PINTADO': 'Pintado, esperando despacho',
                'ENTREGADO': 'Entregado a obra'}


def hora(d, h=0.0):
    return (d - EPOCA).days * 24.0 + h


def a_fecha(t):
    return EPOCA + timedelta(days=int(t // 24))


def _q(con, sql, params=()):
    return pd.read_sql(sql, con, params=params)


def registrar(app, hist, usuario_actual):
    def listo(con):
        if not con.execute("SELECT 1 FROM sqlite_master WHERE name='gem_op'").fetchone():
            raise HTTPException(503, 'Falta el gemelo: ejecute py scripts/exp6_gemelo.py')

    @app.get('/api/gemelo/meta')
    def meta(u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        pols = [r[0] for r in con.execute('SELECT DISTINCT politica FROM gem_op ORDER BY politica')]
        todas = [r[0] for r in con.execute('SELECT DISTINCT politica FROM gem_resultado ORDER BY politica')]
        pr = _q(con, 'SELECT pid, cod, nombre, tipo, ton, ini, fp, fr, en_muestra, contratista, n_lotes, paquetes, rfis, cambios, ritmo, crew FROM gem_proyecto ORDER BY ini, pid')
        res = _q(con, "SELECT politica, pid, compromiso, fin, tarde, costo, intervenciones FROM gem_resultado WHERE replica=(SELECT MIN(replica) FROM gem_resultado)")
        el = _q(con, 'SELECT id, tipo, nombre, proceso_orden, x, z, ancho, largo, alto, rot, capacidad FROM sim_planta_elemento ORDER BY id')
        resumen = None
        f = RAIZ / 'data' / 'exp6_resumen.csv'
        if f.exists():
            resumen = json.loads(pd.read_csv(f).fillna('').to_json(orient='records'))
        personal = _q(con, 'SELECT nombre, grupo, rol FROM gem_personal ORDER BY id')
        alerta = None
        f = RAIZ / 'data' / 'exp6_alerta.csv'
        if f.exists():
            alerta = json.loads(pd.read_csv(f).to_json(orient='records'))
        return dict(politicas=pols, todas_politicas=todas, proyectos=json.loads(pr.to_json(orient='records')),
                    resultados=json.loads(res.to_json(orient='records')), elementos=json.loads(el.to_json(orient='records')),
                    resumen=resumen, alerta=alerta, personal=json.loads(personal.to_json(orient='records')), epoca=str(EPOCA), aviso=AVISO)

    @app.get('/api/gemelo/estado')
    def estado(t: float, politica: str = 'A0', u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        return _estado(con, politica, t)

    @app.get('/api/gemelo/lote/{lid}')
    def lote(lid: int, politica: str = 'A0', u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        l = _q(con, 'SELECT * FROM gem_lote WHERE id=?', (lid,))
        if l.empty:
            raise HTTPException(404, 'Lote no encontrado')
        l = l.iloc[0]
        piezas = _q(con, 'SELECT marca, perfil, kg, largo, agujeros FROM gem_pieza WHERE lote_id=? ORDER BY kg DESC', (lid,))
        ops = _q(con, 'SELECT tipo, recurso, estacion, t_ini, t_fin, personas, hh FROM gem_op WHERE politica=? AND lote_id=? ORDER BY t_ini', (politica, lid))
        est = _q(con, 'SELECT t, etapa, ubic FROM gem_estado WHERE politica=? AND lote_id=? ORDER BY t', (politica, lid))
        proy = _q(con, 'SELECT cod, nombre FROM gem_proyecto WHERE pid=?', (int(l.pid),)).iloc[0]
        est['dur_h'] = (est.t.shift(-1) - est.t).fillna(0)
        return dict(lote=json.loads(l.to_json()), proyecto=dict(cod=None if pd.isna(proy.cod) else int(proy.cod), nombre=proy.nombre),
                    piezas=json.loads(piezas.to_json(orient='records')), ops=json.loads(ops.to_json(orient='records')),
                    estados=json.loads(est.to_json(orient='records')), aviso=AVISO)

    @app.get('/api/gemelo/maquina/{k}')
    def maquina(k: int, t: float, politica: str = 'A0', u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        if not 0 <= k <= 3:
            raise HTTPException(404)
        rec = f'maq{k}'
        d1 = int(t // 24)
        ventana = [(7.0, 15.0)] if politica == 'A0' else [(7.0, 23.0)]           # horas en que puede trabajar (con segundo turno si se aplicó)
        o = _q(con, 'SELECT t_ini, t_fin, hh FROM gem_op WHERE politica=? AND recurso=? AND t_fin>? AND t_ini<?', (politica, rec, (d1 - 14) * 24.0, (d1 + 1) * 24.0))
        p = _q(con, 'SELECT t_ini, t_fin, horas FROM gem_parada WHERE maquina=? AND t_fin>? AND t_ini<?', (k, (d1 - 14) * 24.0, (d1 + 1) * 24.0))

        def reparto(df, col, d):
            """Horas de trabajo (col) de cada intervalo que caen en el día d, repartidas según su solape con las horas hábiles."""
            tot = 0.0
            for r in df.itertuples():
                pesos = {}
                dd = int(r.t_ini // 24)
                while dd <= int(r.t_fin // 24):
                    pesos[dd] = sum(max(0.0, min(r.t_fin, dd * 24 + b) - max(r.t_ini, dd * 24 + a)) for a, b in ventana)
                    dd += 1
                s = sum(pesos.values())
                if s > 0 and d in pesos:
                    tot += getattr(r, col) * pesos[d] / s
            return tot
        dias = [dict(fecha=str(a_fecha(d * 24.0)), uso_h=round(reparto(o, 'hh', d), 1), parada_h=round(reparto(p, 'horas', d), 1)) for d in range(d1 - 13, d1 + 1)]
        par = _q(con, 'SELECT t_ini, t_fin, causa, planificada, horas FROM gem_parada WHERE maquina=? AND t_fin>? AND t_ini<? ORDER BY t_ini', (k, t - 24 * 30, t + 24))
        tot = _q(con, 'SELECT COUNT(*) n, COALESCE(SUM(t_fin-t_ini),0) h FROM gem_op WHERE politica=? AND recurso=? AND t_fin<=?', (politica, rec, t))
        return dict(maquina=MAQ[k], dias=dias, paradas=json.loads(par.to_json(orient='records')), operaciones=int(tot.n[0]),
                    horas_totales=round(float(tot.h[0]), 0), aviso=AVISO)

    @app.get('/api/gemelo/proyecto/{pid}')
    def proyecto(pid: int, u=Depends(usuario_actual), con=Depends(hist)):
        listo(con)
        p = _q(con, 'SELECT * FROM gem_proyecto WHERE pid=?', (pid,))
        if p.empty:
            raise HTTPException(404)
        res = _q(con, 'SELECT politica, compromiso, fin, tarde, penalidad, costo, lead, intervenciones FROM gem_resultado WHERE pid=? AND replica=(SELECT MIN(replica) FROM gem_resultado) ORDER BY politica', (pid,))
        curvas = {}
        for pol in [r[0] for r in con.execute('SELECT DISTINCT politica FROM gem_estado')]:
            e = _q(con, "SELECT e.t, l.kg FROM gem_estado e JOIN gem_lote l ON l.id=e.lote_id WHERE e.politica=? AND e.pid=? AND e.etapa='ENTREGADO' ORDER BY e.t", (pol, pid))
            if len(e):
                curvas[pol] = dict(t=e.t.round(1).tolist(), kg=e.kg.cumsum().round(0).tolist())
        fases = {}
        for pol in curvas:
            o = _q(con, 'SELECT tipo, MIN(t_ini) a, MAX(t_fin) b, COUNT(*) n, SUM(hh) hh FROM gem_op WHERE politica=? AND pid=? GROUP BY tipo', (pol, pid))
            fases[pol] = json.loads(o.to_json(orient='records'))
        mat = _q(con, 'SELECT politica, paquete, t_pedido, t_llegada, kg FROM gem_material WHERE pid=? ORDER BY politica, paquete', (pid,))
        pal = _q(con, 'SELECT politica, t, tipo, proceso, valor, costo FROM gem_palanca WHERE pid=? AND replica=(SELECT MIN(replica) FROM gem_palanca) ORDER BY t', (pid,))
        return dict(proyecto=json.loads(p.to_json(orient='records'))[0], politicas=json.loads(res.to_json(orient='records')), curvas=curvas,
                    fases=fases, material=json.loads(mat.to_json(orient='records')), palancas=json.loads(pal.to_json(orient='records')), aviso=AVISO)


def _estado(con, politica, T):
    pr = _q(con, 'SELECT pid, cod, nombre, ton, ini, fr, contratista, crew FROM gem_proyecto')
    fin = _q(con, "SELECT pid, fin FROM gem_resultado WHERE politica LIKE ? AND replica=(SELECT MIN(replica) FROM gem_resultado)", (politica + '%',))
    fin_d = {int(r.pid): r.fin for r in fin.itertuples()}
    act = []
    for r in pr.itertuples():
        a = hora(date.fromisoformat(r.ini)) - 24
        b = hora(date.fromisoformat(fin_d.get(r.pid, r.fr))) + 48
        if a <= T <= b:
            act.append(r)
    pids = [int(r.pid) for r in act]
    if not pids:
        return dict(t=T, fecha=str(a_fecha(T)), hora=round(T % 24, 2), proyectos=[], lotes=[], ops=[], movs=[], camiones=[], paradas=[],
                    ing=[], material=[], kpi=dict(proyectos=0, personas=0, kg_en_proceso=0, kg_en_cola=0, stock_kg=0), aviso=AVISO)
    marca = ','.join('?' * len(pids))
    est = _q(con, f'SELECT lote_id, t, etapa, ubic FROM gem_estado WHERE politica=? AND pid IN ({marca}) AND t<=? ORDER BY t',
             (politica, *pids, T))
    ult = est.groupby('lote_id').tail(1).set_index('lote_id') if len(est) else pd.DataFrame(columns=['t', 'etapa', 'ubic'])
    prev = est.groupby('lote_id').nth(-2).set_index('lote_id') if len(est) else pd.DataFrame(columns=['t', 'etapa', 'ubic'])
    lotes = _q(con, f'SELECT id, pid, indice, elemento, perfil, kg, n_piezas, largo, doblez, nc, adicional FROM gem_lote WHERE pid IN ({marca})', tuple(pids))
    lotes = lotes.set_index('id')
    ops = _q(con, 'SELECT id, pid, lote_id, tipo, recurso, estacion, t_ini, t_fin, personas, hh FROM gem_op WHERE politica=? AND t_ini<=? AND t_fin>?',
             (politica, T, T))
    movs = _q(con, 'SELECT pid, lote_id, grua, destino, t_ini, t_fin FROM gem_mov WHERE politica=? AND t_ini<=? AND t_fin>?', (politica, T, T))
    ult_op = _q(con, f'''SELECT o.lote_id, o.recurso, o.estacion FROM gem_op o JOIN (SELECT lote_id, MAX(t_fin) m FROM gem_op
                         WHERE politica=? AND pid IN ({marca}) AND t_fin<=? GROUP BY lote_id) x ON x.lote_id=o.lote_id AND x.m=o.t_fin
                         WHERE o.politica=?''', (politica, *pids, T, politica)).drop_duplicates('lote_id').set_index('lote_id') if True else None
    op_de = {int(r.lote_id): r for r in ops.itertuples() if r.recurso and not str(r.recurso).startswith('grua')}
    mv_de = {int(r.lote_id): r for r in movs.itertuples()}
    out_l = []
    kg_proc = kg_cola = 0.0
    for lid, e in ult.iterrows():
        if lid not in lotes.index:
            continue
        L = lotes.loc[lid]
        etapa, ubic = e.etapa, e.ubic
        if etapa == 'ENTREGADO' and T - e.t > 3:
            continue
        if etapa == 'ESPERA':
            continue
        d = dict(id=int(lid), pid=int(L.pid), indice=int(L.indice), elemento=L.elemento, perfil=L.perfil, kg=round(float(L.kg), 1),
                 n_piezas=int(L.n_piezas), largo=round(float(L.largo), 1), doblez=bool(L.doblez), nc=bool(L.nc), adicional=bool(L.adicional),
                 etapa=etapa, ubic=ubic, desde=round(float(e.t), 2), estado='cola')
        if lid in op_de:
            o = op_de[lid]
            d.update(estado='proceso', recurso=o.recurso, estacion=int(o.estacion), op=o.tipo, personas=int(o.personas),
                     op_ini=round(float(o.t_ini), 2), op_fin=round(float(o.t_fin), 2))
            kg_proc += float(L.kg)
        elif lid in mv_de:
            m = mv_de[lid]
            d.update(estado='grua', grua=int(m.grua), destino=m.destino, mov_ini=round(float(m.t_ini), 3), mov_fin=round(float(m.t_fin), 3))
            if lid in ult_op.index:
                d.update(origen_recurso=ult_op.loc[lid].recurso, origen_estacion=int(ult_op.loc[lid].estacion))
            d['origen_ubic'] = prev.loc[lid].ubic if lid in prev.index else 'patio'
            kg_proc += float(L.kg)
        elif etapa in ('PINTURA', 'DOBLEZ') and ubic == 'externo':
            d['estado'] = 'externo'
        elif etapa == 'ENTREGADO':
            d['estado'] = 'entregado'
        else:
            kg_cola += float(L.kg)
            if lid in ult_op.index and etapa in ('HABILITADO',):
                d.update(origen_recurso=ult_op.loc[lid].recurso, origen_estacion=int(ult_op.loc[lid].estacion))
        out_l.append(d)
    camiones = _q(con, 'SELECT pid, tipo, t_ini, t_fin, kg, n_lotes FROM gem_camion WHERE politica=? AND ((t_ini BETWEEN ? AND ?) OR (t_fin BETWEEN ? AND ?) OR (t_ini<=? AND t_fin>=?))',
                  (politica, T - 1, T + 4, T - 4, T + 1, T, T))
    paradas = _q(con, 'SELECT maquina, t_ini, t_fin, causa, planificada FROM gem_parada WHERE t_ini<=? AND t_fin>?', (T, T))
    ing = _q(con, 'SELECT pid, t_ini, t_fin, personas FROM gem_ing WHERE politica=? AND t_ini<=? AND t_fin>?', (politica, T, T))
    mat = _q(con, f'SELECT pid, paquete, t_pedido, t_llegada, kg FROM gem_material WHERE politica=? AND pid IN ({marca}) AND t_pedido<=?', (politica, *pids, T))
    stock = {}
    for r in mat.itertuples():
        if r.t_llegada <= T:
            stock[r.pid] = stock.get(r.pid, 0.0) + r.kg
    consumido = {}
    for L in lotes.itertuples():
        if L.Index in ult.index and ult.loc[L.Index].etapa not in ('ESPERA', 'HABILITADO') or (L.Index in op_de and op_de[L.Index].tipo in ('sierra', 'cizalla', 'cnc', 'roscado')):
            consumido[L.pid] = consumido.get(L.pid, 0.0) + L.kg
    pedidos = [dict(pid=int(r.pid), paquete=int(r.paquete), kg=round(float(r.kg)), llegada=round(float(r.t_llegada), 1), llegado=bool(r.t_llegada <= T))
               for r in mat.itertuples() if r.t_llegada > T - 24]
    kg_stock = {int(p): max(0.0, stock.get(p, 0.0) - consumido.get(p, 0.0)) for p in pids}
    personas = int(sum(o.personas for o in ops.itertuples() if not str(o.recurso).startswith('maq')))
    personas += int(sum(1 for o in ops.itertuples() if str(o.recurso).startswith('maq')))
    personas += int(ing.personas.sum()) if len(ing) else 0
    proyectos = []
    for r in act:
        ls = [d for d in out_l if d['pid'] == r.pid]
        tot = int(_q(con, 'SELECT n_lotes FROM gem_proyecto WHERE pid=?', (int(r.pid),)).n_lotes[0])
        ent = int(_q(con, "SELECT COUNT(DISTINCT lote_id) n FROM gem_estado WHERE politica=? AND pid=? AND etapa='ENTREGADO' AND t<=?", (politica, int(r.pid), T)).n[0])
        proyectos.append(dict(pid=int(r.pid), cod=None if pd.isna(r.cod) else int(r.cod), nombre=r.nombre, ton=float(r.ton), contratista=r.contratista,
                              crew=json.loads(r.crew), lotes_total=tot, entregados=ent, stock_kg=round(kg_stock.get(int(r.pid), 0.0)),
                              lotes_activos=len(ls)))
    return dict(t=T, fecha=str(a_fecha(T)), hora=round(T % 24, 2), proyectos=proyectos, lotes=out_l, ops=json.loads(ops.to_json(orient='records')),
                movs=json.loads(movs.to_json(orient='records')), camiones=json.loads(camiones.to_json(orient='records')),
                paradas=json.loads(paradas.to_json(orient='records')), ing=json.loads(ing.to_json(orient='records')), material=pedidos,
                kpi=dict(proyectos=len(proyectos), personas=personas, kg_en_proceso=round(kg_proc), kg_en_cola=round(kg_cola),
                         stock_kg=round(sum(kg_stock.values()))), aviso=AVISO)
