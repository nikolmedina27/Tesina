"""BD operativa de la plataforma (data/plataforma.db).

Separada de data/steelser.db a propósito: steelser.db es el histórico que `scripts/build_db.py` recrea desde
cero; aquí vive lo que se registra día a día (usuarios, proyectos en curso, tareo, paradas, tareas), que nunca
debe borrarse al reconstruir el histórico.
"""
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / 'data' / 'plataforma.db'
CREDENCIALES = RAIZ / 'data' / 'credenciales_demo.txt'

ROLES = {
    'gerencia': 'Gerencia (administra usuarios y ve todo)',
    'cotizador': 'Cotizaciones (cotiza y crea proyectos)',
    'jefe_taller': 'Jefe de taller (programa, registra tareo y paradas)',
    'supervisor': 'Supervisor / contratista (registra su tareo y sus tareas)',
    'calidad': 'Calidad (liberaciones y no conformidades)',
    'mantenimiento': 'Mantenimiento (órdenes, plan preventivo y fichas de máquinas)',
}

ESQUEMA = '''
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY, usuario TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, rol TEXT NOT NULL,
    area TEXT, color TEXT, clave_hash TEXT NOT NULL, sal TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS proyecto_activo (
    id INTEGER PRIMARY KEY, codigo TEXT UNIQUE NOT NULL, cliente TEXT, nombre TEXT NOT NULL, tipo TEXT NOT NULL,
    ton REAL NOT NULL, pct_planchas REAL, piezas_por_t REAL, m2_pint_t REAL, montaje INTEGER DEFAULT 0,
    presupuesto REAL, moneda TEXT DEFAULT 'USD', inicio TEXT NOT NULL, fecha_comprometida TEXT, alpha REAL,
    prob_cumplir REAL, estado TEXT NOT NULL DEFAULT 'EN_CURSO'
        CHECK (estado IN ('COTIZADO','EN_CURSO','PAUSADO','ENTREGADO','PERDIDO')),
    es_demo INTEGER NOT NULL DEFAULT 0, cotizacion_json TEXT, creado_por INTEGER REFERENCES usuario(id),
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS tareo (
    id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, proyecto_id INTEGER NOT NULL REFERENCES proyecto_activo(id),
    proceso INTEGER NOT NULL CHECK (proceso BETWEEN 1 AND 13), contratista TEXT, n_personas INTEGER NOT NULL,
    horas_persona REAL NOT NULL, hh REAL GENERATED ALWAYS AS (n_personas * horas_persona) STORED,
    kg_avanzados REAL, observacion TEXT, registrado_por INTEGER REFERENCES usuario(id),
    registrado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS parada (
    id INTEGER PRIMARY KEY, maquina TEXT NOT NULL, inicio TEXT NOT NULL, fin TEXT NOT NULL,
    planificada INTEGER NOT NULL, causa TEXT NOT NULL, proyecto_id INTEGER REFERENCES proyecto_activo(id),
    observacion TEXT, registrado_por INTEGER REFERENCES usuario(id), registrado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS tarea (
    id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, descripcion TEXT, proyecto_id INTEGER REFERENCES proyecto_activo(id),
    proceso INTEGER, estado TEXT NOT NULL DEFAULT 'POR_HACER'
        CHECK (estado IN ('BACKLOG','POR_HACER','EN_CURSO','REVISION','HECHO')),
    prioridad INTEGER NOT NULL DEFAULT 3 CHECK (prioridad BETWEEN 1 AND 4),
    tipo TEXT NOT NULL DEFAULT 'TAREA' CHECK (tipo IN ('TAREA','BLOQUEO','NO_CONFORMIDAD','RFI','CAMBIO_ALCANCE','COMPRA')),
    responsable_id INTEGER REFERENCES usuario(id), creado_por INTEGER REFERENCES usuario(id),
    fecha_limite TEXT, creado_en TEXT DEFAULT CURRENT_TIMESTAMP, actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS comentario (
    id INTEGER PRIMARY KEY, tarea_id INTEGER NOT NULL REFERENCES tarea(id), usuario_id INTEGER REFERENCES usuario(id),
    texto TEXT NOT NULL, creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS actividad (
    id INTEGER PRIMARY KEY, usuario_id INTEGER REFERENCES usuario(id), tipo TEXT NOT NULL, detalle TEXT,
    proyecto_id INTEGER, tarea_id INTEGER, creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
-- v2: formato único importado desde Excel
CREATE TABLE IF NOT EXISTS pieza (
    id INTEGER PRIMARY KEY, proyecto_id INTEGER NOT NULL REFERENCES proyecto_activo(id), n_item INTEGER, tipo_elemento TEXT,
    conjunto TEXT, perfil TEXT, longitud_mm REAL, cantidad INTEGER, peso_unit REAL, peso_total REAL, clase_peso TEXT,
    area_m2 REAL, contratista TEXT, orden_fab TEXT, pu_kg REAL, f_habilitado TEXT, f_armado TEXT, f_soldeo TEXT,
    f_liberacion TEXT, f_granallado TEXT, f_pintura TEXT, f_despacho TEXT, importacion_id INTEGER,
    UNIQUE (proyecto_id, conjunto, n_item));
CREATE TABLE IF NOT EXISTS cotiz_proceso (
    proyecto_id INTEGER NOT NULL REFERENCES proyecto_activo(id), proceso INTEGER NOT NULL, hh_estimadas REAL,
    dias_estimados REAL, cuadrilla INTEGER, contratista TEXT, estimado_por TEXT, fecha TEXT, PRIMARY KEY (proyecto_id, proceso));
CREATE TABLE IF NOT EXISTS proceso_fecha (
    proyecto_id INTEGER NOT NULL REFERENCES proyecto_activo(id), proceso INTEGER NOT NULL, inicio TEXT, fin TEXT,
    cuadrilla REAL, observacion TEXT, PRIMARY KEY (proyecto_id, proceso));
CREATE TABLE IF NOT EXISTS servicio_externo (
    id INTEGER PRIMARY KEY, proyecto_id INTEGER REFERENCES proyecto_activo(id), servicio TEXT, proveedor TEXT,
    fecha_envio TEXT, fecha_retorno TEXT, kg REAL, m2 REAL, observacion TEXT,
    UNIQUE (proyecto_id, servicio, proveedor, fecha_envio));
CREATE TABLE IF NOT EXISTS compra (
    id INTEGER PRIMARY KEY, proyecto_id INTEGER REFERENCES proyecto_activo(id), n_oc TEXT, proveedor TEXT, material TEXT,
    kg REAL, fecha_pedido TEXT, fecha_prometida TEXT, fecha_recepcion TEXT, certificado TEXT, UNIQUE (proyecto_id, n_oc, material));
CREATE TABLE IF NOT EXISTS evento (
    id INTEGER PRIMARY KEY, proyecto_id INTEGER REFERENCES proyecto_activo(id), fecha TEXT, tipo TEXT, imputable TEXT,
    dias_impacto REAL, pidio_ampliacion INTEGER, descripcion TEXT, UNIQUE (proyecto_id, fecha, tipo, descripcion));
CREATE TABLE IF NOT EXISTS importacion (
    id INTEGER PRIMARY KEY, archivo TEXT, usuario_id INTEGER REFERENCES usuario(id), resumen TEXT,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
-- v2.1: historial de re-pronósticos (permite medir alertas tempranas en el piloto) y cambios de pieza
CREATE TABLE IF NOT EXISTS pronostico (
    id INTEGER PRIMARY KEY, proyecto_id INTEGER NOT NULL REFERENCES proyecto_activo(id), fecha TEXT NOT NULL,
    p50 TEXT, p80 TEXT, p90 TEXT, prob_cumplir REAL, penalidad REAL, avance_hh REAL, avance_fisico REAL,
    semaforo TEXT, usuario_id INTEGER REFERENCES usuario(id), creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS pieza_cambio (
    id INTEGER PRIMARY KEY, pieza_id INTEGER NOT NULL REFERENCES pieza(id), etapa TEXT NOT NULL, antes TEXT, despues TEXT,
    usuario_id INTEGER REFERENCES usuario(id), creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
-- v3: mantenimiento de máquinas (fichas, plan preventivo y órdenes); las paradas siguen en `parada`
CREATE TABLE IF NOT EXISTS maquina (
    id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL, centro TEXT, marca TEXT, modelo TEXT, anio INTEGER,
    criticidad TEXT DEFAULT 'A' CHECK (criticidad IN ('A','B','C')), horas_turno REAL DEFAULT 8, turnos INTEGER DEFAULT 1,
    descripcion TEXT, activa INTEGER NOT NULL DEFAULT 1, creado_en TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS plan_mantenimiento (
    id INTEGER PRIMARY KEY, maquina_id INTEGER NOT NULL REFERENCES maquina(id), tarea TEXT NOT NULL,
    frecuencia_dias INTEGER, frecuencia_horas REAL, duracion_h REAL NOT NULL DEFAULT 1, responsable TEXT,
    desde TEXT, activo INTEGER NOT NULL DEFAULT 1, origen TEXT DEFAULT 'manual', creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
    CHECK (frecuencia_dias IS NOT NULL OR frecuencia_horas IS NOT NULL));
CREATE TABLE IF NOT EXISTS orden_mantenimiento (
    id INTEGER PRIMARY KEY, maquina_id INTEGER NOT NULL REFERENCES maquina(id), plan_id INTEGER REFERENCES plan_mantenimiento(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('PREVENTIVO','CORRECTIVO','PREDICTIVO')),
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE','EN_CURSO','CERRADA','ANULADA')),
    titulo TEXT NOT NULL, descripcion TEXT, programada_para TEXT, duracion_h REAL, inicio TEXT, fin TEXT, tecnico TEXT,
    repuestos TEXT, costo REAL, parada_id INTEGER REFERENCES parada(id), creado_por INTEGER REFERENCES usuario(id),
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP, cerrado_en TEXT);
-- v3.1: programación automática de la cartera. Se guardan TODAS las versiones (propuestas, aprobadas, descartadas):
-- son la línea base para contar reprogramaciones y medir si los avisos llegaron a tiempo.
CREATE TABLE IF NOT EXISTS plan_version (
    id INTEGER PRIMARY KEY, creado_en TEXT DEFAULT CURRENT_TIMESTAMP, motivo TEXT NOT NULL, regla TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PROPUESTO' CHECK (estado IN ('PROPUESTO','APROBADO','DESCARTADO','REEMPLAZADO')),
    creado_por INTEGER REFERENCES usuario(id), aprobado_por INTEGER REFERENCES usuario(id), aprobado_en TEXT,
    huella TEXT, resultado TEXT NOT NULL, cambios TEXT, avisos TEXT);
CREATE TABLE IF NOT EXISTS plan_proyecto (
    plan_id INTEGER NOT NULL REFERENCES plan_version(id), proyecto_id INTEGER, codigo TEXT, prioridad INTEGER,
    compromiso TEXT, p50 TEXT, p80 TEXT, prob_cumplir REAL, penalidad REAL, PRIMARY KEY (plan_id, codigo));
CREATE TABLE IF NOT EXISTS plan_linea (
    plan_id INTEGER NOT NULL REFERENCES plan_version(id), proyecto_id INTEGER, codigo TEXT, proceso INTEGER,
    inicio TEXT, fin TEXT, hh REAL, PRIMARY KEY (plan_id, codigo, proceso));
'''

