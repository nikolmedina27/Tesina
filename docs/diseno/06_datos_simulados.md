# 06 · Datos simulados (banco de pruebas)

> **Todo lo de este documento es SIMULADO.** Sirve para construir y probar el pipeline (C1→C4) antes de tener los tareos reales. No es evidencia empírica sobre Steelser y así debe declararse en la tesis y en cualquier paper. En la BD, las tablas `sim_*` están separadas de las reales y cada fila lleva `origen = 'SIMULADO'`.

## Qué es real y qué es simulado

| Real (se respeta) | Simulado |
|---|---|
| 25 proyectos 2021–2026: toneladas, tipo, fecha de inicio, fin planificado y **fin real** | HH reales por proceso (la variable objetivo de C2) |
| Cuadrilla y días planificados por proceso | Paradas de las 4 máquinas (disponibilidad Dₖ diaria) |
| Ratio vigente (HH estimadas) | Plazos de los 2 servicios externos |
| Los 6 atrasos reales de la muestra | Variables del plano: n° de piezas, % planchas, m² de pintura, montaje, contratista |

## Cómo se generan (`dss/simulador.py`)

1. **Motor CRP** (`dss/crp_engine.py`, el mismo que usará el cotizador): programa día a día (lunes a sábado) los 13 procesos con precedencias y solapes. Un proceso avanza hasta la capacidad de su centro (cuadrilla × 8 h × Dₖ) y no puede ir más allá del avance de sus predecesores. Los servicios externos avanzan por plazo de calendario.
2. **Solapes calibrados** contra el plazo planificado real: con las HH del ratio y sin paradas, el motor reproduce los 25 plazos con **error medio de 2.0 días laborables y sesgo de −0.1** (`scripts/calibrar_solapes.py`).
3. **Paradas**: por máquina, eventos con tiempo entre fallas exponencial (MTBF 12 / 9 / 15 / 25 días laborables: sierra, cizalla-punzonadora, mesa CNC, roscadora) y duración lognormal (mediana 0.6 días), más mantenimiento planificado de media jornada cada 30 días. Parámetros **supuestos**, a reemplazar por la bitácora real.
4. **φ verdadero** (HH_real / HH_ratio) con
   log φ_ij = sesgo(tipo) + sesgo(proceso) + efectos de variables del plano − γ·log(t/80) + σ·(√ρ·η_proyecto + √(1−ρ)·ε_ij).
   η es el choque común del proyecto; γ hace que los proyectos chicos cuesten más HH/t, coherente con las 4 OT reales (29–121 HH/t).
5. **Carga del taller** (`dss/datos.py::CargaTaller`): las 4 máquinas son únicas y las comparten los proyectos simultáneos. Cada proyecto previo (de los 38 de la Tabla 3) ocupa las máquinas entre el 20 % y el 50 % de su duración con sus HH de habilitado (ratio de su tipo; 13 proyectos fuera de la muestra no tienen toneladas y se imputan con 93 t). El proyecto nuevo recibe disponibilidad efectiva D · (1 − κ·u) con κ = 0.5 y u ≤ 0.9. Solo cargan los proyectos iniciados **antes**, así la regla es causal. κ, la ventana y la imputación son **supuestos**.
6. **Condicionamiento a lo real (ABC)**: para cada proyecto se sortean 3 000 "verdades" (φ y plazos externos), se programan con las paradas simuladas de su fecha y la carga del taller, y se elige la que reproduce la **duración real del proyecto**. Aceptación con tolerancia ±1 día: 14–25 %.

## Los 4 mundos

| Mundo | Idea | σ por proceso | ρ | Qué prueba |
|---|---|---|---|---|
| M1 ratio casi correcto | φ ≈ 1 ± 6 % | 0.06 | 0.3 | El modelo no empeora lo que ya funciona |
| M2 sesgo sistemático | Sesgo por tipo y proceso (a priori) | 0.15 | 0.5 | Caso típico del problema |
| M3 no lineal y colas pesadas | Umbrales e interacciones, errores t(4) | 0.12 | 0.5 | Ventaja de QRF sobre regresión lineal |
| M4 deriva del taller | Como M2; desde 2024 contratista más lento (+15 % en armado/soldeo/limpieza) y MTBF ×0.6 | 0.15 | 0.5 | El lazo cerrado C4 |

