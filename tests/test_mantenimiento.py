import sqlite3
from datetime import date, datetime, timedelta

import pytest
import asyncio

from fastapi import FastAPI, HTTPException

from dss.mantenimiento import dias_laborables, disponibilidad_futura, dk_mensual, indicadores, proximo_vencimiento, semaforo
from plataforma import db_plataforma as dbp
from plataforma import mantenimiento as mant


def test_indicadores_tpm():
    # semana lun 5/10/2026 – sáb 10/10/2026: 6 días laborables × 8 h = 48 h programadas
    par = [dict(inicio='2026-10-06 08:00', fin='2026-10-06 12:00', planificada=0, causa='Falla eléctrica'),
           dict(inicio='2026-10-08 10:00', fin='2026-10-08 12:00', planificada=0, causa='Falla mecánica'),
           dict(inicio='2026-10-09 08:00', fin='2026-10-09 10:00', planificada=1, causa='Mantenimiento preventivo'),
           dict(inicio='2026-09-01 08:00', fin='2026-09-01 18:00', planificada=0, causa='Falla eléctrica')]   # fuera del periodo
    r = indicadores(par, '2026-10-05', '2026-10-11')
    assert dias_laborables('2026-10-05', '2026-10-11') == 6 and r['tp_h'] == 48
    assert r['horas_parada'] == 8 and r['horas_falla'] == 6 and r['n_fallas'] == 2
    assert r['dk'] == pytest.approx(40 / 48, abs=1e-4)
    assert r['mtbf_h'] == 20 and r['mttr_h'] == 3 and r['pct_preventivo'] == pytest.approx(0.25)
    assert r['causas'][0] == {'causa': 'Falla eléctrica', 'horas': 4.0}
    assert indicadores([], '2026-10-05', '2026-10-11')['dk'] == 1.0 and indicadores([], '2026-10-05', '2026-10-11')['mtbf_h'] is None


def test_parada_que_cruza_el_periodo_se_recorta():
    par = [dict(inicio='2026-10-10 20:00', fin='2026-10-12 10:00', planificada=0, causa='Falla mecánica')]
    assert indicadores(par, '2026-10-12', '2026-10-14')['horas_parada'] == 10          # 10 h del lunes 12
    assert indicadores(par, '2026-10-12', '2026-10-13')['horas_parada'] == 8            # nunca más que lo programado (1 turno)


def test_vencimiento_y_semaforo():
    plan = dict(frecuencia_dias=6, desde='2026-10-05')
    assert proximo_vencimiento(plan, None, '2026-10-05') == ('2026-10-12', 6)
    assert proximo_vencimiento(plan, '2026-10-01', '2026-10-12')[1] < 0                       # vencido
    assert proximo_vencimiento(dict(frecuencia_horas=48, desde='2026-10-05'), None, '2026-10-05')[0] == '2026-10-12'
    assert semaforo(0.95) == 'v' and semaforo(0.85) == 'a' and semaforo(0.95, vencidas=1) == 'a' and semaforo(0.7) == 'r'
    assert semaforo(0.99, parada_ahora=True) == 'r'


def test_dk_mensual_y_disponibilidad_futura():
    par = [dict(inicio='2026-09-07 08:00', fin='2026-09-07 16:00', planificada=0, causa='Falla eléctrica')]
    m = dk_mensual(par, '2026-10-07', meses=3)
    assert [x['mes'] for x in m] == ['2026-08', '2026-09', '2026-10'] and m[1]['n_fallas'] == 1 and m[1]['dk'] < 1 == m[0]['dk'] * 1
    d = disponibilidad_futura([dict(maquina='Mesa CNC', programada_para='2026-10-07', duracion_h=4)], '2026-10-05', 10, ['Sierra', 'Mesa CNC'])
    assert d.shape == (10, 2) and d[2, 1] == 0.5 and d[2, 0] == 1 and d.sum() == 19.5


