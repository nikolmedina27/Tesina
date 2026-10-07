# 04 · Modelo matemático

Reconstrucción de las **Ecuaciones 4–15** que el Cap. III de la tesis cita (la 4 está como texto plano; las 5–15 no están en el Word), más cuatro ecuaciones nuevas (16–19) que fortalecen el modelo para una revista Q1. Copiar al Word con el editor de ecuaciones y renumerar desde 1.

## Estado de implementación

| Ecuación | Dónde |
|---|---|
| 7, 8, 9, 17 (QRF, φ, conformal) | `dss/c2_modelo.py` (`PhiQRF`); la calibración usa GroupKFold por proyecto en vez de LOPO exacto |
| 10, 11, 19 (Dₖ, capacidad, disponibilidad estocástica) | `dss/crp_engine.py`, `dss/c3_montecarlo.py::muestrear_disp` (eventos de falla en lugar de Beta; ver [05](05_simulacion_montecarlo_crp.md)) |
| 12, 13, 16 (fecha α, penalidad esperada, α\*) | `dss/c3_montecarlo.py` (`Resultado`, `alpha_optimo`) |
| 18 (cópula entre procesos) | `dss/c3_montecarlo.py::muestrear_phi`; ρ estimado por ANOVA en `c2_modelo.estimar_rho` |
| 4, 5, 6 (C1: TS, filtro, Io) | ⏳ pendiente (`c1_datos`) |
| 14, 15 (Md, PICP, regla de reentrenamiento) | ⏳ pendiente (`c4_lazo`); el PICP ya se mide en `scripts/exp1_prediccion.py` |

## Notación

| Símbolo | Significado |
|---|---|
| i | proyecto (i = 1…N, hoy N = 25) |
| j | proceso (j = 1…13) |
| k | máquina (k = 1…4: sierra cinta, cizalladora-punzonadora, mesa CNC, roscadora) |
| Qᵢ | toneladas del metrado del proyecto i |
| HH^real_ij | horas-hombre reales del proceso j en el proyecto i |
| HH^ratio_ij = Qᵢ · ρ_{tipo(i), j} | HH del ratio vigente (práctica actual) |
| xᵢⱼ | vector de variables del proyecto y del proceso |
| P | presupuesto del contrato |
| p = 0.01 | penalidad diaria como fracción de P |
| R | número de réplicas de Monte Carlo (1 000) |
| α | cuantil con que se cotiza |

---

## C1 · Estandarización y curaduría de datos

**Ec. 4 — Tiempo estándar**

$$TS_j = TO_j \cdot FR_j \cdot (1 + S_j)$$

TO = tiempo observado promedio (cronometraje), FR = factor de ritmo (Westinghouse u OIT), S = suplementos por fatiga y necesidades personales. Unidad según el proceso: h/t, h/pieza, h/m² o h/m de soldadura.

**Ec. 5 — Filtro de depuración**

$$r_{ij} = \frac{HH^{real}_{ij}}{TS_j \cdot Q_{ij}}, \qquad \text{se conserva el registro si } L \le r_{ij} \le U$$

Valores iniciales L = 0.5, U = 2.0 (a calibrar). Los registros fuera de rango se revisan (tiempos muertos, errores de tareo, condiciones atípicas) antes de descartarlos; nunca se descartan en silencio.

**Ec. 6 — Índice de Obsolescencia del Ratio**

$$Io_j = \frac{1}{N_j} \sum_{i=1}^{N_j} \frac{\left| HH^{ratio}_{ij} - HH^{real}_{ij} \right|}{HH^{real}_{ij}}$$

Es el MAPE del ratio vigente para el proceso j. Mide obsolescencia por error, no por antigüedad.

---

## C2 · Predicción de HH con Quantile Regression Forest

**Ec. 7 — Random Forest (Breiman, 2001)**

$$\hat{y}(x) = \frac{1}{B} \sum_{b=1}^{B} T_b(x)$$

**Ec. 8 — Quantile Regression Forest (Meinshausen, 2006)**

