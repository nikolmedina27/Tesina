"""Reconstruye (SIMULADA) la muestra de 25 proyectos cuando falta `extras/` y la BD tiene datos degenerados.

Cuándo se usa: `data/steelser.db` se puede haber creado sin los Excel de la empresa (que son confidenciales y no
están en el repo). En ese caso las 25 obras salen con toneladas idénticas (93 t) y cuadrillas de 1-4 personas, y
el motor CRP las programa en ~170 días cuando las duraciones reales son de 40-80 días: la simulación no tiene
sentido. Este script devuelve la muestra a un estado coherente, declarado como SIMULADO:

  - Conserva lo que sí es real: tipo de estructura, fechas de inicio / fin planificado / fin real (Tabla 3).
  - Toma las toneladas reales de la tabla de verificación de `docs/diseno/06_datos_simulados.md` (que se calculó
    con la BD original); si esa tabla no está, las simula (39-200 t, crecientes con la duración real).
  - Simula las cuadrillas por proceso (se calibra un factor por proyecto para que el motor reproduzca la
    duración real con φ = 1).
  - Recalcula las HH del ratio vigente (toneladas × ratio) y los días por proceso.
  - Marca `fuente_tonelaje = 'Estimada'` (el esquema no admite otro valor); lo simulado se declara aquí y en la documentación.

Si la BD ya tiene toneladas distintas entre proyectos (datos reales), no hace nada.
Uso: py scripts/reconstruir_muestra.py [--forzar]   (después: py -m dss.simulador y py -m dss.simulador_planta)
`--forzar` vuelve a reconstruir desde el respaldo `data/steelser_antes_reconstruccion.db`.
"""
import shutil
import sqlite3
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.crp_engine import programar, MAQUINAS, EXTERNOS, N_PROC, n_dias_laborables    # noqa: E402
from dss.datos import DB, ratio_vigente, TIPOS                                            # noqa: E402

BASE = np.array([3, 1, 1, 1, 1, 1, 1, 6, 6, 3, 3, 1, 2], float)     # cuadrilla de partida; se escala por proyecto
ESCALABLES = [j for j in range(N_PROC) if j not in MAQUINAS and j not in EXTERNOS]
DISP = np.full((400, 4), 0.92)                                       # disponibilidad media supuesta
FUENTE = 'Estimada'      # la restricción de la tabla solo admite 'Estimada' o 'Dato real'


def toneladas_documentadas():
    """Toneladas reales por código de muestra, leídas de la tabla de verificación de docs/diseno/06_datos_simulados.md."""
    f = Path(__file__).resolve().parent.parent / 'docs' / 'diseno' / '06_datos_simulados.md'
    if not f.exists():
        return {}
    t = {}
    for linea in f.read_text(encoding='utf-8').splitlines():
        c = [x.strip() for x in linea.strip().strip('|').split('|')]
        if len(c) >= 6 and c[0].isdigit() and c[1].isdigit() and c[3].isdigit():
            t[int(c[0])] = float(c[3])
    return t if len(t) == 25 else {}


def toneladas_por_rango(n_reales, semilla=2026):
    """Toneladas simuladas (39-200 t) con el mismo orden que la duración real (más largo = más grande)."""
    n = len(n_reales)
    q = np.exp(np.log(80) + 0.5 * norm.ppf((np.arange(n) + 0.5) / n))
    q = np.clip(q, 39, 200)
    orden = np.argsort(np.argsort(n_reales, kind='stable'), kind='stable')
    return np.round(q[orden], 0)


def duracion(hh, c, ext):
    crew = BASE.copy()
    crew[ESCALABLES] = np.maximum(BASE[ESCALABLES] * c, 0.5)
    return float(programar(hh[None, :], crew, DISP, ext[None, :])['fin'][0]), crew


