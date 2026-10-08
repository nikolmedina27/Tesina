# 09 · Resultados: el DSS evaluado contra el gemelo de eventos discretos

> **Todo es SIMULADO.** La «verdad» es el gemelo hora a hora de [diseno/08](../diseno/08_gemelo_planta.md), calibrado a las fechas reales de la Tabla 3. Sirve para probar el pipeline y para saber qué esperar con datos reales; no es evidencia sobre Steelser. Reemplaza al estudio retrospectivo de [08](08_retrospectivo_planta3d.md), cuya «verdad» salía del mismo motor que el DSS (circular).

## Qué se hizo

1. Se generó la historia 2019–2026 de los 38 proyectos (9 162 lotes, 1 425 paradas de máquina) y se **calibró el gemelo**: con la política «como se hizo» reproduce el cumplimiento de la muestra (76 %, igual que la realidad) con un error medio de ≈ 2 días laborables por proyecto.
2. Se corrió **toda la historia una vez por política, con el mismo azar** (mismos tiempos de soldeo, mismas fallas, mismos proveedores). El DSS solo ve lo que vería la empresa.
3. Se midió también la **alerta temprana**: un observador que re-pronostica cada 12 días sin tocar la planta.

Políticas (25 proyectos de la muestra): **A0** como se hizo · **B1** regla del jefe de taller (compara avance con un plan lineal y pone horas extra y gente) · **C1** colchón fijo (fecha del cotizador + 7 días laborables, el cuantil 80 % del atraso de los 13 proyectos fuera de la muestra) · **D0** monitoreo · **D1** DSS con fecha al 80 % · **D2** DSS con fecha α\* (≈ 0.93) · **D3** DSS gestionando con la fecha original · **D4** DSS completo (α\* + gestión).

## Resultados

| Política | OTD | Retraso (d) | Palancas (% presup.) | Penalidad + palancas | + costo comercial del plazo | Plazo cotizado (d cal.) |
|---|---|---|---|---|---|---|
| A0 Como se hizo | 76 % | 1.00 | 0 | **1.00** | **1.00** | 66.6 |
| B1 Regla del jefe de taller | 76 % | 1.24 | 9.64 | 10.88 | 10.88 | 66.6 |
| C1 Colchón fijo (+7 d lab.) | 100 % | 0 | 0 | 0 | **0.66** | 74.8 (+12 %) |
| D1 DSS fecha α = 0.80 | 80 % | 1.12 | 0 | 1.12 | 1.16 | 67.1 (+0.8 %) |
| D2 DSS fecha α\* | 88 % | 0.52 | 0 | 0.52 | 0.98 | 72.3 (+8.6 %) |
| D3 DSS gestión (fecha original) | 76 % | 1.12 | 1.29 | 2.41 | 2.41 | 66.6 |
| D4 DSS completo | 88 % | 0.32 | 0.30 | 0.62 | 1.08 | 72.3 (+8.6 %) |

Penalidad = 1 % del presupuesto por día. El costo comercial del plazo extra es un **supuesto** (0.08 % por día, de `alpha_optimo`). Archivos: `data/exp6_resumen.csv`, `exp6_gemelo.csv` (por proyecto), `exp6_decisiones.csv`, `exp6_alerta.csv`.

**Diferencia frente a A0** en penalidad + palancas + costo comercial (IC 95 % bootstrap sobre los 25 proyectos): B1 **+9.9** [+1.9, +23.2] (peor) · C1 −0.34 [−1.2, +0.3] · D1 +0.16 [−0.4, +0.8] · D2 −0.02 [−0.9, +0.9] · D3 **+1.4** [+0.9, +2.1] (peor) · D4 +0.08 [−0.8, +0.7]. Ninguna mejora es estadísticamente distinguible de cero.

### Alerta temprana (D0)

| Tramo del plazo | Observaciones (atrasados) | AUC | Brier | Brier de la base | Error de fecha (d) |
|---|---|---|---|---|---|
| 0–25 % | 20 (6) | 0.55 | 0.200 | 0.214 | 3.9 |
| 25–50 % | 26 (7) | 0.68 | 0.192 | 0.198 | 6.1 |
| 50–75 % | 29 (8) | 0.68 | 0.199 | 0.201 | 6.5 |
| 75–100 % | 23 (7) | **0.83** | **0.140** | 0.216 | 4.7 |

