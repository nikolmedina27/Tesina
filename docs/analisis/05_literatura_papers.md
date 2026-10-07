# 05 · Análisis de los 27 papers de `papers/`

Qué herramientas usan, cuáles se parecen a las nuestras y qué dejan abierto. Los PDFs se renombraron a su título (mapeo en [papers_mapeo.csv](papers_mapeo.csv), script `scripts/renombrar_papers.py`).

**Cómo se leyó**: se extrajo el texto completo de los 27 y se contaron términos clave en todos. Se leyeron con detalle (conclusiones, tablas y metodología) Wei, Hajj Chehade, Flores-Huamán, Rokoss, Mundt & Lödding, May, Roblek, Hollerweger, Anand, Urban y De Simone 2025. El resto se clasificó con el resumen, la introducción y el conteo de términos; está marcado como *resumen*.

Etiquetas: **C1** estandarización y tiempos estándar · **C2** ML para estimar horas, tiempos o lead time · **C3** capacidad, CRP, simulación o disponibilidad · **C4** reentrenamiento o lazo de aprendizaje · **P** salida probabilística (intervalos o riesgo cuantificado) · **$** costo asimétrico de plazo o penalidad.

## 1. Resumen de cobertura

| Pregunta | Resultado en los 27 papers |
|---|---|
| ¿Usan **Quantile Regression Forest**? | **0**. Términos *quantile* y *conformal*: 0 menciones en toda la carpeta |
| ¿Dan una **fecha de entrega con probabilidad**? | **0** como combinación ML + capacidad. Mundt & Lödding dan fechas confiables con un **colchón fijo** (sin ML ni distribución) |
| ¿Cuantifican incertidumbre con intervalos? | **1** (May et al., semiconductores, intervalos de predicción de una cola y PICP) y **1** con métrica de riesgo (Urban et al.) |
| ¿Usan **Monte Carlo**? | 2 menciones, solo en Mundt & Lödding (simulación de eventos discretos, no sobre ML) |
| ¿Incluyen **penalidad por atraso** o costo asimétrico en la decisión? | **0** (Anand et al. usan la lógica de costo de desajuste oferta-demanda, no de fecha) |
| ¿ML para estimar tiempos (C2)? | 11 papers: Wei, Hajj Chehade, Aslan, Flores-Huamán, Çakıt, Rokoss, Urban, De Simone 2025, Wang, Roblek, Cruz |
| ¿Capacidad, simulación o disponibilidad (C3)? | 10: Mundt, Anand, Woschank, Hollerweger, Bianchini, Wolska, Wang, Werth, Zanella, Liang |
| ¿Estandarización de tiempos (C1)? | 2 directos (Ki, Çakıt) y 2 indirectos (Bianchini, Wolska) |
| ¿Reentrenamiento o lazo cerrado (C4)? | 3: Flores-Huamán (reentrena), Del Gallo (autoaprendizaje), Werth (adaptación) |
| ¿Hay alguno que junte C2 + C3 + P? | **Ninguno** |

**Conclusión sobre la novedad**: el vacío que describe la tesis (herramientas monofuncionales) **se confirma dentro de esta carpeta**. Pero esta carpeta es una selección; hay antecedentes externos que hay que tratar (sección 4).

## 2. Los 27 papers

