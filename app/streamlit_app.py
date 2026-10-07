"""Cotizador de fechas de entrega (prototipo). Ejecutar:  py -m streamlit run app/streamlit_app.py"""
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dss.c2_modelo import dataset, PhiQRF                                  # noqa: E402
from dss.c3_montecarlo import Cotizador, Proyecto, alpha_optimo, P_PENALIDAD  # noqa: E402
from dss.crp_engine import programar, WEEKMASK                              # noqa: E402
from dss.datos import conectar, TIPOS, mtbf_estimado, cuadrilla, dias_externos  # noqa: E402
from dss.simulador import MAQ_NOMBRE                                        # noqa: E402

warnings.filterwarnings('ignore')
PROCESOS = ['Ingeniería', 'Compra de material', 'Habilitado: sierra cinta', 'Habilitado: cizalla-punzonadora',
            'Habilitado: mesa CNC', 'Roscado', 'Doblez (externo)', 'Armado', 'Soldeo', 'Limpieza',
            'Despacho a pintura', 'Granallado y pintura (externo)', 'Despacho a obra']

st.set_page_config(page_title='Cotizador de plazos', layout='wide')


@st.cache_resource
def cargar(mundo, corte):
    con = conectar()
    df = dataset(con, mundo)
    tr = df[df.fin < corte]
    modelo = PhiQRF().fit(tr)
    cen = dict(con.execute('SELECT nombre, id FROM centro_trabajo'))
    mtbf = mtbf_estimado(con, mundo, [cen[n] for n in MAQ_NOMBRE], corte)
    return con, Cotizador(con, modelo), modelo, mtbf, tr.pid.nunique()


DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']


def fmt(d):
    t = pd.Timestamp(d)
    return f'{t:%d/%m/%Y} ({DIAS[t.dayofweek]})'


st.title('Cotizador de plazos de entrega')
st.warning('**DATOS SIMULADOS.** El modelo está entrenado con datos simulados anclados a 25 proyectos reales de '
           'Steelser (2021-2026). Las horas reales por proceso aún no se han recolectado. Úsalo para probar el flujo, no para ofertar.')

con = conectar()
mundos = dict(con.execute('SELECT nombre, id FROM sim_mundo'))

with st.sidebar:
    st.header('Proyecto nuevo')
    tipo = st.selectbox('Tipo de estructura', TIPOS, index=1)
    ton = st.number_input('Toneladas (metrado)', 5.0, 400.0, 47.0, 1.0)
    pct_pl = st.slider('% de planchas', 0, 60, 17) / 100
    pz_t = st.number_input('Piezas por tonelada', 1.0, 40.0, 8.0, 0.5)
    m2_t = st.number_input('m² de pintura por tonelada', 3.0, 40.0, 14.0, 1.0)
    montaje = st.checkbox('Incluye montaje', False)
    presupuesto = st.number_input('Presupuesto del contrato (USD)', 5_000.0, 5_000_000.0, 150_000.0, 5_000.0)
    inicio = st.date_input('Día 1 (planos aprobados + OC)', date(2026, 11, 2))
    pedido = st.date_input('Fecha que pide el cliente (opcional)', inicio + timedelta(days=75))
    st.header('Riesgo y competitividad')
    pen = st.number_input('Penalidad por día (% del presupuesto)', 0.1, 5.0, P_PENALIDAD * 100, 0.1) / 100
    pierde = st.number_input('Prob. de perder la oferta por cada día de plazo de más (puntos %)', 0.0, 5.0, 0.5, 0.1) / 100
    margen = st.number_input('Margen de utilidad', 0.01, 0.5, 0.16, 0.01)
    a_opt = alpha_optimo(pen, pierde, margen)
    auto = st.checkbox(f'Usar confianza óptima (α* = {a_opt:.2f})', True)
    alpha = a_opt if auto else st.slider('Confianza de cumplir (α)', 0.5, 0.99, 0.80, 0.01)
    carga_extra = st.slider('Carga adicional de máquinas por otros proyectos (%)', 0, 80, 0) / 100
    R = st.select_slider('Réplicas de Monte Carlo', [200, 500, 1000, 2000], 1000)
    st.header('Datos (simulados)')
    nombre_mundo = st.selectbox('Escenario', list(mundos), index=1)

corte = str(inicio) if inicio < date(2027, 1, 1) else '2027-01-01'
_, cot, modelo, mtbf, n_proy = cargar(mundos[nombre_mundo], corte)
proy = Proyecto(tipo, ton, str(inicio), presupuesto, pct_pl, pz_t, m2_t, montaje)

if st.sidebar.button('Cotizar', type='primary', use_container_width=True) or 'res' not in st.session_state \
        or st.session_state.get('clave') != (tipo, ton, pct_pl, pz_t, m2_t, montaje, presupuesto, str(inicio), R, nombre_mundo, carga_extra):
    with st.spinner(f'Simulando {R} futuros del taller...'):
        st.session_state['res'] = cot.cotizar(proy, R=R, alpha=alpha, mtbf=mtbf, semilla=7, carga_extra=carga_extra)
        st.session_state['clave'] = (tipo, ton, pct_pl, pz_t, m2_t, montaje, presupuesto, str(inicio), R, nombre_mundo, carga_extra)
res = st.session_state['res']

# --- línea base: lo que da hoy el ratio (sin paradas, sin carga, sin incertidumbre)
hh_ratio = ton * cot.rv.loc[tipo].values
o = programar(hh_ratio[None], cuadrilla(cot.par_cuad, ton), np.ones((300, 4)), dias_externos(cot.par_ext, ton)[None])
base = np.busday_offset(np.datetime64(str(inicio)), int(o['fin'][0]) - 1, roll='forward', weekmask=WEEKMASK)

