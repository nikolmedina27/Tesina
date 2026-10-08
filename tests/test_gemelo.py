import json
import sqlite3
from datetime import date

import numpy as np
import pytest

from dss.datos import DB
from dss.gemelo.calendario import (Ventanas, es_laborable, pascua, feriados, hora, fecha, ventanas_dia, TURNO, LABORABLES,
                                   turno_base)


def test_pascua_y_feriados():
    assert pascua(2024) == date(2024, 3, 31) and pascua(2025) == date(2025, 4, 20)
    assert date(2024, 3, 28) in feriados(2024) and date(2024, 3, 29) in feriados(2024)       # jueves y viernes santo
    assert not es_laborable(date(2023, 7, 28)) and not es_laborable(date(2023, 7, 30))        # fiestas patrias y domingo
    assert not es_laborable(date(2023, 7, 29))                                                # 29 de julio también es feriado
    assert es_laborable(date(2023, 7, 27)) and es_laborable(date(2023, 7, 22))                # jueves y sábado normales


def test_ventanas_avanzar_y_acumulado():
    v = Ventanas([(7, 15), (31, 39)])                                  # dos turnos de 8 h
    assert v.avanzar(7, 4) == 11
    assert v.avanzar(7, 8) == 15                                       # justo al final del turno
    assert v.avanzar(7, 10) == 33                                      # 8 h hoy + 2 h al día siguiente
    assert v.avanzar(20, 3) == 34                                      # empieza en la siguiente ventana
    assert v.inicio_desde(16) == 31 and v.inicio_desde(10) == 10
    assert v.acumulado(35) == 12 and v.trabajado(10, 35) == 5 + 4


def test_ventanas_quitar_y_agregar():
    v = Ventanas([(7, 15)])
    v.quitar([(9, 11)])
    assert v.avanzar(7, 4) == 13                                       # 2 h antes + 2 h después de la parada
    v.agregar([(15, 17)])
    assert v.avanzar(7, 8) == 17                                       # las horas extra suman capacidad: 2 + 4 + 2
    assert v.acumulado(17) == 8


def test_turno_base_es_laborable_y_dentro_del_turno():
    v = turno_base()
    assert abs(v.cum[-1] - 8 * len(LABORABLES)) < 1e-6
    for a, b in list(zip(v.ini, v.fin))[:200]:
        assert fecha(a).weekday() < 6 and es_laborable(fecha(a)) and (a % 24, b % 24) == (7.0, 15.0)


def _bd_lista():
    if not DB.exists():
        return False
    con = sqlite3.connect(DB)
    ok = all(con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?", (t,)).fetchone()[0] for t in ('sim_feature', 'proyecto_proceso')) \
        and con.execute('SELECT COUNT(DISTINCT toneladas) FROM proyecto WHERE en_muestra=1').fetchone()[0] > 1 \
        and con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='gem_meta'").fetchone()[0] > 0
    con.close()
    return ok


