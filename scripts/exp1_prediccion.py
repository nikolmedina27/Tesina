"""Experimento 1: predicción de HH por proceso, validación leave-one-project-out sobre datos SIMULADOS.

Compara: ratio vigente (práctica actual), regresión lineal múltiple, RF puntual, Empírico, QRF, QRF + conformal.
Métricas a nivel proyecto (suma de procesos) y por registro; cobertura P10-P90.
Uso: py scripts/exp1_prediccion.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.c2_modelo import dataset, X_de, PhiQRF, PhiEmpirico            # noqa: E402
from dss.datos import conectar                                          # noqa: E402

warnings.filterwarnings('ignore')
TAUS = np.array([0.1, 0.5, 0.9])


def pinball(y, q, tau):
    d = y - q
    return np.mean(np.maximum(tau * d, (tau - 1) * d))


def correr(con, mundo):
    df = dataset(con, mundo)
    X = X_de(df)
    pids = df.pid.unique()
    pred = {k: np.zeros(len(df)) for k in ['Ratio vigente', 'Regresión lineal', 'RF puntual', 'Empírico', 'GBM cuantílico', 'QRF', 'QRF + conformal']}
    q = {k: np.zeros((len(df), 3)) for k in ['Empírico', 'GBM cuantílico', 'QRF', 'QRF + conformal']}
    for p in pids:
        te = (df.pid == p).values
        tr = ~te
        pred['Ratio vigente'][te] = 0.0
        pred['Regresión lineal'][te] = LinearRegression().fit(X[tr], df.logphi[tr]).predict(X[te])
        pred['RF puntual'][te] = RandomForestRegressor(200, min_samples_leaf=4, max_features=0.6, random_state=0).fit(X[tr], df.logphi[tr]).predict(X[te])
        proy = type('P', (), dict(ton=df.ton[te].iloc[0], tipo=df.tipo[te].iloc[0], piezas_por_t=df.piezas_por_t[te].iloc[0],
                                  pct_planchas=df.pct_planchas[te].iloc[0], m2_pintura_t=df.m2_pintura[te].iloc[0] / df.ton[te].iloc[0],
                                  montaje=df.montaje[te].iloc[0], inicio=df.ini[te].iloc[0]))
        # competidor tipo Bekci et al. (2022): gradient boosting con pérdida cuantílica, un modelo por cuantil
        gq = np.column_stack([GradientBoostingRegressor(loss='quantile', alpha=a, n_estimators=150, max_depth=3, learning_rate=0.05,
                                                        min_samples_leaf=5, random_state=0).fit(X[tr], df.logphi[tr]).predict(X[te])
                              for a in TAUS])
        gq = np.sort(gq, axis=1)
        q['GBM cuantílico'][te] = gq
        pred['GBM cuantílico'][te] = gq[:, 1]
        for nombre, modelo in [('Empírico', PhiEmpirico().fit(df[tr])), ('QRF', PhiQRF(conformal=False, min_proyectos=3).fit(df[tr])),
                               ('QRF + conformal', PhiQRF(conformal=True, min_proyectos=3).fit(df[tr]))]:
            qq, _ = modelo.cuantiles(proy, TAUS)
            q[nombre][te] = np.log(qq)
            pred[nombre][te] = np.log(qq[:, 1])
    filas = []
    real = df.hh_real.values
    ratio = df.hh_ratio.values
    for k, lp in pred.items():
        est = ratio * np.exp(lp)
        e_proy = pd.DataFrame({'p': df.pid, 'e': est, 'r': real}).groupby('p').sum()
        fila = dict(Modelo=k, MAE_HH_registro=np.mean(np.abs(est - real)),
                    MAPE_proyecto=100 * np.mean(np.abs(e_proy.e - e_proy.r) / e_proy.r),
                    MAE_logphi=np.mean(np.abs(lp - df.logphi)))
        if k in q:
            qk = q[k]
            fila['PICP_P10_P90'] = np.mean((df.logphi >= qk[:, 0]) & (df.logphi <= qk[:, 2]))
            fila['Ancho_medio'] = np.mean(np.exp(qk[:, 2]) - np.exp(qk[:, 0]))
            fila['Pinball_0.9'] = pinball(df.logphi.values, qk[:, 2], 0.9)
        filas.append(fila)
    return pd.DataFrame(filas).set_index('Modelo').round(3)


if __name__ == '__main__':
    con = conectar()
    nombres = dict(con.execute('SELECT id, nombre FROM sim_mundo'))
    out = []
    for m in sorted(nombres):
        r = correr(con, m)
        print(f'\n=== {nombres[m]} (LOPO, 25 proyectos) ===')
        print(r.to_string())
        out.append(r.assign(mundo=nombres[m]))
    pd.concat(out).to_csv(Path(__file__).resolve().parent.parent / 'data' / 'exp1_resultados.csv')
