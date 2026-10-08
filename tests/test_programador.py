from datetime import date

import numpy as np
import pandas as pd
import pytest

from dss.c3_montecarlo import TAUS, Proyecto
from dss.crp_engine import N_PROC
from dss.programador import Cartera, ProyectoPlan, diferencias, meta_a_fecha, proponer

MAQ = ['Sierra', 'Cizalla', 'CNC', 'Roscadora']
HOY = '2026-10-05'                       # lunes


class CotPrueba:
    """Cotizador mínimo: ratio 30 HH/t repartido entre procesos, φ ≈ 1 con poca dispersión."""

    def __init__(self):
        reparto = np.array([2, 1, 3, 2, 2, 1, 1, 6, 6, 3, 1, 1, 1], float)
        self.rv = pd.DataFrame([30 * reparto / reparto.sum()], index=['Nave'])
        self.par_cuad = {o: (1.0, 0.3) for o in range(1, N_PROC + 1)}
        self.par_ext = {7: (2.0, 0.2), 12: (4.0, 0.2)}
        self.escala = 1.0
        q = np.exp(0.08 * np.array([-1.64, -1.28, -0.67, 0, 0.67, 1.28, 1.64]))
        self.predictor = type('P', (), {'cuantiles': lambda s, proy, taus: (np.tile(q, (N_PROC, 1)), 0.3)})()


def pp(cod, ton, compromiso=None, inicio=HOY, presupuesto=100000, avance0=None, nuevo=False, i=None):
    return ProyectoPlan(id=i, codigo=cod, proy=Proyecto('Nave', ton, inicio, presupuesto), compromiso=compromiso, avance0=avance0, nuevo=nuevo)


def test_meta_mensual():
    assert meta_a_fecha('2027-07') == '2027-07-31'          # sábado: la planta trabaja de lunes a sábado
    assert meta_a_fecha('2026-08') == '2026-08-31' and meta_a_fecha('') is None and meta_a_fecha('2026-12-15') == '2026-12-15'


def test_capacidad_de_maquinas_nunca_se_excede():
    c = Cartera(CotPrueba(), [pp('A', 60), pp('B', 40), pp('C', 30)], HOY, [], MAQ, [15, 15, 15, 15], R=40)
    o = c.simular([0, 1, 2], guardar_uso=True)
    uso = sum(x['uso'] for x in o)                           # (R, T, 4) horas de máquina tomadas por todos
    assert np.all(uso <= 8.0 * c.disp() + 1e-6)


def test_la_prioridad_decide_quien_termina_antes():
    c = Cartera(CotPrueba(), [pp('A', 60), pp('B', 60)], HOY, [], MAQ, [40, 40, 40, 40], R=40)
    a_primero, b_primero = c.simular([0, 1]), c.simular([1, 0])
    assert np.median(a_primero[0]['fin']) < np.median(b_primero[0]['fin'])
    assert np.median(b_primero[1]['fin']) < np.median(a_primero[1]['fin'])


def test_avance_y_preventivos():
    hecho = pp('H', 50, avance0=np.ones(N_PROC))
    c = Cartera(CotPrueba(), [hecho, pp('A', 50)], HOY, [], MAQ, [40, 40, 40, 40], R=30)
    o = c.simular([0, 1])
    assert np.all(o[0]['fin'] == 0)                           # ya terminado: no ocupa la planta
    # un preventivo largo en las 4 máquinas el primer día no adelanta a nadie
    prev = [dict(maquina=m, programada_para=HOY, duracion_h=8) for m in MAQ]
    c2 = Cartera(CotPrueba(), [pp('A', 50)], HOY, prev, MAQ, [40, 40, 40, 40], R=30)
    c3 = Cartera(CotPrueba(), [pp('A', 50)], HOY, [], MAQ, [40, 40, 40, 40], R=30)
    assert np.all(c2.simular([0])[0]['fin'] >= c3.simular([0])[0]['fin'])


def test_propuesta_regla_penalidad_y_proyecto_nuevo():
    cot = CotPrueba()
    cart = [pp('CHICO', 20, compromiso='2027-06-30', presupuesto=50000, i=1),
            pp('URGENTE', 60, compromiso='2026-11-20', presupuesto=400000, i=2),
            pp('NUEVO', 30, compromiso=meta_a_fecha('2027-02'), nuevo=True)]
    r = proponer(cot, cart, HOY, [], MAQ, [20, 20, 20, 20], R=60)
    assert r['proyectos'][0]['codigo'] == 'URGENTE'            # el de mayor penalidad en riesgo va primero
    nuevo = next(x for x in r['proyectos'] if x['nuevo'])
    assert nuevo['inicio_mas_tardio'] and HOY <= nuevo['inicio_mas_tardio'] <= '2027-02-27'
    assert all(len(c['horas']) == len(r['fechas']) for c in r['carga'])
    assert {x['codigo'] for x in r['proyectos']} == {'CHICO', 'URGENTE', 'NUEVO'}
    # diferencias: si se aprueba y luego se agrega un proyecto, aparece como nuevo
    r2 = proponer(cot, cart + [pp('OTRO', 50, compromiso='2027-01-15', i=9)], HOY, [], MAQ, [20, 20, 20, 20], R=60)
    assert any(d.get('cambio') == 'nuevo en el plan' and d['codigo'] == 'OTRO' for d in diferencias(r, r2))
