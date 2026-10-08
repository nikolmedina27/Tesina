"""Planta, personal, material y lotes SIMULADOS para la vista 3D retrospectiva.

Todo es SIMULADO y se declara así (columna `origen`): el layout es una plantilla funcional de 100 × 50 m
(5 000 m², como la planta de Steelser) y no un plano medido; el personal, las asignaciones diarias, el stock
de material y los lotes de producción se derivan de los 25 proyectos y de sus HH y fechas simuladas
(`sim_proyecto_proceso`). Nada de esto son mediciones.

Tablas (se crean con `py -m dss.simulador_planta`, después de `py -m dss.simulador`):
  sim_planta_elemento   layout: naves, máquinas, mesas, puestos, grúas, racks, muelles, oficinas
  sim_personal          personas (anónimas) por contratista o área
  sim_cuadrilla         quiénes trabajaron en cada proyecto × proceso
  sim_asignacion        por día: estación, personas y HH de cada proyecto × proceso
  sim_material_lote     stock: perfil, kg, colada, certificado, ubicación, fechas de ingreso y consumo
  sim_lote              lotes de piezas de cada proyecto (unidad que se mueve por la planta)
  sim_lote_etapa        ventana de cada lote en cada etapa (habilitado, doblez, armado, soldeo, ...)
"""
import json
import sqlite3
from pathlib import Path

import numpy as np

from .crp_engine import WEEKMASK
from .simulador import CONTRATISTAS, MAQ_NOMBRE

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / 'data' / 'steelser.db'
ORIGEN = 'SIMULADO'
ORIGEN_DIA = np.datetime64('2019-01-01', 'D')

# etapas del flujo de un lote → procesos (orden 1-13) que las componen
ETAPAS = [('HABILITADO', (3, 4, 5, 6)), ('DOBLEZ', (7,)), ('ARMADO', (8,)), ('SOLDEO', (9,)),
          ('LIMPIEZA', (10,)), ('PINTURA', (11, 12)), ('DESPACHO', (13,))]


# --------------------------------------------------------------------------- calendario (días laborables)
def a_idx(fecha):
    """Índice de día laborable (lunes a sábado) de una fecha ISO."""
    return int(np.busday_count(ORIGEN_DIA, np.datetime64(fecha, 'D'), weekmask=WEEKMASK))


def de_idx(i):
    return str(np.busday_offset(ORIGEN_DIA, int(i), weekmask=WEEKMASK))