# columnas agregadas en v2 a tablas que ya existían (migración sin perder datos)
COLUMNAS_V2 = {
    'proyecto_activo': [('n_piezas', 'INTEGER'), ('metros_soldadura', 'REAL'), ('fuente_ton', 'TEXT'), ('fecha_pedida', 'TEXT'),
                        ('fecha_fin_real', 'TEXT'), ('ampliacion_dias', 'REAL'), ('penalidad_aplicada', 'REAL'),
                        ('resultado_cot', 'TEXT'), ('plazo_competidor', 'REAL'), ('motivo_perdida', 'TEXT')],
    # v2.1: bandeja de RFI / no conformidades
    'tarea': [('imputable', 'TEXT'), ('dias_impacto', 'REAL'), ('conjunto', 'TEXT'), ('fecha_cierre', 'TEXT')],
    # v3: una parada puede venir de (o generar) una orden de mantenimiento
    'parada': [('orden_id', 'INTEGER')],
}

# v3: fichas de las 4 máquinas de habilitado y un plan preventivo SUGERIDO (frecuencias típicas de fabricante;
# validar con la empresa). Se siembran una sola vez, también en BD que ya existían.
MAQUINAS_INICIALES = [
    ('Sierra Cinta Kaltenbach', 'Habilitado · corte de perfiles', 'Kaltenbach', 'A',
     [('Inspección y tensado de la hoja, limpieza de viruta y refrigerante', 6, 1.0),
      ('Lubricación general y revisión del sistema hidráulico', 26, 3.0)]),
    ('Cizalladora Punzonadora Pedimax', 'Habilitado · corte y punzonado', 'Pedimax', 'A',
     [('Lubricación y revisión de punzones y matrices', 6, 1.0), ('Revisión del sistema hidráulico y cuchillas', 26, 3.0)]),
    ('Mesa CNC', 'Habilitado · corte de planchas', None, 'A',
     [('Cambio de consumibles y limpieza de la mesa', 6, 1.5), ('Calibración de ejes y limpieza de rieles', 26, 3.0)]),
    ('Roscadora RIDGID', 'Habilitado · roscado de barra', 'RIDGID', 'B',
     [('Limpieza, cambio de aceite de corte y revisión de peines', 12, 0.5), ('Revisión eléctrica y del motor', 78, 2.0)]),
]


