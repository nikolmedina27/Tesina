"""Generador de datos SIMULADOS anclados a los 25 proyectos reales (2021-2026).

Qué es real y se respeta:  toneladas, tipo, fechas de inicio / fin planificado / fin real,
cuadrilla y días planificados por proceso, y el ratio vigente (HH estimadas).
Qué se simula:  paradas de las 4 máquinas, plazos de servicios externos, variables del
plano y las HH reales por proceso (variable objetivo de C2).

Las HH simuladas se condicionan a los resultados reales (ABC): de miles de "verdades"
posibles se elige la que, programada con el motor CRP sobre las paradas simuladas,
reproduce la duración real de cada proyecto. Todo queda marcado como SIMULADO.
"""
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .crp_engine import (N_PROC, LAM_DEFECTO, MAQUINAS, EXTERNOS, WEEKMASK, programar,
                         dias_laborables, n_dias_laborables)
from .datos import CargaTaller

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / 'data' / 'steelser.db'
TIPOS = ['Nave industrial / packing / cobertura', 'Planta industrial / minería',
         'Edificación / infraestructura', 'Mezzanine / plataformas / oficinas']
CONTRATISTAS = ['T&C FABRICACION', 'FRANCISCO TARRILLO', 'RFR METALICAS', 'ROGGER TORRES', 'LHL INGENIERIA']
MAQ_NOMBRE = ['Sierra Cinta Kaltenbach', 'Cizalladora Punzonadora Pedimax', 'Mesa CNC', 'Roscadora RIDGID']


@dataclass
class Mundo:
    id: int
    nombre: str
    descripcion: str
    sesgo_tipo: dict = field(default_factory=dict)      # log φ medio por tipo de estructura
    sesgo_proc: dict = field(default_factory=dict)      # log φ medio por proceso (1-13)
    sigma: float = 0.15                                 # desvío idiosincrático por proceso
    rho: float = 0.5                                    # correlación entre procesos de un proyecto
    colas_t: int = 0                                    # 0 = normal; k = t de Student con k g.l.
    no_lineal: bool = False
    deriva_desde: str | None = None                     # fecha a partir de la cual cambia el taller
    deriva_contratista: float = 0.0
    mtbf: tuple = (12, 9, 15, 25)                       # días laborables entre fallas por máquina
    mtbf_deriva: float = 1.0                            # factor sobre MTBF tras la deriva
    gamma_ton: float = 0.08                             # los proyectos chicos cuestan más HH/t


MUNDOS = [
    Mundo(1, 'M1 ratio casi correcto', 'El ratio vigente ya es bueno: φ ≈ 1 ± 6 %. El modelo no debe empeorarlo.',
          sigma=0.06, rho=0.3, gamma_ton=0.0, mtbf=(18, 14, 22, 35)),
    Mundo(2, 'M2 sesgo sistemático', 'El ratio subestima soldeo/armado y las plantas industriales; ruido moderado.',
          sesgo_tipo={TIPOS[1]: 0.12, TIPOS[2]: 0.05, TIPOS[0]: -0.04, TIPOS[3]: 0.02},
          sesgo_proc={9: 0.10, 8: 0.06, 12: 0.05}, sigma=0.15, rho=0.5),
    Mundo(3, 'M3 no lineal y colas pesadas', 'Efectos no lineales con las variables del plano y errores t(4).',
          sesgo_tipo={TIPOS[1]: 0.10, TIPOS[2]: 0.04, TIPOS[0]: -0.03, TIPOS[3]: 0.02},
          sesgo_proc={9: 0.08, 8: 0.05, 12: 0.04}, sigma=0.12, rho=0.5, colas_t=4, no_lineal=True),
    Mundo(4, 'M4 deriva del taller', 'Como M2, pero desde 2024 entra un contratista más lento y las máquinas fallan más.',
          sesgo_tipo={TIPOS[1]: 0.12, TIPOS[2]: 0.05, TIPOS[0]: -0.04, TIPOS[3]: 0.02},
          sesgo_proc={9: 0.10, 8: 0.06, 12: 0.05}, sigma=0.15, rho=0.5,
          deriva_desde='2024-01-01', deriva_contratista=0.15, mtbf_deriva=0.6),
    Mundo(5, 'M5 disponibilidad baja', 'Como M2 pero con paradas frecuentes: disponibilidad media ≈ 80 % (72-88 % por máquina), cerca de la celda CNC de Hollerweger et al. (69-78 %).',
          sesgo_tipo={TIPOS[1]: 0.12, TIPOS[2]: 0.05, TIPOS[0]: -0.04, TIPOS[3]: 0.02},
          sesgo_proc={9: 0.10, 8: 0.06, 12: 0.05}, sigma=0.15, rho=0.5, mtbf=(3.8, 2.9, 4.7, 7.8)),
]