# --------------------------------------------------------------------------- layout
def layout():
    """Plantilla funcional de 100 × 50 m. Coordenadas en metros: x hacia el este, z hacia el norte."""
    E = []

    def el(tipo, nombre, x, z, ancho, largo, alto=1.0, proceso=None, centro=None, cap=None, rot=0.0, **meta):
        E.append(dict(tipo=tipo, nombre=nombre, x=x, z=z, ancho=ancho, largo=largo, alto=alto, rot=rot,
                      proceso_orden=proceso, centro_nombre=centro, capacidad=cap, meta=meta))

    el('terreno', 'Predio Steelser (5 000 m²)', 50, 25, 100, 50, 0.1)
    el('nave', 'Nave A · recepción y habilitado', 22.5, 15, 45, 30, 9.0, descripcion='Corte, punzonado, CNC y roscado')
    el('nave', 'Nave B · armado y soldeo', 72.5, 15, 45, 30, 9.0, descripcion='Armado, soldeo, limpieza y liberación')
    el('zona', 'Patio de acopio de perfiles y planchas', 22.5, 40, 45, 16, 0.2)
    el('zona', 'Buffer de piezas habilitadas', 47.5, 15, 5, 30, 0.2)
    el('grua', 'Puente grúa A (10 t)', 22.5, 15, 42, 3, 8.0, capacidad=10, nave='A')
    el('grua', 'Puente grúa B (10 t)', 72.5, 15, 42, 3, 8.0, capacidad=10, nave='B')
    for i, (x, z) in enumerate([(5, 24), (5, 20), (5, 16)], 1):
        el('rack', f'Rack de perfiles R{i}', x, z, 2.2, 8, 3.5, capacidad=12000)
    for nombre, x, p in zip(MAQ_NOMBRE, (12, 22, 32, 41), (3, 4, 5, 6)):
        el('maquina', nombre, x, 6, 4.0 if p != 5 else 7.0, 3.0 if p != 5 else 4.0, 2.2, proceso=p, centro=nombre, cap=8.0)
    for i in range(6):
        el('mesa', f'Mesa de armado M{i + 1}', 56 + (i % 3) * 11, 7 + (i // 3) * 9, 8, 4, 1.0, proceso=8, cap=3)
    for i in range(8):
        el('puesto', f'Puesto de soldeo S{i + 1}', 55 + (i % 4) * 8.5, 24 + (i // 4) * 3.5 - 1.5, 3.2, 2.6, 2.0,
           proceso=9, cap=2)
    for i in range(2):
        el('zona', f'Zona de limpieza y liberación L{i + 1}', 90, 8 + i * 10, 8, 8, 0.3, proceso=10, cap=4)
    el('muelle', 'Muelle de doblez (servicio externo)', 98, 5, 4, 8, 0.3, proceso=7, externo=True)
    el('muelle', 'Muelle a granallado y pintura (externo)', 98, 17, 4, 8, 0.3, proceso=11, externo=True)
    el('muelle', 'Muelle de despacho a obra', 98, 29, 4, 8, 0.3, proceso=13)
    el('oficina', 'Oficina técnica', 90, 43, 12, 8, 4.0, proceso=1)
    el('oficina', 'Compras', 76, 43, 8, 8, 4.0, proceso=2)
    return E


# --------------------------------------------------------------------------- tablas
SCHEMA = '''
DROP TABLE IF EXISTS sim_planta_elemento; DROP TABLE IF EXISTS sim_personal; DROP TABLE IF EXISTS sim_cuadrilla;
DROP TABLE IF EXISTS sim_asignacion; DROP TABLE IF EXISTS sim_material_lote; DROP TABLE IF EXISTS sim_lote;
DROP TABLE IF EXISTS sim_lote_etapa;
CREATE TABLE sim_planta_elemento (id INTEGER PRIMARY KEY, tipo TEXT NOT NULL, nombre TEXT NOT NULL,
    centro_id INTEGER REFERENCES centro_trabajo(id), proceso_orden INTEGER, x REAL, z REAL, ancho REAL, largo REAL,
    alto REAL, rot REAL, capacidad REAL, meta TEXT, origen TEXT NOT NULL DEFAULT 'SIMULADO');
CREATE TABLE sim_personal (id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, grupo TEXT NOT NULL, rol TEXT,
    origen TEXT NOT NULL DEFAULT 'SIMULADO');
CREATE TABLE sim_cuadrilla (mundo_id INTEGER, proyecto_id INTEGER REFERENCES proyecto(id), proceso_orden INTEGER,
    persona_id INTEGER REFERENCES sim_personal(id), PRIMARY KEY (mundo_id, proyecto_id, proceso_orden, persona_id));
CREATE TABLE sim_asignacion (mundo_id INTEGER, proyecto_id INTEGER REFERENCES proyecto(id), proceso_orden INTEGER,
    fecha TEXT, estacion_id INTEGER REFERENCES sim_planta_elemento(id), personas INTEGER, hh REAL,
    PRIMARY KEY (mundo_id, proyecto_id, proceso_orden, fecha, estacion_id));
CREATE INDEX ix_sim_asignacion_fecha ON sim_asignacion (mundo_id, fecha);
CREATE TABLE sim_material_lote (id INTEGER PRIMARY KEY, mundo_id INTEGER, proyecto_id INTEGER REFERENCES proyecto(id),
    tipo TEXT, perfil TEXT, cantidad INTEGER, kg REAL, colada TEXT, certificado TEXT,
    ubicacion_id INTEGER REFERENCES sim_planta_elemento(id), f_ingreso TEXT, f_consumo TEXT,
    origen TEXT NOT NULL DEFAULT 'SIMULADO');
CREATE INDEX ix_sim_material_fecha ON sim_material_lote (mundo_id, f_ingreso, f_consumo);
CREATE TABLE sim_lote (mundo_id INTEGER, proyecto_id INTEGER REFERENCES proyecto(id), lote INTEGER, kg REAL,
    n_piezas INTEGER, descripcion TEXT, PRIMARY KEY (mundo_id, proyecto_id, lote));
CREATE TABLE sim_lote_etapa (mundo_id INTEGER, proyecto_id INTEGER, lote INTEGER, etapa TEXT, orden INTEGER,
    f_inicio TEXT, f_fin TEXT, PRIMARY KEY (mundo_id, proyecto_id, lote, etapa));
CREATE INDEX ix_sim_lote_etapa_fecha ON sim_lote_etapa (mundo_id, f_inicio, f_fin);
'''

# perfiles de material: (tipo, designación, kg por unidad)
PERFILES = {
    'PERFIL_W': [('W12x26 · 12 m', 464), ('W16x31 · 12 m', 553), ('W8x18 · 12 m', 321)],
    'PERFIL_HEA': [('HEA 200 · 12 m', 635), ('HEA 160 · 12 m', 361)],
    'CANAL': [('C 10x15.3 · 6 m', 137), ('C 8x11.5 · 6 m', 103)],
    'ANGULO': [('L 3x3x1/4 · 6 m', 52), ('L 2x2x3/16 · 6 m', 27)],
    'PLANCHA': [('PL 3/8" 1.2x2.4 m', 85), ('PL 1/2" 1.5x6 m', 353), ('PL 1/4" 1.2x2.4 m', 57)],
    'TUBO': [('Tubo 4" x 3 mm · 6 m', 52), ('Tubo 6" x 4 mm · 6 m', 102)],
}


def crear_tablas(con):
    con.executescript(SCHEMA)


def _grupos_personal(rng):
    """Pool de personas anónimas: contratistas (armado, soldeo, limpieza) y personal de planta."""
    pers, nid = [], 1
    for c in CONTRATISTAS:
        sigla = ''.join(w[0] for w in c.replace('&', ' ').split())[:3]
        for i in range(1, 15):
            pers.append((nid, f'Obrero {sigla}-{i:02d}', c, 'Obrero de contratista'))
            nid += 1
    for g, rol, n in [('Planta', 'Operador de máquina', 8), ('Planta', 'Supervisor', 3), ('Planta', 'Soldador de planta', 4),
                      ('Oficina técnica', 'Proyectista', 6), ('Compras', 'Comprador', 2), ('Despacho', 'Despachador', 4)]:
        for i in range(1, n + 1):
            pers.append((nid, f'{rol} {g[:3].upper()}-{i:02d}', g, rol))
            nid += 1
    return pers


# --------------------------------------------------------------------------- lotes de producción
def etapas_de_lotes(n, ventanas):
    """Ventana (índices de día) de cada uno de los `n` lotes en cada etapa, sin azar: dentro de la ventana de los
    procesos de la etapa y sin empezar antes de que el lote termine la etapa anterior.
    Devuelve ({lote: [(etapa, orden, ini, fin), ...]}, [(etapa, ini, fin), ...])."""
    etapas = {k: [] for k in range(n)}
    ventanas_etapa = []
    for nombre, procs in ETAPAS:
        a = min(ventanas[p][0] for p in procs)
        b = max(ventanas[p][1] for p in procs)
        ventanas_etapa.append((nombre, a, b))
    ultimo_fin = {k: -10 ** 9 for k in range(n)}
    for orden, (nombre, a, b) in enumerate(ventanas_etapa):
        ancho = b - a + 1
        largo = max(1, int(np.ceil(ancho * 0.5)))
        for k in range(n):
            nominal = a + int(round((ancho - largo) * k / max(n - 1, 1)))
            ini = int(min(max(nominal, ultimo_fin[k]), b))
            fin = int(min(b, ini + largo - 1))
            etapas[k].append((nombre, orden, ini, fin))
            ultimo_fin[k] = fin
    return etapas, ventanas_etapa


def lotes_y_etapas(ton, n_piezas, ventanas, rng):
    """Divide el proyecto en lotes (kg y piezas al azar con semilla) y calcula su ventana en cada etapa.
    `ventanas`: {orden_proceso: (idx_inicio, idx_fin)}. Devuelve (lotes, etapas, ventanas_etapa)."""
    n = int(np.clip(round(ton / 8), 4, 14))
    w = rng.dirichlet(np.full(n, 8.0))
    kg = np.round(w * ton * 1000.0, 1)
    kg[-1] = round(ton * 1000.0 - kg[:-1].sum(), 1)
    piezas = np.maximum(1, np.round(w * n_piezas)).astype(int)
    lotes = [(float(kg[k]), int(piezas[k]), f'Lote {k + 1} de {n}') for k in range(n)]
    etapas, ventanas_etapa = etapas_de_lotes(n, ventanas)
    return lotes, etapas, ventanas_etapa


# --------------------------------------------------------------------------- generación
def _elegir(estaciones, k, ventana, ocupacion):
    """Elige las k estaciones con menos personas ya asignadas en la ventana (idx_ini, idx_fin)."""
    a, b = ventana
    carga = []
    for e in estaciones:
        c = sum(p for (x0, x1, p) in ocupacion.get(e, []) if not (x1 < a or x0 > b))
        carga.append((c, e))
    carga.sort()
    return [e for _, e in carga[:k]]


def generar_mundo(con, mundo_id, ids, semilla=2026):
    """Genera asignaciones, cuadrillas, material y lotes de un mundo. `ids`: dict nombre → id de elemento."""
    rng = np.random.default_rng(semilla + mundo_id)
    proy = con.execute('''SELECT p.id, p.toneladas, f.n_piezas, f.pct_planchas, f.contratista
                          FROM proyecto p JOIN sim_feature f ON f.proyecto_id=p.id
                          WHERE p.en_muestra=1 ORDER BY p.fecha_inicio, p.id''').fetchall()
    filas_sp = con.execute('''SELECT s.proyecto_id, pr.orden, s.hh_real, s.f_inicio, s.f_fin
                              FROM sim_proyecto_proceso s JOIN proceso pr ON pr.id=s.proceso_id
                              WHERE s.mundo_id=?''', (mundo_id,)).fetchall()
    sp = {}
    for pid, o, hh, fi, ff in filas_sp:
        sp.setdefault(pid, {})[o] = (hh, fi, ff)
    crew = {(r[0], r[1]): r[2] for r in con.execute(
        '''SELECT pp.proyecto_id, pr.orden, pp.n_personas FROM proyecto_proceso pp JOIN proceso pr ON pr.id=pp.proceso_id''')}
    personal = con.execute('SELECT id, grupo, rol FROM sim_personal').fetchall()
    por_contr = {c: [p[0] for p in personal if p[1] == c] for c in CONTRATISTAS}
    por_grupo = {g: [p[0] for p in personal if p[1] == g] for g in ('Planta', 'Oficina técnica', 'Compras', 'Despacho')}
    mesas = [ids[n] for n in sorted(ids) if n.startswith('Mesa de armado')]
    puestos = [ids[n] for n in sorted(ids) if n.startswith('Puesto de soldeo')]
    zonas = [ids[n] for n in sorted(ids) if n.startswith('Zona de limpieza')]
    maq = [ids[n] for n in MAQ_NOMBRE]
    fijos = {1: ids['Oficina técnica'], 2: ids['Compras'], 7: ids['Muelle de doblez (servicio externo)'],
             11: ids['Muelle a granallado y pintura (externo)'], 12: ids['Muelle a granallado y pintura (externo)'],
             13: ids['Muelle de despacho a obra']}
    for i, o in enumerate((3, 4, 5, 6)):
        fijos[o] = maq[i]
    ocup = {}
    asign, cuad, mats, lotes_rows, etapas_rows = [], [], [], [], []
    racks = [ids[n] for n in sorted(ids) if n.startswith('Rack de perfiles')]
    patio = ids['Patio de acopio de perfiles y planchas']
    nmat = 0
    for pid, ton, n_piezas, pct_pl, contr in proy:
        v = sp[pid]
        ventanas = {o: (a_idx(v[o][1]), a_idx(v[o][2])) for o in v}
        # asignación diaria por proceso
        for o in range(1, 14):
            hh, fi, ff = v[o]
            a, b = ventanas[o]
            n = int(crew.get((pid, o), 0) or 0)
            externo = o in (7, 12)
            n_pers = 0 if externo else max(n, 1)
            if o == 8:
                est = _elegir(mesas, int(np.clip(np.ceil(n_pers / 3), 1, len(mesas))), (a, b), ocup)
            elif o == 9:
                est = _elegir(puestos, int(np.clip(np.ceil(n_pers / 2), 1, len(puestos))), (a, b), ocup)
            elif o == 10:
                est = _elegir(zonas, int(np.clip(np.ceil(n_pers / 4), 1, len(zonas))), (a, b), ocup)
            else:
                est = [fijos[o]]
            reparto = [n_pers // len(est) + (1 if i < n_pers % len(est) else 0) for i in range(len(est))]
            for e, pe in zip(est, reparto):
                ocup.setdefault(e, []).append((a, b, pe))
            dias = max(b - a + 1, 1)
            for d in range(a, b + 1):
                for e, pe in zip(est, reparto):
                    asign.append((mundo_id, pid, o, de_idx(d), e, pe, float(hh) / dias / len(est)))
            # cuadrilla nominal
            if n_pers:
                pool = por_contr.get(contr, por_contr[CONTRATISTAS[0]]) if o in (8, 9, 10) else \
                    por_grupo['Oficina técnica'] if o == 1 else por_grupo['Compras'] if o == 2 else \
                    por_grupo['Despacho'] if o in (11, 13) else por_grupo['Planta']
                elegidos = rng.choice(pool, size=min(n_pers, len(pool)), replace=False)
                cuad += [(mundo_id, pid, o, int(x)) for x in elegidos]
        # material (stock): ingresa durante la compra y se consume en el habilitado
        kg_total = ton * 1000.0 * 1.05
        cat = {'PLANCHA': pct_pl}
        resto = 1.0 - pct_pl
        for t, wgt in zip(('PERFIL_W', 'PERFIL_HEA', 'CANAL', 'ANGULO', 'TUBO'), (0.32, 0.28, 0.15, 0.15, 0.10)):
            cat[t] = resto * wgt
        c0, c1 = ventanas[2]
        h0, h1 = ventanas[3][0], max(ventanas[x][1] for x in (3, 4, 5, 6))
        for t, share in cat.items():
            kg_t = kg_total * share
            n_lotes = max(1, int(np.ceil(kg_t / 4000.0)))
            for k in range(n_lotes):
                desig, kg_u = PERFILES[t][int(rng.integers(len(PERFILES[t])))]
                kg_l = kg_t / n_lotes
                cant = max(1, int(round(kg_l / kg_u)))
                ing = int(c0 + round((c1 - c0) * (0.5 + 0.5 * (k + 1) / n_lotes)))
                con_ = int(min(max(h1, ing), ing + 25)) if h1 > ing else ing + 1
                con_ = max(con_ - int(round((n_lotes - 1 - k) * 0.5)), ing)
                ubic = patio if t in ('PLANCHA', 'TUBO') else racks[int(rng.integers(len(racks)))]
                nmat += 1
                mats.append((None, mundo_id, pid, t, desig, cant, round(cant * kg_u, 1),
                             'C' + ''.join(rng.choice(list('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'), 6)),
                             f'CERT-{rng.integers(10000, 99999)}', ubic, de_idx(ing), de_idx(con_)))
        # lotes de producción
        lotes, etapas, _ = lotes_y_etapas(ton, n_piezas, ventanas, rng)
        for k, (kg, npz, desc) in enumerate(lotes):
            lotes_rows.append((mundo_id, pid, k + 1, kg, npz, desc))
            for nombre, orden, ini, fin in etapas[k]:
                etapas_rows.append((mundo_id, pid, k + 1, nombre, orden, de_idx(ini), de_idx(fin)))
    con.executemany('INSERT INTO sim_asignacion VALUES (?,?,?,?,?,?,?)', asign)
    con.executemany('INSERT OR IGNORE INTO sim_cuadrilla VALUES (?,?,?,?)', cuad)
    con.executemany('''INSERT INTO sim_material_lote (id, mundo_id, proyecto_id, tipo, perfil, cantidad, kg, colada,
                       certificado, ubicacion_id, f_ingreso, f_consumo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', mats)
    con.executemany('INSERT INTO sim_lote VALUES (?,?,?,?,?,?)', lotes_rows)
    con.executemany('INSERT INTO sim_lote_etapa VALUES (?,?,?,?,?,?,?)', etapas_rows)
    return dict(asignaciones=len(asign), material=len(mats), lotes=len(lotes_rows))


def main():
    con = sqlite3.connect(DB)
    crear_tablas(con)
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    for e in layout():
        con.execute('''INSERT INTO sim_planta_elemento (tipo, nombre, centro_id, proceso_orden, x, z, ancho, largo, alto, rot,
                       capacidad, meta) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (e['tipo'], e['nombre'], cen.get(e['centro_nombre']), e['proceso_orden'], e['x'], e['z'], e['ancho'],
                     e['largo'], e['alto'], e['rot'], e['capacidad'], json.dumps(e['meta'], ensure_ascii=False)))
    ids = dict(con.execute('SELECT nombre, id FROM sim_planta_elemento'))
    rng = np.random.default_rng(2026)
    con.executemany('INSERT INTO sim_personal VALUES (?,?,?,?, "SIMULADO")', _grupos_personal(rng))
    mundos = [r[0] for r in con.execute('SELECT id FROM sim_mundo ORDER BY id')]
    for m in mundos:
        r = generar_mundo(con, m, ids)
        print(f'mundo {m}: {r["asignaciones"]} asignaciones, {r["material"]} lotes de material, {r["lotes"]} lotes de producción')
    con.commit()
    con.close()


if __name__ == '__main__':
    main()
