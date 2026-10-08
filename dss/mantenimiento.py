"""Indicadores de mantenimiento (TPM) de las máquinas y vencimiento del plan preventivo.

- Dₖ = (TPₖ − T paradasₖ) / TPₖ (Ec. 10 de la tesis, criterio de Nakajima). TPₖ = días laborables (lunes a sábado)
  × horas por turno × turnos de la máquina en el periodo. Las paradas se recortan al periodo; se asume que ocurren
  dentro del turno (es como se registran en planta).
- MTBF = tiempo operativo / n.º de fallas; MTTR = horas de reparación / n.º de fallas. "Falla" = parada no planificada.
- Preventivo por frecuencia en días o en horas de uso; las horas se convierten a días laborables con las horas del
  turno (supuesto: la máquina trabaja el turno completo; se reemplaza cuando haya horómetro).

Funciones puras (sin BD) para poder probarlas; la plataforma las llama con lo registrado en plataforma.db.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta

import numpy as np

from .crp_engine import HORAS_TURNO, WEEKMASK

META_DK = 0.90


def _dt(x):
    x = str(x).replace('T', ' ')
    return datetime.fromisoformat(x if len(x) > 10 else x + ' 00:00')


def dias_laborables(desde, hasta):
    """Días laborables en [desde, hasta) (fechas ISO)."""
    return int(np.busday_count(str(desde)[:10], str(hasta)[:10], weekmask=WEEKMASK))


def horas_parada(p, desde, hasta):
    """Horas de la parada p (dict con inicio, fin) dentro de [desde, hasta)."""
    a, b = max(_dt(p['inicio']), _dt(desde)), min(_dt(p['fin']), _dt(hasta))
    return max(0.0, (b - a).total_seconds() / 3600)


def indicadores(paradas, desde, hasta, horas_turno=HORAS_TURNO, turnos=1):
    """Indicadores de una máquina en [desde, hasta). paradas: dicts con inicio, fin, planificada, causa."""
    tp = dias_laborables(desde, hasta) * horas_turno * turnos
    h_fallas = h_plan = 0.0
    n_fallas = n_plan = 0
    causas = defaultdict(float)
    for p in paradas:
        h = horas_parada(p, desde, hasta)
        if h <= 0:
            continue
        causas[p.get('causa') or 'Otro'] += h
        if p.get('planificada'):
            h_plan += h
            n_plan += 1
        else:
            h_fallas += h
            n_fallas += 1
    h_tot = min(h_fallas + h_plan, tp)
    operativo = tp - h_tot
    return dict(tp_h=round(tp, 1), horas_parada=round(h_tot, 1), horas_falla=round(h_fallas, 1), horas_planificada=round(h_plan, 1),
                n_fallas=n_fallas, n_planificadas=n_plan,
                dk=round(operativo / tp, 4) if tp else None,
                mtbf_h=round(operativo / n_fallas, 1) if n_fallas else None,
                mttr_h=round(h_fallas / n_fallas, 2) if n_fallas else None,
                pct_preventivo=round(h_plan / (h_fallas + h_plan), 3) if h_fallas + h_plan else None,
                causas=sorted(({'causa': k, 'horas': round(v, 1)} for k, v in causas.items()), key=lambda x: -x['horas']))


def dk_mensual(paradas, hasta, meses=12, horas_turno=HORAS_TURNO, turnos=1, desde_registro=None):
    """Dₖ de cada uno de los últimos `meses` meses calendario (el actual, hasta `hasta`).
    Los meses anteriores a `desde_registro` (cuando empezó a registrarse paradas) quedan sin dato: no tener
    registros no significa que la máquina no haya fallado."""
    h = date.fromisoformat(str(hasta)[:10])
    r0 = date.fromisoformat(str(desde_registro)[:10]) if desde_registro else None
    out, y, m = [], h.year, h.month
    for _ in range(meses):
        ini = date(y, m, 1)
        fin = date(y + (m == 12), m % 12 + 1, 1)
        fin = min(fin, h + timedelta(days=1))
        if r0 and fin <= r0:
            out.append(dict(mes=f'{y}-{m:02d}', dk=None, horas_parada=None, n_fallas=None))
            y, m = (y - 1, 12) if m == 1 else (y, m - 1)
            continue
        r = indicadores(paradas, max(ini, r0).isoformat() if r0 else ini.isoformat(), fin.isoformat(), horas_turno, turnos)
        out.append(dict(mes=f'{y}-{m:02d}', dk=r['dk'], horas_parada=r['horas_parada'], n_fallas=r['n_fallas']))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out[::-1]


def dias_de_frecuencia(plan, horas_turno=HORAS_TURNO):
    """Frecuencia del plan en días laborables (si viene en horas de uso, con el turno completo)."""
    if plan.get('frecuencia_dias'):
        return int(plan['frecuencia_dias'])
    if plan.get('frecuencia_horas'):
        return max(1, int(round(plan['frecuencia_horas'] / horas_turno)))
    return None


def proximo_vencimiento(plan, ultima, hoy, horas_turno=HORAS_TURNO):
    """Fecha en que vence el preventivo: `frecuencia` días laborables después de la última ejecución
    (o del alta del plan si nunca se hizo). Devuelve (fecha ISO, días laborables que faltan; negativo = vencido)."""
    f = dias_de_frecuencia(plan, horas_turno)
    if not f:
        return None, None
    base = str(ultima or plan.get('desde') or hoy)[:10]
    vence = str(np.busday_offset(np.datetime64(base, 'D'), f, roll='forward', weekmask=WEEKMASK))
    falta = int(np.busday_count(str(hoy)[:10], vence, weekmask=WEEKMASK)) if vence >= str(hoy)[:10] else \
        -int(np.busday_count(vence, str(hoy)[:10], weekmask=WEEKMASK))
    return vence, falta


def semaforo(dk, vencidas=0, parada_ahora=False):
    """Estado resumido de una máquina para las tarjetas."""
    if parada_ahora:
        return 'r'
    if dk is not None and dk < 0.80:
        return 'r'
    if vencidas or (dk is not None and dk < META_DK):
        return 'a'
    return 'v'


def disponibilidad_futura(ordenes, desde, T, maquinas, horas_turno=HORAS_TURNO):
    """Calendario (T, n_maquinas) de fracción disponible por día laborable desde `desde`, descontando los
    preventivos programados (ordenes: dicts con maquina, programada_para, duracion_h). Es la entrada del programador."""
    base = np.busday_offset(np.datetime64(str(desde)[:10], 'D'), 0, roll='forward', weekmask=WEEKMASK)
    d = np.ones((T, len(maquinas)))
    for o in ordenes:
        if not o.get('programada_para') or o.get('maquina') not in maquinas:
            continue
        k = int(np.busday_count(base, np.datetime64(str(o['programada_para'])[:10], 'D'), weekmask=WEEKMASK))
        if 0 <= k < T:
            j = maquinas.index(o['maquina'])
            d[k, j] = max(0.0, d[k, j] - (o.get('duracion_h') or 0) / horas_turno)
    return d
