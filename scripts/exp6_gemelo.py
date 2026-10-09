"""Experimento 6: el DSS evaluado contra el gemelo de eventos discretos (datos SIMULADOS).

1. Genera la historia simulada de los 38 proyectos y calibra el gemelo para que «como se hizo» reproduzca las
   fechas reales (Tabla 3).
2. Guarda la historia en `gem_*` y como mundo 6 en `sim_*` (el DSS aprende de ese tareo, no de su propio motor).
3. Vuelve a correr toda la historia 2019-2026 con cada política (mismos números aleatorios) y compara.
4. Repite con otras semillas del gemelo (réplicas: misma calibración, otro azar) para medir la robustez.

Uso: py scripts/exp6_gemelo.py               (historia calibrada, ≈ 8 min con 6 núcleos)
     py scripts/exp6_gemelo.py --replicas N  (N realizaciones más del azar del gemelo; con la misma calibración e historia: mide solo ese azar)
     py scripts/exp6_gemelo.py --recalibrar  (vuelve a calibrar el gemelo; si no, usa los factores guardados)
Salidas: data/exp6_gemelo.csv, data/exp6_resumen.csv, data/exp6_decisiones.csv, tablas gem_* y mundo 6.
"""
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.datos import conectar                                                # noqa: E402
from dss.gemelo import exportar                                               # noqa: E402
from dss.gemelo.calendario import fecha                                       # noqa: E402
from dss.gemelo.calibrar import calibrar                                      # noqa: E402
from dss.gemelo.calibrar_dss import calibrar_crp, vector                      # noqa: E402
from dss.gemelo.generador import generar, SEMILLA                             # noqa: E402
from dss.gemelo.motor import Gemelo                                           # noqa: E402
from dss.gemelo.politicas import Planificador, politicas                      # noqa: E402

warnings.filterwarnings('ignore')
DATA = Path(__file__).resolve().parent.parent / 'data'
CO_PCT_DIA = 100 * 0.005 * 0.16          # costo comercial por día de plazo extra (supuesto de alpha_optimo)
DETALLE = ('A0', 'B1', 'D3', 'D4')       # políticas cuyo detalle hora a hora se guarda para la vista 3D


def correr(args):
    """Corre una política sobre una realización del gemelo. Devuelve filas por proyecto y decisiones."""
    semilla, i_pol, factores, fin_base = args
    warnings.filterwarnings('ignore')
    con = conectar()
    P, par = generar(con, semilla)
    muestra = [p.pid for p in P if p.en_muestra]
    plan = Planificador(con, fin_base)
    pol = politicas(plan, muestra, P)[i_pol]
    t0 = time.time()
    sim = Gemelo(P, par, pol, factores)
    res = sim.correr()
    costo = {}
    n_int = {}
    for pid, t, pal, c in res.palancas:
        costo[pid] = costo.get(pid, 0.0) + c
        n_int[pid] = n_int.get(pid, 0) + 1
    filas = []
    for p in P:
        comp = res.compromiso[p.pid]
        fin = fecha(res.fin[p.pid])
        tarde = max(0, (fin - comp).days)
        filas.append(dict(semilla=semilla, politica=pol.nombre, pid=p.pid, cod=p.cod, en_muestra=p.en_muestra,
                          compromiso=str(comp), fin=str(fin), tarde=tarde, penalidad=float(tarde), costo=costo.get(p.pid, 0.0),
                          lead=(comp - p.ini).days + 1, intervenciones=n_int.get(p.pid, 0),
                          p_inicio=getattr(pol, 'p_inicio', getattr(pol, 'p_cumplir', {})).get(p.pid, np.nan)))
    pal = [dict(semilla=semilla, politica=pol.nombre, pid=pid, t=t, tipo=x.tipo, proceso=x.proceso, valor=x.valor, costo=c)
           for pid, t, x, c in res.palancas]
    dec = [dict(semilla=semilla, politica=pol.nombre, pid=d[0], fecha=d[1], p_cumplir=d[2], penalidad_esp=d[3], total_mejor=d[4],
                palancas=' + '.join(d[5]), **(d[6] if len(d) > 6 else {})) for d in getattr(pol, 'decisiones', [])]
    con.close()
    sim.politica = None                          # tiene la conexión a la BD: no se puede enviar entre procesos
    return filas, pal, dec, (sim, res) if (semilla == SEMILLA and pol.nombre[:2] in DETALLE) else None, time.time() - t0


