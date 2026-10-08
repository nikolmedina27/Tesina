import sqlite3

import numpy as np
import pytest

from dss.datos import DB
from dss.simulador_planta import layout, lotes_y_etapas, ETAPAS, a_idx, de_idx


def test_layout_dentro_del_predio_y_con_las_4_maquinas():
    E = layout()
    nombres = [e['nombre'] for e in E]
    assert len(nombres) == len(set(nombres))
    for e in E:
        if e['tipo'] == 'terreno':
            continue
        assert 0 <= e['x'] - e['ancho'] / 2 and e['x'] + e['ancho'] / 2 <= 100 + 1e-9, e['nombre']
        assert 0 <= e['z'] - e['largo'] / 2 and e['z'] + e['largo'] / 2 <= 50 + 1e-9, e['nombre']
    assert sum(e['tipo'] == 'maquina' for e in E) == 4
    assert sum(e['tipo'] == 'mesa' for e in E) >= 6 and sum(e['tipo'] == 'puesto' for e in E) >= 8
    assert next(e for e in E if e['tipo'] == 'terreno')['ancho'] * next(e for e in E if e['tipo'] == 'terreno')['largo'] == 5000


def test_maquinas_no_se_solapan_entre_si():
    maq = sorted((e for e in layout() if e['tipo'] == 'maquina'), key=lambda e: e['x'])
    for a, b in zip(maq, maq[1:]):
        assert a['x'] + a['ancho'] / 2 <= b['x'] - b['ancho'] / 2, (a['nombre'], b['nombre'])


def test_calendario_ida_y_vuelta():
    for f in ['2021-02-19', '2024-12-28', '2026-09-25']:
        assert de_idx(a_idx(f)) == f
    assert a_idx('2021-02-22') - a_idx('2021-02-20') == 1          # sábado → lunes: no hay domingo


def _ventanas():
    v, t = {}, 0
    for o in range(1, 14):
        v[o] = (t, t + 8)
        t += 5                                                      # los procesos se solapan
    return v


def test_lotes_conservan_kg_y_respetan_ventanas_y_orden():
    v = _ventanas()
    lotes, etapas, ventanas_etapa = lotes_y_etapas(100.0, 800, v, np.random.default_rng(1))
    assert sum(l[0] for l in lotes) == pytest.approx(100_000.0)
    lim = {n: (min(v[p][0] for p in ps), max(v[p][1] for p in ps)) for n, ps in ETAPAS}
    for k, fases in etapas.items():
        previo = -1
        for nombre, orden, ini, fin in fases:
            assert lim[nombre][0] <= ini <= fin <= lim[nombre][1]
            assert ini >= previo                                     # no empieza una etapa antes de terminar la anterior
            previo = fin
        assert [f[1] for f in fases] == list(range(len(ETAPAS)))


@pytest.mark.skipif(not DB.exists(), reason='requiere data/steelser.db')
def test_bd_planta_consistente():
    con = sqlite3.connect(DB)
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='sim_lote'").fetchone():
        pytest.skip('falta py -m dss.simulador_planta')
    m = con.execute('SELECT MIN(id) FROM sim_mundo').fetchone()[0]
    hh_a = con.execute('SELECT SUM(hh) FROM sim_asignacion WHERE mundo_id=?', (m,)).fetchone()[0]
    hh_r = con.execute('SELECT SUM(hh_real) FROM sim_proyecto_proceso WHERE mundo_id=?', (m,)).fetchone()[0]
    assert hh_a == pytest.approx(hh_r, rel=1e-6)                      # lo asignado por día suma las HH simuladas
    kg_l, kg_p = con.execute('''SELECT SUM(l.kg), (SELECT SUM(toneladas)*1000 FROM proyecto WHERE en_muestra=1)
                                FROM sim_lote l WHERE mundo_id=?''', (m,)).fetchone()
    assert kg_l == pytest.approx(kg_p, rel=1e-6)
    assert con.execute('SELECT COUNT(*) FROM sim_material_lote WHERE f_consumo < f_ingreso').fetchone()[0] == 0
    assert con.execute('SELECT COUNT(*) FROM sim_planta_elemento WHERE origen != "SIMULADO"').fetchone()[0] == 0
