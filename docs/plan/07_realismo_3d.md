# 07 · Plan de realismo del Gemelo 3D

> Estado: **propuesto** (aún sin ejecutar). Complementa [05](05_planta_3d.md) y [06](06_alcance_q1.md); el diseño actual de la escena está en [diseno/08](../diseno/08_gemelo_planta.md). Todo lo que muestra el gemelo es **simulado**.

## Por qué tiene sentido

El realismo no es una contribución científica, pero sí sirve para el experimento con usuarios de [06](06_alcance_q1.md) §6 (tablas contra gemelo 3D con jefes de taller y cotizadores): una escena que parece un juguete resta credibilidad. Por eso el esfuerzo se concentra donde el usuario mira (personas, máquinas, piezas) y el entorno se rellena con decorado barato.

## Fase 1 · Quitar el *popping* (sin assets nuevos)

- Lotes y camiones se desvanecen al entrar y salir y se deslizan a su nueva posición en vez de saltar.
- Las personas conservan su identidad entre horas y se animan al cambiar de estación.
- Transiciones suaves de día a noche y del techo que se abre al acercar la cámara.
- Caminata en primera persona: colisión simple con máquinas y muros, altura de ojos real y pasos suaves.

## Fase 2 · Personas, camiones y vehículos con modelos reales

- Reemplazar las figuras armadas con cajas por modelos **glTF (GLB)** con esqueleto y animaciones (caminar, soldar, martillar, esmerilar, operar), además de camiones y montacargas.
- Cargador GLB con instancias y `AnimationMixer`; si la carga falla, se usa el modelo procedural actual.
- **Licencias**: solo CC0 o CC-BY con atribución registrada en `plataforma/web/vendor/LICENCIAS.md`, porque el repositorio es público. Fuentes candidatas: Quaternius, Kenney, KayKit, Poly Haven (verificar la licencia de cada archivo al descargar). Evitar Mixamo (no permite redistribuir el archivo) y Sketchfab (licencias mezcladas).
- Las animaciones de soldadura pueden no existir en los paquetes gratuitos: se combinan o se aproximan.
- Peso estimado: 5–15 MB, servidos localmente y guardados en la caché del service worker.

## Fase 3 · Máquinas y planta con más fidelidad

- Pedir a la empresa **fotos de las 4 máquinas** (sierra Kaltenbach, Pedimax, mesa CNC, RIDGID) para ajustar colores, proporciones y rótulos; hoy son esquemas genéricos.
- Texturas PBR (concreto, acero, chapa) y un HDRI para reflejos, de Poly Haven (CC0).
- Sombras suaves, oclusión ambiental, detalles de las grúas (cadena, botonera), señalización de seguridad y marcas en el piso.
- Si la empresa entrega un **plano medido**, reemplaza la plantilla de 100 × 50 m.

## Fase 4 · Entorno

Una planta en un parque industrial de Lima no está aislada. Decorado barato, no seleccionable:

- Más árboles y arbustos, bardas, veredas, postes.
- Algunas naves vecinas y unas pocas casas o edificios a lo lejos, de baja complejidad.
- Camiones estacionados en la calle.
- Instancias y niebla ligera para no afectar el rendimiento.

## Orden

1. Fase 1 y caminata.
2. Fase 2 con una selección corta de modelos.
3. Fase 4.
4. Fase 3 cuando lleguen las fotos o el plano.

## Pendiente de decisión

- Autorizar la descarga de modelos CC0; antes de bajarlos se lista cada archivo con fuente, licencia y tamaño.
- Pedir a la empresa las fotos de las máquinas.
