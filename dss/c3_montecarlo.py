"""C3: CRP de carga finita + simulación de Monte Carlo -> fecha de cotización.

Para un proyecto nuevo, simula R futuros posibles del taller (HH reales por proceso,
paradas de las 4 máquinas, plazos externos, carga de los proyectos en curso), programa
el proyecto día a día en cada uno y obtiene R fechas de fin. De esa distribución salen
la fecha a cotizar, la probabilidad de cumplirla y la penalidad esperada.
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import norm

from .crp_engine import N_PROC, LAM_DEFECTO, WEEKMASK, programar, dias_laborables
from .datos import (CargaTaller, ratio_vigente, modelo_cuadrilla, cuadrilla,
                    modelo_dias_externos, dias_externos, TIPOS)

TAUS = np.array([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95])
T_DIAS = 300
MTBF_DEFECTO = np.array([15.0, 15.0, 15.0, 15.0])   # supuesto inicial hasta registrar paradas reales
DUR_MU, DUR_SIGMA = np.log(0.6), 0.9                # duración de una falla (días laborables)
SIGMA_EXT = 0.2                                     # variabilidad lognormal del plazo externo
P_PENALIDAD = 0.01                                  # por día calendario, sin tope


@dataclass
class Proyecto:
    tipo: str
    ton: float
    inicio: str                      # 'YYYY-MM-DD': día 1 (planos aprobados + orden de compra)
    presupuesto: float = 100_000.0
    pct_planchas: float = 0.2
    piezas_por_t: float = 8.0
    m2_pintura_t: float = 14.0
    montaje: bool = False
    contratista: str = ''
    cuadrilla: np.ndarray | None = None   # personas por proceso (13); por defecto la típica según toneladas
    ext_dias: np.ndarray | None = None    # plazo esperado de doblez y granallado/pintura (2); por defecto el típico
    id: int | None = None            # si ya existe en la BD (se excluye de su propia carga)


@dataclass
class Resultado:
    proyecto: Proyecto
    inicio: np.datetime64
    fechas: np.ndarray               # (R,) fechas de fin simuladas
    dias_lab: np.ndarray             # (R,) días laborables desde el inicio
    hh: np.ndarray                   # (R, 13)
    alpha: float = 0.8

    def fecha_alpha(self, alpha=None):
        a = self.alpha if alpha is None else alpha
        return np.sort(self.fechas)[min(len(self.fechas) - 1, int(np.ceil(a * len(self.fechas))) - 1)]

    def prob_cumplir(self, fecha):
        return float((self.fechas <= np.datetime64(fecha, 'D')).mean())

    def dias_atraso(self, fecha):
        return np.clip((self.fechas - np.datetime64(fecha, 'D')).astype(int), 0, None)

    def penalidad_esperada(self, fecha, p=P_PENALIDAD):
        return float(p * self.proyecto.presupuesto * self.dias_atraso(fecha).mean())

    def plazo_calendario(self, fecha):
        return int((np.datetime64(fecha, 'D') - self.inicio).astype(int)) + 1

    def curva(self, p=P_PENALIDAD):
        """Tabla plazo -> probabilidad de cumplir y penalidad esperada (cada día calendario entre P05 y P99)."""
        lo, hi = np.quantile(self.fechas.astype('int64'), [0.05, 0.99]).astype(int)
        filas = []
        for f in range(lo, hi + 1):
            d = np.datetime64(f, 'D')
            filas.append((d, self.plazo_calendario(d), self.prob_cumplir(d), self.penalidad_esperada(d, p)))
        return filas


def alpha_optimo(p=P_PENALIDAD, prob_pierde_por_dia=0.005, margen=0.16, lo=0.5, hi=0.95):
    """Cuantil crítico tipo newsvendor: α* = c_u / (c_u + c_o).
    c_u = p (por día de atraso, fracción del presupuesto); c_o = pérdida esperada por cada día de plazo ofertado
    de más = (caída de la probabilidad de ganar por día) × margen. `prob_pierde_por_dia` es un SUPUESTO hasta
    tener las cotizaciones ganadas y perdidas."""
    c_o = prob_pierde_por_dia * margen
    return float(np.clip(p / (p + c_o), lo, hi))


# ------------------------------------------------------------------ muestreo
def muestrear_phi(q_phi, rho, R, rng, taus=TAUS):
    """φ por proceso (R, 13) desde sus cuantiles q_phi (13, K) con dependencia gaussiana entre procesos."""
    eta = rng.standard_normal((R, 1))
    eps = rng.standard_normal((R, N_PROC))
    U = norm.cdf(np.sqrt(rho) * eta + np.sqrt(1 - rho) * eps)
    out = np.empty((R, N_PROC))
    for j in range(N_PROC):
        q = np.maximum.accumulate(q_phi[j])
        x = np.concatenate([[taus[0] - 0.045], taus, [taus[-1] + 0.045]])
        y = np.concatenate([[q[0] - (q[1] - q[0]) * 0.9], q, [q[-1] + (q[-1] - q[-2]) * 0.9]])
        out[:, j] = np.interp(U[:, j], x, np.maximum(y, 0.05))
    return out


def muestrear_disp(R, T, mtbf, rng, planificado=True):
    """Disponibilidad diaria (R, T, 4): fallas con tiempo entre fallas exponencial y duración lognormal."""
    loss = np.zeros((R, T, 4))
    filas = np.arange(R)
    n_ev = int(T / max(mtbf.min(), 1) * 2.5) + 10
    for k in range(4):
        llegada = np.cumsum(rng.exponential(mtbf[k], (R, n_ev)), axis=1)
        dur = np.clip(np.exp(rng.normal(DUR_MU, DUR_SIGMA, (R, n_ev))), 0.1, 10)
        for e in range(n_ev):
            i0 = llegada[:, e].astype(int)
            for d in range(11):
                ok = (i0 + d) < T
                monto = np.clip(dur[:, e] - d, 0, 1)
                if not ok.any() or not (monto[ok] > 0).any():
                    continue
                np.add.at(loss[:, :, k], (filas[ok], (i0 + d)[ok]), monto[ok])
        if planificado:
            fase = rng.integers(0, 30, R)
            for r0 in range(0, T, 30):
                idx = r0 + fase
                ok = idx < T
                loss[filas[ok], idx[ok], k] += 0.5
    return np.clip(1.0 - loss, 0.0, 1.0)


# ------------------------------------------------------------------ cotizador
class Cotizador:
    """Une datos de referencia, predictor de φ (C2), carga del taller y motor CRP."""

    def __init__(self, con, predictor, dias_cal=None):
        self.con = con
        self.predictor = predictor
        self.dias_cal = dias_laborables('2019-01-01', 3200) if dias_cal is None else dias_cal
        self.rv = ratio_vigente(con)
        self.par_cuad = modelo_cuadrilla(con)
        self.par_ext = modelo_dias_externos(con)
        self.carga = CargaTaller(con, self.dias_cal)
        self.escala = 1.0                       # factor de ritmo del proyecto (anclaje a la estimación del cotizador)
        self.lam = LAM_DEFECTO                  # solapes del CRP; el gemelo los recalibra con el tareo (dss/gemelo/calibrar_dss.py)

    def cotizar(self, proy, R=1000, alpha=0.8, mtbf=MTBF_DEFECTO, semilla=1, lam=None, carga_extra=0.0,
                sin_disponibilidad=False, sin_carga=False, rho=None, restante=None, mult=None, mult_desde=0, esperas=None):
        """`sin_disponibilidad`, `sin_carga` y `rho` (valor fijo) son para las ablaciones del experimento 4.
        `restante` (13,): fracción de trabajo que falta por proceso (re-pronóstico de un proyecto en curso,
        con `proy.inicio` = hoy). `mult` (13,) son las palancas de gestión del what-if (ver dss/whatif.py). `esperas`: dict con 'ing' y 'compra', arrays
        (R,) de días laborables que faltan de ingeniería (con RFIs) y de espera de material; reemplazan las HH de esos dos
        procesos por la espera (aprendida de las compras pasadas)."""
        rng = np.random.default_rng(semilla)
        lam = self.lam if lam is None else lam
        hh_ratio = proy.ton * self.rv.loc[proy.tipo].values
        crew = proy.cuadrilla if proy.cuadrilla is not None else cuadrilla(self.par_cuad, proy.ton)
        q_phi, rho_est = self.predictor.cuantiles(proy, TAUS)
        phi = muestrear_phi(q_phi, rho_est if rho is None else rho, R, rng)
        hh = hh_ratio * phi
        if esperas is not None:
            if 'ing' in esperas:
                hh[:, 0] = np.asarray(esperas['ing'], float)[:R] * 8.0 * crew[0]
            if 'compra' in esperas:
                hh[:, 1] = np.asarray(esperas['compra'], float)[:R] * 8.0 * crew[1]
        hh = hh * self.escala
        ext_base = proy.ext_dias if proy.ext_dias is not None else dias_externos(self.par_ext, proy.ton)
        avance0 = None if restante is None else 1.0 - np.clip(np.asarray(restante, float), 0.0, 1.0)
        ext = ext_base * self.escala * np.exp(rng.normal(0, SIGMA_EXT, (R, 2)))
        u = np.minimum(self.carga.u(proy.inicio, excluir=proy.id, T=T_DIAS) + carga_extra, 0.9)
        if sin_carga:
            u = np.zeros_like(u)
        d = np.ones((R, T_DIAS, 4)) if sin_disponibilidad else muestrear_disp(R, T_DIAS, mtbf, rng)
        disp = CargaTaller.efectiva(d, u[None])
        o = programar(hh, crew, disp, ext, lam=lam, mult=mult, mult_desde=mult_desde, avance0=avance0)
        n = np.maximum(np.nan_to_num(o['fin'], nan=T_DIAS).astype(int), 1)
        base = np.busday_offset(np.datetime64(proy.inicio, 'D'), 0, roll='forward', weekmask=WEEKMASK)
        fechas = np.busday_offset(base, n - 1, weekmask=WEEKMASK)
        res = Resultado(proy, base, fechas, n, hh, alpha)
        # programa de la réplica mediana (para dibujar el Gantt)
        r_med = int(np.argsort(n)[len(n) // 2])
        res.programa = [(None if np.isnan(a) else int(a), None if np.isnan(b) else int(b))
                        for a, b in zip(o['ini'][r_med], o['fin_proc'][r_med])]
        return res

    def fecha_con_colchon(self, proy, mtbf=MTBF_DEFECTO, lam=LAM_DEFECTO, semilla=1):
        """Alternativa determinista (estilo Mundt & Lödding): plan con la mediana de φ, disponibilidad esperada y
        carga del taller, sin distribución. Devuelve (días laborables del plan, fecha base); la fecha cotizada es
        la del plan más un colchón fijo de días laborables."""
        rng = np.random.default_rng(semilla)
        hh_ratio = proy.ton * self.rv.loc[proy.tipo].values
        crew = proy.cuadrilla if proy.cuadrilla is not None else cuadrilla(self.par_cuad, proy.ton)
        q_phi, _ = self.predictor.cuantiles(proy, TAUS)
        hh = (hh_ratio * q_phi[:, list(TAUS).index(0.50)])[None]
        ext = (proy.ext_dias if proy.ext_dias is not None else dias_externos(self.par_ext, proy.ton))[None]
        u = np.minimum(self.carga.u(proy.inicio, excluir=proy.id, T=T_DIAS), 0.9)
        d_esp = muestrear_disp(200, T_DIAS, mtbf, rng).mean(axis=0)            # (T, 4) disponibilidad esperada
        o = programar(hh, crew, CargaTaller.efectiva(d_esp, u), ext, lam=lam)
        base = np.busday_offset(np.datetime64(proy.inicio, 'D'), 0, roll='forward', weekmask=WEEKMASK)
        return int(np.nan_to_num(o['fin'][0], nan=T_DIAS)), base
