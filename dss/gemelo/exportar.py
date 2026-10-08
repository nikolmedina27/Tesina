"""Guarda el gemelo en `data/steelser.db` (tablas `gem_*`, SIMULADAS) y como mundo 6 en `sim_*`.

- gem_*: proyectos, lotes, piezas, operaciones hora a hora, movimientos de grúa, camiones, material, paradas,
  tareo diario (formato único), personal, palancas y resultados por política. Los tiempos `t_*` están en horas
  desde 2019-01-01 00:00 (calendario del gemelo).
- Mundo 6 en sim_mundo / sim_proyecto_proceso / sim_parada / sim_verificacion: las HH «reales» por proceso que
  registró el gemelo para los 25 proyectos de la muestra. Con eso el QRF y el Monte Carlo existentes aprenden de
  datos que NO salen de su propio motor (el gemelo trabaja por hora y por lote; el planificador, por día).
"""
import json
from datetime import timedelta

import numpy as np

from .calendario import EPOCA, Ventanas, fecha, hora, turno_base
from .generador import CONTRATISTAS, MAQUINAS
from .motor import OP_PROC

MUNDO = 6
NOMBRE_MUNDO = 'M6 gemelo DES (hora a hora, por lote)'

SCHEMA = '''
DROP TABLE IF EXISTS gem_proyecto; DROP TABLE IF EXISTS gem_lote; DROP TABLE IF EXISTS gem_pieza;
DROP TABLE IF EXISTS gem_op; DROP TABLE IF EXISTS gem_mov; DROP TABLE IF EXISTS gem_camion;
DROP TABLE IF EXISTS gem_material; DROP TABLE IF EXISTS gem_parada; DROP TABLE IF EXISTS gem_tareo;
DROP TABLE IF EXISTS gem_personal; DROP TABLE IF EXISTS gem_palanca; DROP TABLE IF EXISTS gem_resultado;
DROP TABLE IF EXISTS gem_paquete; DROP TABLE IF EXISTS gem_meta; DROP TABLE IF EXISTS gem_espera;
DROP TABLE IF EXISTS gem_estado; DROP TABLE IF EXISTS gem_ing;
CREATE TABLE gem_meta (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE gem_espera (pid INTEGER PRIMARY KEY, fin TEXT, ing_dias REAL, compra_dias REAL);
CREATE TABLE gem_proyecto (pid INTEGER PRIMARY KEY, cod INTEGER, nombre TEXT, tipo TEXT, ton REAL, ini TEXT, fp TEXT, fr TEXT,
    en_muestra INTEGER, contratista TEXT, presupuesto REAL, ritmo REAL, n_lotes INTEGER, paquetes INTEGER, rfis INTEGER,
    cambios INTEGER, piezas_por_t REAL, pct_planchas REAL, hh_ratio REAL, hh_verdad REAL, origen TEXT DEFAULT 'SIMULADO',
    crew TEXT);
CREATE TABLE gem_lote (id INTEGER PRIMARY KEY, pid INTEGER, indice INTEGER, paquete INTEGER, elemento TEXT, perfil TEXT,
    kg REAL, n_piezas INTEGER, largo REAL, doblez INTEGER, nc INTEGER, adicional INTEGER, hh TEXT);
CREATE INDEX ix_gem_lote_pid ON gem_lote (pid);
CREATE TABLE gem_pieza (lote_id INTEGER, marca TEXT, perfil TEXT, kg REAL, largo REAL, agujeros INTEGER);
CREATE INDEX ix_gem_pieza_lote ON gem_pieza (lote_id);
CREATE TABLE gem_op (politica TEXT, id INTEGER, pid INTEGER, lote_id INTEGER, tipo TEXT, proceso INTEGER, recurso TEXT,
    estacion INTEGER, t_ini REAL, t_fin REAL, personas INTEGER, hh REAL);
CREATE INDEX ix_gem_op_t ON gem_op (politica, t_ini, t_fin);
CREATE INDEX ix_gem_op_lote ON gem_op (politica, lote_id);
CREATE TABLE gem_mov (politica TEXT, pid INTEGER, lote_id INTEGER, grua INTEGER, destino TEXT, t_ini REAL, t_fin REAL);
CREATE INDEX ix_gem_mov_t ON gem_mov (politica, t_ini, t_fin);
CREATE TABLE gem_camion (politica TEXT, pid INTEGER, tipo TEXT, t_ini REAL, t_fin REAL, kg REAL, n_lotes INTEGER);
CREATE TABLE gem_material (politica TEXT, pid INTEGER, paquete INTEGER, t_pedido REAL, t_llegada REAL, kg REAL);
CREATE TABLE gem_estado (politica TEXT, pid INTEGER, lote_id INTEGER, t REAL, etapa TEXT, ubic TEXT);
CREATE INDEX ix_gem_estado ON gem_estado (politica, pid, t);
CREATE TABLE gem_ing (politica TEXT, pid INTEGER, t_ini REAL, t_fin REAL, personas INTEGER);
CREATE TABLE gem_paquete (politica TEXT, pid INTEGER, paquete INTEGER, t_liberacion REAL, dias_rfi REAL);
CREATE TABLE gem_parada (maquina INTEGER, nombre TEXT, t_ini REAL, t_fin REAL, causa TEXT, planificada INTEGER, horas REAL);
CREATE TABLE gem_tareo (politica TEXT, fecha TEXT, pid INTEGER, proceso INTEGER, contratista TEXT, horas REAL);
CREATE INDEX ix_gem_tareo ON gem_tareo (politica, pid, proceso);
CREATE TABLE gem_personal (id INTEGER PRIMARY KEY, nombre TEXT, grupo TEXT, rol TEXT);
CREATE TABLE gem_palanca (politica TEXT, replica INTEGER, pid INTEGER, t REAL, tipo TEXT, proceso INTEGER, valor INTEGER, costo REAL);
CREATE TABLE gem_resultado (politica TEXT, replica INTEGER, pid INTEGER, cod INTEGER, en_muestra INTEGER, compromiso TEXT,
    fin TEXT, tarde INTEGER, penalidad REAL, costo REAL, lead INTEGER, intervenciones INTEGER);
'''