def resumen(df):
    m = df[df.en_muestra].copy()
    base = m[m.politica.str.startswith('A0')].set_index(['semilla', 'pid']).lead
    m['plazo_extra'] = m.lead.values - base.reindex(list(zip(m.semilla, m.pid))).values
    m['total'] = m.penalidad + m.costo
    m['total_ajustado'] = m.total + CO_PCT_DIA * m.plazo_extra
    g = m.groupby('politica', sort=False)
    t = g.agg(OTD=('tarde', lambda s: 100 * (s == 0).mean()), retraso_dias=('tarde', 'mean'), penalidad=('penalidad', 'mean'),
              costo_palancas=('costo', 'mean'), total=('total', 'mean'), total_ajustado=('total_ajustado', 'mean'),
              plazo=('lead', 'mean'), intervenciones=('intervenciones', 'mean')).round(2)
    por_sem = m.groupby(['politica', 'semilla']).agg(OTD=('tarde', lambda s: 100 * (s == 0).mean()), total=('total', 'mean'),
                                                       total_ajustado=('total_ajustado', 'mean'))
    t['OTD_sd_replicas'] = por_sem.groupby('politica').OTD.std().reindex(t.index).round(1)
    t['total_aj_sd_replicas'] = por_sem.groupby('politica').total_ajustado.std().reindex(t.index).round(2)
    return t, m


def auc(y, p):
    """AUC de p para separar y=1 de y=0 (probabilidad de que un atrasado tenga más riesgo que uno puntual)."""
    y, p = np.asarray(y, bool), np.asarray(p, float)
    if y.sum() == 0 or (~y).sum() == 0:
        return np.nan
    pos, neg = p[y], p[~y]
    return float(((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()))


def alerta_temprana(df, dec):
    """Calidad del re-pronóstico sin actuar (D0): AUC y Brier de P(atraso) a distintos puntos del plazo, contra A0 como línea base
    (la probabilidad histórica de atraso, igual para todos) y error de la fecha pronosticada."""
    o = dec[dec.politica.str.startswith('D0')].copy()
    fin = df[df.politica.str.startswith('A0') & df.en_muestra].set_index(['semilla', 'pid'])
    o['tarde'] = [fin.loc[(r.semilla, r.pid), 'tarde'] for r in o.itertuples()]
    o['atrasado'] = o.tarde > 0
    o['p_atraso'] = 1.0 - o.p_cumplir
    o['err_dias'] = [(np.datetime64(fin.loc[(r.semilla, r.pid), 'fin']) - np.datetime64(r.mediana)).astype(int) for r in o.itertuples()]
    base = o.groupby(['semilla', 'pid']).atrasado.first().mean()
    filas = []
    for a, b in [(0, .25), (.25, .5), (.5, .75), (.75, 1.1)]:
        g = o[(o.frac_plazo >= a) & (o.frac_plazo < b)]
        if len(g) < 5:
            continue
        filas.append(dict(tramo=f'{int(a * 100)}-{int(min(b, 1) * 100)} % del plazo', n=len(g), atrasados=int(g.atrasado.sum()),
                          AUC=round(auc(g.atrasado, g.p_atraso), 3), Brier=round(float(((g.p_atraso - g.atrasado) ** 2).mean()), 3),
                          Brier_base=round(float(((base - g.atrasado) ** 2).mean()), 3), MAE_fecha_dias=round(float(g.err_dias.abs().mean()), 1),
                          sesgo_fecha_dias=round(float(g.err_dias.mean()), 1)))
    return pd.DataFrame(filas)


def bootstrap(m, pol, col='total_ajustado', B=2000, semilla=0):
    a = m[m.politica == pol].set_index(['semilla', 'pid'])[col]
    b = m[m.politica.str.startswith('A0')].set_index(['semilla', 'pid'])[col].reindex(a.index)
    d = (a - b).values
    rng = np.random.default_rng(semilla)
    medias = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(B)])
    return d.mean(), np.quantile(medias, .025), np.quantile(medias, .975)


