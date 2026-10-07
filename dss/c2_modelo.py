"""C2: predicción de las HH por proceso como factor de corrección φ = HH_real / HH_ratio.

Predictores con la misma interfaz `.cuantiles(proyecto, taus) -> (q_phi (13, K), rho)`:
  - PhiEmpirico: cuantiles de φ por proceso, sin variables (línea base "sin modelo").
  - PhiQRF: Quantile Regression Forest sobre log φ con las variables del plano, más
    calibración conformal agrupada por proyecto (garantiza cobertura con pocos proyectos).
"""
import numpy as np
import pandas as pd
from quantile_forest import RandomForestQuantileRegressor
from sklearn.model_selection import GroupKFold

from .crp_engine import N_PROC
from .datos import TIPOS

FEATURES = ['log_ton', 'piezas_por_t', 'pct_planchas', 'm2_pint_t', 'montaje', 't_anio', 'orden'] + \
           [f'tipo_{i}' for i in range(len(TIPOS))]


def dataset(con, mundo_id):
    """Un registro por proyecto × proceso del mundo simulado `mundo_id`, con variables y φ verdadero."""
    d = pd.read_sql('''SELECT p.id pid, p.codigo_muestra cod, p.fecha_inicio ini, p.fecha_fin_real fin, t.nombre tipo,
                       p.toneladas ton, f.piezas_por_t, f.pct_planchas, f.m2_pintura, f.montaje, pr.orden,
                       pp.hh_ratio_vigente hh_ratio, s.hh_real, s.phi
                       FROM sim_proyecto_proceso s JOIN proyecto p ON p.id=s.proyecto_id
                       JOIN sim_feature f ON f.proyecto_id=p.id JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                       JOIN proceso pr ON pr.id=s.proceso_id
                       JOIN proyecto_proceso pp ON pp.proyecto_id=s.proyecto_id AND pp.proceso_id=s.proceso_id
                       WHERE s.mundo_id=? ORDER BY p.fecha_inicio, pr.orden''', con, params=(mundo_id,))
    d['logphi'] = np.log(d.phi)
    return d


def _t_anio(ini):
    ts = pd.Timestamp(ini)
    return ts.year + (ts.dayofyear - 1) / 365.25


def matriz(ton, tipo, piezas_por_t, pct_planchas, m2_pint_t, montaje, t_anio, ordenes):
    """Matriz de variables (len(ordenes), len(FEATURES)) de UN proyecto en sus procesos."""
    n = len(ordenes)
    X = np.zeros((n, len(FEATURES)))
    X[:, 0] = np.log(ton); X[:, 1] = piezas_por_t; X[:, 2] = pct_planchas; X[:, 3] = m2_pint_t
    X[:, 4] = float(montaje); X[:, 5] = t_anio; X[:, 6] = ordenes
    X[:, 7 + TIPOS.index(tipo)] = 1.0
    return X


def X_de(df):
    return np.vstack([matriz(g.ton.iloc[0], g.tipo.iloc[0], g.piezas_por_t.iloc[0], g.pct_planchas.iloc[0],
                             g.m2_pintura.iloc[0] / g.ton.iloc[0], g.montaje.iloc[0], _t_anio(g.ini.iloc[0]),
                             g.orden.values) for _, g in df.groupby('pid', sort=False)])


def estimar_rho(resid, pid):
    """Correlación intra-proyecto de los residuos (ANOVA): varianza entre proyectos / varianza total."""
    r = pd.Series(resid)
    tot = r.var()
    medias = r.groupby(np.asarray(pid)).mean()
    n_j = r.groupby(np.asarray(pid)).size().mean()
    entre = max(medias.var() - (tot / n_j), 0.0) if len(medias) > 1 else 0.0
    return float(np.clip(entre / tot, 0.0, 0.9)) if tot > 0 else 0.0


class PhiEmpirico:
    """Cuantiles de φ por proceso de los proyectos terminados (sin variables explicativas)."""
    nombre = 'Empírico'

    def __init__(self, prior_sigma=0.15):
        self.prior_sigma = prior_sigma

    def fit(self, df):
        self.df = df
        self.n_proy = df.pid.nunique() if len(df) else 0
        if self.n_proy >= 3:
            self.mu = df.groupby('orden').logphi.mean().reindex(range(1, N_PROC + 1)).fillna(0.0).values
            self.res = (df.logphi - df.orden.map(dict(zip(range(1, N_PROC + 1), self.mu)))).values
            self.rho = estimar_rho(self.res, df.pid.values)
        else:
            self.rho = 0.4
        return self

    def cuantiles(self, proy, taus):
        from scipy.stats import norm
        if self.n_proy < 3:                            # sin historia: prior lognormal centrado en el ratio
            q = np.exp(self.prior_sigma * norm.ppf(taus))
            return np.tile(q, (N_PROC, 1)), self.rho
        q = np.empty((N_PROC, len(taus)))
        for o in range(1, N_PROC + 1):
            x = self.df.loc[self.df.orden == o, 'logphi'].values
            q[o - 1] = np.exp(np.quantile(x, taus) if len(x) >= 5 else
                              self.mu[o - 1] + x.std(ddof=0) * norm.ppf(taus))
        return q, self.rho


class PhiQRF:
    """Quantile Regression Forest sobre log φ + calibración conformal por proyecto."""
    nombre = 'QRF + conformal'

    def __init__(self, n_estimators=200, min_samples_leaf=4, max_features=0.6, conformal=True,
                 cobertura=0.8, semilla=0, min_proyectos=6):
        self.kw = dict(n_estimators=n_estimators, min_samples_leaf=min_samples_leaf,
                       max_features=max_features, random_state=semilla, n_jobs=1)
        self.conformal, self.cobertura, self.min_proyectos = conformal, cobertura, min_proyectos

    def _nuevo(self):
        return RandomForestQuantileRegressor(**self.kw)

    def fit(self, df):
        self.n_proy = df.pid.nunique() if len(df) else 0
        self.respaldo = PhiEmpirico().fit(df)
        self.E = 0.0
        if self.n_proy < self.min_proyectos:
            self.modelo, self.rho = None, self.respaldo.rho
            return self
        X, y, g = X_de(df), df.logphi.values, df.pid.values
        self.modelo = self._nuevo().fit(X, y)
        k = min(5, self.n_proy)
        pred = np.zeros((len(y), 3))
        for tr, te in GroupKFold(n_splits=k).split(X, y, g):
            m = self._nuevo().fit(X[tr], y[tr])
            pred[te] = m.predict(X[te], quantiles=[0.1, 0.5, 0.9])
        self.res = y - pred[:, 1]
        self.rho = estimar_rho(self.res, g)
        if self.conformal:
            score = np.maximum(pred[:, 0] - y, y - pred[:, 2])
            n = len(score)
            self.E = float(np.quantile(score, min(1.0, np.ceil((n + 1) * self.cobertura) / n)))
        return self

    def cuantiles(self, proy, taus):
        if self.modelo is None:
            return self.respaldo.cuantiles(proy, taus)
        X = matriz(proy.ton, proy.tipo, proy.piezas_por_t, proy.pct_planchas, proy.m2_pintura_t, proy.montaje,
                   _t_anio(proy.inicio), np.arange(1, N_PROC + 1))
        q = self.modelo.predict(X, quantiles=list(taus))
        if self.conformal:
            q = q + self.E * np.clip((np.asarray(taus) - 0.5) / 0.4, -1.25, 1.25)
        return np.exp(np.maximum.accumulate(q, axis=1)), self.rho