def _sembrar_maquinas(con):
    if con.execute('SELECT COUNT(*) FROM maquina').fetchone()[0]:
        return
    hoy = str(date.today())
    for nombre, centro, marca, crit, planes in MAQUINAS_INICIALES:
        mid = con.execute('INSERT INTO maquina (nombre, centro, marca, criticidad) VALUES (?,?,?,?)', (nombre, centro, marca, crit)).lastrowid
        con.executemany('''INSERT INTO plan_mantenimiento (maquina_id, tarea, frecuencia_dias, duracion_h, desde, origen)
                           VALUES (?,?,?,?,?, 'sugerido')''', [(mid, t, f, h, hoy) for t, f, h in planes])
    con.commit()


def _migrar(con):
    for tabla, cols in COLUMNAS_V2.items():
        existentes = {r[1] for r in con.execute(f'PRAGMA table_info({tabla})')}
        for nombre, tipo in cols:
            if nombre not in existentes:
                con.execute(f'ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}')

COLORES = ['#0a6ed1', '#e9730c', '#107e3e', '#925ace', '#c0399f', '#1a9898', '#5b738b']


def hash_clave(clave, sal=None):
    sal = sal or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', clave.encode(), bytes.fromhex(sal), 200_000).hex()
    return h, sal


def verificar_clave(clave, h, sal):
    return secrets.compare_digest(hash_clave(clave, sal)[0], h)


