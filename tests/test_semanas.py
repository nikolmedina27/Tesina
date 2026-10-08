from datetime import date, timedelta

import pytest

from plataforma.avance import ETAPAS, curva_s, error_orden_etapas, semanas

HOY = date.today()
D = lambda n: (HOY - timedelta(days=n)).isoformat()
PROG = [(0, 5), (4, 7), (7, 12), (7, 11), (7, 12), (7, 9), (10, 14), (11, 20), (13, 24), (18, 26), (26, 28), (28, 36), (36, 38)]


def curva():
    piezas = [dict(peso_total=1000, f_habilitado=D(9), f_armado=D(6), f_soldeo=D(2), f_liberacion=None, f_granallado=None,
                   f_pintura=None, f_despacho=None),
              dict(peso_total=500, **{e[0]: D(4) for e in ETAPAS})]
    tareo = [dict(fecha=D(k), hh=16) for k in (1, 3, 8, 10)]
    return curva_s(D(20), PROG, [10.0] * 13, piezas, tareo, HOY.isoformat(), 1500)


def test_semanas_cuadran_con_la_curva():
    c = curva()
    s = semanas(c)
    assert all(date.fromisoformat(x['inicio']).weekday() == 0 for x in s)             # cada ciclo empieza en lunes
    assert sum(x['plan_kg'] for x in s) == pytest.approx(c['plan_kg'][-1], abs=0.5)
    assert sum(x['plan_hh'] for x in s) == pytest.approx(130, abs=0.5)
    assert sum(x['real_hh'] or 0 for x in s) == pytest.approx(64)                       # todo el tareo, también la semana en curso
    assert sum(x['real_kg'] or 0 for x in s) == pytest.approx(1000 * 0.525 + 500, abs=0.5)
    assert sum(x['en_curso'] for x in s) == 1
    futuras = [x for x in s if x['inicio'] > c['hoy']]
    assert all(x['real_hh'] is None and x['spi_hh'] is None for x in futuras)


def test_orden_de_etapas():
    ok = dict(f_habilitado='2026-01-02', f_armado='2026-01-03', f_soldeo='2026-01-05', f_despacho='2026-01-20')
    assert error_orden_etapas(ok) is None
    assert 'anterior' in error_orden_etapas(ok | dict(f_armado='2026-01-01'))
    assert 'despacho' in error_orden_etapas(ok | dict(f_pintura='2026-01-25'))
    assert error_orden_etapas(dict(f_granallado='2026-01-01', f_liberacion='2026-01-04')) is None   # recubrimiento puede ir en paralelo
