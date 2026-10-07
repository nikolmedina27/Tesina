> Conversión automática de `extras/Tesis_TF1_Steelser.docx` generada por `scripts/docx_a_md.py`. No editar a mano: regenerar si cambia el Word.

# Capítulo II. REVISIÓN LITERATURA

En este capítulo se realiza una revisión de la literatura relacionada con la estandarización de tiempos, el uso de técnicas de Machine Learning y el sistema Capacity Requirements Planning (CRP) en la planificación y control de la producción de empresas del sector metalmecánico. Asimismo, se analizan investigaciones enfocadas en la estimación de requerimientos de capacidad, la programación de órdenes de producción y la reducción de las desviaciones en los tiempos de entrega mediante herramientas de analítica de datos e inteligencia artificial.

Para ello, la revisión bibliográfica se desarrolla en tres fases: desarrollo, análisis y conclusiones.

En la fase de desarrollo, se establecieron los criterios de búsqueda y selección de artículos científicos indexados en las bases de datos Scopus y Web of Science (WoS), considerando investigaciones relacionadas con la estandarización de tiempos de producción, Machine Learning aplicado a la planificación y programación de la producción, Capacity Requirements Planning (CRP), programación de órdenes, optimización de procesos productivos y sistemas inteligentes de apoyo a la toma de decisiones. Asimismo, se identificaron los principales enfoques metodológicos y tecnológicos utilizados en empresas manufactureras, con énfasis en el sector metalmecánico.

En la fase de análisis, se presentan los fundamentos teóricos de la estandarización de tiempos, los modelos de Machine Learning utilizados para la predicción y estimación de tiempos de producción, el sistema Capacity Requirements Planning (CRP) para la planificación de capacidad y las metodologías de programación de órdenes de producción. Además, se analizan los principales resultados reportados por las investigaciones seleccionadas, considerando indicadores de desempeño como la precisión en la estimación de requerimientos, la utilización de la capacidad instalada, el cumplimiento de los programas de producción, la reducción de retrasos y las desviaciones en los tiempos de entrega.

Finalmente, en la fase de conclusiones, se sintetizan los principales aportes de la literatura revisada, identificando las contribuciones, tendencias y limitaciones de los estudios analizados. Este análisis constituye el sustento teórico y metodológico para el desarrollo de la propuesta de integración entre la estandarización de tiempos, Machine Learning y el sistema CRP planteado en la presente investigación.

## Desarrollo

### Búsqueda de artículos

La búsqueda de artículos para la presente investigación se realizó en bases de datos científicas indexadas, principalmente Scopus y Web of Science (WoS), considerando publicaciones comprendidas entre los años 2023 y la actualidad. El objetivo fue identificar investigaciones relacionadas con la estandarización de tiempos de producción, Machine Learning aplicado a la planificación y programación de la producción, Capacity Requirements Planning (CRP), estimación de requerimientos de capacidad, programación de órdenes de producción y optimización de procesos en empresas manufactureras, especialmente del sector metalmecánico.

Para ello, para la búsqueda tradicional se definió la siguiente cadena estructurada:

(("standard time*" OR "time standardization" OR "work measurement" OR "time study") AND ("Machine Learning" OR "artificial intelligence" OR prediction OR forecasting) AND ("Capacity Requirements Planning" OR CRP OR "capacity planning") AND ("production scheduling" OR "production planning" OR "job scheduling" OR "order scheduling") AND (metalworking OR metalmechanic OR manufacturing OR "manufacturing industry"))

En la base de datos Scopus, la búsqueda se aplicó en los campos Title, Abstract and Keywords, mientras que en Web of Science se utilizó la categoría Topic. Asimismo, se aplicaron filtros relacionados con el período de publicación, artículos de investigación y revistas indexadas con cuartil Q1 y Q2 según Scimago Journal Rank (SJR).

El siguiente cuadro muestra las cadenas de búsqueda utilizadas en cada base de datos.

**Tabla 1: Keywords empleadas en la búsqueda de artículos científicos**

| Base de datos | Cadena de búsqueda |
|---|---|
| Scopus | TITLE-ABS-KEY (("standard time*" OR "time standardization" OR "work measurement" OR "time study") AND ("Machine Learning" OR "artificial intelligence" OR prediction OR forecasting) AND ("Capacity Requirements Planning" OR CRP OR "capacity planning") AND ("production scheduling" OR "production planning" OR "order scheduling" OR "production control") AND ("delivery time" OR "lead time" OR "delivery performance") AND (metalworking OR metalmechanic OR manufacturing OR "manufacturing industry")) |
| Web of Science | TS=(("standard time*" OR "time standardization" OR "work measurement" OR "time study") AND ("Machine Learning" OR "artificial intelligence" OR prediction OR forecasting) AND ("Capacity Requirements Planning" OR CRP OR "capacity planning") AND ("production scheduling" OR "production planning" OR "order scheduling" OR "production control") AND ("delivery time" OR "lead time" OR "delivery performance") AND (metalworking OR metalmechanic OR manufacturing OR "manufacturing industry")) |

Nota. Elaboración propia. Las palabras clave fueron utilizadas en las bases de datos Scopus, ScienceDirect y Web of Science durante el periodo 2023–2026

Como apoyo al proceso de búsqueda bibliográfica, también se utilizaron herramientas de inteligencia artificial con el fin de facilitar la identificación inicial de publicaciones relacionadas con el tema de investigación. Estas herramientas permitieron generar combinaciones de palabras clave, identificar términos equivalentes empleados en la literatura científica y orientar la búsqueda hacia estudios vinculados con la estandarización de tiempos, la aplicación de Machine Learning en la planificación de la producción y el sistema Capacity Requirements Planning (CRP). Asimismo, contribuyeron a organizar la información encontrada y a realizar una primera clasificación de los artículos de acuerdo con las categorías establecidas para el estado del arte.

Para este propósito se emplearon ChatGPT y Gemini IA, las cuales fueron utilizadas únicamente como herramientas de apoyo durante la fase exploratoria de la revisión bibliográfica. A partir de las respuestas obtenidas se identificaron posibles artículos, revistas y palabras clave que posteriormente fueron verificadas directamente en las bases de datos Scopus y Web of Science, asegurando que las publicaciones cumplieran con los criterios definidos para la investigación.

Para ello, se empleó el siguiente prompt:

"Actúa como un asistente especializado en investigación científica y análisis bibliométrico. Lleva a cabo una búsqueda sistemática de artículos publicados entre 2022 y la actualidad relacionados con la integración de la estandarización de tiempos, Machine Learning y el sistema Capacity Requirements Planning (CRP), orientados a mejorar la precisión en la estimación de requerimientos, la programación de órdenes de producción y la reducción de las desviaciones en los tiempos de entrega en empresas pymes del sector metalmecánico. La búsqueda debe realizarse en revistas de acceso abierto (Open Access) indexadas en Scopus y Web of Science, priorizando aquellas clasificadas en los cuartiles Q1 y Q2. Presenta los resultados indicando título del artículo, autores, revista, cuartil, año de publicación y DOI."

La información proporcionada por las herramientas de inteligencia artificial no fue incorporada directamente a la investigación. Cada artículo sugerido fue revisado de manera individual para comprobar su relación con el problema de estudio, verificar su indexación, confirmar la información bibliográfica y validar la disponibilidad del documento completo. De esta manera, la inteligencia artificial se empleó únicamente como un recurso complementario para agilizar la localización de literatura científica, mientras que la selección definitiva dependió del análisis realizado por el investigador.

### Selección de artículos

Los artículos encontrados en el proceso de búsqueda fueron sometidos a un proceso de selección para garantizar su pertinencia con la presente investigación, considerando criterios de exclusión relacionados con el problema, el objeto y el contexto de estudio. La búsqueda estuvo enfocada en investigaciones publicadas entre los años 2022 y la actualidad, relacionadas con planificación de la producción, gestión de compras, Lead Time, Engineer-to-Order (ETO), Lean Manufacturing, control de operaciones y cumplimiento de plazos en entornos industriales y metalmecánicos.

Los criterios de exclusión aplicados fueron los siguientes:

Fueron descartados estudios publicados antes del año 2023

Fueron descartados estudios pertenecientes a revistas distintas a los cuartiles Q1 y Q2.

Fueron descartados estudios que corresponden a otros problemas como sostenibilidad, impacto ambiental o reducción de desperdicios sin relación con incumplimiento de plazos y deficiencias en planificación.