AUC 0.5 = sin señal. El re-pronóstico gana señal conforme avanza el proyecto, pero solo en el último cuarto supera claramente a «la probabilidad histórica de atraso». La fecha pronosticada queda a ±4–6 días y con un sesgo de +1 a +3 días (pesimista).

## Lectura

1. **La fecha del DSS está calibrada, y ese es su aporte.** Con α = 0.80 el 80 % de los proyectos cumple (nominal 80 %); con α\* ≈ 0.93 cumple el 88 %. Pero **un colchón fijo bien afinado hace lo mismo con menos esfuerzo** y, a igual cumplimiento, el DSS no cobra menos plazo. Coincide con el experimento 4 de [04](04_resultados_banco_pruebas.md) y con Mundt & Lödding: la ventaja del Monte Carlo es la **probabilidad interpretable y la penalidad esperada**, no un plazo menor.
2. **La gestión no sirve en este gemelo, y por una razón que se entiende.** Los atrasos de los 6 proyectos tardíos vienen de la **pintura externa (13 a 26 días)** y de la espera de **material**, no de la capacidad de la planta. Para un proyecto normal el tiempo se reparte así: ingeniería 2.4 d, el material llega a los 19 d, el habilitado termina a los 26 d, limpieza a los 47 d, pintura +12 d y entrega +1 d. Las palancas internas (gente u horas extra en armado, soldeo y limpieza) actúan sobre unos 21 de los 60 días de un proyecto normal, es decir un tercio, y no tocan lo que atrasa. La regla del jefe de taller gasta casi 10 % del presupuesto en horas extra sin mejorar nada.
3. **Riesgo de modelo.** Las palancas internas que recomienda el DSS (+2 personas en limpieza, segundo turno en la sierra) mejoran la fecha en su planificador diario pero no en la planta: es lo que se espera cuando el modelo de planificación omite lo que de verdad domina el plazo. Por eso se le enseñó a aprender las esperas de compras e ingeniería desde los proyectos terminados y a calibrar sus solapes con el tareo (antes cotizaba +50 % de plazo y recomendaba palancas sobre el cuello equivocado). Aun así, la gestión no se justifica; **hace falta el lazo cerrado C4**: medir si cada palanca produjo el efecto que predijo y dejar de usar las que no.
4. **Cuando el DSS aprende del experto, mejora; cuando lo ignora, empeora.** Sin anclarlo al plazo del cotizador cotizaba +36 % de plazo para cumplir; anclado, +0.8 % para cumplir lo mismo que la realidad. Es un resultado sobre el diseño del DSS, consistente con Rokoss et al.: el experto es una base fuerte.
5. **La alerta temprana es lo más prometedor**: AUC 0.83 en el último cuarto del plazo, a tiempo de gestionar con el cliente (fecha, penalidad). Con datos reales conviene medirla desde el inicio del piloto.

## Qué cambia con datos reales

Todo lo anterior depende del gemelo. Con tareos reales: (a) el gemelo se **valida** en vez de calibrarse (¿reproduce las duraciones por proceso?), (b) el efecto de las palancas se mide en la planta, no se supone, (c) los plazos de proveedores y pintura se aprenden de las órdenes reales, (d) N crece más allá de 25. Es posible que la gestión sí funcione en Steelser; el experimento permite saberlo.

## Límites (declararlos)

- Simulado y de una sola historia (una realización del azar): los intervalos del bootstrap miden la variación entre proyectos, no entre realizaciones del gemelo.
- N = 25 proyectos (IC de proporciones ±16 puntos); A0 tiene solo 6 atrasos de 2 a 8 días.
- El factor de ritmo por proyecto es una caja negra que absorbe lo que el gemelo no modela; los plazos de proveedores y pintura son lognormales independientes.
- Costos de palancas y costo comercial del plazo son supuestos sin datos de la empresa.
- El error de planificación del CRP frente al gemelo, aun con las entradas observadas, es de ≈ 12 días laborables en promedio (24 %): es el tamaño del «riesgo de modelo».

## Reproducir

```bash
py scripts/reconstruir_muestra.py   # solo si falta extras/
py -m dss.simulador && py -m dss.simulador_planta
py scripts/exp6_gemelo.py           # ≈ 6 min con 6 núcleos; escribe data/exp6_*.csv y las tablas gem_*
py -m pytest tests -q
```
