# 04 · Resultados en el banco de pruebas (datos SIMULADOS)

> **Todos estos resultados salen de datos simulados** ([diseno/06](../diseno/06_datos_simulados.md)). Muestran que el pipeline funciona y cómo se comporta el método bajo supuestos conocidos. **No son evidencia sobre Steelser.** Se regeneran con `scripts/exp1_prediccion.py`, `exp2_backtest.py`, `exp3_frontera.py` y `exp4_ablacion.py` (resultados en `data/*.csv`). Los experimentos 2 y 3 se corrieron con los 4 primeros escenarios; el 1 y el 4 incluyen el escenario M5 (disponibilidad ≈ 80 %).

> Para el estudio retrospectivo «cómo se hizo vs. qué habría pasado» (palancas de gestión, 6 políticas, base reconstruida) ver [08](08_retrospectivo_planta3d.md). Sus números no coinciden con los de este documento porque usa la BD reconstruida de la PC de Paolo.

## Resumen en cinco líneas

1. **C2 funciona**: el QRF reduce el error de HH frente al ratio vigente en los escenarios con sesgo o no linealidad, no lo empeora cuando el ratio ya es bueno (M1), y con la calibración conformal el intervalo P10–P90 alcanza cobertura ≈ 0.80.
2. **C3 funciona y es rápido**: 1 000 réplicas por cotización en ≈ 0.2 s. Los cuantiles quedan calibrados: la fecha cotizada con α = 0.80 se cumple 76–84 % de las veces.
3. **No hay evidencia de que la fecha del DSS supere a la del cotizador a igual plazo.** El plan manual real (76 % de cumplimiento con 0 % de plazo extra) queda en o por encima de la frontera del método. Con N = 25 los intervalos se traslapan, así que tampoco se puede afirmar lo contrario.
4. **La meta "OTD ≥ 85 % con plazo +5 %" no se alcanza** en este banco de pruebas. Con α = 0.85 se llega a 84–88 % de cumplimiento con +8 a +11 % de plazo.
5. **El valor del DSS es otro**: dice con qué probabilidad se cumple cualquier fecha (el plan del cotizador tiene en promedio ≈ 50 % de probabilidad según el modelo, aunque se cumplió 76 %), calcula la penalidad esperada y deja elegir el punto de la frontera con criterio económico.
6. **Un colchón fijo iguala al Monte Carlo en la frontera** (experimento 4): plan determinista con la carga del taller + N días necesita 6.3 % de plazo extra para 80 % de cumplimiento contra 6.9 % del Monte Carlo completo. Lo que sí aporta es la **carga del taller**; la distribución aporta **calibración interpretable** (α → cumplimiento observado), no una frontera mejor. Hay un punto débil: la calibración es **marginal y no por tamaño de proyecto** (los chicos cumplen 67 % cuando se prometió 80 %).

## Experimento 1 · Predicción de HH (leave-one-project-out, 25 proyectos)

Error porcentual absoluto medio de las HH totales del proyecto (menor es mejor):

| Escenario | Ratio vigente | Regresión lineal | RF puntual | Empírico | GBM cuantílico | QRF | QRF + conformal |
|---|---|---|---|---|---|---|---|
| M1 | 4.4 % | 4.9 % | 4.3 % | 4.0 % | 4.4 % | 4.4 % | 4.4 % |
| M2 | 7.4 % | 6.8 % | 4.9 % | 7.7 % | 5.3 % | 5.4 % | 5.4 % |
| M3 | 8.7 % | 9.6 % | 8.8 % | 8.8 % | 8.9 % | 8.5 % | 8.5 % |
| M4 | 8.7 % | 7.8 % | 8.0 % | 8.8 % | 8.2 % | 8.1 % | 8.1 % |
| M5 | 11.1 % | 8.8 % | 9.1 % | 9.2 % | 10.1 % | 9.5 % | 9.5 % |

