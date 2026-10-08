"""Experimento 5: estudio retrospectivo "cómo se hizo" contra "qué habría pasado con el DSS" (datos SIMULADOS).

Para cada uno de los 25 proyectos, en orden cronológico y con solo la información disponible a su fecha de
inicio, aplica 6 políticas (ver dss/retrospectivo.py) y mide cumplimiento, retraso, penalidad, costo de las
palancas y plazo cotizado. Se corre en paralelo por mundo simulado.

Uso: py scripts/exp5_retrospectivo.py                 (todos los mundos, ~4 min con 5 núcleos)
     py scripts/exp5_retrospectivo.py 2 5             (solo los mundos 2 y 5)
     py scripts/exp5_retrospectivo.py --costo 2       (sensibilidad: costos de las palancas × 2)
Salidas: data/exp5_retrospectivo[_costoX].csv, data/exp5_resumen[_costoX].csv y la tabla sim_retro_resultado.
"""
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.datos import conectar                                            # noqa: E402
from dss.retrospectivo import Retro, evaluar_proyecto, POLITICAS         # noqa: E402

warnings.filterwarnings('ignore')
DATA = Path(__file__).resolve().parent.parent / 'data'


def correr_mundo(args):
    mundo_id, escala, R = args
    warnings.filterwarnings('ignore')
    con = conectar()
    retro = Retro(con, mundo_id)
    filas = []
    for pid in retro.P.index:
        filas += evaluar_proyecto(retro, int(pid), R=R, escala_costo=escala)
    con.close()
    return filas


CO_PCT_DIA = 100 * 0.005 * 0.16        # costo comercial de cada día de plazo ofertado de más: 0.08 % del presupuesto
                                       # (SUPUESTO de alpha_optimo: cada día pierde 0.5 pts de probabilidad de ganar × margen 16 %)


def resumen(df, co=CO_PCT_DIA):
    """Resumen por mundo y política. `total` = penalidad + costo de palancas; `total_ajustado` suma además el costo
    comercial `co` por cada día de plazo ofertado de más respecto de la fecha original del cotizador."""
    base = df[df.politica == POLITICAS[0]].set_index(['mundo', 'cod']).lead
    df = df.assign(plazo_extra=df.lead.values - base.reindex(list(zip(df.mundo, df.cod))).values)
    df['total_ajustado'] = df.total + co * df.plazo_extra
    g = df.groupby(['mundo', 'politica'], sort=False)
    t = g.agg(OTD=('cumple', lambda s: 100 * s.mean()), retraso_dias=('tarde', 'mean'), penalidad=('penalidad', 'mean'),
              costo_palancas=('costo', 'mean'), total=('total', 'mean'), total_ajustado=('total_ajustado', 'mean'),
              lead=('lead', 'mean'), intervenciones=('intervino', 'sum')).round(2)
    a0 = t.xs(POLITICAS[0], level='politica')['lead']
    t['lead_vs_A0_%'] = [round(100 * (r.lead / a0[m] - 1), 1) for (m, _), r in t.iterrows()]
    return t


def bootstrap_dif(df, mundo, politica, base=POLITICAS[0], col='total', B=2000, semilla=0):
    if col == 'total_ajustado':
        b0 = df[df.politica == base].set_index(['mundo', 'cod']).lead
        df = df.assign(total_ajustado=df.total + CO_PCT_DIA * (df.lead.values - b0.reindex(list(zip(df.mundo, df.cod))).values))
    """IC 95 % (bootstrap sobre proyectos) de la diferencia media política − base de `col`, pareada."""
    a = df[(df.mundo == mundo) & (df.politica == politica)].set_index('cod')[col]
    b = df[(df.mundo == mundo) & (df.politica == base)].set_index('cod')[col]
    d = (a - b.reindex(a.index)).values
    rng = np.random.default_rng(semilla)
    m = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)])
    return d.mean(), np.quantile(m, 0.025), np.quantile(m, 0.975)


def guardar_bd(df):
    con = conectar()
    con.execute('DROP TABLE IF EXISTS sim_retro_resultado')
    con.execute('''CREATE TABLE sim_retro_resultado (mundo TEXT, cod INTEGER, ini TEXT, politica TEXT, plan TEXT, real TEXT,
                   commit_ TEXT, fin TEXT, tarde INTEGER, cumple INTEGER, penalidad REAL, costo REAL, total REAL, lead INTEGER,
                   intervino INTEGER, palancas TEXT, p_commit REAL, origen TEXT NOT NULL DEFAULT 'SIMULADO')''')
    d = df.rename(columns={'commit': 'commit_'}).copy()
    d['cumple'] = d.cumple.astype(int)
    d['intervino'] = d.intervino.astype(int)
    d = d[['mundo', 'cod', 'ini', 'politica', 'plan', 'real', 'commit_', 'fin', 'tarde', 'cumple', 'penalidad', 'costo', 'total',
           'lead', 'intervino', 'palancas', 'p_commit']]
    con.executemany('''INSERT INTO sim_retro_resultado (mundo, cod, ini, politica, plan, real, commit_, fin, tarde, cumple,
                       penalidad, costo, total, lead, intervino, palancas, p_commit) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    d.itertuples(index=False, name=None))
    con.commit()
    con.close()


def main(mundos=None, escala=1.0, R=600):
    con = conectar()
    todos = [r[0] for r in con.execute('SELECT id FROM sim_mundo ORDER BY id')]
    con.close()
    mundos = mundos or todos
    with ProcessPoolExecutor(max_workers=min(len(mundos), 8)) as ex:
        res = list(ex.map(correr_mundo, [(m, escala, R) for m in mundos]))
    df = pd.DataFrame([f for r in res for f in r])
    sufijo = '' if escala == 1.0 else f'_costo{escala:g}'
    df.to_csv(DATA / f'exp5_retrospectivo{sufijo}.csv', index=False)
    t = resumen(df)
    t.to_csv(DATA / f'exp5_resumen{sufijo}.csv')
    if escala == 1.0 and len(mundos) == len(todos):
        guardar_bd(df)
    return df, t


if __name__ == '__main__':
    args = sys.argv[1:]
    escala = 1.0
    if '--costo' in args:
        i = args.index('--costo')
        escala = float(args[i + 1])
        del args[i:i + 2]
    mundos = [int(a) for a in args] or None
    df, t = main(mundos, escala)
    pd.set_option('display.width', 250)
    pd.set_option('display.max_colwidth', 60)
    print(t.to_string())
    for col, titulo in [('total', 'penalidad + palancas'), ('total_ajustado', 'penalidad + palancas + costo comercial del plazo extra')]:
        print(f'\nDiferencia pareada de {titulo} (% del presupuesto) frente a A0, IC 95 % bootstrap sobre proyectos:')
        for m in df.mundo.unique():
            for p in POLITICAS[1:]:
                d, lo, hi = bootstrap_dif(df, m, p, col=col)
                print(f'  {m[:28]:28} {p[:46]:46} {d:+6.2f}  [{lo:+6.2f}, {hi:+6.2f}]')
