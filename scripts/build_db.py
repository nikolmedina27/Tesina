"""Construye data/steelser.db (SQLite) a partir de los archivos en extras/.

Uso:  python scripts/build_db.py
Fuentes:
  - extras/Tesis_TF1_Steelser.docx            -> Tabla 3 (38 proyectos 2019-2026)
  - extras/Proyectos_muestra_25 Dep.xlsx      -> 25 proyectos x 13 procesos
  - extras/REPORTE DE AVANCE _PROYECTOS ...   -> HH reales por OT y avance por pieza
  - extras/Ejemplo data de un proyecto.xlsx   -> ACU de la cotización ST087
  - extras/Cotizacion_ST087_BYPS_...pdf       -> cabecera de la cotización ST087
La BD se recrea desde cero en cada ejecución.
"""
import re
import sqlite3
import warnings
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import openpyxl
import pandas as pd

warnings.filterwarnings('ignore')
RAIZ = Path(__file__).resolve().parent.parent
EXTRAS = RAIZ / 'extras'
DB = RAIZ / 'data' / 'steelser.db'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

PARAMETROS = [
    ('penalidad_diaria', 0.01, 'Penalidad por día de retraso como fracción del presupuesto (sin tope)'),
    ('alpha', 0.80, 'Cuantil de la distribución de fechas usado para cotizar'),
    ('replicas_mc', 1000, 'Réplicas de la simulación de Monte Carlo'),
    ('md_umbral', 0.30, 'Umbral del Índice de Deriva del Modelo (Md) para reentrenar'),
    ('picp_min', 0.70, 'Cobertura mínima aceptable del intervalo P10-P90'),
    ('min_proyectos_reentreno', 3, 'Proyectos cerrados mínimos desde el último entrenamiento'),
    ('d_meta', 0.90, 'Meta de disponibilidad por máquina (clase mundial)'),
    ('horas_turno', 8, 'Horas programadas por turno'),
    ('dias_laborables_semana', 6, 'Lunes a sábado (según propuestas técnicas)'),
    ('otd_meta', 0.85, 'Meta de cumplimiento de entregas'),
    ('lead_time_aumento_max', 0.05, 'Aumento máximo permitido del lead time cotizado'),
]

# recurso '—' de la muestra se asigna a un centro interno según el proceso
CENTRO_INTERNO = {'Ingeniería': 'Oficina técnica', 'Compra de material': 'Compras',
                  'Despacho a obra': 'Despacho'}
TIPO_CENTRO = {
    'Sierra Cinta Kaltenbach': 'MAQUINA', 'Cizalladora Punzonadora Pedimax': 'MAQUINA',
    'Mesa CNC': 'MAQUINA', 'Roscadora RIDGID': 'MAQUINA', 'Contratista': 'CONTRATISTA',
    'Servicio externo - Doblez': 'SERVICIO_EXTERNO', 'Servicio externo - Granallado/Pintura': 'SERVICIO_EXTERNO',
    'Planta': 'INTERNO', 'Oficina técnica': 'INTERNO', 'Compras': 'INTERNO', 'Despacho': 'INTERNO',
}


def fecha(v):
    if v is None or v is pd.NaT or (isinstance(v, float) and pd.isna(v)) or v == '':
        return None
    if isinstance(v, (datetime, pd.Timestamp)):
        return v.strftime('%Y-%m-%d')
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(v).strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return None


def norm(s):
    return re.sub(r'\s+', ' ', str(s)).strip().upper()


def tabla3_word():
    z = zipfile.ZipFile(EXTRAS / 'Tesis_TF1_Steelser.docx')
    body = ET.fromstring(z.read('word/document.xml')).find(W + 'body')
    txt = lambda e: ' '.join(''.join(t.text or '' for t in p.iter(W + 't')) for p in e.iter(W + 'p')).strip()
    for tbl in body.iter(W + 'tbl'):
        filas = [[txt(tc) for tc in tr.findall(W + 'tc')] for tr in tbl.iter(W + 'tr')]
        if filas and 'AÑO' in filas[0] and 'FINAL REAL' in filas[0]:
            return pd.DataFrame(filas[1:], columns=filas[0])
    raise RuntimeError('No se encontró la Tabla 3 en el Word')


