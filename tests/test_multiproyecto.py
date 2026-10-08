import numpy as np

from dss.crp_engine import programar, LAM_DEFECTO, MAQUINAS
from dss.multiproyecto import programar_multi

CREW = np.array([3, 1, 1, 1, 1, 1, 2, 8, 8, 8, 4, 5, 3], float)
HH = np.array([[300, 40, 120, 90, 100, 60, 40, 900, 1100, 450, 150, 380, 100]], float)
EXT = np.array([[6.0, 12.0]])
DISP = np.ones((300, 4))


def _p(inicio=0, prioridad=0, hh=HH):
    return dict(hh=hh, cuadrilla=CREW, ext=EXT, inicio=inicio, prioridad=prioridad)


def test_un_proyecto_equivale_al_motor_individual():
    solo = programar(HH, CREW, DISP, EXT, lam=LAM_DEFECTO)['fin'][0]
    multi = programar_multi([_p()], DISP)[0]['fin'][0]
    assert multi == solo


def test_proyectos_que_comparten_maquinas_se_atrasan_entre_si():
    solo = programar_multi([_p()], DISP)[0]['fin'][0]
    dos = programar_multi([_p(prioridad=0), _p(prioridad=1)], DISP)
    assert dos[0]['fin'][0] == solo                       # el de mayor prioridad no se ve afectado
    assert dos[1]['fin'][0] > solo                        # el otro espera su turno en las máquinas


def test_la_prioridad_decide_quien_termina_primero():
    a, b = programar_multi([_p(prioridad=1), _p(prioridad=0)], DISP)
    assert b['fin'][0] <= a['fin'][0]


def test_proyectos_separados_en_el_tiempo_no_compiten():
    solo = programar_multi([_p()], DISP)[0]['duracion'][0]
    tarde = programar_multi([_p(0), _p(200)], DISP)
    assert tarde[1]['duracion'][0] == solo


def test_segundo_turno_alivia_la_cola():
    base = programar_multi([_p(0, 0), _p(0, 1)], DISP)[1]['fin'][0]
    turno2 = programar_multi([_p(0, 0), _p(0, 1)], DISP, turnos_maq=np.array([2, 2, 2, 2]))[1]['fin'][0]
    assert turno2 <= base


def test_conserva_las_horas_de_maquina():
    o = programar_multi([_p(0, 0), _p(0, 1)], DISP, guardar_uso=True)
    total = o[0]['uso'][0] + o[1]['uso'][0]                 # (T, 4) horas tomadas por ambos
    assert (total <= 8.0 + 1e-9).all()                      # nunca más que el turno de la máquina
    for p in o:
        usado = p['uso'][0].sum(axis=0)
        assert np.allclose(usado, HH[0, MAQUINAS])          # cada proyecto hace todas sus horas de máquina
