# 02 · Hoja de ruta

Plan en semanas relativas al inicio del trabajo. Las fases 1 y 2 se pueden solapar con la recolección de datos (fase 0) si se usan datos reconstruidos parciales.

| Fase | Semanas | Estado | Entregable | Hecho cuando… |
|---|---|---|---|---|
| **0 · Datos** | 1–4 | ⏳ **Bloqueante, sin iniciar**: se trabaja con datos simulados | Datos P0 cargados en `data/steelser.db`; registro diario de tareo y paradas en marcha | `SELECT COUNT(*) FROM proyecto_proceso WHERE hh_real IS NOT NULL` ≥ 25 × 13 (o el máximo disponible, documentado) |
| **1 · C1 Estandarización** | 3–6 | ⏳ Pendiente | Importador del formato único (`dss/c1_datos.py`), filtro de depuración, Io por proceso, primer Dₖ | Tabla de Io por proceso y Dₖ por máquina en la tesis |
| **2 · C2 Predicción** | 5–9 | ✅ Hecho sobre datos **simulados** (`dss/c2_modelo.py`, `scripts/exp1_prediccion.py`); repetir con datos reales | QRF + conformal con validación LOPO; comparación contra ratio, RLM, RF | Tabla de métricas por modelo; QRF + conformal con PICP en 0.80 ± 0.05 ([analisis/04](../analisis/04_resultados_banco_pruebas.md)) |
| **3 · C3 CRP + Monte Carlo** | 8–12 | ✅ Hecho (`dss/crp_engine.py`, `dss/c3_montecarlo.py`, 49 pruebas en total); falta convergencia en R y sensibilidades | Simulador verificado (determinista, convergencia) | d_α, P(cumplir) y E[Pen] para un proyecto nuevo; ⏳ cotización ST087 |
| **4 · C4 + interfaz** | 11–14 | 🟡 Interfaz Cotizar hecha (`app/streamlit_app.py`); ⏳ lazo cerrado y pantallas Planta, Modelo, Indicadores | Lazo cerrado y app Streamlit con 4 pantallas | El cotizador puede cotizar un proyecto sin ayuda de los tesistas |
| **5 · Validación** | 13–16 | 🟡 Backtest, frontera y retrospectivo con palancas de gestión hechos sobre datos simulados (`exp2`, `exp3`, `exp5`); ⏳ piloto y datos reales | Backtest sobre proyectos pasados + piloto en paralelo con cotizaciones reales | Resultados de [03_diseno_experimental.md](03_diseno_experimental.md) |
| **6 · Redacción** | 15–18 | ⏳ Pendiente | Tesis TF2 corregida + borrador de paper (congreso) | Lista de [analisis/02 §4](../analisis/02_diagnostico_calidad_datos.md) resuelta |

## Tareas inmediatas

1. Corregir las inconsistencias de la tesis (lista en [analisis/02](../analisis/02_diagnostico_calidad_datos.md)) e incorporar las ecuaciones de [diseno/04](../diseno/04_modelo_matematico.md).
2. Llevar el checklist de [01_datos_a_recolectar.md](01_datos_a_recolectar.md) a la empresa y empezar el registro de tareo y paradas con el formato único (kit en [04_kit_empresa.md](04_kit_empresa.md)).
3. Completar la lista de referencias y verificar "Zhang et al. (2024)".
4. Implementar C4 (`dss/c4_lazo.py`) y las ablaciones y sensibilidades pendientes.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| No existen tareos históricos por proceso | Reconstrucción por kg avanzados (ver [01](01_datos_a_recolectar.md)); si tampoco, registrar prospectivamente 5–8 proyectos y declarar el resto como limitación |
| Muy pocos proyectos cerrados durante la tesis para el lazo cerrado | Demostrar C4 con una simulación de deriva (*drift*) sobre los datos históricos ordenados por fecha |
| La empresa no registra paradas | Empezar el registro en la semana 1; mientras tanto, Dₖ con supuestos documentados y análisis de sensibilidad |
| Resultados del modelo no superan al ratio | Es un resultado válido; reportar en qué procesos el ratio ya es bueno (Io bajo) y en cuáles no |
