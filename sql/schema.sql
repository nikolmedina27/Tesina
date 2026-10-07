-- Esquema de la BD del DSS de cotización probabilística (Steelser S.A.C.)
-- Motor: SQLite 3 (prototipo). Compatible con PostgreSQL con cambios mínimos
-- (INTEGER PRIMARY KEY -> SERIAL/IDENTITY, TEXT fechas -> DATE/TIMESTAMP).
-- Fechas en ISO-8601 (YYYY-MM-DD / YYYY-MM-DD HH:MM).
PRAGMA foreign_keys = ON;

-- =====================================================================
-- CATÁLOGOS
-- =====================================================================
CREATE TABLE centro_trabajo (
    id              INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE,
    tipo            TEXT NOT NULL CHECK (tipo IN ('MAQUINA','CONTRATISTA','SERVICIO_EXTERNO','INTERNO')),
    horas_turno     REAL DEFAULT 8,          -- horas programadas por turno
    turnos_dia      INTEGER DEFAULT 1,
    cuadrilla_min   INTEGER,                 -- solo CONTRATISTA
    cuadrilla_max   INTEGER,
    activo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE proceso (
    id              INTEGER PRIMARY KEY,
    orden           INTEGER NOT NULL,        -- secuencia típica (1..13)
    nombre          TEXT NOT NULL,
    centro_id       INTEGER REFERENCES centro_trabajo(id),
    UNIQUE (nombre, centro_id)
);

CREATE TABLE tipo_estructura (
    id              INTEGER PRIMARY KEY,
    nombre          TEXT NOT NULL UNIQUE
);

-- =====================================================================
-- CAPA 1 · DATOS HISTÓRICOS (cargados desde extras/ por scripts/build_db.py)
-- =====================================================================
CREATE TABLE proyecto (
    id                  INTEGER PRIMARY KEY,
    n_registro          INTEGER UNIQUE,          -- N° en Tabla 3 de la tesis (1..38)
    codigo_muestra      INTEGER UNIQUE,          -- N° en Proyectos_muestra_25 (1..25) o NULL
    anio                INTEGER,
    cliente             TEXT,
    nombre              TEXT NOT NULL,
    tipo_estructura_id  INTEGER REFERENCES tipo_estructura(id),
    toneladas           REAL,
    fuente_tonelaje     TEXT CHECK (fuente_tonelaje IN ('Estimada','Dato real') OR fuente_tonelaje IS NULL),
    fecha_inicio        TEXT,
    fecha_fin_plan      TEXT,
    fecha_fin_real      TEXT,
    dias_retraso        REAL,                    -- calendario, + = atraso
    dias_retraso_hab    REAL,
    presupuesto         REAL,                    -- monto del contrato (falta recolectar)
    moneda              TEXT,
    en_muestra          INTEGER NOT NULL DEFAULT 0,
    motivo_exclusion    TEXT                     -- por confirmar con la empresa
);

-- Un registro = un proceso de un proyecto (unidad de modelado de C2)
CREATE TABLE proyecto_proceso (
    id                  INTEGER PRIMARY KEY,
    proyecto_id         INTEGER NOT NULL REFERENCES proyecto(id),
    proceso_id          INTEGER NOT NULL REFERENCES proceso(id),
    n_personas          INTEGER,
    dias_plan           REAL,
    dias_retraso_asig   REAL,
    dias_real           REAL,
    hh_ratio_vigente    REAL,     -- = toneladas × ratio (lo que hoy se cotiza)
    hh_real             REAL,     -- OBJETIVO DEL MODELO. Hoy NULL: hay que recolectarlo
    fecha_inicio_real   TEXT,
    fecha_fin_real      TEXT,
    fuente              TEXT,
    UNIQUE (proyecto_id, proceso_id)
);

-- Ratio vigente HH/t por tipo de estructura y proceso (derivado de la muestra)
CREATE TABLE ratio_vigente (
    tipo_estructura_id  INTEGER NOT NULL REFERENCES tipo_estructura(id),
    proceso_id          INTEGER NOT NULL REFERENCES proceso(id),
    hh_por_t            REAL NOT NULL,
    vigente_desde       TEXT,
    PRIMARY KEY (tipo_estructura_id, proceso_id)
);

-- HH reales por OT (hoja CONTROL GENERAL del reporte de avance)
CREATE TABLE ot_hh_real (
    centro_costo    TEXT PRIMARY KEY,
    cliente         TEXT,
    proyecto        TEXT,
    peso_kg         REAL,
    hh_reales       REAL,
    hh_por_t        REAL
);

-- Avance por pieza (reporte de producción OPE-PRO-FR): base del formato único
CREATE TABLE pieza_avance (
    id              INTEGER PRIMARY KEY,
    hoja_origen     TEXT,
    n_item          INTEGER,
    elemento        TEXT,
    conjunto        TEXT,
    perfil          TEXT,
    longitud_mm     REAL,
    cantidad        REAL,
    peso_neto_kg    REAL,
    area_m2         REAL,
    contratista     TEXT,
    orden_fab       TEXT,
    precio_kg       REAL,
    f_inicio        TEXT,
    f_armado        TEXT,
    f_soldeo        TEXT,
    f_liberacion    TEXT,
    f_granallado    TEXT,
    f_pintura       TEXT,
    f_despacho      TEXT
);

-- Cotizaciones emitidas (histórico y nuevas que pasen por el DSS)
CREATE TABLE cotizacion (
    id              INTEGER PRIMARY KEY,
    codigo          TEXT UNIQUE,
    cliente         TEXT,
    descripcion     TEXT,
    fecha           TEXT,
    peso_kg         REAL,
    monto           REAL,
    moneda          TEXT,
    plazo_dias      REAL,          -- plazo ofertado
    plazo_base      TEXT,          -- hito de inicio del plazo
    forma_pago      TEXT,
    validez_dias    INTEGER,
    proyecto_id     INTEGER REFERENCES proyecto(id),   -- si se adjudicó
    origen          TEXT DEFAULT 'MANUAL' CHECK (origen IN ('MANUAL','DSS'))
);

-- Análisis de costo unitario de una cotización
CREATE TABLE acu_linea (
    id              INTEGER PRIMARY KEY,
    cotizacion_id   INTEGER NOT NULL REFERENCES cotizacion(id),
    partida         TEXT,
    unidad          TEXT,
    metrado         REAL,
    peso_kg         REAL,
    costo_unit      REAL,
    costo_total     REAL
);

-- =====================================================================
-- CAPA 1 · REGISTRO OPERATIVO (formato único; se llena desde la implementación)
-- =====================================================================
-- Tareo diario: fuente de las HH reales por proceso
CREATE TABLE tareo (
    id              INTEGER PRIMARY KEY,
    fecha           TEXT NOT NULL,
    proyecto_id     INTEGER NOT NULL REFERENCES proyecto(id),
    proceso_id      INTEGER NOT NULL REFERENCES proceso(id),
    centro_id       INTEGER REFERENCES centro_trabajo(id),
    contratista     TEXT,
    n_personas      INTEGER NOT NULL,
    horas_persona   REAL NOT NULL,           -- horas trabajadas por persona ese día
    hh              REAL GENERATED ALWAYS AS (n_personas * horas_persona) STORED,
    kg_avanzados    REAL,
    observacion     TEXT
);

-- Paradas de máquina: base de la disponibilidad D_k (TPM)
CREATE TABLE parada_maquina (
    id              INTEGER PRIMARY KEY,
    centro_id       INTEGER NOT NULL REFERENCES centro_trabajo(id),
    inicio          TEXT NOT NULL,
    fin             TEXT NOT NULL,
    planificada     INTEGER NOT NULL CHECK (planificada IN (0,1)),
    causa           TEXT,                    -- falla mecánica, eléctrica, falta repuesto, setup...
    proyecto_id     INTEGER REFERENCES proyecto(id)
);

-- Tiempo programado por máquina y día (denominador de D_k)
CREATE TABLE calendario_planta (
    fecha           TEXT NOT NULL,
    centro_id       INTEGER NOT NULL REFERENCES centro_trabajo(id),
    horas_programadas REAL NOT NULL,
    laborable       INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (fecha, centro_id)
);

-- Estudio de tiempos (C1): TS = TO × FR × (1 + S)
CREATE TABLE estudio_tiempos (
    id              INTEGER PRIMARY KEY,
    proceso_id      INTEGER NOT NULL REFERENCES proceso(id),
    fecha           TEXT NOT NULL,
    unidad          TEXT NOT NULL,           -- 'h/t', 'h/pieza', 'h/m2', 'h/m soldadura'
    n_ciclos        INTEGER,
    to_promedio     REAL NOT NULL,
    factor_ritmo    REAL NOT NULL,
    suplemento      REAL NOT NULL,
    ts              REAL GENERATED ALWAYS AS (to_promedio * factor_ritmo * (1 + suplemento)) STORED
);

-- Plazos de servicios externos (doblez, granallado/pintura)
CREATE TABLE servicio_externo_plazo (
    id              INTEGER PRIMARY KEY,
    centro_id       INTEGER NOT NULL REFERENCES centro_trabajo(id),
    proyecto_id     INTEGER REFERENCES proyecto(id),
    proveedor       TEXT,
    fecha_envio     TEXT,
    fecha_retorno   TEXT,
    kg              REAL,
    m2              REAL
);

-- =====================================================================
-- CAPA 2-4 · MODELO, SIMULACIÓN Y LAZO DE CONTROL
-- =====================================================================
CREATE TABLE parametro (
    clave           TEXT PRIMARY KEY,
    valor           REAL NOT NULL,
    descripcion     TEXT
);

CREATE TABLE modelo_version (
    id              INTEGER PRIMARY KEY,
    fecha_entreno   TEXT NOT NULL,
    algoritmo       TEXT NOT NULL,           -- 'QRF', 'RF', 'RLM', 'RATIO'
    n_proyectos     INTEGER,
    n_registros     INTEGER,
    mae_lopo        REAL,                    -- error de validación leave-one-project-out
    mape_lopo       REAL,
    picp_lopo       REAL,
    hiperparametros TEXT,                    -- JSON
    ruta_artefacto  TEXT,
    activo          INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE prediccion (
    id              INTEGER PRIMARY KEY,
    modelo_id       INTEGER NOT NULL REFERENCES modelo_version(id),
    cotizacion_id   INTEGER REFERENCES cotizacion(id),
    proyecto_id     INTEGER REFERENCES proyecto(id),
    proceso_id      INTEGER NOT NULL REFERENCES proceso(id),
    hh_ratio        REAL,
    p10 REAL, p50 REAL, p80 REAL, p90 REAL,
    fecha           TEXT NOT NULL
);

CREATE TABLE simulacion (
    id                  INTEGER PRIMARY KEY,
    cotizacion_id       INTEGER NOT NULL REFERENCES cotizacion(id),
    fecha               TEXT NOT NULL,
    replicas            INTEGER NOT NULL,
    alpha               REAL NOT NULL,
    fecha_inicio        TEXT NOT NULL,
    fecha_cotizada      TEXT NOT NULL,       -- cuantil alpha de C_n
    fecha_p50           TEXT,
    fecha_p90           TEXT,
    prob_cumplimiento   REAL,
    penalidad_esperada  REAL,
    semaforo            TEXT CHECK (semaforo IN ('VERDE','AMBAR','ROJO')),
    semilla             INTEGER
);

CREATE TABLE alerta_reentreno (
    id              INTEGER PRIMARY KEY,
    fecha           TEXT NOT NULL,
    modelo_id       INTEGER REFERENCES modelo_version(id),
    md              REAL,
    picp            REAL,
    proyectos_nuevos INTEGER,
    motivo          TEXT,
    atendida        INTEGER NOT NULL DEFAULT 0
);

-- =====================================================================
-- VISTAS
-- =====================================================================
CREATE VIEW v_otd AS
SELECT anio,
       COUNT(*)                                   AS proyectos,
       SUM(dias_retraso <= 0)                     AS cumplen,
       ROUND(100.0 * SUM(dias_retraso <= 0) / COUNT(*), 1) AS otd_pct,
       ROUND(AVG(MAX(dias_retraso, 0)), 2)        AS retraso_prom
FROM proyecto GROUP BY anio;

CREATE VIEW v_hh_por_tipo AS
SELECT t.nombre AS tipo_estructura, COUNT(*) AS proyectos,
       ROUND(SUM(x.hh_ratio) / SUM(p.toneladas), 2) AS hh_t_ratio,
       ROUND(SUM(x.hh_real) / SUM(CASE WHEN x.hh_real IS NOT NULL THEN p.toneladas END), 2) AS hh_t_real
FROM proyecto p
JOIN tipo_estructura t ON t.id = p.tipo_estructura_id
JOIN (SELECT proyecto_id, SUM(hh_ratio_vigente) AS hh_ratio, SUM(hh_real) AS hh_real
      FROM proyecto_proceso GROUP BY proyecto_id) x ON x.proyecto_id = p.id
GROUP BY t.nombre;

CREATE VIEW v_disponibilidad AS
SELECT c.nombre AS maquina,
       SUM(cp.horas_programadas) AS horas_programadas,
       COALESCE((SELECT SUM((julianday(pm.fin) - julianday(pm.inicio)) * 24)
                 FROM parada_maquina pm WHERE pm.centro_id = c.id), 0) AS horas_parada,
       ROUND(1 - COALESCE((SELECT SUM((julianday(pm.fin) - julianday(pm.inicio)) * 24)
                 FROM parada_maquina pm WHERE pm.centro_id = c.id), 0)
             / NULLIF(SUM(cp.horas_programadas), 0), 4) AS d_k
FROM centro_trabajo c
JOIN calendario_planta cp ON cp.centro_id = c.id
WHERE c.tipo = 'MAQUINA'
GROUP BY c.id;