PREFIJO = {'Columna': 'C', 'Viga principal': 'VP', 'Tijeral': 'T', 'Viga secundaria': 'VS', 'Arriostre': 'A', 'Correa': 'CO',
           'Placa base': 'PB', 'Escalera': 'E', 'Templador': 'TM', 'Placa / conexión': 'PL'}


def crear(con):
    con.executescript(SCHEMA)


def personal():
    filas, n = [], 1
    for c, (_, _, plantilla) in CONTRATISTAS.items():
        sig = ''.join(w[0] for w in c.replace('&', ' ').split())[:3]
        for i in range(1, plantilla + 1):
            rol = 'Armador' if i % 3 == 1 else 'Soldador' if i % 3 == 2 else 'Ayudante'
            filas.append((n, f'{rol} {sig}-{i:02d}', c, rol))
            n += 1
    for g, rol, k in [('Planta', 'Operador de máquina', 8), ('Planta', 'Gruista', 3), ('Planta', 'Supervisor', 3),
                      ('Oficina técnica', 'Proyectista', 6), ('Compras', 'Comprador', 2), ('Despacho', 'Despachador', 4)]:
        for i in range(1, k + 1):
            filas.append((n, f'{rol} {g[:3].upper()}-{i:02d}', g, rol))
            n += 1
    return filas


def guardar_base(con, proyectos, paradas, factores, semilla):
    crear(con)
    con.execute('INSERT INTO gem_meta VALUES (?,?)', ('semilla', str(semilla)))
    con.execute('INSERT INTO gem_meta VALUES (?,?)', ('epoca', str(EPOCA)))
    con.execute('INSERT INTO gem_meta VALUES (?,?)', ('factores', json.dumps({str(k): v for k, v in factores.items()})))
    for p in proyectos:
        con.execute('INSERT INTO gem_proyecto VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (p.pid, p.cod, p.nombre, p.tipo, p.ton, str(p.ini), str(p.fp), str(p.fr), int(p.en_muestra), p.contratista,
                     p.presupuesto, factores.get(p.pid, 1.0), len(p.conjuntos), p.paquetes, len(p.rfis), len(p.cambios),
                     p.feats['piezas_por_t'], p.feats['pct_planchas'], float(p.hh_ratio.sum()), float(p.hh.sum()), 'SIMULADO',
                     json.dumps([float(x) for x in p.crew])))
        rng = np.random.default_rng([semilla, p.pid, 3])
        lotes, piezas = [], []
        for c in p.conjuntos:
            lotes.append((c.id, p.pid, c.indice, c.paquete, c.elemento, c.perfil, c.kg, c.n_piezas, c.largo, int(c.doblez),
                          int(c.nc), int(c.adicional), json.dumps({k: round(v, 2) for k, v in c.hh.items()})))
            w = rng.dirichlet(np.full(c.n_piezas, 3.0)) if c.n_piezas > 1 else np.array([1.0])
            pref = PREFIJO.get(c.elemento, 'P')
            for i in range(c.n_piezas):
                principal = i == int(np.argmax(w))
                piezas.append((c.id, f'{pref}{c.indice}-{i + 1}', c.perfil if principal else ('PL 3/8"' if i % 2 else 'L 2x2x3/16'),
                               round(float(c.kg * w[i]), 1), round(float(c.largo if principal else rng.uniform(0.2, 1.5)), 2),
                               int(rng.integers(0, 12))))
        con.executemany('INSERT INTO gem_lote VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', lotes)
        con.executemany('INSERT INTO gem_pieza VALUES (?,?,?,?,?,?)', piezas)
    base = turno_base()
    con.executemany('INSERT INTO gem_parada VALUES (?,?,?,?,?,?,?)',
                    [(k, MAQUINAS[k], a, b, c, pl, base.trabajado(a, b)) for k, a, b, c, pl in paradas])      # horas de trabajo perdidas
    con.executemany('INSERT INTO gem_personal VALUES (?,?,?,?)', personal())


