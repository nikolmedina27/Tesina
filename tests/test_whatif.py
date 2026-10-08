import numpy as np
import pytest

from dss.crp_engine import programar, LAM_DEFECTO, N_PROC
from dss.datos import DB
from dss.whatif import Palanca, candidatas, multiplicadores, costo_palancas, COSTOS, CONTRATISTAS

CREW = np.array([3, 1, 1, 1, 1, 1, 2, 8, 8, 8, 4, 5, 3], float)
HH = np.array([[300, 40, 120, 90, 100, 60, 40, 900, 1100, 450, 150, 380, 100]], float)
EXT = np.array([[6.0, 12.0]])


def fin(**kw):
    return programar(HH, CREW, np.ones((300, 4)), EXT, lam=LAM_DEFECTO, **kw)['fin'][0]


def test_multiplicadores_de_cada_palanca():
    m = multiplicadores([Palanca('personas', 8, 2), Palanca('turno2', 2), Palanca('expeditar', 6)], CREW)
    assert m[8] == pytest.approx(10 / 8) and m[2] == 2.0 and m[6] == COSTOS['mult_expeditar']
    assert m[0] == 1.0 and len(m) == N_PROC


def test_mas_capacidad_en_el_cuello_de_botella_adelanta():
    base = fin()
    m = np.ones(N_PROC); m[8] = 2.0                         # soldeo, el cuello de botella de este caso
    assert fin(mult=m) < base


def test_palanca_desde_un_dia_no_cambia_lo_anterior():
    m = np.full(N_PROC, 2.0)
    assert fin(mult=m, mult_desde=10_000) == fin()          # nunca llega a aplicarse
    assert fin(mult=m, mult_desde=0) < fin(mult=m, mult_desde=20) <= fin()


def test_snapshot_devuelve_el_avance_al_dia_pedido():
    o = programar(HH, CREW, np.ones((300, 4)), EXT, lam=LAM_DEFECTO, snapshot=[0, 15, 5000])
    assert (o['estado'][0] == 0).all()
    assert (o['estado'][15] >= 0).all() and o['estado'][15].max() > 0
    assert (o['estado'][5000] >= 1 - 1e-9).all()            # ya había terminado


def test_costos_proporcionales_y_no_negativos():
    crew = CREW
    dias = np.full(N_PROC, 10.0)
    hh_prom = HH[0]
    c1 = costo_palancas([Palanca('personas', 0, 1)], crew, hh_prom, dias, hh_prom.sum())
    c2 = costo_palancas([Palanca('personas', 0, 2)], crew, hh_prom, dias, hh_prom.sum())
    assert 0 < c1 < c2
    assert costo_palancas([], crew, hh_prom, dias, hh_prom.sum()) == 0.0
    assert costo_palancas([Palanca('turno2', 2)], crew, hh_prom, dias, hh_prom.sum(), escala=2.0) == \
        pytest.approx(2 * costo_palancas([Palanca('turno2', 2)], crew, hh_prom, dias, hh_prom.sum()))
    # a un contratista (pago por kg) acelerar le cuesta solo la prima, no sus jornales
    assert costo_palancas([Palanca('personas', CONTRATISTAS[0], 1)], crew, hh_prom, dias, hh_prom.sum()) < \
        costo_palancas([Palanca('personas', 0, 1)], crew, hh_prom, dias, hh_prom.sum())


def test_hay_candidatas_para_todos_los_tipos():
    tipos = {p.tipo for p in candidatas()}
    assert tipos == {'personas', 'turno2', 'horas_extra', 'expeditar'}


@pytest.mark.skipif(not DB.exists(), reason='requiere data/steelser.db (build_db + simulador)')
def test_busqueda_encuentra_mejora_con_semillas_comunes():
    from dss.c2_modelo import dataset, PhiQRF
    from dss.c3_montecarlo import Cotizador, Proyecto
    from dss.datos import conectar
    from dss.whatif import buscar
    con = conectar()
    cot = Cotizador(con, PhiQRF().fit(dataset(con, 2)))
    p = Proyecto(tipo='Planta industrial / minería', ton=120, inicio='2026-03-02')
    fo = str(cot.cotizar(p, R=400, semilla=1).fecha_alpha(0.5))
    out, base = buscar(cot, p, fo, R=400, semilla=1)
    assert out[0].total <= base.total                       # el mejor nunca es peor que no hacer nada
    otra, _ = buscar(cot, p, fo, R=400, semilla=1)
    assert [e.a_dict() for e in otra[:3]] == [e.a_dict() for e in out[:3]]     # reproducible con la semilla
