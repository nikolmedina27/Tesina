# 02 · Diagnóstico de calidad de datos e inconsistencias

**Conclusión principal: con los datos actuales no se puede entrenar el modelo.** La variable objetivo (HH reales por proceso) no existe todavía en ningún archivo. Este documento explica por qué y qué corregir en la tesis.

## 1. Las "HH estimadas" son el ratio vigente, no horas reales

En `Proyectos_muestra_25 Dep.xlsx`, `HH estimadas / Toneladas` es **constante** dentro de cada combinación tipo de estructura × proceso (desviación máxima 0.0007 HH/t). Es decir:

```
HH_estimadas = Toneladas × ratio(tipo, proceso)
```

| Tipo de estructura | HH/t total | Factor vs. Nave |
|---|---|---|
| Nave industrial / packing / cobertura | 28.04 | 1.000 |
| Mezzanine / plataformas / oficinas | 30.96 | 1.111 |
| Edificación / infraestructura | 33.88 | 1.222 |
| Planta industrial / minería | 36.79 | 1.333 |

Además, los ratios de un tipo son el ratio de "Nave" multiplicado por un factor fijo (p. ej. armado: 7.2 / 8.0 / 8.8 / 9.6 HH/t).

**Consecuencias**

- Si se entrena un Random Forest o QRF para predecir esta columna, el modelo tendrá R² ≈ 1 porque aprende una fórmula conocida. Un revisor lo detecta de inmediato: **es fuga de información / dato sintético**.
- El factor de corrección φ = HH_real / HH_ratio (Ecuación 9) no se puede calcular: falta el numerador.
- Lo rescatable: esta columna **es** el ratio vigente, que el modelo necesita como entrada y como línea base. Quedó en la tabla `ratio_vigente`.

## 2. Los días por proceso también están construidos

- `Días reales = Días planificados + Días de retraso asignados` en las 325 filas, y los "días de retraso asignados" son siempre −1, 0 o +1, repartidos para que su suma sea igual al retraso del proyecto en días hábiles. No es un registro de planta, es un reparto.
- `N° personas` es 1 en todas las máquinas y casi constante en el resto.
- La suma de días por proceso (71–158) es mucho mayor que la duración del proyecto (≈ 66–70 días calendario): los procesos se **solapan**, pero el archivo no tiene fechas de inicio/fin por proceso, por lo que no se pueden medir los solapes que el CRP necesita.

## 3. La muestra excluye la mitad de los proyectos atrasados (sesgo de selección)

Los 25 proyectos de la muestra se cruzaron con los 38 de la Tabla 3 del Word (ver `proyecto.en_muestra`).

| Grupo | n | Atrasados | OTD | Retraso promedio | Retraso máx. |
|---|---|---|---|---|---|
| Población (Tabla 3) | 38 | 12 | **68.4 %** | 2.29 días | 18 |
| Muestra Excel | 25 | 6 | **76.0 %** | 1.20 días | 8 |
| Excluidos | 13 | 6 | 53.8 % | 4.38 días | 18 |

Excluidos: #1 (2019), #2–#5 (2020), #8 (12 días de retraso), #13 (6), #19 FUCSA puentes grúa, #26, #28 PUCP caseta (7), #32 CUMBRA cabezales (6), #34 CELSA, #35.

Un revisor preguntará por qué los criterios de exclusión eliminan justo los peores casos. Hay que documentar el motivo **por proyecto** (`proyecto.motivo_exclusion`, hoy vacío) y reportar resultados con y sin excluidos.

## 4. Inconsistencias internas de la tesis (corregir antes de TF2)

