# 07 · Plataforma web SteelPlan

Frontend tipo ERP (estructura Odoo, colores SAP Fiori celeste, iconografía metalmecánica) para gestionar los proyectos y cotizar plazos. Reemplaza al prototipo Streamlit como interfaz principal; Streamlit queda como herramienta de análisis.

## Diseño y navegación

Estilo minimalista tipo Linear: barra lateral fija con el logo de Steelser, buscador (Ctrl+K), cinco grupos y, al final, **Configuración** y el usuario; bordes rectos, líneas finas, paleta neutra con el azul del logo y densidad compacta. **Modo claro y oscuro** (o el del sistema), que se elige en Configuración o con el botón de la barra lateral y se recuerda en el navegador; los gráficos y el Gantt cambian con el tema. En pantallas angostas la barra lateral se abre con un botón de menú. Configuración también guarda las preferencias del Gemelo 3D (techos, etiquetas, velocidad y modo limpio) y muestra la cuenta y datos de la versión.

Los cinco grupos, con la sub-navegación del grupo activo en la barra lateral: **Inicio**, **Cotizar** (el núcleo del DSS), **Proyectos** (lista, Gantt, tareas, RFI y NC), **Planta** (Gemelo 3D y registro diario de tareo y paradas) y **Datos** (importar el formato único y usuarios). Los grupos se filtran por rol. El buscador Ctrl+K sigue siendo un atajo global a cualquier vista.

## 1. Cómo se abre (el "enlace")

| Forma | Cómo | Quién |
|---|---|---|
| Acceso directo en el escritorio | **SteelPlan** (inicia el servidor si no está corriendo y abre el navegador) y **SteelPlan (enlace)** (solo abre `http://localhost:8600`) | La PC donde vive la BD |
| Red local de la planta | `lanzador/iniciar_red_local.bat` → otras PCs y tablets abren `http://IP-DE-LA-PC:8600` | Jefe de taller, supervisores, calidad |
| Linux | `bash lanzador/instalar_linux.sh` (instala `lanzador/SteelPlan.desktop` con la ruta de esa copia; clic derecho: Tablero de producción, Programación, Mantenimiento, Modo TV) | Opcional |
| Internet (futuro) | Servidor con HTTPS, dominio propio, respaldos y datos anonimizados o con autorización expresa | Etapa 2 (SaaS para pymes) |

Los accesos directos se recrean con `powershell -ExecutionPolicy Bypass -File lanzador\crear_acceso_directo.ps1`. La documentación de la API está en `http://localhost:8600/api/docs`.

## 2. Arquitectura

```mermaid
flowchart LR
    U["Navegador / tablet<br>(SPA: HTML + JS)"] -->|JSON + cookie de sesión| S["FastAPI<br>plataforma/server.py"]
    S --> H[("data/steelser.db<br>histórico 2019-2026<br>(solo lectura)")]
    S --> O[("data/plataforma.db<br>usuarios, proyectos en curso,<br>tareo, paradas, tareas")]
    S --> M["dss/ (C2 QRF + C3 Monte Carlo)<br>motor CRP día a día"]
    M --> H
```

