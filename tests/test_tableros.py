import json
import sqlite3
from datetime import date, timedelta

from fastapi import FastAPI

from plataforma import db_plataforma as dbp
from plataforma import tableros

HOY = date.today()


def _bds():
    p = sqlite3.connect(':memory:', check_same_thread=False)
    p.row_factory = sqlite3.Row
    p.executescript(dbp.ESQUEMA)
    dbp._migrar(p)
    dbp._sembrar_maquinas(p)
    h = sqlite3.connect(':memory:', check_same_thread=False)
    h.row_factory = sqlite3.Row
    h.execute('CREATE TABLE proyecto (id INTEGER, n_registro INTEGER, codigo_muestra INTEGER, nombre TEXT, cliente TEXT, fecha_fin_real TEXT, dias_retraso REAL)')
    hace = lambda d: str(HOY - timedelta(days=d))
    h.executemany('INSERT INTO proyecto VALUES (?,?,?,?,?,?,?)', [(1, 1, 1, 'A', 'C1', hace(40), 0), (2, 2, 2, 'B', 'C2', hace(70), 3),
                                                                (3, 3, 3, 'Viejo', 'C3', hace(500), 0)])
    # proyecto de la plataforma entregado tarde pero dentro de la ampliación concedida → a tiempo
    p.execute('''INSERT INTO proyecto_activo (codigo, nombre, tipo, ton, inicio, fecha_comprometida, estado, fecha_fin_real, ampliacion_dias)
                 VALUES ('OT-1', 'P', 'Nave', 10, ?, ?, 'ENTREGADO', ?, 5)''', (hace(90), hace(15), hace(12)))
    # plan aprobado: Sierra sin capacidad 10 días, Mesa CNC saturada 3 días
    fechas = [str(HOY + timedelta(days=k)) for k in range(12)]
    carga = [dict(maquina='Sierra', horas=[0.0] * 12, capacidad=[0.0] * 10 + [8.0, 8.0]),
             dict(maquina='Mesa CNC', horas=[8.0] * 3 + [2.0] * 9, capacidad=[8.0] * 12)]
    res = dict(hoy=str(HOY), fechas=fechas, carga=carga, proyectos=[dict(id=None, codigo='OT-9', prioridad=1, compromiso=hace(-30), p50=hace(-20), p80=hace(-25),
                                                                          prob_cumplir=0.5, alpha=0.8, penalidad=1200.0)])
    p.execute("INSERT INTO plan_version (motivo, regla, estado, resultado) VALUES ('t', 'penalidad', 'APROBADO', ?)", (json.dumps(res),))
    return p, h


def _rutas():
    app = FastAPI()
    tableros.registrar(app, None, None, lambda: None, lambda p: [], lambda p, r: None,
                       lambda p: dict(filas=[], resumen=dict(dias_cliente=0, dias_steelser=0)), lambda p: [])
    return {r.path: r.endpoint for r in app.routes if '/tableros/' in getattr(r, 'path', '')}


def test_gerencia_y_produccion():
    p, h = _bds()
    rutas = _rutas()
    g = rutas['/api/tableros/gerencia'](u=None, p=p, h=h)
    assert g['otd']['entregas'] == 3 and g['otd']['a_tiempo'] == 2          # el de hace 500 días queda fuera de los 12 meses
    assert len(g['otd']['meses']) == 12 and g['otd']['meses'][-1]['mes'] == HOY.strftime('%Y-%m')
    assert g['penalidad_total'] == 1200 and g['proyectos'][0]['semaforo'] == 'r'
    assert g['plan']['estado'] == 'APROBADO' and len(g['carga']) == 2
    pr = rutas['/api/tableros/produccion'](u=None, p=p)
    cu = {c['maquina']: c for c in pr['cuellos']}
    assert cu['Sierra']['dias_saturada'] == 0 and cu['Sierra']['dias_sin_capacidad'] == 10     # sin capacidad no cuenta como saturada
    assert cu['Mesa CNC']['dias_saturada'] == 3


def test_mensual():
    p, h = _bds()
    m = _rutas()['/api/tableros/mensual'](mes=HOY.strftime('%Y-%m'), u=None, p=p, h=h)
    assert m['mes'] == HOY.strftime('%Y-%m') and len(m['maquinas']) == 4
    assert all(x['indicadores'] is None for x in m['maquinas'])           # sin paradas registradas no se inventa disponibilidad
