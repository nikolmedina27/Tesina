"""Acceso a la BD y datos de referencia comunes (ratio vigente, cuadrillas, carga del taller)."""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from .crp_engine import N_PROC, MAQUINAS, WEEKMASK, n_dias_laborables

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / 'data' / 'steelser.db'
TIPOS = ['Nave industrial / packing / cobertura', 'Planta industrial / minería',
         'Edificación / infraestructura', 'Mezzanine / plataformas / oficinas']
TON_IMPUTADA = 93.0            # toneladas de los 13 proyectos fuera de la muestra (media de la muestra)
FRAC_VENTANA = (0.20, 0.50)    # el habilitado ocupa las máquinas entre el 20 % y el 50 % del proyecto
KAPPA = 0.5                    # fracción de la capacidad de máquina que los proyectos en curso le quitan al nuevo
U_MAX = 0.9


def conectar():
    return sqlite3.connect(DB)


def mtbf_estimado(con, mundo, centros, ini, desde='2021-01-01', mtbf0=15.0, peso_prior=2):
    """Días laborables entre fallas por máquina, estimados con las paradas NO planificadas registradas
    hasta `ini` (tablas simuladas) y encogidos hacia un prior de `mtbf0` días."""
    d = pd.read_sql('SELECT centro_id FROM sim_parada WHERE mundo_id=? AND planificada=0 AND fecha>=? AND fecha<?',
                    con, params=(mundo, desde, str(ini)))
    dias = max(int(np.busday_count(desde, str(ini), weekmask=WEEKMASK)), 1)
    n = d.groupby('centro_id').size().reindex(centros).fillna(0).values
    return (dias + peso_prior * mtbf0) / (n + peso_prior)


def ratio_vigente(con):
    """DataFrame (4 tipos × 13 procesos) de HH por tonelada: la práctica actual."""
    r = pd.read_sql('''SELECT t.nombre tipo, pr.orden o, rv.hh_por_t FROM ratio_vigente rv
                       JOIN tipo_estructura t ON t.id=rv.tipo_estructura_id JOIN proceso pr ON pr.id=rv.proceso_id''', con)
    return r.pivot(index='tipo', columns='o', values='hh_por_t').loc[TIPOS]


def modelo_cuadrilla(con):
    """Cuadrilla típica por proceso en función de las toneladas: personas ≈ a · t^b (ajuste log-log)."""
    d = pd.read_sql('''SELECT pr.orden o, p.toneladas t, pp.n_personas n FROM proyecto_proceso pp
                       JOIN proyecto p ON p.id=pp.proyecto_id JOIN proceso pr ON pr.id=pp.proceso_id
                       WHERE p.en_muestra=1''', con)
    par = {}
    for o, g in d.groupby('o'):
        if g.n.nunique() == 1:
            par[o] = (float(g.n.iloc[0]), 0.0)
        else:
            b, a = np.polyfit(np.log(g.t), np.log(g.n), 1)
            par[o] = (float(np.exp(a)), float(b))
    return par


def modelo_dias_externos(con):
    """Plazo planificado de los servicios externos (procesos 7 y 12) vs toneladas: días ≈ a · t^b."""
    d = pd.read_sql('''SELECT pr.orden o, p.toneladas t, pp.dias_plan n FROM proyecto_proceso pp
                       JOIN proyecto p ON p.id=pp.proyecto_id JOIN proceso pr ON pr.id=pp.proceso_id
                       WHERE p.en_muestra=1 AND pr.orden IN (7, 12)''', con)
    par = {}
    for o, g in d.groupby('o'):
        b, a = np.polyfit(np.log(g.t), np.log(g.n), 1)
        par[o] = (float(np.exp(a)), float(b))
    return par


def dias_externos(par, ton):
    return np.array([max(1.0, par[o][0] * ton ** par[o][1]) for o in (7, 12)])


def cuadrilla(par, ton):
    return np.array([max(1.0, round(par[o][0] * ton ** par[o][1])) for o in range(1, N_PROC + 1)])


def proyectos_carga(con):
    """Los 38 proyectos con ventana y HH de máquina (ratio de su tipo; imputado si no hay toneladas)."""
    P = pd.read_sql('''SELECT p.id pid, p.fecha_inicio ini, p.fecha_fin_real fin, p.toneladas ton, t.nombre tipo
                       FROM proyecto p LEFT JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                       WHERE p.n_registro IS NOT NULL ORDER BY p.fecha_inicio, p.id''', con)
    P['ton'] = P.ton.fillna(TON_IMPUTADA)
    P['tipo'] = P.tipo.fillna(TIPOS[0])
    return P


class CargaTaller:
    """Carga de las 4 máquinas (fracción 0-1 por día laborable) por los proyectos en curso."""

    def __init__(self, con, dias_cal):
        self.dias = dias_cal
        rv = ratio_vigente(con)
        self.P = proyectos_carga(con)
        self.contrib = {}
        for r in self.P.itertuples():
            i0 = int(np.searchsorted(dias_cal, np.datetime64(r.ini, 'D')))
            dur = n_dias_laborables(r.ini, r.fin)
            a, b = i0 + int(FRAC_VENTANA[0] * dur), i0 + max(int(FRAC_VENTANA[1] * dur), int(FRAC_VENTANA[0] * dur) + 1)
            hh = r.ton * rv.loc[r.tipo].values[MAQUINAS]
            self.contrib[r.pid] = (a, b, hh / ((b - a) * 8.0))

    def u(self, ini_ref, excluir=None, T=300, extra=()):
        """Carga (T, 4) en los T días que siguen a ini_ref causada por proyectos iniciados antes que él.
        `extra`: proyectos en curso adicionales como (fecha_inicio, fecha_fin, toneladas, tipo)."""
        i0 = int(np.searchsorted(self.dias, np.datetime64(ini_ref, 'D')))
        u = np.zeros((T, 4))
        previos = self.P[(self.P.ini < str(ini_ref)) & (self.P.pid != excluir)]
        for pid in previos.pid:
            a, b, rate = self.contrib[pid]
            lo, hi = max(a, i0), min(b, i0 + T)
            if hi > lo:
                u[lo - i0:hi - i0] += rate
        return np.minimum(u, U_MAX)

    @staticmethod
    def efectiva(disp, u):
        """Disponibilidad efectiva para el proyecto nuevo = D · (1 − κ·u)."""
        return disp * (1.0 - KAPPA * u)
