"""Programación automática de la cartera: asigna fechas a todos los proyectos que comparten la planta.

Es C3 con la carga REAL del taller: en vez de suponer la carga de los otros proyectos (κ·u de `CargaTaller`),
programa juntos todos los proyectos en curso (y, si se pide, uno nuevo) con `multiproyecto.programar_multi`,
en R réplicas Monte Carlo con números aleatorios comunes:

- horas por proceso: φ del QRF (C2) con dependencia entre procesos, solo lo que falta de cada proyecto;
- máquinas: fallas aleatorias con el MTBF registrado + los preventivos programados reales (mantenimiento);
- servicios externos con su variabilidad.

Regla de prioridad (fija para toda la cartera, no por proyecto):
- 'penalidad' (por defecto): primero el proyecto con mayor penalidad esperada si se lo atiende después; se estima
  con una primera pasada por fecha comprometida y se reordena de mayor a menor penalidad en riesgo.
- 'edd': fecha comprometida más cercana primero.

Para un proyecto nuevo con meta ("julio" = último día hábil del mes, o una fecha) calcula además la fecha de
inicio más tardía que todavía cumple la meta con probabilidad α (búsqueda binaria sobre el inicio).
Propone mover preventivos que chocan con proyectos en riesgo; nunca los mueve (eso lo decide quien aprueba).
"""
import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from .c3_montecarlo import P_PENALIDAD, SIGMA_EXT, TAUS, Proyecto, muestrear_disp, muestrear_phi
from .crp_engine import MAQUINAS, N_PROC, WEEKMASK
from .datos import cuadrilla, dias_externos
from .mantenimiento import disponibilidad_futura
from .multiproyecto import programar_multi

T_PLAN = 300
REGLAS = ('penalidad', 'edd')


@dataclass
class ProyectoPlan:
    id: int | None
    codigo: str
    proy: Proyecto
    compromiso: str | None = None        # fecha comprometida (o meta del proyecto nuevo)
    avance0: np.ndarray | None = None    # (13,) fracción hecha por proceso
    alpha: float = 0.8
    nuevo: bool = False


def ultimo_habil_del_mes(anio, mes):
    d = date(anio, mes, calendar.monthrange(anio, mes)[1])
    return str(np.busday_offset(np.datetime64(d.isoformat(), 'D'), 0, roll='backward', weekmask=WEEKMASK))


def meta_a_fecha(meta):
    """'2027-07' → último día hábil de julio de 2027; 'AAAA-MM-DD' → esa fecha; vacío → None (lo antes posible)."""
    if not meta:
        return None
    meta = str(meta).strip()
    if len(meta) == 7:
        a, m = meta.split('-')
        return ultimo_habil_del_mes(int(a), int(m))
    return str(np.datetime64(meta[:10], 'D'))