Cobertura del intervalo P10–P90 (meta 0.80 ± 0.05):

| Escenario | Empírico | GBM cuantílico | QRF | QRF + conformal |
|---|---|---|---|---|
| M1 | 0.74 | 0.66 | 0.73 | 0.80 |
| M2 | 0.75 | 0.69 | 0.79 | 0.81 |
| M3 | 0.75 | 0.62 | 0.70 | 0.78 |
| M4 | 0.74 | 0.64 | 0.77 | 0.79 |
| M5 | 0.73 | 0.64 | 0.73 | 0.81 |

- **En error puntual el QRF no es el mejor**: el RF puntual gana en M2 (4.9 % vs 5.4 %) y la regresión lineal en M4 y M5. Se elige QRF por la distribución completa que necesita C3, no por exactitud.
- El **GBM cuantílico** (el tipo de modelo de Bekci et al. 2022) tiene error parecido al QRF pero **subcubre mucho** el intervalo (0.62–0.69 frente a 0.80 deseado): con 25 proyectos los intervalos de los modelos cuantílicos sin calibrar no son confiables.
- El **conformal** corrige la subcobertura del QRF (0.70–0.79 → 0.78–0.81) en los 5 escenarios.
- En M5 (disponibilidad baja) el ratio vigente empeora (11.1 %) porque la verdad simulada queda con φ medio menor; todos los modelos lo mejoran.

## Experimento 2/3 · Backtest de fechas (rolling origin, 25 proyectos)

Para cada proyecto, en orden cronológico, se cotiza solo con lo que se sabía a su fecha de inicio: proyectos terminados (entrenamiento), proyectos en curso (carga del taller) y paradas registradas hasta entonces. Se compara con la fecha de fin **real** (Tabla 3).

- **Plazo cotizado vs. plan**: promedio del plazo en días calendario del DSS dividido entre el plazo que cotizó el cotizador (66.6 días de promedio).
- IC 95 % por bootstrap de proyectos (con 25 proyectos el cumplimiento avanza en saltos de 4 puntos).

### Auditando el plan del cotizador (el DSS recibe sus cuadrillas y plazos externos)

| Escenario | Método | OTD [IC 95 %] | Plazo cotizado vs. plan del cotizador | Retraso medio (días) |
|---|---|---|---|---|
| M1 | Criterio del cotizador (real) | 76 % [56–92] | 0 % | 1.20 |
| M1 | DSS α = 0.50 | 64 % [44–84] | +2.3 % | 1.20 |
| M1 | DSS α = 0.70 | 84 % [68–96] | +5.2 % | 0.68 |
| M1 | DSS α = 0.80 | 84 % [68–96] | +7.4 % | 0.48 |
| M1 | DSS α = 0.90 | 88 % [72–100] | +10.1 % | 0.24 |
| M1 | DSS α = 0.93 | 92 % [80–100] | +11.3 % | 0.20 |
| M2 | Criterio del cotizador (real) | 76 % [60–92] | 0 % | 1.20 |
| M2 | DSS α = 0.50 | 56 % [36–76] | +1.1 % | 1.88 |
| M2 | DSS α = 0.70 | 72 % [52–88] | +5.4 % | 1.04 |
| M2 | DSS α = 0.80 | 80 % [64–96] | +7.9 % | 0.80 |
| M2 | DSS α = 0.90 | 88 % [76–100] | +11.2 % | 0.40 |
| M2 | DSS α = 0.93 | 88 % [76–100] | +12.7 % | 0.32 |
| M3 | Criterio del cotizador (real) | 76 % [56–92] | 0 % | 1.20 |
| M3 | DSS α = 0.50 | 52 % [32–72] | +1.5 % | 1.76 |
| M3 | DSS α = 0.70 | 76 % [60–92] | +5.9 % | 0.84 |
| M3 | DSS α = 0.80 | 80 % [64–96] | +9.3 % | 0.44 |
| M3 | DSS α = 0.90 | 88 % [72–100] | +13.3 % | 0.16 |
| M3 | DSS α = 0.93 | 92 % [80–100] | +14.9 % | 0.08 |
| M4 | Criterio del cotizador (real) | 76 % [60–92] | 0 % | 1.20 |
| M4 | DSS α = 0.50 | 40 % [20–60] | +1.1 % | 1.64 |
| M4 | DSS α = 0.70 | 80 % [64–96] | +5.8 % | 0.56 |
| M4 | DSS α = 0.80 | 84 % [68–96] | +8.7 % | 0.32 |
| M4 | DSS α = 0.90 | 96 % [88–100] | +12.3 % | 0.04 |
| M4 | DSS α = 0.93 | 100 % [100–100] | +14.1 % | 0.00 |

