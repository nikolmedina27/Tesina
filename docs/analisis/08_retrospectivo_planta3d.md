# 08 · Estudio retrospectivo: cómo se hizo y qué habría pasado con el DSS

> **Sustituido por [09](09_resultados_gemelo.md).** Este estudio usa el CRP como «verdad» (circular); se conserva para reproducir `exp5`. El resultado principal es el de 09.

> **Todo es SIMULADO.** Es un banco de pruebas retrospectivo: la «verdad» de cada proyecto sale de los mundos simulados (`sim_*`), condicionados a la duración real de los 25 proyectos. No es evidencia sobre Steelser y así debe declararse. La BD de esta PC además es una **reconstrucción** (ver [diseno/06](../diseno/06_datos_simulados.md)): las cuadrillas por proceso son simuladas, por eso estos números **no** coinciden con los de [04](04_resultados_banco_pruebas.md), que salen de la BD original.

## Qué se hizo

Para cada proyecto, en orden cronológico y **solo con lo que se sabía a su fecha de inicio** (proyectos terminados antes para entrenar el QRF, paradas registradas hasta ese día, carga del taller), se aplican 6 políticas y se mide el resultado contra la ejecución simulada:

| | Política | Qué decide el DSS | Ejecución |
|---|---|---|---|
| A0 | Como se hizo | Nada: la fecha la puso el criterio del cotizador | La real |
| A1 | DSS fecha α = 0.80 | Cotiza la fecha del Monte Carlo al 80 % | La misma real |
| A2 | DSS fecha α\* | Cotiza con el cuantil crítico tipo newsvendor (α\* ≈ 0.93) | La misma real |
| A3 | Fecha original + gestión al inicio | Calcula el riesgo de la fecha original; si compensa, aplica la mejor palanca desde el día 1 | Se vuelve a programar con la palanca |
| A4 | Fecha original + re-pronóstico al 40 % | A los 40 % del plazo, con el avance real, re-pronostica y corrige si compensa | Palanca desde ese día |
| A5 | Sistema completo | Fecha α\* y re-pronóstico al 40 % | Palanca desde ese día |

**Cómo se calcula «qué habría pasado»**: `dss/retrospectivo.py` vuelve a programar el proyecto con la verdad del mundo (HH reales simuladas, paradas, carga del taller, plazos externos). Con la ejecución sin decisión reproduce la duración real con 0.2 a 0.4 días de error medio por mundo (máximo 2 días). Con una palanca el resultado es *fecha real + (duración con palanca − duración sin palanca)*: se ancla a lo que realmente pasó y solo se toma de la simulación la diferencia que causa la decisión.

**Palancas** (`dss/whatif.py`): más personas en armado, soldeo o limpieza; segundo turno en una máquina; horas extra; expeditar un servicio externo. La búsqueda prueba cada una sola con pocas réplicas, combina las mejores y reevalúa con todas, siempre con las mismas semillas. Todo en % del presupuesto: penalidad = 1 % por día.

**Costos de las palancas = SUPUESTOS** (a los contratistas se les paga por kg: acelerarlos solo cuesta una prima del 10 %; mano de obra directa = 30 % del presupuesto; hora extra = 1.5×; expeditar un servicio externo = 1 %). Por eso se corre también con costos × 0.5 y × 2.

**Costo comercial del plazo**: cotizar más tarde no es gratis. `total_ajustado` suma 0.08 % del presupuesto por cada día de plazo ofertado de más (supuesto de `alpha_optimo`: cada día baja 0.5 puntos la probabilidad de ganar, con margen del 16 %). Sin datos de cotizaciones perdidas no se puede medir de verdad.

## Resultados (25 proyectos, promedio de los 5 mundos)

| Política | OTD | Retraso medio (d) | Costo de palancas (% presup.) | Penalidad + palancas | + costo comercial del plazo | Plazo cotizado (d cal.) | Intervenciones (de 25) |
|---|---|---|---|---|---|---|---|
| A0 Como se hizo | 76 % | 1.20 | 0 | **1.20** | **1.20** | 66.6 | — |
| A1 DSS α = 0.80 | 100 % | 0 | 0 | 0 | 0.93 | 78.3 (+17.6 %) | — |
| A2 DSS α\* | 100 % | 0 | 0 | 0 | 1.39 | 83.9 (+26.0 %) | — |
| A3 Original + gestión al inicio | 100 % | 0 | 1.22 | 1.22 | 1.22 | 66.6 | 25 |
| A4 Original + re-pronóstico 40 % | 98.4 % | 0.02 | 1.09 | 1.11 | 1.11 | 66.6 | 25 |
| A5 Sistema completo | 100 % | 0 | 0.03 | 0.03 | 1.41 | 83.9 (+26.0 %) | 7 |

Los 6 proyectos atrasados de A0 se retrasaron 4, 4, 4, 5, 5 y 8 días. Resultados por mundo en `data/exp5_resumen.csv` y por proyecto en `data/exp5_retrospectivo.csv` (también en la tabla `sim_retro_resultado`).

**Diferencia pareada frente a A0** (penalidad + palancas, % del presupuesto; IC 95 % por bootstrap sobre los 25 proyectos, rango entre mundos):

| Política | Sin costo del plazo | Con costo del plazo |
|---|---|---|
| A1 | −1.20 [−2.08, −0.40] | −0.26 [−1.24, +0.59] |
| A2 | −1.20 [−2.08, −0.40] | +0.19 [−0.80, +1.06] |
| A3 | +0.02 [−0.89, +0.87] | +0.02 [−0.89, +0.87] |
| A4 | −0.09 [−1.00, +0.71] | −0.09 [−1.00, +0.71] |
| A5 | −1.17 [−2.07, −0.34] | +0.21 [−0.78, +1.08] |