| # | Dónde | Problema |
|---|---|---|
| 1 | Cap. III, 3.4.1 | "De 38 proyectos… se excluyeron nueve… muestra de 28": 38 − 9 = 29, no 28. El Excel tiene 25 |
| 2 | Cap. III, 3.4.1 | Ventana COVID mar–ago 2020 contiene **4** proyectos (#2, #3, #4, #5), no 3 |
| 3 | Cap. III, línea base | OTD 71.4 % (20/28) y retraso máx. 12 días no coinciden con la muestra Excel (76 %, máx. 8) ni con la población (68.4 %) |
| 4 | Tablas 4 y 7, árbol de problemas | Dicen 70 %; 26/38 = 68.4 % |
| 5 | Resumen, keywords, objetivo 1 | Hablan de **Random Forest**; el Cap. III usa **Quantile Regression Forest** + Monte Carlo + lazo cerrado. Alinear |
| 6 | Figura 3 (framework) | Dice "Random Forest", "reducción −25 % a −40 %" y "cumplimiento 90 % o más"; la meta del texto es OTD ≥ 85 % y lead time +5 % máx. |
| 7 | Cap. III | Se citan **Ecuaciones 4 a 15**: la 4 está como texto plano y las **5 a 15 no existen en el Word** (ni como fórmula ni como imagen); la numeración empieza en 4. Reconstruidas en [diseno/04_modelo_matematico.md](../diseno/04_modelo_matematico.md) |
| 7b | Cap. III, inicio | El 2.º párrafo describe "tres componentes" con "Regresión Random Forest"; el resto del capítulo, cuatro componentes con QRF. Los dos párrafos "El aporte integra cuatro componentes…" y "A diferencia de la estimación puntual…" están **duplicados** antes y después de la Figura 3 |
| 8 | Objetivos vs. aporte | 3 objetivos (uno por causa) vs. 4 componentes (C1–C4). El objetivo 3 (protocolo de estandarización) cubre C1 y C4; explicitar el mapeo |
| 9 | Referencias | Faltan en la lista: Breiman (2001), Meinshausen (2006), Nakajima (1988), Power (2002), Hollerweger et al. (2026), Wei et al. (2024), y la mayoría de los 29 artículos de la Tabla 2. Hay duplicados (Barros, Mundt y Lödding, Ördek) |
| 10 | Revisión de literatura | El texto dice 30 artículos, la Tabla 2 tiene 29. "Zhang et al. (2024)", 2.2.6.7, no está en la Tabla 2 ni tiene DOI: **verificar que el artículo exista** (posible referencia inventada por la IA usada en la búsqueda) |
| 11 | Revisión de literatura | Algunos artículos (sostenibilidad, semiconductores) tienen relación débil con el problema; para Q1 conviene reemplazarlos por literatura de *due-date quoting* y predicción probabilística |
| 12 | Cap. I | Se definen indicadores Io y QLT pero no tienen línea base medida |
| 13 | Revisión de literatura, Hajj Chehade et al. (2024) | Dice que logran estimaciones precisas "incluso en familias con tan solo 78 registros". El paper dice que con 78, 87 o 6 filas **no se puede construir un modelo**; agrupan familias (3 modelos para 7). Verificado contra el PDF ([analisis/05 §6](05_literatura_papers.md)) |
| 14 | Revisión de literatura, Rokoss et al. (2024) | Dice "reducción de casi 50 % frente a la estimación tradicional del área de planificación". En su Tabla 6 el área de planificación (RMSE 5.87) supera al modelo sin sus tiempos planificados (7.73); el ~50 % es contra el promedio histórico (12.15) |
| 15 | Tabla 2 | Faltan en `papers/` Canedo Rosa et al. (2025) y Barros et al. (2023); Zhang et al. (2024) no está en la tabla ni tiene DOI |

## 5. Qué sí es sólido

- Las fechas a nivel proyecto de los 38 proyectos (Tabla 3), con las que se calcula la línea base de OTD.
- La estructura de 13 procesos y 4 máquinas, coherente con el layout y el SIPOC.
- El ratio vigente (la práctica actual), que sirve como línea base.
- El formato de control por pieza que ya usa la planta (`REPORTE_DE_HABILITADO`), que tiene fechas reales por proceso y por contratista. Extenderlo es más barato que inventar un formato nuevo.
- La regla contractual de penalidad (1 % del presupuesto por día, sin tope), que justifica la cotización asimétrica.

## 6. Acción

Ver [plan/01_datos_a_recolectar.md](../plan/01_datos_a_recolectar.md). Lo mínimo para tener un modelo defendible: **HH reales por proyecto × proceso para ≥ 25 proyectos**, reconstruidas desde tareos/planillas, y **fechas reales de inicio y fin por proceso**.