@pytest.fixture
def cliente():
    con = sqlite3.connect(':memory:', check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(dbp.ESQUEMA)
    dbp._migrar(con)
    dbp.crear_usuario(con, 'jt', 'Jefe de taller', 'jefe_taller', clave='clave-de-prueba')
    dbp._sembrar_maquinas(con)
    app = FastAPI()
    usuario = {'id': 1, 'nombre': 'Jefe de taller', 'rol': 'jefe_taller'}

    def plat():
        yield con

    def requiere(*roles):
        return lambda: usuario

    def actividad(c, u, tipo, detalle, proyecto_id=None, tarea_id=None):
        c.execute('INSERT INTO actividad (usuario_id, tipo, detalle) VALUES (?,?,?)', (u['id'], tipo, detalle))

    mant.registrar(app, plat, lambda: usuario, requiere, actividad, ['Falla mecánica', 'Falla eléctrica', 'Mantenimiento preventivo'],
                   lambda c: [dict(maquina='Mesa CNC', inicio=f'{date.today()} 08:00', fin=f'{date.today()} 16:00', titulo='OT-1 · Mesa CNC',
                                   detalle='', proyecto='OT-1', ref='proyecto:1')])
    return Cliente(app, usuario, con), con


class Cliente:
    """Llama a las funciones de las rutas directamente (sin servidor HTTP), con la sesión y la BD de prueba."""

    def __init__(self, app, usuario, con):
        self.rutas = {(m, r.path): r for r in app.routes for m in getattr(r, 'methods', ())}
        self.u, self.con = usuario, con

    def _llamar(self, metodo, url, params=None, json=None):
        partes = url.strip('/').split('/')
        for (m, path), r in self.rutas.items():
            pp = path.strip('/').split('/')
            if m != metodo or len(pp) != len(partes) or any(a != b and not a.startswith('{') for a, b in zip(pp, partes)):
                continue
            kw = {a[1:-1]: int(b) for a, b in zip(pp, partes) if a.startswith('{')}
            kw.update(params or {})
            for nombre, campo in r.endpoint.__annotations__.items():
                if json is not None and isinstance(campo, type) and hasattr(campo, 'model_validate'):
                    kw[nombre] = campo.model_validate(json)
            kw.update(u=self.u, p=self.con)
            try:
                return Resp(200, r.endpoint(**kw))
            except HTTPException as e:
                return Resp(e.status_code, {'detail': e.detail})
        raise AssertionError(f'ruta no encontrada: {metodo} {url}')

    get = lambda self, url, params=None: self._llamar('GET', url, params)
    post = lambda self, url, json=None: self._llamar('POST', url, json=json)
    patch = lambda self, url, json=None: self._llamar('PATCH', url, json=json)


class Resp:
    def __init__(self, status_code, cuerpo):
        self.status_code, self.cuerpo = status_code, cuerpo

    def json(self):
        return self.cuerpo

    @property
    def content(self):
        async def leer():
            return b''.join([c async for c in self.cuerpo.body_iterator])
        return asyncio.run(leer())


def test_flujo_de_ordenes(cliente):
    c, con = cliente
    r = c.get('/api/mant/maquinas').json()
    assert len(r['maquinas']) == 4 and r['resumen']['paradas_ahora'] == 0
    assert con.execute('SELECT COUNT(*) FROM plan_mantenimiento').fetchone()[0] == 8
    # los 3 planes semanales (6 días) vencen dentro del horizonte de 10 días → se generan solas, una por plan, sin
    # duplicar; el de la roscadora (12 días) y los mensuales todavía no
    n = con.execute("SELECT COUNT(*) FROM orden_mantenimiento WHERE tipo='PREVENTIVO'").fetchone()[0]
    c.get('/api/mant/ordenes')
    assert n == 3 and con.execute("SELECT COUNT(*) FROM orden_mantenimiento").fetchone()[0] == 3
    # correctiva: se abre, se cierra con inicio/fin y deja su parada (no planificada) enlazada
    mid = r['maquinas'][2]['id']
    oid = c.post('/api/mant/ordenes', json=dict(maquina_id=mid, titulo='Falla del pórtico')).json()['id']
    hace = lambda h: (datetime.now() - timedelta(hours=h)).strftime('%Y-%m-%d %H:%M')
    assert c.patch(f'/api/mant/ordenes/{oid}', json=dict(estado='CERRADA', fin=hace(1))).status_code == 422     # falta inicio
    assert c.patch(f'/api/mant/ordenes/{oid}', json=dict(estado='CERRADA', inicio=hace(3), fin=hace(1), causa='Falla eléctrica')).status_code == 200
    pa = con.execute('SELECT * FROM parada WHERE orden_id=?', (oid,)).fetchone()
    assert pa and pa['planificada'] == 0 and pa['causa'] == 'Falla eléctrica' and pa['maquina'] == 'Mesa CNC'
    assert c.patch(f'/api/mant/ordenes/{oid}', json=dict(estado='EN_CURSO')).status_code == 422                  # ya cerrada
    f = c.get(f'/api/mant/maquinas/{mid}').json()
    assert f['indicadores']['30d']['n_fallas'] == 1 and f['indicadores']['30d']['horas_falla'] == pytest.approx(2, abs=0.05)
    # cerrar el preventivo de esa máquina crea una parada planificada y programa el siguiente
    pv = con.execute("SELECT id, plan_id FROM orden_mantenimiento WHERE maquina_id=? AND tipo='PREVENTIVO'", (mid,)).fetchone()
    assert c.patch(f'/api/mant/ordenes/{pv["id"]}', json=dict(estado='CERRADA', inicio=hace(2), fin=hace(1))).status_code == 200
    assert con.execute('SELECT planificada FROM parada WHERE orden_id=?', (pv['id'],)).fetchone()[0] == 1
    sig = con.execute("SELECT programada_para FROM orden_mantenimiento WHERE plan_id=? AND estado='PENDIENTE'", (pv['plan_id'],)).fetchone()
    assert sig and sig[0] > str(date.today())
    # Gantt: paradas, órdenes abiertas y operaciones de proyectos en una sola respuesta; filtros y Excel de paradas
    g = c.get('/api/mant/gantt', params=dict(dias=30)).json()
    assert {'falla', 'planificada', 'orden_preventivo', 'proyecto'} <= {x['tipo'] for x in g['items']}
    p = c.get('/api/mant/paradas', params=dict(tipo='falla')).json()
    assert p['n'] == 1 and p['por_causa'][0]['clave'] == 'Falla eléctrica'
    x = c.get('/api/mant/paradas/excel')
    assert x.status_code == 200 and x.content[:2] == b'PK'
    # desactivar un plan anula su orden pendiente
    plid = con.execute("SELECT plan_id FROM orden_mantenimiento WHERE estado='PENDIENTE' LIMIT 1").fetchone()[0]
    c.patch(f'/api/mant/planes/{plid}', json=dict(activo=False))
    assert con.execute("SELECT estado FROM orden_mantenimiento WHERE plan_id=? ORDER BY id DESC", (plid,)).fetchone()[0] == 'ANULADA'


def test_meses_sin_registro_no_cuentan_como_disponibles():
    par = [dict(inicio='2026-09-22 08:00', fin='2026-09-22 14:00', planificada=0, causa='Falla eléctrica')]
    m = dk_mensual(par, '2026-10-07', meses=4, desde_registro='2026-09-22')
    assert [x['dk'] for x in m[:2]] == [None, None]                        # julio y agosto: sin dato, no 100 %
    sep = m[2]
    assert sep['n_fallas'] == 1 and sep['dk'] == pytest.approx(1 - 6 / (8 * 8), abs=1e-3)   # 22–30/09: 8 días laborables