### Con cuadrilla y plazos externos típicos según toneladas

| Escenario | Método | OTD [IC 95 %] | Plazo cotizado vs. plan del cotizador | Retraso medio (días) |
|---|---|---|---|---|
| M1 | Criterio del cotizador (real) | 76 % [56–92] | 0 % | 1.20 |
| M1 | DSS α = 0.50 | 56 % [36–76] | +1.8 % | 1.72 |
| M1 | DSS α = 0.70 | 68 % [52–84] | +4.8 % | 1.00 |
| M1 | DSS α = 0.80 | 80 % [64–96] | +6.9 % | 0.48 |
| M1 | DSS α = 0.90 | 88 % [72–100] | +9.4 % | 0.24 |
| M1 | DSS α = 0.93 | 88 % [76–100] | +10.6 % | 0.16 |
| M2 | Criterio del cotizador (real) | 76 % [60–92] | 0 % | 1.20 |
| M2 | DSS α = 0.50 | 52 % [32–72] | +0.9 % | 2.20 |
| M2 | DSS α = 0.70 | 72 % [56–88] | +4.6 % | 1.28 |
| M2 | DSS α = 0.80 | 76 % [60–92] | +7.4 % | 0.88 |
| M2 | DSS α = 0.90 | 84 % [68–96] | +10.7 % | 0.48 |
| M2 | DSS α = 0.93 | 84 % [68–96] | +12.3 % | 0.32 |
| M3 | Criterio del cotizador (real) | 76 % [56–92] | 0 % | 1.20 |
| M3 | DSS α = 0.50 | 52 % [32–72] | +1.0 % | 2.32 |
| M3 | DSS α = 0.70 | 68 % [48–84] | +5.7 % | 1.00 |
| M3 | DSS α = 0.80 | 80 % [64–96] | +8.8 % | 0.48 |
| M3 | DSS α = 0.90 | 92 % [80–100] | +12.7 % | 0.12 |
| M3 | DSS α = 0.93 | 92 % [80–100] | +14.3 % | 0.08 |
| M4 | Criterio del cotizador (real) | 76 % [60–92] | 0 % | 1.20 |
| M4 | DSS α = 0.50 | 36 % [20–56] | +0.3 % | 2.20 |
| M4 | DSS α = 0.70 | 72 % [52–88] | +5.3 % | 0.72 |
| M4 | DSS α = 0.80 | 84 % [68–96] | +8.0 % | 0.32 |
| M4 | DSS α = 0.90 | 96 % [88–100] | +11.9 % | 0.08 |
| M4 | DSS α = 0.93 | 100 % [100–100] | +13.7 % | 0.00 |

### Lectura

