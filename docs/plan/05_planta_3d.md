# 05 · Planta 3D para gestionar con QRF y Monte Carlo (propuesta)

> Estado: **superado por el gemelo de eventos discretos** ([diseno/08](../diseno/08_gemelo_planta.md), [plan/06](06_alcance_q1.md)). La vista 3D de este plan (replay del CRP) se reemplazó por el Gemelo 3D, cuya «verdad» no sale del motor del DSS; `plataforma/web/planta3d.js` se eliminó. Se conserva como registro del diseño original y de lo que dejó: `dss/whatif.py`, `dss/multiproyecto.py` y `plataforma/planta.py`. Antes: implementado en su versión retrospectiva con datos simulados (ver «Estado de implementación»). Amplía el alcance aprobado (C1–C4): requiere visto bueno del asesor antes de entrar a la tesis. Referencia visual: tablero isométrico tipo "WareTrack" (escena 3D movible, KPIs arriba, panel lateral al hacer clic, seguimiento abajo).

## Estado de implementación (retrospectivo, datos simulados)

| Fase | Estado | Dónde |
|---|---|---|
| 1 · Motor de decisión | ✅ What-if y búsqueda automática con semillas comunes (`dss/whatif.py`), palancas en el motor (`mult`, `mult_desde`, `avance0` en `dss/crp_engine.py`), motor multi-proyecto con máquinas compartidas por prioridad (`dss/multiproyecto.py`, probado pero aún sin interfaz), criticidad por sensibilidad. ⏳ Convergencia de R, correlación en el multi-proyecto, costos reales de las palancas | `tests/test_whatif.py`, `tests/test_multiproyecto.py` |
| 2 · Modelo de planta | ✅ Layout por plantilla, personal, asignaciones, material y lotes simulados en SQL (`dss/simulador_planta.py`). ⏳ Editor 2D, plano medido, tabla operativa en `plataforma.db` | `tests/test_planta.py` |
| 3 · Escena 3D | ✅ (reemplazada por `plataforma/web/gemelo3d.js`) vista *Planta 3D* en SteelPlan: clic, panel, línea de tiempo, techos y etiquetas. ⏳ Modo «Riesgo» por colores, arrastrar cuadrillas | verificado en el navegador |
| 4 · Gestión | 🟡 Palancas, evaluar, sugerir y probar en la escena. ⏳ Arrastrar y soltar, guardar decisiones (`decision`) | `plataforma/planta.py` |
| 5 · Validación | 🟡 Estudio retrospectivo con 6 políticas (`dss/retrospectivo.py`, `scripts/exp5_retrospectivo.py`, [analisis/08](../analisis/08_retrospectivo_planta3d.md)). ⏳ Datos reales, piloto en paralelo, experimento 2D vs. 3D con usuarios | `data/exp5_*.csv` |

Hallazgo de esta implementación: el re-pronóstico de proyectos en curso tenía un defecto (cada proceso ya terminado tardaba un día en «registrarse» y retrasaba toda la cadena de precedencias, unos 5 a 11 días de pesimismo). Se corrigió dándole al motor el avance inicial real (`avance0`); también mejora el re-pronóstico de SteelPlan.

## 1. Idea en una frase

Una **vista 3D de la planta de Steelser** que sirve de entrada para **gestionar** (asignar cuadrillas, turnos, prioridades, mantenimiento), donde **cada decisión se evalúa con el QRF y el Monte Carlo** antes de aplicarse. El 3D es la capa visual; el cerebro sigue siendo C2 + C3.

| Capa | Qué es | Estado |
|---|---|---|
| Visual | Escena 3D: naves, máquinas, mesas, material, personal, piezas | Nueva |
| Gestión | Acciones del jefe de taller / PM sobre la escena: asignar, priorizar, programar | Nueva |
| Decisión | What-if y búsqueda automática de escenarios con números aleatorios comunes | Nueva (sobre el motor actual) |
| Modelos | QRF (φ por proyecto × proceso) + Monte Carlo sobre el CRP | Existe (`dss/c2_modelo.py`, `dss/c3_montecarlo.py`) |
| Datos | Proyectos, piezas, tareo, paradas, cuadrillas + **modelo de planta** y **stock** | Parcial |

## 2. Qué NO es (para no prometer de más)

