# 03 · Potencial de publicación en revista Q1

> **Actualización tras el banco de pruebas** ([04](04_resultados_banco_pruebas.md)): en datos simulados el DSS **no supera** a la fecha del cotizador a igual plazo (necesita +4 a +7 % de plazo para igual cumplimiento) y la meta "OTD ≥ 85 % con plazo +5 %" no se alcanza. Eso cambia el relato del paper: la contribución es **cuantificar el riesgo, calibrarlo con pocos proyectos y elegir la fecha con criterio económico (α\*)**, mostrando la frontera cumplimiento-plazo, no "acertar mejor que el cotizador". Eso solo se puede afirmar o descartar con HH reales.

## Veredicto

**La idea tiene potencial Q1. El estado actual no.** El aporte metodológico es publicable: cotizar fechas de entrega de forma probabilística, con pocos datos, en una pyme MTO/ETO, bajo una penalidad asimétrica y sin tope. Pero una revista Q1 exige tres cosas que hoy faltan:

1. **Datos reales** de la variable objetivo (HH por proceso), no el ratio recalculado (ver [02](02_diagnostico_calidad_datos.md)).
2. **Validación cuantitativa** contra la práctica actual: backtest sobre proyectos pasados y, de preferencia, un piloto prospectivo con cotizaciones nuevas.
3. **Un aporte teórico explícito** más allá de "integrar herramientas conocidas". La integración (QRF + CRP + Monte Carlo + lazo cerrado) se puede presentar como novedad, pero los revisores Q1 piden una formulación que generalice.

| Escenario | Destino realista |
|---|---|
| Como está (datos sintéticos, sin validación) | Ninguno serio. Riesgo de rechazo de escritorio |
| Datos reales retrospectivos + backtest | Congreso indexado en Scopus (LACCEI, IEOM, IEEE IEEM, ICIEA) o revista Q2 (*Processes*, *Applied Sciences*, *Machines*, *Mathematics*) |
| + piloto prospectivo + aportes 1–3 de abajo | Q1: *International Journal of Production Economics*, *International Journal of Production Research*, *Production Planning & Control*, *Computers & Industrial Engineering*, *Journal of Intelligent Manufacturing*, *Engineering Applications of AI* |

> Verificar el cuartil vigente de cada revista en SJR (scimagojr.com) antes de enviar; cambia cada año y por categoría.

Ruta recomendada: **paper 1 de congreso** con el backtest (sale de la tesis) → **paper 2 a revista** con el piloto y los aportes metodológicos.

## Fortalezas actuales

- Problema real y caro: penalidad de 1 %/día sin tope; OTD de 68.4 % en 38 proyectos.
- Vacío de literatura bien argumentado: los modelos de ML para estimar tiempos (Wei et al., 2024; Hajj Chehade et al., 2024; Rokoss et al., 2024) son monofuncionales y usan datasets grandes; Ördek et al. (2024) y Guerrero et al. (2025) señalan la falta de integración y de aplicación en pymes.
- Elección técnica correcta: QRF (Meinshausen, 2006) da distribución completa y no solo un promedio. Predecir el **factor de corrección φ del ratio** en vez de las HH directas es una buena idea con pocos datos.
- Validación agrupada leave-one-project-out: evita la fuga de información entre procesos del mismo proyecto.
- Lazo de control con dos señales (error **y** calibración), activado por proyecto cerrado.

## Debilidades que un revisor Q1 señalaría

| # | Debilidad | Severidad | Cómo resolverla |
|---|---|---|---|
| D1 | Variable objetivo sintética | Bloqueante | Reconstruir HH reales desde tareos/planillas ([plan/01](../plan/01_datos_a_recolectar.md)) |
| D2 | n = 25 proyectos: los cuantiles P80/P90 estimados por QRF con 25 grupos no tienen cobertura garantizada | Alta | **Conformal prediction** (CQR, Romano et al., 2019, o jackknife+, Barber et al., 2021) sobre el QRF: da cobertura válida en muestras finitas. Es un aporte en sí mismo |
| D3 | α = 0.80 "por defecto" es arbitrario | Alta | Derivar α de la economía del problema (**cuantil crítico tipo newsvendor**), ver aporte 1 |
| D4 | En el Monte Carlo, muestrear cada proceso de forma independiente subestima la varianza del proyecto (los errores de un mismo proyecto están correlacionados: misma ingeniería, mismo cliente, mismo contratista) | Alta | Choque común por proyecto o cópula gaussiana con ρ estimada de los residuos LOPO ([diseno/05](../diseno/05_simulacion_montecarlo_crp.md)) |
| D5 | Sesgo de selección de la muestra (se excluyen 6 de 12 atrasados) | Media | Justificar cada exclusión y reportar el análisis con y sin excluidos |
| D6 | Sin comparación contra la práctica actual en condiciones reales | Alta | Backtest con la carga del taller de cada fecha + piloto en paralelo (*shadow mode*) |
| D7 | Literatura sin la línea clásica de *due-date quoting* / *due-date management* | Media | Incorporar Keskinocak & Tayur (2004) y la literatura de *lead-time quotation*; posicionar el aporte frente a ella |
| D8 | Inconsistencias internas y referencias faltantes | Media | Lista en [02 §4](02_diagnostico_calidad_datos.md) |
| D9 | Un solo caso de estudio | Media | Declararlo como limitación; diseñar el software multiempresa para replicar en 2–3 pymes (aporte 4) |