def tareo(sim, res):
    """Horas-persona por día, proyecto y proceso (como la hoja TAREO del formato único)."""
    acc = {}
    for op in res.ops:
        if op.recurso.startswith('grua'):
            continue
        proc = OP_PROC.get(op.tipo)
        if proc is None:
            continue
        if op.recurso.startswith('maq'):
            v, pers = sim.v_maq[int(op.recurso[3])], 1
        else:
            v, pers = sim.crews[(op.pid, proc)].v, op.personas
        horas_op = v.por_dia(op.t_ini, op.t_fin)
        tot = sum(horas_op.values()) or 1.0
        for d, h in horas_op.items():
            k = (d, op.pid, proc)
            acc[k] = acc.get(k, 0.0) + op.horas * sim._ef(op.pid) * h / tot     # se reparten las HH del lote en sus días
    for pid, (t0, t1) in res.ingenieria.items():                    # oficina técnica
        p = sim.P[pid]
        dias = sim.base.por_dia(t0, max(t1, t0 + 1))
        tot = sum(dias.values()) or 1.0
        for d, h in dias.items():
            acc[(d, pid, 1)] = acc.get((d, pid, 1), 0.0) + p.hh[0] * sim._ef(pid) * h / tot
    return acc


def guardar_politica(con, sim, res, politica, detalle=True):
    if detalle:
        con.executemany('INSERT INTO gem_op VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        [(politica, o.id, o.pid, o.cid, o.tipo, OP_PROC.get(o.tipo), o.recurso, o.estacion, o.t_ini, o.t_fin,
                          o.personas, o.horas * sim._ef(o.pid)) for o in res.ops if not o.recurso.startswith('grua')])      # hh = horas en obra
        con.executemany('INSERT INTO gem_mov VALUES (?,?,?,?,?,?,?)', [(politica, *m) for m in res.movimientos])
        con.executemany('INSERT INTO gem_camion VALUES (?,?,?,?,?,?,?)', [(politica, *c) for c in res.camiones])
        con.executemany('INSERT INTO gem_material VALUES (?,?,?,?,?,?)', [(politica, *m) for m in res.material])
        con.executemany('INSERT INTO gem_paquete VALUES (?,?,?,?,?)', [(politica, *m) for m in res.paquetes])
        con.executemany('INSERT INTO gem_estado VALUES (?,?,?,?,?,?)',
                        [(politica, sim.conj[c].pid, c, t, e, u) for c, t, e, u in res.estados])
        con.executemany('INSERT INTO gem_ing VALUES (?,?,?,?,?)',
                        [(politica, pid, a, b, int(sim.P[pid].crew[0])) for pid, (a, b) in res.ingenieria.items()])
        acc = tareo(sim, res)
        con.executemany('INSERT INTO gem_tareo VALUES (?,?,?,?,?,?)',
                        [(politica, str(d), pid, proc, sim.P[pid].contratista if proc in (8, 9, 10) else 'Steelser', round(h, 3))
                         for (d, pid, proc), h in acc.items()])


