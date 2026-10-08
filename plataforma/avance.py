"""Avance físico ponderado por pieza y curva S (planificado vs. real) de un proyecto en curso.

Pesos por etapa tomados de la hoja REPORTE_DE_HABILITADO de la empresa: el "fierro negro" (habilitado, armado,
soldeo, liberación; 25 % cada uno) vale 70 % del avance, el recubrimiento 20 % (granallado 40 %, pintura 60 %;
la empresa usa 0.4/0.3/0.3 con dos capas) y el despacho 10 %. Son parámetros: ajustarlos con la empresa.
"""
from collections import defaultdict
from datetime import date, timedelta

import numpy as np

from dss.crp_engine import WEEKMASK

ETAPAS = [  # (columna de fecha, nombre, peso global, índices de proceso 0-based que la ejecutan en el plan)
    ('f_habilitado', 'Habilitado', 0.70 * 0.25, [2, 3, 4]),
    ('f_armado', 'Armado', 0.70 * 0.25, [7]),
    ('f_soldeo', 'Soldeo', 0.70 * 0.25, [8]),
    ('f_liberacion', 'Liberación calidad', 0.70 * 0.25, [9]),
    ('f_granallado', 'Granallado', 0.20 * 0.40, [11]),
    ('f_pintura', 'Pintura', 0.20 * 0.60, [11]),
    ('f_despacho', 'Despacho', 0.10, [12]),
]
assert abs(sum(e[2] for e in ETAPAS) - 1) < 1e-9


def error_orden_etapas(p):
    """Mensaje de error si las fechas de etapa de una pieza no respetan el orden de fabricación, o None.

    Fierro negro en orden (habilitado ≤ armado ≤ soldeo ≤ liberación); el despacho va después de todo.
    Granallado y pintura pueden ir en paralelo con la liberación, por eso no se exige más."""
    fab = [(n, str(p[c])[:10]) for c, n, *_ in ETAPAS[:4] if p.get(c)]
    for (n1, d1), (n2, d2) in zip(fab, fab[1:]):
        if d2 < d1:
            return f'{n2} ({d2}) es anterior a {n1} ({d1})'
    desp = p.get('f_despacho')
    if desp and any(p.get(c) and str(p[c])[:10] > str(desp)[:10] for c, *_ in ETAPAS[:-1]):
        return 'hay etapas con fecha posterior al despacho'
    return None


def fraccion_pieza(p, hoy):
    """Fracción ponderada (0–1) de una pieza con las etapas cuya fecha ya pasó."""
    return sum(w for col, _, w, _ in ETAPAS if p.get(col) and str(p[col])[:10] <= hoy)


def resumen_piezas(piezas, hoy):
    kg_total = sum(p['peso_total'] or 0 for p in piezas)
    grupos = {'tipo_elemento': defaultdict(lambda: [0.0, 0.0, 0]), 'contratista': defaultdict(lambda: [0.0, 0.0, 0]),
              'clase_peso': defaultdict(lambda: [0.0, 0.0, 0])}
    por_etapa = {col: 0.0 for col, *_ in ETAPAS}
    kg_av = 0.0
    for p in piezas:
        w = p['peso_total'] or 0
        f = fraccion_pieza(p, hoy)
        kg_av += w * f
        for g in grupos:
            k = p.get(g) or '—'
            grupos[g][k][0] += w
            grupos[g][k][1] += w * f
            grupos[g][k][2] += 1
        for col, *_ in ETAPAS:
            if p.get(col) and str(p[col])[:10] <= hoy:
                por_etapa[col] += w
    fmt = lambda d: sorted([dict(nombre=k, kg=round(v[0], 1), kg_avanzado=round(v[1], 1), n=v[2],
                                 avance=round(100 * v[1] / v[0], 1) if v[0] else 0) for k, v in d.items()], key=lambda x: -x['kg'])
    return dict(n_piezas=len(piezas), kg_total=round(kg_total, 1), kg_avanzado=round(kg_av, 1),
                avance=round(100 * kg_av / kg_total, 1) if kg_total else 0,
                etapas=[dict(etapa=n, peso=round(100 * w, 1), kg=round(por_etapa[col], 1),
                             avance=round(100 * por_etapa[col] / kg_total, 1) if kg_total else 0) for col, n, w, _ in ETAPAS],
                **{g: fmt(d) for g, d in grupos.items()})


