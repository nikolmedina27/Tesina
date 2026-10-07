"""Experimento 2: backtest de cotización de fechas (rolling origin) sobre los 25 proyectos, datos SIMULADOS.

Para cada proyecto (en orden cronológico) se cotiza usando SOLO lo que se sabía a su fecha de inicio:
proyectos terminados antes (para entrenar C2), proyectos en curso (carga del taller) y las paradas
registradas hasta esa fecha. Se compara contra la fecha de fin REAL (Tabla 3) y contra la fecha que
cotizó el criterio del cotizador (fecha_fin_plan).
Uso: py scripts/exp2_backtest.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.c2_modelo import dataset, PhiQRF, PhiEmpirico                      # noqa: E402
from dss.c3_montecarlo import Cotizador, Proyecto, alpha_optimo, MTBF_DEFECTO  # noqa: E402
from dss.crp_engine import WEEKMASK                                          # noqa: E402
from dss.datos import conectar, mtbf_estimado                               # noqa: E402
from dss.simulador import MAQ_NOMBRE                                         # noqa: E402

warnings.filterwarnings('ignore')
HIST_DESDE = '2021-01-01'


def lead(ini, fecha):
    return int((np.datetime64(fecha, 'D') - np.datetime64(ini, 'D')).astype(int)) + 1


def main(R=1000):
    con = conectar()
    mundos = dict(con.execute('SELECT id, nombre FROM sim_mundo'))
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    centros = [cen[n] for n in MAQ_NOMBRE]
    a_star = alpha_optimo()
    filas = []
    for m, nombre in mundos.items():
        df = dataset(con, m)
        cot = Cotizador(con, predictor=None)
        proy = df.groupby('pid', sort=False).first().reset_index()
        real = pd.read_sql('SELECT id pid, fecha_fin_plan fp, fecha_fin_real fr, dias_retraso FROM proyecto', con).set_index('pid')
        for r in proy.itertuples():
            tr = df[df.fin < r.ini]
            mtbf = mtbf_estimado(con, m, centros, r.ini)
            p = Proyecto(tipo=r.tipo, ton=r.ton, inicio=r.ini, presupuesto=100.0, pct_planchas=r.pct_planchas,
                         piezas_por_t=r.piezas_por_t, m2_pintura_t=r.m2_pintura / r.ton, montaje=bool(r.montaje), id=r.pid)
            fr, fp = real.loc[r.pid, 'fr'], real.loc[r.pid, 'fp']
            variantes = {'A0 criterio del cotizador (real)': (None, fp)}
            qrf = PhiQRF().fit(tr)
            for key, pred, alpha in [('A5 MC empírico α=0.80', PhiEmpirico().fit(tr), 0.80),
                                     ('A6 MC QRF+conformal α=0.80', qrf, 0.80),
                                     ('A7 MC QRF+conformal α*', qrf, a_star)]:
                cot.predictor = pred
                res = cot.cotizar(p, R=R, alpha=alpha, mtbf=mtbf, semilla=int(r.pid))
                f = str(res.fecha_alpha(alpha))
                variantes[key] = (res, f)
                if key.startswith('A6'):
                    p_plan = res.prob_cumplir(fp)
                    p_fecha = res.prob_cumplir(f)
            for key, (res, f) in variantes.items():
                tarde = max(int((np.datetime64(fr, 'D') - np.datetime64(f, 'D')).astype(int)), 0)
                filas.append(dict(mundo=nombre, cod=r.cod, ini=r.ini, variante=key, fecha=f, lead=lead(r.ini, f),
                                  lead_plan=lead(r.ini, fp), cumple=tarde == 0, dias_tarde=tarde,
                                  p_plan=p_plan if key.startswith('A6') else np.nan,
                                  p_fecha=p_fecha if key.startswith('A6') else np.nan))
        print(nombre, 'listo', flush=True)
    out = pd.DataFrame(filas)
    out.to_csv(Path(__file__).resolve().parent.parent / 'data' / 'exp2_backtest.csv', index=False)
    return out


def resumen(out):
    g = out.groupby(['mundo', 'variante'])
    t = g.agg(OTD=('cumple', lambda s: 100 * s.mean()), retraso_prom=('dias_tarde', 'mean'),
              penalidad_pct=('dias_tarde', lambda s: s.mean()), lead_med=('lead', 'mean'), lead_plan=('lead_plan', 'mean')).round(2)
    t['lead_vs_plan_%'] = (100 * (t.lead_med / t.lead_plan - 1)).round(1)
    return t.drop(columns=['lead_plan'])


if __name__ == '__main__':
    out = main()
    pd.set_option('display.width', 220)
    print(resumen(out).to_string())
    print('\nCalibración en A6: prob. asignada a cumplir el plan del cotizador vs. cumplimiento real')
    a6 = out[out.variante.str.startswith('A6')].groupby('mundo').agg(p_plan_media=('p_plan', 'mean'), p_fecha_media=('p_fecha', 'mean'))
    a6['real_cumple_A6'] = out[out.variante.str.startswith('A6')].groupby('mundo').cumple.mean()
    a6['real_cumple_plan'] = out[out.variante.str.startswith('A0')].groupby('mundo').cumple.mean()
    print(a6.round(3).to_string())