- **A igual cumplimiento (76 %) el DSS necesita entre +4 % y +7 % más de plazo** que el cotizador real (si se le da su plan de cuadrillas; más si no). El criterio del cotizador ya es bueno: la desviación real es pequeña (el 76 % termina a tiempo y el peor atraso es de 8 días).
- **A mayor confianza el método sí controla el riesgo**: con α = 0.90 el cumplimiento es 88–96 % y el retraso medio baja de 1.2 días a 0.04–0.4 días, a cambio de +10 a +13 % de plazo.
- **Calibración**: la fecha con α = 0.80 se cumplió 76–84 % de las veces (meta 80 %). En cambio, el plan manual del cotizador tiene en el modelo ≈ 47–53 % de probabilidad de cumplirse; se cumplió 76 %. Es decir, el método tiene incertidumbre algo mayor que la observada en esta muestra: es conservador.
- **Valor económico**: con penalidad de 1 %/día y un costo de plazo largo de 0.08 % del presupuesto por día (supuesto: perder 0.5 puntos de probabilidad de ganar por día × margen 16 %), el ahorro neto por proyecto de pasar del plan manual a α = 0.90 es del orden de **0.2–0.5 % del presupuesto**. Es pequeño y sensible al supuesto, que debe medirse con las cotizaciones ganadas y perdidas.

## Experimento 4 · Ablaciones, colchón fijo y sensibilidad a la disponibilidad

**Diseño.** Mismo backtest causal, 5 escenarios × 25 proyectos = 125 cotizaciones, y el DSS recibe las cuadrillas y plazos externos del cotizador. Cada método se barre (α de 0.50 a 0.97, o colchón de 0 a 15 días laborables) y se mide el **plazo extra (% sobre el plazo del cotizador) que necesita para llegar a 80 % y a 90 % de cumplimiento**, interpolado en la curva. IC 95 % por bootstrap de proyectos (300 remuestras). El cotizador real queda en 76 % con 0 % de plazo extra.

- **Colchón fijo**: plan determinista con la mediana de φ, disponibilidad esperada y carga del taller, más N días laborables (estilo Mundt & Lödding).
- **MC completo**: QRF + conformal, Dₖ, carga del taller y ρ estimado.
- Las demás filas quitan una pieza del MC completo.

| Método | Plazo extra para 80 % [IC] | Plazo extra para 90 % [IC] | Remuestras que no llegan a 90 % |
|---|---|---|---|
| Colchón fijo (plan + N días) | 6.3 % [3.0–10.5] | 9.9 % [6.0–13.4] | 0 % |
| MC completo | 6.9 % [3.4–12.6] | 12.8 % [6.1–16.4] | 0.3 % |
| MC sin conformal | 6.9 % [3.8–12.4] | 12.4 % [6.0–16.6] | 0 % |
| MC sin disponibilidad | 7.4 % [3.6–11.6] | 12.0 % [6.4–14.9] | **15.0 %** |
| MC sin carga del taller | **9.1 %** [3.6–12.4] | 12.8 % [7.3–15.5] | 1.0 % |
| MC con ρ = 0 | 7.1 % [3.7–12.3] | 12.2 % [5.8–15.5] | **15.3 %** |
| MC sin variables (empírico) | 7.2 % [3.7–13.9] | 13.1 % [6.5–18.1] | 8.3 % |

Plazo extra (%) para llegar a 80 % de cumplimiento, por escenario:

| Método | M1 | M2 | M3 | M4 | M5 (D ≈ 80 %) |
|---|---|---|---|---|---|
| Colchón fijo | 4.3 | 6.1 | 6.6 | 6.3 | 6.2 |
| MC completo | 5.3 | 8.6 | 9.8 | 6.1 | 6.5 |
| MC sin carga del taller | 9.2 | 9.4 | 11.1 | 9.2 | 7.2 |
| MC sin variables (empírico) | 6.7 | 6.9 | 6.2 | 6.1 | 7.6 |

**Calibración del MC completo** (los 5 escenarios juntos): α = 0.70 → 79 % de cumplimiento, 0.80 → 83 %, 0.90 → 90 %, 0.95 → 96 %. Es **interpretable de antemano**. El colchón fijo no: 4 días → 79 %, 6 días → 89 %, 8 días → 97 %, y el valor correcto hay que descubrirlo con historia.

### Lectura

