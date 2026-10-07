"""Experimento 3: frontera cumplimiento (OTD) vs. plazo cotizado al variar la confianza α (datos SIMULADOS).

Mismo backtest que exp2 (rolling origin, solo información disponible a la fecha de inicio) pero con
QRF + conformal y un barrido de α. Bootstrap por proyecto para los intervalos.
Uso: py scripts/exp3_frontera.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.c2_modelo import dataset, PhiQRF                          # noqa: E402
from dss.c3_montecarlo import Cotizador, Proyecto                  # noqa: E402
from dss.datos import conectar, mtbf_estimado                      # noqa: E402
from dss.simulador import MAQ_NOMBRE                               # noqa: E402

warnings.filterwarnings('ignore')
ALPHAS = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97]


def lead(ini, f):
    return int((np.datetime64(f, 'D') - np.datetime64(ini, 'D')).astype(int)) + 1


def main(R=1000, plan_cotizador=False):
    """plan_cotizador=True: el DSS recibe las cuadrillas y plazos externos que planificó el cotizador
    (auditoría de su plan). False: usa cuadrilla y plazos típicos según las toneladas."""
    con = conectar()
    plan = pd.read_sql('''SELECT p.id pid, pr.orden o, pp.n_personas n, pp.dias_plan d FROM proyecto_proceso pp
                          JOIN proyecto p ON p.id=pp.proyecto_id JOIN proceso pr ON pr.id=pp.proceso_id
                          WHERE p.en_muestra=1 ORDER BY pid, o''', con)
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    centros = [cen[n] for n in MAQ_NOMBRE]
    real = pd.read_sql('SELECT id pid, fecha_fin_plan fp, fecha_fin_real fr FROM proyecto', con).set_index('pid')
    filas = []
    for m, nombre in dict(con.execute('SELECT id, nombre FROM sim_mundo')).items():
        df = dataset(con, m)
        cot = Cotizador(con, None)
        for r in df.groupby('pid', sort=False).first().reset_index().itertuples():
            cot.predictor = PhiQRF().fit(df[df.fin < r.ini])
            p = Proyecto(tipo=r.tipo, ton=r.ton, inicio=r.ini, presupuesto=100.0, pct_planchas=r.pct_planchas,
                         piezas_por_t=r.piezas_por_t, m2_pintura_t=r.m2_pintura / r.ton, montaje=bool(r.montaje), id=r.pid)
            if plan_cotizador:
                x = plan[plan.pid == r.pid]
                p.cuadrilla = x.n.values.astype(float)
                p.ext_dias = x.d.values[[6, 11]].astype(float)
            res = cot.cotizar(p, R=R, mtbf=mtbf_estimado(con, m, centros, r.ini), semilla=int(r.pid))
            fr, fp = real.loc[r.pid, 'fr'], real.loc[r.pid, 'fp']
            filas.append(dict(mundo=nombre, cod=r.cod, alpha='plan', lead=lead(r.ini, fp), lead_plan=lead(r.ini, fp),
                              tarde=max((np.datetime64(fr) - np.datetime64(fp)).astype(int), 0)))
            for a in ALPHAS:
                f = str(res.fecha_alpha(a))
                filas.append(dict(mundo=nombre, cod=r.cod, alpha=a, lead=lead(r.ini, f), lead_plan=lead(r.ini, fp),
                                  tarde=max((np.datetime64(fr) - np.datetime64(f)).astype(int), 0)))
        print(nombre, 'listo', flush=True)
    return pd.DataFrame(filas)


def resumir(d, n_boot=2000, semilla=0):
    rng = np.random.default_rng(semilla)
    salida = []
    for (mundo, a), g in d.groupby(['mundo', 'alpha'], sort=False):
        otd = (g.tarde == 0).values
        lv = (g.lead / g.lead_plan - 1).values * 100
        idx = rng.integers(0, len(g), (n_boot, len(g)))
        salida.append(dict(mundo=mundo, alpha=a, OTD=100 * otd.mean(),
                           OTD_lo=100 * np.percentile(otd[idx].mean(1), 2.5), OTD_hi=100 * np.percentile(otd[idx].mean(1), 97.5),
                           lead_vs_plan=lv.mean(), retraso_prom=g.tarde.mean()))
    return pd.DataFrame(salida)


if __name__ == '__main__':
    plan_cot = 'plan' in sys.argv
    sufijo = '_plan_cotizador' if plan_cot else ''
    d = main(plan_cotizador=plan_cot)
    d.to_csv(Path(__file__).resolve().parent.parent / 'data' / f'exp3_frontera_raw{sufijo}.csv', index=False)
    s = resumir(d)
    s.to_csv(Path(__file__).resolve().parent.parent / 'data' / f'exp3_frontera{sufijo}.csv', index=False)
    pd.set_option('display.width', 200)
    print(s.round(2).to_string(index=False))