# --------------------------------------------------------------------------- datos reales
def cargar_reales(con):
    P = pd.read_sql('''SELECT p.id pid, p.codigo_muestra cod, p.anio, p.nombre, t.nombre tipo, p.toneladas ton,
                       p.fecha_inicio ini, p.fecha_fin_plan fp, p.fecha_fin_real fr, p.dias_retraso ret
                       FROM proyecto p JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                       WHERE p.en_muestra=1 ORDER BY p.codigo_muestra''', con)
    X = pd.read_sql('''SELECT p.codigo_muestra cod, pr.orden, pp.n_personas, pp.dias_plan, pp.dias_real,
                       pp.hh_ratio_vigente hh_ratio, pp.proceso_id
                       FROM proyecto_proceso pp JOIN proyecto p ON p.id=pp.proyecto_id
                       JOIN proceso pr ON pr.id=pp.proceso_id WHERE p.en_muestra=1 ORDER BY cod, orden''', con)
    P['n_plan'] = [n_dias_laborables(a, b) for a, b in zip(P.ini, P.fp)]
    P['n_real'] = [n_dias_laborables(a, b) for a, b in zip(P.ini, P.fr)]
    return P, X


# --------------------------------------------------------------------------- variables del plano
def generar_features(P, semilla=7):
    """Variables que el cotizador podría extraer del plano. Independientes del mundo."""
    rng = np.random.default_rng(semilla)
    n = len(P)
    f = pd.DataFrame({'cod': P.cod.values})
    f['piezas_por_t'] = np.exp(rng.normal(np.log(8), 0.5, n))
    f['n_piezas'] = np.round(f.piezas_por_t * P.ton.values).astype(int)
    f['pct_planchas'] = rng.beta(2, 8, n)
    f['m2_pintura'] = np.round(np.exp(rng.normal(np.log(14), 0.3, n)) * P.ton.values, 1)
    f['montaje'] = rng.random(n) < 0.35
    f['contratista'] = rng.choice(CONTRATISTAS, n, p=[.3, .25, .2, .15, .1])
    return f


# --------------------------------------------------------------------------- paradas y disponibilidad
def generar_paradas(mundo, fecha_ini='2019-01-01', fecha_fin='2026-12-31', semilla=11):
    """Eventos de parada por máquina y disponibilidad diaria D (1 = sin pérdida)."""
    rng = np.random.default_rng(semilla + mundo.id)
    fechas = np.arange(np.datetime64(fecha_ini, 'D'), np.datetime64(fecha_fin, 'D') + np.timedelta64(1, 'D'))
    lab = np.is_busday(fechas, weekmask=WEEKMASK)
    dias = fechas[lab]
    n = len(dias)
    D = np.ones((n, 4))
    eventos = []
    deriva_i = None if mundo.deriva_desde is None else int(np.searchsorted(dias, np.datetime64(mundo.deriva_desde)))
    for k in range(4):
        t = 0.0
        while True:
            fac = mundo.mtbf_deriva if (deriva_i is not None and t >= deriva_i) else 1.0
            t += rng.exponential(mundo.mtbf[k] * fac)
            if t >= n: break
            dur = float(np.clip(np.exp(rng.normal(np.log(0.6), 0.9)), 0.1, 10))     # días laborables
            i0, rest = int(t), dur
            eventos.append((k, str(dias[i0]), dur, 0))
            for i in range(i0, n):
                perdida = min(1.0, rest)
                D[i, k] = max(0.0, D[i, k] - perdida)
                rest -= perdida
                if rest <= 1e-9: break
        for i in range(10, n, 30):                                                    # mantenimiento planificado
            D[i, k] = max(0.0, D[i, k] - 0.5)
            eventos.append((k, str(dias[i]), 0.5, 1))
    return dias, D, eventos