f_rec = res.fecha_alpha(alpha)
curva = pd.DataFrame(res.curva(pen), columns=['fecha', 'plazo', 'prob', 'pen'])
c_o = pierde * margen * presupuesto
curva['costo'] = curva.pen + c_o * (curva.plazo - curva.plazo.min())
f_min = curva.loc[curva.costo.idxmin(), 'fecha']

c = st.columns(4)
c[0].metric('Fecha recomendada', fmt(f_rec), f'plazo {res.plazo_calendario(f_rec)} días calendario')
c[1].metric('Probabilidad de cumplirla', f'{res.prob_cumplir(f_rec):.0%}', f'confianza elegida {alpha:.0%}')
c[2].metric('Penalidad esperada', f'USD {res.penalidad_esperada(f_rec, pen):,.0f}',
            f'{100 * res.penalidad_esperada(f_rec, pen) / presupuesto:.2f} % del presupuesto', delta_color='off')
c[3].metric('Fecha con el método actual (ratio)', fmt(base),
            f'{res.prob_cumplir(base):.0%} de probabilidad de cumplirla', delta_color='off')

semaforo = res.prob_cumplir(pedido)
if semaforo >= alpha:
    st.success(f'**Verde.** El cliente pide el {fmt(pedido)}: probabilidad de cumplir {semaforo:.0%}.')
elif semaforo >= 0.5:
    st.warning(f'**Ámbar.** Para el {fmt(pedido)} la probabilidad de cumplir es {semaforo:.0%} y la penalidad esperada '
               f'USD {res.penalidad_esperada(pedido, pen):,.0f}. Ofertar el {fmt(f_rec)} es más seguro.')
else:
    st.error(f'**Rojo.** Para el {fmt(pedido)} la probabilidad de cumplir es solo {semaforo:.0%} '
             f'(penalidad esperada USD {res.penalidad_esperada(pedido, pen):,.0f}). No ofertar ese plazo sin cambiar el plan.')

t1, t2, t3 = st.tabs(['Plazo vs. riesgo', 'Horas por proceso', 'Cómo se calculó'])
with t1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curva.fecha, y=curva.prob * 100, name='Probabilidad de cumplir (%)', line=dict(width=3)))
    fig.add_trace(go.Scatter(x=curva.fecha, y=curva.pen, name='Penalidad esperada (USD)', yaxis='y2', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=curva.fecha, y=curva.costo, name='Costo esperado total (penalidad + plazo largo)', yaxis='y2'))
    for x, t in [(f_rec, 'recomendada'), (base, 'método actual'), (np.datetime64(pedido, 'D'), 'pedida')]:
        fig.add_vline(x=pd.Timestamp(x).timestamp() * 1000, line_dash='dash', annotation_text=t)
    fig.update_layout(height=420, yaxis=dict(title='Probabilidad (%)', range=[0, 102]),
                      yaxis2=dict(title='USD', overlaying='y', side='right'), legend=dict(orientation='h', y=-0.2),
                      margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f'La fecha de menor costo esperado total (penalidad + perder competitividad por plazo largo) es el {fmt(f_min)}. '
               'Con la penalidad de 1 % por día sin tope, conviene cotizar con probabilidad alta; el costo de plazo largo '
               '(prob. de perder la oferta × margen) es un supuesto hasta tener las cotizaciones ganadas y perdidas.')
    h = pd.Series(res.fechas.astype('datetime64[ns]')).dt.date.value_counts().sort_index()
    st.bar_chart(h, height=200)
with t2:
    q = pd.DataFrame({'Proceso': PROCESOS, 'HH ratio actual': hh_ratio.round(0)})
    for p in (10, 50, 80, 90):
        q[f'HH P{p}'] = np.percentile(res.hh, p, axis=0).round(0)
    q['P50 / ratio'] = (q['HH P50'] / q['HH ratio actual'].replace(0, np.nan)).round(2)
    st.dataframe(q, use_container_width=True, hide_index=True)
    st.caption(f'Total ratio actual: {hh_ratio.sum():,.0f} HH · P50: {np.median(res.hh.sum(1)):,.0f} HH · '
               f'P90: {np.percentile(res.hh.sum(1), 90):,.0f} HH.')
with t3:
    st.markdown(f'''
1. **Horas por proceso (C2):** Quantile Regression Forest entrenado con **{n_proy} proyectos terminados** antes del {corte} (escenario *{nombre_mundo}*), corregido con calibración conformal. Predice cuánto se desvía el ratio actual (φ) en cada proceso.
2. **Paradas de las 4 máquinas:** fallas simuladas con tiempo entre fallas estimado de las paradas registradas ({', '.join(f'{m.split()[0]} {x:.0f} d' for m, x in zip(MAQ_NOMBRE, mtbf))}).
3. **Carga del taller:** proyectos ya en curso que ocupan las máquinas (+ {carga_extra:.0%} adicional que indiques).
4. **Monte Carlo (C3):** {R} réplicas; cada una programa los 13 procesos día a día (lunes a sábado) con solapes y cuadrillas.
5. **Fecha recomendada:** el cuantil {alpha:.0%} de las fechas de fin. La confianza óptima α* = c_u / (c_u + c_o) balancea la penalidad ({pen:.1%} por día) contra el costo de ofertar un plazo largo.
''')