def main(replicas=4, recalibrar=False):
    t0 = time.time()
    con = conectar()
    P, par = generar(con, SEMILLA)
    guardados = None
    if not recalibrar and con.execute("SELECT 1 FROM sqlite_master WHERE name='gem_meta'").fetchone():
        r = con.execute("SELECT valor FROM gem_meta WHERE clave='factores'").fetchone()
        guardados = {int(k): v for k, v in json.loads(r[0]).items()} if r else None
    if guardados and set(guardados) == {p.pid for p in P}:
        factores = guardados
        print('Factores de calibración guardados')
    else:
        factores, mae, _, _ = calibrar(P, par)
        print(f'Calibración: error medio {mae:.2f} días laborables ({time.time() - t0:.0f} s)')
    sim0 = Gemelo(P, par, None, factores)
    res0 = sim0.correr()
    exportar.guardar_base(con, P, par, factores, SEMILLA)
    exportar.guardar_mundo(con, sim0, res0)
    exportar.guardar_esperas(con, sim0, res0)
    v, antes, despues = calibrar_crp(sim0, res0, [p.pid for p in P if not p.en_muestra])
    con.execute('INSERT INTO gem_meta VALUES (?,?)', ('lam_crp', json.dumps([float(x) for x in vector(v)])))
    print(f'Planificador (CRP) calibrado con los 13 proyectos fuera de la muestra: sesgo {antes.mean():+.1f} -> {despues.mean():+.1f} d, '
          f'error absoluto {np.abs(antes).mean():.1f} -> {np.abs(despues).mean():.1f} d; lambda = {v}')
    con.commit()
    fin_base = {pid: fecha(t) for pid, t in res0.fin.items()}
    semillas = [SEMILLA] + [SEMILLA + 101 * k for k in range(1, replicas + 1)]
    tareas = [(s, i, factores, fin_base) for s in semillas for i in range(8)]
    filas, pal, dec, detalles = [], [], [], []
    con.close()                                  # los procesos solo leen la BD mientras corren; se escribe al final
    with ProcessPoolExecutor(max_workers=6) as ex:
        for f, p_, d, det, seg in ex.map(correr, tareas):
            filas += f
            pal += p_
            dec += d
            if det is not None:
                detalles.append(det)
            print(f'  {f[0]["politica"]:42} semilla {f[0]["semilla"]}: {seg:.0f} s', flush=True)
    con = conectar()
    for sim, res in detalles:
        exportar.guardar_politica(con, sim, res, res.politica[:2])
    df = pd.DataFrame(filas)
    df.to_csv(DATA / 'exp6_gemelo.csv', index=False)
    pd.DataFrame(dec).to_csv(DATA / 'exp6_decisiones.csv', index=False)
    con.execute('DELETE FROM gem_resultado')
    con.executemany('INSERT INTO gem_resultado VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    [(r['politica'], r['semilla'], r['pid'], r['cod'], int(r['en_muestra']), r['compromiso'], r['fin'], r['tarde'],
                      r['penalidad'], r['costo'], r['lead'], r['intervenciones']) for r in filas])
    con.execute('DELETE FROM gem_palanca')
    con.executemany('INSERT INTO gem_palanca VALUES (?,?,?,?,?,?,?,?)',
                    [(x['politica'], x['semilla'], x['pid'], x['t'], x['tipo'], x['proceso'], x['valor'], x['costo']) for x in pal])
    con.commit()
    t, m = resumen(df)
    t.to_csv(DATA / 'exp6_resumen.csv')
    al = alerta_temprana(df, pd.DataFrame(dec))
    al.to_csv(DATA / 'exp6_alerta.csv', index=False)
    print('\nAlerta temprana (D0, sin actuar):')
    print(al.to_string(index=False))
    con.close()
    print(f'Listo en {time.time() - t0:.0f} s')
    return df, t, m


if __name__ == '__main__':
    a = sys.argv[1:]
    rep = int(a[a.index('--replicas') + 1]) if '--replicas' in a else 0
    df, t, m = main(rep, '--recalibrar' in a)
    pd.set_option('display.width', 250)
    print(t.to_string())
    print('\nDiferencia frente a A0 en penalidad + palancas + costo comercial del plazo (% del presupuesto), IC 95 %:')
    for pol in t.index[1:]:
        d, lo, hi = bootstrap(m, pol)
        print(f'  {pol:42} {d:+6.2f}  [{lo:+6.2f}, {hi:+6.2f}]')
