# 03 · Formato único de registro (Componente 1)

Objetivo: que cada proyecto, desde hoy, deje los datos que el modelo necesita, con un formato que comparten cotizaciones y taller. **No es un formato nuevo desde cero**: extiende el control de producción por pieza que la planta ya usa (`OPE-PRO-FR`, hoja `REPORTE_DE_HABILITADO`), que ya registra contratista, O.F., peso y fechas de armado, soldeo y liberación.

Se implementa como un libro Excel con 5 hojas (para importar a la BD con un script) y, en la etapa 2, como formulario web en tablet.

## Hoja 1 · `PROYECTO` (una fila por proyecto, la llena Cotizaciones al adjudicar)

| Campo | Tipo | Regla | Columna BD |
|---|---|---|---|
| codigo_ot | texto | obligatorio, único | `proyecto.n_registro` / código |
| cliente | texto | obligatorio | `proyecto.cliente` |
| nombre | texto | obligatorio | `proyecto.nombre` |
| tipo_estructura | lista | Nave / Planta / Edificación / Mezzanine / Otro | `tipo_estructura_id` |
| toneladas_metrado | número | > 0, del metrado de planos de fabricación | `toneladas` |
| fuente_tonelaje | lista | Estimada (cotización) / Planos / Despacho real | `fuente_tonelaje` |
| n_piezas | entero | del listado de piezas | nueva variable de C2 |
| pct_planchas | % | kg de planchas / kg total | nueva variable de C2 |
| area_pintura_m2 | número | suma de área de piezas | nueva variable de C2 |
| incluye_montaje | sí/no | | nueva variable de C2 |
| presupuesto | número | monto del contrato sin IGV | `presupuesto` |
| moneda | lista | PEN / USD | `moneda` |
| fecha_inicio_contractual | fecha | "día 1" según contrato (planos aprobados + OC) | `fecha_inicio` |
| plazo_ofertado_dias | entero | | `cotizacion.plazo_dias` |
| fecha_fin_contractual | fecha | | `fecha_fin_plan` |
| fecha_fin_real | fecha | al cierre (acta de entrega) | `fecha_fin_real` |
| penalidad_aplicada | número | monto realmente descontado | nuevo |

## Hoja 2 · `TAREO` (una fila por día × proceso × cuadrilla; la llena el jefe de taller o el supervisor del contratista)

Es la fuente de las **HH reales**. Sin esta hoja no hay modelo.

| Campo | Tipo | Regla |
|---|---|---|
| fecha | fecha | día trabajado |
| codigo_ot | lista | proyectos activos |
| proceso | lista | los 13 procesos (catálogo `proceso`) |
| centro / contratista | lista | máquina o nombre del contratista |
| n_personas | entero | ≥ 1 |
| horas_por_persona | número | 0–12 (incluye horas extra) |
| kg_avanzados | número | opcional, del control por pieza |
| observación | texto | paradas, falta de material, retrabajo |

HH del día = n_personas × horas_por_persona. HH reales del proceso = suma de su tareo.

## Hoja 3 · `PROCESO_FECHAS` (una fila por proyecto × proceso)

| Campo | Regla |
|---|---|
| codigo_ot, proceso | |
| fecha_inicio_real | primer día con tareo del proceso |
| fecha_fin_real | último día con tareo del proceso |
| tamaño_cuadrilla_promedio | calculado |

Con esta hoja se miden los **solapes** entre procesos (cuánto avanza el armado antes de que empiece el soldeo), que el CRP necesita.

## Hoja 4 · `PARADAS` (una fila por parada de cualquiera de las 4 máquinas)

| Campo | Regla |
|---|---|
| máquina | Sierra Cinta Kaltenbach / Cizalladora Punzonadora Pedimax / Mesa CNC / Roscadora RIDGID |
| inicio, fin | fecha y hora |
| planificada | sí (mantenimiento preventivo, setup) / no (falla) |
| causa | mecánica, eléctrica, falta de repuesto, falta de operador, falta de material, otro |
| codigo_ot afectado | opcional |

Además, registrar las **horas programadas por máquina y día** (normalmente 8 h, lunes a sábado). Con eso: Dₖ = 1 − horas de parada / horas programadas.

## Hoja 5 · `SERVICIOS_EXTERNOS`

| Campo | Regla |
|---|---|
| codigo_ot, servicio | doblez, granallado/pintura, rolado, plasma |
| proveedor | |
| fecha_envío, fecha_retorno | |
| kg, m² | |

## Validaciones (al importar)

- Ninguna HH diaria por persona > 12 h; ninguna fecha fuera del rango inicio–fin del proyecto.
- Filtro de depuración de C1: descartar o revisar los registros con HH_real / HH_estándar fuera de [0.5, 2.0] (rango inicial, a ajustar con el estudio de tiempos).
- Suma de kg avanzados por proceso ≈ toneladas del metrado (± 5 %).

## Reconstrucción retrospectiva de los 25 proyectos

Para no esperar a proyectos nuevos, llenar las hojas 2 y 3 hacia atrás con:

1. Tareos o partes diarios archivados del contratista y del personal propio.
2. Planillas (personas por semana × horas de jornada).
3. Valorizaciones (kg por semana y por contratista) para repartir HH entre procesos cuando el tareo no distinga proceso.
4. Control por pieza (fechas de armado, soldeo, liberación) para las fechas de inicio y fin por proceso.

Marcar cada registro con su `fuente` y nivel de confianza (directo / reconstruido), y reportarlo en la tesis.

## Ejemplo de proyecto nuevo (entrada del cotizador)

| Campo | Valor |
|---|---|
| tipo_estructura | Planta industrial / minería |
| toneladas_metrado | 47 |
| n_piezas | 420 |
| pct_planchas | 17 % |
| area_pintura_m2 | 1 650 |
| incluye_montaje | no |
| presupuesto | USD 150 000 |
| fecha_inicio_contractual | 2026-11-02 |

Con eso el DSS devuelve HH por proceso (P10–P90), la fecha a cotizar y la penalidad esperada.
