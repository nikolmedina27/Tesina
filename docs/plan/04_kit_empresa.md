# 04 · Kit para la empresa (Steelser S.A.C.)

Todo lo que hay que llevar y pedir para completar los registros operativos por proceso, validar los componentes simulados con observaciones y empezar el piloto. La historia de proyectos y fechas ya es real.

## Qué se lleva

| Entregable | Archivo | Para qué |
|---|---|---|
| Formato único de registro (Excel) | `entregables/Formato_Unico_Steelser_v1.xlsx` (se regenera con `py scripts/generar_formato_unico.py`) | 9 hojas con listas desplegables: PROYECTO, COTIZ_PROCESO, PIEZAS, TAREO, PROCESO_FECHAS, PARADAS, SERV_EXTERNOS, COMPRAS, EVENTOS. Sigue su control por pieza OPE-PRO-FR |
| Plataforma SteelPlan (demo en laptop) | acceso directo "SteelPlan" en el escritorio | Mostrar cómo se verá el registro y el cotizador; se usa en vivo con el proyecto DEMO |
| Ejemplo del formato lleno | `entregables/Ejemplo_importacion_OT-DEMO-001.xlsx` | Mostrar en la reunión cómo se llena cada hoja, importarlo en vivo (vista **Importar**) y ver el avance por pieza y la curva S que resultan |
| Checklist de datos | este documento, sección 3 | Lo que se pide, a quién y en qué formato |
| Guía de procedimientos de planta | [`docs/guia/procedimientos_planta.md`](../guia/procedimientos_planta.md) | Quién hace qué y cuándo: fallas, reparaciones, preventivos, aprobación del plan, rutinas diarias, semanales y mensuales; base de la capacitación |
| Autorización de uso de información | anexo de la tesis | Debe cubrir tareos, planillas, contratos, cotizaciones perdidas y bitácora de mantenimiento |

## 1. Agenda de la reunión (60 min)

| Min | Tema | Con quién |
|---|---|---|
| 0–10 | Qué encontramos: el cumplimiento real es 68.4 % (26 de 38); el ratio por tonelada es correcto en promedio pero falla por proyecto. Hoy no existen horas reales por proceso | Gerencia, jefe de proyectos |
| 10–25 | Demo de SteelPlan: cotizar un proyecto de 47 t, ver fecha y probabilidad, crear el proyecto, registrar tareo, re-pronosticar | Gerencia, cotizador, jefe de taller |
| 25–40 | Qué datos necesitamos (sección 3) y quién los tiene | Todos |
| 40–50 | Piloto: 3 meses de registro diario con el formato o la plataforma; cotizaciones en paralelo (sección 4) | Gerencia, cotizador, jefe de taller |
| 50–60 | Cuentas de usuario, confidencialidad y próximos pasos | Gerencia |

## 2. Cuentas de la plataforma (una por persona)

| Rol en SteelPlan | Quién | Puede |
|---|---|---|
| Gerencia | Gerente general | Ver todo, crear y desactivar usuarios |
| Cotizador | Área comercial / ingeniería | Cotizar, crear proyectos desde una cotización, gestionar tareas |
| Jefe de taller | Jefe de planta | Cotizar, registrar tareo y paradas, **aprobar el plan de la cartera**, gestionar órdenes de mantenimiento |
| Supervisor / contratista | Supervisor de cada contratista (T&C, Tarrillo, RFR, Torres, LHL) | Registrar el tareo de su cuadrilla y sus paradas, **reportar fallas**, ver y comentar sus tareas |
| Calidad | Responsable de calidad | Registrar paradas y no conformidades, liberar, **reportar fallas** |
| **Mantenimiento** | Técnico o encargado de mantenimiento | Órdenes preventivas y correctivas, cierre de reparaciones, plan preventivo y fichas de las 4 máquinas |

Se crean en **Usuarios** (rol gerencia). Las cuentas de demostración se desactivan antes de usar datos reales.

## 3. Solicitud de datos

**P0 · sin esto no hay modelo**

| # | Dato | Quién lo tiene | Formato aceptado | Periodo |
|---|---|---|---|---|
| 1 | Tareos o partes diarios (personal propio y contratistas) | Jefe de taller, RR.HH., contratistas | Fotos, PDF o Excel; se transcriben a la hoja TAREO | 2021–2026 (los 25 proyectos) |
| 2 | Planillas semanales (n° de personas) | RR.HH. | Excel | Mismo |
| 3 | Lista de piezas o modelo Tekla de cada proyecto | Oficina técnica | Excel o reporte Tekla | Los 25 |
| 4 | Contratos u órdenes de compra (monto, plazo, penalidades) | Comercial | PDF | Los 38 |
| 5 | **Lo que estimó el cotizador** por proceso (HH, días, cuadrilla) | Cotizador | ACU o Excel de cotización; hoja COTIZ_PROCESO | Los que existan |
| 6 | Motivo de exclusión de los 13 proyectos fuera de la muestra | Jefe de proyectos | Conversación | — |