- **Dos BD a propósito**: `scripts/build_db.py` recrea `steelser.db` desde cero; lo que se registra en planta vive en `plataforma.db` y nunca se borra al reconstruir el histórico.
- **Librerías del navegador** (copias locales en `plataforma/web/vendor/`, sin internet desde v2.1): [frappe-gantt](https://github.com/frappe/gantt) 0.6.1 (MIT, el mismo Gantt que usa ERPNext) y [Apache ECharts](https://github.com/apache/echarts) 5.5 (Apache-2.0). Origen y licencias en `vendor/LICENCIAS.md`.
- **PWA** (v2.1): `manifest.webmanifest` y `sw.js` (servidos en la raíz) permiten instalar SteelPlan como app en la tablet. El service worker guarda solo la cáscara (HTML, JS, CSS, librerías); la API nunca se sirve desde caché. Los navegadores solo activan el service worker en `localhost` o con HTTPS: por la red local con `http://IP:8600` la app funciona igual pero sin instalación ni caché; para eso hace falta HTTPS (etapa v4).
- **Cuentas**: contraseñas con PBKDF2-SHA256 (200 000 iteraciones, sal por usuario), sesión firmada por cookie (12 h), permisos por rol en cada endpoint. Las cuentas demo se generan al crear `plataforma.db` y sus claves quedan en `data/credenciales_demo.txt` (ignorado por git).

## 3. Módulos (v1, implementados)

| Módulo | Qué hace | Vista estilo |
|---|---|---|
| **Inicio** | Lanzador de aplicaciones + KPIs (cumplimiento histórico, retrasos, proyectos en curso, HH de la semana, tareas abiertas), cumplimiento por año, disponibilidad de máquinas de los últimos 30 días, alertas y actividad del equipo | Odoo home + Fiori launchpad |
| **Proyectos** | En curso (avance por HH contra P50) e histórico (38 proyectos con filtros Cumplió / Retraso / Muestra) | Odoo list view con botones de estado |
| **Proyecto en curso** | Gantt P50 con avance real, avance por proceso, último tareo y **re-pronóstico desde hoy** (Monte Carlo sobre el trabajo restante → semáforo) | Odoo form + Gantt |
| **Proyecto histórico** | Gantt del plan con el ratio vigente y de la ejecución simulada | Gantt |
| **Gantt** | Todos los proyectos por año o los que están en curso; verde = cumplió, rojo = retraso | Timeline |
| **Cotizador** | Fecha recomendada, probabilidad, penalidad esperada, comparación con el método actual, semáforo frente a la fecha pedida, curva plazo-riesgo-costo, histograma, HH P10/P50/P90 y Gantt probable. Botón **Crear proyecto con esta fecha** | Fiori analytical page |
| **Planta** | Tareo diario y paradas de máquina con validaciones (no se aceptan fechas futuras ni causas fuera de catálogo) | Odoo form + lista |
| **Tareas** | Tablero tipo Linear: Backlog → Por hacer → En curso → En revisión → Hecho; arrastrar y soltar, prioridad, tipo (bloqueo, no conformidad, RFI, cambio de alcance, compra), responsable, fecha límite, comentarios, identificador STL-n | Linear board |
| **Usuarios** | Alta de cuentas por rol (solo gerencia) | Odoo settings |
| **Importar** (v2) | Sube el formato único: **1. Validar** (revisa todas las filas sin guardar; errores con número de fila) y **2. Importar** (idempotente: reimportar actualiza u omite, nunca duplica). Historial de importaciones y descarga de la plantilla vacía | Odoo import |
| **Proyecto › Piezas y avance** (v2) | Avance físico ponderado por pieza, avance por etapa, por tipo de elemento, contratista y clase de peso, y lista de piezas con el estado de cada etapa | Odoo list + barras |
| **Proyecto › Curva S** (v2) | kg ponderados y HH acumuladas, plan P50 contra real, con índice de avance (real/plan a hoy) | Fiori analytical |
| **Proyecto › Compras, servicios y eventos** (v2) | Atraso de compras, servicios externos en proveedor y eventos imputables al cliente | Lista |
| **Proyecto › Piezas: marcar etapa** (v2.1) | Selección de piezas con casilla → **Marcar etapa** con fecha o **Quitar fecha** (corrección). Exige la etapa previa del fierro negro y el orden de fechas; cada cambio queda en `pieza_cambio` (quién, cuándo, antes, después) | Odoo list con acción masiva |
| **Proyecto › Semanas** (v2.1) | Semanas de producción (ciclo lunes–sábado): kg y HH planificados y reales por semana, índice de avance acumulado (en la semana en curso, a hoy) e **historial de re-pronósticos** con la probabilidad de cumplir en el tiempo | Ciclos tipo Linear + Fiori |
| **Reporte semanal** (v2.1) | Actualización semanal imprimible (A4 horizontal → **Imprimir / guardar PDF**): KPIs, último re-pronóstico, lo logrado por etapa, HH por proceso, plan de la semana siguiente, RFI/NC abiertas, compras y servicios pendientes, eventos y paradas, curva acumulada | Informe de obra |
| **RFI y NC** (v2.1) | Bandeja de RFI, no conformidades, bloqueos y cambios de alcance: abiertas, vencidas, días abierta, días promedio de cierre, **imputable a** (cliente, Steelser, proveedor, contratista, fuerza mayor), días de impacto y pieza afectada | Bandeja de entrada |
| **Buscador Ctrl+K** (v2.1) | Paleta de comandos: proyectos en curso e históricos, tareas (por texto o STL-n), piezas por marca o perfil, vistas y acciones; flechas + Enter | Linear command menu |

### Gemelo 3D de la planta (datos simulados)

Vista del menú *Planta 3D*: la planta de Steelser en 3D (three.js, copia local en `vendor/three/`), reconstruida **hora a hora** desde el gemelo de eventos discretos. Diseño en [08](08_gemelo_planta.md); resultados en [analisis/09](../analisis/09_resultados_gemelo.md); alcance en [plan/06](../plan/06_alcance_q1.md).

| Parte | Qué hace |
|---|---|
| Escena | Naves, 4 máquinas detalladas y animadas (sierra cinta con volantes y banda, cizalla-punzonadora con ariete, mesa de plasma con pórtico y chispas, roscadora con mandril; torre de luces verde/ámbar/roja), 2 puentes grúa que trasladan cada lote, 6 mesas de armado, 8 puestos de soldeo con arco, zonas de limpieza, racks con material, patios, 3 muelles con camiones, oficinas, comedor y garita. Personal con el color de su contratista, soldadores con arco y esmerilado, trabajadores en espera en el comedor. Ciclo de día y noche (la luz cambia con la hora; los turnos extra se ven de noche) |
| Cámara y atajos | **2** plano 2D, **3** perspectiva 3D, **C** caminata en primera persona, **R** rotación automática, **F**/**K** enfocar o seguir la selección, **H** ayuda con todos los atajos; botones 2D · 3D · Caminar · ⟳ · ? sobre la escena. Doble clic en una máquina abre la inspección (componentes, vista explosionada, rayos X). Detalle en [08](08_gemelo_planta.md) |
| Control del tiempo | Política (A0 como se hizo, B1 regla del jefe, D3 y D4 DSS), proyecto, control deslizante por hora, reproducción de 1 h/s a 3 días/s, vistas rápidas (general, naves, máquinas, patio, muelles, oficinas), doble clic para volar a un objeto; el techo se abre al acercarse |
| Seguimiento | Por etapa del proyecto seleccionado: lotes en proceso, en cola y entregados; fecha comprometida y fecha de término de la política elegida |
| Panel Objeto | **Máquina**: estado (operando, libre, en falla y su causa), lote que trabaja, utilización y disponibilidad de 14 días, paradas recientes. **Estación**: lote, personas, hora de término. **Lote**: marcas con perfil, kg, longitud y agujeros; tiempo en cada etapa; no conformidad y cambio de alcance. **Persona**, **camión** (carga, salida y regreso), **grúa** (qué lleva y adónde), **material** (stock por proyecto y pedidos) |
| Panel Proyecto | Cómo habría terminado con cada política (compromiso, término, días tarde, costo de palancas), curva de kg entregados por política y palancas aplicadas |
| Panel Resultados | Tabla de las 8 políticas y alerta temprana del DSS |

API (`plataforma/gemelo.py`, solo lectura de `steelser.db`): `GET /api/gemelo/meta`, `/estado?t&politica`, `/lote/{id}`, `/maquina/{k}`, `/proyecto/{pid}`. Si faltan las tablas, responde 503 con la instrucción `py scripts/exp6_gemelo.py`. `plataforma/planta.py` (what-if y búsqueda sobre el CRP) queda como API heredada sin interfaz.

### Permisos por rol

| Acción | Gerencia | Cotizador | Jefe de taller | Supervisor | Calidad |
|---|---|---|---|---|---|
| Ver tablero, proyectos, Gantt, tareas | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cotizar | ✅ | ✅ | ✅ | — | — |
| Crear proyecto desde cotización | ✅ | ✅ | — | — | — |
| Registrar tareo | ✅ | — | ✅ | ✅ | — |
| Registrar paradas | ✅ | — | ✅ | ✅ | ✅ |
| Crear y mover tareas, comentar | ✅ | ✅ | ✅ | ✅ | ✅ |
| Marcar etapas de pieza (v2.1) | ✅ | — | ✅ | ✅ (salvo liberación) | ✅ |
| Importar el formato único | ✅ | ✅ | ✅ | — | — |
| Gestionar usuarios | ✅ | — | — | — | — |

## 4. Sus Excel → módulos de la plataforma

| Hoja del Excel de la empresa (REPORTE DE AVANCE) | Qué hace hoy | Dónde va en SteelPlan | Estado |
|---|---|---|---|
| `REPORTE_DE_HABILITADO`, `REPORTE_DE_AVANCE ZONA 2`, `Hval`, `LOLIN` | Control por pieza: perfil, peso, contratista, O.F., fechas de armado, soldeo, liberación, pintura y despacho, con pesos por etapa (0.25 / 0.4 / 0.3) | Pestaña **Piezas y avance** del proyecto; hoja PIEZAS del formato único | ✅ v2 |
| `F5-434`, `F5-20050`, `RESUMEN-DANPER` | Informe de avance por partida y etapa (suministro, habilitado, fabricación, pintura, despacho, montaje) programado vs real | Pestaña **Partidas** del proyecto con barras por etapa | ⏳ v3 (falta el campo "partida" en PIEZAS) |
| `CURVA S-Producción`, `CURVA S-Montaje`, `Curva S` | Kg planificados vs ejecutados por semana | Pestaña **Curva S** del proyecto (kg desde las piezas, HH desde el tareo) | ✅ v2 (producción; montaje ⏳) |
| `HojaValorizacion`, `CONTRATOS`, `P.U`, `P.UNI`, `LISTA DE ORDENES POR CONTRATO`, `Datos_No tocar` (estados X VALORIZAR / EMITIR / VALORIZADO) | Valorización de contratistas por kg y precio unitario por tipo de elemento | Módulo **Contratistas y valorizaciones** | ⏳ v3 |
| `Suministro OT425` | Lista de control de materiales con certificados y coladas | Hoja COMPRAS → pestaña **Compras, servicios y eventos** (certificado y colada); trazabilidad completa por pieza ⏳ | 🟡 v2 |
| `CONTROL GENERAL` | HH y HH/t por OT | KPI de HH/t real en el proyecto (desde el tareo) | ✅ (avance por HH) |
| `Reporte Sem General`, `INFORME#2`, `Reporte Fotográfico` | Reporte semanal al cliente con fotos | **Actualización semanal del proyecto** (al estilo *project updates* de Linear) con exportación a PDF | ✅ v2.1 (reporte semanal imprimible; fotos ⏳ v2.2) |
| `Revision Costo` | ACU vs valorizaciones vs utilidad | **Costo real vs cotizado** | ⏳ v3 |

### "Tipos" que sugiero estandarizar (catálogos)

| Catálogo | Valores | Por qué |
|---|---|---|
| Tipo de estructura | Nave, Planta, Edificación, Mezzanine, Equipo especial | Variable del modelo y filtro de proyectos |
| Tipo de elemento | Columna, viga, tijeral, cercha, correa, arriostre, templador, placa, inserto, conector, soporte, dintel, escalera, baranda, tubería rolada… (23, tomados de sus hojas) | Hoy se escriben distinto en cada hoja (`TIJERAL`, `TIJERAL T-1 (N)`); es la base del avance por pieza y de los P.U. |
| Clase de peso | Liviana 0–250 kg, Mediana 251–1 000 kg, Pesada > 1 000 kg | Ya la usan en `REPORTE_DE_HABILITADO`; afecta el P.U. y el tiempo |
| Proceso | Los 13 procesos con su centro de trabajo | Une cotización, tareo, Gantt y modelo |
| Causa de parada | 9 causas (falla mecánica, eléctrica, repuesto, lubricación, setup, operador, material, preventivo, otro) | Disponibilidad y TPM (Hollerweger) |
| Tipo de tarea | Tarea, bloqueo, no conformidad, RFI, cambio de alcance, compra | Separa lo que atrasa por la planta de lo que atrasa por el cliente |
| Evento imputable a | Cliente, Steelser, proveedor, contratista, fuerza mayor | Define el cumplimiento contractual real (ampliaciones) |

## 5. Funciones tipo Linear: qué se tomó y qué falta

[Linear](https://linear.app/docs/making-the-most-of-linear) organiza el trabajo en *issues*, *projects*, *cycles*, *triage* e *initiatives*, con vistas de lista, tablero y *timeline* (Gantt), *project updates* y menú de comandos (Ctrl+K).

| Concepto de Linear | Equivalente en SteelPlan | Estado |
|---|---|---|
| Issue con identificador (ENG-123), prioridad, responsable | Tarea **STL-n** con prioridad Urgente/Alta/Media/Baja, tipo, responsable, fecha límite | ✅ |
| Board / list | Tablero kanban con arrastrar y soltar; filtros por proyecto y responsable | ✅ (lista ⏳) |
| Comentarios y actividad | Comentarios por tarea y *feed* de actividad en Inicio | ✅ |
| Project | Proyecto (OT) con sus tareas | ✅ |
| Timeline | Gantt del proyecto y Gantt del taller | ✅ |
| Cycles (sprints de 1–2 semanas) | **Semana de producción**: plan semanal por cuadrilla y cumplimiento del plan semanal (PPC, como en Last Planner) | ✅ v2.1 pestaña Semanas (PPC por cuadrilla ⏳) |
| Triage (bandeja de entrada) | **Bandeja de RFI y no conformidades** que entran sin asignar | ✅ v2.1 (con imputabilidad y días de impacto) |
| Project updates | **Actualización semanal** con semáforo del re-pronóstico, avance y fotos | ✅ v2.1 reporte semanal + historial de re-pronósticos (fotos ⏳) |
| Initiatives / roadmap | Cartera de proyectos por cliente o sector | ⏳ v3 |
| Ctrl+K, atajos | Buscador global de OT, tareas y piezas | ✅ v2.1 |
| Notificaciones (Slack) | Avisos por correo o WhatsApp cuando una tarea se asigna, se bloquea o el semáforo pasa a rojo | ⏳ v3 |

## 6. Hoja de ruta de la plataforma

| Versión | Contenido |
|---|---|
| **v1 (hecha)** | Cuentas y roles, tablero, proyectos, Gantt, cotizador, crear proyecto, re-pronóstico, tareo, paradas, tareas tipo Linear, accesos directos |
| **v2 (hecha)** | Importar el formato único (validar e importar, idempotente, con errores por fila), avance físico ponderado por pieza, curva S de kg y HH con índice de avance, compras, servicios externos y eventos, HH estimadas por el cotizador junto al P50 |
| **v2.1 (hecha)** | Reporte semanal imprimible (PDF desde el navegador), semanas de producción, historial de re-pronósticos, bandeja de RFI/NC con imputabilidad, buscador Ctrl+K, librerías locales (sin internet), PWA, marcar etapas de pieza en la interfaz con trazabilidad |
| **v2.2 (hecha)** | Gemelo 3D de la planta con datos simulados: escena detallada hora a hora, políticas, paneles de máquina, lote y proyecto, resultados |
| **v2.3 a v2.5 (hechas)** | Navegación en 5 grupos con barra lateral, rediseño minimalista con modo oscuro y Configuración, proyectos activos en la barra lateral |
| **v2.6 (hecha)** | Gemelo 3D realista: cámaras 2D/3D/caminata con atajos, inspección de máquinas (componentes, despiece, rayos X), personas que caminan y camiones por la calle de servicio. Plan siguiente: [plan/07](../plan/07_realismo_3d.md) |
| **v3.0 (hecha) · Mantenimiento** | Máquinas (tarjetas con estado, Dₖ 30 días vs. meta 90 %, MTBF, MTTR, último y próximo preventivo), ficha con historial, Dₖ por mes y Pareto de causas, Gantt de máquinas (Hoy · 2 días · Semana · Mes) con trabajo de proyectos, paradas y preventivos, vista de todas las paradas con calendario y Excel, órdenes preventivas automáticas y correctivas, plan preventivo editable. Rol `mantenimiento`. Detalle y fases siguientes en [plan/08](../plan/08_plan_mejoras_v3.md) |
| **v3.1 (hecha) · Programación automática** | Plan de la cartera con capacidad finita compartida, preventivos y paradas abiertas; regla de prioridad por penalidad en riesgo o EDD; propuesta vs. aprobado con diferencias y avisos; versiones guardadas (reprogramaciones); readaptación automática; sugerencias de mover preventivos; simulador de proyecto nuevo con meta mensual; Gantt maestro (proyectos + carga de máquinas); cotizador sobre el plan aprobado ([plan/08 B](../plan/08_plan_mejoras_v3.md)) |
| **v3.2 (hecha) · Tableros fijos** | Gerencia (cumplimiento 12 meses, riesgo y penalidad de la cartera, carga 4 semanas, disponibilidad, días imputables al cliente), Producción (plan vs. real de la semana, cuellos de botella, máquinas, paradas de hoy, preventivos de 2 días, bloqueos), Informe mensual imprimible y Modo TV con rotación y cinta de avisos; tablero por rol al entrar ([plan/08 C](../plan/08_plan_mejoras_v3.md)) |
| v2.7 (pendiente) | Registro sin conexión en la tablet (cola local que se sincroniza), envío del reporte semanal por correo, adjuntar fotos a RFI/NC, pesos de etapa editables desde la interfaz |
| v3.3+ | Contratistas y valorizaciones, costo real vs cotizado, trazabilidad de material, notificaciones, reentrenamiento C4 desde la interfaz |
| v4 | Multiempresa (`empresa_id`), PostgreSQL, Keycloak, despliegue con HTTPS |

## 7. Importación del formato único (v2)

- **Una sola definición** del formato en `plataforma/formato.py`: la usan el generador del Excel (`scripts/generar_formato_unico.py`) y el importador (`plataforma/importador.py`), así nunca se desalinean.
- **Validaciones por fila**:
  - valores de las listas;
  - fechas válidas y entre 2015 y 2035;
  - tareo sin fechas futuras y con 0–12 h por persona;
  - orden de etapas de cada pieza (armado no antes que habilitado, nada después del despacho);
  - fin posterior al inicio en paradas y procesos;
  - la OT debe existir (en la hoja PROYECTO del mismo archivo o ya creada).
- **Transacción**: el modo validar ejecuta exactamente lo mismo y revierte al final.
- **Idempotencia**:
  - piezas por (OT, marca, N° item);
  - tareo por (fecha, OT, proceso, cuadrilla, personas, horas);
  - paradas por (máquina, inicio);
  - compras por (OT, OC, material).
- **Fila de ejemplo**: se ignora si conserva su marcador «← EJEMPLO».
- **Avance físico ponderado** (`plataforma/avance.py`):
  - fierro negro 70 %: habilitado, armado, soldeo y liberación, 25 % cada una;
  - recubrimiento 20 %: granallado 40 %, pintura 60 %;
  - despacho 10 %.

  Viene de su hoja `REPORTE_DE_HABILITADO`; son parámetros, a validar con la empresa.
- **Curva S planificada**: reparte el peso de las piezas según la ventana de cada etapa en el programa P50 (habilitado = procesos 3–5, armado = 8, soldeo = 9, liberación = 10, granallado y pintura = 12, despacho = 13).
- **Ejemplo lleno para la demo**: `entregables/Ejemplo_importacion_OT-DEMO-001.xlsx` (no versionado; se genera con `python scripts/generar_ejemplo_importacion.py`), con 81 partidas y 42 t, todo marcado DEMO.

## 8. Ejecutar y probar

```bash
python -m pip install -r requirements.txt
python -m uvicorn plataforma.server:app --port 8600     # http://localhost:8600
python -m pytest tests -q                               # incluye importador y semanas
```

Las pruebas automáticas del importador (`tests/test_importador.py`) cubren errores por fila, que validar no escribe, que reimportar no duplica y el avance con la curva S. Al crear `plataforma.db` por primera vez se generan las cuentas demo (claves en `data/credenciales_demo.txt`).
