"""Motor de programación día a día (CRP de carga finita), vectorizado por réplica.

Es el núcleo de C3: lo usa el Monte Carlo del cotizador y el simulador de datos.
Un "día" es un día laborable (lunes a sábado). Un proceso avanza cada día hasta la
capacidad del centro (HH/día) y solo puede ir hasta la fracción de avance de sus
predecesores; empieza cuando estos llegan a la fracción de solape `LAM`.
"""
import numpy as np

N_PROC = 13
WEEKMASK = '1111110'          # lunes a sábado
HORAS_TURNO = 8.0

# predecesores por proceso (índice 0-based; proceso n = índice n-1)
PREDS = {0: [], 1: [0], 2: [1], 3: [1], 4: [1], 5: [1], 6: [4], 7: [2, 3, 4, 6],
         8: [7], 9: [8], 10: [9], 11: [10], 12: [11, 5]}
# fracción de avance del predecesor para poder empezar (solape inicio-inicio).
# Calibrado por grilla contra el plazo planificado real de los 25 proyectos:
# error medio 2.0 días laborables, sesgo -0.1 (scripts/calibrar_solapes.py).
LAM_DEFECTO = np.array([0, .6, .6, .6, .6, .6, .6, .8, .8, .6, 1., 1., 1.])
MAQUINAS = [2, 3, 4, 5]       # procesos 3-6 usan sierra, cizalla, mesa CNC, roscadora
EXTERNOS = [6, 11]            # doblez y granallado/pintura: plazo de calendario


def programar(hh, cuadrilla, disp, ext_dias, lam=LAM_DEFECTO, dias_max=400, mult=None, mult_desde=0, snapshot=None, avance0=None):
    """Programa R réplicas de un proyecto.

    hh        (R, 13)  horas-hombre por proceso
    cuadrilla (13,)    personas por proceso (1 en máquinas)
    disp      (T, 4) o (R, T, 4)  disponibilidad diaria de las 4 máquinas (1 = sin paradas)
    ext_dias  (R, 2)   plazo en días de los 2 servicios externos
    mult      (13,)    palancas de gestión: multiplica la capacidad de cada proceso (máquina, cuadrilla o
                       velocidad del servicio externo) desde el día `mult_desde` (0 = desde el inicio)
    snapshot  lista de días: devuelve en 'estado' la fracción de avance (R, 13) al comenzar cada uno
    avance0   (13,) fracción de cada proceso que ya está hecha al empezar (re-pronóstico de un proyecto en curso)
    Devuelve dict con fin (R,) en días laborables transcurridos, ini y fin por proceso (R, 13).
    """
    hh = np.asarray(hh, float)
    R = hh.shape[0]
    disp = np.asarray(disp, float)
    T = disp.shape[-2]
    done = np.zeros((R, N_PROC))
    ini = np.full((R, N_PROC), np.nan)
    fin = np.full((R, N_PROC), np.nan)
    cap_base = cuadrilla * HORAS_TURNO                               # (13,)
    cap_ext = hh[:, EXTERNOS] / np.maximum(ext_dias, 1.0)            # (R, 2)
    frac = np.zeros((R, N_PROC))
    if avance0 is not None:
        a0 = np.clip(np.asarray(avance0, float), 0.0, 1.0)
        done += hh * a0
        frac[:] = np.where(hh > 0, done / np.where(hh > 0, hh, 1.0), 1.0)
        ini[:, a0 > 0] = 0
        fin[:, a0 >= 1 - 1e-9] = 0
    mult = np.ones(N_PROC) if mult is None else np.asarray(mult, float)
    estado = {}
    for t in range(min(T, dias_max)):
        prev = frac.copy()
        if snapshot is not None and t in snapshot:
            estado[t] = prev.copy()
        m_t = mult if t >= mult_desde else np.ones(N_PROC)
        d_t = disp[..., t, :] if disp.ndim == 3 else disp[t][None, :]
        for j in range(N_PROC):
            cap = np.full(R, cap_base[j] * m_t[j])
            if j in MAQUINAS:
                cap = cap_base[j] * m_t[j] * d_t[:, MAQUINAS.index(j)] if d_t.shape[0] == R else \
                    np.full(R, cap_base[j] * m_t[j] * d_t[0, MAQUINAS.index(j)])
            elif j in EXTERNOS:
                cap = cap_ext[:, EXTERNOS.index(j)] * m_t[j]
            if PREDS[j]:
                fp = prev[:, PREDS[j]].min(axis=1)
                permitido = np.where(fp >= lam[j] - 1e-12, fp * hh[:, j], 0.0)
            else:
                permitido = hh[:, j]
            trabajo = np.clip(np.minimum(cap, permitido - done[:, j]), 0.0, None)
            trabajo = np.minimum(trabajo, hh[:, j] - done[:, j])
            nuevo = trabajo > 1e-9
            ini[:, j] = np.where(np.isnan(ini[:, j]) & nuevo, t, ini[:, j])
            done[:, j] += trabajo
            frac[:, j] = np.where(hh[:, j] > 0, done[:, j] / hh[:, j], 1.0)
            termino = np.isnan(fin[:, j]) & (frac[:, j] >= 1 - 1e-9)
            fin[:, j] = np.where(termino, t + 1, fin[:, j])
        if not np.isnan(fin[:, -1]).any():
            break
    if snapshot is not None:
        for t in snapshot:
            estado.setdefault(t, frac.copy())      # el proyecto ya había terminado antes de ese día
    return {'fin': fin[:, -1], 'ini': ini, 'fin_proc': fin, 'estado': estado}


def dias_laborables(inicio, n):
    """Fechas (datetime64[D]) de los n primeros días laborables desde `inicio` (inclusive)."""
    inicio = np.datetime64(inicio, 'D')
    base = np.busday_offset(inicio, 0, roll='forward', weekmask=WEEKMASK)
    return np.busday_offset(base, np.arange(n), weekmask=WEEKMASK)


def n_dias_laborables(inicio, fin):
    """Días laborables en [inicio, fin] (lunes a sábado)."""
    return int(np.busday_count(np.datetime64(inicio, 'D'),
                               np.datetime64(fin, 'D') + np.timedelta64(1, 'D'), weekmask=WEEKMASK))
