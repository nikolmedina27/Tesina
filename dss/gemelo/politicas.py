"""Políticas que se comparan en el gemelo (datos SIMULADOS).

  A0 Como se hizo            fecha del cotizador; nadie gestiona con datos
  B1 Regla del jefe de taller fecha del cotizador; cada 12 días compara avance real contra un plan lineal y, si va
                             atrasado, pone horas extra (y gente en soldeo si va muy atrasado). Es el comparador justo
  D1 DSS fecha α = 0.80      fecha del Monte Carlo; sin gestión
  D2 DSS fecha α*            fecha con el cuantil crítico (newsvendor); sin gestión
  D3 DSS gestión             fecha del cotizador; cada 12 días el DSS re-pronostica con el avance y aplica la palanca
                             que más baja penalidad esperada + costo (búsqueda con semillas comunes)
  D4 Sistema completo        fecha α* + gestión del DSS

El DSS (QRF + Monte Carlo sobre el CRP diario) solo ve lo que vería en la realidad: el tareo de los proyectos ya
terminados (para entrenar), las paradas registradas y el avance del proyecto. No ve la «verdad» del gemelo.
"""
import json
from datetime import date

import numpy as np
import pandas as pd

from ..c2_modelo import dataset, PhiQRF
from ..c3_montecarlo import Cotizador, Proyecto, alpha_optimo
from ..datos import mtbf_estimado
from ..simulador import MAQ_NOMBRE
from ..whatif import buscar
from .calendario import fecha
from .motor import Politica, Palanca
from .calibrar import dias_lab

MUNDO = 6


def _a_date(x):
    return date.fromisoformat(str(x)[:10])


