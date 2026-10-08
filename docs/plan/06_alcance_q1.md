# 06 · Alcance y ruta a una revista Q1

> Decisión de alcance a partir de lo construido y de los resultados sobre el gemelo ([analisis/09](../analisis/09_resultados_gemelo.md)). Sustituye al enfoque «el DSS gana al cotizador» de [analisis/03](../analisis/03_potencial_q1.md), que los datos no sostienen. Complementa [plan/05](05_planta_3d.md) (3D) y [analisis/06](../analisis/06_ruta_q1_y_ampliacion_bd.md).

## 1. Franqueza: qué atacaría un revisor Q1

| Ataque | Estado |
|---|---|
| «La verdad sale del mismo motor que el DSS» (circularidad) | **Resuelto en simulación**: gemelo de eventos discretos hora a hora, independiente del planificador diario, con azar común entre políticas |
| «N = 25 proyectos, sin datos reales» | **Sin resolver.** Es el bloqueo. Con N = 25 los IC de proporciones son de ±16 puntos; detectar +10 puntos de cumplimiento exige ≈ 70–80 proyectos |
| «El DSS no supera a un colchón fijo» | **Cierto en el gemelo.** Hay que replantear la contribución (sección 2) |
| «QRF, Monte Carlo, conformal, gemelo y 3D no son nuevos» | Cierto; Mehdiyev et al. 2025 ya usa QRF en manufactura. La novedad solo puede ser la integración y el hallazgo |
| «La gestión recomendada no funciona» | **Hallazgo propio**: el modelo de planificación omite lo que domina el plazo (proveedores, pintura). Es riesgo de modelo, y es publicable |
| «Costos y proveedores son supuestos» | Declarado. Se reemplazan con datos de la empresa (diseno/08 §6) |

## 2. Contribución defendible (reformulada)

No «el DSS acierta mejor que el cotizador», sino:

1. **Cotización probabilística de fecha anclada al experto y calibrada** para una pyme de manufactura bajo pedido con pocos proyectos: QRF sobre el factor de corrección de horas + calibración conformal agrupada por proyecto + Monte Carlo de capacidad finita; con α = 0.80 cumple 80 %, y entrega probabilidad de cumplir y penalidad esperada para negociar.
2. **Un banco de pruebas contrafactual con gemelo de eventos discretos** para evaluar políticas de compromiso y de gestión con **números aleatorios comunes** sobre la historia real de la empresa: método reutilizable y replicable (código abierto).
3. **Hallazgo de riesgo de modelo**: las palancas de capacidad que recomienda un planificador diario no mueven la fecha cuando el plazo lo dominan proveedores y servicios externos; el efecto de cada palanca hay que medirlo (lazo cerrado), no suponerlo.
4. **Alerta temprana** con probabilidad calibrada: AUC 0.83 en el último cuarto del plazo (simulado).
5. **Evaluación con usuarios** de si el gemelo 3D mejora la decisión frente a tablas (SUS, tiempo, calidad de decisión): lo que le da sentido científico al 3D.

Revistas candidatas (verificar cuartil actual en SJR): *International Journal of Production Research*, *Production Planning & Control*, *Journal of Manufacturing Systems*, *Computers & Industrial Engineering*, *Simulation Modelling Practice and Theory*, *Journal of Intelligent Manufacturing*.

## 3. Alcance: qué entra, qué se congela y qué se quita