| # | Paper | Datos y método | Etiquetas | Qué aporta y qué limita para nosotros |
|---|---|---|---|---|
| 1 | **Wei et al. 2024**, *Processes* — Man-hour prediction in structural steel fabrication | Corte longitudinal en acero estructural. ~3 000 registros depurados (test n = 600). Random Forest vs SVR, BPNN y regresión lineal. RMSE 2.96, MAPE 6.51 %, R² 0.9447 | C2 | **El más cercano en sector y algoritmo.** Predicción puntual, de un solo proceso (corte), sin capacidad ni fecha. Los expertos estimaban peor que el modelo |
| 2 | **Hajj Chehade et al. 2024**, *Eng. Appl. AI* — Manufacturing time estimation for offer pricing | Metalurgia francesa MTO/ETO. Más de 23 000 líneas de ERP; la familia principal tiene 2 119 filas. Varios algoritmos, CatBoost el mejor (MAE 1.90 en validación cruzada y 1.81 en datos recientes). Usa texto libre y conocimiento de dominio | C2 | Es **el mismo problema de cotización**. **Matiz importante**: las familias con 6, 78 y 87 filas **no se pueden modelar solas**; se agrupan (3 modelos para 7 familias). Sin incertidumbre ni fecha. Piden evaluar sobre y subestimación |
| 3 | **Aslan et al. 2023**, *IJAMT* — Hierarchical ensemble deep learning for lead time prediction | Bosch: 1 183 747 muestras, ~970 sensores. Redes jerárquicas (generalista + especialistas). R² hasta 0.96 | C2 | Escala industrial muy distinta a una pyme. Aporta la idea de **estado de planta a la llegada de la orden** como variable. *Resumen + términos* |
| 4 | **Flores-Huamán et al. 2024**, *Mathematics* — Lead-time prediction in wind tower manufacturing | 231 678 observaciones, 11 algoritmos. XGBoost y LightGBM los mejores; TabNet y NODE más lentos de entrenar. Incluye función de **reentrenamiento** | C2 C4 | Sustenta usar árboles y no redes en tabulares. Su reentrenamiento no usa una regla de deriva |
| 5 | **Çakıt & Dağdeviren 2023**, *AI EDAM* — Predicting standard time in a manufacturing environment | **305 registros** de una fábrica de buses. kNN mejor. Variables: n° de soldaduras, n° de piezas, factor de superficie, dificultad, conformados | C1 C2 | **Muestra pequeña que funciona** y buena **lista de variables** para estimar tiempos de soldadura. Sin intervalos |
| 6 | **Ki et al. 2023**, *Applied Sciences* — Production improvement rate with time series data on standard time | Series de tiempo del tiempo estándar en planta (Corea) para planificar a largo plazo | C1 | Respalda **actualizar tiempos estándar** (nuestro Io). ML secundario. *Resumen* |
| 7 | **Rokoss et al. 2024**, *J. Intell. Manuf.* — Delivery time determination with ML in small batch companies | Caso 1: 16 361 órdenes (58 344 pasos). XGBoost con 13 variables elegidas con SHAP. Variable clave: **fecha deseada por el cliente** | C2 $ parcial | **Hallazgo crítico**: el **departamento de planificación (RMSE 5.87 días) casi iguala al ML con tiempos planificados (5.56)**. El ML sin tiempos planificados rinde peor (7.73). Corrobora lo que vimos en nuestro banco de pruebas |
| 8 | **Urban et al. 2024**, *Applied Sciences* — ML in SMEs, estimation of production time | Pyme alemana, 3 704 trabajos, WEKA. Clasifica trabajos en 4 tipos y define una **métrica de riesgo** | C2 P parcial | **Pocos datos y pyme**, igual que nosotros. Modelos de baja precisión por pocos atributos. Recomiendan agregar geometría, material, tolerancias vía CAD-ERP |
| 9 | **Ördek et al. 2024**, *Prod. & Manuf. Res.* — ML-supported manufacturing: a review | Revisión de 114 artículos. *Resumen* | C2 | Cita que RF es de los más usados y que las aplicaciones son aisladas. No verificado el conteo exacto |
| 10 | **Guerrero et al. 2025**, *IJPR* — Sustainable optimisation approaches for PPC, industry 5.0 | Revisión de estudios de PPC. *Resumen* | — | Brecha de uso en pymes. No verifiqué la cifra "6 de 77" que cita la tesis |
| 11 | **Wolska et al. 2023**, *Encyclopedia* — Implementation of the TPM concept | Revisión teórica de TPM (OEE, MTBF, MTTR). *Resumen* | C3 | Define disponibilidad. Sin datos propios |
| 12 | **Mundt & Lödding 2025**, *Prod. Plan. & Control* — Reliable delivery times with the throughput diagram | Fechas de entrega confiables en MTO. 3 estudios con 10 000 ofertas simuladas. Cumplimiento 97.1–99.9 % con carga balanceada o sobrecarga de 5 %; 91.0 % y **41.9 %** con los tiempos estándar | C3 $ parcial | **El rival más cercano en la idea de fecha confiable.** Usa un **colchón fijo** (1 día) y capacidad, sin ML ni distribución, y considera la probabilidad de aceptación de ofertas. Es la comparación obligada |
| 13 | **De Simone et al. 2023**, *Sustainability* — Sustainable PPC: a bibliometric review | 437 artículos en Scopus. Los DSS de PPC siguen poco desarrollados. *Resumen* | — | Útil como cita de brecha |
| 14 | **Zanella & Vaz 2023**, *SN Comput. Sci.* — Sustainable short-term production planning optimization | MILP y regla de secuenciación en Excel para una prensa. Ahorra hasta 22.1 % del costo. *Resumen* | C3 | Precedente de DSS en **Excel** para pymes. Poco relevante para fechas |
| 15 | **Liang et al. 2025**, *IJPR* — Integrated scheduling of production and material delivery | Optimización de programación con entrega de materiales. *Resumen* | C3 | Relevancia baja; recuerda que la **llegada de materiales** afecta los plazos |
| 16 | **De Simone et al. 2025**, *Machines* — Task workload prediction in manufacturing | Pyme italiana, KNIME + AutoML. Reduce el MAE 31 % y 47 % frente al promedio y la estimación manual (un producto), 32 % y 42 % con todos los productos (XGBoost) | C2 | Evidencia **a favor** del ML sobre estimación manual con pocos datos; contrasta con Rokoss y Roblek |
| 17 | **Hollerweger et al. 2026**, *Machines* — OEE and free generative-AI tools in a CNC machining cell | Metalmecánica brasileña, 31 meses de MES. **Disponibilidad 75.8 % (2023), 77.8 % (2024) y 68.9 % (2025)**; causas: mantenimiento correctivo, repuestos, lubricación, cambio de herramienta | C3 | **Valores reales de disponibilidad** para calibrar Dₖ. Mi simulación asumía ≈ 90 %: era optimista |
| 18 | **Woschank et al. 2024**, *Flex. Serv. Manuf. J.* — Real-time data to increase update frequency of PPC in MTO | Simulación de eventos discretos con datos de una empresa electrónica; compara estrategias push y pull | C3 | Respalda **actualizar los parámetros con más frecuencia**. Sin ML |
| 19 | **Bianchini et al. 2024**, *Sustainability* — MES in manufacturing SMEs: KPI development | MES en una pyme italiana con CNC; KPIs de utilización, disponibilidad, eficiencia y saturación. *Resumen* | C1 C3 | Modelo de **captura de datos y KPIs** para pymes (útil para nuestra BD) |
| 20 | **Anand et al. 2023**, *POM* — Capacity planning with limited information | Cinco heurísticas para planificar capacidad con información incompleta. Conviene planificar con rigor pocos **recursos "conductores"** y usar **ratios** para el resto. Reducir el error de medición de los conductores es lo que más aporta | C3 | **Justifica nuestro diseño**: las 4 máquinas y los contratistas son los conductores; el resto va con ratios. Usa lógica de costo asimétrico (11 menciones de *newsvendor*) |
| 21 | **Pereira et al. 2025**, *Applied Sciences* — Manufacturing management processes integration framework | Marco con CPS, gemelos digitales, IA y blockchain; validado con encuesta Likert a 32 personas. *Resumen* | — | Sustenta la integración comercial-taller, pero la validación es solo percepción |
| 22 | **Wang et al. 2024**, *Sci. Reports* — EMA-DCPM algorithm for production scheduling | Aeroespacial, ~40 000 elementos. Atención para predecir tiempos y CPM dinámico. *Resumen* | C2 C3 | Parecido a nuestro motor (ruta crítica con tiempos predichos) pero **determinista** |
| 23 | **May et al. 2024**, *J. Intell. Manuf.* — Product-inherent constraints with AI, semiconductor control | Predice tiempos de transición con **intervalos de predicción de una cola**, mide **PICP** y ancho; desbalance de clases | P | **El único con intervalos calibrados**; usa las mismas métricas que nosotros (cobertura contra ancho). Sin capacidad ni fecha de entrega; dejan Bayesian networks como trabajo futuro |
| 24 | **Roblek et al. 2024**, *Processes* — Human vs AI planning in production | 110 productos, 18 ID. Compara el plan del planificador con la predicción de IA. **El plan humano se acercó más a la realidad** (59.4 % de eventos dentro de ±25 % frente a 20.7 % de la IA; RQ2 no confirmada) | C2 | **Evidencia directa** de que el planificador humano es una base fuerte; apoya el enfoque "DSS que audita al cotizador" |
| 25 | **Del Gallo et al. 2024**, *Prod. & Manuf. Res.* — Self-learning framework with association rules for scheduling | 11 960 trabajos; reglas de asociación + modelos matemáticos. *Resumen* | C4 | Concepto de **aprendizaje continuo** en la programación |
| 26 | **Werth et al. 2024**, *Applied Sciences* — Learning and self-adaptation in dynamic scheduling | Aprende tiempos y lotes en línea con ML y los usa en una metaheurística. *Resumen* | C3 C4 | Idea de que el modelo se actualice durante la operación |
| 27 | **Cruz et al. 2024**, *Oper. Res. Perspectives* — AutoML methodology for SMEs | 1 500 muestras; AutoML + NSGA-II multiobjetivo. *Resumen* | C2 C3 | Pipeline automatizado para pymes; optimiza parámetros, no fechas |

