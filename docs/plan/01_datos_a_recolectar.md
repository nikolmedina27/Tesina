# 01 · Datos que faltan y cómo conseguirlos

Ordenados por prioridad. **P0 bloquea el modelo**: sin esos datos no hay tesis defendible ni paper.

## P0 · Imprescindibles

| # | Dato | Para qué | Fuente en Steelser | Cantidad mínima | Tabla BD |
|---|---|---|---|---|---|
| 1 | **HH reales por proyecto × proceso** | Variable objetivo de C2 (φ), Io, Md, PICP | Tareos o partes diarios, planillas de personal propio, partes del contratista (personas × días × horas). Las valorizaciones solo dan kg, no horas | Los 25 proyectos de la muestra (ideal: los 38) | `tareo` → `proyecto_proceso.hh_real` |
| 2 | **Fechas reales de inicio y fin por proceso** | Solapes y duración por proceso en el CRP; backtest | Control por pieza (fechas de armado, soldeo, liberación), guías de despacho, actas | Los mismos proyectos | `proyecto_proceso.fecha_*_real` |
| 3 | **Toneladas reales** (22 de 25 son estimadas) | Variable principal de C2 | Metrado de planos de fabricación, listas de piezas (Tekla), guías de despacho con peso | Todos | `proyecto.toneladas`, `fuente_tonelaje` |
| 4 | **Presupuesto del contrato** | Penalidad en soles (Ec. 13) y α\* | Contratos u órdenes de compra | Todos | `proyecto.presupuesto` |
| 5 | **Motivo de exclusión** de los 13 proyectos fuera de la muestra | Defender la muestra ante el jurado/revisor | Gerencia / jefe de proyectos | 13 | `proyecto.motivo_exclusion` |

**Si los tareos no distinguen proceso**: repartir las HH semanales de cada cuadrilla entre armado, soldeo y limpieza en proporción a los kg avanzados por proceso esa semana (del control por pieza). Declarar el método en la tesis y marcar la fuente como "reconstruido".

**Si para algún proyecto no hay ningún registro de horas**: excluirlo de C2 (pero mantenerlo en la línea base de OTD). Es preferible 18 proyectos reales que 25 sintéticos.

## P1 · Necesarios para el CRP (C3)

| # | Dato | Para qué | Fuente | Cantidad mínima |
|---|---|---|---|---|
| 6 | Paradas de las 4 máquinas (inicio, fin, causa, planificada) | Dₖ y su distribución diaria | Bitácora de mantenimiento, órdenes de trabajo de mantenimiento, reportes del jefe de taller. Si no existe, **empezar a registrar ya** | ≥ 3 meses (ideal 6–12) | `parada_maquina` |
| 7 | Horas programadas por máquina y día (turnos, feriados) | Denominador de Dₖ | Jefe de taller | Mismo periodo | `calendario_planta` |
| 8 | Proyectos simultáneos (WIP) en cada fecha | Carga del taller en el backtest | Cronogramas y Tabla 3 (fechas de inicio y fin) | Todos | derivado de `proyecto` |
| 9 | Plazos de servicios externos (doblez, granallado/pintura, rolado, plasma) por proveedor | Distribución de L_s | Órdenes de servicio, guías de envío y retorno | ≥ 15 envíos por servicio | `servicio_externo_plazo` |
| 10 | Rango de cuadrilla por contratista (mín./máx. personas) | Capacidad de contratista (Ec. 11) | Contratos y tareos | 5–8 contratistas | `centro_trabajo` |

## P2 · Variables del plano (mejoran C2)

Del listado de piezas de cada proyecto (como `REPORTE_DE_AVANCE ZONA 2`): **n° de piezas, peso medio por pieza, % de planchas, m² de pintura**, metros y tipo de soldadura (filete vs. penetración completa), n° de conexiones, perfiles pesados vs. livianos (la planta ya clasifica Liviana 0–250 kg, Mediana 251–1 000 kg, Pesada > 1 000 kg), acabado (sistema de pintura, mils), montaje sí/no, contratista asignado.

## P3 · Datos comerciales (para α\* y competitividad)

| # | Dato | Para qué |
|---|---|---|
| 11 | **Todas las cotizaciones emitidas**, ganadas y **perdidas**, con plazo ofertado, precio y, si se sabe, plazo/precio del ganador | Estimar cómo baja la probabilidad de ganar por cada día extra de plazo → c_o y α\* (Ec. 16). Es el dato que convierte "fecha competitiva" en número |
| 12 | Penalidades realmente aplicadas y ampliaciones de plazo concedidas | Validar el supuesto de 1 %/día sin tope |
| 13 | Tiempo entre recepción de planos y envío de la cotización | Línea base de QLT |

## P4 · Estudio de tiempos (C1, durante la implementación)

Cronometraje en planta de los procesos de mayor HH: **armado, soldeo, limpieza** (≈ 80 % de las HH según el ratio) y habilitado en las 4 máquinas.

- N° de ciclos por elemento: según la tabla de Westinghouse o el método estadístico (error ±5 %, confianza 95 %).
- Factor de ritmo con escala de Westinghouse; suplementos según la OIT.
- Unidad por proceso: h/t (armado, soldeo), h/pieza (habilitado), h/m² (limpieza, pintura), h/m (soldadura si se mide por cordón).
- Registrar en `estudio_tiempos`.

## Checklist para la reunión con la empresa

- [ ] Acceso a tareos/partes diarios 2021–2026 (personal propio y contratistas)
- [ ] Planillas (n° de personas por semana)
- [ ] Listas de piezas o modelos Tekla de los 25 proyectos
- [ ] Contratos/OC con monto y plazo
- [ ] Bitácora de mantenimiento de las 4 máquinas
- [ ] Órdenes de servicio de granallado/pintura y doblez
- [ ] Registro de cotizaciones 2023–2026 (ganadas y perdidas)
- [ ] Firma de la autorización de uso de información (anexo de la tesis) que cubra todo lo anterior
- [ ] Acordar el inicio del registro diario de tareo y paradas con el formato único
