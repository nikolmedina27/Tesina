"""Generador de la historia SIMULADA del gemelo: 38 proyectos 2019-2026 con sus lotes de piezas, paquetes de
ingeniería, compras, RFIs, cambios de alcance, fallas de máquina y todo el azar que el gemelo necesita.

Se respeta lo real: lista de proyectos, fechas de inicio y de fin planificado (Tabla 3), tipo, toneladas de la
muestra y cuadrillas planificadas. Todo lo demás es SIMULADO, con supuestos declarados aquí.

Todo el azar se sortea por adelantado y por entidad (números aleatorios comunes): al comparar políticas en el
gemelo, el mismo lote tiene el mismo tiempo de soldeo, la misma máquina falla el mismo día y el mismo proveedor se
atrasa igual; solo cambia lo que las decisiones cambian.

Modelo oculto de horas (la «verdad» que el QRF debe aprender, nunca se le muestra):
  log φ_j = sesgo_j + efecto de piezas por t (armado, soldeo) + planchas (CNC, sierra) + habilidad del contratista
            + aprendizaje (−2 %/año) + escala (−6 % por log t/90) + umbral no lineal (piezas/t > 11)
            + efecto del proyecto (ρ ≈ 0.3) + ruido del proceso
"""
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from ..datos import ratio_vigente, modelo_cuadrilla, cuadrilla as cuadrilla_tipica, TIPOS
from .calendario import LABORABLES, Ventanas, ventanas_dia, TURNO, EPOCA, FIN, hora, a_fecha

SEMILLA = 2026
CONTRATISTAS = {                      # habilidad (factor de HH), calidad (factor de NC), plantilla máxima
    'T&C FABRICACION': (0.95, 1.0, 16), 'FRANCISCO TARRILLO': (1.05, 1.3, 12), 'RFR METALICAS': (1.00, 0.9, 14),
    'ROGGER TORRES': (1.12, 1.5, 10), 'LHL INGENIERIA': (0.92, 0.8, 12)}
MAQUINAS = ['Sierra Cinta Kaltenbach', 'Cizalladora Punzonadora Pedimax', 'Mesa CNC', 'Roscadora RIDGID']
OP_MAQ = ['sierra', 'cizalla', 'cnc', 'roscado']                  # procesos 3-6
MTBF_H = [90.0, 60.0, 110.0, 220.0]                               # horas de trabajo entre fallas (Weibull, forma 1.3)
MTTR_H = [3.0, 4.0, 2.5, 1.5]                                     # mediana de reparación (lognormal σ 0.8)
CAUSAS = ['Falla mecánica', 'Falla eléctrica', 'Falta de repuesto', 'Lubricación', 'Cambio de herramienta / setup']
PESO_MEDIO = {TIPOS[0]: 420.0, TIPOS[1]: 380.0, TIPOS[2]: 330.0, TIPOS[3]: 260.0}
PRECIO_T = 10_500.0                                               # S/ por tonelada fabricada (supuesto)
ELEMENTOS = [('Columna', 'W12x26', 1.6), ('Viga principal', 'W16x31', 1.4), ('Tijeral', 'L 3x3x1/4', 1.1),
             ('Viga secundaria', 'W8x18', 0.9), ('Arriostre', 'L 2x2x3/16', 0.5), ('Correa', 'C 8x11.5', 0.4),
             ('Placa base', 'PL 1/2"', 0.3), ('Escalera', 'C 10x15.3', 0.7), ('Templador', 'Barra 5/8"', 0.15)]


@dataclass
class Conjunto:
    id: int
    pid: int
    indice: int
    paquete: int
    elemento: str
    perfil: str
    kg: float
    n_piezas: int
    largo: float
    hh: dict                      # horas por operación (verdad)
    doblez: bool
    nc: bool                      # no conformidad en la inspección (se sortea ahora)
    adicional: bool = False       # agregado por cambio de alcance


@dataclass
class ProyectoG:
    pid: int
    cod: int | None
    nombre: str
    tipo: str
    ton: float
    ini: date
    fp: date
    fr: date
    en_muestra: bool
    presupuesto: float
    contratista: str
    crew: np.ndarray
    feats: dict
    hh_ratio: np.ndarray
    phi: np.ndarray
    hh: np.ndarray
    conjuntos: list = field(default_factory=list)
    paquetes: int = 4
    rfis: list = field(default_factory=list)          # (paquete, días laborables de atraso)
    cambios: list = field(default_factory=list)       # (fracción de la ingeniería en que llega, índices de conjuntos)
    lead_compra: dict = field(default_factory=dict)   # paquete -> días laborables del proveedor
    lead_doblez: list = field(default_factory=list)   # k-ésimo envío -> días laborables
    lead_pintura: list = field(default_factory=list)
    semilla: int = 0


def _ton_no_muestra(rng):
    return float(np.clip(np.exp(rng.normal(np.log(80), 0.45)), 25, 200))