def main():
    DB.parent.mkdir(exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((RAIZ / 'sql' / 'schema.sql').read_text(encoding='utf-8'))
    cur = con.cursor()
    cur.executemany('INSERT INTO parametro VALUES (?,?,?)', PARAMETROS)

    # --- catálogos ---------------------------------------------------------
    for nombre, tipo in TIPO_CENTRO.items():
        cur.execute('INSERT INTO centro_trabajo (nombre, tipo) VALUES (?,?)', (nombre, tipo))
    centro_id = dict(cur.execute('SELECT nombre, id FROM centro_trabajo'))

    m = pd.read_excel(EXTRAS / 'Proyectos_muestra_25 Dep.xlsx')
    m.columns = ['cod', 'anio', 'cliente', 'proyecto', 'tipo', 'ton', 'fuente_ton', 'ret_cal', 'ret_hab',
                 'nproc', 'proceso', 'recurso', 'personas', 'dias_plan', 'dias_ret', 'dias_real', 'hh_est']

    def centro_de(r):
        if r.recurso == '—':
            return CENTRO_INTERNO[r.proceso]
        if r.recurso == 'Servicio externo':
            return 'Servicio externo - Doblez' if 'Doblez' in r.proceso else 'Servicio externo - Granallado/Pintura'
        return r.recurso
    m['centro'] = m.apply(centro_de, axis=1)

    for r in m.drop_duplicates('nproc').sort_values('nproc').itertuples():
        cur.execute('INSERT INTO proceso (orden, nombre, centro_id) VALUES (?,?,?)',
                    (int(r.nproc), r.proceso, centro_id[r.centro]))
    proceso_id = {o: i for i, o in cur.execute('SELECT id, orden FROM proceso')}
    for t in sorted(m.tipo.unique()):
        cur.execute('INSERT INTO tipo_estructura (nombre) VALUES (?)', (t,))
    tipo_id = dict(cur.execute('SELECT nombre, id FROM tipo_estructura'))

    # --- proyectos: Tabla 3 del Word (38) + muestra (25) -------------------
    t3 = tabla3_word()
    t3.columns = ['n', 'anio', 'cliente', 'nombre', 'inicio', 'final', 'final_real', 'estado', 'retraso']
    for r in t3.itertuples():
        cur.execute('''INSERT INTO proyecto (n_registro, anio, cliente, nombre, fecha_inicio, fecha_fin_plan,
                       fecha_fin_real, dias_retraso) VALUES (?,?,?,?,?,?,?,?)''',
                    (int(r.n), int(r.anio), r.cliente, r.nombre, fecha(r.inicio), fecha(r.final),
                     fecha(r.final_real), float(r.retraso)))

    proyectos_m = m.drop_duplicates('cod')
    sin_match = []
    for r in proyectos_m.itertuples():
        cand = [(i, c) for i, c, n in cur.execute(
                    'SELECT id, cliente, nombre FROM proyecto WHERE anio=? AND codigo_muestra IS NULL', (int(r.anio),))
                if norm(n) == norm(r.proyecto)]
        if len(cand) > 1:  # mismo nombre en dos proyectos (FAMESA / CELSA 2025): desempata el cliente
            cand = [c for c in cand if norm(c[1]).startswith(norm(r.cliente)[:6])] or cand[:1]
        if not cand:
            sin_match.append(r.cod)
            cur.execute('INSERT INTO proyecto (anio, cliente, nombre) VALUES (?,?,?)',
                        (int(r.anio), r.cliente, r.proyecto))
            pid = cur.lastrowid
        else:
            pid = cand[0][0]
        cur.execute('''UPDATE proyecto SET codigo_muestra=?, tipo_estructura_id=?, toneladas=?, fuente_tonelaje=?,
                       dias_retraso_hab=?, en_muestra=1 WHERE id=?''',
                    (int(r.cod), tipo_id[r.tipo], float(r.ton), r.fuente_ton, float(r.ret_hab), pid))
        dif = cur.execute('SELECT dias_retraso FROM proyecto WHERE id=?', (pid,)).fetchone()[0]
        if dif is not None and dif != r.ret_cal:
            print(f'  ! retraso distinto Word vs Excel en muestra {r.cod}: {dif} vs {r.ret_cal}')
    pid_de = dict(cur.execute('SELECT codigo_muestra, id FROM proyecto WHERE codigo_muestra IS NOT NULL'))

    for r in m.itertuples():
        cur.execute('''INSERT INTO proyecto_proceso (proyecto_id, proceso_id, n_personas, dias_plan,
                       dias_retraso_asig, dias_real, hh_ratio_vigente, fuente) VALUES (?,?,?,?,?,?,?,?)''',
                    (pid_de[r.cod], proceso_id[r.nproc], int(r.personas), float(r.dias_plan), float(r.dias_ret),
                     float(r.dias_real), float(r.hh_est), 'Proyectos_muestra_25 Dep.xlsx'))

    m['ratio'] = m.hh_est / m.ton
    rv = m.groupby(['tipo', 'nproc']).ratio.agg(['mean', 'std']).reset_index()
    for r in rv.itertuples():
        cur.execute('INSERT INTO ratio_vigente (tipo_estructura_id, proceso_id, hh_por_t) VALUES (?,?,?)',
                    (tipo_id[r.tipo], proceso_id[r.nproc], round(r.mean, 4)))
    print(f'  ratio_vigente: desviación máx. dentro de tipo×proceso = {rv["std"].max():.4f} HH/t '
          '(≈0 ⇒ HH estimadas = toneladas × ratio fijo)')

    # --- reporte de avance: HH reales por OT y avance por pieza ------------
    rep = EXTRAS / 'REPORTE DE AVANCE _PROYECTOS - copia.xlsx'
    cg = pd.read_excel(rep, sheet_name='CONTROL GENERAL', header=2).dropna(subset=['CENTRO DE COSTO'])
    cg = cg[cg['HORAS HOMBRE'].apply(lambda v: isinstance(v, (int, float)))]
    for r in cg.itertuples(index=False):
        cur.execute('INSERT INTO ot_hh_real VALUES (?,?,?,?,?,?)',
                    (str(r[1]), r[2], r[3], float(r[4]), float(r[9]), round(float(r[10]), 2)))

    for hoja in ('REPORTE_DE_HABILITADO', 'REPORTE_DE_AVANCE ZONA 2'):
        df = pd.read_excel(rep, sheet_name=hoja, header=15)
        df = df[pd.to_numeric(df['N°'], errors='coerce').notna()]
        df['PESO TOTAL NETO'] = pd.to_numeric(df.get('PESO TOTAL NETO'), errors='coerce')
        df = df[df['PESO TOTAL NETO'] > 0]
        col = lambda name: df[name] if name in df else pd.Series([None] * len(df), index=df.index)
        granallado = [c for c in df.columns if 'Granallado' in str(c) and 'FECHA' in str(c)]
        pintura = [c for c in df.columns if 'PINTURA' in str(c).upper() and 'FECHA' in str(c).upper()]
        for i, r in df.iterrows():
            num = lambda v: float(v) if isinstance(v, (int, float)) and not pd.isna(v) else None
            txt = lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()
            cur.execute('''INSERT INTO pieza_avance (hoja_origen, n_item, elemento, conjunto, perfil, longitud_mm,
                cantidad, peso_neto_kg, area_m2, contratista, orden_fab, precio_kg, f_inicio, f_armado, f_soldeo,
                f_liberacion, f_granallado, f_pintura, f_despacho) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (hoja, int(r['N°']), txt(r.get('ELEMENTO')), txt(r.get('CONJUNTO')), txt(r.get('PERFIL')),
                 num(r.get('LONG.')), num(r.get('CANT.')), num(r['PESO TOTAL NETO']), num(r.get('AREA TOTAL')),
                 txt(r.get('CONTRATISTA')) if isinstance(r.get('CONTRATISTA'), str) else None,
                 txt(r.get('O.F')), num(r.get('PRECIO UNITARIO')), fecha(r.get('FECHA DE INICIO')),
                 fecha(r.get('FECHA')), fecha(r.get('FECHA.1')), fecha(r.get('FECHA LIBERACION')),
                 fecha(r[granallado[0]]) if granallado else None, fecha(r[pintura[0]]) if pintura else None,
                 fecha(r.get('FECHA DE DESPACHO'))))

    # --- cotización ST087 (PDF) + ACU (Excel) ------------------------------
    import pdfplumber
    with pdfplumber.open(next(EXTRAS.glob('Cotizacion_ST087*.pdf'))) as pdf:
        texto = '\n'.join(p.extract_text() or '' for p in pdf.pages)
    monto = re.search(r'\$\s*([\d,]+\.\d+)', texto)
    plazo = re.search(r'TIEMPO DE EJECUCI[ÓO]N\s*\n?\s*(\d+)\s*d[ií]as,?\s*([^\n]*)', texto)
    validez = re.search(r'validez de esta oferta es por (\d+)', texto)
    pago = re.search(r'FORMA DE PAGO\s*\n\s*([^\n]+)', texto)
    ws = openpyxl.load_workbook(EXTRAS / 'Ejemplo data de un proyecto.xlsx', data_only=True).worksheets[0]
    filas = [[c for c in row] for row in ws.iter_rows(values_only=True)]
    acero = next(f for f in filas if f[7] == 'Acero')
    cur.execute('''INSERT INTO cotizacion (codigo, cliente, descripcion, fecha, peso_kg, monto, moneda, plazo_dias,
                   plazo_base, forma_pago, validez_dias) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                ('ST-PPTO 07_2026 ST087 Rv2', 'BYPS', 'Fabricación de inductores de flujo', '2026-09-14',
                 float(acero[10]), float(monto.group(1).replace(',', '')) if monto else None, 'USD',
                 float(plazo.group(1)) if plazo else None, plazo.group(2).strip() if plazo else None,
                 pago.group(1).strip() if pago else None, int(validez.group(1)) if validez else None))
    cot_id = cur.lastrowid
    for f in filas[3:]:
        if f[7] and isinstance(f[12], (int, float)):
            cur.execute('''INSERT INTO acu_linea (cotizacion_id, partida, unidad, metrado, peso_kg, costo_unit,
                           costo_total) VALUES (?,?,?,?,?,?,?)''',
                        (cot_id, str(f[7]).strip(), f[8], f[9] if isinstance(f[9], (int, float)) else None,
                         f[10] if isinstance(f[10], (int, float)) else None, f[11], f[12]))
        elif f[11] in ('CD', 'GG', 'Utilidad', 'Precio'):
            cur.execute('INSERT INTO acu_linea (cotizacion_id, partida, costo_unit, costo_total) VALUES (?,?,?,?)',
                        (cot_id, f[11], f[10], f[12]))

    con.commit()
    print('\nResumen de la BD:')
    for (t,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        print(f'  {t:25} {cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]:5} filas')
    print('\nOTD población (38):', cur.execute(
        'SELECT ROUND(100.0*SUM(dias_retraso<=0)/COUNT(*),1) FROM proyecto WHERE n_registro IS NOT NULL').fetchone())
    print('OTD muestra (25):', cur.execute(
        'SELECT ROUND(100.0*SUM(dias_retraso<=0)/COUNT(*),1) FROM proyecto WHERE en_muestra=1').fetchone())
    if sin_match:
        print('Muestra sin match en Tabla 3:', sin_match)
    print('Excluidos de la muestra:')
    for r in cur.execute('SELECT n_registro, anio, cliente, substr(nombre,1,60), dias_retraso FROM proyecto '
                         'WHERE en_muestra=0 ORDER BY n_registro'):
        print('  ', r)
    con.close()
    print(f'\nOK -> {DB}')


if __name__ == '__main__':
    main()
