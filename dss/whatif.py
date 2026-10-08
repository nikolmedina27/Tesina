"""What-if y búsqueda automática de escenarios sobre el cotizador (C3).

Una **palanca** es una decisión de gestión que cambia la capacidad de un proceso (más gente, segundo turno,
horas extra, expeditar un servicio externo). Un **escenario** es un conjunto de palancas. Cada escenario se
evalúa con el mismo Monte Carlo y **las mismas semillas** (números aleatorios comunes): la diferencia entre
escenarios se debe a la decisión y no al azar.

Costos: todo en % del presupuesto del proyecto (la penalidad es 1 %/día). Los costos de las palancas son
SUPUESTOS (COSTOS) hasta que la empresa entregue los reales; por eso `evaluar` permite escalarlos y el estudio
retrospectivo reporta la sensibilidad.
"""
from dataclasses import dataclass, field

import numpy as np

from .c3_montecarlo import P_PENALIDAD, Proyecto
from .crp_engine import MAQUINAS, EXTERNOS, N_PROC, HORAS_TURNO
from .datos import cuadrilla as cuadrilla_tipica

NOMBRES = ['Ingeniería', 'Compra de material', 'Habilitado · sierra cinta', 'Habilitado · cizalla-punzonadora',
           'Habilitado · mesa CNC', 'Roscado de barra lisa', 'Doblez (externo)', 'Armado', 'Soldeo', 'Limpieza',
           'Despacho a pintura', 'Granallado y pintura (externo)', 'Despacho a obra']
CONTRATISTAS = [7, 8, 9]                       # armado, soldeo, limpieza (índices 0-based)
INTERNOS = [0, 1, 10, 12]

# SUPUESTOS de costo (a validar con la empresa); se pueden sobrescribir pasando `costos=` a las funciones
COSTOS = dict(
    frac_mano_obra=0.30,        # mano de obra directa = 30 % del presupuesto
    prima_contratista=0.10,     # sobreprecio por acelerar a un contratista (se les paga por kg)
    recargo_hora_extra=1.5,     # una hora extra cuesta 1.5 veces
    horas_extra_dia=2.0,        # horas extra por día
    mult_hora_extra=1.0 + 2.0 / HORAS_TURNO,   # capacidad con horas extra
    expeditar_externo=0.01,     # expeditar un servicio externo cuesta 1 % del presupuesto
    mult_expeditar=1.25,        # y lo acorta un 20 % (capacidad × 1.25)
)


@dataclass(frozen=True)
class Palanca:
    tipo: str          # 'personas' | 'turno2' | 'horas_extra' | 'expeditar'
    proceso: int       # índice 0-based del proceso
    valor: int = 1     # personas adicionales (solo 'personas')

    def etiqueta(self):
        n = NOMBRES[self.proceso]
        return {'personas': f'+{self.valor} persona(s) en {n}', 'turno2': f'Segundo turno en {n}',
                'horas_extra': f'Horas extra en {n}', 'expeditar': f'Expeditar {n}'}[self.tipo]


def candidatas(compras=False, ejecutables=False):
    """Palancas que la búsqueda automática prueba (una por una y luego combinadas). `compras`: agrega expeditar la
    compra de material; `ejecutables`: solo las que la planta puede ejecutar (sin horas extra en oficinas ni despacho)."""
    c = []
    for j in CONTRATISTAS:
        c += [Palanca('personas', j, 1), Palanca('personas', j, 2)]
    c += [Palanca('turno2', j) for j in MAQUINAS]
    c += [Palanca('horas_extra', j) for j in (CONTRATISTAS if ejecutables else INTERNOS + CONTRATISTAS)]
    c += [Palanca('expeditar', j) for j in EXTERNOS]
    if compras:
        c.append(Palanca('expeditar', 1))
    return c


def multiplicadores(palancas, crew):
    """Vector `mult` (13,) de capacidad que producen las palancas (sobre la cuadrilla base `crew`)."""
    m = np.ones(N_PROC)
    for p in palancas:
        if p.tipo == 'personas':
            m[p.proceso] *= (crew[p.proceso] + p.valor) / crew[p.proceso]
        elif p.tipo == 'turno2':
            m[p.proceso] *= 2.0
        elif p.tipo == 'horas_extra':
            m[p.proceso] *= COSTOS['mult_hora_extra']
        elif p.tipo == 'expeditar':
            m[p.proceso] *= COSTOS['mult_expeditar']
    return m


