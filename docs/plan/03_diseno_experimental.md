# 03 · Diseño experimental y validación

Cómo demostrar que el DSS es mejor que la práctica actual, con el rigor que pide una revista Q1.

## Estado de implementación

| Experimento | Estado | Script | Resultados |
|---|---|---|---|
| 1 · Predicción de HH (LOPO) | ✅ sobre datos simulados | `scripts/exp1_prediccion.py` | `data/exp1_resultados.csv`, [analisis/04](../analisis/04_resultados_banco_pruebas.md) |
| 2 · Backtest de cotización | ✅ sobre datos simulados (variantes A0, A5, A6, A7) | `scripts/exp2_backtest.py`, `exp3_frontera.py` | `data/exp2_backtest.csv`, `data/exp3_frontera*.csv` |
| 2 · Ablación y competidor de colchón fijo (sin conformal, sin Dₖ, sin carga del taller, ρ = 0, sin variables) | ✅ sobre datos simulados, 5 escenarios | `scripts/exp4_ablacion.py` | `data/exp4_ablacion*.csv`, [analisis/04](../analisis/04_resultados_banco_pruebas.md) |
| 3 · Piloto prospectivo (*shadow mode*) | ⏳ requiere cotizaciones reales | — | — |
| 4 · Sensibilidad: Dₖ | ✅ escenario M5 (≈ 80 %) | `dss/simulador.py` | idem |
| 4 · Sensibilidad: R, ρ, α, κ de la carga del taller, σ de plazos externos, c_o | ⏳ pendiente | — | — |
| 5 · Retrospectivo «cómo se hizo vs. qué habría pasado» (6 políticas, palancas de gestión, sensibilidad al costo) | ✅ línea base histórica real; contrafactuales sobre variables simuladas | `scripts/exp5_retrospectivo.py` | `data/exp5_*.csv`, [analisis/08](../analisis/08_retrospectivo_planta3d.md) |
| 6 · Calibración condicional por tamaño (conformal Mondrian) | ⏳ pendiente; motivado por los experimentos 4 y 5 (el pronóstico es pesimista y la calibración no es por tamaño) | — | — |
| 7 · Experimento con usuarios 2D vs. 3D (tiempo y calidad de decisión, SUS) | ⏳ pendiente; ver [plan/05](05_planta_3d.md) | — | — |

Los experimentos 1 y 2 usan **datos simulados**; sus resultados validan el pipeline, no el desempeño en Steelser.

## Hipótesis

- **H1 (C2)**: el QRF sobre φ estima las HH por proceso con menor error que el ratio vigente.
- **H2 (C2)**: el intervalo P10–P90 calibrado tiene cobertura de 0.80 ± 0.05.
- **H3 (C3)**: las fechas cotizadas con el DSS habrían alcanzado OTD ≥ 85 % con un aumento del lead time cotizado ≤ 5 %.
- **H4 (C3)**: considerar Dₖ, la carga del taller y la correlación entre procesos mejora la calibración de P(cumplir) frente a omitirlos.

## Experimento 1 · Predicción de HH (H1, H2)

- **Unidad**: registro proyecto × proceso; **validación**: leave-one-project-out (`LeaveOneGroupOut` con grupo = proyecto). Ningún proceso del proyecto de prueba se usa para entrenar.
- **Modelos**:
  1. Ratio vigente (línea base = práctica actual)
  2. Regresión lineal múltiple sobre log φ
  3. Random Forest puntual
  4. QRF
  5. QRF + calibración conformal (propuesto)
  6. (opcional) Gradient boosting cuantílico (LightGBM) como modelo alternativo
- **Métricas** por proceso y a nivel proyecto (suma de procesos): MAE, MAPE, RMSE, pinball loss en τ = 0.1/0.5/0.8/0.9, PICP, MPIW.
- **Prueba estadística**: Wilcoxon de rangos con signo pareado por proyecto (modelo vs. ratio) sobre el error absoluto a nivel proyecto; intervalos de confianza por bootstrap de proyectos (2 000 remuestreos).
- **Hiperparámetros**: búsqueda pequeña anidada dentro de cada fold (n_estimators 500–1 000, min_samples_leaf 3–10, max_features). Con pocos datos, preferir hojas grandes.
- **Importancia de variables**: permutación agrupada, reportada pero sin sobreinterpretar con N pequeño.

## Experimento 2 · Backtest de cotización (H3, H4)

Reproducir "qué habría cotizado el DSS" para cada proyecto pasado, usando solo información disponible a su fecha de inicio:

1. Ordenar los proyectos por fecha de inicio.
2. Para cada proyecto i (desde el 8.º, para tener un mínimo de entrenamiento): entrenar C2 solo con proyectos **terminados** antes de su inicio (*rolling origin*).
3. Reconstruir la carga del taller en esa fecha con los proyectos activos (Tabla 3).
4. Correr C3 → d_α; comparar con la fecha real de fin.
5. Contar si se habría cumplido (C_real ≤ d_α), el retraso y la penalidad, y el lead time cotizado vs. el que se ofertó de verdad.

**Métricas**: OTD, retraso promedio, penalidad promedio, Δ lead time cotizado, Brier score y diagrama de calibración de P(cumplir).

**Ablación** (cada una quita una pieza del modelo):

| Variante | Qué se quita |
|---|---|
| A0 | Práctica actual: ratio + capacidad al 100 % |
| A1 | QRF sin Monte Carlo (fecha = suma de P50 / capacidad) |
| A2 | Monte Carlo con D = 1 (sin TPM) |
| A3 | Monte Carlo sin WIP (taller vacío) |
| A4 | Monte Carlo con ρ = 0 (procesos independientes) |
| A5 | Modelo completo con α = 0.80 |
| A6 | Modelo completo con α\* (newsvendor) |

## Experimento 3 · Piloto prospectivo (*shadow mode*)

Durante la fase 5, cada cotización real se hace por duplicado: el cotizador con su método y el DSS en paralelo, sin que el DSS influya en la oferta. Para los proyectos que se adjudiquen y terminen en el periodo de la tesis, comparar ambas fechas con la real. Aunque sean pocos casos (3–6), es la evidencia más fuerte para el paper.

Registrar también el tiempo que toma cotizar (QLT) con y sin el DSS.

## Experimento 4 · Sensibilidad

- R ∈ {100, 500, 1 000, 2 000, 5 000}: estabilidad de d_α.
- ρ ∈ {0, 0.2, 0.4, 0.6}; Dₖ ± 10 puntos; α ∈ [0.5, 0.95].
- Umbrales de depuración (L, U) y del lazo (Md, PICP).

## Reproducibilidad

- Semilla fija y registrada en `simulacion.semilla` y `modelo_version`.
- Código versionado (Git) y BD con datos anonimizados (clientes como C01…C38) publicables en Zenodo al enviar el paper.
- Cada tabla y figura de la tesis generada por un script, no a mano.

## Amenazas a la validez (declararlas)

- **Interna**: datos reconstruidos de tareos; sesgo de selección de la muestra.
- **Externa**: un solo caso de estudio; tipología de proyectos de Steelser.
- **De constructo**: OTD medido sobre la fecha contractual, que pudo ampliarse por causas del cliente (ver cláusulas de la propuesta técnica).
- **Conclusión**: N pequeño → reportar intervalos, no solo puntos.
