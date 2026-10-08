# Guía · Entorno de trabajo

## Requisitos

- **Python 3.12** (probado con 3.12.10 en Windows y 3.12.14 en Linux). SQLite viene incluido en Python.
- **Git** y acceso de colaborador al repositorio.
- Nada más: no hay servicios externos ni Docker.

En los comandos de esta documentación se usa `python`. En Windows, si `python` abre la Microsoft Store, usar `py` o desactivar el alias en *Configuración → Aplicaciones → Alias de ejecución de aplicaciones*. En Linux, usar `python3` o el del entorno virtual.

## Instalar

```bash
git clone https://github.com/nikolmedina27/Tesina.git
cd Tesina
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

`python-docx` no se usa: `scripts/docx_a_md.py` y `scripts/build_db.py` leen el Word con la librería estándar (`zipfile` + `xml.etree`).

## Qué datos hay al clonar y qué no

El repositorio solo trae código, Markdown y los resultados de los experimentos (`data/*.csv`). **No** trae:

| Falta | Por qué | Cómo se obtiene |
|---|---|---|
| `extras/` (Word de la tesis, 3 Excel, PDF de cotización) | Confidencial (declaración jurada con Steelser) | Pedirlos a las autoras; se colocan en `extras/` y git los ignora |
| `data/steelser.db` | Se regenera | `python scripts/build_db.py` (necesita `extras/`). Si no tienes `extras/`, ver `scripts/reconstruir_muestra.py` y [diseno/06](../diseno/06_datos_simulados.md) |
| `papers/` (27 PDFs) | Tamaño y derechos de autor | Carpeta local; el mapeo está en `docs/analisis/papers_mapeo.csv` |
| `entregables/*.xlsx` | Se generan | `python scripts/generar_formato_unico.py` y `python scripts/generar_ejemplo_importacion.py` |
| `data/plataforma.db`, `data/credenciales_demo.txt`, `data/secret.key` | Datos locales de la plataforma | Se crean solos al iniciar la plataforma |

Los Word, Excel y PDF de trabajo no van en el repo: viven fuera de él (`~/Documents/shirley docs/` en la PC de Paolo). `.gitignore` los bloquea.

## Comandos

Reconstruir todo desde cero (requiere `extras/`):

```bash
python scripts/build_db.py             # 1. BD desde extras/ (borra las tablas sim_*)
python -m dss.simulador                # 2. datos simulados (~30 s)
python -m dss.simulador_planta         # 3. layout de la planta
python scripts/exp6_gemelo.py          # 4. gemelo de eventos discretos y 8 políticas (~6 min); crea las tablas gem_* de la vista 3D
python -m pytest tests -q              # 5. pruebas (49; algunas se omiten sin la BD)
```

Interfaces:

```bash
python -m uvicorn plataforma.server:app --port 8600   # plataforma SteelPlan -> http://localhost:8600
python -m streamlit run app/streamlit_app.py          # cotizador Streamlit (prototipo)
```

Experimentos (cada uno tarda varios minutos; resultados en `data/*.csv`):

```bash
python scripts/exp1_prediccion.py      # predicción de HH, leave-one-project-out (~10 min)
python scripts/exp2_backtest.py        # backtest de fechas, variantes A0/A5/A6/A7 (~10 min)
python scripts/exp3_frontera.py        # frontera cumplimiento-plazo con cuadrilla típica (~10 min)
python scripts/exp3_frontera.py plan   # igual, con las cuadrillas del cotizador
python scripts/exp4_ablacion.py        # ablaciones, colchón fijo y 5 escenarios (~30 min)
python scripts/calibrar_solapes.py     # recalibrar los solapes del motor CRP (~5 min)
python scripts/exp6_gemelo.py          # gemelo de eventos discretos (estudio principal)
python scripts/exp5_retrospectivo.py   # retrospectivo anterior con el CRP como verdad, 6 políticas (~8 min con 5 núcleos)
python scripts/exp5_retrospectivo.py --costo 2   # sensibilidad al costo de las palancas
```

Regenerar la tesis en Markdown desde el Word (`docs/tesis/`):

```bash
python scripts/docx_a_md.py
```

Abrir la BD con interfaz gráfica: [DB Browser for SQLite](https://sqlitebrowser.org/) y abrir `data/steelser.db`.

## Si se actualiza el Word de la tesis

1. Reemplazar `extras/Tesis_TF1_Steelser.docx` (mismo nombre).
2. `python scripts/docx_a_md.py` regenera `docs/tesis/`.
3. `python scripts/build_db.py` y `python -m dss.simulador` vuelven a leer la Tabla 3.

Las correcciones de la tesis se hacen en el Word, no en `docs/tesis/`.

## Trabajo en equipo con Git

- El repo es `https://github.com/nikolmedina27/Tesina` (público). Los colaboradores con permiso de escritura suben directo a `main`, que no tiene protección.
- Antes de empezar y antes de subir: `git pull --rebase`.
- Un commit por bloque de trabajo, con mensaje en español.
- **Nunca subir `extras/`, bases de datos, Word, Excel ni PDF** (están en `.gitignore`). Los datos de Steelser son confidenciales.
- Si un cambio es grande o riesgoso, trabajar en una rama y abrir un pull request.

## Convenciones

- Idioma de trabajo: español (documentación, comentarios, nombres de tablas y columnas).
- Los originales de la empresa viven en `extras/` y no se editan; todo lo derivado se regenera con scripts.
- Documentación en Markdown dentro de `docs/`; diagramas en Mermaid (se ven en GitHub y en VS Code con *Markdown Preview Mermaid Support*).
- El esquema de la BD se cambia en `sql/schema.sql`, nunca directamente en el `.db`. Las tablas `sim_*` las define `dss/simulador.py`.
- Toda simulación fija y guarda la semilla.