class Cartera:
    """Simulador de la cartera con números aleatorios comunes: las mismas muestras se reutilizan en cada pasada,
    así las diferencias entre órdenes de prioridad, inicios o preventivos se deben a la decisión y no al azar."""

    def __init__(self, cot, proyectos, hoy, preventivos, maquinas, mtbf, R=200, semilla=7, T=T_PLAN):
        self.cot, self.pp, self.R, self.T = cot, list(proyectos), R, T
        self.hoy = str(hoy)[:10]
        self.base = np.busday_offset(np.datetime64(self.hoy, 'D'), 0, roll='forward', weekmask=WEEKMASK)
        self.maquinas = list(maquinas)
        self.preventivos = list(preventivos)
        rng = np.random.default_rng(semilla)
        self.muestras = []
        for p in self.pp:
            pr = p.proy
            q_phi, rho = cot.predictor.cuantiles(pr, TAUS)
            hh = pr.ton * cot.rv.loc[pr.tipo].values * muestrear_phi(q_phi, rho, R, rng) * cot.escala
            ext = dias_externos(cot.par_ext, pr.ton) * cot.escala * np.exp(rng.normal(0, SIGMA_EXT, (R, 2)))
            self.muestras.append(dict(hh=hh, ext=ext, cuadrilla=cuadrilla(cot.par_cuad, pr.ton)))
        self.d_fallas = muestrear_disp(R, T, np.asarray(mtbf, float), rng, planificado=False)   # (R, T, 4)

    def indice(self, fecha):
        return max(0, int(np.busday_count(self.base, np.datetime64(str(fecha)[:10], 'D'), weekmask=WEEKMASK)))

    def fecha(self, k):
        return str(np.busday_offset(self.base, int(k), weekmask=WEEKMASK))

    def disp(self, preventivos=None):
        prev = disponibilidad_futura(self.preventivos if preventivos is None else preventivos, self.hoy, self.T, self.maquinas)
        return self.d_fallas * prev[None]

    def simular(self, orden, inicios=None, preventivos=None, guardar_uso=False):
        """orden: lista de posiciones de self.pp de mayor a menor prioridad. inicios: {pos: índice de día}."""
        prio = {pos: k for k, pos in enumerate(orden)}
        entrada = []
        for pos, (p, m) in enumerate(zip(self.pp, self.muestras)):
            ini = (inicios or {}).get(pos, self.indice(max(p.proy.inicio, self.hoy)))
            entrada.append(dict(hh=m['hh'], cuadrilla=m['cuadrilla'], ext=m['ext'], inicio=ini, prioridad=prio[pos], avance0=p.avance0))
        return programar_multi(entrada, self.disp(preventivos), guardar_uso=guardar_uso, dias_max=self.T)

    def metricas(self, pos, o):
        """Fechas P50/P80, P(cumplir), atraso y penalidad esperada de un proyecto en una simulación."""
        p = self.pp[pos]
        n = np.nan_to_num(o['fin'], nan=self.T).astype(int)
        fechas = np.busday_offset(self.base, np.maximum(n - 1, 0), weekmask=WEEKMASK)
        out = dict(p50=str(np.sort(fechas)[len(fechas) // 2]), p80=str(np.sort(fechas)[int(0.8 * (len(fechas) - 1))]),
                   no_termina=float(np.mean(np.isnan(o['fin']))))
        if p.compromiso:
            c = np.datetime64(p.compromiso[:10], 'D')
            atraso = np.maximum((fechas - c).astype(int), 0)
            out.update(prob_cumplir=round(float(np.mean(fechas <= c)), 4), atraso_esperado=round(float(atraso.mean()), 2),
                       penalidad=round(float(p.proy.presupuesto * P_PENALIDAD * atraso.mean()), 2))
        else:
            out.update(prob_cumplir=None, atraso_esperado=None, penalidad=0.0)
        return out

    def orden_por(self, regla):
        edd = sorted(range(len(self.pp)), key=lambda i: (self.pp[i].compromiso or '9999', self.pp[i].codigo))
        if regla == 'edd':
            return edd
        o = self.simular(edd)
        pen = [self.metricas(i, o[i])['penalidad'] for i in range(len(self.pp))]
        return sorted(range(len(self.pp)), key=lambda i: (-pen[i], self.pp[i].compromiso or '9999', self.pp[i].codigo))

    def inicio_mas_tardio(self, pos, orden):
        """Último día de inicio con el que el proyecto `pos` todavía cumple su meta con probabilidad α."""
        p = self.pp[pos]
        if not p.compromiso:
            return None
        lo, hi = self.indice(max(p.proy.inicio, self.hoy)), self.indice(p.compromiso)
        cumple = lambda s: self.metricas(pos, self.simular(orden, {pos: s})[pos])['prob_cumplir'] >= p.alpha
        if not cumple(lo):
            return None
        while lo < hi:
            mid = (lo + hi + 1) // 2
            lo, hi = (mid, hi) if cumple(mid) else (lo, mid - 1)
        return self.fecha(lo)


def _procesos(cart, pos, o):
    """Inicio y fin P50 de cada proceso (mediana entre réplicas) en fechas."""
    filas = []
    for j in range(N_PROC):
        a, b = o['ini'][:, j], o['fin_proc'][:, j]
        if np.all(np.isnan(a)) or np.all(np.isnan(b)):
            continue
        ia, ib = int(np.nanmedian(a)), int(np.nanmedian(b))
        filas.append(dict(proceso=j + 1, inicio=cart.fecha(ia), fin=cart.fecha(max(ib - 1, ia)),
                          hh=round(float(np.median(cart.muestras[pos]['hh'][:, j] * (1 - (0 if cart.pp[pos].avance0 is None else cart.pp[pos].avance0[j])))), 1)))
    return filas


def proponer(cot, proyectos, hoy, preventivos, maquinas, mtbf, regla='penalidad', R=200, semilla=7, sugerir_preventivos=True):
    """Plan propuesto para la cartera. preventivos: dicts con id, maquina, programada_para, duracion_h, titulo."""
    if regla not in REGLAS:
        raise ValueError('Regla de prioridad no válida')
    if not proyectos:
        return dict(regla=regla, hoy=str(hoy)[:10], proyectos=[], carga=[], sugerencias=[], fechas=[])
    cart = Cartera(cot, proyectos, hoy, preventivos, maquinas, mtbf, R=R, semilla=semilla)
    orden = cart.orden_por(regla)
    o = cart.simular(orden, guardar_uso=True)
    out = []
    for k, pos in enumerate(orden):
        p = cart.pp[pos]
        m = cart.metricas(pos, o[pos])
        fila = dict(id=p.id, codigo=p.codigo, prioridad=k + 1, compromiso=p.compromiso, alpha=p.alpha, nuevo=p.nuevo,
                    inicio=max(p.proy.inicio, cart.hoy), procesos=_procesos(cart, pos, o[pos]), **m)
        if p.nuevo:
            fila['inicio_mas_tardio'] = cart.inicio_mas_tardio(pos, orden)
        out.append(fila)
    # carga diaria de cada máquina (horas, promedio entre réplicas) y capacidad con preventivos
    uso = sum(x['uso'].mean(axis=0) for x in o)                           # (T, 4)
    cap = 8.0 * disponibilidad_futura(cart.preventivos, cart.hoy, cart.T, cart.maquinas)
    ult = int(max([np.nanmax(np.nan_to_num(x['fin'], nan=0)) for x in o] + [20]))
    dias = min(cart.T, ult + 5)
    carga = [dict(maquina=mq, horas=[round(float(v), 2) for v in uso[:dias, k]], capacidad=[round(float(v), 2) for v in cap[:dias, k]])
             for k, mq in enumerate(cart.maquinas)]
    sug = _sugerir_preventivos(cart, orden, o, out) if sugerir_preventivos and cart.preventivos else []
    return dict(regla=regla, hoy=cart.hoy, R=R, proyectos=out, carga=carga, fechas=[cart.fecha(k) for k in range(dias)], sugerencias=sug)


def _sugerir_preventivos(cart, orden, o, filas):
    """Para cada proyecto en riesgo, prueba postergar el preventivo que cae dentro de su habilitado hasta el día
    siguiente al fin P50 de ese habilitado. Solo se sugiere si sube su P(cumplir) en ≥ 2 puntos."""
    por_pos = {orden[k]: f for k, f in enumerate(filas)}
    sug = []
    for pos, f in por_pos.items():
        if f['prob_cumplir'] is None or f['prob_cumplir'] >= f['alpha']:
            continue
        for pv in cart.preventivos:
            if not pv.get('id') or pv.get('maquina') not in cart.maquinas or not pv.get('programada_para'):
                continue                                                       # solo órdenes reales se pueden reprogramar
            j = MAQUINAS[cart.maquinas.index(pv['maquina'])] + 1                 # proceso (1-based) de esa máquina
            pr = next((x for x in f['procesos'] if x['proceso'] == j), None)
            if not pr or not (pr['inicio'] <= pv['programada_para'][:10] <= pr['fin']):
                continue
            nueva = str(np.busday_offset(np.datetime64(pr['fin'], 'D'), 1, weekmask=WEEKMASK))
            otros = [dict(x, programada_para=nueva) if x is pv else x for x in cart.preventivos]
            m2 = cart.metricas(pos, cart.simular(orden, preventivos=otros)[pos])
            gana = m2['prob_cumplir'] - f['prob_cumplir']
            if gana >= 0.02:
                sug.append(dict(orden_id=pv.get('id'), maquina=pv['maquina'], titulo=pv.get('titulo'), de=pv['programada_para'][:10], a=nueva,
                                proyecto=f['codigo'], prob_antes=f['prob_cumplir'], prob_despues=m2['prob_cumplir'],
                                penalidad_antes=f['penalidad'], penalidad_despues=m2['penalidad']))
            if len(sug) >= 3:
                return sug
    return sug


def diferencias(aprobado, propuesto):
    """Qué cambia del plan aprobado al propuesto, por proyecto (días laborables de diferencia en el fin P80)."""
    if not aprobado:
        return []
    antes = {(x['id'], x['codigo']): x for x in aprobado['proyectos']}
    out = []
    for x in propuesto['proyectos']:
        a = antes.get((x['id'], x['codigo']))
        if not a:
            out.append(dict(codigo=x['codigo'], cambio='nuevo en el plan'))
            continue
        d80 = int(np.busday_count(a['p80'], x['p80'], weekmask=WEEKMASK)) if x['p80'] >= a['p80'] else -int(np.busday_count(x['p80'], a['p80'], weekmask=WEEKMASK))
        dp = None if x['prob_cumplir'] is None or a['prob_cumplir'] is None else round(x['prob_cumplir'] - a['prob_cumplir'], 3)
        if d80 or (dp and abs(dp) >= 0.05) or a['prioridad'] != x['prioridad']:
            out.append(dict(codigo=x['codigo'], p80_antes=a['p80'], p80_despues=x['p80'], dias=d80, prioridad_antes=a['prioridad'],
                            prioridad_despues=x['prioridad'], prob_antes=a['prob_cumplir'], prob_despues=x['prob_cumplir'], cambio_prob=dp))
    for k, a in antes.items():
        if not any((x['id'], x['codigo']) == k for x in propuesto['proyectos']):
            out.append(dict(codigo=a['codigo'], cambio='sale del plan'))
    return out