| Pieza | Decisión | Por qué |
|---|---|---|
| C1 formato único y registro (importador, tareo, paradas, compras) | **Entra** | Es la fuente de los datos reales; sin él no hay Q1 |
| C2 QRF anclado al plan del cotizador + conformal | **Entra** | Núcleo de la contribución 1 |
| C3 CRP + Monte Carlo con esperas de compras e ingeniería aprendidas y solapes calibrados | **Entra** | Núcleo |
| **Gemelo de eventos discretos** (`dss/gemelo/`) | **Entra** | Banco de pruebas y contribución 2 |
| C4 lazo cerrado: alerta temprana, medición del efecto de palancas, reentrenamiento | **Entra; falta implementarlo** | Es la respuesta al hallazgo 3 |
| Vista **Gemelo 3D** | **Entra, como herramienta de explicación y de la prueba con usuarios** | No es contribución por sí sola |
| α\* newsvendor | **Entra** | Pero sin cotizaciones perdidas solo se reporta la frontera |
| Gestión con palancas (`dss/whatif.py`) | **Entra como experimento negativo y como módulo a validar con datos reales** | No se vende como mejora |
| Motor multi-proyecto del CRP (`dss/multiproyecto.py`) | **Se congela** | Útil, sin uso en los resultados; el gemelo ya modela la competencia por recursos |
| Estudio retrospectivo con el CRP como verdad (exp5, `dss/retrospectivo.py`) | **Se congela como histórico** | Sustituido por exp6; queda para reproducir `analisis/08` |
| Cotizador Streamlit (`app/streamlit_app.py`) | **Se retira de la tesis** | SteelPlan lo reemplaza; solo análisis exploratorio |
| Tablero de tareas, bandeja RFI/NC, buscador Ctrl+K, reporte semanal, PWA | **Se congelan (solo mantenimiento)** | Útiles como canal de captura de datos, pero no son contribución; no escribir de ellos en el paper |
| Multiempresa, PostgreSQL, Keycloak, notificaciones, valorización de contratistas, costo real vs. cotizado | **Fuera de alcance (trabajo futuro)** | Producto, no investigación |
| Vista «Planta 3D» basada en el replay del CRP | **Eliminada** | Reemplazada por el Gemelo 3D |

## 4. Diseño de la planta y la simulación: qué se agregó y qué falta

**Hecho** (ver [diseno/08](../diseno/08_gemelo_planta.md)): flujo por lote con 4 máquinas detalladas (sierra cinta con volantes y banda, cizalla-punzonadora con ariete, mesa de plasma con pórtico y chispas, roscadora con mandril), 2 puentes grúa que trasladan cada lote, 6 mesas de armado con cuadrillas de 2, 8 puestos de soldeo con arco, 2 zonas de limpieza e inspección con retrabajo, cuadrillas de 5 contratistas con ausentismo, ingeniería con RFIs y cambios de alcance, compras con proveedores, doblez y pintura externos con camiones, fallas y mantenimiento, calendario con feriados, turnos, horas extra y segundo turno; en 3D, ciclo de día y noche, vuelo de cámara a cada objeto y el contenido de cada lote (marcas, perfiles, kg, agujeros, tiempos por etapa).

**Falta**, por orden de valor para la tesis:

1. **Plano medido** de la planta y de los equipos reales (hoy es una plantilla de 100 × 50 m); fotos de las máquinas para ajustar su aspecto.
2. **Restricciones de espacio y de grúa reales** si resultan ser cuello de botella (preguntar en planta).
3. Montacargas y transporte interno, calidad (inspección con equipos), herramientas y plantillas, merma.
4. Especialidades y curva de aprendizaje por contratista.
5. Piezas individuales (no solo lotes) en el 3D, y vista de colas con tiempos de espera.

## 5. Datos a pedir a la empresa (por prioridad)

| Prioridad | Dato | Para qué |
|---|---|---|
| P0 | Tareo diario por proceso de los últimos 12–25 proyectos (HH reales) | Entrenar C2 y validar el gemelo |
| P0 | Fecha de pedido y recepción de cada compra de material, por proyecto | Aprender la espera de proveedores (el mayor componente del plazo) |
| P0 | Fechas de envío y regreso de doblez y pintura | Servicios externos |
| P0 | Lo que estimó el cotizador por proceso y su fecha, guardado antes de ejecutar | Línea base justa y anclaje |
| P1 | Paradas de máquina (causa, duración) de 6 meses | Disponibilidad real |
| P1 | RFIs y cambios de alcance con fechas | Esperas de ingeniería |
| P1 | Costo de acelerar: prima de contratistas, hora extra, segundo turno, expeditar | Costos de palancas reales |
| P2 | Cotizaciones ganadas y perdidas con plazo y precio | Costo comercial del plazo (α\*) |
| P2 | Plano con medidas, puentes grúa, mesas y puestos | Gemelo 3D fiel |