Resultado realizado (tras condicionar a los datos reales):

| Mundo | φ medio | Desvío de log φ por proceso | Desvío a nivel proyecto | HH/t medias (mín–máx) |
|---|---|---|---|---|
| M1 | 0.980 | 0.068 | 0.048 | 30.8 (25.3–39.6) |
| M2 | 0.994 | 0.141 | 0.096 | 31.3 (23.0–47.2) |
| M3 | 0.986 | 0.143 | 0.105 | 31.0 (22.5–43.9) |
| M4 | 1.001 | 0.161 | 0.112 | 31.5 (21.7–47.4) |

## Hallazgo: el problema es la dispersión, no el sesgo medio

Como 19 de los 25 proyectos terminaron a ±2 días de lo planificado, el φ total de cada proyecto queda forzado cerca de 1 en todos los mundos (φ medio 0.98–1.00). El sesgo a priori de M2 sobrevive atenuado por tipo (planta +3 %, mezzanine +2 %, edificación +1 %, nave −7 %) y casi desaparece por proceso.

Lectura: el ratio vigente es correcto **en promedio**, pero cada proyecto se desvía de ±5 % a ±11 % en HH totales y de ±14 % a ±16 % por proceso (±7 % en M1). Un plazo único calculado con el promedio falla cuando la desviación cae del lado malo, y eso explica el 24–32 % de incumplimiento. Es el argumento a favor de cotizar con un cuantil y no con un valor central.

## Limitaciones (declararlas)

- **La carga del taller es un modelo simplificado** (ventana 20–50 % de la duración, κ = 0.5, ocupación proporcional a las HH del ratio, toneladas imputadas en 13 proyectos). Si en la realidad las colas son menores o mayores, parte del atraso real se estaría atribuyendo mal entre φ y la carga. Falta la sensibilidad a κ y a la ventana. Los contratistas no se modelan como recurso compartido: se asume que cada proyecto tiene su propia cuadrilla.
- Los días por proceso del Excel de 25 proyectos son un reparto construido (ver `analisis/02`); la duración **total** sí es real (Tabla 3).
- Los parámetros de paradas, plazos externos y efectos de las variables del plano son supuestos del simulador, no mediciones.
- Los mundos se parecen entre sí en el promedio por construcción; sus diferencias están en dispersión, estructura y deriva.

## Verificación por proyecto (días laborables, lunes a sábado)

El motor, con las HH simuladas, las paradas y la carga del taller de cada mundo, reproduce la duración real de los 25 proyectos con residuo 0 en M2, M3 y M4. En M1 (donde φ casi no varía y por tanto no puede absorber el atraso) el residuo medio es 0.12 días y un proyecto queda a 3 días.

