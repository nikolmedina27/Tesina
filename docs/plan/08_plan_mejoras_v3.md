# 08 · Plan de mejoras v3: programación automática, mantenimiento y tableros ejecutivos

Tres ideas del equipo (8/10/2026), ordenadas por dependencia: el **mantenimiento** produce el calendario de
disponibilidad de las máquinas; el **programador automático** lo usa para asignar fechas a todos los proyectos;
los **tableros fijos** muestran lo que producen ambos. Por eso el orden de construcción es A → B → C.

> Relación con [06_alcance_q1](06_alcance_q1.md): ese documento congela `dss/multiproyecto.py` y las funciones de
> producto. Este plan **descongela el motor multi-proyecto** porque pasa a ser C3 con la carga real del taller
> (hueco señalado en la revisión del 7/10: el cotizador no lee los proyectos en curso de la plataforma), y justifica
> el módulo de mantenimiento por la meta de la tesis Dₖ ≥ 90 % (TPM). Los tableros son producto: no van al paper.

---

## A. Vista de mantenimiento de máquinas (primero) · ✅ hecha (v3.0, 8/10/2026)

**Objetivo**: que el jefe de taller vea en una pantalla el estado de las 4 máquinas, su historia y lo que viene,
y que cada parada y cada mantenimiento alimente Dₖ, MTBF y MTTR reales (hoy Dₖ sale de paradas sueltas o simuladas).

### Pantallas (grupo nuevo **Mantenimiento** en la barra lateral)

| Vista | Contenido |
|---|---|
| **Máquinas** (listado ejecutivo) | Una tarjeta por máquina: foto, estado ahora (operando / parada / en mantenimiento), Dₖ de 30 días contra la meta 90 %, MTBF, MTTR, último y próximo preventivo, horas de uso. Semáforo por máquina |
| **Ficha de máquina** | Datos técnicos (marca, modelo, año, criticidad), historial completo de paradas y órdenes de mantenimiento, Pareto de causas, tendencia de Dₖ por mes, repuestos usados |
| **Gantt de máquinas** | Una fila por máquina con lo programado (operaciones de los proyectos), los preventivos y las paradas. Zoom **Hoy · 2 días · Semana · Mes**; clic en una barra → detalle |
| **Paradas (todas)** | Lista y calendario de todas las paradas: filtros por máquina, causa, planificada / falla, proyecto afectado y rango de fechas; totales de horas perdidas; exportar a Excel |
| **Plan preventivo** | Tareas preventivas por máquina con frecuencia (cada N días o N horas de uso); el sistema genera las órdenes y avisa las vencidas |
| **Órdenes de mantenimiento** | Tablero (pendiente → en curso → cerrada): tipo preventivo / correctivo, técnico, inicio y fin, repuestos, costo, parada asociada |

### Datos (en `plataforma/db_plataforma.py`, `ESQUEMA`; sin perder lo existente)

- `maquina`: id, nombre, centro de trabajo, marca, modelo, año, criticidad (A/B/C), horas por turno, foto, activa.
  Se siembra con las 4 máquinas actuales (`MAQ_NOMBRE`).
- `plan_mantenimiento`: maquina_id, tarea, frecuencia_dias o frecuencia_horas, duración estimada, responsable.
- `orden_mantenimiento`: maquina_id, tipo (PREVENTIVO / CORRECTIVO / PREDICTIVO), estado, programada_para, inicio,
  fin, técnico, descripción, repuestos, costo, parada_id, plan_id.
- `parada` se mantiene; columna nueva `orden_id` en `COLUMNAS_V2`. Una correctiva cerrada crea o enlaza su parada.

### Cálculos (`dss/mantenimiento.py`, con pruebas)

- Dₖ = (TP − T paradas) / TP por máquina y periodo (Ec. 10 de la tesis), con el calendario de turnos y feriados.
- MTBF = tiempo operativo / n.º de fallas; MTTR = horas de reparación / n.º de fallas; % preventivo vs. correctivo;
  cumplimiento del plan preventivo.
- **Calendario de disponibilidad futura** (T × 4): preventivos programados como horas no disponibles + fallas
  esperadas con el MTBF real. Es la entrada que usa B.

