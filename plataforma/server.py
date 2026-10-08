"""SteelPlan · servidor web (FastAPI).

Ejecutar:  py -m uvicorn plataforma.server:app --port 8600     (o lanzador/iniciar_plataforma.bat)
Abrir:     http://localhost:8600

Dos BD: data/steelser.db (histórico, solo lectura aquí) y data/plataforma.db (operación diaria).
El modelo de horas (C2) se entrena con datos SIMULADOS (escenario M2) hasta tener tareos reales.
"""
import json
import secrets
import sqlite3
import threading
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from dss.c2_modelo import dataset, PhiQRF
from dss.c3_montecarlo import Cotizador, Proyecto, alpha_optimo, MTBF_DEFECTO, TAUS
from dss.crp_engine import programar, WEEKMASK, N_PROC, MAQUINAS as MAQUINAS_CRP
from dss.datos import TIPOS, cuadrilla, dias_externos, mtbf_estimado
from dss.simulador import MAQ_NOMBRE
from . import db_plataforma as dbp
from dss.mantenimiento import indicadores as indicadores_mant
from .avance import ETAPAS, curva_s, error_orden_etapas, resumen_piezas, semanas
from .formato import LISTAS
from .importador import importar, tipo_modelo

warnings.filterwarnings('ignore')
RAIZ = Path(__file__).resolve().parent.parent
WEB = Path(__file__).resolve().parent / 'web'
HIST = RAIZ / 'data' / 'steelser.db'
MUNDO_ENTRENAMIENTO = 2

PROCESOS = ['Ingeniería', 'Compra de material', 'Habilitado · sierra cinta', 'Habilitado · cizalla-punzonadora',
            'Habilitado · mesa CNC', 'Roscado de barra lisa', 'Doblez (externo)', 'Armado', 'Soldeo', 'Limpieza',
            'Despacho a pintura', 'Granallado y pintura (externo)', 'Despacho a obra']
CATEGORIA = ['interno', 'interno', 'maquina', 'maquina', 'maquina', 'maquina', 'externo', 'contratista',
             'contratista', 'contratista', 'interno', 'externo', 'interno']
CAUSAS = ['Falla mecánica', 'Falla eléctrica', 'Falta de repuesto', 'Lubricación', 'Cambio de herramienta / setup',
          'Falta de operador', 'Falta de material', 'Mantenimiento preventivo', 'Otro']
CONTRATISTAS = ['T&C FABRICACION', 'FRANCISCO TARRILLO', 'RFR METALICAS', 'ROGGER TORRES', 'LHL INGENIERIA']
IMPUTABLE = LISTAS['IMPUTABLE']


def _secreto():
    f = RAIZ / 'data' / 'secret.key'
    if not f.exists():
        f.write_text(secrets.token_hex(32))
    return f.read_text().strip()


dbp.inicializar()
app = FastAPI(title='SteelPlan', docs_url='/api/docs')
app.add_middleware(SessionMiddleware, secret_key=_secreto(), max_age=60 * 60 * 12, same_site='lax')
app.mount('/static', StaticFiles(directory=WEB), name='static')


@app.middleware('http')
async def sin_cache(request: Request, call_next):
    """La interfaz se revalida siempre: así, tras actualizar el código, el navegador no se queda con una versión vieja."""
    r = await call_next(request)
    p = request.url.path
    if p == '/' or p.startswith('/static') or p in ('/sw.js', '/manifest.webmanifest'):
        r.headers['Cache-Control'] = 'no-cache'
    return r


# ------------------------------------------------------------------ recursos compartidos
class Motor:
    """Cotizador y modelo de horas, construidos una sola vez al arrancar."""
    _cot = None
    _lock = threading.Lock()

    @classmethod
    def get(cls):
        with cls._lock:
            return cls._construir()

    @classmethod
    def _construir(cls):
        if cls._cot is None:
            con = sqlite3.connect(HIST, check_same_thread=False)
            df = dataset(con, MUNDO_ENTRENAMIENTO)
            cls._cot = Cotizador(con, PhiQRF().fit(df))
            cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
            cls.mtbf_sim = mtbf_estimado(con, MUNDO_ENTRENAMIENTO, [cen[n] for n in MAQ_NOMBRE], '2027-01-01')
            cls.n_entreno = df.pid.nunique()
        return cls._cot


threading.Thread(target=Motor.get, daemon=True).start()     # entrena el modelo en segundo plano al arrancar


def hist():
    con = sqlite3.connect(HIST, check_same_thread=False)    # FastAPI corre la dependencia y el endpoint en hilos distintos
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def plat():
    con = dbp.conectar()
    try:
        yield con
    finally:
        con.close()


def usuario_actual(request: Request, con=Depends(plat)):
    uid = request.session.get('uid')
    u = con.execute('SELECT id, usuario, nombre, rol, area, color FROM usuario WHERE id=? AND activo=1', (uid,)).fetchone() if uid else None
    if not u:
        raise HTTPException(401, 'Sesión no iniciada')
    return dict(u)


def requiere(*roles):
    def dep(u=Depends(usuario_actual)):
        if u['rol'] not in roles and u['rol'] != 'gerencia':
            raise HTTPException(403, f'Requiere rol: {", ".join(roles)}')
        return u
    return dep


def actividad(con, u, tipo, detalle, proyecto_id=None, tarea_id=None):
    con.execute('INSERT INTO actividad (usuario_id, tipo, detalle, proyecto_id, tarea_id) VALUES (?,?,?,?,?)',
                (u['id'], tipo, detalle, proyecto_id, tarea_id))


def dia(base, n):
    return str(np.busday_offset(np.datetime64(base, 'D'), int(n), roll='forward', weekmask=WEEKMASK))


def programa_a_gantt(inicio, programa, prefijo, avance=None, hh=None):
    tareas = []
    for j, (a, b) in enumerate(programa):
        if a is None or b is None:
            continue
        tareas.append(dict(id=f'{prefijo}{j + 1}', name=PROCESOS[j], start=dia(inicio, a), end=dia(inicio, max(b - 1, a)),
                           progress=round(100 * (avance[j] if avance is not None else 0)), categoria=CATEGORIA[j],
                           hh=None if hh is None else round(float(hh[j]))))
    return tareas


# ------------------------------------------------------------------ páginas y sesión
@app.get('/')
def index():
    return FileResponse(WEB / 'index.html')


@app.get('/sw.js')
def service_worker():
    """En la raíz para que su alcance cubra toda la aplicación (PWA instalable en la tablet de planta)."""
    return FileResponse(WEB / 'sw.js', media_type='application/javascript', headers={'Cache-Control': 'no-cache'})


@app.get('/manifest.webmanifest')
def manifiesto():
    return FileResponse(WEB / 'manifest.webmanifest', media_type='application/manifest+json')


class Login(BaseModel):
    usuario: str
    clave: str


@app.post('/api/login')
def login(datos: Login, request: Request, con=Depends(plat)):
    u = con.execute('SELECT * FROM usuario WHERE usuario=? AND activo=1', (datos.usuario.strip().lower(),)).fetchone()
    if not u or not dbp.verificar_clave(datos.clave, u['clave_hash'], u['sal']):
        raise HTTPException(401, 'Usuario o clave incorrectos')
    request.session['uid'] = u['id']
    return {'ok': True}