def conectar():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def crear_usuario(con, usuario, nombre, rol, area='', clave=None):
    assert rol in ROLES, rol
    clave = clave or secrets.token_urlsafe(9)
    h, sal = hash_clave(clave)
    n = con.execute('SELECT COUNT(*) FROM usuario').fetchone()[0]
    con.execute('INSERT INTO usuario (usuario, nombre, rol, area, color, clave_hash, sal) VALUES (?,?,?,?,?,?,?)',
                (usuario, nombre, rol, area, COLORES[n % len(COLORES)], h, sal))
    return clave


def inicializar():
    """Crea el esquema y, si la BD está vacía, usuarios y un proyecto DEMO (marcado como tal)."""
    con = conectar()
    con.executescript(ESQUEMA)
    _migrar(con)
    con.commit()
    _sembrar_maquinas(con)
    if con.execute('SELECT COUNT(*) FROM usuario').fetchone()[0] == 0:
        demo = [('gerencia', 'Gerencia (demo)', 'gerencia', 'Gerencia'),
                ('cotizador', 'Cotizador (demo)', 'cotizador', 'Comercial'),
                ('taller', 'Jefe de taller (demo)', 'jefe_taller', 'Planta'),
                ('supervisor', 'Supervisor contratista (demo)', 'supervisor', 'Planta'),
                ('calidad', 'Calidad (demo)', 'calidad', 'Calidad')]
        lineas = ['# Usuarios de DEMOSTRACIÓN de SteelPlan (generados al crear data/plataforma.db).',
                  '# Cambiar o desactivar antes de usar con datos reales. Este archivo NO se versiona.', '']
        for u, nombre, rol, area in demo:
            lineas.append(f'{u:12} {crear_usuario(con, u, nombre, rol, area)}   ({ROLES[rol]})')
        CREDENCIALES.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
        _sembrar_demo(con)
        con.commit()
    con.close()