Fueron descartados estudios que corresponden a otros objetos de estudio como modelos conceptuales, estándares o enfoques tecnológicos sin aplicación directa en la gestión operativa.

Estos criterios se han aplicado siguiendo el orden: Primero, sobre el título de todos los artículos encontrados; Segundo, sobre el resumen (abstract) de los artículos no excluidos; Tercero, sobre la introducción y las conclusiones de los artículos restantes del paso anterior; y, Cuarto, sobre la revisión de todo el artículo.

Para acelerar la búsqueda y selección de los artículos se utilizaron herramientas de inteligencia artificial como ChatGPT y Gemini IA; sin embargo, se revisaron manualmente los resultados obtenidos por las herramientas con el fin de garantizar la pertinencia y calidad de los artículos seleccionados. Esta validación consistió en la revisión de títulos, abstracts e introducciones para verificar su relación directa con el problema de investigación.

Como resultado de la aplicación de los criterios de selección y exclusión, se obtuvo un total de 30 artículos científicos que conforman la base de la presente revisión de literatura.

**Tabla 2: Artículos seleccionados para revisión de literatura**

| N° | Título del artículo | Autor(es) | Revista (Cuartil) | Año | DOI | Cuartil |
|---|---|---|---|---|---|---|
| 1 | A study on the man-hour prediction in structural steel fabrication. | Wei, Z., Li, Z., Niu, R., Jin, P., & Yu, Z. | Processes | 2024 | https://doi.org/10.3390/pr12061068 | Q2 |
| 2 | Manufacturing time estimation for offer pricing: A machine learning application in a French metallurgy industry. | Hajj Chehade, M., Sylla, A., Diallo, A. R., & Doremus, Y. | Engineering Applications of Artificial Intelligence | 2024 | https://doi.org/10.1016/j.engappai.2024.109089 | Q1 |
| 3 | Hierarchical ensemble deep learning for data-driven lead time prediction. | Aslan, A., Vasantha, G., El-Raoui, H., Quigley, J., Hanson, J., Corney, J., & Sherlock, A. | The International Journal of Advanced Manufacturing Technology | 2023 | https://doi.org/10.1007/s00170-023-12123-4 | Q1 |
| 4 | Machine learning applied to forecasting the manufacturing time of new products prototypes and ETO products: An exploratory study. | Canedo Rosa, R., Carneiro Gonçalves, M., & Macêdo Barbalho, S. C. | International Journal of Production Economics | 2025 | https://doi.org/10.1016/j.ijpe.2025.109688 | Q1 |
| 5 | Lead-time prediction in wind tower manufacturing: A machine learning-based approach. | Flores-Huamán, K.-J., Escudero-Santana, A., Muñoz-Díaz, M.-L., & Cortés, P. | Mathematics | 2024 | https://doi.org/10.3390/math12152347 | Q2 |
| 6 | Comparative analysis of machine learning algorithms for predicting standard time in a manufacturing environment. | Çakıt, E., & Dağdeviren, M. | Artificial Intelligence for Engineering Design, Analysis and Manufacturing | 2023 | https://doi.org/10.1017/S0890060422000245 | Q2 |
| 7 | Production Improvement Rate with Time Series Data on Standard Time at Manufacturing Sites. | Ki, I., Song, H., Ryu, J., & Jeong, J. | Applied Sciences | 2023 | https://doi.org/10.3390/app131910937 | Q2 |
| 8 | Case study on delivery time determination using a machine learning approach in small batch production companies. | Rokoss, A., Syberg, M., & Tomidei, L. | Journal of Intelligent Manufacturing | 2024 | https://doi.org/10.1007/s10845-023-02290-2 | Q1 |
| 9 | Machine learning in small and medium-sized enterprises: Methodology for the estimation of the production time. | Urban, M., Koblasa, F., & Mendřický, R. | Applied Sciences | 2024 | https://doi.org/10.3390/app14198608 | Q2 |
| 10 | A decision support system based on a multivariate supervised regression strategy for estimating supply lead times. | Barros, J., Gonçalves, J. N. C., Cortez, P., & Carvalho, M. S. | Engineering Applications of Artificial Intelligence | 2023 | https://doi.org/10.1016/j.engappai.2023.106671 | Q2 |
| 11 | Machine learning-supported manufacturing: a review and directions for future research. | Ördek, B., Borgianni, Y., & Coatanea, E. | Production & Manufacturing Research | 2024 | https://doi.org/10.1080/21693277.2024.2326526 | Q2 |
| 12 | Sustainable optimisation approaches for production planning and control to evolve towards industry 5.0. | Guerrero, B., Mula, J., & Poler, R. | International Journal of Production Research | 2025 | https://doi.org/10.1080/00207543.2025.2507794 | Q1 |
| 13 | Implementation and improvement of the total productive maintenance concept in an organization. | Wolska, M., Gorewoda, T., Roszak, M., & Gajda, L. | Encyclopedia | 2023 | https://doi.org/10.3390/encyclopedia3040110 | Q1 |
| 14 | Coping with the uncertainties of make-to-order production: a new approach for determining reliable delivery times with the throughput diagram. | Mundt, C., & Lödding, H. | Production Planning & Control | 2025 | https://doi.org/10.1080/09537287.2024.2344066 | Q1 |
| 15 | Sustainable production planning and control in manufacturing contexts: A bibliometric review | De Simone, V., Di Pasquale, V., Nenni, M. E., & Miranda, S. | Sustainability | 2023 | https://doi.org/10.3390/su151813701 | Q1 |
| 16 | Sustainable short-term production planning optimization. | Zanella, F., & Vaz, C. B. | SN Computer Science | 2023 | https://doi.org/10.1007/s42979-023-02261-7 | Q2 |
| 17 | Integrated scheduling of production and material delivery for the intelligent manufacturing system. | Liang, T., Zhou, L., & Jiang, Z. | International Journal of Production Research | 2024 | https://doi.org/10.1080/00207543.2024.2363435 | Q1 |
| 18 | A supervised machine learning-based approach for task workload prediction in manufacturing: A case study application. | De Simone, V., Di Pasquale, V., Calabrese, J., Miranda, S., & Iannone, R. | Machines | 2025 | https://doi.org/10.3390/machines13070602 | Q2 |
| 19 | Integrated application of overall equipment effectiveness and free generative-AI tools to improve productivity in a CNC machining cell. | Hollerweger, G., Medeiros, J. L. B., Biehl, L. V., Trento, L. R., & Baierle, I. C. | Machines | 2026 | https://doi.org/10.3390/machines14060585 | Q2 |
| 20 | Potentials of using real-time data to increase the update frequency of production planning and control strategies in MTO: a discrete event simulation study. | Woschank, M., Dallasega, P., König, A., & Hofelner, M. | Flexible Services and Manufacturing Journal | 2024 | https://doi.org/10.1007/s10696-024-09550-0 | Q1 |
| 21 | Manufacturing execution system application within manufacturing small–medium enterprises towards key performance indicators development and their implementation in the production line. | Bianchini, A., Savini, I., Andreoni, A., Morolli, M., & Solfrini, V. | Sustainability | 2024 | https://doi.org/10.3390/su16072974 | Q1 |
| 22 | Capacity planning with limited information. | Anand, V., Balakrishnan, R., & Gavirneni, S. | Production and Operations Management | 2023 | https://doi.org/10.1111/poms.14004 | Q1 |
| 23 | Manufacturing management processes integration framework. | Pereira, M. Â., Vieira, G., Varela, L., Putnik, G., Cruz-Cunha, M., Santos, A., Dieguez, T., Pereira, F., Leal, N., & Machado, J. | Applied Sciences | 2025 | https://doi.org/10.3390/app15169165 | Q2 |
| 24 | A machine learning based EMA-DCPM algorithm for production scheduling. | Wang, L., Liu, H., Xia, M., Wang, Y., & Li, M. | Scientific Reports | 2024 | https://doi.org/10.1038/s41598-024-71355-w | Q1 |
| 25 | Managing product-inherent constraints with artificial intelligence: Production control for time constraints in semiconductor manufacturing. | May, M. C., Oberst, J., & Lanza, G. | Journal of Intelligent Manufacturing | 2024 | https://doi.org/10.1007/s10845-024-02472-6 | Q1 |
| 26 | Comparative analysis of human and artificial intelligence planning in production processes. | Roblek, M., Kern, T., Krhač Andrašec, E., & Brezavšček, A. | Processes | 2024 | https://doi.org/10.3390/pr12102300 | Q2 |
| 27 | A self-learning framework combining association rules and mathematical models to solve production scheduling programs. | Del Gallo, M., Antomarioni, S., & Mazzuto, G. | Production & Manufacturing Research | 2024 | https://doi.org/10.1080/21693277.2024.2332285 | Q1 |
| 28 | Applying learning and self-adaptation to dynamic scheduling. | Werth, B., Karder, J., Heckmann, M., Wagner, S., & Affenzeller, M. | Applied Sciences | 2024 | https://doi.org/10.3390/app14010049 | Q2 |
| 29 | Automated machine learning methodology for optimizing production processes in small and medium-sized enterprises. | Yarens J. Cruz, Alberto Villalonga, Fernando Castaño, Marcelino Rivas, Rodolfo E. Haber | Operations Research Perspectives | 2024 | https://doi.org/10.1016/j.orp.2024.100308 | Q1 |