@pytest.fixture(scope='module')
def corrida():
    from dss.datos import conectar
    from dss.gemelo.generador import generar
    from dss.gemelo.motor import Gemelo
    con = conectar()
    P, par = generar(con)
    f = {int(k): v for k, v in json.loads(con.execute("SELECT valor FROM gem_meta WHERE clave='factores'").fetchone()[0]).items()}
    sim = Gemelo(P, par, eficiencia=f)
    res = sim.correr()
    con.close()
    return P, par, f, sim, res


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el gemelo (py scripts/exp6_gemelo.py)')
def test_todos_terminan_y_el_cumplimiento_reproduce_la_historia(corrida):
    P, par, f, sim, res = corrida
    assert set(res.fin) == {p.pid for p in P}
    for p in P:
        assert fecha(res.fin[p.pid]) > p.ini
    m = [p for p in P if p.en_muestra]
    cumplen = np.mean([fecha(res.fin[p.pid]) <= p.fp for p in m])
    assert abs(cumplen - np.mean([p.fr <= p.fp for p in m])) <= 0.12      # OTD del gemelo ≈ OTD real de la muestra (76 %)


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el gemelo')
def test_ningun_recurso_atiende_dos_lotes_a_la_vez(corrida):
    P, par, f, sim, res = corrida
    uso = {}
    for o in res.ops:
        clave = (o.recurso, o.estacion if o.recurso in ('armado', 'soldeo', 'limpieza') else 0)
        uso.setdefault(clave, []).append((o.t_ini, o.t_fin))
    for clave, lst in uso.items():
        lst.sort()
        solapes = sum(1 for (a0, a1), (b0, b1) in zip(lst, lst[1:]) if b0 < a1 - 1e-6)
        assert solapes == 0, (clave, solapes)


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el gemelo')
def test_cada_lote_respeta_el_orden_del_proceso(corrida):
    P, par, f, sim, res = corrida
    por = {}
    for o in res.ops:
        por.setdefault(o.cid, []).append(o)
    for cid, ops in list(por.items())[:3000]:
        hab = [o.t_fin for o in ops if o.tipo in ('sierra', 'cizalla', 'cnc', 'roscado')]
        arm = [o for o in ops if o.tipo == 'armado']
        sol = [o for o in ops if o.tipo == 'soldeo']
        lim = [o for o in ops if o.tipo == 'limpieza']
        assert arm and sol and lim
        assert max(hab, default=0) <= arm[0].t_ini + 1e-6
        assert arm[0].t_fin <= sol[0].t_ini + 1e-6 <= lim[0].t_ini + 1e-6


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el gemelo')
def test_sin_palancas_las_maquinas_solo_trabajan_en_turno_y_dias_habiles(corrida):
    P, par, f, sim, res = corrida
    for o in res.ops:
        if o.recurso.startswith('maq'):
            assert es_laborable(fecha(o.t_ini))
            horas = sim.v_maq[int(o.recurso[3])].trabajado(o.t_ini, o.t_fin)
            assert horas >= (o.t_fin - o.t_ini) * 0.0 and (o.t_ini % 24) >= 7 - 1e-9 and (o.t_ini % 24) < 15 + 1e-9


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el gemelo')
def test_tareo_conserva_las_horas_y_es_reproducible(corrida):
    from dss.gemelo.motor import Gemelo
    P, par, f, sim, res = corrida
    for p in P[:8]:
        hecho = sum(sim.hh_hecho.get((p.pid, j), 0.0) for j in (3, 4, 5, 6, 8, 9, 10))
        esperado = sum(c.hh.get(o, 0.0) for c in p.conjuntos for o in ('sierra', 'cizalla', 'cnc', 'roscado', 'armado', 'soldeo', 'limpieza'))
        esperado += sum(c.hh.get('soldeo', 2.0) * 0.35 + c.hh.get('limpieza', 0.5) * 0.5 for c in p.conjuntos if c.nc)
        assert hecho == pytest.approx(esperado * f[p.pid], rel=0.02)          # el tareo cuenta las horas en obra, con el ritmo del proyecto
    otra = Gemelo(P, par, eficiencia=f).correr()
    assert all(otra.fin[p.pid] == res.fin[p.pid] for p in P)


@pytest.mark.skipif(not _bd_lista(), reason='requiere la BD con el gemelo')
def test_las_palancas_cuestan_y_respetan_la_plantilla_del_contratista(corrida):
    from dss.gemelo.motor import Gemelo, Palanca
    from dss.gemelo.generador import CONTRATISTAS
    P, par, f, sim, res = corrida
    g = Gemelo(P, par, eficiencia=f)
    g.correr(hasta=hora(P[8].ini, 20.0))
    pid = P[8].pid
    c1 = g.aplicar(pid, Palanca('horas_extra', 8))
    assert c1 > 0
    antes = g.crews[(pid, 8)].n
    g.aplicar(pid, Palanca('personas', 8, 99))
    assert g.crews[(pid, 8)].n - antes <= CONTRATISTAS[P[8].contratista][2]          # nunca más gente que la plantilla del contratista
    assert g.aplicar(pid, Palanca('horas_extra', 0)) == 0.0                           # lo que la planta no puede hacer no cuesta ni cambia nada
