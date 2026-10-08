# 07 · Plan de realismo del Gemelo 3D

> Estado: **propuesto** (aún sin ejecutar). Complementa [05](05_planta_3d.md) y [06](06_alcance_q1.md); el diseño actual de la escena está en [diseno/08](../diseno/08_gemelo_planta.md). Todo lo que muestra el gemelo es **simulado**. Versión 2: agrega el explicador de máquinas y las fuentes de personas, tras revisar qué existe con licencia libre.

## Por qué tiene sentido

El realismo no es una contribución científica, pero sí sirve para el experimento con usuarios de [06](06_alcance_q1.md) §6 (tablas contra gemelo 3D con jefes de taller y cotizadores): una escena que parece un juguete resta credibilidad. El esfuerzo se concentra donde el usuario mira (máquinas, personas, piezas) y el entorno se rellena con decorado barato.

## Qué se encontró sobre los assets (y qué cambia)

| Tema | Hallazgo | Consecuencia |
|---|---|---|
| Personas | **Microsoft Rocketbox** ([GitHub](https://github.com/microsoft/Microsoft-Rocketbox)): 115 avatares realistas, con esqueleto, formato FBX, licencia **MIT** desde dic. 2020 | Mejor candidato para personas realistas; hay que convertir FBX → GLB y asignarles animaciones |
| Personas | **MakeHuman**: lo que se exporta queda en **CC0**; permite elegir cuerpo, ropa y casco | Alternativa para generar operarios con ropa de trabajo |
| Personas | **Quaternius, Kenney, KayKit**: CC0, glTF, animados, pero **estilizados** (low-poly) | Sirven de respaldo y para animaciones; no son «realistas» |
| Personas | **Mixamo** (animaciones y personajes muy usados): el archivo **no se puede redistribuir** | No se sube al repositorio público; solo local (como `extras/`) si se decide usarlo |
| Máquinas | Búsquedas de sierra de cinta, cizalla-punzonadora y mesa de plasma **no dieron modelos CC0** de calidad (los de Sketchfab son por modelo y de licencia variable; GrabCAD no es redistribuible) | Las cuatro máquinas hay que **construirlas nosotros**, a partir de fotos y manuales de Steelser |

Las licencias hay que **verificar archivo por archivo** al descargar y registrarlas en `plataforma/web/vendor/LICENCIAS.md`.

## El explicador de máquinas (la ventana emergente que describes)

Al hacer clic en una máquina se abre una **ficha 3D** aparte de la escena: un visor propio con la máquina aislada sobre fondo neutro, que gira sola y se puede orbitar. Es lo que se ve en los videos de despiece, pero con datos del gemelo.

| Pestaña | Contenido |
|---|---|
| **Componentes** | Lista de partes; al pasar el cursor, la parte se resalta y una línea la une a su nombre y función |
| **Funcionamiento** | Ciclo animado paso a paso (p. ej. sierra: cargar viga → sujetar con mordaza → bajar cabezal → cortar → liberar → avanzar al tope), con reproducir, pausa y barra de tiempo; la parte que actúa se resalta |
| **Despiece** | Deslizador de vista explosionada y rayos X (ya existe una versión en la escena) |
| **Sección** | Plano de corte para ver el interior |
| **Datos** | Capacidad, potencia y velocidad típicas, más lo que mide el gemelo: utilización, disponibilidad, paradas y horas por tipo de operación |
| **Seguridad** | Zonas de peligro y protecciones |

**Cómo se procesa**: el modelo es un GLB cuyos **nodos llevan el nombre de la pieza** (`cabezal`, `volante_motriz`, `mordaza`…); un archivo de datos por máquina (`maquinas/sierra.json`) asigna a cada nodo su nombre, función, dirección de despiece y los **fotogramas de cada paso del ciclo**. La ventana lee el GLB, agrupa los nodos y construye lista, despiece y animación sin tener que programar cada máquina.

**Aspecto**: «realista, pero como CAD limpio». Dos modos: **realista** (materiales PBR, aristas biseladas, calcomanías, sombras de contacto, oclusión ambiental, reflejos) y **técnico** (los mismos modelos con contorno de aristas y sombreado plano, como un visor CAD).

**Fuente de los modelos**: Blender (script o modelado) a partir de fotos y manuales de las cuatro máquinas reales (sierra Kaltenbach, Pedimax, mesa CNC, RIDGID). Hasta que lleguen, se refinan los esquemas genéricos actuales.

## Fases

### Fase 1 · Quitar el *popping* y la caminata (sin assets nuevos)
- Lotes y camiones se desvanecen y se deslizan en vez de aparecer o saltar; las personas conservan identidad entre horas.
- Transiciones suaves de día a noche y del techo.
- Caminata: colisión simple con máquinas y muros, altura de ojos real y pasos suaves.

### Fase 2 · Explicador de máquinas (esquemas genéricos refinados)
- Ventana con visor propio, pestañas Componentes, Funcionamiento y Despiece, y modos realista/técnico.
- Archivo de datos por máquina y ciclo animado de cada una.
- Materiales PBR, biseles y calcomanías en las cuatro máquinas actuales.

### Fase 3 · Personas con modelos reales
- Cargador GLB con instancias y `AnimationMixer`; respaldo al modelo actual si falla.
- Convertir una selección corta de avatares Rocketbox (operarios, soldadores, supervisores) a GLB; ropa de trabajo y casco; animaciones de caminar, operar, soldar, martillar y esmerilar (retargeting; si no hay clip de soldadura gratuito, se aproxima con poses).
- Camiones y montacargas desde paquetes CC0 (Quaternius, Kenney).
- Peso estimado: 10–30 MB servidos localmente y guardados en la caché del service worker.

### Fase 4 · Entorno
Decorado barato y no seleccionable: más árboles y arbustos, bardas, veredas, postes, algunas naves vecinas y unas pocas casas o edificios a lo lejos, camiones estacionados; con instancias y niebla ligera. Una planta en un parque industrial de Lima no está aislada.

### Fase 5 · Fidelidad con datos de la empresa
- **Fotos y manuales de las 4 máquinas** para reemplazar los esquemas genéricos por modelos fieles.
- Plano medido de la planta (reemplaza la plantilla de 100 × 50 m).
- Texturas PBR y HDRI de Poly Haven (CC0).

## Orden recomendado
1. Fase 1.
2. Fase 2 (es lo que más se ve y no depende de descargas).
3. Fase 3.
4. Fase 4.
5. Fase 5 cuando lleguen las fotos y el plano.

## Pendiente de decisión
- Autorizar la descarga de Rocketbox y de los paquetes CC0; antes se lista cada archivo con fuente, licencia y tamaño.
- Pedir a la empresa fotos y manuales de las máquinas, y el plano.
- Confirmar si hay Blender disponible en el equipo para modelar y convertir.