Nota: Elaboración propia a partir de artículos científicos indexados en Scopus y Web of Science durante el periodo 2023–2025.

## Análisis

Con el propósito de organizar y analizar la literatura científica seleccionada, los artículos fueron clasificados en seis categorías temáticas de acuerdo con su relación con el problema de investigación y los enfoques de mejora identificados en la revisión bibliográfica. Esta clasificación permitió agrupar estudios con características similares y facilitar el análisis de sus principales aportes.

Categoría 1 — Machine Learning para la Estimación de Tiempos de Fabricación y Lead Time

#### Título del artículo:

#### Wei, Z., Li, Z., Niu, R., Jin, P., & Yu, Z. (2024). A study on the man-hour prediction in structural steel fabrication. Processes, 12(6), 1068.

Resumen del aporte del artículo:

Los autores desarrollaron un sistema de predicción de horas-hombre para el proceso de corte longitudinal en fabricación de estructuras de acero, mediante el algoritmo Random Forest Regression, aplicando one-hot encoding, normalización de datos y el coeficiente de correlación de Pearson para la selección de variables. Utilizaron una base depurada de 3,000 registros a partir de más de 5,000 datos históricos, el modelo obtuvo un RMSE de 2.96, MAPE de 6.51%, R² de 0.9447 y PSI de 0.0072, superando a los modelos SVR, BPNN y de Regresión Lineal comparados. Finalmente, concluyen que el sistema propuesto supera significativamente al método convencional de estimación por criterio de expertos, confirmando la superioridad de Random Forest en la predicción de horas-hombre en contextos de fabricación de estructuras metálicas hallazgo directamente comparable al problema y al algoritmo central del presente estudio.

#### Título del artículo:

#### Hajj Chehade, M., Sylla, A., Diallo, A. R., & Doremus, Y. (2024). Manufacturing time estimation for offer pricing: A machine learning application in a French metallurgy industry. Engineering Applications of Artificial Intelligence, 137, 109089.

Resumen del aporte del artículo:

En esta literatura, los autores implementaron Machine Learning para estimar tiempos de fabricación en una pyme metalúrgica francesa que opera bajo contexto ETO, utilizando un histórico de más de 23,000 órdenes almacenadas en ERP y evaluando ocho algoritmos mediante validación cruzada (k=5) con métricas MAE y RMSE. CatBoost resultó el modelo superior: para la familia de producto principal (n=2,119 registros) obtuvo un MAE de 1.90 en validación cruzada y 1.81 en datos recientes, superando a Random Forest, ANN y SVM. Adicionalmente, una estrategia de combinación de familias de producto permitió reducir de once a cuatro los modelos necesarios, logrando estimaciones precisas incluso en familias con tan solo 78 registros disponibles. Los resultados confirman la viabilidad del Machine Learning supervisado para la estimación de tiempos de fabricación en entornos de alta diversidad productiva y datos escasos contexto directamente análogo al de la presente investigación, y que sustenta la aplicabilidad del enfoque propuesto pese al tamaño reducido del dataset de Steelser S.A.C.

#### Título del artículo:

#### Aslan, A., Vasantha, G., El-Raoui, H., Quigley, J., Hanson, J., Corney, J., & Sherlock, A. (2023). Hierarchical ensemble deep learning for data-driven lead time prediction. The International Journal of Advanced Manufacturing Technology, 128, 4169–4188.

Resumen del aporte del artículo:

Este artículo es un desarrollo de un modelo de aprendizaje profundo jerárquico denominado HEDA para predecir el Lead Time de productos en sector de manufactura, utilizando datos reales de la planta Bosch y una simulación de producción MTO, con una base de 1,183,747 registros correspondientes a cuatro líneas de producción, 51 estaciones y cerca de 970 sensores. Se evaluaron seis tipos de productos mediante validación cruzada de 10 modelos, comparando los desempeño de HEDA con Ridge, Random Forest, kNN y redes neuronales artificiales. Los resultados mostraron que HEDA alcanzó valores de R² de hasta 0.96, mientras que Random Forest obtuvo aproximadamente un R² entre 0.91 y 0.92. Este artículo sustenta que los modelos de aprendizaje automático permiten estimar con alta precisión el Lead Time y mejorar la planificación de la producción en entornos manufactureros complejos.

#### Título del artículo:

#### Canedo Rosa, R., Carneiro Gonçalves, M., & Macêdo Barbalho, S. C. (2025). Machine learning applied to forecasting the manufacturing time of new products prototypes and ETO products: An exploratory study. International Journal of Production Economics, 287, 109688.

Resumen del aporte del artículo:

Los autores compararon resultados de diferentes modelos de machine learning como: ANN, SVM y Random Forest (RF) para predecir el Lead Time de fabricación en una empresa aeroespacial y médica que opera en contextos MTO y ETO. Utilizaron un dataset histórico de 18,329 órdenes de producción depurado a 11,356 registros válidos tras eliminar el 19.36% de outliers, evaluado mediante validación cruzada k=10 con métricas de exactitud, MAE y MSE en 12 topologías construidas a partir de variables de material y subconjunto de producto. Los resultados muestran que las topologías generales alcanzaron aproximadamente 70% de exactitud con un MAE de 3 a 4 días, mientras que al segmentar por tipo de material los modelos mejoraron sustancialmente: para AL 7075 la exactitud superó el 82% con MAE de aproximadamente 2 días para ANN y SVM, y para AL 6061 se alcanzó hasta 87.87% de exactitud (SVM) con MAE menor a 1 día; el test estadístico de Friedman confirmó diferencias significativas entre algoritmos, con SVM como superior en producción estandarizada y RF como mejor opción para órdenes de alta variabilidad.

#### Título del artículo:

#### Flores-Huamán, K.-J., Escudero-Santana, A., Muñoz-Díaz, M.-L., & Cortés, P. (2024). Lead-time prediction in wind tower manufacturing: A machine learning-based approach. Mathematics, 12(15), 2347.

#### Resumen del aporte del artículo:

#### Los autores desarrollaron e implementaron un sistema basado en Machine Learning para estimar los tiempos de distintas operaciones de fabricación con el objetivo de mejorar la cotización y la programación de la producción. En la investigación se utilizó 231,678 registros históricos provenientes de plantas de fabricación, evaluando 11 algoritmos mediante validación cruzada y métricas MAE, RMSE, MAPE, R² y R² ajustado. Los resultados evidenciaron que los modelos de ensamble, principalmente XGBoost, LightGBM y Random Forest, alcanzaron los mejores desempeños según el tipo de operación, logrando en algunos procesos coeficientes de determinación (R²) superiores a 0.90, lo que demostró la viabilidad del Machine Learning para mejorar la estimación de tiempos de fabricación y apoyar la planificación de la producción.

#### Título del artículo:

#### Çakıt, E., & Dağdeviren, M. (2023). Comparative analysis of machine learning algorithms for predicting standard time in a manufacturing environment. AI EDAM (Artificial Intelligence for Engineering Design, Analysis and Manufacturing), 37, e2.

Resumen del aporte del artículo:

El estudio de los autores, demuestran una comparación entre diferentes algoritmos de Machine Learning para la predicción de tiempos estándar en un entorno de manufactura. El objetivo principal es identificar qué modelos ofrecen mayor precisión frente a los métodos tradicionales utilizados en la industria. Para ello, se emplean datos de procesos productivos que permiten entrenar y evaluar diferentes técnicas predictivas. Los autores evidencian que los modelos basados en Machine Learning superan en precisión a los enfoques convencionales, especialmente en entornos donde existe variabilidad en los procesos.