def _phi(rng, p, j_idx, contratista, anio, feats):
    skill = np.log(CONTRATISTAS[contratista][0])
    ppt, pl = feats['piezas_por_t'], feats['pct_planchas']
    mu = np.zeros(13)
    mu[7] += 0.04; mu[8] += 0.06                                       # armado y soldeo: el ratio subestima
    mu[[7, 8]] += 0.10 * np.log(ppt / 8.0) + 0.12 * (ppt > 11)
    mu[4] += 0.08 * (pl - 0.2) / 0.1; mu[2] -= 0.03 * (pl - 0.2) / 0.1
    mu[[7, 8, 9]] += skill
    mu -= 0.02 * (anio - 2021)
    mu -= 0.06 * np.log(p['ton'] / 90.0)
    eta = rng.standard_normal()
    eps = rng.standard_normal(13)
    return np.exp(mu + 0.12 * (np.sqrt(0.3) * eta + np.sqrt(0.7) * eps))


def _reparto(total, pesos, rng, sigma=0.25):
    w = np.asarray(pesos, float) * np.exp(rng.normal(0, sigma, len(pesos)))
    w = np.maximum(w, 1e-9)
    return total * w / w.sum()


def generar(con, semilla=SEMILLA):
    """Devuelve (proyectos, paradas) con todo lo necesario para el gemelo."""
    rng0 = np.random.default_rng(semilla)
    rv = ratio_vigente(con)
    par_cuad = modelo_cuadrilla(con)
    P = pd.read_sql('''SELECT p.id pid, p.codigo_muestra cod, p.nombre, t.nombre tipo, p.toneladas ton, p.fecha_inicio ini,
                       p.fecha_fin_plan fp, p.fecha_fin_real fr, p.en_muestra
                       FROM proyecto p LEFT JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                       WHERE p.n_registro IS NOT NULL ORDER BY p.fecha_inicio, p.id''', con)
    feats_m = pd.read_sql('SELECT proyecto_id pid, piezas_por_t, pct_planchas, m2_pintura, montaje, contratista FROM sim_feature',
                          con).set_index('pid')
    crews = pd.read_sql('''SELECT pp.proyecto_id pid, pr.orden o, pp.n_personas n FROM proyecto_proceso pp
                           JOIN proceso pr ON pr.id=pp.proceso_id''', con)
    crew_m = {pid: g.sort_values('o').n.values.astype(float) for pid, g in crews.groupby('pid')}
    nombres_c = list(CONTRATISTAS)
    proyectos = []
    cid = 0
    for r in P.itertuples():
        rng = np.random.default_rng([semilla, int(r.pid)])
        tipo = TIPOS[0] if pd.isna(r.tipo) or not r.tipo else r.tipo
        muestra = bool(r.en_muestra)
        ton = float(r.ton) if muestra else _ton_no_muestra(rng)
        if muestra and r.pid in feats_m.index:
            f = feats_m.loc[r.pid]
            feats = dict(piezas_por_t=float(f.piezas_por_t), pct_planchas=float(f.pct_planchas),
                         m2_pintura=float(f.m2_pintura), montaje=bool(f.montaje))
            contr = f.contratista if f.contratista in CONTRATISTAS else nombres_c[int(r.pid) % 5]
        else:
            feats = dict(piezas_por_t=float(np.exp(rng.normal(np.log(8), 0.5))), pct_planchas=float(rng.beta(2, 8)),
                         m2_pintura=float(np.exp(rng.normal(np.log(14), 0.3)) * ton), montaje=bool(rng.random() < .35))
            contr = nombres_c[int(rng.integers(5))]
        crew = crew_m.get(int(r.pid))
        if crew is None:
            crew = cuadrilla_tipica(par_cuad, ton).astype(float)
        crew = np.maximum(crew, 1.0)
        hh_ratio = ton * rv.loc[tipo].values
        ini = a_fecha(r.ini)
        phi = _phi(rng, dict(ton=ton), None, contr, ini.year, feats)
        hh = hh_ratio * phi
        p = ProyectoG(pid=int(r.pid), cod=None if pd.isna(r.cod) else int(r.cod), nombre=r.nombre, tipo=tipo, ton=ton,
                      ini=ini, fp=a_fecha(r.fp), fr=a_fecha(r.fr), en_muestra=muestra,
                      presupuesto=float(ton * PRECIO_T * np.exp(rng.normal(0, .15))), contratista=contr, crew=crew,
                      feats=feats, hh_ratio=hh_ratio, phi=phi, hh=hh, semilla=int(rng.integers(1 << 30)))
        # lotes (conjuntos)
        n = int(max(12, round(ton * 1000 / PESO_MEDIO[tipo])))
        kg = _reparto(ton * 1000.0, np.ones(n), rng, sigma=0.7)
        piezas = np.maximum(1, np.round(_reparto(feats['piezas_por_t'] * ton, kg ** 0.6 + 1, rng, 0.3))).astype(int)
        p.paquetes = int(np.clip(round(n / 35), 3, 8))
        paquete = np.sort(rng.integers(0, p.paquetes, n))
        es_plancha = rng.random(n) < np.clip(feats['pct_planchas'] * 1.4, 0.05, 0.9)
        rosca = rng.random(n) < 0.10
        doblez = rng.random(n) < 0.07
        hh_maq = {
            'sierra': _reparto(hh[2], kg * (~es_plancha + .15), rng),
            'cizalla': _reparto(hh[3], piezas.astype(float), rng),
            'cnc': _reparto(hh[4], kg * (es_plancha + .05), rng),
            'roscado': _reparto(hh[5], rosca + 0.02, rng),
            'armado': _reparto(hh[7], piezas ** 0.8 * kg ** 0.2, rng),
            'soldeo': _reparto(hh[8], kg ** 0.9, rng),
            'limpieza': _reparto(hh[9], piezas ** 0.6 * kg ** 0.3, rng),
        }
        q_nc = CONTRATISTAS[contr][1] * 0.06
        orden_el = np.argsort(-kg)
        for k in range(n):
            pos = int(np.where(orden_el == k)[0][0]) / n
            el = ELEMENTOS[min(int(pos * len(ELEMENTOS)), len(ELEMENTOS) - 1)] if not rosca[k] else ELEMENTOS[-1]
            if es_plancha[k] and not rosca[k]:
                el = ('Placa / conexión', 'PL 3/8"', 0.3)
            cid += 1
            p.conjuntos.append(Conjunto(
                id=cid, pid=p.pid, indice=k + 1, paquete=int(paquete[k]), elemento=el[0], perfil=el[1], kg=float(kg[k]),
                n_piezas=int(piezas[k]), largo=float(np.clip(rng.normal(7.5, 2.5) * el[2] ** .2, 1.0, 12.0)),
                hh={o: float(v[k]) for o, v in hh_maq.items() if v[k] > 0.05},
                doblez=bool(doblez[k]), nc=bool(rng.random() < q_nc)))
        # RFIs del cliente y cambios de alcance
        for _ in range(int(rng.poisson(0.7))):
            p.rfis.append((int(rng.integers(p.paquetes)), float(np.exp(rng.normal(np.log(5), 0.5)))))
        for _ in range(int(rng.poisson(0.3))):
            extra = max(2, int(n * rng.uniform(0.03, 0.08)))
            nuevos = []
            for _k in range(extra):
                base = p.conjuntos[int(rng.integers(n))]
                cid += 1
                c = Conjunto(id=cid, pid=p.pid, indice=len(p.conjuntos) + 1, paquete=p.paquetes - 1, elemento=base.elemento,
                             perfil=base.perfil, kg=base.kg, n_piezas=base.n_piezas, largo=base.largo,
                             hh={o: h * float(np.exp(rng.normal(0, .2))) for o, h in base.hh.items()}, doblez=base.doblez,
                             nc=bool(rng.random() < q_nc), adicional=True)
                p.conjuntos.append(c)
                nuevos.append(c.id)
            p.cambios.append((float(rng.uniform(0.5, 0.8)), nuevos))
        # proveedores y servicios externos (k-ésimo envío → k-ésimo plazo)
        for k in range(p.paquetes):
            d = float(np.exp(rng.normal(np.log(6), 0.35)))
            if rng.random() < 0.18:
                d += float(rng.uniform(4, 14))
            p.lead_compra[k] = d
        p.lead_doblez = [float(np.exp(rng.normal(np.log(4), 0.35))) for _ in range(40)]
        p.lead_pintura = [float(np.exp(rng.normal(np.log(7), 0.35)) + (rng.uniform(5, 12) if rng.random() < .12 else 0))
                          for _ in range(40)]
        proyectos.append(p)
    return proyectos, generar_paradas(semilla)