## 6. Diseño de validación para Q1

1. **Retrospectivo sobre datos reales** con corte temporal (rolling origin): cada proyecto se cotiza con lo que se sabía a su inicio. Comparadores: A0 criterio del cotizador, colchón fijo afinado, regresión lineal, RF puntual, GBM cuantílico (tipo Bekci), QRF directo sobre el plazo, y el DSS completo. Métricas: MAE, pinball, PICP, error de fecha, % tardíos, tardanza, penalidad esperada, costo.
2. **Gemelo validado** contra datos reales por proceso (no solo contra la fecha final).
3. **Ablaciones**: sin anclaje, sin esperas aprendidas, sin carga del taller, sin conformal, sin correlación entre procesos.
4. **Piloto en paralelo** (*shadow mode*) con ≥ 6 cotizaciones nuevas, protocolo pre-registrado, fechas del DSS guardadas antes de ejecutar.
5. **Alerta temprana**: AUC y Brier del re-pronóstico semanal en el piloto.
6. **Experimento con usuarios** (cotizador y jefe de taller): tareas de decisión con tablas contra gemelo 3D; SUS, tiempo y calidad de decisión.
7. **Potencia**: con 38 proyectos retrospectivos más el piloto se llega a ≈ 45; para un efecto de +10 puntos de cumplimiento hace falta pooling con datos de otras pymes o declarar el resultado como exploratorio.
8. **Reproducibilidad**: código abierto, datos anonimizados (C01…C38), semillas fijas, un script por tabla y figura.

## 7. Referencias de código y de diseño (consultadas)

- [realvirtual WEB](https://github.com/game4automation/realvirtual-WEB): visor 3D de gemelos digitales con three.js y modelos GLB (licencia AGPL-3.0: solo referencia de diseño, no se copia código).
- [simpanda](https://github.com/ghackenberg/simpanda): plantilla de simulación de eventos discretos (SimPy) con 3D (Panda3D); marco académico de gemelo SimPy con visualización 3D de una línea SMT.
- [Voortman: optimal beam processing layout](https://www.voortman.net/en/knowledge-base/optimal-beam-processing-layout) y [AISC Modern Steel](https://www.aisc.org/globalassets/modern-steel/archives/2009/08/2009v08_tale_of_two.pdf): flujo real de un taller de estructuras (sierra, taladro/punzonado, armado, soldeo, granallado y pintura, inspección tras cada paso, puentes grúa por nave).
- Modelos 3D libres (CC0), **no descargados**: Kenney y Quaternius; el gemelo usa geometría procedural propia para no depender de activos externos.
- Cotización de fechas y simulación: Keskinocak & Tayur; Mundt & Lödding (2025); Bekci et al. (2022); Mehdiyev et al. (2025); Flores-Gómez & Dauzère-Pérès (2026).

## 8. Hoja de ruta con puertas de decisión

| Fase | Contenido | Criterio para pasar |
|---|---|---|
| 1 | Conseguir los datos P0 de la empresa; importarlos con el formato único | ≥ 12 proyectos con tareo, compras y servicios externos |
| 2 | Validar el gemelo contra los datos reales; recalibrar o corregirlo | El gemelo reproduce las duraciones por proceso con error medio ≤ 15 % |
| 3 | C4: medir el efecto real de las palancas y apagar las que no funcionan; reentrenar | Informe de eficacia por palanca |
| 4 | Retrospectivo con datos reales + ablaciones | Tablas y figuras generadas por script |
| 5 | Piloto en paralelo y experimento con usuarios | ≥ 6 proyectos y ≥ 8 participantes |
| 6 | Redacción (tesis TF2 y paper) | Decidir la revista con los resultados |

**Si con datos reales el DSS tampoco supera a un colchón fijo**, el paper sigue siendo viable como estudio de calibración, riesgo de modelo y alerta temprana (revistas Q2 con probabilidad alta); lo que no se puede es prometer una mejora de cumplimiento.