## Aportes que elevan el trabajo a nivel Q1

### Aporte 1 — Cuantil óptimo de cotización (newsvendor)

Hoy: "se usa α = 0.80". Propuesta: elegir el plazo d que minimiza el costo esperado

```
min_d  E[ c_u · (C − d)⁺ + c_o · d ]
```

- c_u = 0.01 · P por día de atraso (contractual, sin tope).
- c_o = costo marginal de ofertar un día más: pérdida de competitividad = (caída en la probabilidad de ganar la licitación por día adicional) × margen esperado.

La solución es el cuantil crítico **α\* = c_u / (c_u + c_o)**. Esto convierte el "80 %" en una decisión justificada y hace explícito el balance entre "fecha que no pierda por penalidad" y "fecha competitiva". Para estimar c_o se necesita el historial de **cotizaciones ganadas y perdidas** con su plazo ofertado (regresión logística de la probabilidad de ganar vs. plazo y precio).

Ejemplo ilustrativo (supuesto, a calibrar): si cada día extra reduce la probabilidad de ganar en 0.5 puntos y el margen es 16 %, c_o ≈ 0.0008 P, y α\* = 0.01 / 0.0108 ≈ 0.93. Con penalidades sin tope, lo óptimo sería cotizar cerca de P90, no de P80.

### Aporte 2 — Cobertura garantizada con pocos datos (QRF + conformal)

Combinar QRF con calibración conformal agrupada por proyecto. Resultado demostrable: el PICP observado queda en 0.80 ± 0.05 incluso con 25 proyectos; sin conformal, el QRF suele subcubrir. Es un resultado metodológico transferible a cualquier pyme con pocos proyectos.

### Aporte 3 — CRP de carga finita estocástico con dependencia

Monte Carlo día a día que combina: incertidumbre de HH (desde C2), disponibilidad diaria por máquina (Dₖ, TPM), plazos de servicios externos, la carga del taller (WIP) en la fecha de cotización y la correlación entre procesos de un mismo proyecto. La ablación (sin Dₖ, sin correlación, sin WIP) cuantifica cuánto aporta cada pieza.

### Aporte 4 — Artefacto replicable (Design Science Research)

Enmarcar la tesis como **Design Science Research** (Hevner et al., 2004): el artefacto es el DSS, y se evalúa por su utilidad. Un prototipo de código abierto con datos anonimizados (Zenodo/GitHub) y un formato único que otras pymes puedan llenar cumple el estándar de reproducibilidad que piden las revistas Q1.

## Métricas que el paper debe reportar

- **Predicción de HH** (LOPO): MAE, MAPE, pinball loss por cuantil, PICP y ancho medio del intervalo (MPIW), contra ratio vigente, regresión lineal múltiple, RF puntual, QRF y QRF + conformal.
- **Fechas** (backtest): OTD simulado, retraso promedio, penalidad esperada vs. real, lead time cotizado vs. histórico (restricción: aumento ≤ 5 %), calibración de P(cumplir) (Brier score).
- **Pruebas estadísticas**: Wilcoxon por pares sobre errores por proyecto; intervalos bootstrap.
- **Sensibilidad**: R (100 → 5 000 réplicas), ρ, Dₖ, α.

Diseño completo en [plan/03_diseno_experimental.md](../plan/03_diseno_experimental.md).

## Título sugerido (inglés, para el paper)

*Probabilistic due-date quoting for make-to-order metal fabrication SMEs under uncapped tardiness penalties: a quantile regression forest and finite-capacity Monte Carlo approach*

## Referencias nuevas citadas aquí (verificar datos exactos antes de citar)

- Barber, R. F., Candès, E. J., Ramdas, A., & Tibshirani, R. J. (2021). Predictive inference with the jackknife+. *The Annals of Statistics*, 49(1), 486–507.
- Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly*, 28(1), 75–105.
- Keskinocak, P., & Tayur, S. (2004). Due date management policies. En D. Simchi-Levi, S. D. Wu & Z.-J. Shen (Eds.), *Handbook of Quantitative Supply Chain Analysis* (pp. 485–554). Springer.
- Meinshausen, N. (2006). Quantile regression forests. *Journal of Machine Learning Research*, 7, 983–999.
- Romano, Y., Patterson, E., & Candès, E. (2019). Conformalized quantile regression. *Advances in Neural Information Processing Systems*, 32.