Los resultados muestran que una mejor estimación de los tiempos estándar contribuye a una planificación más confiable de la producción. Asimismo, se mejora la programación de órdenes y se reducen errores asociados a estimaciones inexactas. Bajo este contexto, este aporte es relevante porque demuestra la utilidad del Machine Learning en la estandarización de tiempos productivos. Además, permite generar información más precisa para alimentar sistemas de planificación como el CRP, fortaleciendo la asignación de capacidad y mejorando la eficiencia operativa.

#### Título del artículo:

#### Ki, I., Song, H., Ryu, J., & Jeong, J. (2023). Production Improvement Rate with Time Series Data on Standard Time at Manufacturing Sites. Applied Sciences, 13(19), 10937.

Resumen del aporte del artículo:

En esta literatura se analiza el uso de datos de series temporales para el seguimiento y evaluación de los tiempos estándar en procesos de manufactura. El objetivo es observar cómo la evolución de estos tiempos influye en la productividad y en la planificación de la producción. A través del análisis continuo de datos en planta, los autores buscan identificar patrones que permitan mejorar la gestión operativa y la toma de decisiones.

Los resultados indican que el monitoreo constante de los tiempos estándar permite mejorar la productividad y la precisión en la planificación. Asimismo, se evidencia que contar con información actualizada facilita la programación de órdenes y reduce desviaciones en la producción. En relación con la tesis, este aporte es importante porque refuerza la necesidad de mantener datos actualizados para modelos de Machine Learning. Además, sirve como base para mejorar la estimación de requerimientos en sistemas como el CRP, contribuyendo a una planificación más precisa y eficiente del sistema productivo.

#### Título del artículo:

#### Rokoss, A., Syberg, M., & Tomidei, L. (2024). Case study on delivery time determination using a machine learning approach in small batch production companies. Journal of Intelligent Manufacturing, 35, 3937–3958.

Resumen del aporte del artículo:

Rokoss et al. (2024) analiza la aplicación de Machine Learning para la estimación de tiempos de entrega en empresas de producción por lotes pequeños,aplicando la metodología CRISP-DM extendida con Modelos Cuantitativos Logísticos. En el primer caso de estudio, 16,361 órdenes, el modelo XGBoost redujo el error de predicción de 12.1 días a 9.5 días usando solo datos del pedido, y hasta 7.7 días al incorporar variables de conocimiento del dominio (WIP, cuellos de botella, rango de sistema), una reducción de casi 50% frente a la estimación tradicional del área de planificación; en el segundo caso (2,632 órdenes), la fecha de entrega deseada por el cliente resultó la variable de mayor impacto predictivo en ambos escenarios. Para la presente investigación, este artículo resulta relevante por compartir el mismo tipo de sistema productivo y por validar empíricamente que predecir la fecha de entrega en la etapa de cotización reduce el error frente al método tradicional, confirmando además que el conocimiento del dominio productivo aporta más valor predictivo que el detalle técnico fino del proceso.

#### Título del artículo:

#### Urban, M., Koblasa, F., & Mendřický, R. (2024). Machine learning in small and medium-sized enterprises: Methodology for the estimation of the production time. Applied Sciences, 14(19), 8608.

Resumen del aporte del artículo:

Urban et al. (2024) propusieron una metodología de Machine Learning para la estimación del tiempo de producción adaptada específicamente a las necesidades de pequeñas y medianas empresas, partiendo del diagnóstico de que estas organizaciones suelen contar con un volumen de datos reducido, lo que ha limitado históricamente la adopción de técnicas de data mining y ML, manteniendo la estimación de tiempos basada en aproximaciones empíricas poco precisas y no reproducibles.

La metodología propuesta se estructura mediante la categorización de cuatro tipos de trabajo, la partición de los datos según el teorema del límite de convergencia de datos, y la definición de un nivel de riesgo basado en métricas de probabilidad y estadística, permitiendo su aplicación efectiva incluso con datos limitados. Para este estudio, el artículo resulta relevante por abordar el mismo problema estructural que enfrenta la empresa de estudio la escasez de datos históricos característica de las PYME y por proponer una metodología replicable que respalda la viabilidad de aplicar Machine Learning al presente framework pese al tamaño reducido del dataset disponible (25 proyectos).

Categoría 2 : Selección y Validación del Algoritmo Random Forest en Entornos de Manufactura

#### Título del artículo:

#### Barros, J., Gonçalves, J. N. C., Cortez, P., & Carvalho, M. S. (2023). A decision support system based on a multivariate supervised regression strategy for estimating supply lead times. Engineering Applications of Artificial Intelligence, 125, Artículo 106671.

Resumen del aporte del artículo:

Los autores proponen un sistema de soporte a la decisión basado en modelos de regresión supervisada multivariada para estimar el Lead Time de suministro, demostrando mediante datos empíricos de Bosch Automotive Electronics que el algoritmo Random Forest supera consistentemente a modelos alternativos de Árbol de Decisión, Gradient-Boosted Tree, Regresión Lineal y GLM, con un MAE de 7.378 días, un R² de 0.860 y reducciones del error absoluto medio entre 18% y 24%. Para la presente investigación, este artículo resulta relevante porque, su aporte metodológico es transferible al presente trabajo en tanto valida empíricamente la superioridad de Random Forest para la predicción de tiempos en entornos de manufactura compleja, sustentando su selección como algoritmo del Componente 2 del framework propuesto, y fundamenta además el mecanismo de calibración continua del modelo.

#### Título del artículo:

#### Ördek, B., Borgianni, Y., & Coatanea, E. (2024). Machine learning-supported manufacturing: a review and directions for future research. Production & Manufacturing Research, 12(1), 2326526.

Resumen del aporte del artículo:

Los autores realizaron una revisión de 114 artículos clasificados en cinco funciones de manufactura, selección de material, planificación de producción, selección de proceso, monitoreo y control de calidad. Los resultados muestran que el Aprendizaje Supervisado es el paradigma dominante, que Random Forest figura entre los algoritmos más utilizados junto a ANN y SVM. La principal limitación del campo es la naturaleza mono-funcional y fragmentada de las aplicaciones existentes. Para la presente investigación, este artículo aporta tres contribuciones: la elección del algoritmo Random Forest en regresión supervisada, evidencia un vacío de investigación en entornos Engineer-to-Order que el framework propuesto busca llenar, y respalda académicamente la declaración de limitaciones asociadas al tamaño reducido del dataset histórico de la presente investigación (25 proyectos).

#### Título del artículo:

#### Guerrero, B., Mula, J., & Poler, R. (2025). Sustainable optimisation approaches for production planning and control to evolve towards industry 5.0. International Journal of Production Research, 63(21), 8091–8123.

Resumen del aporte del artículo:

Guerrero et al. (2025) analizaron 77 estudios sobre optimización de la planificación y control de la producción (PPC) en contextos de Industria 4.0 e Industria 5.0. Los resultados muestran que la programación de la producción concentra el 38% de las referencias en contexto de manufactura, siendo el problema más estudiado, mientras que Machine Learning aparece en solo 6 de los 77 trabajos revisados identificando explícitamente a Random Forest, redes neuronales y aprendizaje por refuerzo profundo como las técnicas de ML predominantes en ese reducido grupo. Los autores identifican como brecha crítica la escasa implementación de estas metodologías en PYMEs, así como la ausencia de modelos que integren capacidad real de planta, tiempos estándar actualizados y cumplimiento de entrega bajo condiciones de demanda variable vacío que coincide de manera precisa con los tres componentes centrales del framework propuesto en la presente investigación.

Categoría 3: Planificación y Control de la Producción en Sistemas Make-to-Order: Lead Time y Cumplimiento de Entrega

#### Título del artículo:

#### Wolska, M., Gorewoda, T., Roszak, M., & Gajda, L. (2023). Implementation and improvement of the total productive maintenance concept in an organization. Encyclopedia, 3(4), 1537–1564.

Resumen del aporte del artículo:

El artículo formaliza las métricas operativas del TPM (OEE, MTTR, MTTF y MTBF) y define la tasa de Disponibilidad como el cociente entre el tiempo productivo real y el tiempo planificado de producción, estableciendo que valores de clase mundial exigen disponibilidades superiores al 90% con un OEE objetivo de 85% según Nakajima. La evidencia reporta que la implementación exitosa de TPM produce reducciones de costos de mantenimiento de entre 25% y 30%, eliminación de fallas de entre 70% y 75%, y reducciones del tiempo de inactividad no planificada de entre 35% y 45%, siendo la tasa de Disponibilidad el indicador central que permite cuantificar la capacidad real de operación de los equipos en entornos de manufactura industrial.

