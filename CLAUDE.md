# CLAUDE.md

Tesis de Ingeniería Industrial (UPC, Seminario de Investigación Aplicada 1FII0283, ciclo 202615) y prototipo de software asociado. Autoras: Ruth Vanessa Huamaní Hinostroza y Shirley Nikol Medina Luque. Asesor: Eduardo Emiliano Torres Yokoki. Estado: TF1 entregado (20/07/2026); en camino a TF2 y a un paper.

Idioma de trabajo: **español** (docs, comentarios, nombres de tablas y columnas).

## La tesis en una página

**Título**: "Modelo de mejora de procesos utilizando estandarización del trabajo y pronósticos con machine learning para mejorar el cumplimiento de entregas de estructuras metálicas en una industria metalmecánica".

**Caso**: Steelser S.A.C. (Lima), pyme metalmecánica que fabrica estructuras metálicas bajo pedido (MTO/ETO). Planta de 5 000 m², 4 máquinas de habilitado (sierra cinta Kaltenbach, cizalladora-punzonadora Pedimax, mesa CNC, roscadora RIDGID); armado, soldeo y limpieza los hacen **contratistas pagados por kg**; doblez y granallado/pintura son servicios externos.

**Problema**: incumplimiento de plazos. OTD = **68.4 %** (26 de 38 proyectos 2019–2026). Penalidad contractual de **1 % del presupuesto por día, sin tope**. Tres causas raíz:
1. Cotización con **ratios HH/t estáticos** según el criterio del cotizador, sin estandarizar ni recalibrar (Índice de Obsolescencia del Ratio, Io).
2. Programación con **disponibilidad de planta asumida al 100 %** (sin TPM, sin paradas).
3. **Desconexión de datos** entre cotizaciones y taller.

**Aporte**: un DSS de cotización probabilística de fechas con 4 componentes:
- **C1 · Estandarización y curaduría de datos**: formato único de registro (HH reales, fechas, cuadrilla, paradas), estudio de tiempos TS = TO·FR·(1+S), depuración, Io.
- **C2 · Quantile Regression Forest**: predice el factor de corrección φ = HH_real / HH_ratio por proyecto × proceso → P10/P50/P80/P90. Validación leave-one-project-out contra ratio, regresión lineal y RF puntual.
- **C3 · CRP de carga finita + Monte Carlo** (R = 1 000): capacidad diaria por máquina × Dₖ (TPM), cuadrillas, servicios externos y carga actual del taller → fecha cotizada = cuantil α (0.80 por defecto), probabilidad de cumplir, penalidad esperada, semáforo.
- **C4 · Lazo de control cerrado**: reentrenar si Md > 0.30 con ≥ 3 proyectos nuevos, o si PICP < 0.70.

**Metas**: OTD ≥ 85 %, retraso promedio ≤ 0.5 días, lead time cotizado +5 % como máximo, PICP 0.80 ± 0.05, Dₖ ≥ 90 %.

## Hallazgos que condicionan todo el trabajo

1. **No hay HH reales.** En `Proyectos_muestra_25 Dep.xlsx`, `HH estimadas = toneladas × ratio(tipo, proceso)` exacto (28.04 / 30.96 / 33.88 / 36.79 HH/t por tipo). Entrenar C2 sobre esa columna es fuga de información. Esa columna es el **ratio vigente** (línea base), guardado en `ratio_vigente`. La variable objetivo `proyecto_proceso.hh_real` está vacía hasta que se recolecten tareos.
2. Los días por proceso de ese Excel también son un reparto construido (retrasos de ±1 día por proceso que suman el retraso del proyecto).
3. **Sesgo de selección**: la muestra (25) deja fuera 6 de los 12 proyectos atrasados (OTD muestra 76 % vs. población 68.4 %).
4. La tesis tiene inconsistencias (28 vs. 25 proyectos, 38 − 9 ≠ 28, Ecuaciones 5–15 ausentes, RF vs. QRF, referencias faltantes). Lista completa en `docs/analisis/02_diagnostico_calidad_datos.md`.
5. **La historia de proyectos y fechas de Steelser es real.** Distinguirla de los campos generados por los experimentos: la reconstrucción de `scripts/reconstruir_muestra.py` es solo una ruta auxiliar para instalaciones sin `extras/`, y los escenarios `sim_*` no son registros de ejecución. El retrospectivo (`analisis/08`) conserva la línea base real y simula los contrafactuales; detalle en `docs/diseno/06_datos_simulados.md`.