- **No es seguimiento en tiempo real con sensores.** No hay RTLS, PLC ni cámaras. Las personas y piezas se ubican según el **plan** y el **último registro** (tareo, etapas de pieza). "En vivo" = tan fresco como el último registro (diario o por pieza).
- **Las personas son representativas**: un avatar por persona registrada en la cuadrilla de esa estación ese día, no su posición física.
- **No reemplaza a un simulador de eventos discretos** tipo Simio. El motor es por día; la animación dentro del día es interpolada.
- **El 3D no es la contribución científica.** La generación automática de gemelos digitales y la visualización 3D de simulaciones ya tienen literatura (ver §9). La contribución sigue siendo la decisión: fecha y asignación con probabilidad calibrada.

## 3. La planta (cómo se modela)

### 3.1 Lo que sabemos
- 5 000 m², distribución **funcional por procesos** (tesis, Figura 8): recepción y almacén de materiales → corte y habilitado → armado y soldeo → inspección → despacho. Doblez y granallado/pintura son **externos**.
- 4 máquinas: sierra cinta Kaltenbach, cizalladora-punzonadora Pedimax, mesa CNC, roscadora RIDGID.
- Armado, soldeo y limpieza: **contratistas pagados por kg**.
- Patrón típico de plantas de estructuras: material en patio de acopio → línea de vigas (corte, perforado o punzonado) → armado en mesas → soldeo → control → pintura → despacho, con **puentes grúa** por nave; casi cada paso es un izaje.

### 3.2 Lo que falta (levantamiento en planta, Fase 0)

| Dato | Para qué | Cómo |
|---|---|---|
| Plano con medidas (CAD o croquis acotado) | Posición real de naves, pasillos, zonas | Pedir a la empresa o medir con wincha láser |
| Posición y huella de las 4 máquinas | Ubicarlas en la escena | Medición + fotos |
| Puentes grúa: cantidad, capacidad, nave que cubren | Recurso compartido; posible cuello de botella | Preguntar a jefe de taller |
| N° de mesas de armado y puestos de soldeo, por contratista | Estaciones y capacidad de C3 | Conteo |
| Zonas de acopio de perfiles, planchas, piezas habilitadas, piezas terminadas | Material clicable | Recorrido |
| Punto de carga a granallado/pintura y patio de despacho | Flujo de salida | Recorrido |
| 20–40 fotos de referencia | Fidelidad visual | Celular |

**Pregunta clave para la planta**: ¿la grúa o el espacio frenan la producción? Si sí, se modelan como recurso en C3 (y entonces el layout sí cambia las fechas). Si no, el layout es explicativo.

### 3.3 Modelo de planta (fuente única)
Archivo/tabla `planta_elemento` que define la escena **sin modelar a mano**:

```
id, tipo (nave|zona|maquina|mesa|puesto_soldeo|grua|rack|patio|muelle),
nombre, centro_trabajo_id, proceso_id, x, y, ancho, largo, alto, rotacion, capacidad, metadatos(json)
```

- Generador por **plantilla**: desde `centro_trabajo` y `proceso` arma un layout funcional por defecto (naves en fila, flujo izquierda → derecha).
- Editor 2D sencillo (vista en planta, arrastrar rectángulos) para ajustar al plano real.
- El 3D se **genera** de esta tabla: cambiar una fila cambia la escena. Esto es lo "automático" medible (horas para tener el modelo vs. modelado manual).

## 4. La escena 3D (qué se ve y qué se puede tocar)

Isométrica, movible (rotar, acercar, encuadrar), al estilo de la referencia.

| Objeto | Cómo se ve | Al hacer clic (panel lateral) |
|---|---|---|
| **Máquina** | Volumen low-poly por tipo, luz de estado (verde operando / ámbar en cola / rojo parada) | Estado, cola de piezas, utilización hoy y 7 días, Dₖ, paradas recientes, **índice de criticidad** (% de réplicas en que es cuello de botella), **efecto en P(cumplir)** de cada proyecto si se para 1 día |
| **Mesa de armado / puesto de soldeo** | Mesa con piezas encima, avatares de la cuadrilla | Contratista, personas, kg y HH hoy, pieza en curso, proyecto, avance |
| **Rack o acopio de material** | Paquetes de perfiles / planchas | Contenido: perfil, cantidad, kg, colada, certificado, OT a la que está reservado, días en stock |
| **Pieza** | Bloque coloreado por etapa (habilitado, armado, soldeo, liberado, pintura, despacho) | Marca, perfil, peso, OT, etapa, fechas, contratista, siguiente estación |
| **Proyecto** (resaltado) | Todas sus piezas iluminadas en la planta | Fecha comprometida, P(cumplir) hoy, P10–P90 de fin, procesos atrasados, RFI/NC abiertas |
| **Personal** | Avatar simple con color por contratista | Cuadrilla, estación, horas registradas |
| **Grúa** | Puente sobre la nave | Cola de izajes (si se modela) |
| **Muelle externo** | Camión en salida a granallado o despacho | Lote, proveedor, fecha de retorno estimada (P50/P80) |

