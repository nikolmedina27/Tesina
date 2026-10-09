# Procedimientos de planta con SteelPlan (v3)

Guía para el personal de Steelser: quién hace qué, cuándo y en qué pantalla. Vale para el piloto y la operación
diaria. Para la capacitación (30 minutos por rol) basta con las secciones de su rol y la tabla de rutinas.

## Roles

| Rol | Quién | Qué hace en SteelPlan |
|---|---|---|
| Gerencia | Gerente general | Ve todo; tablero de **Gerencia** e **Informe mensual**; crea y desactiva cuentas |
| Cotizador | Comercial / ingeniería | Cotiza; pregunta **¿Cabe un proyecto nuevo?**; crea proyectos desde la cotización |
| Jefe de taller | Jefe de planta | Tareo, paradas, **aprueba el plan de la cartera**, gestiona órdenes de mantenimiento |
| Supervisor / contratista | Supervisor de cada cuadrilla | Tareo de su cuadrilla, marca etapas de pieza, **reporta fallas** |
| Calidad | Responsable de calidad | Liberaciones, no conformidades, **reporta fallas** |
| **Mantenimiento** (nuevo) | Técnico o encargado de mantenimiento | Órdenes preventivas y correctivas, cierre de reparaciones, plan preventivo, fichas de máquinas |

## 1. Una máquina falla (la máquina sigue parada)

Quién: cualquiera que la vea (supervisor, calidad, mantenimiento, jefe de taller).

1. **Mantenimiento › Máquinas** → botón **Falla** en la tarjeta de la máquina (o **Reportar falla** arriba).
2. Escribir qué pasó y dejar marcado **«La máquina está parada ahora»**.
3. Se abre una **orden correctiva en curso** y la máquina pasa a **Parada por falla** en todas las pantallas (tablero, TV, Gantt de máquinas). El plan de la cartera la descuenta de la capacidad en su próximo recálculo.

> No registrar la falla como «parada» con una hora de fin estimada: la plataforma **no acepta paradas con fin futuro**.
> Mientras la máquina siga parada, la falla vive como orden en curso.

## 2. Se termina la reparación

Quién: mantenimiento o jefe de taller.

1. **Mantenimiento › Órdenes y plan** → abrir la orden (columna *En curso*).
2. Completar **inicio real**, **fin real**, técnico, repuestos, costo y **causa** de la falla.
3. **Cerrar orden**. La plataforma registra la parada con esas horas, y se actualizan la disponibilidad (Dₖ), el MTBF y el MTTR de la máquina.

## 3. Una parada que ya terminó (registro posterior)

Quién: jefe de taller, supervisor, calidad o mantenimiento.

- **Mantenimiento › Paradas › Registrar parada** (o *Planta › Registro diario › Paradas*), con inicio y fin ya ocurridos, causa y si fue planificada.
- Si hace falta reparar algo después, en la lista de paradas: **Crear orden** (queda enlazada; no duplica la parada).

## 4. Mantenimiento preventivo

Quién: mantenimiento (ejecuta) y jefe de taller (valida el plan).

- **Semana 1 del piloto:** revisar el **plan preventivo sugerido** (*Órdenes y plan › Plan preventivo*): las frecuencias iniciales son típicas de fabricante, no de Steelser. Ajustar tarea, frecuencia (días laborables u horas de uso) y duración; desactivar lo que no aplique.
- Las órdenes preventivas **se crean solas** 10 días laborables antes de vencer. Se ven en *Órdenes y plan*, en el **Gantt de máquinas** y en el tablero de **Producción** («preventivos de hoy y 2 días»).
- Para ejecutar: abrir la orden → **Iniciar ahora** → al terminar, **Cerrar orden**. Queda como parada planificada y se programa la siguiente.
- Para cambiar la fecha: editar *Programada para* en la orden. Si una entrega está en riesgo, el plan de la cartera puede **proponer** mover un preventivo; solo se mueve si el jefe de taller lo marca al aprobar.

## 5. Plan de la cartera (programación automática)

Quién: jefe de taller (aprueba); cotizador y mantenimiento pueden pedir un recálculo.

- El sistema **propone** un plan nuevo solo cuando cambia algo (tareo, piezas, paradas, preventivos, proyectos), lo revisa cada 10 minutos, y además recalcula cada noche. **Nada se aplica sin aprobación.**
- **Proyectos › Programación**: revisar la propuesta (qué fechas cambian, avisos de riesgo, preventivos que conviene mover) y **Aprobar** o **Descartar**.
- Regla de prioridad: **penalidad en riesgo** (acordada). Cambiarla solo si gerencia lo decide.
- Al aprobar, el cotizador pasa a usar la carga real de ese plan.

## 6. Un cliente pide un proyecto nuevo

Quién: cotizador (con el jefe de taller).

1. **Proyectos › Programación › ¿Cabe un proyecto nuevo?**: toneladas, tipo, día 1 y meta (un **mes**, p. ej. julio = último día hábil del mes, o una fecha).
2. Responde si cabe, **cuándo debe empezar a más tardar** y cómo afecta a los proyectos en curso. No guarda nada.
3. Para la oferta formal, usar el **Cotizador** (fecha recomendada, probabilidad y penalidad esperada).

## Rutinas

| Cuándo | Qué | Quién | Pantalla |
|---|---|---|---|
| Todo el día | Pantalla de planta encendida | — | **Inicio › Modo TV** |
| Diario, fin de turno | Tareo de cada cuadrilla; marcar etapas de pieza | Supervisores | Planta › Registro diario; Proyecto › Piezas |
| Diario, apenas ocurra | Fallas y paradas (procedimientos 1–3) | Quien la vea / mantenimiento | Mantenimiento |
| Diario, 10 min | Reunión de producción: plan vs. real, cuellos, paradas, preventivos, bloqueos | Jefe de taller + supervisores | **Inicio › Producción** |
| Diario | Revisar y aprobar la propuesta del plan si la hay | Jefe de taller | Proyectos › Programación |
| Semanal | Re-pronóstico de cada proyecto y **reporte semanal** en PDF | Jefe de taller | Proyecto › Re-pronosticar; Reporte semanal |
| Semanal | Revisión de riesgo, penalidad y carga | Gerencia | **Inicio › Gerencia** |
| Mensual, 1.er día hábil | **Informe mensual** impreso o en PDF | Gerencia / jefe de taller | Inicio › Informe mensual |

## Reglas que conviene recordar

- Todo cambio queda registrado con quién y cuándo (piezas, órdenes, planes).
- Si nunca se registró una parada, la disponibilidad dice **«sin dato»**, no 100 %: no tener registros no es no tener fallas.
- Las cuentas de demostración (`data/credenciales_demo.txt`, solo en la PC del servidor) se desactivan antes de usar datos reales; cada persona usa su propia cuenta.