class Planificador:
    """El DSS tal como lo usaría la empresa: entrenado con lo ya terminado a la fecha de cada decisión."""

    def __init__(self, con, fin_real, R=300):
        self.con = con
        self.R = R
        df = dataset(con, MUNDO)
        df['fin'] = df.pid.map(lambda pid: str(fin_real.get(pid, '2100-01-01')))
        self.df = df
        self.cot = Cotizador(con, None)
        r = con.execute("SELECT valor FROM gem_meta WHERE clave='lam_crp'").fetchone()
        if r:
            self.cot.lam = np.array(json.loads(r[0]), float)
        cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
        self.centros = [cen[n] for n in MAQ_NOMBRE]
        ext = pd.read_sql('''SELECT pp.proyecto_id pid, pr.orden o, pp.dias_plan d FROM proyecto_proceso pp
                             JOIN proceso pr ON pr.id=pp.proceso_id WHERE pr.orden IN (7, 12)''', con)
        self.ext = {pid: g.sort_values('o').d.values.astype(float) for pid, g in ext.groupby('pid')}
        self._cache = {}
        self.escala = {}
        self.esp = pd.read_sql('SELECT pid, fin, ing_dias, compra_dias FROM gem_espera', con)

    def _predictor(self, hoy):
        tr = self.df[self.df.fin < str(hoy)]
        clave = tuple(sorted(tr.pid.unique()))
        if clave not in self._cache:
            self._cache[clave] = PhiQRF().fit(tr)
        return self._cache[clave]

    def proyecto(self, p, inicio):
        fila = self.df[self.df.pid == p.pid].iloc[0]
        return Proyecto(tipo=p.tipo, ton=p.ton, inicio=str(inicio), presupuesto=100.0, pct_planchas=float(fila.pct_planchas),
                        piezas_por_t=float(fila.piezas_por_t), m2_pintura_t=float(fila.m2_pintura / p.ton),
                        montaje=bool(fila.montaje), id=p.pid, cuadrilla=p.crew, ext_dias=self.ext.get(p.pid))

    def esperas(self, p, hoy, R, sim=None, semilla=0):
        """Muestras (R,) de los días que faltan de ingeniería y de espera de material, remuestreando los proyectos
        terminados antes de `hoy` y condicionando a lo que ya transcurrió en este proyecto."""
        rng = np.random.default_rng([semilla, p.pid, hoy.toordinal() % 1000])
        pas = self.esp[self.esp.fin < str(hoy)]
        out = {}
        for col, clave, a_idx in (('ing_dias', 'ing', 0), ('compra_dias', 'compra', 1)):
            hist = pas[col].values if len(pas) >= 4 else np.exp(rng.normal(np.log(6 if clave == 'ing' else 16), 0.4, 12))
            transcurrido, hecho = 0.0, False
            if sim is not None:
                a = sim.avance(p.pid)
                hecho = a[a_idx] >= 0.999
                if clave == 'ing':
                    transcurrido = dias_lab(p.ini, hoy)
                else:
                    pk = [x[2] for x in sim.paquetes if x[0] == p.pid]
                    transcurrido = dias_lab(fecha(min(pk)), hoy) if pk else 0.0
            if hecho:
                out[clave] = np.zeros(R)
                continue
            cand = hist[hist > transcurrido + 0.5]
            if len(cand) == 0:
                cand = np.array([transcurrido + 2.0])
            out[clave] = np.maximum(rng.choice(cand, R) - transcurrido, 1.0)
        return out

    def mtbf(self, hoy):
        return mtbf_estimado(self.con, MUNDO, self.centros, str(hoy))

    def anclar(self, p, sim=None):
        """Factor de ritmo del proyecto: el que hace que el pronóstico mediano coincida con el plazo que estimó el cotizador
        (el DSS corrige al experto en vez de ignorarlo). Se calcula una vez, al iniciar el proyecto."""
        if p.pid in self.escala:
            return self.escala[p.pid]
        self.cot.predictor = self._predictor(p.ini)
        esp = self.esperas(p, p.ini, 200, None, semilla=p.pid)
        meta = dias_lab(p.ini, p.fp)
        lo, hi = 0.3, 4.0
        for _ in range(9):
            s = float(np.sqrt(lo * hi))
            self.cot.escala = s
            d = float(np.median(self.cot.cotizar(self.proyecto(p, p.ini), R=200, mtbf=self.mtbf(p.ini), semilla=p.pid,
                                                 esperas=esp).dias_lab))
            lo, hi = (s, hi) if d < meta else (lo, s)
        self.escala[p.pid] = float(np.sqrt(lo * hi))
        return self.escala[p.pid]

    def cotizar(self, p, hoy, alpha, restante=None, R=1000, sim=None):
        self.cot.escala = 1.0
        self.cot.escala = self.anclar(p, sim)
        self.cot.predictor = self._predictor(hoy)
        esp = self.esperas(p, hoy, R, sim, semilla=p.pid)
        if restante is not None:
            restante = np.array(restante, float)
            restante[:2] = 1.0                      # ingeniería y compras: lo que falta ya viene como espera
        return self.cot.cotizar(self.proyecto(p, hoy), R=R, alpha=alpha, mtbf=self.mtbf(hoy), semilla=p.pid,
                                restante=restante, esperas=esp)

    def mejor_palanca(self, p, hoy, compromiso, restante, semilla, sim=None):
        self.cot.escala = self.anclar(p, sim)
        self.cot.predictor = self._predictor(hoy)
        restante = np.array(restante, float)
        restante[:2] = 1.0
        ranking, base = buscar(self.cot, self.proyecto(p, hoy), str(compromiso), R=self.R, semilla=semilla,
                               mtbf=self.mtbf(hoy), restante=restante, n_finalistas=4, max_palancas=3, compras=True,
                               ejecutables=True, esperas=self.esperas(p, hoy, self.R, sim, semilla=semilla))
        mejor = ranking[0]
        if not mejor.palancas or mejor.total >= base.total - 0.05:
            return [], base, mejor
        return [Palanca(x.tipo, x.proceso, x.valor) for x in mejor.palancas], base, mejor


class ComoSeHizo(Politica):
    nombre = 'A0 como se hizo'


class ReglaJefe(Politica):
    """Gestión «a ojo»: avance ponderado por HH contra un plan lineal entre inicio y fecha comprometida."""
    nombre = 'B1 regla del jefe de taller'

    def __init__(self, muestra):
        self.aplica_a = set(muestra)

    def revisar(self, sim, p, t):
        hoy = fecha(t)
        comp = sim.compromiso[p.pid]
        plan = min(1.0, dias_lab(p.ini, hoy) / max(dias_lab(p.ini, comp), 1))
        a = sim.avance(p.pid)
        peso = p.hh_ratio
        real = float(np.average(a, weights=peso))
        if real >= plan - 0.10:
            return []
        pal = [Palanca('horas_extra', 7), Palanca('horas_extra', 8)]
        if real < plan - 0.20:
            pal.append(Palanca('personas', 8, 2))
        return pal