def _sembrar_demo(con):
    hoy = date.today()
    inicio = hoy - timedelta(days=24)
    con.execute('''INSERT INTO proyecto_activo (codigo, cliente, nombre, tipo, ton, pct_planchas, piezas_por_t, m2_pint_t,
                   presupuesto, inicio, fecha_comprometida, alpha, estado, es_demo, creado_por)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1,2)''',
                ('OT-DEMO-001', 'Cliente demo', 'Nave de almacenamiento (DEMO)', 'Nave industrial / packing / cobertura',
                 47, 0.17, 8, 14, 150000, str(inicio), str(inicio + timedelta(days=62)), 0.9, 'EN_CURSO'))
    pid = con.execute('SELECT id FROM proyecto_activo WHERE codigo=?', ('OT-DEMO-001',)).fetchone()[0]
    # tareo demo de los primeros procesos
    filas = []
    d = inicio
    plan = [(1, 3, 12), (2, 1, 9), (3, 1, 8), (4, 1, 6), (5, 1, 6), (8, 7, 4)]
    cursor = 0
    for proceso, personas, dias in plan:
        for k in range(dias):
            f = d + timedelta(days=cursor + k)
            if f.weekday() == 6 or f > hoy:
                continue
            filas.append((str(f), pid, proceso, 'T&C FABRICACION' if proceso >= 8 else None, personas, 8.0, 3))
        cursor += max(2, dias // 2)
    con.executemany('''INSERT INTO tareo (fecha, proyecto_id, proceso, contratista, n_personas, horas_persona, registrado_por)
                       VALUES (?,?,?,?,?,?,?)''', filas)
    con.executemany('''INSERT INTO parada (maquina, inicio, fin, planificada, causa, proyecto_id, registrado_por)
                       VALUES (?,?,?,?,?,?,3)''',
                    [('Mesa CNC', f'{inicio + timedelta(days=9)} 08:00', f'{inicio + timedelta(days=9)} 14:00', 0, 'Falla eléctrica', pid),
                     ('Sierra Cinta Kaltenbach', f'{inicio + timedelta(days=15)} 10:00', f'{inicio + timedelta(days=15)} 12:00', 1,
                      'Mantenimiento preventivo', pid)])
    tareas = [('Aprobar planos de fabricación (rev. B)', 'HECHO', 2, 'TAREA', 2, 1),
              ('Comprar perfiles W8x31 faltantes', 'EN_CURSO', 1, 'COMPRA', 2, 2),
              ('Calibrar mesa CNC tras falla eléctrica', 'REVISION', 2, 'BLOQUEO', 3, 5),
              ('Liberar tijerales T-1 a T-4', 'POR_HACER', 3, 'TAREA', 5, 10),
              ('RFI: confirmar espesor de placas base', 'POR_HACER', 2, 'RFI', 2, 1),
              ('Programar granallado con proveedor', 'BACKLOG', 3, 'TAREA', 3, 12),
              ('No conformidad: porosidad en soldadura viga V-3', 'EN_CURSO', 1, 'NO_CONFORMIDAD', 5, 9)]
    for titulo, estado, prio, tipo, resp, proc in tareas:
        con.execute('''INSERT INTO tarea (titulo, proyecto_id, proceso, estado, prioridad, tipo, responsable_id, creado_por,
                       fecha_limite) VALUES (?,?,?,?,?,?,?,?,?)''',
                    (titulo, pid, proc, estado, prio, tipo, resp, 1, str(hoy + timedelta(days=prio * 3))))
    con.execute("INSERT INTO comentario (tarea_id, usuario_id, texto) VALUES (2, 3, 'El proveedor confirma entrega para el jueves.')")
    con.execute("INSERT INTO actividad (usuario_id, tipo, detalle, proyecto_id) VALUES (2, 'proyecto', 'Creó el proyecto OT-DEMO-001 desde una cotización', ?)", (pid,))


if __name__ == '__main__':
    inicializar()
    print('OK', DB, '| credenciales demo en', CREDENCIALES)