Elementos de pantalla (como la referencia):
- **Arriba**: KPIs del taller: proyectos en curso, % en verde/ámbar/rojo, cumplimiento histórico, HH de la semana, cuello de botella del día.
- **Derecha**: panel del objeto seleccionado.
- **Abajo**: seguimiento del proyecto seleccionado (etapas como la "Shipment Tracking" de la referencia: habilitado → armado → soldeo → pintura → despacho, con fecha P50/P80) y lista de estaciones.
- **Línea de tiempo**: deslizador de días para ver hoy, el plan P50 de las próximas semanas o un escenario.

### Modos de la escena
1. **Hoy** — estado según tareo y etapas de pieza registradas.
2. **Plan** — reproducción día a día de la réplica P50 del Monte Carlo (qué estará dónde).
3. **Riesgo** — color de cada estación según su contribución al atraso (criticidad del Monte Carlo).
4. **Escenario** — lo mismo bajo una decisión propuesta, comparado lado a lado con el plan actual.

## 5. Gestión: qué hace el usuario y qué responde el modelo

El PM (proyectos, tareas, Gantt) queda como **entrada**; el foco es **asignar y decidir**.

| Acción en la escena | Qué se recalcula | Respuesta |
|---|---|---|
| Arrastrar una cuadrilla a otra mesa / proyecto | Monte Carlo multi-proyecto con la nueva cuadrilla | Δ P(cumplir) por proyecto, Δ penalidad esperada, nuevo cuello de botella |
| Activar turno 2 u horas extra en una máquina | Capacidad diaria de ese centro | Ídem + costo adicional |
| Programar mantenimiento (bloquear días) | Dₖ de la máquina | Ídem |
| Cambiar prioridad entre proyectos | Regla de reparto de capacidad | Quién gana y quién pierde probabilidad |
| Tercerizar un proceso | Plazo externo en vez de capacidad interna | Ídem + costo |
| Botón **Sugerir** | Búsqueda automática sobre las palancas | Top 3 decisiones con su efecto y costo, frontera probabilidad–costo |
| **Aplicar** | Se guarda como decisión | Registro inmutable (quién, cuándo, alternativa elegida, predicción) para evaluar después |

Todas las comparaciones usan **números aleatorios comunes** (mismas semillas para todos los escenarios) para que las diferencias sean de la decisión y no del azar.

## 6. Cambios en los modelos (lo científico)

1. **Monte Carlo multi-proyecto** (el cambio más importante). Hoy la carga del taller se aproxima (κ = 0.5, ventana 20–50 %). Para asignar entre proyectos, todos los proyectos en curso deben simularse **juntos** compartiendo máquinas, cuadrillas y grúa, con una regla de prioridad. Extiende `dss/crp_engine.py` de (R, 13) a (R, P, 13).
2. **QRF por proyecto × proceso sin cambios**: sigue dando φ; las HH muestreadas alimentan el motor multi-proyecto. Se mantiene la dependencia entre procesos (ρ).
3. **Despacho diario a estaciones**: convierte el avance diario por proceso en piezas por estación (reparto por la ventana P50, como ya hace la curva S en `plataforma/avance.py`). Es lo que se anima.
4. **Optimizador de escenarios**: palancas discretas (cuadrilla ±1, turno, horas extra, prioridad, tercerizar, mantenimiento); búsqueda por evaluación sucesiva (descartar malas con pocas réplicas, refinar las buenas con más; tipo *successive halving* / OCBA). Objetivo: minimizar penalidad esperada + costo de recursos con P(cumplir) ≥ meta. Costos de palancas: pedir a la empresa o declararlos como supuestos con sensibilidad.
5. **Criticidad**: por estación, fracción de réplicas en que es el cuello de botella del proyecto; alimenta el modo Riesgo.
6. **Convergencia de R**: justificar el número de réplicas por estabilidad de P(cumplir) y del cuantil α (pendiente ya listado en la hoja de ruta).

## 7. Datos nuevos en `plataforma.db`

Respetando la regla del repo (tablas nuevas en `ESQUEMA`, columnas nuevas en `COLUMNAS_V2`):

| Tabla | Contenido |
|---|---|
| `planta_elemento` | Layout (§3.3) |
| `material_lote` | Stock: perfil/plancha, cantidad, kg, colada, certificado, ubicación (`planta_elemento`), OT reservada |
| `asignacion` | Fecha, estación, cuadrilla/contratista, personas, proyecto, turno, horas extra |
| `escenario` | Palancas propuestas, semilla, resultado (P(cumplir) y penalidad por proyecto), origen (manual/sugerido) |
| `decision` | Escenario aplicado, quién, cuándo, predicción en ese momento (append-only) |

