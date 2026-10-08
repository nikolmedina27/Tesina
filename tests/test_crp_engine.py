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


def test_avance_inicial_adelanta_y_cero_equivale_a_nada():
    hecho = np.zeros(N_PROC); hecho[:8] = 1.0                       # todo hasta el armado ya terminó
    base = fin()
    desde_avance = programar(HH, CREW, np.ones((300, 4)), EXT, lam=LAM_DEFECTO, avance0=hecho)['fin'][0]
    assert desde_avance < base
    cero = programar(HH, CREW, np.ones((300, 4)), EXT, lam=LAM_DEFECTO, avance0=np.zeros(N_PROC))['fin'][0]
    assert cero == base
    # lo que queda por hacer: soldeo + limpieza + despacho + pintura externa, sin esperas artificiales por lo ya hecho
    resto = HH.copy(); resto[0, :8] = 1e-6
    assert desde_avance <= programar(resto, CREW, np.ones((300, 4)), EXT, lam=LAM_DEFECTO)['fin'][0]


def test_proyecto_ya_terminado_tiene_fin_cero():
    o = programar(HH, CREW, np.ones((300, 4)), EXT, lam=LAM_DEFECTO, avance0=np.ones(N_PROC))
    assert o['fin'][0] == 0
