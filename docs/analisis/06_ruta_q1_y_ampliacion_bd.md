# 06 · Ruta a Q1 y qué agregar a la BD (a partir de los 27 papers)

Complementa [03_potencial_q1.md](03_potencial_q1.md) con lo que mostró la literatura de `papers/` ([05](05_literatura_papers.md)) y los resultados del banco de pruebas ([04](04_resultados_banco_pruebas.md)).

## 1. Qué cambia respecto de lo que ya sabíamos

| Hallazgo de la literatura | Consecuencia para el trabajo |
|---|---|
| Rokoss (planificación 5.87 vs ML 5.56 días) y Roblek (el plan humano gana) coinciden con nuestro banco de pruebas: **el experto es difícil de superar** | No vender "el DSS acierta mejor que el cotizador". Vender "el DSS **audita** el plan del cotizador, le pone probabilidad y propone el plazo con criterio económico" |
| El ML mejora mucho con **variables de dominio** (WIP, cuellos de botella) y con **lo que estimó el planificador** | Guardar y usar el estado del taller y **la estimación del cotizador por proceso** |
| Hay antecedente probabilístico: Bekci et al. 2022 (cotizar con intervalos, corte láser) | Diferenciarse: proyectos multi-proceso + capacidad + penalidad + calibración con N pequeño |
| Hay antecedente de fecha confiable con capacidad: Mundt & Lödding 2025 (colchón fijo) y Keskinocak & Tayur | Compararse contra ellos (colchón fijo y regla P50 + colchón) |
| Disponibilidad real 69–78 % (Hollerweger) | Mi simulación asumió ≈ 90 %: hacer **sensibilidad con Dₖ entre 0.70 y 0.90** |
| Ninguno de los 27 reporta cobertura de intervalos salvo May | La **calibración** (PICP, Brier) es un diferenciador fácil de defender |

## 2. Qué sugiero para llegar a Q1

**Mensaje del paper** (propuesto): *un marco para cotizar fechas de entrega en pymes de fabricación bajo pedido que entrega la fecha con su probabilidad, la calibra con pocos proyectos y elige el plazo con criterio económico, y que se evalúa contra el criterio del planificador.*

### A. Datos (lo que bloquea todo)
1. HH reales por proceso de los 25 proyectos (ver [plan/01](../plan/01_datos_a_recolectar.md)).
2. **Lo que estimó el cotizador** por proceso y su fecha cotizada, guardado antes de ejecutar (línea base justa y variable de entrada).
3. Las variables nuevas de la sección 3 (WIP, carga, fecha pedida, compras, cambios).
4. Las **cotizaciones perdidas** con plazo y precio, para el costo de plazo largo c_o.
5. Ampliar la muestra: los 13 proyectos excluidos y proyectos nuevos. Con 25, el IC del cumplimiento es de ±16 puntos.

### B. Método
1. **Competidores de C2**: agregar a la comparación gradient boosting cuantílico (LightGBM) y NGBoost, que es lo que usa Bekci, junto con QRF, regresión lineal y RF. Si QRF no gana, se reporta y se discute.
2. **Competidores de C3**: (a) fecha con colchón fijo a la Mundt (P50 + colchón de 1 día), (b) suma de P80 por proceso, (c) criterio del cotizador, (d) nuestro Monte Carlo.
3. **Estimación del cotizador como variable** de C2 (igual que los "tiempos planificados" de Rokoss): el modelo corrige al experto en vez de reemplazarlo.
4. **Conformal agrupado por proyecto** con garantía de cobertura, con una prueba de cobertura empírica sobre las 4 variantes del simulador y los datos reales.
5. **α\* con c_o estimado** de las cotizaciones ganadas y perdidas; si no hay datos, reportar la frontera completa y la sensibilidad a c_o.
6. **Ablaciones**: sin Dₖ, sin carga del taller, sin correlación entre procesos (ρ = 0), sin conformal.
7. **Sesgo**: reportar tendencia a subestimar (pedido por Hajj Chehade), no solo MAE.

### C. Evidencia
1. **Backtest causal** con datos reales (ya implementado sobre simulados).
2. **Piloto en paralelo** (*shadow mode*) con 3–6 cotizaciones nuevas.
3. **Sensibilidad** a κ (carga del taller), Dₖ (0.70–0.90), σ de plazos externos, ρ y c_o.
4. **Reproducibilidad**: código y BD anonimizada.

