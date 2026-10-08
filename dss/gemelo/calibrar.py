"""Calibración del gemelo: un factor de ritmo por proyecto para que, con la política «como se hizo», el gemelo
reproduzca la historia real (Tabla 3).

Objetivo de cada proyecto (fecha en que queda listo para entregar):
  - si se atrasó: su fecha real de entrega;
  - si cumplió: su fecha planificada menos una holgura SIMULADA de 0 a 6 días laborables (no se sabe cuánto antes
    estuvo listo; la entrega real se pacta cerca de la fecha comprometida).
Así, con la fecha del cotizador, el gemelo da el mismo cumplimiento y los mismos atrasos que la realidad.

El factor escala las HH del proyecto y, con su raíz, los plazos de proveedores y servicios externos. Se itera porque
los proyectos comparten máquinas y grúas: cambiar uno mueve a los demás.
"""
import bisect

import numpy as np

from .calendario import LABORABLES, fecha
from .motor import Gemelo

L = [d.toordinal() for d in LABORABLES]


def dias_lab(a, b):
    return bisect.bisect_right(L, b.toordinal()) - bisect.bisect_left(L, a.toordinal())


def objetivo(p, semilla=2026):
    """Fecha objetivo (ordinal de día laborable) del proyecto para la calibración."""
    if p.fr > p.fp:
        return p.fr
    rng = np.random.default_rng([semilla, p.pid, 7])
    holgura = int(rng.integers(0, 7))
    i = bisect.bisect_right(L, p.fp.toordinal()) - 1 - holgura
    return LABORABLES[max(i, bisect.bisect_left(L, p.ini.toordinal()) + 5)]


def calibrar(proyectos, paradas, iteraciones=30, lim=(0.15, 10.0), verbose=False):
    """Devuelve (factores {pid: f}, error medio absoluto en días laborables, historial, errores por pid)."""
    f = {p.pid: 1.4 for p in proyectos}
    obj = {p.pid: objetivo(p) for p in proyectos}
    mejor = (1e9, dict(f), {})
    hist = []
    for it in range(iteraciones):
        usado = dict(f)
        r = Gemelo(proyectos, paradas, eficiencia=usado).correr()
        err = {}
        for p in proyectos:
            meta = dias_lab(p.ini, obj[p.pid])
            sim = dias_lab(p.ini, fecha(r.fin[p.pid]))
            err[p.pid] = sim - meta
            paso = 1.0 if it < iteraciones // 2 else 0.6
            f[p.pid] = float(np.clip(f[p.pid] * (meta / max(sim, 1)) ** paso, *lim))
        mae = float(np.mean(np.abs(list(err.values()))))
        hist.append(mae)
        if mae < mejor[0]:
            mejor = (mae, usado, dict(err))
        if verbose:
            print(f'iteración {it + 1}: error medio {mae:.2f} d, máx {max(np.abs(list(err.values())))} d')
        if mae < 0.3:
            break
    return mejor[1], mejor[0], hist, mejor[2]
