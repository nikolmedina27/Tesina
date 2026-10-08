"""Estudio retrospectivo sobre datos SIMULADOS: "cómo se hizo" contra "qué habría pasado con el DSS".

El mundo simulado (`sim_*`) es la verdad: HH reales por proceso, paradas y duración real de cada proyecto
(las simulaciones se condicionan a la duración real de los 25 proyectos). `Retro.replay` vuelve a
programar un proyecto con esa verdad —con o sin decisiones de gestión— y devuelve cuándo habría terminado.

Políticas comparadas por proyecto, siempre con la información disponible a la fecha de la decisión:
  A0 como se hizo            fecha cotizada por el criterio del cotizador; ejecución real
  A1 DSS fecha α = 0.80      fecha del Monte Carlo; misma ejecución real
  A2 DSS fecha α*            fecha con el cuantil crítico (newsvendor); misma ejecución real
  A3 fecha original + gestión al inicio
                             el DSS evalúa el riesgo de la fecha original y, si compensa, aplica la mejor palanca
  A4 fecha original + re-pronóstico al 40 %
                             a los 40 % del plazo real se re-pronostica con el avance y se corrige si compensa
  A5 sistema completo        fecha α* + re-pronóstico al 40 %

El resultado contrafactual es `fecha real + (duración con decisión − duración sin decisión)`: se ancla al
resultado real y solo se toma de la simulación la diferencia que causa la decisión.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from .c2_modelo import dataset, PhiQRF
from .c3_montecarlo import Cotizador, Proyecto, alpha_optimo, MTBF_DEFECTO
from .crp_engine import programar, WEEKMASK, N_PROC, EXTERNOS
from .datos import CargaTaller, mtbf_estimado
from .simulador import MUNDOS, MAQ_NOMBRE, cargar_reales, generar_paradas, disp_de_proyecto
from .whatif import buscar, multiplicadores

CHECKPOINT = 0.40            # fracción del plazo real en la que se re-pronostica
POLITICAS = ['A0 como se hizo', 'A1 DSS fecha α=0.80', 'A2 DSS fecha α*', 'A3 fecha original + gestión al inicio',
             'A4 fecha original + re-pronóstico 40 %', 'A5 sistema completo (α* + re-pronóstico 40 %)']


def desplazar(fecha, dias_lab):
    """Fecha + n días laborables (lunes a sábado; n puede ser negativo)."""
    return str(np.busday_offset(np.datetime64(fecha, 'D'), int(dias_lab), roll='backward', weekmask=WEEKMASK))


def dias_cal(a, b):
    return int((np.datetime64(b, 'D') - np.datetime64(a, 'D')).astype(int))


class Retro:
    """Mundo simulado `mundo_id` con la verdad de cada proyecto, listo para volver a programarlo."""

    def __init__(self, con, mundo_id):
        self.con = con
        self.mundo = next(m for m in MUNDOS if m.id == mundo_id)
        self.dias, self.D, _ = generar_paradas(self.mundo)
        self.carga = CargaTaller(con, self.dias)
        P, X = cargar_reales(con)
        self.P = P.set_index('pid')
        hh = pd.read_sql('''SELECT s.proyecto_id pid, pr.orden o, s.hh_real, s.dias_real FROM sim_proyecto_proceso s
                            JOIN proceso pr ON pr.id=s.proceso_id WHERE s.mundo_id=?''', con, params=(mundo_id,))
        self.hh = {pid: g.sort_values('o').hh_real.values for pid, g in hh.groupby('pid')}
        self.dias_real = {pid: g.sort_values('o').dias_real.values for pid, g in hh.groupby('pid')}
        self.crew = {cod: g.sort_values('orden').n_personas.values.astype(float) for cod, g in X.groupby('cod')}
        self.dias_plan = {cod: g.sort_values('orden').dias_plan.values.astype(float) for cod, g in X.groupby('cod')}
        self.df = dataset(con, mundo_id)

    def datos(self, pid):
        r = self.P.loc[pid]
        ext_real = self.dias_real[pid][EXTERNOS].astype(float)
        return SimpleNamespace(pid=pid, cod=int(r.cod), tipo=r.tipo, ton=float(r.ton), ini=r.ini, fp=r.fp, fr=r.fr,
                               n_real=int(r.n_real), hh_real=self.hh[pid], crew=self.crew[int(r.cod)],
                               ext_real=ext_real, ext_plan=self.dias_plan[int(r.cod)][EXTERNOS])

    def disp_efectiva(self, pid, ini):
        return CargaTaller.efectiva(disp_de_proyecto(self.dias, self.D, ini), self.carga.u(ini, excluir=pid))

    def replay(self, pid, mult=None, mult_desde=0, snapshot=None):
        """Duración (días laborables) con la verdad del mundo, con las palancas `mult` desde `mult_desde`."""
        d = self.datos(pid)
        o = programar(d.hh_real[None, :], d.crew, self.disp_efectiva(pid, d.ini), d.ext_real[None, :],
                      mult=mult, mult_desde=mult_desde, snapshot=snapshot)
        return dict(fin=int(o['fin'][0]), estado={t: v[0] for t, v in o['estado'].items()}, ini=o['ini'][0],
                    fin_proc=o['fin_proc'][0])


def _proyecto(retro, pid, fila):
    d = retro.datos(pid)
    return Proyecto(tipo=d.tipo, ton=d.ton, inicio=d.ini, presupuesto=100.0, pct_planchas=fila.pct_planchas,
                    piezas_por_t=fila.piezas_por_t, m2_pintura_t=fila.m2_pintura / d.ton, montaje=bool(fila.montaje),
                    id=pid, cuadrilla=d.crew, ext_dias=d.ext_plan)


def _resultado(commit, fin, ini, costo=0.0, palancas=(), p_commit=np.nan, intervino=False):
    tarde = max(dias_cal(commit, fin), 0)
    return dict(commit=commit, fin=fin, tarde=tarde, cumple=tarde == 0, penalidad=float(tarde),     # 1 %/día de 100
                costo=float(costo), total=float(tarde + costo), lead=dias_cal(ini, commit) + 1,
                intervino=bool(intervino), palancas=' + '.join(p.etiqueta() for p in palancas),
                p_commit=p_commit)


def _gestionar(retro, cot, proy, d, commit, t0, R, semilla, mtbf, costos, escala_costo):
    """Decide y aplica la mejor palanca (si compensa) en el día laborable t0. Devuelve (fin real con la decisión,
    evaluación elegida o None, probabilidad de cumplir `commit` antes de decidir)."""
    base = retro.replay(d.pid, snapshot=[t0] if t0 > 0 else None)
    if t0 == 0:
        p_t, restante, mult_desde = proy, None, 0
    else:
        frac = base['estado'][t0]
        restante = np.clip(1.0 - frac, 0.0, 1.0)
        base_date = np.busday_offset(np.datetime64(d.ini, 'D'), 0, roll='forward', weekmask=WEEKMASK)
        p_t = Proyecto(**{**proy.__dict__, 'inicio': str(np.busday_offset(base_date, t0, weekmask=WEEKMASK))})
        mult_desde = t0
    ranking, ev0 = buscar(cot, p_t, commit, R=R, semilla=semilla, mtbf=mtbf, restante=restante, costos=costos,
                          escala_costo=escala_costo)
    mejor = ranking[0]
    if not mejor.palancas or mejor.total >= ev0.total - 1e-9:
        return base['fin'], None, ev0.prob
    crew = d.crew
    m = multiplicadores(mejor.palancas, crew)
    fin = retro.replay(d.pid, mult=m, mult_desde=mult_desde)['fin']
    return fin, mejor, ev0.prob


def evaluar_proyecto(retro, pid, a_star=None, R=600, costos=None, escala_costo=1.0, politicas=None):
    """Aplica las 6 políticas al proyecto `pid` usando solo lo que se sabía a su fecha de inicio."""
    a_star = alpha_optimo() if a_star is None else a_star
    con, d = retro.con, retro.datos(pid)
    df = retro.df
    fila = df[df.pid == pid].iloc[0]
    tr = df[df.fin < d.ini]
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    mtbf = mtbf_estimado(con, retro.mundo.id, [cen[n] for n in MAQ_NOMBRE], d.ini)
    cot = Cotizador(con, PhiQRF().fit(tr), dias_cal=retro.dias)
    proy = _proyecto(retro, pid, fila)
    res = cot.cotizar(proy, R=1000, alpha=0.8, mtbf=mtbf, semilla=pid)
    f80, fas = str(res.fecha_alpha(0.80)), str(res.fecha_alpha(a_star))
    p_fp = res.prob_cumplir(d.fp)
    n_base = retro.replay(pid)['fin']
    t0 = max(1, int(round(CHECKPOINT * d.n_real)))
    salida = {}
    salida[POLITICAS[0]] = _resultado(d.fp, d.fr, d.ini, p_commit=p_fp)
    salida[POLITICAS[1]] = _resultado(f80, d.fr, d.ini, p_commit=res.prob_cumplir(f80))
    salida[POLITICAS[2]] = _resultado(fas, d.fr, d.ini, p_commit=res.prob_cumplir(fas))
    casos = [(POLITICAS[3], d.fp, 0), (POLITICAS[4], d.fp, t0), (POLITICAS[5], fas, t0)]
    for nombre, commit, t in casos:
        fin, mejor, p_antes = _gestionar(retro, cot, proy, d, commit, t, R, pid, mtbf, costos, escala_costo)
        fin_real = desplazar(d.fr, fin - n_base)
        salida[nombre] = _resultado(commit, fin_real, d.ini, costo=0.0 if mejor is None else mejor.costo,
                                    palancas=() if mejor is None else mejor.palancas, p_commit=p_antes,
                                    intervino=mejor is not None)
    filas = []
    for nombre, r in salida.items():
        filas.append(dict(mundo=retro.mundo.nombre, cod=d.cod, ini=d.ini, politica=nombre, plan=d.fp, real=d.fr, **r))
    return filas