def costo_palancas(palancas, crew, hh_prom, dias_activos, hh_total, costos=None, escala=1.0):
    """Costo de las palancas en % del presupuesto. `hh_prom` (13,) HH esperadas por proceso, `dias_activos`
    (13,) días en que el proceso trabaja desde que se aplica la palanca, `hh_total` HH esperadas del proyecto."""
    c = dict(COSTOS, **(costos or {}))
    c_hh = c['frac_mano_obra'] * 100.0 / max(hh_total, 1.0)           # % del presupuesto por HH
    total = 0.0
    for p in palancas:
        j = p.proceso
        d = float(dias_activos[j])
        if p.tipo == 'personas':
            if j in CONTRATISTAS:
                total += c['prima_contratista'] * c_hh * hh_prom[j] * p.valor / (crew[j] + p.valor)
            else:
                total += p.valor * d * HORAS_TURNO * c_hh
        elif p.tipo == 'turno2':
            total += d * HORAS_TURNO * c_hh * crew[j]
        elif p.tipo == 'horas_extra':
            total += max(crew[j], 1) * d * c['horas_extra_dia'] * c_hh * c['recargo_hora_extra']
        elif p.tipo == 'expeditar':
            total += c['expeditar_externo'] * 100.0
    return float(total * escala)


@dataclass
class Evaluacion:
    palancas: tuple
    prob: float                  # P(cumplir la fecha objetivo)
    penalidad: float             # penalidad esperada (% del presupuesto)
    costo: float                 # costo de las palancas (% del presupuesto)
    dias_medios: float           # días laborables medios hasta terminar
    fecha_alpha: str             # fecha con confianza α del escenario
    res: object = field(default=None, repr=False)

    @property
    def total(self):
        return self.penalidad + self.costo

    def a_dict(self):
        return dict(palancas=[p.etiqueta() for p in self.palancas], prob=self.prob, penalidad=self.penalidad,
                    costo=self.costo, total=self.total, dias_medios=self.dias_medios, fecha_alpha=self.fecha_alpha)


def _evaluar(cot, proy, palancas, fecha_obj, R, semilla, mtbf, restante, mult_desde, costos, escala_costo, alpha, p_pen, esperas=None):
    crew = proy.cuadrilla if proy.cuadrilla is not None else cuadrilla_tipica(cot.par_cuad, proy.ton)
    mult = multiplicadores(palancas, crew) if palancas else None
    res = cot.cotizar(proy, R=R, alpha=alpha, mtbf=mtbf, semilla=semilla, restante=restante,
                      mult=mult, mult_desde=mult_desde, esperas=esperas)
    prob = res.prob_cumplir(fecha_obj)
    pen = 100.0 * p_pen * float(res.dias_atraso(fecha_obj).mean())          # % del presupuesto
    costo = 0.0
    if palancas:
        prog = res.programa
        dias = np.array([max(0, (b - max(a, mult_desde)) if (a is not None and b is not None) else 0) for a, b in prog], float)
        hh_total = float(proy.ton * cot.rv.loc[proy.tipo].values.sum())      # HH del proyecto completo (ratio)
        costo = costo_palancas(palancas, crew, res.hh.mean(axis=0), dias, hh_total, costos, escala_costo)
    return Evaluacion(tuple(palancas), prob, pen, costo, float(res.dias_lab.mean()), str(res.fecha_alpha(alpha)), res)


def evaluar(cot, proy, palancas, fecha_obj, R=1000, semilla=1, mtbf=None, restante=None, mult_desde=0,
            costos=None, escala_costo=1.0, alpha=0.8, p_pen=P_PENALIDAD):
    """Evalúa un escenario (lista de palancas) contra la fecha objetivo con el Monte Carlo del cotizador."""
    from .c3_montecarlo import MTBF_DEFECTO
    mtbf = MTBF_DEFECTO if mtbf is None else mtbf
    return _evaluar(cot, proy, list(palancas), fecha_obj, R, semilla, mtbf, restante, mult_desde, costos,
                    escala_costo, alpha, p_pen)