class Observador(Politica):
    """Monitoreo sin actuar: cada 12 días re-pronostica con el avance real y solo registra. Como no toca la planta, el mundo
    es idéntico al de A0 y mide la calidad de la alerta temprana sin contaminar nada."""
    nombre = 'D0 monitoreo (alerta temprana)'

    def __init__(self, plan, muestra):
        self.plan = plan
        self.aplica_a = set(muestra)
        self.decisiones = []

    def revisar(self, sim, p, t):
        a = sim.avance(p.pid)
        if a.min() >= 0.999:
            return []
        hoy = fecha(t)
        comp = sim.compromiso[p.pid]
        res = self.plan.cotizar(p, hoy, 0.8, restante=1.0 - a, R=400, sim=sim)
        plan_dias = max(dias_lab(p.ini, comp), 1)
        extra = dict(frac_plazo=dias_lab(p.ini, hoy) / plan_dias, mediana=str(res.fecha_alpha(0.5)), p80=str(res.fecha_alpha(0.8)),
                     avance=float(np.average(a, weights=p.hh_ratio)))
        self.decisiones.append((p.pid, str(hoy), res.prob_cumplir(str(comp)), np.nan, np.nan, [], extra))
        return []


class FechaDSS(Politica):
    def __init__(self, plan, muestra, alpha, nombre):
        self.plan, self.alpha, self.nombre = plan, alpha, nombre
        self.muestra = set(muestra)
        self.p_cumplir = {}

    def compromiso(self, sim, p):
        if p.pid not in self.muestra:
            return p.fp
        res = self.plan.cotizar(p, p.ini, self.alpha, sim=sim)
        f = _a_date(res.fecha_alpha(self.alpha))
        self.p_cumplir[p.pid] = res.prob_cumplir(str(f))
        return f


class GestionDSS(Politica):
    def __init__(self, plan, muestra, nombre, alpha=None):
        self.plan, self.nombre, self.alpha = plan, nombre, alpha
        self.aplica_a = set(muestra)
        self.p_inicio = {}
        self.decisiones = []

    def compromiso(self, sim, p):
        if p.pid not in self.aplica_a or self.alpha is None:
            if p.pid in self.aplica_a:
                self.p_inicio[p.pid] = self.plan.cotizar(p, p.ini, 0.8, sim=sim).prob_cumplir(str(p.fp))
            return p.fp
        res = self.plan.cotizar(p, p.ini, self.alpha, sim=sim)
        f = _a_date(res.fecha_alpha(self.alpha))
        self.p_inicio[p.pid] = res.prob_cumplir(str(f))
        return f

    def revisar(self, sim, p, t):
        a = sim.avance(p.pid)
        if a.min() >= 0.999:
            return []
        hoy = fecha(t)
        comp = sim.compromiso[p.pid]
        pal, base, mejor = self.plan.mejor_palanca(p, hoy, comp, 1.0 - a, semilla=p.pid * 31 + hoy.toordinal() % 97, sim=sim)
        self.decisiones.append((p.pid, str(hoy), base.prob, base.penalidad, mejor.total, [x.etiqueta() for x in mejor.palancas]))
        return pal


class ColchonFijo(Politica):
    """Competidor sin modelo (estilo Mundt & Lödding): la fecha del cotizador más N días laborables, con N el cuantil 80 %
    del atraso de los proyectos de calibración (los 13 fuera de la muestra)."""
    def __init__(self, n):
        self.n = int(n)
        self.nombre = f'C1 colchón fijo (+{self.n} d lab.)'

    def compromiso(self, sim, p):
        from .calendario import LABORABLES
        import bisect
        i = bisect.bisect_right([d.toordinal() for d in LABORABLES], p.fp.toordinal()) - 1
        return LABORABLES[i + self.n]


def colchon_calibrado(proyectos):
    """N de días laborables: cuantil 80 % del atraso real (fecha real - fecha del cotizador) de los proyectos fuera de la muestra."""
    atr = [max(0, dias_lab(p.fp, p.fr)) for p in proyectos if not p.en_muestra]
    return int(np.ceil(np.quantile(atr, 0.8))) if atr else 3


def politicas(plan, muestra, proyectos=None):
    a_star = alpha_optimo()
    extra = [ColchonFijo(colchon_calibrado(proyectos))] if proyectos else []
    return [ComoSeHizo(), ReglaJefe(muestra), *extra, Observador(plan, muestra),
            FechaDSS(plan, muestra, 0.80, 'D1 DSS fecha α=0.80'), FechaDSS(plan, muestra, a_star, 'D2 DSS fecha α*'),
            GestionDSS(plan, muestra, 'D3 DSS gestión (fecha original)'),
            GestionDSS(plan, muestra, 'D4 sistema completo (α* + gestión)', alpha=a_star)]
