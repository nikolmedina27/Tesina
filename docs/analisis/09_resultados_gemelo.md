# 09 · Resultados: el DSS evaluado contra el gemelo de eventos discretos

> **Resultados contrafactuales simulados, anclados a historia real.** Los 38 proyectos y sus fechas históricas proceden de registros de Steelser. El gemelo hora a hora de [diseno/08](../diseno/08_gemelo_planta.md) genera eventos y datos de proceso calibrados a esas fechas; por ello, las comparaciones de políticas y las alertas son resultados del modelo, no observaciones de cómo habría operado la planta. Reemplaza al estudio retrospectivo de [08](08_retrospectivo_planta3d.md), cuya «verdad» salía del mismo motor que el DSS (circular).

> **Corrida vigente: 9/10/2026, Windows, pandas 3.0.6** (`py scripts/exp6_gemelo.py`, semilla 2026, 740 s). Reproduce exactamente
> los `data/exp6_*.csv` del repositorio. La corrida anterior (8/10/2026, Linux, pandas 2) daba resultados más favorables al
> DSS (al final, en *Corrida anterior*). Con el mismo código y las mismas semillas, **el cambio de entorno movió las
> conclusiones principales**: hasta fijar versiones (`requirements.txt` no las fija) y correr réplicas (`--replicas 4`),
> ninguna cifra de este documento debe citarse en la tesis ni en el paper como definitiva.

## Qué se hizo

1. Se generó la historia 2019–2026 de los 38 proyectos (9 162 lotes, 1 425 paradas de máquina) y se **calibró el gemelo**: con la política «como se hizo» da 72 % de cumplimiento en la muestra (la realidad es 76 %: un proyecto de diferencia). El planificador (CRP) se calibró con los 13 proyectos fuera de la muestra: sesgo +33.9 → +2.4 d, error absoluto 33.9 → 4.4 d.
2. Se corrió **toda la historia una vez por política, con el mismo azar** (mismos tiempos de soldeo, mismas fallas, mismos proveedores). El DSS solo ve lo que vería la empresa.
3. Se midió también la **alerta temprana**: un observador que re-pronostica cada 12 días sin tocar la planta.

Políticas (25 proyectos de la muestra): **A0** como se hizo · **B1** regla del jefe de taller (compara avance con un plan lineal y pone horas extra y gente) · **C1** colchón fijo (fecha del cotizador + 7 días laborables, el cuantil 80 % del atraso de los 13 proyectos fuera de la muestra) · **D0** monitoreo · **D1** DSS con fecha al 80 % · **D2** DSS con fecha α\* (≈ 0.93) · **D3** DSS gestionando con la fecha original · **D4** DSS completo (α\* + gestión).

## Resultados

| Política | OTD | Retraso (d) | Palancas (% presup.) | Penalidad + palancas | + costo comercial del plazo | Plazo cotizado (d cal.) |
|---|---|---|---|---|---|---|
| A0 Como se hizo | 72 % | 1.56 | 0 | **1.56** | **1.56** | 66.6 |
| B1 Regla del jefe de taller | 80 % | 1.04 | 3.79 | 4.83 | 4.83 | 66.6 |
| C1 Colchón fijo (+7 d lab.) | 100 % | 0 | 0 | 0 | **0.66** | 74.8 (+12 %) |
| D1 DSS fecha α = 0.80 | 60 % | 3.40 | 0 | 3.40 | 3.13 | 63.2 (−5.1 %) |
| D2 DSS fecha α\* | 68 % | 1.76 | 0 | 1.76 | 1.95 | 68.9 (+3.5 %) |
| D3 DSS gestión (fecha original) | 72 % | 1.52 | 0.26 | 1.78 | 1.78 | 66.6 |
| D4 DSS completo | 68 % | 1.76 | 0.19 | 1.95 | 2.13 | 68.9 (+3.5 %) |

Penalidad = 1 % del presupuesto por día. El costo comercial del plazo extra es un **supuesto** (0.08 % por día, de `alpha_optimo`). Archivos: `data/exp6_resumen.csv`, `exp6_gemelo.csv` (por proyecto), `exp6_decisiones.csv`, `exp6_alerta.csv`.

**Diferencia frente a A0** en penalidad + palancas + costo comercial (IC 95 % bootstrap sobre los 25 proyectos): B1 **+3.27** [+1.45, +5.47] (peor) · C1 −0.90 [−2.03, +0.03] · D1 **+1.57** [+0.58, +2.74] (peor) · D2 +0.39 [−0.51, +1.38] · D3 **+0.22** [+0.04, +0.44] (peor) · D4 +0.57 [−0.46, +1.81]. Ninguna mejora es distinguible de cero; el colchón fijo es el único con tendencia favorable.

### Alerta temprana (D0)

| Tramo del plazo | Observaciones (atrasados) | AUC | Brier | Brier de la base | Error de fecha (d) |
|---|---|---|---|---|---|
| 0–25 % | 20 (7) | 0.63 | 0.234 | 0.232 | 7.5 |
| 25–50 % | 26 (8) | 0.69 | 0.213 | 0.214 | 9.1 |
| 50–75 % | 29 (9) | **0.78** | 0.246 | 0.215 | 9.5 |
| 75–100 % | 23 (8) | 0.73 | 0.259 | 0.231 | 5.9 |

AUC 0.5 = sin señal. El re-pronóstico **ordena** bien los proyectos que se atrasarán (AUC 0.63–0.78), pero sus **probabilidades no están calibradas**: el Brier es igual o peor que el de «la probabilidad histórica de atraso» en todos los tramos. La fecha pronosticada queda a ±6–10 días con un sesgo de +6 a +8 días (pesimista).