def buscar(cot, proy, fecha_obj, R=1000, semilla=1, mtbf=None, restante=None, mult_desde=0, costos=None,
           escala_costo=1.0, alpha=0.8, p_pen=P_PENALIDAD, n_finalistas=6, max_palancas=3, compras=False, ejecutables=False,
           esperas=None):
    """Búsqueda automática: prueba cada palanca sola con pocas réplicas, descarta las malas, combina las
    mejores de forma voraz y re-evalúa a los finalistas con todas las réplicas. Todos los escenarios usan la
    misma semilla (números aleatorios comunes). Devuelve la lista de evaluaciones ordenada por costo total
    (penalidad esperada + costo de palancas); el escenario sin palancas siempre está incluido."""
    from .c3_montecarlo import MTBF_DEFECTO
    mtbf = MTBF_DEFECTO if mtbf is None else mtbf
    kw = dict(fecha_obj=fecha_obj, semilla=semilla, mtbf=mtbf, restante=restante, mult_desde=mult_desde,
              costos=costos, escala_costo=escala_costo, alpha=alpha, p_pen=p_pen, esperas=esperas)
    R1 = max(150, R // 5)
    base = _evaluar(cot, proy, [], R=R1, **kw)
    primera = [_evaluar(cot, proy, [p], R=R1, **kw) for p in candidatas(compras, ejecutables)]
    primera.sort(key=lambda e: e.total)
    mejores = [e for e in primera if e.total < base.total][:n_finalistas]
    vistos = {tuple(e.palancas) for e in mejores}
    pool = list(mejores)
    for e in mejores[:3]:                                   # combinaciones voraces desde las mejores
        actual = e
        for _ in range(max_palancas - 1):
            ext = []
            for p in (x.palancas[0] for x in mejores):
                if p in actual.palancas or any(q.proceso == p.proceso for q in actual.palancas):
                    continue
                cand = tuple(sorted(actual.palancas + (p,), key=lambda q: (q.proceso, q.tipo)))
                if cand in vistos:
                    continue
                ext.append(_evaluar(cot, proy, list(cand), R=R1, **kw))
            if not ext:
                break
            mejor = min(ext, key=lambda x: x.total)
            if mejor.total >= actual.total - 1e-9:
                break
            vistos.add(tuple(mejor.palancas))
            pool.append(mejor)
            actual = mejor
    pool.sort(key=lambda e: e.total)
    finales = [_evaluar(cot, proy, list(e.palancas), R=R, **kw) for e in pool[:n_finalistas]]
    base_final = _evaluar(cot, proy, [], R=R, **kw)
    out = sorted(finales + [base_final], key=lambda e: e.total)
    return out, base_final


def sensibilidad(cot, proy, fecha_obj, aumento=0.25, R=500, semilla=1, mtbf=None, restante=None, mult_desde=0,
                 alpha=0.8):
    """Criticidad por proceso: cuánto mejora el proyecto si ese proceso tuviera `aumento` más capacidad
    (mismas semillas). Devuelve, por proceso, los días laborables ahorrados y el aumento de P(cumplir)."""
    from .c3_montecarlo import MTBF_DEFECTO
    mtbf = MTBF_DEFECTO if mtbf is None else mtbf
    base = cot.cotizar(proy, R=R, alpha=alpha, mtbf=mtbf, semilla=semilla, restante=restante, mult_desde=mult_desde)
    p0, d0 = base.prob_cumplir(fecha_obj), float(base.dias_lab.mean())
    filas = []
    for j in range(N_PROC):
        m = np.ones(N_PROC)
        m[j] = 1.0 + aumento
        r = cot.cotizar(proy, R=R, alpha=alpha, mtbf=mtbf, semilla=semilla, restante=restante, mult=m,
                        mult_desde=mult_desde)
        filas.append(dict(proceso=j + 1, nombre=NOMBRES[j], dias_ahorrados=d0 - float(r.dias_lab.mean()),
                          delta_prob=r.prob_cumplir(fecha_obj) - p0))
    return dict(prob_base=p0, dias_base=d0, procesos=filas)