Potencial Q1: alto **si** se consiguen HH reales, se valida con backtest + piloto y se agregan α\* tipo newsvendor, calibración conformal y correlación entre procesos en el Monte Carlo (`docs/analisis/03_potencial_q1.md`).

## Decisiones tomadas

- La solución es un **DSS implementado como aplicación web**: prototipo en **Streamlit + SQLite** (tesis); a futuro, SaaS multiempresa con FastAPI + PostgreSQL + PWA de captura en planta. Excel se mantiene como canal de entrada y salida del formato único.
- El formato único **extiende** el control por pieza que la planta ya usa (`OPE-PRO-FR`, hoja `REPORTE_DE_HABILITADO`) y agrega TAREO, PROCESO_FECHAS, PARADAS y SERVICIOS_EXTERNOS.
- El bucket de simulación es el **día** (lunes a sábado, 8 h/turno por defecto), con disponibilidad por máquina muestreada por día.

## Estructura del repositorio

**Este repo es solo código y Markdown.** Los Word, Excel y PDF viven fuera, en `~/Documents/shirley docs/` (Word de la tesis, `Papers/`, `entregables/`). `.gitignore` bloquea `*.docx`, `*.xlsx`, `*.xls`, `*.pdf` y `*.pptx`. Los documentos de trabajo se escriben en `docs/` como `.md`.

```
CLAUDE.md                 este archivo
requirements.txt          dependencias Python
extras/                   ORIGINALES de la empresa (no editar; NO versionado, solo local): Word de la tesis, 3 Excel, PDF ST087
data/steelser.db          BD SQLite generada (en .gitignore; no editar a mano)
data/*.csv                resultados de los experimentos 1-3 (versionados)
sql/schema.sql            esquema de la BD real: fuente de verdad (las tablas sim_* las crea dss/simulador.py)
scripts/                  build_db, reconstruir_muestra, docx_a_md, calibrar_solapes, exp1-exp5
dss/                      código del DSS (ver "Estado del código")
plataforma/               plataforma web SteelPlan (FastAPI + SPA; planta.py = API de la planta 3D)
lanzador/                 .bat, .desktop, ícono y script de accesos directos
entregables/              Excel generados (no versionados; se regeneran con scripts/generar_*.py)
app/streamlit_app.py      cotizador Streamlit (prototipo anterior, para análisis)
tests/                    pruebas (pytest)
.claude/launch.json       configuración para abrir el cotizador en el navegador de la app
README.md                 presentación del proyecto e instalación para colaboradores
docs/README.md            índice de toda la documentación
docs/tesis/               tesis convertida por capítulos (generada)
docs/analisis/            inventario de datos, diagnóstico, potencial Q1, resultados, literatura, retrospectivo (08)
docs/diseno/              arquitectura, BD, formato único, ecuaciones, Monte Carlo
docs/plan/                datos a recolectar, hoja de ruta, diseño experimental, kit empresa, planta 3D (05)
docs/guia/                entorno Python y comandos
```

## Plataforma web SteelPlan (`plataforma/`)

