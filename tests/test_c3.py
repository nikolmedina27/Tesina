import numpy as np

from dss.c3_montecarlo import muestrear_phi, muestrear_disp, alpha_optimo, Resultado, Proyecto, TAUS


def _q(sesgo=1.0, s=0.1):
    from scipy.stats import norm
    return np.tile(sesgo * np.exp(s * norm.ppf(TAUS)), (13, 1))


def test_muestreo_respeta_cuantiles():
    phi = muestrear_phi(_q(1.2), 0.5, 20000, np.random.default_rng(0))
    assert abs(np.median(phi) - 1.2) < 0.01
    q = np.quantile(phi[:, 0], [0.1, 0.9])
    assert abs(q[0] - 1.2 * np.exp(0.1 * -1.2816)) < 0.01 and abs(q[1] - 1.2 * np.exp(0.1 * 1.2816)) < 0.01


def test_rho_induce_correlacion_entre_procesos():
    alto = muestrear_phi(_q(), 0.8, 20000, np.random.default_rng(1))
    bajo = muestrear_phi(_q(), 0.0, 20000, np.random.default_rng(1))
    assert np.corrcoef(alto[:, 0], alto[:, 5])[0, 1] > 0.6
    assert abs(np.corrcoef(bajo[:, 0], bajo[:, 5])[0, 1]) < 0.05


def test_disponibilidad_plausible():
    d = muestrear_disp(400, 200, np.array([12.0, 9.0, 15.0, 25.0]), np.random.default_rng(2))
    assert d.shape == (400, 200, 4)
    m = d.mean(axis=(0, 1))
    assert (m > 0.8).all() and (m < 0.99).all()
    assert m[1] < m[3]                      # la máquina con más fallas tiene menor disponibilidad


def test_alpha_optimo():
    assert 0.5 <= alpha_optimo() <= 0.95
    assert alpha_optimo(prob_pierde_por_dia=0.02) < alpha_optimo(prob_pierde_por_dia=0.002)   # plazo largo cuesta más -> α menor
    assert alpha_optimo(p=0.02) > alpha_optimo(p=0.005)                                       # penalidad más alta -> α mayor


def test_resultado_cuantiles_y_penalidad():
    f = np.datetime64('2026-01-01') + np.arange(100)
    r = Resultado(Proyecto('x', 10, '2026-01-01', presupuesto=1000.0), np.datetime64('2026-01-01'), f, np.arange(100), np.zeros((100, 13)))
    assert r.fecha_alpha(0.5) <= r.fecha_alpha(0.9)
    assert r.prob_cumplir(r.fecha_alpha(0.8)) >= 0.8
    assert r.penalidad_esperada(f[-1]) == 0.0
    assert r.penalidad_esperada(f[0]) > r.penalidad_esperada(f[50]) > 0
