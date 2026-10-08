import sqlite3

import numpy as np
import pytest

from dss.datos import DB
from dss.retrospectivo import desplazar, dias_cal, POLITICAS


def test_desplazar_cuenta_dias_laborables_de_lunes_a_sabado():
    assert desplazar('2026-03-06', 1) == '2026-03-07'            # viernes → sábado
    assert desplazar('2026-03-07', 1) == '2026-03-09'            # sábado → lunes (no hay domingo)
    assert desplazar('2026-03-09', -1) == '2026-03-07'
    assert desplazar('2026-03-09', 0) == '2026-03-09'
    assert desplazar('2026-03-08', 0) == '2026-03-07'            # un domingo cae al sábado anterior


def test_dias_cal():
    assert dias_cal('2026-01-01', '2026-01-31') == 30


def test_seis_politicas():
    assert len(POLITICAS) == 6 and POLITICAS[0].startswith('A0') and POLITICAS[-1].startswith('A5')


def _bd_lista():
    if not DB.exists():
        return False
    con = sqlite3.connect(DB)
    ok = bool(con.execute("SELECT 1 FROM sqlite_master WHERE name='sim_proyecto_proceso'").fetchone()) and \
        con.execute('SELECT COUNT(*) FROM sim_proyecto_proceso').fetchone()[0] > 0 and \
        con.execute('SELECT COUNT(DISTINCT toneladas) FROM proyecto WHERE en_muestra=1').fetchone()[0] > 1
    con.close()
    return ok


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con la muestra y el mundo simulado (build_db / reconstruir_muestra + simulador)')
def test_replay_reproduce_la_duracion_real_y_las_palancas_adelantan():
    from dss.datos import conectar
    from dss.retrospectivo import Retro
    from dss.whatif import Palanca, multiplicadores
    con = conectar()
    r = Retro(con, 2)
    errores = []
    for pid in list(r.P.index)[:8]:
        d = r.datos(pid)
        errores.append(abs(r.replay(pid)['fin'] - d.n_real))
    assert np.mean(errores) <= 2.0 and max(errores) <= 6        # la verdad simulada reproduce los plazos reales
    pid = list(r.P.index)[10]
    d = r.datos(pid)
    base = r.replay(pid)['fin']
    m = multiplicadores([Palanca('personas', 9, 2), Palanca('personas', 8, 2)], d.crew)
    assert r.replay(pid, mult=m)['fin'] <= base                 # más gente nunca atrasa
    assert r.replay(pid, mult=m, mult_desde=10_000)['fin'] == base     # una decisión que nunca se aplica no cambia nada
    con.close()


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el mundo simulado y la planta simulada')
def test_estado_de_la_planta_es_consistente():
    from plataforma.planta import _estado
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='sim_lote'").fetchone():
        pytest.skip('falta py -m dss.simulador_planta')
    ini = con.execute('SELECT fecha_inicio FROM proyecto WHERE en_muestra=1 ORDER BY fecha_inicio LIMIT 1 OFFSET 10').fetchone()[0]
    fecha = str(np.busday_offset(np.datetime64(ini, 'D'), 12, roll='forward', weekmask='1111110'))
    e = _estado(con, DB, 2, fecha, None, None)
    assert e['kpi']['personas'] == sum(s['personas'] for s in e['estaciones'])
    assert all(l['estado'] in ('ACOPIO', 'EN_PROCESO', 'EN_COLA', 'DESPACHADO') for l in e['lotes'])
    assert all(l['ubicacion'] is not None for l in e['lotes'] if l['estado'] != 'DESPACHADO')
    assert all(m['f_ingreso'] <= fecha <= m['f_consumo'] for m in e['material'])
    assert len(e['proyectos']) >= 1
    con.close()
