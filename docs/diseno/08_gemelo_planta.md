# 08 · Gemelo de la planta (simulación de eventos discretos)

> **Todo es SIMULADO.** El gemelo reproduce la historia 2019–2026 de Steelser con datos inventados pero realistas, calibrados a las fechas reales de la Tabla 3. Sirve para evaluar el DSS contra una «verdad» que **no sale del mismo motor que el DSS**, y para animar la planta en 3D. Cuando lleguen los tareos reales, cada tabla simulada se reemplaza por su equivalente real (sección 6).

## Por qué existe

El DSS planifica por **día y por proceso** (`dss/crp_engine.py`). Si la «verdad» con la que se evalúa sale de ese mismo motor, un revisor lo rechaza por circular (el DSS ve el mundo con los mismos supuestos con que se construyó). El gemelo trabaja por **hora y por lote de piezas**, con recursos que tienen calendario propio, cuadrillas con ausentismo, fallas de máquina, proveedores, RFIs y retrabajos. Aparecen diferencias reales entre el modelo de planificación y la planta, que es justo lo que hay que medir.

## Flujo de un lote (`dss/gemelo/motor.py`)

```
paquete de ingeniería liberado (RFIs del cliente lo atrasan)
  → compra y llegada del material (proveedor)
  → habilitado en las máquinas que necesite, en paralelo: sierra cinta · cizalla-punzonadora · mesa CNC · roscadora
  → puente grúa A al buffer → [doblez externo: envío los martes, plazo del servicio] → puente grúa B a una mesa
  → armado (mesa + 2 armadores del contratista) → grúa B → soldeo (puesto + 1 soldador)
  → limpieza e inspección (zona + 1 ayudante) → si hay no conformidad: retrabajo de soldeo y nueva inspección
  → grúa B al patio de salida → camión a granallado y pintura (≥ 12 t o el sábado) → vuelve pintado
  → camión a obra (hasta 25 t). El proyecto termina con el último camión.
```

## Recursos y calendarios

| Recurso | Cantidad | Calendario / regla |
|---|---|---|
| Sierra cinta, cizalla-punzonadora, mesa CNC, roscadora | 4 | Turno 07–15, lunes a sábado sin feriados peruanos (incl. Semana Santa); fallas (Weibull, MTBF 60–220 h de trabajo) y mantenimiento preventivo cada 160 h; reparación lognormal |
| Puentes grúa A y B | 2 (10 t) | 06–23; cada traslado ocupa la grúa; los lotes esperan en cola |
| Mesas de armado / puestos de soldeo / cupos de limpieza | 6 / 8 / 8 | Cada estación atiende un lote a la vez |
| Cuadrillas por proyecto y proceso (armado, soldeo, limpieza) | del tareo/plan de cada proyecto | Ausentismo diario (8 % por persona); tope = plantilla del contratista (10–16) |
| Camiones de pintura, doblez y obra | muelles propios | Plazos de proveedor aleatorios; 12 % de demoras largas |

Cola de cada recurso: fecha comprometida del proyecto (EDD), luego orden del lote. **Números aleatorios comunes**: todo el azar (HH por lote, plazos, ausentismo, fallas) se sortea por entidad, así que al comparar políticas el mismo lote tiene el mismo tiempo de soldeo y la misma máquina falla el mismo día; solo cambia lo que las decisiones cambian.

## Datos que genera (`dss/gemelo/generador.py`)

| Qué | Cómo |
|---|---|
| 38 proyectos y 9 162 lotes | Real: lista, tipo, fechas de inicio y fin planificado, toneladas de la muestra y cuadrillas. Simulado: lotes por proyecto (≈ toneladas / 330–420 kg), kg y piezas por lote, perfil y elemento (columna, viga, tijeral, correa, placa…), qué lotes pasan por doblez (7 %) y cuáles tienen no conformidad (≈ 6 % × calidad del contratista) |
| HH por proceso y lote | Modelo oculto de φ: sesgo por proceso, piezas por tonelada (armado y soldeo), planchas (CNC y sierra), habilidad del contratista, aprendizaje (−2 %/año), escala del proyecto, umbral no lineal, efecto del proyecto (ρ ≈ 0.3) y ruido. **El QRF nunca lo ve**: aprende del tareo que registra el gemelo |
| Proveedores, RFIs y cambios de alcance | Plazo de compra lognormal por paquete (mediana 6 días laborables, 18 % con demoras de 4 a 14 días); 0–2 RFIs por proyecto; 0–1 cambios de alcance que agregan lotes |
| Paradas de máquina | Weibull (forma 1.3), reparación lognormal, causas del catálogo, mantenimiento preventivo |
| Personal | 100 personas anónimas: 5 contratistas (10–16 c/u), operadores, gruistas, supervisores, proyectistas, compradores, despachadores |

## Calibración al historial real (`dss/gemelo/calibrar.py`)

Un **factor de ritmo por proyecto** escala las duraciones (y, con su raíz, los plazos de proveedores) hasta que, con la política «como se hizo», cada proyecto termine en su fecha real: si se atrasó, en su fecha real; si cumplió, en su fecha planificada menos una holgura simulada de 0 a 6 días laborables. Resultado: error medio ≈ 2 días laborables y cumplimiento simulado 76 % = real en la muestra. El tareo (`gem_tareo`, `sim_proyecto_proceso` del mundo 6) cuenta las **horas en obra incluyendo esa ineficiencia**, como en la planta real.

