import numpy as np

from dss.crp_engine import programar, LAM_DEFECTO, N_PROC

CREW = np.array([3, 1, 1, 1, 1, 1, 2, 8, 8, 8, 4, 5, 3], float)
HH = np.array([[300, 40, 120, 90, 100, 60, 40, 900, 1100, 450, 150, 380, 100]], float)
EXT = np.array([[6.0, 12.0]])


def fin(hh=HH, disp=None, ext=EXT):
    disp = np.ones((300, 4)) if disp is None else disp
    return programar(hh, CREW, disp, ext, lam=LAM_DEFECTO)['fin'][0]


def test_termina_y_es_deterministico():
    assert np.isfinite(fin())
    assert fin() == fin()


def test_mas_horas_no_adelanta_la_fecha():
    assert fin(HH * 1.3) >= fin(HH)


def test_paradas_de_maquina_atrasan():
    disp = np.ones((300, 4)); disp[:, 0] = 0.5          # la sierra cinta trabaja a media capacidad
    assert fin(disp=disp) >= fin()


def test_servicio_externo_mas_lento_atrasa():
    assert fin(ext=EXT * 2) > fin()


def test_replicas_independientes():
    hh = np.vstack([HH, HH * 1.5])
    o = programar(hh, CREW, np.ones((300, 4)), np.vstack([EXT, EXT]), lam=LAM_DEFECTO)
    assert o['fin'][1] > o['fin'][0]
    assert o['fin'][0] == fin()