@app.post('/api/logout')
def logout(request: Request):
    request.session.clear()
    return {'ok': True}


@app.get('/api/me')
def me(u=Depends(usuario_actual)):
    return u | {'rol_nombre': dbp.ROLES[u['rol']]}


@app.get('/api/catalogos')
def catalogos(u=Depends(usuario_actual), con=Depends(plat)):
    return dict(procesos=[dict(id=i + 1, nombre=p, categoria=c) for i, (p, c) in enumerate(zip(PROCESOS, CATEGORIA))],
                maquinas=MAQ_NOMBRE, causas=CAUSAS, contratistas=CONTRATISTAS, tipos=TIPOS, roles=dbp.ROLES, imputable=IMPUTABLE,
                etapas=[dict(col=c, nombre=n, peso=round(100 * w, 1)) for c, n, w, _ in ETAPAS],
                usuarios=[dict(r) for r in con.execute('SELECT id, nombre, rol, color FROM usuario WHERE activo=1')],
                proyectos=[dict(r) for r in con.execute(
                    "SELECT id, codigo, nombre FROM proyecto_activo WHERE estado IN ('EN_CURSO','PAUSADO') ORDER BY id DESC")])


# ------------------------------------------------------------------ tablero
@app.get('/api/dashboard')
def dashboard(u=Depends(usuario_actual), h=Depends(hist), p=Depends(plat)):
    otd = [dict(r) for r in h.execute('SELECT * FROM v_otd ORDER BY anio')]
    tot = h.execute('SELECT COUNT(*) n, SUM(dias_retraso>0) atr, AVG(MAX(dias_retraso,0)) ret FROM proyecto WHERE n_registro IS NOT NULL').fetchone()
    activos = [dict(r) for r in p.execute("SELECT * FROM proyecto_activo WHERE estado='EN_CURSO'")]
    tareas = dict(p.execute('SELECT estado, COUNT(*) FROM tarea GROUP BY estado').fetchall())
    hh7 = p.execute("SELECT COALESCE(SUM(hh),0) FROM tareo WHERE fecha >= ?", (str(date.today() - timedelta(days=7)),)).fetchone()[0]
    # Dₖ de 30 días con el mismo cálculo que la vista Mantenimiento (dss/mantenimiento.py)
    d30, manana = str(date.today() - timedelta(days=30)), str(date.today() + timedelta(days=1))
    r0 = p.execute('SELECT MIN(inicio) FROM parada').fetchone()[0]       # antes del primer registro no hay dato
    d30 = max(d30, r0[:10]) if r0 else d30
    disp = {}
    for m in MAQ_NOMBRE:
        par = [dict(r) for r in p.execute('SELECT inicio, fin, planificada, causa FROM parada WHERE maquina=? AND fin>=?', (m, d30))]
        disp[m] = indicadores_mant(par, d30, manana)['dk'] or 1.0
    feed = [dict(r) for r in p.execute('''SELECT a.*, u.nombre, u.color FROM actividad a LEFT JOIN usuario u ON u.id=a.usuario_id
                                          ORDER BY a.id DESC LIMIT 12''')]
    criticas = [dict(r) for r in p.execute('''SELECT t.id, t.titulo, t.tipo, t.prioridad, t.fecha_limite, u.nombre responsable
                                              FROM tarea t LEFT JOIN usuario u ON u.id=t.responsable_id
                                              WHERE t.estado!='HECHO' AND (t.prioridad=1 OR t.tipo IN ('BLOQUEO','NO_CONFORMIDAD'))
                                              ORDER BY t.prioridad LIMIT 6''')]
    return dict(historico=dict(proyectos=tot['n'], atrasados=tot['atr'], otd=round(100 * (tot['n'] - tot['atr']) / tot['n'], 1),
                               retraso_prom=round(tot['ret'], 2)), otd_anual=otd, activos=activos, tareas=tareas, hh_7d=hh7,
                disponibilidad=disp, actividad=feed, criticas=criticas)


# ------------------------------------------------------------------ histórico
@app.get('/api/proyectos')
def proyectos(u=Depends(usuario_actual), h=Depends(hist)):
    q = '''SELECT p.id, p.n_registro, p.codigo_muestra, p.anio, p.cliente, p.nombre, t.nombre tipo, p.toneladas,
                  p.fecha_inicio, p.fecha_fin_plan, p.fecha_fin_real, p.dias_retraso, p.en_muestra
           FROM proyecto p LEFT JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
           WHERE p.n_registro IS NOT NULL ORDER BY p.fecha_inicio DESC'''
    return [dict(r) for r in h.execute(q)]


@app.get('/api/proyectos/{pid}')
def proyecto(pid: int, u=Depends(usuario_actual), h=Depends(hist)):
    p = h.execute('''SELECT p.*, t.nombre tipo FROM proyecto p LEFT JOIN tipo_estructura t ON t.id=p.tipo_estructura_id
                     WHERE p.id=?''', (pid,)).fetchone()
    if not p:
        raise HTTPException(404)
    p = dict(p)
    out = dict(proyecto=p, gantt_plan=[], gantt_sim=[], procesos=[])
    if p['en_muestra']:
        x = pd.read_sql('''SELECT pr.orden, pp.n_personas, pp.dias_plan, pp.hh_ratio_vigente hh FROM proyecto_proceso pp
                           JOIN proceso pr ON pr.id=pp.proceso_id WHERE pp.proyecto_id=? ORDER BY pr.orden''', h, params=(pid,))
        o = programar(x.hh.values[None], x.n_personas.values.astype(float), np.ones((300, 4)), x.dias_plan.values[[6, 11]][None])
        prog = list(zip(o['ini'][0].astype(int), o['fin_proc'][0].astype(int)))
        out['gantt_plan'] = programa_a_gantt(p['fecha_inicio'], prog, 'p', hh=x.hh.values)
        s = h.execute('''SELECT pr.orden, s.f_inicio, s.f_fin, s.hh_real FROM sim_proyecto_proceso s JOIN proceso pr ON pr.id=s.proceso_id
                         WHERE s.proyecto_id=? AND s.mundo_id=? ORDER BY pr.orden''', (pid, MUNDO_ENTRENAMIENTO)).fetchall()
        out['gantt_sim'] = [dict(id=f's{r["orden"]}', name=PROCESOS[r['orden'] - 1], start=r['f_inicio'], end=r['f_fin'],
                                 progress=100, categoria=CATEGORIA[r['orden'] - 1], hh=round(r['hh_real'])) for r in s]
        out['procesos'] = [dict(proceso=PROCESOS[i], personas=int(r.n_personas), dias_plan=float(r.dias_plan), hh_ratio=round(float(r.hh)))
                           for i, r in x.iterrows()]
    return out


