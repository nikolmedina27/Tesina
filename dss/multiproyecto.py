"""Motor multi-proyecto: varios proyectos en curso comparten las 4 máquinas de habilitado.

En `crp_engine.programar` la carga de los otros proyectos entra como una fracción fija de capacidad (κ).
Aquí los proyectos se programan **juntos**, día a día, y cada máquina reparte su capacidad diaria por
prioridad: el proyecto con prioridad más alta toma lo que necesita y el siguiente recibe el resto.
Sirve para decidir *entre* proyectos (qué se atiende primero) y para dibujar las colas en la planta 3D.

Supuestos (declararlos): armado, soldeo y limpieza los hacen contratistas con cuadrilla propia por proyecto
(no compiten entre proyectos); los servicios externos tampoco; solo las máquinas son recurso compartido.
"""
import numpy as np

from .crp_engine import N_PROC, PREDS, LAM_DEFECTO, MAQUINAS, EXTERNOS, HORAS_TURNO


def programar_multi(proyectos, disp, turnos_maq=None, lam=LAM_DEFECTO, dias_max=400, guardar_uso=False):
    """Programa R réplicas de P proyectos que comparten las máquinas.

    proyectos  lista de dicts: hh (R, 13), cuadrilla (13,), ext (R, 2), inicio (int: día del calendario común),
               prioridad (número menor = se atiende primero), mult (13, opcional: palancas de gestión),
               avance0 (13, opcional: fracción ya hecha de cada proceso; un proyecto en curso solo programa lo que falta)
    disp       (T, 4) o (R, T, 4) disponibilidad diaria de las máquinas en el calendario común
    turnos_maq (4,) turnos por máquina (1 por defecto; 2 = segundo turno)
    Devuelve una lista (en el orden de entrada) de dicts: fin (R,) día absoluto de término, duracion (R,),
    ini y fin_proc (R, 13) y, si `guardar_uso`, uso (R, T, 4) de horas de máquina que tomó cada proyecto.
    """
    P = len(proyectos)
    R = proyectos[0]['hh'].shape[0]
    disp = np.asarray(disp, float)
    T = disp.shape[-2]
    turnos = np.ones(4) if turnos_maq is None else np.asarray(turnos_maq, float)
    orden = sorted(range(P), key=lambda i: (proyectos[i].get('prioridad', i), i))
    hh = [np.asarray(p['hh'], float) for p in proyectos]
    cap_base = [np.asarray(p['cuadrilla'], float) * HORAS_TURNO * np.asarray(p.get('mult', np.ones(N_PROC)), float)
                for p in proyectos]
    cap_ext = [hh[i][:, EXTERNOS] / np.maximum(np.asarray(proyectos[i]['ext'], float), 1.0) *
               np.asarray(proyectos[i].get('mult', np.ones(N_PROC)), float)[EXTERNOS] for i in range(P)]
    inicio = [int(p['inicio']) for p in proyectos]
    done = [np.zeros((R, N_PROC)) for _ in range(P)]
    frac = [np.zeros((R, N_PROC)) for _ in range(P)]
    ini = [np.full((R, N_PROC), np.nan) for _ in range(P)]
    fin = [np.full((R, N_PROC), np.nan) for _ in range(P)]
    uso = [np.zeros((R, T, 4)) for _ in range(P)] if guardar_uso else None
    for i, p in enumerate(proyectos):                     # proyectos en curso: parten con lo ya avanzado (13,) o (R, 13)
        if p.get('avance0') is None:
            continue
        a0 = np.broadcast_to(np.clip(np.asarray(p['avance0'], float), 0.0, 1.0), (R, N_PROC))
        done[i] = hh[i] * a0
        frac[i] = np.where(hh[i] > 0, a0, 1.0)
        hecho = frac[i] >= 1 - 1e-9
        ini[i] = np.where(hecho | (a0 > 0), float(inicio[i]), ini[i])
        fin[i] = np.where(hecho, float(inicio[i]), fin[i])

    for t in range(min(T, dias_max)):
        d_t = disp[:, t, :] if disp.ndim == 3 else np.broadcast_to(disp[t], (R, 4))
        resto = HORAS_TURNO * turnos[None, :] * d_t                                   # (R, 4) horas de máquina del día
        prev = [f.copy() for f in frac]
        for i in orden:
            if t < inicio[i]:
                continue
            for j in range(N_PROC):
                cap = np.full(R, cap_base[i][j])
                if j in MAQUINAS:
                    k = MAQUINAS.index(j)
                    cap = cap * d_t[:, k]
                elif j in EXTERNOS:
                    cap = cap_ext[i][:, EXTERNOS.index(j)]
                if PREDS[j]:
                    fp = prev[i][:, PREDS[j]].min(axis=1)
                    permitido = np.where(fp >= lam[j] - 1e-12, fp * hh[i][:, j], 0.0)
                else:
                    permitido = hh[i][:, j]
                trabajo = np.clip(np.minimum(cap, permitido - done[i][:, j]), 0.0, None)
                trabajo = np.minimum(trabajo, hh[i][:, j] - done[i][:, j])
                if j in MAQUINAS:
                    k = MAQUINAS.index(j)
                    trabajo = np.minimum(trabajo, resto[:, k])
                    resto[:, k] -= trabajo
                    if uso is not None:
                        uso[i][:, t, k] += trabajo
                nuevo = trabajo > 1e-9
                ini[i][:, j] = np.where(np.isnan(ini[i][:, j]) & nuevo, t, ini[i][:, j])
                done[i][:, j] += trabajo
                frac[i][:, j] = np.where(hh[i][:, j] > 0, done[i][:, j] / hh[i][:, j], 1.0)
                termino = np.isnan(fin[i][:, j]) & (frac[i][:, j] >= 1 - 1e-9)
                fin[i][:, j] = np.where(termino, t + 1, fin[i][:, j])
        if all(not np.isnan(fin[i][:, -1]).any() for i in range(P)):
            break
    salida = []
    for i in range(P):
        f = fin[i][:, -1]
        o = dict(fin=f, duracion=f - inicio[i], ini=ini[i], fin_proc=fin[i])
        if uso is not None:
            o['uso'] = uso[i]
        salida.append(o)
    return salida