$$w_m(x) = \frac{1}{B} \sum_{b=1}^{B} \frac{\mathbb{1}\{X_m \in \ell_b(x)\}}{\left|\ell_b(x)\right|}, \qquad \hat{F}(y \mid x) = \sum_{m} w_m(x)\, \mathbb{1}\{Y_m \le y\}$$

$$\hat{q}_\tau(x) = \inf\{\, y : \hat{F}(y \mid x) \ge \tau \,\}$$

ℓ_b(x) es la hoja del árbol b donde cae x; w_m(x) es el peso de la observación histórica m según su parecido con el proyecto nuevo.

**Ec. 9 — Factor de corrección del ratio**

$$\varphi_{ij} = \frac{HH^{real}_{ij}}{HH^{ratio}_{ij}}, \qquad \widehat{HH}_{ij,\tau} = HH^{ratio}_{ij} \cdot \hat{q}^{\varphi}_{\tau}(x_{ij})$$

El modelo aprende φ (cuánto y cuándo se equivoca el ratio), no las HH desde cero. Como los cuantiles son equivariantes a transformaciones monótonas, se puede entrenar sobre log φ sin cambiar la interpretación.

Variables xᵢⱼ: proceso (one-hot), tipo de estructura, toneladas, n° de piezas, peso medio por pieza, % de planchas, m² de pintura, acabado, montaje (sí/no), contratista, año, ratio vigente.

**Ec. 17 (nueva) — Calibración conformal del intervalo (Romano et al., 2019)**

Con la validación leave-one-project-out se obtiene, para cada registro, el *score*

$$E_{ij} = \max\left\{ \hat{q}^{(-i)}_{0.10}(x_{ij}) - \varphi_{ij},\; \varphi_{ij} - \hat{q}^{(-i)}_{0.90}(x_{ij}) \right\}$$

donde (−i) indica el modelo entrenado sin el proyecto i. Sea Ê el cuantil ⌈(1−β)(N+1)⌉/N de los scores (agregados por proyecto, tomando el máximo o la media por proyecto para respetar la dependencia). El intervalo calibrado es

$$\left[\, \hat{q}_{0.10}(x) - \hat{E},\; \hat{q}_{0.90}(x) + \hat{E} \,\right]$$

con cobertura ≥ 1 − β garantizada en muestra finita bajo intercambiabilidad de proyectos. Con 1 − β = 0.80 esto asegura el PICP de la meta.

---

## C3 · CRP de carga finita ajustado por disponibilidad

**Ec. 10 — Disponibilidad por máquina (Nakajima, 1988)**

$$D_k = \frac{TP_k - T^{paradas}_k}{TP_k}$$

TP_k = tiempo programado; T^paradas = paradas planificadas y no planificadas.

**Ec. 11 — Capacidad diaria por centro de trabajo**

$$Cap_{k,t} = H_{turno} \cdot n_{turnos} \cdot D_{k,t} \quad \text{(máquinas, h-máquina/día)}$$

$$Cap_{c,t} = n_{c,t} \cdot h_{c,t}, \quad n_{min} \le n_{c,t} \le n_{max} \quad \text{(contratista, HH/día)}$$

Los servicios externos no tienen capacidad sino un plazo L_s que se muestrea de su historial. Las horas extra del contratista no generan costo para la empresa (las asume el contratista), por eso entran como mayor h_c,t y no como costo.

**Ec. 19 (nueva) — Disponibilidad diaria estocástica**

$$D_{k,t}^{(r)} \sim \text{Beta}(a_k, b_k) \quad \text{o remuestreo bootstrap de la disponibilidad diaria histórica}$$

con a_k, b_k ajustados por momentos a la media y varianza de la disponibilidad diaria registrada en `parada_maquina` y `calendario_planta`.

**Ec. 18 (nueva) — Dependencia entre procesos de un mismo proyecto**

Las HH de los 13 procesos de un proyecto no son independientes. En cada réplica r:

$$Z^{(r)}_{j} = \sqrt{\rho}\; \eta^{(r)} + \sqrt{1-\rho}\; \varepsilon^{(r)}_{j}, \quad \eta, \varepsilon \sim N(0,1), \qquad U_j = \Phi(Z_j), \qquad HH^{(r)}_{j} = \hat{F}_j^{-1}(U_j)$$

η es un choque común del proyecto, ρ se estima con la correlación promedio de los residuos LOPO dentro de un mismo proyecto. Con ρ = 0 se recupera el muestreo independiente de la tesis; la ablación ρ = 0 vs. ρ estimado es un resultado del paper.

**Ec. 12 — Fecha cotizada**

$$d_\alpha = \inf\left\{ d : \frac{1}{R} \sum_{r=1}^{R} \mathbb{1}\{C^{(r)}_n \le d\} \ge \alpha \right\}$$

C_n^(r) es la fecha de fin del proyecto nuevo n en la réplica r.

**Ec. 13 — Penalidad esperada**

$$\mathbb{E}[Pen(d)] = p \cdot P \cdot \frac{1}{R} \sum_{r=1}^{R} \left( C^{(r)}_n - d \right)^{+}$$

y la probabilidad de cumplir: P(C_n ≤ d) = (1/R) Σ 𝟙{C_n^(r) ≤ d}.

**Ec. 16 (nueva) — Cuantil óptimo de cotización (newsvendor)**

$$\min_d \; \mathbb{E}\left[ c_u (C_n - d)^+ \right] + c_o \, d \quad \Rightarrow \quad \alpha^* = \frac{c_u}{c_u + c_o}$$

c_u = p · P (costo por día de atraso). c_o = costo por día de plazo ofertado adicional = (∂ Pr[ganar] / ∂ d) · margen · P. Si no se puede estimar c_o, se reporta la curva completa (d, P(cumplir), E[Pen]) para todo α ∈ [0.5, 0.95] y se usa α = 0.80 como valor por defecto, declarándolo como supuesto.

---

## C4 · Lazo de control cerrado

**Ec. 14 — Índice de Deriva del Modelo**

$$M_d = \frac{MAE_{rec} - MAE_0}{MAE_0}$$

MAE_0 = error LOPO del entrenamiento; MAE_rec = error de los proyectos cerrados desde el último entrenamiento (sobre HH por proceso, en la escala de HH).

**Ec. 15 — Cobertura del intervalo de predicción**

$$PICP = \frac{1}{n} \sum_{m=1}^{n} \mathbb{1}\left\{ \widehat{HH}_{m,0.10} \le HH^{real}_m \le \widehat{HH}_{m,0.90} \right\}$$

**Regla de reentrenamiento**

$$\text{alerta} \iff \left( M_d > 0.30 \;\wedge\; n_{nuevos} \ge 3 \right) \;\vee\; PICP_{rec} < 0.70$$

Umbrales en la tabla `parametro` (`md_umbral`, `min_proyectos_reentreno`, `picp_min`).

---

## Indicadores de evaluación (Cap. III, 3.4.1)

| Indicador | Fórmula | Línea base | Meta |
|---|---|---|---|
| OTD | proyectos con C ≤ d / total | 68.4 % (38) · 76.0 % (muestra 25) | ≥ 85 % |
| Retraso promedio | (1/N) Σ (C − d)⁺ | 2.29 d (38) · 1.20 d (25) | ≤ 0.5 d |
| Penalidad promedio de atrasados | p · retraso | 7.25 % (38) · 5.0 % (25) | ≤ 3 % |
| Lead time cotizado | promedio de d − inicio | ≈ 70 días calendario (38) | aumento ≤ 5 % |
| PICP | Ec. 15 | — | 0.80 ± 0.05 |
| Dₖ | Ec. 10 | por medir | ≥ 90 % |
| Io | Ec. 6 | por medir | menor que el del ratio |

> La tesis reporta 71.4 %, 1.71 d y 6.0 % sobre "28 proyectos", cifras que no coinciden con ningún archivo; usar las de esta tabla (calculadas en `data/steelser.db`) o documentar el origen de las 28.