Para la tesis propuesta, este artículo resulta relevante porque formaliza matemáticamente el Factor de Disponibilidad (D) empleado en el Componente 3 del framework propuesto, y porque el umbral de 90% establecido por los autores como estándar de clase mundial sustenta directamente la meta de referencia utilizada para evaluar la disponibilidad real de planta en la empresa de estudio.

#### Título del artículo:

#### Mundt, C., & Lödding, H. (2025). Coping with the uncertainties of make-to-order production: a new approach for determining reliable delivery times with the throughput diagram. Production Planning & Control, 36(8), 1110–1136.

Resumen del aporte del artículo:

El artículo aborda el problema central de la determinación de fechas de entrega confiables en empresas de producción bajo pedido (MTO), donde la incertidumbre sobre qué ofertas serán aceptadas por el cliente y qué carga de capacidad representarán constituye la principal causa de incumplimiento de plazos. Es por ello, que los autores proponen el procedimiento denominado Planned Output Control (POC), basado en el diagrama de throughput derivado del modelo embudo, que determina fechas de entrega individuales para cada orden. Los resultados de tres estudios de simulación con 10,000 ofertas cada uno demuestran que el POC, combinado con liberación de órdenes CONWIP y secuenciación EODD, alcanza tasas de cumplimiento de entrega de entre 97.1% y 99.9% bajo escenarios de carga balanceada y sobrecarga del 5%, frente a valores de 41.9% a 91.0% obtenidos con tiempos de entrega estándar bajo las mismas condiciones Para la presente investigación, este artículo resulta relevante porque valida que incorporar la capacidad real de planta en la programación de órdenes eleva el cumplimiento de entregas, sustentando directamente la lógica de CRP ajustado por Disponibilidad y proporcionando la referencia cuantitativa utilizada para proyectar la meta de OTD del presente estudio.

#### Título del artículo:

#### De Simone, V., Di Pasquale, V., Nenni, M. E., & Miranda, S. (2023). Sustainable production planning and control in manufacturing contexts: A bibliometric review. Sustainability, 15(18), 13701.

Resumen del aporte del artículo:

El estudio realiza un análisis de varios artículos, con el objetivo de mapear las brechas de investigación en Planificación y Control de la Producción. Esta investigación es bajo principios de sostenibilidad, con lo que demuestran una aceleración reciente del campo, liderado por China, Estados Unidos y Alemania, situando a Machine Learning e Industria 4.0 como temas emergentes desde 2016, mientras que los sistemas de soporte a la decisión para PPC se clasifican como temas en desarrollo insuficiente. Para la presente investigación, este artículo resulta relevante porque concluye que la reducción del Lead Time y el desarrollo de herramientas de decisión inteligentes para PPC constituyen brechas de investigación prioritarias aún no cubiertas sistemáticamente, respaldando la pertinencia del framework propuesto como respuesta directa a estas brechas.

#### 2.2.3.4. Título del artículo:

#### Zanella, F., & Vaz, C. B. (2023). Sustainable short-term production planning optimization. SN Computer Science, 4, 824.

### Resumen del aporte del artículo:

Zanella y Vaz (2023) desarrollan un modelo de optimización enfocado en la planificación de la producción a corto plazo, cuyo propósito es mejorar la asignación de los recursos disponibles y optimizar la programación de las actividades productivas. La propuesta considera las restricciones propias del sistema de producción y plantea una formulación matemática que permite organizar las órdenes de trabajo de manera más eficiente, favoreciendo un mejor control de las operaciones.

Los autores concluyen que una planificación basada en criterios estructurados contribuye a aprovechar de forma más eficiente la capacidad instalada, disminuye las desviaciones en la programación y favorece una ejecución más estable de las órdenes de producción. En el contexto de la presente investigación, este estudio respalda la incorporación del modelo CRP, ya que demuestra la importancia de planificar la producción considerando la capacidad disponible de la planta. Asimismo, su aporte fortalece la propuesta de integrar la planificación con herramientas de apoyo a la toma de decisiones, con el objetivo de mejorar el cumplimiento de las entregas de estructuras metálicas.

#### 2.2.3.5. Título del artículo:

#### Liang, T., Zhou, L., & Jiang, Z. (2024). Integrated scheduling of production and material delivery for the intelligent manufacturing system. International Journal of Production Research. Advance online publication.

### Resumen del aporte del artículo:

Liang et al. (2024) presentan un modelo integrado orientado a coordinar la programación de la producción con el suministro de materiales en entornos de manufactura inteligente. La propuesta busca sincronizar ambas actividades para minimizar los problemas ocasionados por la falta de coordinación, como retrasos en la producción, interrupciones del flujo de trabajo y cuellos de botella. Para ello, el modelo combina la programación de las órdenes de producción con las decisiones relacionadas con el abastecimiento de materiales.

Los resultados obtenidos demuestran que la integración entre la planificación de la producción y la gestión de materiales favorece el cumplimiento de los plazos establecidos, mejora la utilización de los recursos disponibles y disminuye la variabilidad durante la ejecución de las operaciones. En la presente investigación, este aporte sustenta la necesidad de fortalecer la planificación mediante un enfoque integrado. Asimismo, respalda la incorporación del modelo CRP junto con Machine Learning, ya que ambas herramientas permiten mejorar la programación de las órdenes de producción y contribuir al incremento del cumplimiento de las entregas de estructuras metálicas.

#### 2.2.3.6. Título del artículo:

#### De Simone, V., Di Pasquale, V., Calabrese, J., Miranda, S., & Iannone, R. (2025). A supervised machine learning-based approach for task workload prediction in manufacturing: A case study application. Machines, 13(7), 602.

### Resumen del aporte del artículo:

De Simone et al. (2025) desarrollan un modelo basado en Machine Learning para estimar la carga de trabajo en procesos de manufactura de pequeñas y medianas empresas. La propuesta emplea información histórica de producción para entrenar algoritmos de aprendizaje supervisado capaces de predecir el esfuerzo necesario en cada operación, disminuyendo la dependencia de estimaciones realizadas únicamente por experiencia del personal.

Los resultados obtenidos indican que el uso de modelos predictivos mejora la precisión en la estimación de la carga de trabajo, favorece una asignación más eficiente de los recursos disponibles y contribuye a una planificación más confiable de las operaciones. Además, los autores evidencian una reducción de los cuellos de botella y un mejor cumplimiento de los plazos establecidos.

En el desarrollo de la presente investigación, este estudio respalda la incorporación de Machine Learning como herramienta para estimar los tiempos de fabricación a partir de datos históricos. Asimismo, complementa el modelo CRP, al proporcionar información más precisa sobre la carga de trabajo requerida para cada proyecto, facilitando la planificación de la capacidad y contribuyendo a mejorar el cumplimiento de las entregas de estructuras metálicas.

2.2.4. Categoría 4 — Disponibilidad de Máquina, TPM y Capacidad Real de Planta

#### 2.2.4.1. Título del artículo:

#### Hollerweger, G., Medeiros, J. L. B., Biehl, L. V., Trento, L. R., & Baierle, I. C. (2026). Integrated application of overall equipment effectiveness and free generative-AI tools to improve productivity in a CNC machining cell. Machines, 14(6), 585.

### Resumen del aporte del artículo:

El estudio desarrolló un caso de aplicación en una empresa del sector metalmecánico para analizar el desempeño de una celda de mecanizado mediante el uso de herramientas de inteligencia artificial generativa, empleando información histórica proveniente del sistema MES durante un periodo de 31 meses. El objetivo fue identificar las principales causas que afectaban la eficiencia global de los equipos (OEE) y evaluar el potencial de estas herramientas como apoyo en el análisis de datos y la toma de decisiones.

Los resultados mostraron que la principal limitación del proceso correspondía a la baja disponibilidad de los equipos, ocasionada principalmente por paradas no programadas. Entre las causas identificadas destacaron el mantenimiento correctivo, la falta de repuestos, deficiencias en las actividades de lubricación y la ausencia de procedimientos estandarizados durante el cambio de herramientas. Asimismo, la comparación entre ChatGPT, Gemini y Copilot evidenció diferencias en la calidad de los diagnósticos, obteniendo ChatGPT el mejor desempeño en consistencia y profundidad del análisis.