def generar_paradas(semilla=SEMILLA):
    """Paradas de las 4 máquinas en todo el calendario (independientes del uso): [(maq, ini, fin, causa, planificada)]."""
    rng = np.random.default_rng([semilla, 99])
    base = Ventanas(ventanas_dia(EPOCA, FIN, TURNO))
    total = base.cum[-1]
    paradas = []
    for k in range(4):
        t = 0.0
        while True:
            t += float(MTBF_H[k] * rng.weibull(1.3) / 0.92)
            if t >= total:
                break
            ini = base.avanzar(0.0, t)
            dur = float(np.clip(np.exp(rng.normal(np.log(MTTR_H[k]), 0.8)), 0.5, 40.0))
            fin = base.avanzar(ini, dur)
            paradas.append((k, ini, fin, CAUSAS[int(rng.integers(len(CAUSAS)))], 0))
        for h in np.arange(160.0, total, 160.0):                       # mantenimiento preventivo cada 160 h
            ini = base.avanzar(0.0, float(h))
            paradas.append((k, ini, base.avanzar(ini, 4.0), 'Mantenimiento preventivo', 1))
    return paradas


def ausentismo(semilla, pid, proc, dia_idx, n):
    """Factor de duración por ausentismo del día: n / presentes (cada persona falta con prob. 8 %)."""
    if n <= 1:
        return 1.0
    rng = np.random.default_rng([semilla, pid, proc, dia_idx])
    presentes = max(1, int(rng.binomial(int(round(n)), 0.92)))
    return float(round(n) / presentes)