## Lectura

1. **En esta corrida la fecha del DSS no está calibrada: es optimista.** Con α = 0.80 cumple solo 60 % (20 puntos bajo lo nominal) y cotiza 5 % *menos* plazo que el cotizador; con α\* ≈ 0.93 cumple 68 % con +3.5 % de plazo. En la corrida anterior cumplía 80 % y 88 %. Un **colchón fijo** (+7 d lab.) cumple 100 % y es el mejor en costo ajustado, como en el experimento 4 de [04](04_resultados_banco_pruebas.md) y en Mundt & Lödding. La afirmación «α = 0.80 cumple 80 %» queda **pendiente de revalidar** (réplicas y versiones fijas); en el banco de pruebas de C2/C3 el rango fue 76–84 %.
2. **La gestión no se paga en este gemelo, y por una razón que se entiende.** La regla del jefe de taller ahora sube el cumplimiento de 72 % a 80 %, pero cuesta 3.8 % del presupuesto en palancas y queda peor en costo total. Los atrasos de los 6 proyectos tardíos vienen de la **pintura externa (13 a 26 días)** y de la espera de **material**, no de la capacidad de la planta. Para un proyecto normal el tiempo se reparte así: ingeniería 2.4 d, el material llega a los 19 d, el habilitado termina a los 26 d, limpieza a los 47 d, pintura +12 d y entrega +1 d. Las palancas internas (gente u horas extra en armado, soldeo y limpieza) actúan sobre unos 21 de los 60 días de un proyecto normal, es decir un tercio, y no tocan lo que atrasa. (En la corrida anterior la regla gastaba 9.6 % sin mejorar el cumplimiento.)
3. **Riesgo de modelo.** Las palancas internas que recomienda el DSS (+2 personas en limpieza, segundo turno en la sierra) mejoran la fecha en su planificador diario pero no en la planta: es lo que se espera cuando el modelo de planificación omite lo que de verdad domina el plazo. Por eso se le enseñó a aprender las esperas de compras e ingeniería desde los proyectos terminados y a calibrar sus solapes con el tareo (antes cotizaba +50 % de plazo y recomendaba palancas sobre el cuello equivocado). Aun así, la gestión no se justifica; **hace falta el lazo cerrado C4**: medir si cada palanca produjo el efecto que predijo y dejar de usar las que no.
4. **Cuando el DSS aprende del experto, mejora; cuando lo ignora, empeora.** Sin anclarlo al plazo del cotizador cotizaba +36 % de plazo para cumplir; anclado, +0.8 % para cumplir lo mismo que la realidad. Es un resultado sobre el diseño del DSS, consistente con Rokoss et al.: el experto es una base fuerte.
5. **La alerta temprana discrimina, pero sus probabilidades no sirven tal cual**: AUC hasta 0.78 a mitad del plazo, con Brier peor que la base. Sirve para ordenar qué proyectos vigilar, no como probabilidad para negociar; necesita recalibración (p. ej., isotónica sobre proyectos cerrados) y medirse desde el inicio del piloto.
6. **Robustez**: con N = 25, uno o dos proyectos mueven el cumplimiento 4–8 puntos, y un cambio de entorno (pandas 2 → 3) cambió la conclusión sobre la calibración. El estudio necesita réplicas del gemelo y versiones fijadas antes de reportarse.

## Qué cambia con datos reales

Todo lo anterior depende del gemelo. Con tareos reales: (a) el gemelo se **valida** en vez de calibrarse (¿reproduce las duraciones por proceso?), (b) el efecto de las palancas se mide en la planta, no se supone, (c) los plazos de proveedores y pintura se aprenden de las órdenes reales, (d) N crece más allá de 25. Es posible que la gestión sí funcione en Steelser; el experimento permite saberlo.

## Límites (declararlos)

- Simulado y de una sola historia (una realización del azar): los intervalos del bootstrap miden la variación entre proyectos, no entre realizaciones del gemelo.
- N = 25 proyectos (IC de proporciones ±16 puntos); A0 tiene solo 6 atrasos de 2 a 8 días.
- El factor de ritmo por proyecto es una caja negra que absorbe lo que el gemelo no modela; los plazos de proveedores y pintura son lognormales independientes.
- Costos de palancas y costo comercial del plazo son supuestos sin datos de la empresa.
- El error de planificación del CRP frente al gemelo, aun con las entradas observadas, es de ≈ 12 días laborables en promedio (24 %): es el tamaño del «riesgo de modelo».

## Corrida anterior (8/10/2026, Linux, pandas 2; reemplazada)

OTD por política: A0 76 % · B1 76 % · C1 100 % · D1 80 % · D2 88 % · D3 76 % · D4 88 %. Costo de palancas B1 9.64 %, D3 1.29 %. Alerta temprana AUC 0.55 / 0.68 / 0.68 / 0.83 por cuartil del plazo, Brier 0.140 en el último cuarto. El generador cambió una línea (el `tipo` de los 13 proyectos sin tipo llega como `NaN` en pandas 3 y se reemplaza por el tipo por defecto); con pandas 2 llegaba como `None` y ya recibía ese mismo tipo, así que la diferencia viene del entorno de librerías, no de esa línea.

## Reproducir

```bash
py scripts/reconstruir_muestra.py   # solo si falta extras/
py -m dss.simulador && py -m dss.simulador_planta
py scripts/exp6_gemelo.py           # ≈ 6 min con 6 núcleos (12 min en la PC de Shirley); escribe data/exp6_*.csv y las tablas gem_*
py scripts/exp6_gemelo.py --replicas 4   # réplicas del gemelo: necesarias antes de citar cifras
py -m pytest tests -q
```