Como resultado del diagnóstico, se formuló un plan de mejora orientado a incrementar la disponibilidad de los equipos y elevar el indicador OEE hasta niveles cercanos al estándar de referencia propuesto por el JIPM.

En la presente investigación, este artículo respalda la incorporación del modelo TPM, al demostrar que la disponibilidad de los equipos tiene una influencia directa sobre la capacidad real de producción. Del mismo modo, sus resultados justifican la integración del modelo CRP, ya que una adecuada planificación de la capacidad requiere considerar las paradas de los equipos. Finalmente, el uso de herramientas basadas en inteligencia artificial evidencia el potencial del Machine Learning para apoyar el análisis de información histórica y fortalecer la planificación de la producción, contribuyendo al cumplimiento de las entregas de estructuras metálicas.

#### 2.2.4.2. Título del artículo:

#### Woschank, M., Dallasega, P., König, A., & Hofelner, M. (2024). Potentials of using real-time data to increase the update frequency of production planning and control strategies in MTO: a discrete event simulation study. Flexible Services and Manufacturing Journal, 36, 760–779.

### Resumen del aporte del artículo:

El estudio analizó, mediante simulación de eventos discretos, el efecto de actualizar con mayor frecuencia los parámetros utilizados en la planificación de la producción dentro de un entorno Make-to-Order (MTO). Para ello, se comparó el desempeño de diferentes estrategias de planificación y control de la producción utilizando información real de una empresa del sector electrónico.

Los resultados demostraron que la actualización periódica de variables como los tiempos de ciclo, tiempos de preparación y lead time influye significativamente en el desempeño del sistema productivo. En particular, algunas estrategias lograron reducir el tiempo de fabricación y mejorar el cumplimiento de las entregas, mientras que otras presentaron un comportamiento menos eficiente cuando trabajaban con información desactualizada. Asimismo, el estudio evidenció que la precisión de los parámetros de planificación tiene un impacto directo en la utilización de los recursos y en la estabilidad del proceso productivo.

En la presente investigación, este trabajo respalda la importancia de mantener tiempos estándar actualizados mediante el módulo de estandarización del trabajo, ya que la utilización de datos obsoletos puede afectar la estimación de los tiempos de fabricación y la programación de la producción. Además, sus resultados fortalecen la implementación del modelo CRP, al demostrar que una planificación basada en información confiable permite gestionar de manera más eficiente la capacidad de producción. Finalmente, este aporte complementa el uso de Machine Learning, ya que la calidad de los pronósticos depende de la disponibilidad de datos históricos consistentes y actualizados.

#### 2.2.4.3. Título del artículo:

#### Bianchini, A., Savini, I., Andreoni, A., Morolli, M., & Solfrini, V. (2024). Manufacturing execution system application within manufacturing small–medium enterprises towards key performance indicators development and their implementation in the production line. Sustainability, 16(7), 2974.

### Resumen del aporte del artículo:

El estudio implementó un Sistema de Ejecución de Manufactura (MES) en una empresa metalmecánica italiana con 50 trabajadores, dedicada a la fabricación de piezas de precisión mediante 18 máquinas CNC. La investigación siguió una metodología cuantitativa basada en cuatro etapas: análisis de la arquitectura para la captura de datos, definición de indicadores de desempeño, evaluación de la calidad de los datos y aplicación de herramientas de ciencia de datos para el monitoreo de la producción.

Como parte de la implementación se desarrollaron cuatro indicadores operativos relacionados con la utilización de los equipos, la disponibilidad de las máquinas, la eficiencia del ciclo de producción y el nivel de saturación de la capacidad instalada. Los resultados evidenciaron que, tras un año de funcionamiento del sistema, la empresa incrementó su rentabilidad en 7 % respecto al promedio obtenido en los tres años anteriores. Asimismo, el seguimiento continuo de los indicadores permitió mejorar el control de la producción y favorecer una mayor eficiencia operativa.

En la presente investigación, este artículo respalda la incorporación del modelo TPM, debido a que demuestra la importancia de monitorear la disponibilidad de los equipos para conocer la capacidad real de la planta. Del mismo modo, la información generada por el sistema MES constituye una base confiable para alimentar los modelos de Machine Learning y mejorar la planificación mediante el modelo CRP, contribuyendo a incrementar el cumplimiento de las entregas de estructuras metálicas.

#### 2.2.4.4. Título del artículo:

#### Anand, V., Balakrishnan, R., & Gavirneni, S. (2023). Capacity planning with limited information. Production and Operations Management, 32(9), 2740–2757.

### Resumen del aporte del artículo:

Anand et al. (2023) desarrollaron un estudio cuantitativo orientado a mejorar la planificación de la capacidad en sistemas productivos donde la información disponible presenta incertidumbre o es incompleta. Para ello, propusieron modelos de optimización capaces de estimar los requerimientos de capacidad considerando escenarios con datos limitados, permitiendo apoyar la toma de decisiones en la programación de la producción bajo condiciones más cercanas a la realidad operativa.

Los resultados demostraron que la aplicación de estos modelos permitió una asignación más eficiente de los recursos productivos, reduciendo los cuellos de botella y las diferencias entre la capacidad planificada y la capacidad realmente disponible en planta. Asimismo, los autores evidenciaron que incorporar la incertidumbre en el proceso de planificación mejora la confiabilidad de la programación y favorece el cumplimiento de los tiempos establecidos para la producción.

En la presente investigación, este artículo sustenta la implementación del modelo CRP (Capacity Requirements Planning), ya que demuestra la importancia de planificar la capacidad considerando las condiciones reales de operación. Además, sus hallazgos respaldan la integración del modelo TPM, debido a que la disponibilidad de los equipos influye directamente en la capacidad efectiva de la planta. Finalmente, este aporte complementa el uso de Machine Learning, ya que estimaciones más precisas de los tiempos de fabricación permiten alimentar el modelo de planificación con información más confiable y contribuir al incremento del cumplimiento de las entregas de estructuras metálicas.

2.2.5. Categoría 5 — Frameworks de Integración Digital entre Gestión Comercial y Planta: Arquitecturas Industry 4.0 aplicadas a la Manufactura

#### 2.2.5.1. Título del artículo:

#### Pereira, M. Â., Vieira, G., Varela, L., Putnik, G., Cruz-Cunha, M., Santos, A., Dieguez, T., Pereira, F., Leal, N., & Machado, J. (2025). Manufacturing management processes integration framework. Applied Sciences, 15(16), 9165.

### Resumen del aporte del artículo:

El estudio presenta un framework modular para integrar los procesos de gestión en empresas manufactureras bajo los enfoques de Industria 4.0 e Industria 5.0. La propuesta incorpora tecnologías como Internet de las Cosas (IoT), Inteligencia Artificial y Machine Learning, gemelos digitales y paneles de monitoreo, con el propósito de facilitar el intercambio de información entre los niveles estratégico y operativo de la organización. La validación del modelo se realizó en tres empresas manufactureras de Portugal, mediante la aplicación de un cuestionario de 10 preguntas en escala Likert de cinco niveles a 32 participantes.

Los resultados mostraron que la gestión integrada de los procesos fue el aspecto mejor valorado por los participantes, seguida de la capacidad del framework para operar de forma distribuida y del acceso a información en tiempo real. En contraste, las funcionalidades relacionadas con realidad aumentada y sistemas ciberfísicos obtuvieron las puntuaciones más bajas. Los autores señalan como principal limitación que la validación se basó en la percepción de los participantes y que no se evaluó el impacto del framework mediante indicadores objetivos de desempeño.

En la presente investigación, este artículo respalda la importancia de integrar la información entre las áreas de cotizaciones, planificación y producción, uno de los problemas identificados en el diagnóstico de Steelser S.A.C. Asimismo, sustenta el uso de Machine Learning como herramienta para el análisis de datos y la toma de decisiones, complementando el modelo CRP y el módulo de estandarización del trabajo, al promover una planificación basada en información integrada y actualizada que contribuya a mejorar el cumplimiento de las entregas de estructuras metálicas.

2.2.6. Categoría 6: Aplicación de Machine Learning en la programación, optimización y control de la producción en entornos manufactureros

#### 2.2.6.1. Título del artículo:

#### Wang, L., Liu, H., Xia, M., Wang, Y., & Li, M. (2024). A machine learning based EMA-DCPM algorithm for production scheduling. Scientific Reports, 14, 20810.

### Resumen del aporte del artículo:

Wang et al. (2024) desarrollaron un algoritmo de Machine Learning denominado EMA-DCPM, diseñado para optimizar la programación de la producción en entornos manufactureros con alta complejidad operativa. La investigación se basa en el análisis de datos históricos para generar una secuencia de producción capaz de adaptarse a las variaciones en la carga de trabajo, mejorando la asignación de las órdenes y la utilización de los recursos disponibles.

Los resultados obtenidos evidenciaron que el algoritmo incrementó la precisión en la programación de las órdenes de producción, redujo la variabilidad en los tiempos de ejecución y disminuyó los retrasos frente a los métodos tradicionales de planificación. Asimismo, el modelo logró una mayor estabilidad en la secuenciación de las operaciones, permitiendo una respuesta más eficiente ante cambios en las condiciones del proceso productivo.

En la presente investigación, este artículo sustenta la aplicación de Machine Learning para mejorar la estimación de los tiempos de fabricación y apoyar la planificación de la producción mediante información histórica. Además, sus resultados complementan la implementación del modelo CRP, ya que una programación más precisa facilita la asignación de la capacidad disponible y reduce las desviaciones en la ejecución de los proyectos. Finalmente, el estudio refuerza la importancia de integrar herramientas predictivas con un módulo de estandarización del trabajo y el modelo TPM, con el propósito de incrementar el cumplimiento de las entregas de estructuras metálicas.

#### 2.2.6.2. Título del artículo:

#### May, M. C., Oberst, J., & Lanza, G. (2024). Managing product-inherent constraints with artificial intelligence: Production control for time constraints in semiconductor manufacturing. Journal of Intelligent Manufacturing, 35, 4259–4276.

### Resumen del aporte del artículo:

El estudio desarrollado por May et al. (2024) propone un sistema basado en inteligencia artificial aplicado a la gestión de restricciones dentro de entornos manufactureros complejos, específicamente en procesos de fabricación de semiconductores. La investigación analiza cómo la incorporación de modelos inteligentes permite mejorar la planificación productiva mediante el ajuste dinámico de las decisiones operativas frente a variaciones en la demanda, disponibilidad de recursos y condiciones del proceso. Los resultados evidencian que el modelo propuesto incrementa la capacidad de respuesta del sistema, reduciendo los impactos generados por restricciones temporales y mejorando la estabilidad en la programación de órdenes de producción.

Desde un enfoque cuantitativo, los autores evalúan el desempeño del sistema considerando variables asociadas al cumplimiento de fechas de entrega, utilización de recursos críticos y comportamiento de la programación ante escenarios variables. A diferencia de los métodos tradicionales de planificación, que presentan limitaciones frente a la alta variabilidad y complejidad del entorno industrial, el modelo basado en inteligencia artificial permite identificar posibles conflictos de programación de manera anticipada y ajustar la asignación de recursos de acuerdo con las condiciones reales del proceso.

El aporte de esta investigación para la presente tesis radica en demostrar la importancia de integrar herramientas basadas en Machine Learning dentro de los sistemas de planificación y control de producción. Asimismo, evidencia que la incorporación de restricciones operativas reales constituye un factor fundamental para mejorar la precisión de modelos como el Capacity Requirements Planning (CRP), permitiendo generar planes de producción más confiables y alineados con la capacidad disponible. En este sentido, el estudio confirma que la inteligencia artificial representa una alternativa viable para incrementar la estabilidad operativa y mejorar el desempeño de sistemas productivos con alta variabilidad.

#### 2.2.6.3. Título del artículo:

#### Roblek, M., Kern, T., Krhač Andrašec, E., & Brezavšček, A. (2024). Comparative analysis of human and artificial intelligence planning in production processes. Processes, 12(10), 2300.

### Resumen del aporte del artículo:

La investigación desarrollada por Roblek et al. (2024) realiza un análisis comparativo entre los métodos tradicionales de planificación de la producción ejecutados por especialistas humanos y aquellos generados mediante sistemas basados en inteligencia artificial. El objetivo del estudio fue determinar las diferencias en términos de consistencia, eficiencia y confiabilidad de las decisiones de programación dentro de escenarios productivos caracterizados por elevados niveles de complejidad y variabilidad. Para ello, los autores evaluaron el comportamiento de ambos enfoques considerando indicadores relacionados con la estabilidad de los planes de producción, repetibilidad de resultados y capacidad de respuesta ante cambios en las condiciones operativas.

Los hallazgos obtenidos muestran que los sistemas basados en inteligencia artificial presentan un desempeño superior en la generación de planes de producción más consistentes y reproducibles, debido a su capacidad para procesar grandes cantidades de información y aplicar criterios de decisión de manera uniforme. En contraste, la planificación desarrollada exclusivamente por operadores humanos, aunque conserva una mayor capacidad de adaptación basada en experiencia, presenta mayores niveles de variabilidad asociados a la subjetividad y diferencias en los criterios utilizados durante la toma de decisiones.

Asimismo, el estudio evidencia que la aplicación de inteligencia artificial contribuye a reducir errores derivados de la intervención manual y mejora la eficiencia del proceso de programación al analizar múltiples variables en periodos reducidos de tiempo. Estos resultados demuestran que los modelos inteligentes pueden fortalecer los sistemas de planificación en ambientes industriales donde existen restricciones de capacidad y cambios frecuentes en los requerimientos productivos.

El aporte de esta investigación para la presente tesis se relaciona con la necesidad de incorporar herramientas basadas en Machine Learning para mejorar la precisión de la planificación de producción. Además, respalda la integración de algoritmos predictivos con modelos de Capacity Requirements Planning (CRP), permitiendo generar planes de capacidad más confiables al considerar datos históricos y condiciones reales de operación. Finalmente, los autores plantean que la combinación entre experiencia humana y sistemas inteligentes representa una alternativa adecuada para alcanzar una planificación más eficiente y adaptable.

#### 2.2.6.4. Título del artículo:

#### Del Gallo, M., Antomarioni, S., & Mazzuto, G. (2024). A self-learning framework combining association rules and mathematical models to solve production scheduling programs. Production & Manufacturing Research, 12(1).

### Resumen del aporte del artículo:

El trabajo desarrollado por Del Gallo et al. (2024) plantea un marco de autoaprendizaje orientado a optimizar la programación de la producción mediante la integración de técnicas de minería de datos y modelos matemáticos de optimización. La investigación tiene como objetivo diseñar un sistema capaz de analizar información histórica del proceso productivo, identificar relaciones entre variables operativas y utilizar estos patrones para mejorar progresivamente la toma de decisiones asociada al scheduling. Mediante el procesamiento de datos generados durante las operaciones, el modelo permite reconocer comportamientos recurrentes y ajustar la asignación de recursos, tiempos de fabricación y secuencias de producción.

Desde un enfoque cuantitativo, los autores evalúan el desempeño del modelo considerando métricas relacionadas con la eficiencia de programación, utilización de recursos y reducción de desviaciones generadas durante la planificación. Los resultados obtenidos evidencian que la incorporación de mecanismos de aprendizaje continuo permite disminuir errores de programación y mejorar la capacidad de adaptación del sistema frente a cambios en las condiciones productivas. Asimismo, el enfoque híbrido propuesto combina la capacidad predictiva de los métodos basados en datos con la precisión de los modelos matemáticos, logrando una mayor confiabilidad en la generación de planes de producción.

El principal aporte de este estudio para la presente investigación se encuentra en la importancia del aprendizaje adaptativo como elemento clave para fortalecer los sistemas de planificación productiva. En este sentido, la investigación respalda la incorporación de modelos basados en Machine Learning utilizando datos históricos como fuente de predicción para mejorar la estimación de requerimientos de capacidad dentro de un sistema CRP. Además, demuestra que los modelos auto aprendientes pueden contribuir a una mejora continua del proceso de planificación, incrementando la precisión de las decisiones operativas y la confiabilidad del sistema productivo.

#### 2.2.6.5. Título del artículo:

#### Werth, B., Karder, J., Heckmann, M., Wagner, S., & Affenzeller, M. (2024). Applying learning and self-adaptation to dynamic scheduling. Applied Sciences, 14(1), 49.

### Resumen del aporte del artículo:

El estudio desarrollado por Werth et al. (2024) analiza la aplicación de métodos de aprendizaje automático y mecanismos de auto adaptación para mejorar la programación dinámica de la producción en ambientes industriales con alta variabilidad. La investigación aborda escenarios donde factores como fluctuaciones en la demanda, interrupciones por fallas de equipos y cambios en las condiciones operativas afectan la estabilidad de los planes de producción. Frente a esta problemática, los autores plantean modelos capaces de ajustar automáticamente las decisiones de programación utilizando información actualizada del sistema productivo.