@app.get('/api/gantt/taller')
def gantt_taller(u=Depends(usuario_actual), h=Depends(hist), p=Depends(plat)):
    hist_rows = [dict(id=f'h{r["id"]}', name=f'{r["cliente"][:22]} · {r["nombre"][:38]}', start=r['fecha_inicio'],
                      end=r['fecha_fin_real'], plan_fin=r['fecha_fin_plan'], retraso=r['dias_retraso'], anio=r['anio'],
                      categoria='retraso' if r['dias_retraso'] > 0 else 'cumple')
                 for r in h.execute('SELECT * FROM proyecto WHERE n_registro IS NOT NULL ORDER BY fecha_inicio')]
    act = [dict(id=f'a{r["id"]}', name=f'{r["codigo"]} · {r["nombre"][:40]}', start=r['inicio'], end=r['fecha_comprometida'],
                categoria='activo', anio=int(r['inicio'][:4]))
           for r in p.execute("SELECT * FROM proyecto_activo WHERE estado IN ('EN_CURSO','PAUSADO')")]
    return dict(historico=hist_rows, activos=act)


# ------------------------------------------------------------------ cotizador
class SolicitudCotizacion(BaseModel):
    tipo: str
    ton: float = Field(gt=0, le=2000)
    pct_planchas: float = 0.2
    piezas_por_t: float = 8.0
    m2_pint_t: float = 14.0
    montaje: bool = False
    presupuesto: float = 100000
    inicio: str
    fecha_pedida: str | None = None
    penalidad: float = 0.01
    pierde_por_dia: float = 0.005
    margen: float = 0.16
    alpha: float | None = None
    carga_extra: float = 0.0
    replicas: int = Field(1000, ge=100, le=3000)


def _resultado_json(res, s, alpha, presupuesto):
    f_rec = res.fecha_alpha(alpha)
    curva = [dict(fecha=str(d), plazo=pl, prob=round(pr, 4), pen=round(pe, 2)) for d, pl, pr, pe in res.curva(s.penalidad)]
    c_o = s.pierde_por_dia * s.margen * presupuesto
    pl_min = min(c['plazo'] for c in curva)
    for c in curva:
        c['costo'] = round(c['pen'] + c_o * (c['plazo'] - pl_min), 2)
    hh = res.hh
    return dict(fecha_recomendada=str(f_rec), plazo=res.plazo_calendario(f_rec), prob=res.prob_cumplir(f_rec),
                penalidad=res.penalidad_esperada(f_rec, s.penalidad), alpha=alpha,
                p50=str(res.fecha_alpha(0.5)), p90=str(res.fecha_alpha(0.9)), curva=curva,
                hh=[dict(proceso=PROCESOS[j], categoria=CATEGORIA[j], p10=round(float(np.percentile(hh[:, j], 10))),
                         p50=round(float(np.percentile(hh[:, j], 50))), p90=round(float(np.percentile(hh[:, j], 90)))) for j in range(N_PROC)],
                hh_total_p50=round(float(np.median(hh.sum(1)))), histograma=np.unique(res.fechas.astype(str), return_counts=True)[1].tolist(),
                histograma_fechas=np.unique(res.fechas.astype(str)).tolist(),
                gantt=programa_a_gantt(res.inicio, res.programa, 'c', hh=np.median(hh, axis=0)), programa=res.programa)


@app.post('/api/cotizar')
def cotizar(s: SolicitudCotizacion, u=Depends(requiere('cotizador', 'jefe_taller')), p=Depends(plat)):
    if s.tipo not in TIPOS:
        raise HTTPException(422, 'Tipo de estructura no válido')
    cot = Motor.get()
    proy = Proyecto(s.tipo, s.ton, s.inicio, s.presupuesto, s.pct_planchas, s.piezas_por_t, s.m2_pint_t, s.montaje)
    alpha = s.alpha if s.alpha else alpha_optimo(s.penalidad, s.pierde_por_dia, s.margen)
    oc = _ocupacion(p, s.inicio)              # carga real: lo que toman los proyectos en curso según el plan aprobado
    ocup = None if oc is None else np.clip(oc['frac'] + s.carga_extra, 0, 0.95)
    res = cot.cotizar(proy, R=s.replicas, alpha=alpha, mtbf=mtbf_actual(p), semilla=7, carga_extra=s.carga_extra, ocupacion=ocup)
    out = _resultado_json(res, s, alpha, s.presupuesto)
    hh_ratio = s.ton * cot.rv.loc[s.tipo].values
    o = programar(hh_ratio[None], cuadrilla(cot.par_cuad, s.ton), np.ones((300, 4)), dias_externos(cot.par_ext, s.ton)[None])
    out['fecha_metodo_actual'] = dia(s.inicio, int(o['fin'][0]) - 1)
    out['prob_metodo_actual'] = res.prob_cumplir(out['fecha_metodo_actual'])
    out['hh_ratio_total'] = round(float(hh_ratio.sum()))
    if s.fecha_pedida:
        out['pedida'] = dict(fecha=s.fecha_pedida, prob=res.prob_cumplir(s.fecha_pedida),
                             penalidad=res.penalidad_esperada(s.fecha_pedida, s.penalidad))
    out['carga_taller'] = (f'plan aprobado #{oc["plan_id"]} del {oc["aprobado_en"][:10]} (proyectos en curso)' if oc
                           else 'histórica supuesta (no hay plan aprobado en Programación)')
    out['modelo'] = dict(entrenado_con=f'{Motor.n_entreno} proyectos SIMULADOS (escenario M{MUNDO_ENTRENAMIENTO})',
                         mtbf=[round(float(x), 1) for x in mtbf_actual(p)], fuente_mtbf=fuente_mtbf(p))
    return out


def mtbf_actual(p):
    """MTBF por máquina: de las paradas registradas en la plataforma si hay al menos 60 días de registro; si no,
    del histórico simulado (supuesto)."""
    filas = p.execute('SELECT maquina, inicio FROM parada WHERE planificada=0').fetchall()
    primero = p.execute('SELECT MIN(inicio) FROM parada').fetchone()[0]
    Motor.get()
    if not primero or (date.today() - date.fromisoformat(primero[:10])).days < 60:
        return Motor.mtbf_sim
    dias = max(int(np.busday_count(primero[:10], str(date.today()), weekmask=WEEKMASK)), 1)
    n = np.array([sum(1 for f in filas if f['maquina'] == m) for m in MAQ_NOMBRE])
    return (dias + 2 * MTBF_DEFECTO) / (n + 2)


def fuente_mtbf(p):
    primero = p.execute('SELECT MIN(inicio) FROM parada').fetchone()[0]
    if not primero or (date.today() - date.fromisoformat(primero[:10])).days < 60:
        return 'supuesto (paradas simuladas) hasta tener 60 días de registro'
    return 'paradas registradas en la plataforma'


# ------------------------------------------------------------------ proyectos en curso (prospectivo)
class NuevoProyecto(BaseModel):
    codigo: str
    cliente: str = ''
    nombre: str
    cotizacion: SolicitudCotizacion
    fecha_comprometida: str
    alpha: float
    prob_cumplir: float
    programa: list
    hh_p50: list