### D. Posicionamiento y revistas
Revisión sistemática en Scopus/WoS de *due-date quotation*, *lead-time quotation*, *probabilistic lead time* y *conformal prediction* en manufactura **antes** de afirmar novedad. Citar a Keskinocak & Tayur y a Bekci et al.

Revistas que ya publican temas vecinos (verificar cuartil en SJR): *Production Planning & Control* (Mundt & Lödding), *International Journal of Production Research*, *Journal of Intelligent Manufacturing* (Rokoss, May), *Engineering Applications of AI* (Hajj Chehade), *International Journal of Production Economics*, *Computers & Industrial Engineering*.

**Veredicto**: el aporte es **integrador** (no revoluciona ninguna pieza), así que su fuerza depende de la evidencia: datos reales, comparación con el cotizador y calibración. Con eso, una revista Q2 es realista; Q1 es posible si el piloto o el backtest real muestra un beneficio económico claro y la comparación con Bekci y Mundt es favorable.

## 3. Qué agregar a la BD

Prioridad: **P0** bloquea el modelo o la línea base, **P1** mejora mucho C2 o C3, **P2** deseable. El origen de cada idea está entre paréntesis. Los DDL son propuestas (no se aplicaron a `sql/schema.sql` todavía).

### P0 · Línea base justa y decisión

| Tabla / campo | Para qué | De dónde sale |
|---|---|---|
| `cotizacion_estimacion_proceso` (cotización, proceso, HH estimadas por el cotizador, días estimados, cuadrilla supuesta, quién y cuándo) | La estimación del experto como **línea base** y variable de entrada | Rokoss: los tiempos planificados bajan el error de 7.73 a 5.56; Roblek |
| `cotizacion.fecha_pedida_cliente`, `.fecha_cotizada`, `.resultado` (ganada, perdida, retirada), `.plazo_competidor`, `.precio_competidor`, `.motivo_perdida` | Costo de plazo largo c_o y α\* | Mundt (aceptación de ofertas), Rokoss (fecha deseada es la variable más influyente) |
| `proyecto_proceso.hh_real` (ya existe, **vacía**) y `fuente` (directo, reconstruido) | Variable objetivo | Wei, Hajj Chehade |
| `proyecto.presupuesto`, `.penalidad_aplicada`, `.ampliacion_plazo_dias` | Penalidad real en soles; definir OTD sobre la fecha contractual vigente | Contrato de la cotización ST087 |

### P1 · Estado de la planta y variables del plano

| Tabla / campo | Para qué | De dónde sale |
|---|---|---|
| `estado_planta_dia` (fecha, proyectos en curso, HH pendientes por centro, utilización por máquina, cola en cada máquina) | WIP y cuellos de botella al momento de cotizar; reemplaza el modelo simplificado de carga | Rokoss y Aslan (estado de planta como variable); Woschank |
| `proyecto_feature` ampliada: metros de soldadura, n° de soldaduras, factor de dificultad, factor de superficie (m²/t), n° de perforaciones, perfiles pesados vs livianos, material y espesor, tolerancias, tipo de unión | Mejores variables de C2 | Çakıt (soldaduras, piezas, superficie, dificultad), Urban (geometría, material, tolerancias vía CAD-ERP), Wei (one-hot de tipos) |
| `cotizacion.descripcion_alcance` (texto) y `.familia_producto` | Texto no estructurado y agrupación de familias con pocos datos | Hajj Chehade |
| `compra_material` (OC, proveedor, perfil, fecha de pedido, fecha de recepción, kg) | El proceso 2 (compra) es de los de mayor varianza de plazo | Liang (llegada de materiales); proceso 2 de la muestra |
| `evento_proyecto` (tipo: cambio de alcance, revisión de planos, retraso de información del cliente, suspensión; fecha; días de impacto) | Separar el atraso por causas del cliente del atraso de planta; la propuesta técnica permite ampliar el plazo por esas causas | Cláusulas de la cotización ST087 |

### P1 · Disponibilidad y paradas (C3)