| # | Año | Cliente | t | Retraso real (d) | Días lab. plan | Días lab. real | Simulado (M1-M4) | φ M1 | φ M2 | φ M3 | φ M4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2021 | Agricola Cerro Prieto | 171 | -1 | 71 | 70 | 73/70/70/70 | 0.911 | 0.821 | 0.801 | 0.773 |
| 2 | 2021 | Corporación Saeta Sa | 101 | +0 | 69 | 69 | 69/69/69/69 | 0.954 | 0.996 | 1.013 | 0.987 |
| 3 | 2021 | Saeta Sa | 81 | -1 | 64 | 63 | 63/63/63/63 | 1.077 | 0.931 | 0.967 | 1.015 |
| 4 | 2022 | Agricola Cerro Prieto | 89 | +0 | 55 | 55 | 55/55/55/55 | 0.993 | 1.058 | 0.944 | 0.988 |
| 5 | 2022 | Agricola Cerro Prieto | 121 | +0 | 62 | 62 | 62/62/62/62 | 0.992 | 0.938 | 0.973 | 0.937 |
| 6 | 2022 | Agv-Agrovision Sac | 81 | +5 | 52 | 56 | 56/56/56/56 | 0.980 | 0.970 | 1.174 | 1.133 |
| 7 | 2022 | Especial De Inversión Pú | 71 | +0 | 53 | 53 | 53/53/53/53 | 1.010 | 0.967 | 0.907 | 0.959 |
| 8 | 2023 | Agrícola Alaya S.A.C | 114 | -2 | 60 | 59 | 59/59/59/59 | 0.949 | 0.960 | 0.920 | 0.880 |
| 9 | 2023 | Agrícola Alaya S.A.C | 81 | -2 | 53 | 51 | 51/51/51/51 | 0.910 | 0.922 | 0.896 | 0.973 |
| 10 | 2023 | Famesa Explosivos S.A.C | 52 | +0 | 44 | 44 | 44/44/44/44 | 1.047 | 1.064 | 1.090 | 1.166 |
| 11 | 2023 | Pontificia Universidad C | 39 | +0 | 40 | 40 | 40/40/40/40 | 1.034 | 1.091 | 1.190 | 1.063 |
| 12 | 2023 | Rumi | 77 | +4 | 56 | 60 | 60/60/60/60 | 1.067 | 0.951 | 1.032 | 1.095 |
| 13 | 2023 | Famesa Explosivos S.A.C | 103 | -2 | 56 | 55 | 55/55/55/55 | 0.989 | 1.019 | 0.956 | 0.932 |
| 14 | 2023 | Jcb Estructuras | 71 | +0 | 53 | 53 | 53/53/53/53 | 0.949 | 0.991 | 1.027 | 0.892 |
| 15 | 2023 | Compañía Minera Ares S.A | 81 | -2 | 65 | 63 | 63/63/63/63 | 1.043 | 1.010 | 1.004 | 1.068 |
| 16 | 2024 | Agrícola 3P | 72 | -2 | 48 | 47 | 47/47/47/47 | 0.968 | 0.883 | 0.870 | 1.024 |
| 17 | 2024 | Ajeper Del Oriente S.A. | 47 | +0 | 50 | 50 | 50/50/50/50 | 0.951 | 1.282 | 1.194 | 1.288 |
| 18 | 2024 | Agrícola 3P | 178 | -2 | 74 | 73 | 73/73/73/73 | 0.903 | 0.871 | 0.885 | 0.913 |
| 19 | 2024 | Pontificia Universidad C | 72 | +8 | 49 | 56 | 56/56/56/56 | 0.957 | 1.059 | 0.827 | 1.147 |
| 20 | 2025 | Aquana | 103 | +0 | 57 | 57 | 57/57/57/57 | 0.971 | 1.016 | 0.956 | 0.972 |
| 21 | 2025 | Mas Errázuriz | 107 | +4 | 71 | 74 | 74/74/74/74 | 1.010 | 1.046 | 1.069 | 0.984 |
| 22 | 2025 | Famesa | 81 | +4 | 54 | 57 | 57/57/57/57 | 0.977 | 1.088 | 1.098 | 0.869 |
| 23 | 2026 | Inarco | 60 | +0 | 45 | 45 | 45/45/45/45 | 0.926 | 1.119 | 0.978 | 1.063 |
| 24 | 2026 | Qberries | 200 | +5 | 76 | 80 | 80/80/80/80 | 0.948 | 0.863 | 0.924 | 0.871 |
| 25 | 2026 | Danper | 75 | -1 | 47 | 46 | 46/46/46/46 | 0.996 | 0.945 | 0.958 | 1.027 |

## Regenerar

```bash
py scripts/build_db.py        # recrea la BD (borra las tablas sim_*)
py -m dss.simulador           # genera los 4 mundos y las guarda en sim_*
py -m pytest tests -q         # pruebas del motor
```

Tablas: `sim_mundo`, `sim_feature`, `sim_proyecto_proceso` (HH reales simuladas, φ, fechas por proceso), `sim_parada`, `sim_verificacion`. Semillas fijas en `dss/simulador.py`.