@app.post('/api/proyectos_activos')
def crear_proyecto(d: NuevoProyecto, u=Depends(requiere('cotizador')), p=Depends(plat)):
    c = d.cotizacion
    try:
        cur = p.execute('''INSERT INTO proyecto_activo (codigo, cliente, nombre, tipo, ton, pct_planchas, piezas_por_t, m2_pint_t, montaje,
                           presupuesto, inicio, fecha_comprometida, alpha, prob_cumplir, cotizacion_json, creado_por)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (d.codigo.strip().upper(), d.cliente, d.nombre, c.tipo, c.ton, c.pct_planchas, c.piezas_por_t, c.m2_pint_t,
                         int(c.montaje), c.presupuesto, c.inicio, d.fecha_comprometida, d.alpha, d.prob_cumplir,
                         json.dumps(dict(solicitud=c.model_dump(), programa=d.programa, hh_p50=d.hh_p50)), u['id']))
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Ya existe un proyecto con ese código')
    actividad(p, u, 'proyecto', f'Creó el proyecto {d.codigo} con entrega comprometida el {d.fecha_comprometida}', cur.lastrowid)
    p.commit()
    return {'id': cur.lastrowid}


def _avance(p, r, cot):
    """HH registradas por proceso y avance contra la HH P50 cotizada."""
    if r['cotizacion_json']:
        hh_p50 = np.array(json.loads(r['cotizacion_json'])['hh_p50'], float)
    else:
        q, _ = cot.predictor.cuantiles(_proy(r), TAUS)
        hh_p50 = r['ton'] * cot.rv.loc[tipo_modelo(r['tipo'])].values * q[:, 3]
    reg = np.zeros(N_PROC)
    for f in p.execute('SELECT proceso, SUM(hh) hh FROM tareo WHERE proyecto_id=? GROUP BY proceso', (r['id'],)):
        reg[f['proceso'] - 1] = f['hh']
    return hh_p50, reg, np.clip(reg / np.maximum(hh_p50, 1e-9), 0, 1)


def _proy(r, inicio=None):
    return Proyecto(tipo_modelo(r['tipo']), r['ton'], inicio or r['inicio'], r['presupuesto'] or 100000, r['pct_planchas'] or 0.2,
                    r['piezas_por_t'] or 8, r['m2_pint_t'] or 14, bool(r['montaje']))


@app.get('/api/proyectos_activos')
def lista_activos(u=Depends(usuario_actual), p=Depends(plat)):
    cot = Motor.get()
    out = []
    hoy = str(date.today())
    for r in p.execute('SELECT * FROM proyecto_activo ORDER BY id DESC'):
        hh_p50, reg, av = _avance(p, r, cot)
        piezas = _piezas(p, r['id'])
        out.append(dict(r) | dict(avance=round(100 * float((reg.clip(max=hh_p50)).sum() / hh_p50.sum()), 1),
                                  avance_fisico=resumen_piezas(piezas, hoy)['avance'] if piezas else None,
                                  hh_registradas=round(float(reg.sum())), hh_p50=round(float(hh_p50.sum())), cotizacion_json=None))
    return out


def _piezas(p, pid):
    return [dict(x) for x in p.execute('SELECT * FROM pieza WHERE proyecto_id=? ORDER BY orden_fab, conjunto, n_item', (pid,))]


def _programa(r, cot, hh_p50):
    """Plan P50 por proceso: el guardado al cotizar o, si el proyecto vino del Excel, uno calculado con la cuadrilla típica."""
    cj = json.loads(r['cotizacion_json']) if r['cotizacion_json'] else None
    if cj:
        return [tuple(x) for x in cj['programa']]
    crew = cuadrilla(cot.par_cuad, r['ton'])
    o = programar(hh_p50[None], crew, np.ones((300, 4)), dias_externos(cot.par_ext, r['ton'])[None])
    return [(int(a), int(b)) for a, b in zip(o['ini'][0], o['fin_proc'][0])]


@app.get('/api/proyectos_activos/{pid}')
def detalle_activo(pid: int, u=Depends(usuario_actual), p=Depends(plat)):
    r = p.execute('SELECT * FROM proyecto_activo WHERE id=?', (pid,)).fetchone()
    if not r:
        raise HTTPException(404)
    cot = Motor.get()
    hh_p50, reg, av = _avance(p, r, cot)
    prog = _programa(r, cot, hh_p50)
    tareo = [dict(x) for x in p.execute('''SELECT t.*, u.nombre usuario FROM tareo t LEFT JOIN usuario u ON u.id=t.registrado_por
                                           WHERE proyecto_id=? ORDER BY fecha DESC, id DESC LIMIT 40''', (pid,))]
    cotz = dict(p.execute('SELECT proceso, hh_estimadas FROM cotiz_proceso WHERE proyecto_id=?', (pid,)).fetchall())
    return dict(proyecto=dict(r) | dict(cotizacion_json=None),
                gantt=programa_a_gantt(r['inicio'], prog, 'a', avance=av, hh=hh_p50),
                procesos=[dict(proceso=PROCESOS[j], categoria=CATEGORIA[j], hh_p50=round(float(hh_p50[j])), hh_reg=round(float(reg[j])),
                               hh_cotizador=cotz.get(j + 1), avance=round(100 * float(av[j]), 1)) for j in range(N_PROC)], tareo=tareo)


@app.get('/api/proyectos_activos/{pid}/piezas')
def piezas_proyecto(pid: int, u=Depends(usuario_actual), p=Depends(plat)):
    hoy = str(date.today())
    piezas = _piezas(p, pid)
    from .avance import fraccion_pieza
    for x in piezas:
        x['avance'] = round(100 * fraccion_pieza(x, hoy), 1)
    return dict(resumen=resumen_piezas(piezas, hoy), piezas=piezas, etapas=[dict(col=c, nombre=n, peso=round(100 * w, 1)) for c, n, w, _ in ETAPAS],
                compras=[dict(x) for x in p.execute('SELECT * FROM compra WHERE proyecto_id=? ORDER BY fecha_pedido', (pid,))],
                servicios=[dict(x) for x in p.execute('SELECT * FROM servicio_externo WHERE proyecto_id=? ORDER BY fecha_envio', (pid,))],
                eventos=[dict(x) for x in p.execute('SELECT * FROM evento WHERE proyecto_id=? ORDER BY fecha', (pid,))])


@app.get('/api/proyectos_activos/{pid}/curva_s')
def curva_s_proyecto(pid: int, u=Depends(usuario_actual), p=Depends(plat)):
    r = _activo(p, pid)
    out, _, _, piezas = _curva(p, r)
    out['comprometida'] = r['fecha_comprometida']
    out['fuente_kg'] = 'piezas importadas' if piezas else 'sin piezas: plan con las toneladas del proyecto'
    return out


# ------------------------------------------------------------------ importación del formato único
@app.get('/api/plantilla')
def plantilla(u=Depends(usuario_actual)):
    f = RAIZ / 'entregables' / 'Formato_Unico_Steelser_v1.xlsx'
    if not f.exists():
        raise HTTPException(404, 'Falta la plantilla: ejecute py scripts/generar_formato_unico.py')
    return FileResponse(f, filename=f.name, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.post('/api/importar')
async def importar_excel(request: Request, modo: str = 'validar', archivo: str = 'archivo.xlsx',
                         u=Depends(requiere('jefe_taller', 'cotizador')), p=Depends(plat)):
    contenido = await request.body()
    if not contenido:
        raise HTTPException(422, 'No se recibió ningún archivo')
    if len(contenido) > 15 * 1024 * 1024:
        raise HTTPException(413, 'El archivo supera 15 MB')
    if not contenido[:2] == b'PK':
        raise HTTPException(422, 'El archivo no es un Excel .xlsx')
    try:
        return importar(p, contenido, archivo[:120], u, aplicar=(modo == 'importar'))
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get('/api/importaciones')
def importaciones(u=Depends(usuario_actual), p=Depends(plat)):
    out = []
    for r in p.execute('''SELECT i.id, i.archivo, i.creado_en, i.resumen, u.nombre FROM importacion i LEFT JOIN usuario u ON u.id=i.usuario_id
                          ORDER BY i.id DESC LIMIT 30'''):
        res = json.loads(r['resumen'])
        out.append(dict(id=r['id'], archivo=r['archivo'], creado_en=r['creado_en'], usuario=r['nombre'], filas=res['filas'],
                        cambios=res['cambios'], errores=res['errores'], ots=res['ots']))
    return out


@app.post('/api/proyectos_activos/{pid}/pronostico')
def pronostico(pid: int, u=Depends(usuario_actual), p=Depends(plat)):
    """Re-pronóstico prospectivo: Monte Carlo sobre el trabajo que falta, desde hoy."""
    r = p.execute('SELECT * FROM proyecto_activo WHERE id=?', (pid,)).fetchone()
    if not r:
        raise HTTPException(404)
    cot = Motor.get()
    hh_p50, reg, av = _avance(p, r, cot)
    hoy = str(date.today())
    inicio = max(hoy, r['inicio'])
    res = cot.cotizar(_proy(r, inicio), R=800, alpha=r['alpha'] or 0.8, mtbf=mtbf_actual(p), semilla=pid, restante=1 - av)
    comp = r['fecha_comprometida']
    out = dict(desde=inicio, p50=str(res.fecha_alpha(0.5)), p80=str(res.fecha_alpha(0.8)), p90=str(res.fecha_alpha(0.9)),
               prob_cumplir=res.prob_cumplir(comp), penalidad=res.penalidad_esperada(comp), comprometida=comp,
               avance_global=round(100 * float(av.mean()), 1))
    out['semaforo'] = 'VERDE' if out['prob_cumplir'] >= (r['alpha'] or 0.8) else ('AMBAR' if out['prob_cumplir'] >= 0.5 else 'ROJO')
    piezas = _piezas(p, pid)
    fis = resumen_piezas(piezas, hoy)['avance'] if piezas else None
    p.execute('''INSERT INTO pronostico (proyecto_id, fecha, p50, p80, p90, prob_cumplir, penalidad, avance_hh, avance_fisico, semaforo,
                 usuario_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
              (pid, hoy, out['p50'], out['p80'], out['p90'], out['prob_cumplir'], out['penalidad'],
               round(100 * float(reg.clip(max=hh_p50).sum() / hh_p50.sum()), 1), fis,      # mismo avance HH que el tablero
               out['semaforo'], u['id']))
    actividad(p, u, 'pronostico', f'Re-pronóstico {r["codigo"]}: P(cumplir {comp}) = {out["prob_cumplir"]:.0%} ({out["semaforo"]})', pid)
    p.commit()
    return out


@app.get('/api/proyectos_activos/{pid}/pronosticos')
def historial_pronosticos(pid: int, u=Depends(usuario_actual), p=Depends(plat)):
    """Historial de re-pronósticos: en el piloto mide con cuánta anticipación el sistema avisó un atraso."""
    return [dict(x) for x in p.execute('''SELECT f.*, us.nombre usuario FROM pronostico f LEFT JOIN usuario us ON us.id=f.usuario_id
                                          WHERE proyecto_id=? ORDER BY f.id''', (pid,))]


def _curva(p, r):
    cot = Motor.get()
    hh_p50, _, _ = _avance(p, r, cot)
    piezas = _piezas(p, r['id'])
    kg_plan = sum(x['peso_total'] or 0 for x in piezas) or r['ton'] * 1000
    tareo = [dict(x) for x in p.execute('SELECT fecha, hh FROM tareo WHERE proyecto_id=?', (r['id'],))]
    prog = _programa(r, cot, hh_p50)
    return curva_s(r['inicio'], prog, hh_p50, piezas, tareo, str(date.today()), kg_plan), prog, hh_p50, piezas


def _activo(p, pid):
    r = p.execute('SELECT * FROM proyecto_activo WHERE id=?', (pid,)).fetchone()
    if not r:
        raise HTTPException(404)
    return r


@app.get('/api/proyectos_activos/{pid}/semanas')
def semanas_proyecto(pid: int, u=Depends(usuario_actual), p=Depends(plat)):
    c, *_ = _curva(p, _activo(p, pid))
    return dict(semanas=semanas(c), hoy=c['hoy'], tiene_piezas=c['spi_kg'] is not None or any(v for v in c['real_kg'] if v))


TIPOS_BANDEJA = ('RFI', 'NO_CONFORMIDAD', 'CAMBIO_ALCANCE', 'BLOQUEO')


@app.get('/api/proyectos_activos/{pid}/reporte')
def reporte_semanal(pid: int, semana: str | None = None, u=Depends(usuario_actual), p=Depends(plat)):
    """Actualización semanal del proyecto (se imprime como PDF desde el navegador)."""
    r = _activo(p, pid)
    hoy = date.today()
    lunes = date.fromisoformat(semana) if semana else hoy
    lunes -= timedelta(days=lunes.weekday())
    sab = lunes + timedelta(days=5)
    l1, s1 = str(lunes), str(sab)
    c, prog, hh_p50, piezas = _curva(p, r)
    sem = semanas(c)
    fila = next((s for s in sem if s['inicio'] == l1), None)
    logros = []
    for col, nombre, w, _ in ETAPAS:
        ps = [x for x in piezas if x.get(col) and l1 <= str(x[col])[:10] <= s1]
        if ps:
            logros.append(dict(etapa=nombre, piezas=len(ps), kg=round(sum(x['peso_total'] or 0 for x in ps), 1),
                               marcas=sorted({x['conjunto'] for x in ps if x['conjunto']})[:12]))
    hh_sem = [dict(proceso=PROCESOS[x['proceso'] - 1], hh=round(x['hh'], 1), dias=x['dias'], personas=round(x['personas'], 1))
              for x in p.execute('''SELECT proceso, SUM(hh) hh, COUNT(DISTINCT fecha) dias, AVG(n_personas) personas FROM tareo
                                    WHERE proyecto_id=? AND fecha BETWEEN ? AND ? GROUP BY proceso ORDER BY proceso''', (pid, l1, s1))]
    # procesos que el plan P50 tiene activos la semana siguiente
    base = np.datetime64(r['inicio'], 'D')
    k0 = int(np.busday_count(np.busday_offset(base, 0, roll='forward', weekmask=WEEKMASK), np.datetime64(sab + timedelta(days=2), 'D'), weekmask=WEEKMASK))
    proxima = [dict(proceso=PROCESOS[j], inicio=dia(r['inicio'], a), fin=dia(r['inicio'], max(b - 1, a)), hh_p50=round(float(hh_p50[j])))
               for j, (a, b) in enumerate(prog) if a is not None and b is not None and a < k0 + 6 and b > k0]
    incid = [dict(x) for x in p.execute(f'''SELECT t.id, t.titulo, t.tipo, t.prioridad, t.estado, t.fecha_limite, t.imputable, t.dias_impacto,
                                            t.creado_en, us.nombre responsable FROM tarea t LEFT JOIN usuario us ON us.id=t.responsable_id
                                            WHERE t.proyecto_id=? AND t.estado!='HECHO' AND t.tipo IN {TIPOS_BANDEJA}
                                            ORDER BY t.prioridad, t.id''', (pid,))]
    eventos = [dict(x) for x in p.execute('SELECT * FROM evento WHERE proyecto_id=? AND fecha BETWEEN ? AND ?', (pid, l1, s1))]
    paradas = [dict(x) for x in p.execute('''SELECT maquina, causa, planificada, ROUND((julianday(fin)-julianday(inicio))*24, 1) horas FROM parada
                                             WHERE substr(inicio,1,10) BETWEEN ? AND ?''', (l1, s1))]
    compras = [dict(x) for x in p.execute('''SELECT n_oc, material, kg, fecha_prometida FROM compra WHERE proyecto_id=? AND fecha_recepcion IS NULL
                                             ORDER BY fecha_prometida''', (pid,))]
    servicios = [dict(x) for x in p.execute('''SELECT servicio, proveedor, fecha_envio FROM servicio_externo WHERE proyecto_id=?
                                               AND fecha_retorno IS NULL''', (pid,))]
    pron = p.execute('SELECT * FROM pronostico WHERE proyecto_id=? AND fecha<=? ORDER BY id DESC LIMIT 1', (pid, s1)).fetchone()
    _, reg, _ = _avance(p, r, Motor.get())
    return dict(proyecto=dict(r) | dict(cotizacion_json=None), semana=dict(inicio=l1, fin=s1, n=fila['n'] if fila else None),
                fila=fila, semanas=sem, avance_hh=round(100 * float(reg.clip(max=hh_p50).sum() / hh_p50.sum()), 1),
                avance_fisico=resumen_piezas(piezas, s1)['avance'] if piezas else None, logros=logros, hh_semana=hh_sem,
                proxima=proxima, incidencias=incid, eventos=eventos, paradas=paradas, compras_pendientes=compras,
                servicios_en_proveedor=servicios, pronostico=dict(pron) if pron else None, generado=str(datetime.now())[:16],
                generado_por=u['nombre'])


# ------------------------------------------------------------------ edición de piezas en la interfaz
class CambioEtapa(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=2000)
    etapa: str
    fecha: str | None = None        # None = borrar la fecha (corrección)


@app.post('/api/piezas/etapa')
def marcar_etapa(d: CambioEtapa, u=Depends(requiere('jefe_taller', 'supervisor', 'calidad')), p=Depends(plat)):
    cols = {c: n for c, n, *_ in ETAPAS}
    if d.etapa not in cols:
        raise HTTPException(422, 'Etapa no válida')
    if d.etapa == 'f_liberacion' and u['rol'] not in ('calidad', 'jefe_taller', 'gerencia'):
        raise HTTPException(403, 'La liberación la registra Calidad o el jefe de taller')
    if d.fecha:
        try:
            date.fromisoformat(d.fecha)
        except ValueError:
            raise HTTPException(422, 'Fecha no válida')
        if d.fecha > str(date.today()):
            raise HTTPException(422, 'La fecha no puede ser futura')
    hechos, errores, proyectos = 0, [], set()
    orden = [c for c, *_ in ETAPAS[:4]]
    previa = orden[orden.index(d.etapa) - 1] if d.etapa in orden[1:] else None
    for x in p.execute(f'SELECT * FROM pieza WHERE id IN ({",".join("?" * len(d.ids))})', d.ids).fetchall():
        x = dict(x)
        nueva = dict(x) | {d.etapa: d.fecha}
        # desde la interfaz se exige la etapa previa del fierro negro (el Excel histórico puede venir con huecos)
        err = f'falta {cols[previa].lower()}' if d.fecha and previa and not x[previa] else error_orden_etapas(nueva)
        if err:
            errores.append(dict(id=x['id'], conjunto=x['conjunto'], msg=err))
            continue
        if x[d.etapa] == d.fecha:
            continue
        p.execute(f'UPDATE pieza SET {d.etapa}=? WHERE id=?', (d.fecha, x['id']))
        p.execute('INSERT INTO pieza_cambio (pieza_id, etapa, antes, despues, usuario_id) VALUES (?,?,?,?,?)',
                  (x['id'], d.etapa, x[d.etapa], d.fecha, u['id']))
        hechos += 1
        proyectos.add(x['proyecto_id'])
    for pid in proyectos:
        actividad(p, u, 'pieza', f'{"Marcó" if d.fecha else "Quitó"} {cols[d.etapa].lower()} en {hechos} piezas', pid)
    p.commit()
    return dict(actualizadas=hechos, errores=errores)


# ------------------------------------------------------------------ bandeja de RFI y no conformidades
@app.get('/api/bandeja')
def bandeja(u=Depends(usuario_actual), p=Depends(plat)):
    hoy = str(date.today())
    filas = [dict(x) for x in p.execute(f'''SELECT t.*, us.nombre responsable, us.color color, pa.codigo proyecto,
                                            MAX(0, CAST(julianday(COALESCE(t.fecha_cierre, date('now','localtime'))) - julianday(date(t.creado_en,'localtime')) AS INTEGER)) dias_abierta,
                                            (SELECT COUNT(*) FROM comentario c WHERE c.tarea_id=t.id) n_comentarios
                                            FROM tarea t LEFT JOIN usuario us ON us.id=t.responsable_id
                                            LEFT JOIN proyecto_activo pa ON pa.id=t.proyecto_id
                                            WHERE t.tipo IN {TIPOS_BANDEJA} ORDER BY t.estado='HECHO', t.prioridad, t.id DESC''')]
    for x in filas:
        x['vencida'] = bool(x['estado'] != 'HECHO' and x['fecha_limite'] and x['fecha_limite'] < hoy)
    abiertas = [x for x in filas if x['estado'] != 'HECHO']
    cerradas = [x for x in filas if x['estado'] == 'HECHO']
    return dict(filas=filas, resumen=dict(
        abiertas=len(abiertas), vencidas=sum(x['vencida'] for x in abiertas),
        dias_cierre=round(float(np.mean([x['dias_abierta'] for x in cerradas])), 1) if cerradas else None,
        dias_cliente=sum(x['dias_impacto'] or 0 for x in filas if x['imputable'] == 'Cliente'),
        dias_steelser=sum(x['dias_impacto'] or 0 for x in filas if x['imputable'] == 'Steelser'),
        por_tipo={t: sum(1 for x in abiertas if x['tipo'] == t) for t in TIPOS_BANDEJA}))


# ------------------------------------------------------------------ buscador global (Ctrl+K)
@app.get('/api/buscar')
def buscar(q: str = '', u=Depends(usuario_actual), p=Depends(plat), h=Depends(hist)):
    q = q.strip()
    if len(q) < 2:
        return []
    like = f'%{q}%'
    out = [dict(tipo='Proyecto en curso', titulo=f'{x["codigo"]} · {x["nombre"]}', detalle=x['cliente'] or '', ruta=f'#/proyecto/a/{x["id"]}')
           for x in p.execute('SELECT id, codigo, nombre, cliente FROM proyecto_activo WHERE codigo LIKE ? OR nombre LIKE ? OR cliente LIKE ? LIMIT 8',
                              (like, like, like))]
    out += [dict(tipo='Tarea', titulo=f'STL-{x["id"]} · {x["titulo"]}', detalle=x['tipo'].replace('_', ' ').lower(), ruta=f'#/tareas?t={x["id"]}')
            for x in p.execute('SELECT id, titulo, tipo FROM tarea WHERE titulo LIKE ? OR CAST(id AS TEXT)=? ORDER BY id DESC LIMIT 8',
                               (like, q.upper().removeprefix('STL-')))]
    out += [dict(tipo='Pieza', titulo=f'{x["conjunto"]} · {x["tipo_elemento"]}', detalle=f'{x["codigo"]} · {x["perfil"] or ""}',
                 ruta=f'#/proyecto/a/{x["proyecto_id"]}?tab=pie&q={x["conjunto"]}')
            for x in p.execute('''SELECT pz.proyecto_id, pz.conjunto, pz.tipo_elemento, pz.perfil, pa.codigo FROM pieza pz
                                  JOIN proyecto_activo pa ON pa.id=pz.proyecto_id WHERE pz.conjunto LIKE ? OR pz.perfil LIKE ? LIMIT 8''', (like, like))]
    out += [dict(tipo='Histórico', titulo=f'{x["cliente"]} · {x["nombre"]}', detalle=f'{x["anio"]} · {"retraso " + str(x["dias_retraso"]) + " d" if x["dias_retraso"] > 0 else "cumplió"}',
                 ruta=f'#/proyecto/h/{x["id"]}')
            for x in h.execute('''SELECT id, cliente, nombre, anio, dias_retraso FROM proyecto WHERE n_registro IS NOT NULL
                                  AND (cliente LIKE ? OR nombre LIKE ?) LIMIT 8''', (like, like))]
    return out


# ------------------------------------------------------------------ registro de planta
class Tareo(BaseModel):
    fecha: str
    proyecto_id: int
    proceso: int = Field(ge=1, le=13)
    contratista: str | None = None
    n_personas: int = Field(ge=1, le=60)
    horas_persona: float = Field(gt=0, le=12)
    kg_avanzados: float | None = None
    observacion: str | None = None


@app.get('/api/tareo')
def ver_tareo(u=Depends(usuario_actual), p=Depends(plat)):
    return [dict(r) for r in p.execute('''SELECT t.*, pa.codigo, u.nombre usuario FROM tareo t JOIN proyecto_activo pa ON pa.id=t.proyecto_id
                                          LEFT JOIN usuario u ON u.id=t.registrado_por ORDER BY t.fecha DESC, t.id DESC LIMIT 60''')]


@app.post('/api/tareo')
def registrar_tareo(t: Tareo, u=Depends(requiere('jefe_taller', 'supervisor')), p=Depends(plat)):
    if t.fecha > str(date.today()):
        raise HTTPException(422, 'La fecha no puede ser futura')
    p.execute('''INSERT INTO tareo (fecha, proyecto_id, proceso, contratista, n_personas, horas_persona, kg_avanzados, observacion,
                 registrado_por) VALUES (?,?,?,?,?,?,?,?,?)''',
              (t.fecha, t.proyecto_id, t.proceso, t.contratista, t.n_personas, t.horas_persona, t.kg_avanzados, t.observacion, u['id']))
    actividad(p, u, 'tareo', f'Registró {t.n_personas * t.horas_persona:.0f} HH en {PROCESOS[t.proceso - 1]}', t.proyecto_id)
    p.commit()
    return {'ok': True}


class Parada(BaseModel):
    maquina: str
    inicio: str
    fin: str
    planificada: bool
    causa: str
    proyecto_id: int | None = None
    observacion: str | None = None


@app.get('/api/paradas')
def ver_paradas(u=Depends(usuario_actual), p=Depends(plat)):
    return [dict(r) for r in p.execute('''SELECT pa.*, u.nombre usuario, ROUND((julianday(fin)-julianday(inicio))*24, 1) horas
                                          FROM parada pa LEFT JOIN usuario u ON u.id=pa.registrado_por ORDER BY inicio DESC LIMIT 60''')]


@app.post('/api/paradas')
def registrar_parada(d: Parada, u=Depends(requiere('jefe_taller', 'supervisor', 'calidad', 'mantenimiento')), p=Depends(plat)):
    if d.maquina not in MAQ_NOMBRE or d.causa not in CAUSAS:
        raise HTTPException(422, 'Máquina o causa no válida')
    if d.fin <= d.inicio:
        raise HTTPException(422, 'El fin debe ser posterior al inicio')
    if d.fin.replace('T', ' ')[:16] > (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M'):
        raise HTTPException(422, 'El fin no puede ser futuro: si la máquina sigue parada, usa «Reportar falla» en Mantenimiento')
    p.execute('INSERT INTO parada (maquina, inicio, fin, planificada, causa, proyecto_id, observacion, registrado_por) VALUES (?,?,?,?,?,?,?,?)',
              (d.maquina, d.inicio, d.fin, int(d.planificada), d.causa, d.proyecto_id, d.observacion, u['id']))
    actividad(p, u, 'parada', f'Registró parada de {d.maquina}: {d.causa}', d.proyecto_id)
    p.commit()
    return {'ok': True}


# ------------------------------------------------------------------ tareas (estilo Linear)
class NuevaTarea(BaseModel):
    titulo: str = Field(min_length=3, max_length=200)
    descripcion: str | None = None
    proyecto_id: int | None = None
    proceso: int | None = None
    prioridad: int = Field(3, ge=1, le=4)
    tipo: str = 'TAREA'
    responsable_id: int | None = None
    fecha_limite: str | None = None
    estado: str = 'POR_HACER'
    imputable: str | None = None        # Cliente / Steelser / Proveedor / Otro (RFI, NC, cambios de alcance)
    dias_impacto: float | None = Field(None, ge=0, le=365)
    conjunto: str | None = None         # marca de la pieza afectada


class CambioTarea(BaseModel):
    estado: str | None = None
    prioridad: int | None = None
    responsable_id: int | None = None
    fecha_limite: str | None = None
    imputable: str | None = None
    dias_impacto: float | None = Field(None, ge=0, le=365)
    conjunto: str | None = None


@app.get('/api/tareas')
def tareas(proyecto_id: int | None = None, u=Depends(usuario_actual), p=Depends(plat)):
    q = '''SELECT t.*, u.nombre responsable, u.color color, pa.codigo proyecto,
                  (SELECT COUNT(*) FROM comentario c WHERE c.tarea_id=t.id) n_comentarios
           FROM tarea t LEFT JOIN usuario u ON u.id=t.responsable_id LEFT JOIN proyecto_activo pa ON pa.id=t.proyecto_id'''
    args = ()
    if proyecto_id:
        q += ' WHERE t.proyecto_id=?'
        args = (proyecto_id,)
    return [dict(r) for r in p.execute(q + ' ORDER BY t.prioridad, t.id DESC', args)]


@app.post('/api/tareas')
def crear_tarea(t: NuevaTarea, u=Depends(usuario_actual), p=Depends(plat)):
    if t.imputable and t.imputable not in IMPUTABLE:
        raise HTTPException(422, 'Imputable no válido')
    try:
        cur = p.execute('''INSERT INTO tarea (titulo, descripcion, proyecto_id, proceso, prioridad, tipo, responsable_id, fecha_limite,
                           estado, creado_por, imputable, dias_impacto, conjunto, fecha_cierre) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (t.titulo, t.descripcion, t.proyecto_id, t.proceso, t.prioridad, t.tipo, t.responsable_id, t.fecha_limite,
                         t.estado, u['id'], t.imputable, t.dias_impacto, t.conjunto, str(date.today()) if t.estado == 'HECHO' else None))
    except sqlite3.IntegrityError:
        raise HTTPException(422, 'Valor no válido')
    actividad(p, u, 'tarea', f'Creó STL-{cur.lastrowid}: {t.titulo}', t.proyecto_id, cur.lastrowid)
    p.commit()
    return {'id': cur.lastrowid}


@app.patch('/api/tareas/{tid}')
def cambiar_tarea(tid: int, c: CambioTarea, u=Depends(usuario_actual), p=Depends(plat)):
    t = p.execute('SELECT * FROM tarea WHERE id=?', (tid,)).fetchone()
    if not t:
        raise HTTPException(404)
    cambios = {k: v for k, v in c.model_dump().items() if v is not None}
    if not cambios:
        return {'ok': True}
    if cambios.get('imputable') and cambios['imputable'] not in IMPUTABLE:
        raise HTTPException(422, 'Imputable no válido')
    if 'estado' in cambios:
        cambios['fecha_cierre'] = str(date.today()) if cambios['estado'] == 'HECHO' else None
    sets = ', '.join(f'{k}=?' for k in cambios) + ', actualizado_en=CURRENT_TIMESTAMP'
    try:
        p.execute(f'UPDATE tarea SET {sets} WHERE id=?', (*cambios.values(), tid))
    except sqlite3.IntegrityError:
        raise HTTPException(422, 'Valor no válido')
    if 'estado' in cambios:
        actividad(p, u, 'tarea', f'Movió STL-{tid} a {cambios["estado"].replace("_", " ").title()}', t['proyecto_id'], tid)
    p.commit()
    return {'ok': True}


@app.get('/api/tareas/{tid}/comentarios')
def comentarios(tid: int, u=Depends(usuario_actual), p=Depends(plat)):
    return [dict(r) for r in p.execute('''SELECT c.*, u.nombre, u.color FROM comentario c LEFT JOIN usuario u ON u.id=c.usuario_id
                                          WHERE tarea_id=? ORDER BY c.id''', (tid,))]


class Comentario(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)


@app.post('/api/tareas/{tid}/comentarios')
def comentar(tid: int, c: Comentario, u=Depends(usuario_actual), p=Depends(plat)):
    p.execute('INSERT INTO comentario (tarea_id, usuario_id, texto) VALUES (?,?,?)', (tid, u['id'], c.texto))
    actividad(p, u, 'comentario', f'Comentó en STL-{tid}', None, tid)
    p.commit()
    return {'ok': True}


# ------------------------------------------------------------------ usuarios
class NuevoUsuario(BaseModel):
    usuario: str = Field(min_length=3, max_length=30, pattern=r'^[a-z0-9._-]+$')
    nombre: str
    rol: str
    area: str = ''
    clave: str = Field(min_length=8)


@app.get('/api/usuarios')
def usuarios(u=Depends(requiere('gerencia')), p=Depends(plat)):
    return [dict(r) for r in p.execute('SELECT id, usuario, nombre, rol, area, color, activo, creado_en FROM usuario')]


@app.post('/api/usuarios')
def crear_usr(d: NuevoUsuario, u=Depends(requiere('gerencia')), p=Depends(plat)):
    if d.rol not in dbp.ROLES:
        raise HTTPException(422, 'Rol no válido')
    try:
        dbp.crear_usuario(p, d.usuario, d.nombre, d.rol, d.area, d.clave)
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'El usuario ya existe')
    actividad(p, u, 'usuario', f'Creó la cuenta {d.usuario} ({d.rol})')
    p.commit()
    return {'ok': True}


# ------------------------------------------------------------------ planta 3D retrospectiva (datos simulados)
from . import planta as _planta                                        # noqa: E402
_planta.registrar(app, hist, usuario_actual, requiere, Motor, HIST)
from . import gemelo as _gemelo                                        # noqa: E402
_gemelo.registrar(app, hist, usuario_actual)


# ------------------------------------------------------------------ mantenimiento de máquinas (v3)
PROCESO_MAQUINA = dict(zip(MAQUINAS_CRP, MAQ_NOMBRE))       # proceso 0-based que usa cada máquina de habilitado


def _ops_maquinas(p):
    """Operaciones del plan P50 de los proyectos en curso sobre las 4 máquinas (para el Gantt de máquinas)."""
    cot = Motor.get()
    out = []
    for r in p.execute("SELECT * FROM proyecto_activo WHERE estado IN ('EN_CURSO','PAUSADO')").fetchall():
        hh_p50, _, av = _avance(p, r, cot)
        for j, (a, b) in enumerate(_programa(r, cot, hh_p50)):
            if j not in PROCESO_MAQUINA or a is None or b is None or hh_p50[j] < 0.5:
                continue
            out.append(dict(maquina=PROCESO_MAQUINA[j], inicio=f'{dia(r["inicio"], a)} 08:00', fin=f'{dia(r["inicio"], max(b - 1, a))} 16:00',
                            titulo=f'{r["codigo"]} · {PROCESOS[j]}', detalle=f'{round(float(hh_p50[j]))} HH P50 · avance {round(100 * float(av[j]))} %',
                            proyecto=r['codigo'], ref=f'proyecto:{r["id"]}', avance=round(100 * float(av[j]))))
    return out


from . import mantenimiento as _mant                                   # noqa: E402
_mant.registrar(app, plat, usuario_actual, requiere, actividad, CAUSAS, _ops_maquinas)


# ------------------------------------------------------------------ programación automática de la cartera (v3.1)
def _cartera(p):
    """Proyectos en curso como entrada del programador: lo que falta de cada proceso y su fecha comprometida."""
    from dss.programador import ProyectoPlan
    cot = Motor.get()
    out = []
    for r in p.execute("SELECT * FROM proyecto_activo WHERE estado='EN_CURSO' ORDER BY id").fetchall():
        _, _, av = _avance(p, r, cot)
        out.append(ProyectoPlan(id=r['id'], codigo=r['codigo'], proy=_proy(r), compromiso=r['fecha_comprometida'], avance0=np.asarray(av, float),
                                alpha=r['alpha'] or 0.8))
    return out


from . import programacion as _prog                                   # noqa: E402
_ocupacion = _prog.registrar(app, plat, usuario_actual, requiere, actividad, Motor, _cartera, mtbf_actual, MAQ_NOMBRE)
