# Guía · Entorno de trabajo

## Estado actual de esta PC

- **Python 3.12.10** instalado (winget, `Python.Python.3.12`, usuario) en `%LOCALAPPDATA%\Programs\Python\Python312\`. Está en el PATH de las terminales **nuevas**; `py` también funciona.
- **Git 2.55** instalado (winget, `Git.Git`). El repositorio es local, rama `main`. No hay remoto configurado.
- Librerías: `pandas`, `openpyxl`, `pdfplumber`, `numpy`, `scipy`, `scikit-learn`, `quantile-forest`, `streamlit`, `plotly`, `pytest` (todas en `requirements.txt`).
- SQLite 3.49 viene incluido con Python (módulo `sqlite3`).

> `python-docx` quedó instalado pero **no funciona**: a su dependencia `lxml` le falta el binario `etree` (probablemente lo bloqueó el antivirus). No hace falta: `scripts/docx_a_md.py` y `scripts/build_db.py` leen el Word con la librería estándar.

Si `python` abre la Microsoft Store en vez de Python, usar `py` o desactivar el alias en *Configuración → Aplicaciones → Configuración avanzada de aplicaciones → Alias de ejecución de aplicaciones*.

## Instalar todo lo del proyecto

```bash
py -m pip install -r requirements.txt
```

## Comandos

Orden para reconstruir todo desde cero:

```bash
py scripts/build_db.py                 # 1. BD desde extras/ (borra las tablas sim_*)
py -m dss.simulador                    # 2. datos simulados (~30 s)
py -m pytest tests -q                  # 3. pruebas
```

Experimentos (cada uno tarda varios minutos; resultados en `data/*.csv`):

```bash
py scripts/exp1_prediccion.py          # predicción de HH, leave-one-project-out (~10 min)
py scripts/exp2_backtest.py            # backtest de fechas, variantes A0/A5/A6/A7 (~10 min)
py scripts/exp3_frontera.py            # frontera cumplimiento-plazo con cuadrilla típica (~10 min)
py scripts/exp3_frontera.py plan       # igual, con las cuadrillas del cotizador
py scripts/calibrar_solapes.py         # recalibrar los solapes del motor CRP (~5 min)
```

Cotizador web:

```bash
py -m streamlit run app/streamlit_app.py
```

Regenerar la tesis en Markdown desde el Word:

```bash
py scripts/docx_a_md.py
```

Abrir la BD con interfaz gráfica: [DB Browser for SQLite](https://sqlitebrowser.org/) y abrir `data/steelser.db`.

## Si se actualiza el Word de la tesis

1. Reemplazar `extras/Tesis_TF1_Steelser.docx` (mismo nombre).
2. `py scripts/docx_a_md.py` → regenera `docs/tesis/`.
3. `py scripts/build_db.py` y `py -m dss.simulador` → vuelven a leer la Tabla 3.

## Git

Un commit por bloque de trabajo. `data/*.db` está en `.gitignore` (se regenera). **`extras/` contiene datos confidenciales de la empresa: no subir el repositorio a GitHub ni a ningún remoto sin anonimizar o sin permiso de Steelser.**

## Convenciones

- Los originales viven en `extras/` y no se editan; todo lo derivado se regenera con scripts.
- Documentación en Markdown en `docs/`; diagramas en Mermaid (se ven en VS Code con la extensión *Markdown Preview Mermaid Support* y en GitHub).
- El esquema de la BD se cambia en `sql/schema.sql`, nunca directamente en el archivo `.db`. Las tablas `sim_*` las define `dss/simulador.py`.