def calibrar(hh, ext, n_real):
    """Factor de cuadrilla c con el que el motor (φ = 1) reproduce n_real días laborables."""
    lo, hi = 0.2, 40.0
    mejor = (1e9, 1.0)
    for _ in range(40):
        mid = np.sqrt(lo * hi)
        d, _ = duracion(hh, mid, ext)
        if abs(d - n_real) < mejor[0]:
            mejor = (abs(d - n_real), mid)
        if d > n_real:
            lo = mid
        else:
            hi = mid
    return mejor[1]


def main(forzar=False):
    copia = DB.with_name('steelser_antes_reconstruccion.db')
    if forzar and copia.exists():
        shutil.copy(copia, DB)
        print('Restaurado desde', copia.name)
    con = sqlite3.connect(DB)
    t = [r[0] for r in con.execute('SELECT DISTINCT toneladas FROM proyecto WHERE en_muestra=1')]
    if len(t) > 1:
        print('La muestra ya tiene toneladas distintas por proyecto (datos reales): no se reconstruye.')
        return
    copia = DB.with_name('steelser_antes_reconstruccion.db')
    if not copia.exists():
        shutil.copy(DB, copia)
        print('Respaldo:', copia.name)
    rv = ratio_vigente(con)
    P = con.execute('''SELECT p.id, p.codigo_muestra, p.fecha_inicio, p.fecha_fin_plan, p.fecha_fin_real, t.nombre
                       FROM proyecto p JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                       WHERE p.en_muestra=1 ORDER BY p.codigo_muestra''').fetchall()
    n_real = np.array([n_dias_laborables(r[2], r[4]) for r in P], float)
    doc = toneladas_documentadas()
    if doc:
        tons = np.array([doc[r[1]] for r in P])
        origen = 'reales (docs/diseno/06)'
    else:
        tons = toneladas_por_rango(n_real)
        origen = 'simuladas por rango'
    pr_ids = [r[0] for r in con.execute('SELECT id FROM proceso ORDER BY orden')]
    resid = []
    for (pid, cod, ini, fp, fr, tipo), ton, nr in zip(P, tons, n_real):
        hh = ton * rv.loc[tipo].values
        ext0 = np.array([r[0] for r in con.execute(
            '''SELECT pp.dias_plan FROM proyecto_proceso pp JOIN proceso pr ON pr.id=pp.proceso_id
               WHERE pp.proyecto_id=? AND pr.orden IN (7,12) ORDER BY pr.orden''', (pid,))], float)
        ext = np.maximum(1.0, np.round(ext0 * (ton / 93.0) ** 0.5))
        c = calibrar(hh, ext, nr)
        _, crew = duracion(hh, c, ext)
        crew = np.round(crew)
        o = programar(hh[None, :], crew, DISP, ext[None, :])
        dias = np.maximum(1, (o['fin_proc'][0] - o['ini'][0]).astype(int))
        resid.append(float(o['fin'][0] - nr))
        con.execute('UPDATE proyecto SET toneladas=?, fuente_tonelaje=? WHERE id=?', (float(ton), FUENTE, pid))
        for j, proc_id in enumerate(pr_ids):
            con.execute('''UPDATE proyecto_proceso SET hh_ratio_vigente=?, n_personas=?, dias_plan=?, dias_real=?
                           WHERE proyecto_id=? AND proceso_id=?''',
                        (float(hh[j]), int(crew[j]), float(dias[j]), float(dias[j]), pid, proc_id))
    con.commit()
    con.close()
    r = np.array(resid)
    print(f'Muestra reconstruida: {len(P)} proyectos, toneladas {origen} {tons.min():.0f}-{tons.max():.0f} (media {tons.mean():.0f}).')
    print(f'Duración del motor con φ=1 vs real: error medio {np.abs(r).mean():.1f} d, máx {np.abs(r).max():.0f} d, sesgo {r.mean():+.1f} d')


if __name__ == '__main__':
    main(forzar='--forzar' in sys.argv)
