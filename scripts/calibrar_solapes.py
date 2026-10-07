import sys, sqlite3, itertools
sys.path.insert(0, '.')
import numpy as np, pandas as pd
from dss.crp_engine import *

con = sqlite3.connect('data/steelser.db')
P = pd.read_sql('''SELECT codigo_muestra cod, fecha_inicio ini, fecha_fin_plan fp, fecha_fin_real fr, dias_retraso ret
                   FROM proyecto WHERE en_muestra=1 ORDER BY codigo_muestra''', con)
X = pd.read_sql('''SELECT p.codigo_muestra cod, pr.orden, pp.n_personas, pp.dias_plan, pp.dias_real, pp.hh_ratio_vigente hh
                   FROM proyecto_proceso pp JOIN proyecto p ON p.id=pp.proyecto_id JOIN proceso pr ON pr.id=pp.proceso_id
                   WHERE p.en_muestra=1''', con)
P['n_plan'] = [n_dias_laborables(a, b) for a, b in zip(P.ini, P.fp)]
P['n_real'] = [n_dias_laborables(a, b) for a, b in zip(P.ini, P.fr)]
print(P[['n_plan', 'n_real']].describe().round(1).T)

def correr(lam, ext_factor=1.0):
    out = []
    for r in P.itertuples():
        x = X[X.cod == r.cod].sort_values('orden')
        hh = x.hh.values[None, :]
        crew = x.n_personas.values.astype(float)
        ext = x.dias_plan.values[[6, 11]][None, :].astype(float) * ext_factor
        o = programar(hh, crew, np.ones((300, 4)), ext, lam=lam)
        out.append(o['fin'][0])
    return np.array(out)

base = correr(LAM_DEFECTO)
print('lam defecto: sim', base.mean().round(1), 'real plan', P.n_plan.mean().round(1),
      'MAE', np.abs(base - P.n_plan).mean().round(2), 'sesgo', (base - P.n_plan).mean().round(2))
mejor = None
for a, b, c, d, e in itertools.product([.6,.7,.8,.9],[.6,.7,.8,.9],[.4,.5,.6,.7,.8],[.6,.7,.8,.9],[1.0]):
    lam = LAM_DEFECTO.copy(); lam[[1, 2, 3, 4, 5, 6]] = a; lam[7] = b; lam[8] = c; lam[9] = d; lam[10] = e
    s = correr(lam)
    mae = np.abs(s - P.n_plan).mean()
    if mejor is None or mae < mejor[0]: mejor = (mae, (a, b, c, d, e), (s - P.n_plan).mean())
print('mejor', mejor)