Desde una perspectiva cuantitativa, el estudio evalúa el desempeño del modelo considerando variables asociadas al cumplimiento de fechas planificadas, estabilidad de la programación, capacidad de respuesta ante eventos inesperados y eficiencia operativa. Los resultados muestran que los sistemas basados en aprendizaje automático presentan una mayor capacidad de adaptación frente a escenarios dinámicos, debido a que pueden identificar desviaciones durante la ejecución y generar ajustes en la planificación sin depender completamente de la intervención humana.

Asimismo, la investigación evidencia que los modelos auto adaptativos contribuyen a reducir los efectos negativos ocasionados por eventos no previstos, permitiendo mantener una mayor continuidad operativa y mejorar la confiabilidad de los programas de producción. A diferencia de los métodos convencionales, que requieren frecuentes modificaciones manuales ante cambios en el entorno, los sistemas inteligentes permiten una respuesta más rápida y consistente mediante el análisis continuo de los datos generados por el proceso.

El aporte de este estudio para la presente tesis radica en demostrar la importancia de incorporar algoritmos de Machine Learning en sistemas productivos con incertidumbre y restricciones variables. Además, respalda la integración del Capacity Requirements Planning (CRP) con modelos predictivos capaces de actualizar los requerimientos de capacidad según las condiciones reales de operación. De esta manera, se fortalece la propuesta de utilizar herramientas inteligentes para mejorar la precisión de la planificación, reducir desviaciones en los tiempos de entrega e incrementar la resiliencia del sistema productivo.

#### 2.2.6.6. Título del artículo:

#### Automated machine learning methodology for optimizing production processes in small and medium-sized enterprises. (2024). Operations Research Perspectives, 12, 100308.

### Resumen del aporte del artículo:

El artículo presenta una metodología basada en AutoML orientada a facilitar la implementación de modelos de Machine Learning en pequeñas y medianas empresas, automatizando etapas como la selección, entrenamiento y ajuste de algoritmos predictivos. El estudio evalúa su desempeño mediante indicadores relacionados con la precisión de predicción, eficiencia operativa y capacidad de respuesta del sistema productivo.

Los resultados evidencian que esta metodología permite reducir las barreras tecnológicas para la adopción de inteligencia artificial en las PYMES, mejorando la toma de decisiones mediante el análisis automatizado de datos históricos. Asimismo, contribuye a optimizar el uso de recursos y reducir desviaciones en la planificación de actividades productivas.

El aporte de esta investigación para la presente tesis radica en demostrar la aplicabilidad del Machine Learning en entornos industriales reales. Además, respalda la integración de modelos predictivos con el CRP para mejorar la estimación de capacidad y generar planes de producción más ajustados a las condiciones operativas de la empresa.

#### 2.2.6.7. Título del artículo:

#### Zhang, H., Li, X., Wang, S., & Liu, J. (2024). Deep reinforcement learning for dynamic job shop scheduling under uncertain manufacturing environments. Computers & Industrial Engineering, 190, 109978.

Resumen del aporte del artículo:

El estudio de Zhang et al. (2024) propone un modelo basado en Deep Reinforcement Learning para la programación dinámica de la producción en sistemas job shop bajo condiciones de incertidumbre. El modelo permite optimizar la secuenciación de órdenes considerando variaciones en tiempos de proceso, llegada de trabajos y disponibilidad de máquinas.

Los resultados muestran que el enfoque supera a métodos tradicionales y heurísticos, logrando reducir el makespan y mejorar la estabilidad del sistema productivo. Asimismo, el modelo se adapta en tiempo real a cambios operativos sin necesidad de reprogramación manual. En el contexto de la tesis, este aporte respalda el uso de técnicas avanzadas de Machine Learning para mejorar la programación de la producción e integrar la planificación con sistemas como CRP.

## Conclusiones

#### Conclusión general

Del análisis de la literatura científica revisada se concluye que la aplicación de Machine Learning en la planificación, programación y control de la producción representa una tendencia consolidada en la manufactura moderna, especialmente en entornos de alta variabilidad como los sistemas Make-to-Order y Engineer-to-Order. Los estudios evidencian que los modelos predictivos basados en aprendizaje automático, particularmente Random Forest, XGBoost, CatBoost y redes neuronales, superan consistentemente a los métodos tradicionales en la estimación de tiempos de fabricación, Lead Time y carga de trabajo, mejorando la precisión de la planificación y reduciendo la incertidumbre operativa.

Asimismo, se identifica que la integración de estos modelos con sistemas de planificación de capacidad como CRP, junto con indicadores de desempeño como OEE y disponibilidad de máquina, permite cerrar la brecha entre la planificación teórica y la capacidad real de planta. Sin embargo, también se evidencia una limitada integración de estas herramientas en sistemas unificados, especialmente en PYMEs del sector metalmecánico, donde predominan métodos empíricos y datos no estructurados. En consecuencia, se concluye que existe una necesidad de desarrollar modelos integrados que articulen Machine Learning, planificación de capacidad y control de producción para mejorar el desempeño operativo en entornos industriales complejos.

#### Categoría 1: Machine Learning para la estimación de tiempos de fabricación y Lead Time

Se concluye que el Machine Learning constituye una herramienta altamente efectiva para la estimación de tiempos de fabricación y Lead Time en entornos productivos con alta variabilidad. Los modelos supervisados, especialmente los basados en ensamble, logran altos niveles de precisión al capturar relaciones complejas entre variables de producción, superando a los métodos tradicionales basados en estimaciones empíricas. Asimismo, se evidencia que la calidad del modelo depende directamente de la calidad, volumen y segmentación de los datos históricos utilizados.

#### Categoría 2: Selección y validación del algoritmo Random Forest en manufactura

Se concluye que el algoritmo Random Forest se posiciona como uno de los modelos más robustos y consistentes para la predicción de tiempos en entornos manufactureros complejos. Su capacidad para manejar datos no lineales, ruidosos y heterogéneos lo hace especialmente adecuado para problemas de planificación en producción. La literatura confirma su superioridad frente a modelos como SVM, ANN y regresión lineal, lo que justifica su uso como base metodológica en sistemas predictivos industriales.

#### Categoría 3: Planificación y control de la producción en sistemas MTO

Se concluye que la planificación de la producción en sistemas Make-to-Order está fuertemente influenciada por la incertidumbre de la demanda, la variabilidad de los procesos y las limitaciones de capacidad. Los modelos avanzados de planificación, simulación y optimización permiten mejorar el cumplimiento de entregas y reducir desviaciones en los tiempos de producción. No obstante, aún existe una brecha en la integración en tiempo real de estos modelos con sistemas inteligentes de soporte a la decisión.

#### Categoría 4: Disponibilidad de máquina, TPM y capacidad real de planta

Se concluye que la disponibilidad de máquina es el factor más determinante en la capacidad real de producción dentro de entornos industriales. Indicadores como OEE, MTTR y MTBF permiten medir de manera objetiva el desempeño operativo, siendo la disponibilidad el componente crítico en la eficiencia del sistema productivo. Asimismo, la implementación de TPM y sistemas MES contribuye significativamente a mejorar la confiabilidad de los equipos y la precisión de la planificación de capacidad.

#### Categoría 5: Frameworks de integración digital entre gestión comercial y planta

Se concluye que los frameworks de integración digital basados en Industry 4.0 permiten mejorar la conexión entre la gestión comercial y la planta de producción mediante el uso de tecnologías como IoT, inteligencia artificial y sistemas en la nube. Estos modelos facilitan la toma de decisiones en tiempo real y mejoran la coherencia entre planificación estratégica y ejecución operativa. Sin embargo, su aplicación aún es limitada en entornos reales, especialmente en PYMEs, debido a la falta de validación operativa completa.

#### Categoría 6: Machine Learning en programación, optimización y control de la producción

Se concluye que la aplicación de Machine Learning en la programación y control de la producción mejora significativamente la eficiencia operativa mediante la optimización de la asignación de órdenes, la reducción de retrasos y la adaptación dinámica a cambios en el sistema productivo. Los modelos auto-adaptativos y enfoques híbridos permiten una planificación más estable y eficiente en entornos dinámicos, consolidando el uso de inteligencia artificial como herramienta clave en la evolución de los sistemas de planificación industrial.