| Tabla / campo | Para qué | De dónde sale |
|---|---|---|
| `parada_maquina.causa` con catálogo (correctivo, falta de repuesto, lubricación, cambio de herramienta, falta de operador, falta de material) | Tipificar causas y mejorar el modelo de fallas | Hollerweger |
| `setup_maquina` (máquina, proyecto, tiempo de preparación) | Los tiempos de preparación crecieron y fueron cuello de botella oculto | Hollerweger |
| `oee_dia` (disponibilidad, rendimiento, calidad por máquina) | Seguir OEE y no solo disponibilidad | Hollerweger, Wolska, Bianchini |
| Registrar ≥ 12–24 meses de paradas | Estimar Dₖ con estacionalidad; Hollerweger encontró disponibilidad que cayó de 77.8 % a 68.9 % en un año | Hollerweger |

### P2 · Calidad y control

| Tabla / campo | Para qué | De dónde sale |
|---|---|---|
| `no_conformidad` y `retrabajo` (proyecto, proceso, horas, causa), `inspeccion_ensayo` (UT, tintes, fecha) | Los retrabajos y ensayos agregan tiempo que hoy se atribuye a φ | Propuesta ST087 (UT, tintes, plan de calidad) |
| `kpi_semana` (utilización, saturación, eficiencia de ciclo) | Tablero de seguimiento | Bianchini |
| `recurso_conductor` (marcar las 4 máquinas y los contratistas como recursos "conductores") | Capacidad con ratios para el resto | Anand |
| `actualizacion_parametros` (fecha, qué parámetro, valor anterior y nuevo) | Frecuencia de actualización de datos del taller | Woschank, Ki |

### DDL propuesto (extracto de P0 y P1)

```sql
CREATE TABLE cotizacion_estimacion_proceso (
    cotizacion_id   INTEGER NOT NULL REFERENCES cotizacion(id),
    proceso_id      INTEGER NOT NULL REFERENCES proceso(id),
    hh_estimadas    REAL,
    dias_estimados  REAL,
    cuadrilla       INTEGER,
    estimado_por    TEXT,
    fecha_estimacion TEXT,
    PRIMARY KEY (cotizacion_id, proceso_id)
);
ALTER TABLE cotizacion ADD COLUMN fecha_pedida_cliente TEXT;
ALTER TABLE cotizacion ADD COLUMN fecha_cotizada TEXT;
ALTER TABLE cotizacion ADD COLUMN resultado TEXT CHECK (resultado IN ('GANADA','PERDIDA','RETIRADA','PENDIENTE'));
ALTER TABLE cotizacion ADD COLUMN plazo_competidor_dias REAL;
ALTER TABLE cotizacion ADD COLUMN motivo_perdida TEXT;

CREATE TABLE estado_planta_dia (
    fecha           TEXT NOT NULL,
    centro_id       INTEGER NOT NULL REFERENCES centro_trabajo(id),
    proyectos_en_curso INTEGER,
    hh_pendientes   REAL,
    utilizacion     REAL,
    cola_horas      REAL,
    PRIMARY KEY (fecha, centro_id)
);

CREATE TABLE compra_material (
    id              INTEGER PRIMARY KEY,
    proyecto_id     INTEGER REFERENCES proyecto(id),
    proveedor       TEXT,
    perfil          TEXT,
    kg              REAL,
    fecha_pedido    TEXT,
    fecha_recepcion TEXT
);

CREATE TABLE evento_proyecto (
    id              INTEGER PRIMARY KEY,
    proyecto_id     INTEGER NOT NULL REFERENCES proyecto(id),
    tipo            TEXT NOT NULL CHECK (tipo IN ('CAMBIO_ALCANCE','REVISION_PLANOS','INFO_CLIENTE','SUSPENSION','OTRO')),
    fecha           TEXT,
    dias_impacto    REAL,
    imputable_cliente INTEGER CHECK (imputable_cliente IN (0,1)),
    descripcion     TEXT
);
```

## 4. Orden sugerido

1. Reunión con la empresa con el checklist de [plan/01](../plan/01_datos_a_recolectar.md) **más** la estimación del cotizador, las cotizaciones perdidas y las compras de material.
2. Aplicar a `sql/schema.sql` las tablas P0 y P1 que acepte la empresa y extender `scripts/build_db.py`.
3. Reconstruir HH reales y repetir los tres experimentos con datos reales.
4. Agregar los competidores (LightGBM cuantílico, NGBoost, colchón fijo) a `exp1` y `exp3`.
5. Revisión sistemática de literatura y corrección de los errores de la tesis ([05 §6](05_literatura_papers.md)).