def disp_de_proyecto(dias_cal, D, inicio, T=300):
    """Disponibilidad (T, 4) de los T días laborables que siguen a `inicio`."""
    i0 = int(np.searchsorted(dias_cal, np.datetime64(inicio, 'D')))
    d = D[i0:i0 + T]
    if len(d) < T:
        d = np.vstack([d, np.ones((T - len(d), 4))])
    return d


# --------------------------------------------------------------------------- φ verdadero (prior del mundo)
def muestrear_phi(mundo, proj, x, feat, R, rng, tipo_idx):
    """log φ_ij para R réplicas: (R, 13). `proj` fila de P, `feat` fila de features."""
    j = np.arange(1, N_PROC + 1)
    mu = np.array([mundo.sesgo_proc.get(int(q), 0.0) for q in j]) + mundo.sesgo_tipo.get(proj.tipo, 0.0)
    mu = mu - mundo.gamma_ton * np.log(proj.ton / 80.0)
    z_pl = (feat.pct_planchas - 0.2) / 0.1
    z_pz = (np.log(feat.piezas_por_t) - np.log(8)) / 0.5
    efecto = np.zeros(N_PROC)
    efecto[4] += 0.05 * z_pl; efecto[2] -= 0.02 * z_pl                    # planchas: mesa CNC
    efecto[7] += 0.04 * z_pz; efecto[8] += 0.05 * z_pz                    # piezas por t: armado y soldeo
    efecto[11] += 0.06 * (np.log(feat.m2_pintura / proj.ton / 14) / 0.3)   # m² de pintura
    if mundo.no_lineal:
        efecto[[7, 8]] += 0.16 * (feat.piezas_por_t > 11) + 0.08 * z_pl * z_pz   # umbral e interacción
        efecto[4] += 0.10 * (feat.pct_planchas > 0.3)
    mu = mu + efecto
    if mundo.deriva_desde and proj.ini >= mundo.deriva_desde:
        mu[[7, 8, 9]] += mundo.deriva_contratista
    sig = np.where(np.isin(np.arange(N_PROC), MAQUINAS), 1.0, 1.0) * mundo.sigma
    eta = rng.standard_normal((R, 1))
    if mundo.colas_t:
        eps = rng.standard_t(mundo.colas_t, (R, N_PROC)) / np.sqrt(mundo.colas_t / (mundo.colas_t - 2))
    else:
        eps = rng.standard_normal((R, N_PROC))
    return mu + sig * (np.sqrt(mundo.rho) * eta + np.sqrt(1 - mundo.rho) * eps)


# --------------------------------------------------------------------------- condicionamiento ABC
def simular_mundo(mundo, P, X, feats, con, lam=LAM_DEFECTO, R=3000, semilla=2026):
    rng = np.random.default_rng(semilla + mundo.id)
    dias_cal, D, eventos = generar_paradas(mundo)
    carga = CargaTaller(con, dias_cal)
    filas, resumen = [], []
    for i, proj in enumerate(P.itertuples()):
        x = X[X.cod == proj.cod].sort_values('orden')
        hh_ratio = x.hh_ratio.values
        crew = x.n_personas.values.astype(float)
        ext_plan = x.dias_plan.values[EXTERNOS].astype(float)
        disp = CargaTaller.efectiva(disp_de_proyecto(dias_cal, D, proj.ini), carga.u(proj.ini, excluir=proj.pid))
        logphi = muestrear_phi(mundo, proj, x, feats.iloc[i], R, rng, TIPOS.index(proj.tipo))
        phi = np.exp(logphi)
        ext = ext_plan * np.exp(rng.normal(0, 0.2, (R, 2)))
        o = programar(hh_ratio[None, :] * phi, crew, disp, ext, lam=lam)
        err = o['fin'] - proj.n_real
        mejor = np.abs(err).min()
        cand = np.flatnonzero(np.abs(err) == mejor)
        r = int(rng.choice(cand))
        acept = float((np.abs(err) <= 1).mean())
        ini_d = dias_laborables(proj.ini, 1)[0]
        for j in range(N_PROC):
            fi = int(o['ini'][r, j]); ff = int(o['fin_proc'][r, j])
            filas.append((mundo.id, int(proj.pid), int(x.proceso_id.values[j]), float(hh_ratio[j] * phi[r, j]),
                          float(phi[r, j]), ff - fi,
                          str(np.busday_offset(ini_d, fi, weekmask=WEEKMASK)),
                          str(np.busday_offset(ini_d, ff - 1, weekmask=WEEKMASK))))
        resumen.append(dict(cod=proj.cod, n_real=proj.n_real, n_sim=int(o['fin'][r]), residuo=int(o['fin'][r] - proj.n_real),
                            aceptacion=round(acept, 3), phi_prom=float(np.average(phi[r], weights=hh_ratio))))
    return filas, pd.DataFrame(resumen), eventos


