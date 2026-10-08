# Documentación del proyecto

Toda la tesis y el diseño del DSS en Markdown: no hace falta abrir el Word. Para una visión general del proyecto y cómo instalarlo, ver el [README de la raíz](../README.md).

## Tesis (convertida del Word, `extras/Tesis_TF1_Steelser.docx`)

| Archivo | Contenido |
|---|---|
| [tesis/00_portada_resumen.md](tesis/00_portada_resumen.md) | Portada, resumen/abstract, índices |
| [tesis/01_introduccion.md](tesis/01_introduccion.md) | Cap. I: contexto, problema, motivación, objetivos |
| [tesis/02_revision_literatura.md](tesis/02_revision_literatura.md) | Cap. II: búsqueda, 29 artículos en 6 categorías, conclusiones |
| [tesis/03_aporte.md](tesis/03_aporte.md) | Cap. III: modelo C1–C4 y resultados esperados |
| [tesis/04_caso_estudio_anexos.md](tesis/04_caso_estudio_anexos.md) | Anexos: Steelser S.A.C., procesos, SIPOC, layout, Tabla 3 (38 proyectos), causas, indicadores |
| [tesis/05_referencias.md](tesis/05_referencias.md) | Lista de referencias (incompleta, ver análisis 02) |

Generados con `python scripts/docx_a_md.py` (requiere el Word en `extras/`, que no está en el repo). No editar a mano.

## Análisis

| Archivo | Pregunta que responde |
|---|---|
| [analisis/01_inventario_datos.md](analisis/01_inventario_datos.md) | ¿Qué hay en cada Excel y qué sirve? |
| [analisis/02_diagnostico_calidad_datos.md](analisis/02_diagnostico_calidad_datos.md) | ¿Se puede entrenar el modelo con lo que hay? (No.) Inconsistencias a corregir |
| [analisis/03_potencial_q1.md](analisis/03_potencial_q1.md) | ¿Tiene potencial Q1? Qué falta y qué aportes lo elevan |
| [analisis/04_resultados_banco_pruebas.md](analisis/04_resultados_banco_pruebas.md) | Resultados de C2 y C3 sobre datos simulados: error de HH, cobertura, frontera cumplimiento-plazo |
| [analisis/05_literatura_papers.md](analisis/05_literatura_papers.md) | Los 27 papers de `papers/`: qué herramientas usan, cuáles se parecen a las nuestras, antecedentes externos y errores de la tesis ([mapeo CSV](analisis/papers_mapeo.csv)) |
| [analisis/06_ruta_q1_y_ampliacion_bd.md](analisis/06_ruta_q1_y_ampliacion_bd.md) | Ruta a Q1 según la literatura y qué agregar a la BD (con DDL probado) |
| [analisis/09_resultados_gemelo.md](analisis/09_resultados_gemelo.md) | **Resultados principales**: el DSS evaluado contra el gemelo de eventos discretos (8 políticas, alerta temprana, riesgo de modelo, qué cambia con datos reales) |
| [analisis/08_retrospectivo_planta3d.md](analisis/08_retrospectivo_planta3d.md) | Estudio retrospectivo con datos simulados: cómo se hizo vs. qué habría pasado con el DSS (6 políticas, palancas de gestión, sensibilidad al costo) y sus límites |
| [analisis/07_de_retrospectivo_a_prospectivo.md](analisis/07_de_retrospectivo_a_prospectivo.md) | Puntos de mejora: qué es retrospectivo, qué ya es prospectivo, diseño del piloto y métricas nuevas para Q1 |

## Diseño de la solución

| Archivo | Contenido |
|---|---|
| [diseno/01_arquitectura_dss.md](diseno/01_arquitectura_dss.md) | DSS vs. software vs. app: recomendación, capas, stack, flujo de cotización |
| [diseno/02_base_de_datos.md](diseno/02_base_de_datos.md) | Esquema SQL, tablas, consultas, migración a PostgreSQL |
| [diseno/03_formato_unico_registro.md](diseno/03_formato_unico_registro.md) | Formato único Excel (tareo, fechas, paradas, servicios externos) |
| [diseno/04_modelo_matematico.md](diseno/04_modelo_matematico.md) | Ecuaciones 4–19 (las que faltan en el Word + nuevas) |
| [diseno/05_simulacion_montecarlo_crp.md](diseno/05_simulacion_montecarlo_crp.md) | Algoritmo del Monte Carlo día a día sobre el CRP |
| [diseno/07_plataforma_web.md](diseno/07_plataforma_web.md) | Plataforma SteelPlan: enlace y accesos directos, arquitectura, módulos, roles, sus Excel → módulos, funciones tipo Linear, proyectos de GitHub, hoja de ruta |
| [diseno/08_gemelo_planta.md](diseno/08_gemelo_planta.md) | Gemelo de la planta: flujo por lote, recursos y calendarios, azar común, calibración, tablas `gem_*`, API y 3D, cómo reemplazarlo por datos reales |
| [diseno/06_datos_simulados.md](diseno/06_datos_simulados.md) | Banco de pruebas SIMULADO anclado a los 25 proyectos: motor, 4 mundos, verificación, limitaciones |

## Plan

| Archivo | Contenido |
|---|---|
| [plan/01_datos_a_recolectar.md](plan/01_datos_a_recolectar.md) | Qué datos faltan, prioridad, fuente y checklist para la empresa |
| [plan/02_hoja_de_ruta.md](plan/02_hoja_de_ruta.md) | Fases, entregables, tareas inmediatas y riesgos |
| [plan/03_diseno_experimental.md](plan/03_diseno_experimental.md) | Hipótesis, validación LOPO, backtest, ablación, piloto |
| [plan/04_kit_empresa.md](plan/04_kit_empresa.md) | Kit para Steelser: agenda, cuentas, solicitud de datos, piloto prospectivo, correo modelo; Excel en `entregables/` |
| [plan/06_alcance_q1.md](plan/06_alcance_q1.md) | **Alcance y ruta a una revista Q1**: qué entra, qué se congela y qué se quita, datos a pedir, diseño de validación, referencias de código |
| [plan/05_planta_3d.md](plan/05_planta_3d.md) | Propuesta: planta 3D para gestionar (asignar, priorizar) evaluando cada decisión con QRF + Monte Carlo multi-proyecto; fases, datos, evaluación con usuarios |
| [plan/07_realismo_3d.md](plan/07_realismo_3d.md) | Plan de realismo del Gemelo 3D: sin *popping*, modelos glTF CC0 para personas y vehículos, fotos de máquinas, entorno |

## Guía

| Archivo | Contenido |
|---|---|
| [guia/entorno_python.md](guia/entorno_python.md) | Python instalado, comandos, cómo regenerar BD y docs |