1. **En la frontera media no hay diferencia demostrable** entre el colchón fijo y el Monte Carlo (los IC se solapan por completo); en las estimaciones puntuales el colchón es incluso mejor al 90 %. Hay que decirlo así: el aporte de la distribución **no** es una mejor relación cumplimiento-plazo en este banco.
2. **La pieza que más aporta es la carga del taller**: quitarla cuesta +2.2 puntos de plazo (y +3.9 en M1). Es consistente con la advertencia de Rokoss de que el estado de planta (WIP) es el que reduce el error.
3. **Dₖ y ρ no mueven la mediana, pero sí la cola**: sin ellos, 15 % de las remuestras ya no logra 90 % de cumplimiento con ninguna confianza. Son necesarias para prometer niveles altos de confiabilidad.
4. **El conformal no cambia la frontera de fechas**; su efecto está en la cobertura del intervalo de HH (experimento 1).
5. **QRF contra empírico** (con o sin variables del plano): ≈ 0.3 puntos de diferencia, no distinguibles. Con las HH simuladas el modelo de horas casi no cambia el plazo; con datos reales puede ser distinto.
6. **Disponibilidad baja (M5)**: no se observa degradación (6.5 % de plazo extra frente a 5.3–9.8 % en M1–M4) porque el MTBF se aprende de las paradas registradas. Sin ese registro no se puede cotizar con riesgo calibrado.
7. **Hallazgo negativo: la calibración no es uniforme por tamaño.** Con α = 0.80, los proyectos chicos (tercil inferior de toneladas) cumplen **67 %**, los medianos 85 % y los grandes 100 %. El colchón fijo de 6 días muestra el mismo patrón (82 %, 85 %, 100 %). Es la limitación principal a resolver: conformal condicional por tamaño (Mondrian) o puntajes normalizados, y varianza que dependa del tamaño.

## Qué significa para la tesis y un paper

1. **No prometer** "OTD ≥ 85 % con plazo +5 %". Reformular la meta como: *cuantificar el riesgo de cada fecha, alcanzar OTD ≥ 85 % con el menor plazo adicional posible y reducir la penalidad esperada*; reportar la frontera completa (como en las tablas de arriba) y dejar al decisor elegir el punto.
2. **La contribución sólida** es metodológica: cotización con distribución completa, intervalo calibrado con pocos proyectos, α\* económico y frontera cumplimiento-plazo. No es "el DSS acierta mejor que el cotizador" (hoy no hay evidencia).
3. **Para que el DSS gane a igual plazo hace falta información que hoy el modelo no tiene**: HH reales (reducen φ), paradas reales, plazos reales de proveedores y la cuadrilla efectivamente asignada. Con los tareos reales el resultado puede cambiar en cualquier dirección; hay que correr los mismos experimentos con ellos.
4. **El banco de pruebas es un límite superior optimista en un aspecto y pesimista en otro**: la verdad simulada tiene la misma estructura que el modelo (favorable al DSS), pero la incertidumbre se calibró a los datos reales de duración (el plan manual es muy preciso en el pasado, desfavorable al DSS). No se puede sacar una conclusión sobre Steelser de aquí.
5. **Con 25 proyectos el poder estadístico es bajo**: un IC de ±16 puntos en el cumplimiento. Aumentar la muestra (los 13 excluidos, proyectos nuevos) es tan importante como los datos reales.

## Pendiente

- Repetir todo con HH reales (reconstruidas de tareos) y paradas reales.
- Sensibilidad: κ de la carga del taller, σ del plazo externo, MTBF y supuesto de c_o (la disponibilidad ya se probó con M5).
- **Calibración condicional por tamaño** (conformal Mondrian o puntajes normalizados) y repetir el experimento 4.
- Repetir los experimentos 2 y 3 con M5 incluido.
- Lazo cerrado C4 sobre el escenario M4 (deriva).
- Competidor NGBoost (no instalado) y colchón proporcional a la duración como variante del colchón fijo.
