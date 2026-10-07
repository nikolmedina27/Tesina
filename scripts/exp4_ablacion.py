"""Experimento 4: ablaciones, competidor de colchón fijo y sensibilidad a la disponibilidad (datos SIMULADOS).

Mismo backtest causal que exp2/exp3 (rolling origin, solo información disponible al inicio de cada proyecto) y el
DSS recibe las cuadrillas y plazos externos que planificó el cotizador. Compara, sobre 5 escenarios:
  A0   criterio del cotizador (fecha real cotizada)
  B    colchón fijo: plan determinista con φ mediana + N días laborables (estilo Mundt & Lödding)
  MC   Monte Carlo completo (QRF + conformal, Dk, carga del taller, ρ estimado)
  MC-  y sus variantes sin una pieza: sin conformal, sin Dk, sin carga del taller, ρ = 0, sin variables (empírico)
Métrica de comparación: plazo extra (% sobre el del cotizador) necesario para llegar a OTD 80 % y 90 %.
Uso: py scripts/exp4_ablacion.py
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.c2_modelo import dataset, PhiQRF, PhiEmpirico            # noqa: E402
from dss.c3_montecarlo import Cotizador, Proyecto                  # noqa: E402
from dss.crp_engine import WEEKMASK                                # noqa: E402
from dss.datos import conectar, mtbf_estimado                      # noqa: E402
from dss.simulador import MAQ_NOMBRE                               # noqa: E402

warnings.filterwarnings('ignore')
RAIZ = Path(__file__).resolve().parent.parent
ALPHAS = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.93, 0.95, 0.97]
BUFFERS = [0, 1, 2, 3, 4, 6, 8, 10, 12, 15]          # días laborables
VARIANTES_MC = ['MC completo', 'MC sin conformal', 'MC sin disponibilidad', 'MC sin carga del taller',
                'MC con rho = 0', 'MC sin variables (empírico)']


def lead(ini, f):
    return int((np.datetime64(f, 'D') - np.datetime64(ini, 'D')).astype(int)) + 1


def correr(R=1000):
    con = conectar()
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    centros = [cen[n] for n in MAQ_NOMBRE]
    real = pd.read_sql('SELECT id pid, fecha_fin_plan fp, fecha_fin_real fr FROM proyecto', con).set_index('pid')
    plan = pd.read_sql('''SELECT p.id pid, pr.orden o, pp.n_personas n, pp.dias_plan d FROM proyecto_proceso pp
                          JOIN proyecto p ON p.id=pp.proyecto_id JOIN proceso pr ON pr.id=pp.proceso_id
                          WHERE p.en_muestra=1 ORDER BY pid, o''', con)
    filas = []
    for m, nombre in dict(con.execute('SELECT id, nombre FROM sim_mundo')).items():
        df = dataset(con, m)
        cot = Cotizador(con, None)
        for r in df.groupby('pid', sort=False).first().reset_index().itertuples():
            tr = df[df.fin < r.ini]
            x = plan[plan.pid == r.pid]
            p = Proyecto(tipo=r.tipo, ton=r.ton, inicio=r.ini, presupuesto=100.0, pct_planchas=r.pct_planchas,
                         piezas_por_t=r.piezas_por_t, m2_pintura_t=r.m2_pintura / r.ton, montaje=bool(r.montaje), id=r.pid,
                         cuadrilla=x.n.values.astype(float), ext_dias=x.d.values[[6, 11]].astype(float))
            mtbf = mtbf_estimado(con, m, centros, r.ini)
            fr, fp = real.loc[r.pid, 'fr'], real.loc[r.pid, 'fp']
            base = dict(mundo=nombre, cod=r.cod, lead_plan=lead(r.ini, fp))

            def anotar(variante, param, f):
                tarde = max(int((np.datetime64(fr, 'D') - np.datetime64(f, 'D')).astype(int)), 0)
                filas.append(dict(base, variante=variante, param=param, lead=lead(r.ini, f), tarde=tarde))

            anotar('A0 criterio del cotizador', 0, fp)
            qrf = PhiQRF().fit(tr)
            emp = PhiEmpirico().fit(tr)
            # B: colchón fijo
            cot.predictor = qrf
            n_det, ini_d = cot.fecha_con_colchon(p, mtbf=mtbf, semilla=int(r.pid))
            for b in BUFFERS:
                anotar('B colchón fijo', b, str(np.busday_offset(ini_d, n_det - 1 + b, weekmask=WEEKMASK)))
            # MC y variantes
            configs = {
                'MC completo': dict(pred=qrf, conf=True),
                'MC sin conformal': dict(pred=qrf, conf=False),
                'MC sin disponibilidad': dict(pred=qrf, conf=True, sin_disponibilidad=True),
                'MC sin carga del taller': dict(pred=qrf, conf=True, sin_carga=True),
                'MC con rho = 0': dict(pred=qrf, conf=True, rho=0.0),
                'MC sin variables (empírico)': dict(pred=emp, conf=True),
            }
            for nombre_v, cfg in configs.items():
                cot.predictor = cfg['pred']
                qrf.conformal = cfg['conf']
                res = cot.cotizar(p, R=R, mtbf=mtbf, semilla=int(r.pid), sin_disponibilidad=cfg.get('sin_disponibilidad', False),
                                  sin_carga=cfg.get('sin_carga', False), rho=cfg.get('rho'))
                qrf.conformal = True
                for a in ALPHAS:
                    anotar(nombre_v, a, str(res.fecha_alpha(a)))
        print(nombre, 'listo', flush=True)
    return pd.DataFrame(filas)


def lead_en_otd(curva, objetivo):
    """Plazo extra medio (%) con el que la curva (ordenada por parámetro) alcanza el OTD objetivo (interpolado)."""
    otd = np.maximum.accumulate(curva.otd.values)
    if otd[-1] < objetivo:
        return np.nan
    return float(np.interp(objetivo, otd, curva.lead_pct.values))


def curva(d):
    g = d.groupby('param').agg(otd=('tarde', lambda s: 100 * (s == 0).mean()), lead_pct=('lead', 'mean'),
                               lead_plan=('lead_plan', 'mean'), tarde=('tarde', 'mean')).reset_index()
    g['lead_pct'] = 100 * (g.lead_pct / g.lead_plan - 1)
    return g.sort_values('param')


def resumen(d, n_boot=300, semilla=0):
    rng = np.random.default_rng(semilla)
    cods = d.cod.unique()
    filas = []
    for var, dv in d.groupby('variante', sort=False):
        c = curva(dv)
        fila = dict(variante=var, otd_cotizador=np.nan)
        for obj in (80, 90):
            fila[f'plazo_extra_para_OTD{obj}'] = lead_en_otd(c, obj)
            bs = []
            for _ in range(n_boot):
                muestra = rng.choice(cods, len(cods))
                dd = pd.concat([dv[dv.cod == k] for k in muestra])
                bs.append(lead_en_otd(curva(dd), obj))
            bs = np.array(bs, float)
            fila[f'IC_{obj}'] = f'[{np.nanpercentile(bs, 2.5):.1f}, {np.nanpercentile(bs, 97.5):.1f}]' if np.isfinite(bs).any() else 'n/a'
            fila[f'inalcanzable_{obj}_%'] = 100 * np.isnan(bs).mean()
        filas.append(fila)
    return pd.DataFrame(filas)


if __name__ == '__main__':
    d = correr()
    d.to_csv(RAIZ / 'data' / 'exp4_ablacion_raw.csv', index=False)
    pd.set_option('display.width', 220)
    pd.set_option('display.max_columns', 20)
    r = resumen(d)
    r.to_csv(RAIZ / 'data' / 'exp4_ablacion.csv', index=False)
    print(r.round(1).to_string(index=False))
    print('\nPor escenario (plazo extra % para OTD 80):')
    por = {}
    for m, dm in d.groupby('mundo', sort=False):
        por[m.split(' ')[0]] = {v: lead_en_otd(curva(dv), 80) for v, dv in dm.groupby('variante', sort=False)}
    print(pd.DataFrame(por).round(1).to_string())
