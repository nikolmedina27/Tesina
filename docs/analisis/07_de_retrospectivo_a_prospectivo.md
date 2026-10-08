# 07 · De un análisis retrospectivo a uno prospectivo (puntos de mejora)

Todo lo hecho hasta ahora mira **hacia atrás**: datos históricos (y simulados), backtest de proyectos ya terminados. Una revista Q1 en operaciones pide evidencia de que el artefacto funciona **hacia adelante**, en uso real. Este documento lista qué es retrospectivo, qué ya es prospectivo y qué falta.

## 1. Diagnóstico

| Pieza | Hoy | Límite |
|---|---|---|
| Línea base (68.4 % de cumplimiento) | Retrospectiva (Tabla 3) | Correcta, pero no dice qué pasaría con el sistema |
| Modelo de horas (C2) | Entrenado con datos simulados | Sin horas reales no hay evidencia |
| Fechas (C3) | Backtest *rolling origin* sobre los 25 | Contrafactual: nadie cotizó con esas fechas |
| Disponibilidad | Supuesta (paradas simuladas) | No hay bitácora real |
| Lazo cerrado (C4) | Diseñado, no operativo | No se ha visto deriva real |

## 2. Lo que ya es prospectivo (implementado en SteelPlan)

1. **Registro diario de tareo y paradas** con validaciones: produce las HH reales y la disponibilidad real **desde hoy**.
2. **Re-pronóstico de proyectos en curso**: Monte Carlo sobre el trabajo restante, desde la fecha actual, con semáforo frente a la fecha comprometida.
3. **MTBF desde las paradas registradas**: cuando hay 60 días de registro, la disponibilidad deja de ser un supuesto.
4. **Cotización que crea el proyecto**: la fecha, la probabilidad y el programa P50 quedan guardados **antes** de ejecutar (no se pueden ajustar después; es la base de una evaluación honesta).
5. **Tareas con tipo** (bloqueo, RFI, cambio de alcance): separan el atraso imputable al cliente del de la planta.

## 3. Puntos de mejora para nivel Q1

### 3.1 Diseño del estudio prospectivo
- **Pre-registrar** el protocolo antes del piloto: hipótesis, métricas, umbrales, tamaño esperado, análisis. Por ejemplo, en OSF o como anexo fechado de la tesis.
- **Shadow mode**: el cotizador oferta como siempre y SteelPlan cotiza en paralelo; ambos se guardan con fecha y hora. Al cierre se comparan contra la fecha real. Evita el sesgo de que el sistema cambie su propio resultado.
- **Serie de tiempo interrumpida**: cumplimiento mensual 2021–2026 contra el periodo con la plataforma. Es débil con pocos proyectos al año, pero complementa.
- **Unidad de análisis ampliada**: además del proyecto, evaluar **cada proceso** y **cada semana** (re-pronósticos), para tener cientos de observaciones en vez de 3–6 proyectos.

### 3.2 Métricas prospectivas nuevas

| Métrica | Qué mide | De dónde sale |
|---|---|---|
| **Precisión del re-pronóstico según el % de avance** | Si a 25 %, 50 % y 75 % de avance la P50 se acerca a la fecha real | Re-pronósticos semanales guardados |
| **Anticipación de la alerta** | Cuántos días antes de un atraso el semáforo pasó a ámbar o rojo | Historial de semáforos |
| **Tasa de falsas alarmas** | Proyectos con alerta roja que terminaron a tiempo | Mismo |
| **Calibración prospectiva** | Fracción de fechas cotizadas con α que se cumplen | Cotizaciones en paralelo |
| **Error del ratio vs. del modelo en HH** | Io por proceso con datos reales | Tareo |
| **Cobertura del registro** | % de días laborables con tareo; % de paradas con causa | Plataforma |
| **Usabilidad y aceptación** | SUS (≥ 68 aceptable) y TAM (utilidad y facilidad percibidas) | Encuesta al final del piloto |
| **Tiempo de respuesta comercial (QLT)** | Horas desde que llegan los planos hasta la cotización con fecha | Registro de cotizaciones |

### 3.3 Mejoras al modelo que solo se pueden hacer con datos prospectivos
1. **Actualización bayesiana durante la ejecución**: con el avance real de las primeras semanas, actualizar φ del proyecto (el choque común η) y recortar la incertidumbre del resto. Es el paso natural del re-pronóstico actual.
2. **Calibración por tamaño** (conformal Mondrian): el experimento 4 mostró que los proyectos chicos cumplen 67 % cuando se promete 80 %.
3. **Lazo cerrado real (C4)**: Md y PICP calculados al cerrar cada proyecto del piloto, con alerta de reentrenamiento en la plataforma.
4. **Estado de planta al cotizar**: guardar la carga real de las máquinas y los proyectos en curso en el momento de cada cotización (Rokoss et al. muestran que es la variable que más reduce el error).
5. **Aprendizaje del costo de plazo largo**: con cotizaciones ganadas y perdidas, estimar la probabilidad de ganar según el plazo y el precio, y pasar de un α\* supuesto a uno medido.

### 3.4 Evaluación del artefacto (Design Science Research)
Hevner et al. (2004) piden evaluar el artefacto por su **utilidad, calidad y eficacia**. Para eso conviene una matriz de evaluación con tres niveles:
- **Técnico**: pruebas, tiempo de respuesta, cobertura de pruebas.
- **Analítico**: calibración y error con datos reales.
- **De uso**: piloto, usabilidad y adopción.

Además conviene documentar las iteraciones del diseño (v1 → v2 → v3) como ciclos DSR.

## 4. Qué cambia en la tesis

1. **Objetivo específico nuevo o reformulado**: "validar prospectivamente el modelo mediante un piloto de N semanas con cotización en paralelo y re-pronóstico semanal".
2. **Capítulo de resultados en dos partes**: (a) retrospectivo, con backtest sobre datos reales reconstruidos; (b) prospectivo, con el piloto.
3. **Limitación explícita** si el piloto cierra pocos proyectos: reportar las métricas por proceso y por semana, que sí tienen tamaño suficiente.

## 5. Cronograma sugerido

| Semana | Actividad |
|---|---|
| 0 | Reunión con la empresa ([plan/04](../plan/04_kit_empresa.md)), cuentas, capacitación |
| 1–2 | Arranque del registro diario; carga de proyectos en curso |
| 1–12 | Registro diario, re-pronóstico semanal, cotizaciones en paralelo |
| 4–8 | Reconstrucción de tareos históricos y repetición de los experimentos 1–4 con datos reales |
| 12 | Encuesta SUS/TAM, cierre de proyectos, análisis prospectivo |
| 13–16 | Redacción del paper con ambas evidencias |