**Criterio de aceptación**: Dₖ, MTBF y MTTR de la vista cuadran con un cálculo a mano sobre un conjunto de paradas
de prueba; un preventivo programado aparece en el Gantt de máquinas y reduce la capacidad de ese día.

---

## B. Programación automática de proyectos (núcleo) · ✅ hecha (v3.1, 8/10/2026)

> Implementado en `dss/programador.py`, `plataforma/programacion.py`, `plataforma/web/prog.js`. Diferencias con lo planeado: la readaptación revisa el estado cada 10 minutos (huella) además del recálculo nocturno; las paradas abiertas y las correctivas en curso también restan capacidad; la regla «menor holgura» no se implementó (penalidad y EDD cubren el caso).

**Objetivo**: decir "este proyecto se entrega en **julio**" (o una fecha exacta, o "lo antes posible") y que el
sistema **asigne solo** las fechas de inicio y fin de cada proceso de **todos** los proyectos, respetando la capacidad
de las máquinas (con el mantenimiento de A), las cuadrillas, compras y servicios externos; y que **se readapte**
cuando algo cambia.

### Cómo decide

1. **Entradas**: proyectos en curso de `plataforma.db` (lo que falta de cada uno, por avance de piezas y tareo) +
   el proyecto nuevo; horas P50/P80 de C2; calendario de disponibilidad de A; fecha objetivo o ventana (julio =
   1/07–31/07; se compromete el último día hábil de la ventana salvo que se pida otra).
2. **Prioridad**: por defecto, la de mayor **penalidad en riesgo** (presupuesto × 1 %/día × P(atraso)); alternativas
   elegibles: fecha comprometida más cercana (EDD) y menor holgura. Se fija la regla, no se inventa una por proyecto.
3. **Programación hacia atrás** desde la fecha objetivo → fecha más tardía de inicio de cada proceso; **hacia adelante**
   con capacidad finita (`dss/multiproyecto.programar_multi`, R réplicas) → fechas factibles P50 y P80.
4. **Resultado**: por proyecto, fecha de inicio recomendada, fecha P80, P(cumplir julio), procesos críticos; por
   máquina, carga por día. Si no cabe en julio: cuántos días faltan y qué proyecto o qué preventivo choca.
5. **Aprobación**: el sistema propone un **plan nuevo** y muestra la diferencia con el vigente (qué fechas se movieron
   y por qué); el jefe de taller lo aprueba o lo descarta. Nada se mueve sin aprobación.

### Readaptación automática

Se recalcula una propuesta cuando: se crea o importa un proyecto, se registra una parada o un preventivo, el índice de
avance de un proyecto cae bajo 0.9, o cada noche. Si la propuesta cambia una fecha comprometida o baja P(cumplir)
de α, aparece un aviso en Inicio y en el proyecto.

### Datos

- `plan_version`: id, creado_en, motivo (nuevo proyecto, parada, avance, nocturno, manual), regla de prioridad,
  estado (PROPUESTO / APROBADO / DESCARTADO), aprobado_por.
- `plan_linea`: plan_id, proyecto_id, proceso, inicio_p50, fin_p50, fin_p80, maquina, horas.
- Guardar **todas** las versiones: es la línea base para medir cuántas reprogramaciones hubo y si las alertas llegaron
  a tiempo (indicador "reprogramaciones de producción" de la tesis, y alerta temprana del paper).

### Pantallas

- **Proyectos › Programación**: formulario "fecha o mes objetivo" + botón **Programar**; tarjetas por proyecto con
  semáforo; botón **Aprobar plan**.
- **Gantt maestro**: todos los proyectos y debajo las 4 máquinas, en una misma línea de tiempo (plan aprobado vs.
  propuesto); clic en un proyecto → su Gantt de procesos.
- En el cotizador: la fecha recomendada pasa a calcularse **sobre el plan aprobado** (carga real, no supuesta).

**Criterio de aceptación**: con 3 proyectos demo y un preventivo, el programador no sobrecarga ninguna máquina,
respeta precedencias, y al registrar una falla larga mueve los procesos afectados y avisa; prueba automática que
compara con el motor de un solo proyecto cuando hay un único proyecto (mismo resultado).