## Cómo se evalúa el DSS sobre el gemelo (`dss/gemelo/politicas.py`, `scripts/exp6_gemelo.py`)

Se corre toda la historia 2019–2026 una vez por política, con el mismo azar. El DSS (QRF + Monte Carlo sobre el CRP) solo ve lo que vería la empresa: el tareo de los proyectos ya terminados, las paradas registradas, las esperas de compras e ingeniería de proyectos pasados y el avance del proyecto. Tres piezas hacen justo al DSS:

1. **Anclaje a la fecha del cotizador**: el DSS corrige al experto en vez de ignorarlo (un factor de ritmo por proyecto hace que su pronóstico mediano coincida con el plazo que estimó el cotizador; la literatura, p. ej. Rokoss, muestra que usar el plan del planificador baja mucho el error).
2. **Esperas aprendidas**: ingeniería con RFIs y compra de material se remuestrean de los proyectos terminados (sin esto el CRP no veía el mayor componente del plazo).
3. **Solapes del CRP recalibrados** con el tareo de los 13 proyectos fuera de la muestra (`dss/gemelo/calibrar_dss.py`); los 25 de la muestra no intervienen.

## Tablas (`data/steelser.db`, todas con prefijo `gem_`; `scripts/exp6_gemelo.py` las crea)

`gem_proyecto`, `gem_lote`, `gem_pieza` (marcas con perfil, kg, longitud y agujeros) · `gem_op` (cada operación: recurso, estación, inicio, fin, personas, HH) · `gem_mov` (traslados de grúa) · `gem_estado` (bitácora del estado de cada lote: reconstruye la planta en cualquier instante) · `gem_camion`, `gem_material`, `gem_paquete`, `gem_ing` · `gem_parada` (con horas de trabajo perdidas) · `gem_tareo` (horas por día, proyecto y proceso, como la hoja TAREO del formato único) · `gem_personal` · `gem_palanca`, `gem_resultado` (por política) · `gem_espera`, `gem_meta`. El tiempo `t` está en horas desde 2019-01-01 00:00. El detalle hora a hora se guarda para las políticas A0, B1, D3 y D4.

## API y vista 3D

`plataforma/gemelo.py`: `GET /api/gemelo/meta`, `/estado?t&politica`, `/lote/{id}`, `/maquina/{k}`, `/proyecto/{pid}`. La vista **Gemelo 3D** (`plataforma/web/gemelo3d.js`, three.js local) dibuja la planta en cualquier hora: máquinas con piezas móviles (sierra con volantes, punzonadora con ariete, plasma con pórtico y chispas, roscadora con mandril), puentes grúa que llevan los lotes, soldadores con arco, camiones en los muelles, material en racks, ciclo de día y noche, vuelo de cámara y panel con lo que contiene cada lote (marcas, perfiles, kg, tiempos por etapa).

## Cómo reemplazar lo simulado por datos reales

| Tabla simulada | Equivalente real | Fuente en la empresa |
|---|---|---|
| `gem_proyecto`, `gem_lote`, `gem_pieza` | Lista de piezas por proyecto (marca, perfil, peso, longitud) | Hoja `REPORTE_DE_HABILITADO` / formato único, hoja PIEZAS |
| `gem_op`, `gem_tareo` | Tareo diario por pieza o lote y proceso | Formato único, hoja TAREO |
| `gem_parada` | Bitácora de paradas | Formato único, hoja PARADAS |
| `gem_material`, `gem_espera` (compra) | Órdenes de compra: fecha de pedido y de recepción | Formato único, hoja COMPRAS |
| `gem_camion` | Guías de despacho y de servicios externos | SERVICIOS_EXTERNOS |
| `gem_paquete` | Fechas de liberación de planos y RFIs | Ingeniería / bandeja de RFI de SteelPlan |
| `gem_personal` | Planilla de contratistas | Contratos |
| Layout (`sim_planta_elemento`) | Plano con medidas | Levantamiento en planta (ver plan/05 §3.2) |
| Factor de ritmo, ausentismo, MTBF | Se estiman con el tareo real; los factores por proyecto dejan de ser necesarios | — |

Con datos reales el gemelo se **valida** (¿reproduce las duraciones por proceso y las colas?) en vez de calibrarse; si no lo reproduce, el hallazgo es sobre el gemelo, no sobre el DSS.

## Limitaciones

- La planta es una plantilla de 100 × 50 m; no hay montacargas, pasillos ni espacio como restricción.
- Un lote pasa por una estación a la vez y las cuadrillas son planas (sin especialidades ni curva de aprendizaje).
- El factor de ritmo es una caja negra por proyecto: absorbe todo lo que el gemelo no modela.
- Los plazos de proveedores y servicios externos son lognormales independientes (sin correlación entre proyectos ni estacionalidad).
- Las palancas de gestión del gemelo (horas extra, personas, segundo turno, expeditar) suponen que el contratista tiene gente disponible hasta su plantilla y que los costos son los supuestos de `dss/whatif.py`.
