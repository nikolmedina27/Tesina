# 01 · Inventario de datos disponibles

Qué hay en cada archivo de `extras/`, qué sirve para el modelo y dónde quedó en la BD (`data/steelser.db`).

## Resumen

| Archivo | Qué contiene | ¿Sirve? | Tabla SQLite |
|---|---|---|---|
| `Tesis_TF1_Steelser.docx` | Tesis TF1. **Tabla 3**: registro de 38 proyectos 2019–2026 con fecha inicio, fin plan, fin real y días de retraso | **Sí**: única fuente de fechas reales a nivel proyecto (línea base OTD) | `proyecto` (n_registro 1–38) |
| `Proyectos_muestra_25 Dep.xlsx` | 25 proyectos × 13 procesos = 325 filas: tipo de estructura, toneladas, n° personas, días plan/reales, HH estimadas | **Parcial**: da la estructura de procesos y el **ratio vigente**, pero **no** tiene HH reales (ver [02](02_diagnostico_calidad_datos.md)) | `proyecto` (codigo_muestra), `proyecto_proceso`, `ratio_vigente` |
| `REPORTE DE AVANCE _PROYECTOS - copia.xlsx` (16 MB, 27 hojas) | Plantillas del control de producción por pieza (OPE-PRO-FR), valorizaciones a contratistas, curvas S, reportes fotográficos | **Sí, como formato**: es la base del "formato único". Datos útiles en 3 hojas (abajo) | `ot_hh_real`, `pieza_avance` |
| `Ejemplo data de un proyecto.xlsx` | ACU (análisis de costo unitario) de la cotización ST087 — inductores de flujo, 3 234 kg | **Sí**: muestra cómo cotiza hoy el área comercial (todo por kg) | `acu_linea` |
| `Cotizacion_ST087_BYPS_Inductores.pdf` | Propuesta técnico-económica ST087 Rv2: USD 13 451.14 + IGV, **13 días**, lunes a sábado, turno diurno | **Sí**: caso real para probar el prototipo | `cotizacion` |

## Detalle por fuente

### Proyectos_muestra_25 Dep.xlsx — hoja `Data por proyecto`

Columnas: código muestra, año, cliente, proyecto, tipo de estructura, toneladas, fuente tonelaje, retraso (calendario / hábiles), n° proceso, proceso, máquina/recurso, n° personas, días planificados, días de retraso asignados, días reales, HH estimadas.

- 4 tipos de estructura: Nave industrial/packing/cobertura (12), Planta industrial/minería (5), Edificación/infraestructura (5), Mezzanine/plataformas/oficinas (3).
- Toneladas entre 39 y 200 t (media 93 t). **22 de 25 son "Estimada"**, solo 3 (2026) son "Dato real".
- 13 procesos fijos por proyecto, en este orden:

| # | Proceso | Centro de trabajo | Tipo de centro |
|---|---|---|---|
| 1 | Ingeniería | Oficina técnica | Interno |
| 2 | Compra de material | Compras | Interno |
| 3 | Habilitado de perfiles | Sierra Cinta Kaltenbach | **Máquina** |
| 4 | Habilitado de perfiles | Cizalladora Punzonadora Pedimax | **Máquina** |
| 5 | Habilitado de planchas | Mesa CNC | **Máquina** |
| 6 | Roscado de barra lisa | Roscadora RIDGID | **Máquina** |
| 7 | Doblez de plancha | Servicio externo | Externo |
| 8 | Armado de estructuras | Contratista | Contratista |
| 9 | Soldeo de estructuras | Contratista | Contratista |
| 10 | Limpieza de estructuras | Contratista | Contratista |
| 11 | Despacho a cámara de pintura | Planta | Interno |
| 12 | Preparación superficial (granallado/pintura) | Servicio externo | Externo |
| 13 | Despacho a obra | Despacho | Interno |

Las **4 máquinas** del modelo de disponibilidad (Dₖ) son las de los procesos 3–6.

### REPORTE DE AVANCE — hojas útiles

| Hoja | Contenido útil |
|---|---|
| `CONTROL GENERAL` | **Únicas HH reales** del material: 4 OT pequeñas (0.5–7.1 t) con HH/t reales de 29, 43, 64 y 121 |
| `REPORTE_DE_HABILITADO` | 48 piezas (48.4 t, perfiles soldados PL12) con contratista, O.F., P.U. por kg y **fechas reales por proceso** (inicio, armado, soldeo, liberación). 5 cuadrillas fabricaron 48 t en ~9 días |
| `REPORTE_DE_AVANCE ZONA 2` | 29 piezas con perfil, longitud, peso y área (sin fechas) — útil para derivar variables del plano (n° piezas, peso medio, m² de pintura) |
| `Hval`, `LOLIN`, `Datos_No tocar` | Estructura de columnas del control (sirve para diseñar el formato único), datos vacíos o con `#REF!` |
| `P.U`, `P.UNI`, `CONTRATOS` | Precios unitarios por kg pagados al contratista por tipo de elemento (0.5–2.5 S/ por kg) |
| Resto (curvas S, reporte fotográfico, informes) | No aportan al modelo |

> Muchas hojas tienen `#REF!`: fórmulas rotas por copiar hojas entre libros. El ETL solo toma valores numéricos válidos.

**Implicancia clave**: al contratista se le paga **por kg**, no por hora. Por eso la empresa no registra HH reales de armado/soldeo/limpieza (que son ~80 % de las HH). Las HH reales deben salir del **tareo** (personas × horas por día), no de las valorizaciones.

### ACU de la cotización ST087

Costo directo USD 9 263.69 + GG 25 % + utilidad 16 % = USD 13 061.81 (la oferta final Rv2 es USD 13 451.14). La mano de obra de fabricación se cotiza como **0.647 USD/kg × 3 234 kg**; el plazo (13 días) no sale de ningún cálculo de capacidad. Es exactamente el caso que el DSS debe resolver.

Ejemplo ilustrativo de la brecha: con el ratio vigente de "Planta industrial" (36.8 HH/t) el inductor requeriría ≈ 119 HH; la única OT real del mismo cliente (barcaza B&PS, 3.5 t) consumió **120.8 HH/t**, lo que daría ≈ 391 HH, 3.3 veces más. Son piezas pequeñas y especiales (no comparables con naves de 100 t), pero muestran por qué un ratio fijo por tonelada falla.

## Cómo consultar

```bash
python scripts/build_db.py
```

```sql
SELECT * FROM v_otd;                -- OTD por año (38 proyectos)
SELECT * FROM v_hh_por_tipo;        -- HH/t del ratio vigente vs real (real = NULL hasta recolectar)
SELECT * FROM ot_hh_real;           -- 4 OT con HH reales
```
