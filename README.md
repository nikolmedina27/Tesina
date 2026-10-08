# Tesina · Cotización probabilística de fechas de entrega (Steelser S.A.C.)

Prototipo de software de la tesis de Ingeniería Industrial (UPC, Seminario de Investigación Aplicada 1FII0283, ciclo 202615):

> *Modelo de mejora de procesos utilizando estandarización del trabajo y pronósticos con machine learning para mejorar el cumplimiento de entregas de estructuras metálicas en una industria metalmecánica.*

**Autoras**: Ruth Vanessa Huamaní Hinostroza y Shirley Nikol Medina Luque · **Asesor**: Eduardo Emiliano Torres Yokoki

## El problema

Steelser S.A.C. (Lima) fabrica estructuras metálicas bajo pedido. Solo el **68.4 %** de sus proyectos (26 de 38, 2019–2026) se entrega a tiempo, y el contrato penaliza el **1 % del presupuesto por día de atraso, sin tope**. Las causas raíz son tres:

1. Cotiza con ratios de horas-hombre por tonelada fijos, sin recalibrarlos.
2. Programa asumiendo que la planta trabaja el 100 % del tiempo.
3. Las cotizaciones y el taller no comparten datos.

## La solución

Un sistema de apoyo a la decisión (DSS) que, en vez de una fecha única, entrega **una fecha con su probabilidad de cumplirla** y la penalidad esperada. Tiene cuatro componentes:

| | Componente | Qué hace | Código |
|---|---|---|---|
| C1 | Estandarización de datos | Formato único de registro (tareo, fechas, paradas, servicios externos) | `plataforma/formato.py`, `plataforma/importador.py` |
| C2 | Predicción de horas | Quantile Regression Forest sobre φ = HH real / HH del ratio, con calibración conformal | `dss/c2_modelo.py` |
| C3 | Programación y Monte Carlo | Motor de capacidad finita día a día (13 procesos, 4 máquinas, contratistas) × 1 000 réplicas → fecha para un nivel de confianza α | `dss/crp_engine.py`, `dss/c3_montecarlo.py` |
| C4 | Lazo cerrado | Reentrenar si el modelo se desvía | pendiente (`dss/c4_lazo.py`) |

El DSS se usa desde **SteelPlan**, una aplicación web (FastAPI + página de una sola vista) con cotizador, Gantt, tareo, paradas de máquina, tareas, importación del formato único en Excel, curva S y reporte semanal. La vista **Planta 3D** es un gemelo digital de la planta: simula eventos discretos hora a hora y sirve de banco de pruebas para comparar políticas sobre una base histórica real de proyectos y fechas (2019–2026). Las variables de proceso y los contrafactuales generados por el gemelo son simulados y calibrados a esos resultados históricos.

## Estado y advertencias

- **La historia de proyectos y fechas es real.** Aún faltan HH reales medidas por proceso: la columna "HH estimadas" del Excel de la empresa es el ratio vigente multiplicado por las toneladas. Por eso los experimentos de C2 y los contrafactuales de C3 usan escenarios simulados anclados a los 25 proyectos reales; sus resultados de modelo se reportan como simulados.
- Resultado actual (simulado, sobre el gemelo): anclado al plan del cotizador, el DSS con α = 0.80 cumple 80 % —calibrado— sin alargar el plazo, y avisa con AUC 0.83 de los atrasos en el último cuarto del plazo. Pero un colchón fijo bien afinado cumple lo mismo con menos esfuerzo, y la gestión con palancas de capacidad **no mejora** las fechas porque el atraso viene de proveedores y pintura. Detalle en [docs/analisis/09_resultados_gemelo.md](docs/analisis/09_resultados_gemelo.md) y ruta hacia una revista en [docs/plan/06_alcance_q1.md](docs/plan/06_alcance_q1.md).
- Estado de la tesis: TF1 entregado; en camino a TF2 y a un paper.

## Estructura del repositorio

```
dss/            motor CRP, modelo de φ (C2), Monte Carlo (C3), what-if, gemelo de eventos discretos (dss/gemelo/), estudios retrospectivos, simuladores de datos
plataforma/     SteelPlan: servidor FastAPI, BD operativa, importador, interfaz web (web/)
app/            cotizador Streamlit (prototipo anterior, para análisis)
scripts/        construcción de la BD, experimentos 1-6, generadores del Excel, utilidades
sql/            esquema de la BD histórica (fuente de verdad)
tests/          50 pruebas (pytest)
data/           resultados de los experimentos (CSV); las BD se generan localmente
lanzador/       accesos directos de SteelPlan (Windows y Linux)
docs/           tesis en Markdown, análisis, diseño, plan y guías (índice en docs/README.md)
```

## Cómo empezar

Requiere Python 3.12.

```bash
git clone https://github.com/nikolmedina27/Tesina.git
cd Tesina
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pytest tests -q                              # debe dar 50 passed (algunas se omiten si falta la BD)
```

Para construir la base de datos y abrir la plataforma hacen falta los archivos de la empresa en `extras/`, que **no están en el repositorio** (son confidenciales). Pídelos a las autoras y luego:

```bash
python scripts/build_db.py                             # crea data/steelser.db
python -m dss.simulador                                # datos simulados
python -m dss.simulador_planta                         # layout de la planta
python scripts/exp6_gemelo.py                          # gemelo de eventos discretos y 8 políticas (~6 min)
python -m uvicorn plataforma.server:app --port 8600    # http://localhost:8600
```

La primera vez, la plataforma crea cuentas de demostración y guarda sus claves en `data/credenciales_demo.txt` (ignorado por git). Guía completa y experimentos: [docs/guia/entorno_python.md](docs/guia/entorno_python.md).

## Documentación

Empieza por [docs/README.md](docs/README.md). Lo más útil para entrar al proyecto:

| Si quieres… | Lee |
|---|---|
| Entender los datos y sus límites | [docs/analisis/02_diagnostico_calidad_datos.md](docs/analisis/02_diagnostico_calidad_datos.md) |
| Entender el diseño del DSS | [docs/diseno/01_arquitectura_dss.md](docs/diseno/01_arquitectura_dss.md) y [04_modelo_matematico.md](docs/diseno/04_modelo_matematico.md) |
| Conocer la plataforma | [docs/diseno/07_plataforma_web.md](docs/diseno/07_plataforma_web.md) |
| Ver los resultados | [docs/analisis/04_resultados_banco_pruebas.md](docs/analisis/04_resultados_banco_pruebas.md) |
| Saber qué falta | [docs/plan/02_hoja_de_ruta.md](docs/plan/02_hoja_de_ruta.md) |

`CLAUDE.md` es el contexto que usa el asistente de IA (Claude Code) al trabajar en el repositorio; no hace falta leerlo para colaborar.

## Reglas para colaborar

- Trabajamos en **español** (documentación, comentarios, nombres de tablas y columnas).
- Este repo es **solo código y Markdown**: no se suben Word, Excel ni PDF.
- **Nunca** subir `extras/`, bases de datos (`*.db`), credenciales ni datos de Steelser. Hay declaración jurada de confidencialidad.
- Los resultados con datos simulados siempre se declaran como simulados.
- Toda cifra de la tesis o del paper debe poder recalcularse con un script desde la BD.
- Validación siempre agrupada por proyecto (leave-one-project-out) y con semilla fija.
- Antes de subir: `git pull --rebase` y `python -m pytest tests -q`.