def curva_s(inicio, programa, hh_p50, piezas, tareo, hoy, kg_total_plan):
    """Curvas acumuladas por día laborable: kg ponderados (plan vs. real) y HH (plan vs. real).

    programa: [(inicio, fin)] en días laborables desde `inicio`, por proceso (plan P50 cotizado)."""
    base = np.busday_offset(np.datetime64(inicio, 'D'), 0, roll='forward', weekmask=WEEKMASK)
    fines = [b for a, b in programa if b is not None]
    eventos_kg = defaultdict(float)
    for p in piezas:
        for col, _, w, _ in ETAPAS:
            if p.get(col):
                eventos_kg[str(p[col])[:10]] += (p['peso_total'] or 0) * w
    eventos_hh = defaultdict(float)
    for t in tareo:
        eventos_hh[t['fecha']] += t['hh']
    ultimo = max([hoy] + list(eventos_kg) + list(eventos_hh))
    n_plan = max(fines) if fines else 1
    n_real = int(np.busday_count(base, np.datetime64(ultimo, 'D') + np.timedelta64(1, 'D'), weekmask=WEEKMASK))
    N = max(n_plan, n_real) + 2
    fechas = [str(np.busday_offset(base, k, weekmask=WEEKMASK)) for k in range(N)]

    def frac(k, ini, fin):
        if ini is None or fin is None:
            return 0.0
        return float(np.clip((k + 1 - ini) / max(fin - ini, 1), 0, 1))

    ventanas = []
    for col, _, w, procs in ETAPAS:
        vs = [programa[j] for j in procs if programa[j][0] is not None]
        ventanas.append((w, min(v[0] for v in vs) if vs else None, max(v[1] for v in vs) if vs else None))
    plan_kg = [round(kg_total_plan * sum(w * frac(k, a, b) for w, a, b in ventanas), 1) for k in range(N)]
    plan_hh = [round(sum(hh_p50[j] * frac(k, a, b) for j, (a, b) in enumerate(programa)), 1) for k in range(N)]

    def acumular(ev):
        orden = sorted(ev.items())
        out, acc, i = [], 0.0, 0
        for f in fechas:
            while i < len(orden) and orden[i][0] <= f:
                acc += orden[i][1]
                i += 1
            out.append(round(acc, 1) if f <= hoy else None)
        return out

    real_kg = acumular(eventos_kg) if piezas else [None] * N
    real_hh = acumular(eventos_hh)
    k_hoy = max(i for i, f in enumerate(fechas) if f <= hoy) if fechas[0] <= hoy else 0
    spi = lambda r, p: round(r[k_hoy] / p[k_hoy], 2) if r[k_hoy] is not None and p[k_hoy] else None
    return dict(fechas=fechas, plan_kg=plan_kg, real_kg=real_kg, plan_hh=plan_hh, real_hh=real_hh, hoy=fechas[k_hoy],
                spi_kg=spi(real_kg, plan_kg) if piezas else None, spi_hh=spi(real_hh, plan_hh), kg_total_plan=round(kg_total_plan, 1),
                fin_plan=fechas[min(n_plan, N - 1) - 1] if fines else None)


def semanas(c):
    """Semanas de producción (ciclos lunes–sábado) a partir de la curva S: lo planificado y lo logrado en cada
    semana, y el índice de avance acumulado al cierre de la semana. Las semanas futuras quedan sin real."""
    grupos = defaultdict(list)
    for k, f in enumerate(c['fechas']):
        d = date.fromisoformat(f)
        grupos[str(d - timedelta(days=d.weekday()))].append(k)
    out, prev = [], None
    for n, (lunes, ks) in enumerate(sorted(grupos.items()), 1):
        k = ks[-1]
        en_curso = c['fechas'][ks[0]] <= c['hoy'] <= c['fechas'][k]
        kr = max(j for j in ks if c['fechas'][j] <= c['hoy']) if en_curso else k     # semana en curso: real hasta hoy
        fila = dict(n=n, inicio=lunes, fin=c['fechas'][k], plan_kg_acum=c['plan_kg'][k], real_kg_acum=c['real_kg'][kr],
                    plan_hh_acum=c['plan_hh'][k], real_hh_acum=c['real_hh'][kr], en_curso=en_curso, al=c['fechas'][kr])
        for v in ('plan_kg', 'real_kg', 'plan_hh', 'real_hh'):
            a = fila[v + '_acum']
            b = prev[v + '_acum'] if prev else 0
            fila[v] = None if a is None else round(a - (b or 0), 1)
        # índice acumulado: real contra el plan a la misma fecha (en la semana en curso, a hoy)
        fila['spi_kg'] = round(fila['real_kg_acum'] / c['plan_kg'][kr], 2) if fila['real_kg_acum'] is not None and c['plan_kg'][kr] else None
        fila['spi_hh'] = round(fila['real_hh_acum'] / c['plan_hh'][kr], 2) if fila['real_hh_acum'] is not None and c['plan_hh'][kr] else None
        out.append(fila)
        prev = fila
    return out