## 3. Lo que dicen en conjunto

1. **El experto es una base fuerte.** Rokoss (planificación 5.87 vs ML 5.56 días de RMSE), Roblek (el plan humano gana) y nuestro banco de pruebas coinciden. De Simone 2025 muestra la excepción: cuando la estimación manual es un promedio informal, el ML gana. Hay que **medir bien la estimación del cotizador** y tratarla como línea base y como variable de entrada.
2. **El conocimiento de dominio importa más que más datos**: en Rokoss, agregar variables de dominio (WIP, cuellos de botella) baja el RMSE de 9.47 a 7.73 días; agregar además los tiempos planificados por el área, a 5.56. Es el argumento para guardar el **estado de planta** y **lo que estimó el cotizador**.
3. **Con pocos datos hay estrategias probadas**: agrupar familias (Hajj Chehade), clasificar tipos de trabajo (Urban), AutoML (De Simone, Cruz) y muestras de ~300 registros (Çakıt).
4. **Las métricas puntuales dominan** (MAE, RMSE, R², MAPE). Solo May reporta cobertura de intervalos. Nadie evalúa el **sesgo hacia subestimar** (Hajj Chehade lo pide).
5. **La disponibilidad real es baja** (69–78 %, Hollerweger) y varía mucho entre años; no es un parámetro estable.
6. **La colocación del plazo** (cuánto colchón) se trata con reglas fijas (Mundt) o no se trata. No hay costo explícito de atraso en ninguno.

