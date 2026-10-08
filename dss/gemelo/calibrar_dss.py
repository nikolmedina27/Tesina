"""Calibración del planificador del DSS (CRP diario) contra el tareo del gemelo.

El CRP supone que un proceso empieza cuando su predecesor llega a una fracción λ de avance. El gemelo hace fluir los
lotes por paquetes: apenas llega el primer material arranca el habilitado, y armado y soldeo corren en paralelo. Con los
λ de los datos originales el CRP sobreestima mucho el plazo. Se ajustan por búsqueda por coordenadas usando SOLO los
proyectos de calibración (los 13 fuera de la muestra de 25): con las HH que registró el tareo, las esperas de compras e
ingeniería y los plazos de servicios externos observados, se busca el vector λ con el que el CRP reproduce la duración
real de esos proyectos. Los 25 de la muestra no intervienen, así que la evaluación no se contamina.
"""
import numpy as np

from ..crp_engine import programar, LAM_DEFECTO
from .calendario import fecha
from .calibrar import dias_lab

GRUPOS = {                       # λ compartido por grupo de procesos (índices 0-based)
    'hab': [2, 3, 4, 5],         # habilitado arranca con la llegada de material
    'doblez': [6],
    'armado': [7],
    'soldeo': [8],
    'limpieza': [9],
    'pintura': [10, 11],
    'obra': [12],
    'compra': [1],
}
REJILLA = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


def _lam(v):
    lam = LAM_DEFECTO.copy()
    for g, idx in GRUPOS.items():
        lam[idx] = v[g]
    return lam


def entradas(sim, res, pid):
    """Entradas del CRP para un proyecto ya simulado, tal como las dejaría el registro de la planta."""
    p = sim.P[pid]
    hh = p.hh.copy()
    for j in (3, 4, 5, 6, 8, 9, 10):
        hh[j - 1] = sim.hh_hecho.get((pid, j), p.hh[j - 1])
    pk = [x[2] for x in res.paquetes if x[0] == pid]
    mt = [x for x in res.material if x[0] == pid]
    ing = dias_lab(p.ini, fecha(max(pk)))
    comp = dias_lab(fecha(min(x[2] for x in mt)), fecha(max(x[3] for x in mt)))
    hh[0] = ing * 8.0 * p.crew[0]
    hh[1] = comp * 8.0 * p.crew[1]
    ext = []
    for tipo, j in (('doblez', 7), ('pintura', 12)):
        c = [(x[3] - x[2]) / 24.0 * (5.0 / 6.0) for x in res.camiones if x[0] == pid and x[1] == tipo]
        ext.append(max(1.0, float(np.mean(c)) if c else p.hh[j - 1] / 8.0 / max(p.crew[j - 1], 1)))
    return hh, p.crew, np.array(ext)


def error(v, casos, disp):
    lam = _lam(v)
    e = []
    for hh, crew, ext, real in casos:
        o = programar(hh[None, :], crew, disp, ext[None, :], lam=lam)
        e.append(float(o['fin'][0]) - real)
    return np.array(e)


def calibrar_crp(sim, res, calibracion, disp_media=0.9, rondas=3):
    """Devuelve (λ por grupo, errores antes, errores después). `calibracion`: pids de los proyectos de calibración."""
    disp = np.full((400, 4), disp_media)
    casos = []
    for pid in calibracion:
        hh, crew, ext = entradas(sim, res, pid)
        casos.append((hh, crew, ext, dias_lab(sim.P[pid].ini, fecha(res.fin[pid]))))
    v = {'hab': 0.6, 'doblez': 0.6, 'armado': 0.8, 'soldeo': 0.8, 'limpieza': 1.0, 'pintura': 1.0, 'obra': 1.0, 'compra': 0.6}
    antes = error(v, casos, disp)
    for _ in range(rondas):
        for g in GRUPOS:
            mejor = (1e9, v[g])
            for x in REJILLA:
                w = dict(v, **{g: x})
                m = np.abs(error(w, casos, disp)).mean() + 0.02 * abs(x - v[g])
                if m < mejor[0]:
                    mejor = (m, x)
            v[g] = mejor[1]
    return v, antes, error(v, casos, disp)


def vector(v):
    return _lam(v)