def guardar_esperas(con, sim, res):
    """Esperas observables por proyecto (días laborables): ingeniería con RFIs y compra de material (primer pedido a última
    llegada). Salen del registro de órdenes de compra y de la oficina técnica; el DSS las aprende de los proyectos terminados."""
    from .calibrar import dias_lab
    for p in sim.P.values():
        pk = [x for x in res.paquetes if x[0] == p.pid]
        mt = [x for x in res.material if x[0] == p.pid]
        ing = dias_lab(p.ini, fecha(max(x[2] for x in pk))) if pk else 5
        comp = dias_lab(fecha(min(x[2] for x in mt)), fecha(max(x[3] for x in mt))) if mt else 10
        con.execute('INSERT INTO gem_espera VALUES (?,?,?,?)', (p.pid, str(fecha(res.fin[p.pid])), float(ing), float(comp)))


def guardar_mundo(con, sim, res):
    """Escribe el mundo 6 en las tablas sim_* que usan el QRF y el Monte Carlo (solo los 25 de la muestra)."""
    for t in ('sim_proyecto_proceso', 'sim_parada', 'sim_verificacion'):
        con.execute(f'DELETE FROM {t} WHERE mundo_id=?', (MUNDO,))
    con.execute('DELETE FROM sim_mundo WHERE id=?', (MUNDO,))
    con.execute('INSERT INTO sim_mundo VALUES (?,?,?,?)',
                (MUNDO, NOMBRE_MUNDO, 'Gemelo de eventos discretos: HH por lote, máquinas con fallas, grúas, cuadrillas con '
                 'ausentismo, proveedores, RFIs, retrabajos y lotes a pintura. Calibrado a las fechas reales.', json.dumps({})))
    proc_ids = dict(con.execute('SELECT orden, id FROM proceso'))
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    ventanas = {}
    for op in res.ops:
        proc = OP_PROC.get(op.tipo)
        if proc is None or op.recurso.startswith('grua'):
            continue
        a, b = ventanas.get((op.pid, proc), (op.t_ini, op.t_fin))
        ventanas[(op.pid, proc)] = (min(a, op.t_ini), max(b, op.t_fin))
    filas = []
    for p in sim.P.values():
        if not p.en_muestra:
            continue
        ini_t = hora(p.ini, 7.0)
        ing = res.ingenieria.get(p.pid, (ini_t, ini_t))
        mat = [(m[2], m[3]) for m in res.material if m[0] == p.pid]
        cam = {t: [(c[2], c[3]) for c in res.camiones if c[0] == p.pid and c[1] == t] for t in ('doblez', 'pintura', 'obra')}
        win = {1: ing, 2: (min(a for a, _ in mat), max(b for _, b in mat)) if mat else ing}
        for j in (3, 4, 5, 6, 8, 9, 10):
            win[j] = ventanas.get((p.pid, j), (ini_t, ini_t))
        win[7] = (min(a for a, _ in cam['doblez']), max(b for _, b in cam['doblez'])) if cam['doblez'] else win[3]
        win[11] = (min(a for a, _ in cam['pintura']), max(a for a, _ in cam['pintura'])) if cam['pintura'] else win[10]
        win[12] = (min(a for a, _ in cam['pintura']), max(b for _, b in cam['pintura'])) if cam['pintura'] else win[10]
        win[13] = (min(a for a, _ in cam['obra']), max(b for _, b in cam['obra'])) if cam['obra'] else win[12]
        for j in range(1, 14):
            hh = sim.hh_hecho.get((p.pid, j), 0.0) if j in (3, 4, 5, 6, 8, 9, 10) else float(p.hh[j - 1])
            hh = hh if hh > 0 else float(p.hh[j - 1])
            a, b = win[j]
            dias = max(1, sim.base.trabajado(a, b) / 8.0)
            filas.append((MUNDO, p.pid, proc_ids[j], hh, hh / float(p.hh_ratio[j - 1]), int(round(dias)),
                          str(fecha(a)), str(fecha(b))))
    con.executemany('''INSERT INTO sim_proyecto_proceso (mundo_id, proyecto_id, proceso_id, hh_real, phi, dias_real, f_inicio, f_fin)
                       VALUES (?,?,?,?,?,?,?,?)''', filas)
    con.executemany('INSERT INTO sim_parada VALUES (?,?,?,?,?)',
                    [(MUNDO, cen[MAQUINAS[k]], str(fecha(a)), (b - a) / 8.0, pl) for k, a, b, _c, pl in sim.paradas])
    from .calibrar import dias_lab
    for p in sim.P.values():
        if p.en_muestra:
            real = dias_lab(p.ini, p.fr)
            s = dias_lab(p.ini, fecha(res.fin[p.pid]))
            con.execute('INSERT INTO sim_verificacion VALUES (?,?,?,?,?,?,?)',
                        (MUNDO, p.cod, real, s, s - real, None, float(np.average(p.phi, weights=p.hh_ratio))))