### Sensibilidad al costo de las palancas (penalidad + palancas, % del presupuesto; A0 = 1.20)

| Costo de las palancas | A3 | A4 | A5 (intervenciones) |
|---|---|---|---|
| × 0.5 | 0.73 | 0.59 | 0.08 (13.8) |
| × 1 (supuesto base) | 1.22 | 1.11 | 0.03 (7.2) |
| × 2 | 2.13 | 2.08 | 0.01 (1.8) |

## Lectura

1. **Cómo se hizo**: 19 de 25 proyectos cumplieron; los 6 atrasos fueron de 4 a 8 días, que a 1 % por día son 4–8 % del presupuesto en esos proyectos y **1.2 % en promedio**. El criterio del cotizador ya es preciso: sus fechas se desviaron pocos días.
2. **Con el DSS solo cambiando la fecha (A1, A2)**: los 25 proyectos habrían cumplido, pero cotizando **18 % y 26 % más plazo**. Sin cobrar ese plazo extra parece una mejora (−1.20); cobrándolo con el supuesto de 0.08 %/día desaparece (−0.26 y +0.19, con intervalos que cruzan 0). No hay forma de saber si conviene sin las cotizaciones ganadas y perdidas.
3. **Con el DSS gestionando (A3, A4)**: evita casi todos los atrasos, pero **gasta en palancas lo mismo que se ahorra en penalidad**: 1.22 y 1.11 contra 1.20. Con palancas a la mitad de costo (×0.5) la gestión sí gana (0.73 y 0.59); al doble (×2) pierde (2.13 y 2.08). El punto de equilibrio está cerca de los costos supuestos: **el resultado depende del costo real de acelerar**, que hoy no se conoce.
4. **Por qué interviene en los 25 proyectos**: el modelo cree que la fecha original se cumple solo el **31 %** de las veces (la penalidad esperada que calcula para esa fecha es de 2.5 a 13 % del presupuesto, 6.1 % en promedio), cuando en realidad se cumplió el 76 % y el retraso medio fue de 1.2 días. El pronóstico está sesgado hacia lo pesimista unos +2 a +3 días laborables (≈ +5 %) y es más ancho que el error real del plan del cotizador (P10–P90 ≈ ±12 %). Con un pronóstico mejor calibrado intervendría solo donde hace falta. Es el mismo punto débil que ya mostraba `04`: la calibración es marginal y no por tamaño.
5. **Sistema completo (A5)**: con la fecha más holgada (α\*) casi no hace falta gestionar (7 de 25 proyectos, costo 0.03) y se cumple todo, pero el plazo sube 26 %. Con el costo comercial del plazo queda en 1.41, igual que las demás opciones.
6. **Conclusión honesta**: en esta muestra el DSS **puede evitar los 6 atrasos** de dos maneras (cotizar más tarde o acelerar), pero **ninguna política supera con claridad a la fecha del cotizador una vez que se cobran el plazo y las palancas**. Coincide con `04` y con la literatura (el experto es una base fuerte). Lo que el DSS sí aporta es la **decisión con números**: la probabilidad de cumplir cualquier fecha, la penalidad esperada, la palanca más barata para recuperar una fecha y cuánto cambia el resultado si los costos cambian.

**Palancas que elige** (250 intervenciones de A3 y A4): expeditar el granallado y pintura en todas, +2 personas en limpieza en 181, +2 en armado en 34, +2 en soldeo en 32 y segundo turno en la sierra o la mesa CNC en 35. Es decir, casi siempre la misma receta barata sobre el cuello de botella de este mundo (servicio externo y limpieza).

## Límites (declararlos)

- Mundo simulado y base reconstruida; los 5 mundos comparten los mismos 25 proyectos reales: **no son 5 evidencias independientes**.
- N = 25 (los IC de proporciones son de ±16 puntos); A0 tiene solo 6 atrasos.
- Costos de palancas y costo comercial del plazo son supuestos sin datos de la empresa.
- Las palancas suponen que sumar personas aumenta la capacidad en proporción y que el efecto es inmediato; no modelan disponibilidad de contratistas ni curva de aprendizaje.
- El re-pronóstico al 40 % usa el estado real del proyecto en ese día (de la simulación) y el mismo supuesto de φ a priori; no aprende del avance.
- El modelo de horas del panel de la plataforma (vista 3D) se entrena con los 25 proyectos y por tanto incluye al que se evalúa; este estudio usa solo lo anterior a cada proyecto.

## Qué sigue

1. Corregir el sesgo del pronóstico y calibrar por tamaño (conformal condicional, ver `04`) y volver a correr: debería bajar las intervenciones innecesarias de A3 y A4.
2. Pedir a la empresa los costos reales de acelerar (prima de contratistas, hora extra, segundo turno) y las cotizaciones ganadas y perdidas (para el costo comercial del plazo).
3. Con tareos reales, repetir con datos reales y pasar a un piloto en paralelo (*shadow mode*).

## Reproducir

```bash
py scripts/reconstruir_muestra.py   # solo si falta extras/
py -m dss.simulador
py -m dss.simulador_planta
py scripts/exp5_retrospectivo.py              # ≈ 8 min con 5 núcleos; escribe data/exp5_*.csv y sim_retro_resultado
py scripts/exp5_retrospectivo.py --costo 0.5  # sensibilidad (también --costo 2)
py -m pytest tests -q
```

Código: `dss/retrospectivo.py` (políticas y replay), `dss/whatif.py` (palancas y búsqueda), `scripts/exp5_retrospectivo.py` (corrida, resumen y bootstrap). Semillas: la del proyecto para cada cotización y las de `dss/simulador.py` para los mundos.