---

## C. Tableros fijos (ejecutivos) · ✅ hecha (v3.2, 8/10/2026)

**Objetivo**: pantallas de **diseño fijo** (no configurables) que la gerencia abre o que se dejan en un televisor
de planta, con lo esencial en un vistazo.

| Tablero | Para quién | Contenido |
|---|---|---|
| **Gerencia** | Gerente | OTD de los últimos 12 meses, proyectos en riesgo (semáforo P(cumplir)), penalidad esperada total en riesgo, carga del taller de las próximas 4 semanas, Dₖ de las 4 máquinas, RFI imputables al cliente |
| **Producción** | Jefe de taller | Plan de la semana vs. real por proyecto, cuellos de botella por máquina, paradas de hoy, preventivos de los próximos 2 días, tareas bloqueadas |
| **Planta (TV)** | Todos, en pantalla grande | Modo quiosco a pantalla completa, letra grande, se actualiza cada 5 minutos, rota entre: estado de máquinas, proyectos del día y avisos |
| **Mensual (PDF)** | Gerencia / asesor | Mismo contenido que Gerencia, imprimible, con la serie del mes |

Cada usuario ve por defecto el tablero de su rol al entrar. Todos los números salen de A y B y de lo ya existente
(curva S, pronósticos, bandeja); no se calcula nada nuevo aquí.

**Criterio de aceptación**: cada indicador del tablero coincide con el de su vista de detalle; el modo TV funciona
24 h sin recargar a mano.

---

## Orden y esfuerzo estimado

| Fase | Contenido | Esfuerzo | Depende de |
|---|---|---|---|
| A1 | Tablas `maquina`, `plan_mantenimiento`, `orden_mantenimiento`; `dss/mantenimiento.py` con Dₖ, MTBF, MTTR y pruebas | 1–2 sesiones | — |
| A2 | Vistas Máquinas, Ficha, Paradas (todas), Órdenes y Plan preventivo | 2 sesiones | A1 |
| A3 | Gantt de máquinas (Hoy · 2 días · Semana · Mes) y calendario de disponibilidad futura | 1 sesión | A1 |
| B1 | Programador: atrás + adelante con `programar_multi`, regla de prioridad, ventana "mes" | 2 sesiones | A3 |
| B2 | Versiones de plan, aprobación, diferencias, disparadores y avisos | 1–2 sesiones | B1 |
| B3 | Gantt maestro y cotizador sobre el plan aprobado | 1 sesión | B2 |
| C1 | Tableros Gerencia y Producción; tablero por rol | 1 sesión | A, B |
| C2 | Modo TV y PDF mensual | 1 sesión | C1 |

Las pruebas (`tests/`) y la documentación (`diseno/07`, `CLAUDE.md`) se actualizan en cada fase.

## Datos que pide a la empresa

- Ficha de las 4 máquinas (marca, modelo, año) y una foto de cada una.
- Plan de mantenimiento que usen hoy (aunque sea informal) y la bitácora de reparaciones que exista.
- Turnos reales por máquina y feriados de la planta.
- Hasta tenerlos, todo funciona con los datos demo marcados como tales.

## Decisiones del equipo

Confirmadas el 8/10/2026: prioridad por **penalidad en riesgo**; el programador **puede proponer** mover un preventivo, y solo se mueve con aprobación. Sin respuesta (se usa la interpretación de abajo): "fecha julio" y "día · 2 días".

### Lista original

1. "Fecha julio": se interpreta como **ventana mensual** (comprometer el último día hábil del mes); confirmar si
   prefieren otra fecha dentro del mes.
2. "Día · 2 días": se interpreta como **zoom del Gantt de máquinas** (hoy y los próximos 2 días, para programar el
   turno); confirmar.
3. Regla de prioridad por defecto: penalidad en riesgo (recomendada) o fecha comprometida más cercana.
4. Si el programador puede **proponer** mover un preventivo para salvar una entrega (recomendado: proponer sí, mover solo con aprobación).