# --------------------------------------------------------------------------- persistencia
SCHEMA_SIM = '''
DROP TABLE IF EXISTS sim_mundo; DROP TABLE IF EXISTS sim_feature; DROP TABLE IF EXISTS sim_proyecto_proceso;
DROP TABLE IF EXISTS sim_parada; DROP TABLE IF EXISTS sim_verificacion;
CREATE TABLE sim_mundo (id INTEGER PRIMARY KEY, nombre TEXT, descripcion TEXT, parametros TEXT);
CREATE TABLE sim_feature (proyecto_id INTEGER PRIMARY KEY REFERENCES proyecto(id), n_piezas INTEGER,
    piezas_por_t REAL, pct_planchas REAL, m2_pintura REAL, montaje INTEGER, contratista TEXT);
CREATE TABLE sim_proyecto_proceso (mundo_id INTEGER REFERENCES sim_mundo(id), proyecto_id INTEGER REFERENCES proyecto(id),
    proceso_id INTEGER REFERENCES proceso(id), hh_real REAL, phi REAL, dias_real INTEGER, f_inicio TEXT, f_fin TEXT,
    origen TEXT NOT NULL DEFAULT 'SIMULADO', PRIMARY KEY (mundo_id, proyecto_id, proceso_id));
CREATE TABLE sim_parada (mundo_id INTEGER, centro_id INTEGER, fecha TEXT, dias_perdidos REAL, planificada INTEGER);
CREATE TABLE sim_verificacion (mundo_id INTEGER, codigo_muestra INTEGER, dias_lab_real INTEGER, dias_lab_sim INTEGER,
    residuo INTEGER, aceptacion REAL, phi_prom REAL, PRIMARY KEY (mundo_id, codigo_muestra));
'''


def guardar(con, mundos_res, feats, P):
    con.executescript(SCHEMA_SIM)
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    for m, (filas, res, eventos) in mundos_res:
        con.execute('INSERT INTO sim_mundo VALUES (?,?,?,?)',
                    (m.id, m.nombre, m.descripcion, json.dumps({k: v for k, v in m.__dict__.items()
                                                              if k not in ('id', 'nombre', 'descripcion')}, default=str)))
        con.executemany('INSERT INTO sim_proyecto_proceso (mundo_id, proyecto_id, proceso_id, hh_real, phi, dias_real, '
                        'f_inicio, f_fin) VALUES (?,?,?,?,?,?,?,?)', filas)
        con.executemany('INSERT INTO sim_parada VALUES (?,?,?,?,?)',
                        [(m.id, cen[MAQ_NOMBRE[k]], f, d, p) for k, f, d, p in eventos])
        con.executemany('INSERT INTO sim_verificacion VALUES (?,?,?,?,?,?,?)',
                        [(m.id, int(r.cod), int(r.n_real), int(r.n_sim), int(r.residuo), r.aceptacion, r.phi_prom)
                         for r in res.itertuples()])
    for i, r in enumerate(feats.itertuples()):
        con.execute('INSERT INTO sim_feature VALUES (?,?,?,?,?,?,?)',
                    (int(P.pid.iloc[i]), int(r.n_piezas), float(r.piezas_por_t), float(r.pct_planchas),
                     float(r.m2_pintura), int(r.montaje), r.contratista))
    con.commit()


def main():
    con = sqlite3.connect(DB)
    P, X = cargar_reales(con)
    feats = generar_features(P)
    resultados = []
    for m in MUNDOS:
        filas, res, ev = simular_mundo(m, P, X, feats, con)
        resultados.append((m, (filas, res, ev)))
        print(f'{m.nombre:34} residuo medio {res.residuo.abs().mean():.2f} d  máx {res.residuo.abs().max()} d  '
              f'aceptación media {res.aceptacion.mean():.2f}  φ medio {res.phi_prom.mean():.3f}')
    guardar(con, resultados, feats, P)
    con.close()


if __name__ == '__main__':
    main()