Interfaz principal: estilo minimalista tipo Linear (barra lateral, bordes rectos, paleta neutra con el azul del logo de Steelser, **modo claro y oscuro**), Gantt frappe-gantt, gráficos ECharts. Detalle en `docs/diseno/07_plataforma_web.md`.
- Abrir: acceso directo **SteelPlan** del escritorio (`lanzador/iniciar_plataforma.bat`) o `py -m uvicorn plataforma.server:app --port 8600` → `http://localhost:8600`. Red local: `lanzador/iniciar_red_local.bat`. Linux: `lanzador/SteelPlan.desktop` + `scripts/steelplan-launch.sh` (llevan la ruta de la PC de Paolo; otro usuario debe editarlas). Recrear accesos directos: `lanzador/crear_acceso_directo.ps1`.
- `plataforma/server.py` (FastAPI, sesión por cookie, permisos por rol), `plataforma/db_plataforma.py` (BD operativa), `plataforma/web/` (SPA vanilla JS: index.html, app.js, styles.css).
- **Dos BD**: `data/steelser.db` (histórico, la recrea `build_db.py`) y `data/plataforma.db` (usuarios, proyectos en curso, tareo, paradas, tareas; **nunca se recrea**). No mezclar.
- **Diseño (v2.4)**: tokens de color en `:root` y `:root[data-tema="oscuro"]` de `styles.css` (los nombres antiguos `--azul`, `--gris`… son alias); `--radio: 0`. El tema (claro, oscuro, sistema) y las preferencias del Gemelo 3D se guardan en `localStorage` (`sp_tema`, `sp_prefs`) y se cambian en la vista **Configuración** (`#/config`) o con el botón de la barra lateral. El logo está en `plataforma/web/img/` (extraído del logo de Steelser). Gráficos: tema `sp-oscuro` registrado en `app.js`.
- **Navegación (v2.3, ahora barra lateral)**: el menú tiene 5 grupos, cada uno con una sub-navegación: Inicio · **Cotizar** · **Proyectos** (Proyectos, Gantt, Tareas, RFI y NC) · **Planta** (Gemelo 3D, Registro diario) · **Datos** (Importar, Usuarios). Los grupos y permisos están en `GRUPOS` y `ROLES` de `plataforma/web/app.js`; las rutas `#/gantt`, `#/tareas`, etc. no cambian. El Gemelo 3D tiene «Modo limpio» y el seguimiento de etapas plegable.
- Roles: gerencia, cotizador, jefe_taller, supervisor, calidad. Cuentas demo y sus claves en `data/credenciales_demo.txt` (ignorado por git; no copiar las claves en documentos ni respuestas). Proyecto `OT-DEMO-001` marcado `es_demo`.
- Prospectivo: re-pronóstico de proyectos en curso (`Cotizador.cotizar(..., restante=...)`), MTBF desde paradas registradas tras 60 días, cotización guardada antes de ejecutar.
- El modelo de horas de la plataforma se entrena con el escenario simulado M2; la interfaz lo advierte.
- Kit para la empresa: `docs/plan/04_kit_empresa.md`; el Excel `entregables/Formato_Unico_Steelser_v1.xlsx` no se versiona: se genera con `py scripts/generar_formato_unico.py` (la descarga `/api/plantilla` da 404 hasta generarlo).
- **v2**: importación del formato único (vista Importar; `plataforma/importador.py`, validar = misma transacción revertida, idempotente), avance físico ponderado por pieza y curva S (`plataforma/avance.py`; pesos por etapa 70 % fierro negro / 20 % recubrimiento / 10 % despacho, de su hoja REPORTE_DE_HABILITADO), pestañas Piezas, Curva S y Compras-servicios-eventos en el proyecto.
- **Fuente única del formato**: `plataforma/formato.py` (HOJAS y LISTAS). Si se cambia una columna, se cambia ahí; el generador y el importador la leen. Tablas nuevas en `plataforma.db` se agregan en `ESQUEMA` y las columnas nuevas en `COLUMNAS_V2` (migración sin perder datos).
- Ejemplo lleno DEMO: `entregables/Ejemplo_importacion_OT-DEMO-001.xlsx`, no versionado (`py scripts/generar_ejemplo_importacion.py`).
- **v2.1**: reporte semanal imprimible (`#/reporte/{id}`, PDF desde el navegador), pestaña Semanas (ciclos lunes–sábado, `avance.semanas`), historial de re-pronósticos (tabla `pronostico`; mide alertas tempranas en el piloto), bandeja RFI y NC (`/api/bandeja`; columnas `imputable`, `dias_impacto`, `conjunto`, `fecha_cierre` en `tarea`), buscador Ctrl+K (`/api/buscar`), marcar etapas de pieza desde la interfaz (`/api/piezas/etapa`, trazado en `pieza_cambio`; el orden de etapas está en `avance.error_orden_etapas`, compartido con el importador), librerías locales en `plataforma/web/vendor/` y PWA (`sw.js`, `manifest.webmanifest`; el service worker solo se activa en localhost o HTTPS).
- **v2.2+ · Gemelo 3D** (vista *Planta → Gemelo 3D*; `plataforma/gemelo.py`, `plataforma/web/gemelo3d.js` + `gemelo_modelos.js`, three.js local en `vendor/three/`): reconstruye hora a hora la planta desde el gemelo de eventos discretos (`dss/gemelo/`) con datos SIMULADOS; solo lee `steelser.db` (tablas `gem_*`), no toca `plataforma.db`. Assets procedurales, cámaras 2D/3D/caminata (tecla **H** = atajos; **2**/**3** = 2D/3D). Posición de las máquinas: `layout()` de `dss/simulador_planta.py` (tras cambiarla: `python -m dss.simulador_planta`). Diseño en `docs/diseno/08_gemelo_planta.md`, resultados en `docs/analisis/09_resultados_gemelo.md`, alcance Q1 en `docs/plan/06_alcance_q1.md`, plan de realismo en `docs/plan/07_realismo_3d.md`. `plataforma/planta.py` es API heredada (sin interfaz). El servidor manda `Cache-Control: no-cache` a la interfaz; si cambias rutas de la API hay que reiniciarlo. Al cambiar `app.js`/`styles.css` sube `?v=` en `index.html` y `VERSION` en `sw.js`.
- `creado_en` de SQLite está en UTC; para días o fechas locales usar `date(col,'localtime')`.
- Puntos de mejora retrospectivo → prospectivo: `docs/analisis/07_de_retrospectivo_a_prospectivo.md`.

## Literatura (`papers/`)

27 PDFs renombrados a su título (mapeo en `docs/analisis/papers_mapeo.csv`; script `scripts/renombrar_papers.py`, que espera una carpeta local `papers/`). Los PDFs **no se versionan en git** (tamaño y derechos de autor) y se guardan en `~/Documents/shirley docs/Papers/`. Análisis en `docs/analisis/05_literatura_papers.md` y ruta a Q1 con ampliación de BD en `06_ruta_q1_y_ampliacion_bd.md`. Hallazgos:
- Ninguno de los 27 usa QRF, calibración conformal ni Monte Carlo con penalidad; ninguno junta ML de horas + capacidad + incertidumbre.
- Fuera de los 27 (`analisis/05` §7): Mehdiyev et al. 2025 sí usa QRF + SHAP en manufactura (QRF no es novedad) y Flores-Gómez & Dauzère-Pérès 2026 define el *makespan service level*, equivalente a nuestro P(cumplir).
- **El experto es base fuerte**: Rokoss (planificación RMSE 5.87 vs ML 5.56 días) y Roblek (el plan humano gana) coinciden con nuestro banco de pruebas.
- Antecedentes externos a tratar: Bekci et al. 2022 (arXiv, lead time probabilístico para cotizar), Keskinocak & Tayur (cotización de fechas), Mundt & Lödding 2025 (fecha confiable con colchón fijo).
- Disponibilidad real de una celda CNC: 69–78 % (Hollerweger); los escenarios M1–M4 asumen ≈ 92 %. El escenario M5 (≈ 80 %) cubre la sensibilidad: el método no se degrada si las paradas se registran.
- La tesis tiene dos citas mal resumidas (Hajj Chehade, Rokoss); ver `analisis/02` #13–#15.

## Estado del código

| Módulo | Qué hace |
|---|---|
| `dss/crp_engine.py` | Motor día a día (lunes a sábado), 13 procesos con precedencias y solapes calibrados (error 2.0 d vs. plazo planificado real) |
| `dss/datos.py` | Acceso a BD, ratio vigente, cuadrillas y plazos externos típicos, **carga del taller** (proyectos en curso ocupan las 4 máquinas; κ = 0.5), MTBF estimado |
| `dss/simulador.py` | Datos SIMULADOS de 4 mundos condicionados a los 25 proyectos reales |
| `dss/c2_modelo.py` | `PhiEmpirico` y `PhiQRF` (QRF + calibración conformal agrupada por proyecto); predicen φ = HH_real / HH_ratio |
| `dss/c3_montecarlo.py` | `Cotizador.cotizar()`: φ con dependencia gaussiana entre procesos, paradas aleatorias, carga del taller, plazos externos → `Resultado` (fecha α, P(cumplir), penalidad esperada, curva); `alpha_optimo()` tipo newsvendor |
| `dss/whatif.py` | Palancas de gestión (personas, segundo turno, horas extra, expeditar), evaluación con semillas comunes, búsqueda automática por etapas y sensibilidad por proceso; costos de palancas = SUPUESTOS (`COSTOS`) |
| `dss/multiproyecto.py` | Varios proyectos comparten las 4 máquinas por prioridad (probado; aún sin interfaz) |
| `dss/retrospectivo.py` | `Retro` simula escenarios contrafactuales; 6 políticas (A0 como se hizo … A5 sistema completo); la línea base observada es real y el efecto de la decisión se estima con diferencias simuladas |
| `dss/simulador_planta.py` | Layout de la planta (100 × 50 m; lo usa el gemelo) y datos de planta del estudio retrospectivo anterior (`sim_planta_elemento`, `sim_lote`, …) |
| `dss/gemelo/` | **Gemelo de eventos discretos** hora a hora: `calendario` (turnos, feriados, ventanas por recurso), `generador` (38 proyectos, 9 162 lotes, paradas, proveedores, RFIs; modelo oculto de φ), `motor` (flujo por lote, 4 máquinas, 2 grúas, mesas, puestos, cuadrillas con ausentismo, camiones; palancas), `calibrar` (ritmo por proyecto → reproduce fechas reales), `calibrar_dss` (solapes del CRP con el tareo de los 13 proyectos fuera de la muestra), `politicas` (A0, B1, C1, D0–D4), `exportar` (tablas `gem_*` y mundo 6) |
| `app/streamlit_app.py` | Cotizador web (`py -m streamlit run app/streamlit_app.py`; también `.claude/launch.json`) |
| `scripts/exp1_prediccion.py`, `exp2_backtest.py`, `exp3_frontera.py`, `exp4_ablacion.py` | Experimentos; resultados en `data/*.csv`. exp1 y exp4 usan los 5 escenarios; exp2 y exp3 se corrieron con 4 |
| `scripts/exp5_retrospectivo.py` | Retrospectivo con el CRP como verdad (histórico, circular; ver `analisis/08`) |
| `scripts/exp6_gemelo.py` | **Estudio principal**: calibra el gemelo, corre la historia 2019-2026 con 8 políticas y mide alerta temprana (`data/exp6_*.csv`, tablas `gem_*`) |
| `tests/` | 50 pruebas (`py -m pytest tests -q`; las que necesitan la BD se omiten si falta): motor CRP, multi-proyecto, what-if, C3, planta, gemelo, retrospectivo, importador, semanas de producción y orden de etapas |

Pendiente: C1 (`c1_datos`: importar el formato único, depuración, Io, Dₖ reales), C4 (`c4_lazo`: Md, PICP, alertas), ablaciones A2–A4 y sensibilidades, módulo del formato único en Excel. Ver `docs/diseno/01_arquitectura_dss.md`.

## Resultados sobre datos simulados (docs/analisis/04_resultados_banco_pruebas.md)

- C2: QRF baja el error de HH vs. el ratio donde hay sesgo o no linealidad (p. ej. M2: 7.4 → 5.4 % por proyecto); conformal deja P10-P90 en ≈ 0.80.
- C3: fecha α = 0.80 se cumple 76-84 %; α* = 0.93 (con p = 1 %/día, perder 0.5 pts de prob. por día, margen 16 %) da 84-96 %.
- **El DSS NO supera al cotizador a igual plazo**: necesita +4 a +7 % de plazo para igual cumplimiento (76 %). La meta de la tesis "OTD ≥ 85 % con lead time +5 %" no se alcanza; reformular como frontera cumplimiento-plazo + penalidad esperada. Con N = 25 los IC (±16 pts) se traslapan. Solo datos reales pueden cambiar esto.
- **Experimento 4 (5 escenarios, 125 cotizaciones)**: un **colchón fijo** (plan determinista con carga del taller + N días) iguala al Monte Carlo en la frontera (6.3 % vs 6.9 % de plazo extra para 80 % de cumplimiento; 9.9 % vs 12.8 % para 90 %). La pieza que más aporta es la **carga del taller** (+2.2 pts si se quita); Dₖ y ρ importan en la cola (sin ellos 15 % de las remuestras no llega a 90 %); el conformal no cambia la frontera. La ventaja del Monte Carlo es la **calibración interpretable** (α = 0.8 → 83 % observado).
- **Punto débil abierto**: la calibración es marginal, no por tamaño: con α = 0.80 los proyectos chicos cumplen 67 %, los medianos 85 %, los grandes 100 %. Siguiente mejora: conformal condicional por tamaño.
- GBM cuantílico (competidor tipo Bekci) subcubre el intervalo de HH (0.62–0.69); QRF + conformal queda en 0.78–0.81.

- **Experimento 5 (retrospectivo, `analisis/08`)**: A0 usa los resultados reales: OTD 76 %, penalidad calculada 1.2 % del presupuesto. Las políticas alternativas son contrafactuales simulados; sus horas por proceso, paradas y costos de palancas no son observaciones históricas. Las conclusiones de esas políticas dependen de dichos supuestos.
- **Experimento 6 (gemelo de eventos discretos, `analisis/09`)**: la «verdad» ya no sale del motor del DSS. Anclado al plan del cotizador y con esperas de compras aprendidas: fecha α = 0.80 cumple 80 % (calibrado) con +0.8 % de plazo; α\* cumple 88 % con +8.6 %; un **colchón fijo** de +7 d lab. cumple 100 % con +12 % y es el mejor en costo ajustado. **La gestión con palancas no sirve** (regla del jefe 9.6 % de costo sin mejora; DSS gestión 1.3 % sin mejora): el atraso viene de pintura externa y material, no de la planta (riesgo de modelo). **Alerta temprana**: AUC 0.55 / 0.68 / 0.68 / 0.83 por cuartil del plazo. Ninguna diferencia frente a A0 es distinguible de cero (N = 25). Alcance y ruta a Q1 en `docs/plan/06_alcance_q1.md`.

## Datos simulados (banco de pruebas)

Hasta tener tareos reales, C2 y C3 se desarrollan sobre datos **SIMULADOS** (`docs/diseno/06_datos_simulados.md`): tablas `sim_*`, 5 mundos (M1 ratio casi correcto, M2 sesgo, M3 no lineal/colas, M4 deriva, M5 disponibilidad ≈ 80 %), condicionados a la duración real de los 25 proyectos. Reglas:
- Nunca presentarlos como datos reales; declararlos en tesis y paper. Las tablas reales (`proyecto_proceso.hh_real`) siguen vacías.
- Hallazgo: el ratio es correcto en promedio; el problema es la **dispersión** por proyecto (±5–11 % en HH totales, ±14–16 % por proceso).
- La carga del taller (WIP) ya está modelada de forma simplificada (ventana 20–50 % de la duración, κ = 0.5, toneladas imputadas en 13 proyectos); son supuestos sin sensibilidad todavía.
- Las paradas de máquina, los plazos externos y las variables del plano son supuestos del simulador, no mediciones.
- Orden de regeneración: `py scripts/build_db.py` (o `py scripts/reconstruir_muestra.py` si falta `extras/`), luego `py -m dss.simulador`, `py -m dss.simulador_planta` y `py scripts/exp6_gemelo.py` (build_db borra las tablas `sim_*` y `gem_*`).
- La planta 3D y el gemelo (`gem_*`) también son SIMULADOS: plantilla funcional de 100 × 50 m, personal anónimo, proveedores, paradas y HH inventados y calibrados a las fechas reales; no es un plano medido.

## Comandos

Python 3.12. En Windows (equipo de Shirley) está en `%LOCALAPPDATA%\Programs\Python\Python312` y se usa `py` si `python` abre la Microsoft Store; en Linux (equipo de Paolo) hay un `.venv/` en la raíz (`.venv/bin/python`). Los comandos de abajo usan `py`: en Linux sustituir por `python`. Instalación y guía para colaboradores en `README.md` y `docs/guia/entorno_python.md`.

```bash
py -m pip install -r requirements.txt   # dependencias
py scripts/build_db.py                  # recrear data/steelser.db desde extras/
py scripts/docx_a_md.py                 # regenerar docs/tesis/ desde el Word
py -m dss.simulador                     # generar datos simulados (después de build_db)
py -m pytest tests -q                   # pruebas
py -m streamlit run app/streamlit_app.py  # cotizador web
py -m dss.simulador_planta              # layout de la planta y datos del retrospectivo anterior
py scripts/exp6_gemelo.py               # gemelo de eventos discretos + 8 políticas (~6 min con 6 núcleos); crea las tablas gem_* que usa el Gemelo 3D
py scripts/exp5_retrospectivo.py        # retrospectivo anterior con el CRP como verdad (~8 min); acepta --costo 2
py scripts/exp1_prediccion.py           # experimentos (varios minutos cada uno); exp3_frontera.py acepta "plan"
```

`python-docx` está instalado pero roto (falta el binario de `lxml`); los scripts no lo usan, leen el `.docx` con `zipfile` + `xml.etree`.
Git instalado; `origin` = `https://github.com/nikolmedina27/Tesina.git` (público, `main` sin protección; Paolo es colaborador con escritura, no admin). `extras/` es confidencial: nunca debe entrar al historial (comprobado limpio hasta `e8a23d7`). Hacer `git pull --rebase` antes de empezar y de subir.

## Base de datos (data/steelser.db)

Cargado hoy: `proyecto` (38, Tabla 3 del Word; `en_muestra = 1` para los 25), `proyecto_proceso` (325), `ratio_vigente` (52), `proceso` (13), `centro_trabajo` (11), `tipo_estructura` (4), `ot_hh_real` (4 OT con HH reales), `pieza_avance` (77), `cotizacion` + `acu_linea` (ST087), `parametro` (11).
Vacías, para la implementación: `tareo`, `parada_maquina`, `calendario_planta`, `estudio_tiempos`, `servicio_externo_plazo`, `modelo_version`, `prediccion`, `simulacion`, `alerta_reentreno`.
Simuladas (`py -m dss.simulador`): `sim_mundo`, `sim_feature`, `sim_proyecto_proceso`, `sim_parada`, `sim_verificacion`.
Vistas: `v_otd`, `v_hh_por_tipo`, `v_disponibilidad`.

## Reglas para trabajar en este proyecto

- Nunca editar `extras/`. Si llega un archivo nuevo de la empresa, ponerlo en `extras/` (local, ignorado por git: copiarlo desde `~/Documents/shirley docs/`) y extender `scripts/build_db.py`.
- No agregar Word, Excel ni PDF al repo; van en `~/Documents/shirley docs/`. Las versiones de trabajo de la tesis y del paper se escriben en `.md` bajo `docs/`.
- Cambios de esquema: en `sql/schema.sql` y luego `py scripts/build_db.py` (la BD se recrea desde cero).
- `docs/tesis/` se regenera desde el Word; las correcciones de la tesis se hacen en el Word, no en esos `.md`.
- No entrenar ni reportar modelos sobre `hh_ratio_vigente` como si fuera dato real.
- Toda cifra de la tesis o del paper debe poder recalcularse desde `data/steelser.db` con un script.
- Validación siempre agrupada por proyecto (leave-one-project-out); nunca dividir procesos de un mismo proyecto entre entrenamiento y prueba.
- Fijar y guardar la semilla en toda simulación.
- Datos de la empresa son confidenciales (hay declaración jurada): no subirlos a servicios externos sin anonimizar.