**P1 · para el cálculo de capacidad y el Gantt**

| # | Dato | Quién | Periodo |
|---|---|---|---|
| 7 | Bitácora u órdenes de mantenimiento de las 4 máquinas | Mantenimiento / jefe de taller | Lo que exista; si no hay, empezar a registrar ya |
| 8 | Órdenes de servicio de granallado/pintura, doblez y rolado (envío y retorno) | Logística | 2023–2026 |
| 9 | Órdenes de compra de material (pedido, prometida, recepción) | Compras | 2023–2026 |
| 10 | Cambios de alcance, RFI y suspensiones del cliente | Jefe de proyectos | Los 25 |

**P2 · para la competitividad (α\*)**

| # | Dato | Quién | Periodo |
|---|---|---|---|
| 11 | **Todas las cotizaciones**, ganadas y **perdidas**, con plazo y precio ofertado | Comercial | 2023–2026 |
| 12 | Plazo o precio del ganador cuando se perdió (si se sabe) | Comercial | Mismo |
| 13 | Penalidades realmente cobradas y ampliaciones concedidas | Administración | 2021–2026 |

## 4. Piloto prospectivo (lo que da evidencia de nivel Q1)

1. **Semanas 1–2 · Arranque**: crear cuentas, capacitar 30 minutos al jefe de taller, a cada supervisor y a mantenimiento con la [guía de procedimientos](../guia/procedimientos_planta.md), cargar los proyectos en curso, **validar el plan preventivo sugerido** y aprobar el primer plan de la cartera.
2. **Semanas 1–12 · Registro diario**: tareo y paradas todos los días (plataforma en tablet o la hoja TAREO/PARADAS del Excel); las fallas se reportan en **Mantenimiento** apenas ocurren y se cierran con su orden. Meta: ≥ 90 % de días laborables con registro. Reunión de producción de 10 minutos con el tablero **Producción** y aprobación diaria del plan si hay propuesta.
3. **Cotización en paralelo (*shadow mode*)**: cada cotización nueva se hace como siempre **y** en SteelPlan, sin que el sistema cambie la oferta. Se guardan ambas fechas antes de saber el resultado.
4. **Re-pronóstico semanal** de cada proyecto en curso; la plataforma guarda cada uno (pestaña **Semanas › Historial de re-pronósticos**), lo que permite medir con cuánta anticipación se avisó un atraso. Ese mismo día se imprime el **Reporte semanal** en PDF para la reunión de obra.
5. **RFI y no conformidades** en la bandeja **RFI y NC**, marcando a quién es imputable cada día de impacto: separa el atraso propio del causado por el cliente (dato que falta en el histórico).
6. **Cierre**: al entregar cada proyecto se compara fecha real contra la del cotizador y la del sistema.
7. **Encuesta de usabilidad** (SUS, 10 preguntas) al final a cada usuario.

## 5. Confidencialidad

- Los datos de la empresa se quedan en la PC del servidor (`data/`); el repositorio git no se sube a ningún remoto.
- Para el paper se publican datos **anonimizados** (clientes como C01…C38, montos normalizados).
- La plataforma funciona en la red interna; no se expone a internet sin HTTPS, contraseñas propias y autorización de gerencia.

## 6. Correo modelo para solicitar los datos

> Asunto: Datos para la tesis de cotización de plazos · solicitud
>
> Estimado(a) [nombre]:
>
> Como parte de la tesis sobre el cumplimiento de entregas que venimos desarrollando con Steelser, necesitamos los siguientes registros históricos de los proyectos 2021–2026: tareos o partes diarios de personal propio y de contratistas, planillas semanales, listas de piezas, contratos con su plazo y penalidad, las estimaciones de horas que se hicieron al cotizar, la bitácora de mantenimiento de las cuatro máquinas de habilitado y el registro de cotizaciones ganadas y perdidas.
>
> Adjuntamos el formato único en Excel para el registro desde ahora. Toda la información se usará solo para la tesis, según la autorización firmada, y se presentará anonimizada.
>
> Quedamos atentas para coordinar la entrega. Gracias.

(El correo lo envían las tesistas; aquí solo queda el texto.)