Se queda en **SQLite** (con modo WAL, una conexión por solicitud y `busy_timeout`). El modelo de planta se define independiente del motor de BD para migrar a PostgreSQL cuando haya varios usuarios escribiendo de verdad.

## 8. Técnica

- **three.js** como librería local en `plataforma/web/vendor/` (MIT, sin CDN, igual que ECharts y frappe-gantt). Geometría **procedural low-poly** generada desde `planta_elemento` (sin modelos 3D de terceros; si se usan, solo CC0).
- `InstancedMesh` para piezas y paquetes (cientos de objetos en tablet), `OrbitControls` para mover la cámara, *raycasting* para el clic, etiquetas HTML sobre los objetos.
- Endpoints nuevos: `GET /api/planta/modelo`, `GET /api/planta/estado?fecha=`, `GET /api/planta/plan?proyecto=&dia=`, `POST /api/planta/escenario`, `POST /api/planta/sugerir`, `POST /api/planta/decision`.
- Respuesta de un escenario: < 2 s con R = 1 000 por escenario; sugerencia automática: < 1 min (búsqueda por etapas).
- Pruebas: motor multi-proyecto (conservación de HH, precedencias, reproducibilidad con semilla), optimizador (encuentra el óptimo en casos pequeños enumerables), endpoints con permisos por rol.

## 9. Posicionamiento científico

- **Ya existe**: generación automática de gemelos digitales y de su 3D a partir de modelos de datos, visualización 3D web de simulaciones de eventos discretos y QRF para incertidumbre en manufactura (Mehdiyev et al. 2025). No se reclama novedad en ninguno.
- **Contribución defendible**: decisión de **fecha y asignación** en un taller ETO de pyme con (a) incertidumbre de horas aprendida con pocos proyectos y calibrada, (b) capacidad finita multi-proyecto, (c) búsqueda automática de decisiones con números aleatorios comunes, (d) un modelo de planta generado desde datos, y (e) **evaluación con usuarios reales**.
- **Cómo se evalúa el 3D** (lo que lo convierte en evidencia): experimento con el jefe de taller y el cotizador, mismas tareas de decisión en **2D (tablas/Gantt) vs. 3D**: tiempo de decisión, calidad de la decisión (penalidad esperada de la elegida vs. la óptima), usabilidad (SUS) y carga mental (NASA-TLX). Más el piloto en paralelo con datos reales.
- Sin horas reales y sin piloto, sigue siendo un estudio con datos simulados: congreso o Q2, no Q1.

## 10. Fases

| Fase | Contenido | Duración estimada | Necesita |
|---|---|---|---|
| **0 · Levantamiento** | Checklist §3.2 en planta | 1 semana | Visita |
| **1 · Motor de decisión** | Monte Carlo multi-proyecto, números aleatorios comunes, what-if, criticidad, convergencia de R, pruebas | 3 semanas | Nada nuevo (datos simulados) |
| **2 · Modelo de planta** | `planta_elemento`, generador por plantilla, editor 2D, `material_lote` | 2 semanas | Plano (si no, plantilla) |
| **3 · Escena 3D** | Visor, objetos, clic y panel, modos Hoy/Plan/Riesgo, línea de tiempo, avatares y piezas | 3–4 semanas | Fases 1–2 |
| **4 · Gestión** | Acciones sobre la escena, Sugerir, Aplicar, registro de decisiones | 2 semanas | Fase 3 |
| **5 · Validación** | Datos reales, piloto en paralelo, experimento 2D vs. 3D con usuarios | según la empresa | Tareos reales |

Total sin piloto: **≈ 11–12 semanas**. Orden no negociable: la Fase 1 primero, porque sin ella el 3D solo anima un plan sin decidir nada.

## 11. Riesgos

| Riesgo | Mitigación |
|---|---|
| El alcance no entra en TF2 | Tesis = Fases 1–2 + 3 básica; paper = 3 completa, 4 y 5 |
| Expectativa de "personal en vivo" | Declarar en la interfaz que la escena viene del plan y del último registro |
| Sin horas reales | Todo con datos simulados declarados; priorizar el registro de tareo |
| Rendimiento en tablet | Low-poly, instancias, límite de objetos, modo 2D de respaldo |
| Costos de palancas desconocidos | Supuestos explícitos + análisis de sensibilidad |
| El 3D distrae del núcleo | Cada vista 3D debe mostrar un número de C2/C3; si no, no entra |