## 4. Antecedentes externos verificados (no están en la carpeta)

Búsqueda rápida en la web; falta una revisión sistemática en Scopus y WoS antes de afirmar novedad.

| Antecedente | Qué hace | Implicancia |
|---|---|---|
| [Bekci et al. 2022, *Probabilistic Models for Manufacturing Lead Times*](https://arxiv.org/pdf/2204.13792) (arXiv) | Metalmecánica en Canadá, corte láser. Procesos gaussianos, redes probabilísticas, NGBoost y **boosting con regresión cuantílica**; los modelos superan la estimación de la empresa y están calibrados. Los intervalos sirven "como herramienta para cotizar" | **Es el antecedente más cercano** en predicción probabilística para cotizar. Sin capacidad ni Monte Carlo ni penalidad ni conformal. Es un preprint: revisar si se publicó |
| Keskinocak & Tayur (2001, *Management Science*; 2004, capítulo *Due date management policies*) | Cotización de fechas confiables con capacidad e ingresos que dependen del plazo | Es la línea teórica clásica; **la tesis no la cita** |
| Simulación de Monte Carlo para el riesgo de cronograma | Técnica clásica en gestión de proyectos: las fechas con duraciones "más probables" son optimistas | El Monte Carlo en sí **no es novedad**; lo es su integración con capacidad finita, Dₖ y distribuciones del QRF |
| Conformal en programación | La búsqueda rápida no encontró aplicaciones directas | No afirmar "primero"; verificar con búsqueda sistemática |

## 5. Dónde queda nuestro aporte

| Elemento | Estado en la literatura | Qué podemos sostener |
|---|---|---|
| ML para estimar horas en acero estructural | Hecho (Wei) | Replicamos; no es aporte |
| Distribución de lead time con cuantiles para cotizar | Hecho en otro proceso (Bekci, preprint) | Lo extendemos a **proyectos de varios procesos** |
| Fecha confiable con capacidad finita | Hecho sin ML (Mundt; Keskinocak & Tayur) | **Unimos distribuciones aprendidas + capacidad + disponibilidad** |
| Calibración conformal agrupada por proyecto con N pequeño | No encontrado | **Candidato a aporte metodológico** (a verificar) |
| α\* económico con penalidad sin tope | Lógica conocida (newsvendor) | Aplicación y **frontera cumplimiento-plazo** con datos de una pyme |
| Evaluación contra el cotizador y backtest causal | Poco común (Rokoss y Roblek lo hacen) | Es lo que más valoran los revisores |

## 6. Errores de la revisión de literatura de la tesis (verificados contra los PDFs)

1. **Hajj Chehade**: la tesis dice que se logran "estimaciones precisas incluso en familias con tan solo 78 registros". El paper dice que con 78, 87 o 6 filas **no es posible construir un modelo**; se logra combinando familias (3 modelos para 7).
2. **Rokoss**: la tesis dice que el modelo redujo el error "casi 50 % frente a la estimación tradicional del área de planificación". En la Tabla 6 del paper el área de planificación tiene RMSE 5.87 y el modelo sin sus tiempos planificados 7.73. La reducción de ~50 % es respecto del **promedio histórico** (12.15), no del planificador.
3. **Faltan 2 PDFs** de la Tabla 2: Canedo Rosa et al. 2025 (#4) y Barros et al. 2023 (#10).
4. **Zhang et al. (2024)**, sección 2.2.6.7, no está en la Tabla 2 ni en la carpeta y no tiene DOI. Verificar que exista.
5. Las cifras de Guerrero (77 estudios, ML en 6) y Bianchini (+7 % de rentabilidad) no pude confirmarlas en el texto extraído; revisarlas a mano.

Las correcciones se hacen en el Word; aquí solo quedan documentadas.
