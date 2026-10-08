"""Gemelo de la planta: simulación de eventos discretos hora a hora y lote por lote (SIMULADO).

Flujo de cada lote de piezas (conjunto):
  paquete de ingeniería liberado (RFIs del cliente lo atrasan) → compra y llegada del material (proveedor)
  → habilitado en las máquinas que necesite (sierra, cizalla-punzonadora, mesa CNC, roscadora), en paralelo
  → puente grúa A al buffer → [doblez externo: envío semanal] → puente grúa B a una mesa
  → armado (mesa + 2 armadores de la cuadrilla del contratista) → grúa B → soldeo (puesto + 1 soldador)
  → limpieza e inspección (zona + 1 ayudante) → si hay no conformidad: retrabajo de soldeo y otra inspección
  → grúa B al patio → despacho a granallado y pintura (camión cuando hay ≥ 12 t o los sábados)
  → vuelve pintado → despacho a obra (camiones de hasta 25 t). El proyecto termina con el último camión.

Recursos con calendario propio (`Ventanas`): 4 máquinas (turno 07-15 menos sus paradas), 2 puentes grúa,
6 mesas, 8 puestos de soldeo, 2 zonas de limpieza (4 cupos), cuadrillas por proyecto y proceso, despacho.
Cola de cada recurso por prioridad: fecha comprometida del proyecto (EDD) y luego orden del lote.

La `Politica` decide la fecha comprometida al iniciar cada proyecto y, cada 12 días laborables, puede aplicar
palancas: más personas (si el contratista tiene gente libre), horas extra, segundo turno en una máquina o
expeditar un servicio externo. Todo el azar viene sorteado del generador (números aleatorios comunes).
"""
import bisect
import heapq
import itertools
from dataclasses import dataclass, field

import numpy as np

from .calendario import (Ventanas, ventanas_dia, TURNO, HORAS_EXTRA, SEGUNDO_TURNO, GRUA, EPOCA, FIN, hora, fecha,
                         LABORABLES)
from .generador import CONTRATISTAS, ausentismo

OP_PROC = {'sierra': 3, 'cizalla': 4, 'cnc': 5, 'roscado': 6, 'armado': 8, 'soldeo': 9, 'limpieza': 10,
           'retrabajo': 9, 'reinspeccion': 10}
MAQ = {'sierra': 0, 'cizalla': 1, 'cnc': 2, 'roscado': 3}
MOV_H = {'buffer': 0.20, 'mesa': 0.25, 'puesto': 0.20, 'limpieza': 0.20, 'patio': 0.25}
DIAS_REVISION = 12
FRAC_MO, PRIMA_CONTRATISTA, RECARGO_HE, EXPEDITAR = 0.30, 0.10, 1.5, 0.01
CAP_CAMION_PINTURA, CAP_CAMION_OBRA = 25_000.0, 25_000.0
LAB_ORD = [d.toordinal() for d in LABORABLES]
CREW_Q = ('armado', 'soldeo', 'limpieza')


@dataclass
class Op:
    id: int
    pid: int
    cid: int
    tipo: str
    horas: float                  # horas de trabajo del recurso (máquina) o HH (cuadrilla)
    personas: int = 0
    t_ini: float = -1.0
    t_fin: float = -1.0
    recurso: str = ''
    estacion: int = 0


@dataclass
class Cuadrilla:
    n: float
    ocupados: int = 0
    v: Ventanas = None
    propia: bool = False          # tiene ventanas propias (horas extra)


@dataclass
class Palanca:
    tipo: str                     # personas | horas_extra | turno2 | expeditar
    proceso: int                  # índice 0-based (como dss.whatif)
    valor: int = 1


class Politica:
    """Política «como se hizo»: compromete la fecha del cotizador y no gestiona."""
    nombre = 'A0 como se hizo'
    aplica_a = None               # None = todos los proyectos; si no, conjunto de pid

    def compromiso(self, sim, p):
        return p.fp

    def revisar(self, sim, p, t):
        return []


@dataclass
class Resultado:
    politica: str
    fin: dict                     # pid -> hora de término
    compromiso: dict              # pid -> fecha comprometida
    ops: list
    movimientos: list
    camiones: list
    material: list
    palancas: list                # (pid, t, Palanca, costo % presupuesto)
    paquetes: list                # (pid, paquete, t_liberacion, dias_rfi)
    ingenieria: dict = field(default_factory=dict)
    estados: list = field(default_factory=list)


class Gemelo:
    def __init__(self, proyectos, paradas, politica=None, eficiencia=1.0, revisar_cada=DIAS_REVISION):
        self.P = {p.pid: p for p in proyectos}
        self.politica = politica or Politica()
        self.efic = eficiencia            # ritmo: número global o dict pid -> factor calibrado; escala DURACIONES, no HH
        self.revisar_cada = revisar_cada
        self.cola_ev = []
        self.seq = itertools.count()
        self.opseq = itertools.count(1)
        self.ahora = 0.0
        self.base = Ventanas(ventanas_dia(EPOCA, FIN, TURNO))
        self.paradas = paradas
        self.paradas_maq = [[(a, b) for k, a, b, *_ in paradas if k == m] for m in range(4)]
        self.v_maq = []
        for m in range(4):
            v = Ventanas(self.base.intervalos())
            v.quitar(self.paradas_maq[m])
            self.v_maq.append(v)
        self.v_grua = Ventanas(ventanas_dia(EPOCA, FIN, GRUA))
        self.maq_libre = [True] * 4
        self.grua_libre = [True, True]
        self.mesas = set(range(1, 7))
        self.puestos = set(range(1, 9))
        self.cupos_limpieza = set(range(1, 9))            # zona 1: cupos 1-4, zona 2: 5-8
        self.despacho = Cuadrilla(n=4)
        self.despacho.v = self.base
        self.colas = {k: [] for k in ['maq0', 'maq1', 'maq2', 'maq3', 'grua0', 'grua1']}
        self.colas.update({k: {} for k in CREW_Q})      # por proyecto: {pid: heap}
        self.retrabajados = set()
        self.crews = {}
        self.conj = {}
        self.estado_c = {}                                # cid -> dict de avance
        self.pend_hab = {}
        self.hab_listo = {}
        self.en_buffer_doblez = {}                        # pid -> [cid]
        self.listos_pintura = {}                          # pid -> [cid]
        self.pintados = {}
        self.entregados = {}
        self.envios_doblez = {}
        self.envios_pintura = {}
        self.expeditar = {}                               # (pid, proceso) -> True para el próximo envío
        self.compromiso = {}
        self.fin = {}
        self.activos = set()
        self.hh_hecho = {}                                # (pid, proceso 1-13) -> HH realizadas
        self.ops, self.movs, self.camiones, self.material, self.palancas, self.paquetes = [], [], [], [], [], []
        self.ing = {}
        self.ultimo_rev = {}
        self.log_estado = []

    def _set(self, cid, etapa, ubic):
        """Cambia el estado de un lote y lo anota con su hora (la vista 3D reconstruye la planta en cualquier instante)."""
        self.estado_c[cid] = dict(etapa=etapa, ubic=ubic)
        self.log_estado.append((cid, self.ahora, etapa, ubic))

    # ------------------------------------------------------------------ eventos
    def evento(self, t, tipo, *datos):
        heapq.heappush(self.cola_ev, (t, next(self.seq), tipo, datos))

    def correr(self, hasta=None):
        for p in self.P.values():
            self.evento(hora(p.ini, 7.0), 'inicio', p.pid)
        limite = float('inf') if hasta is None else hasta
        while self.cola_ev:
            t, _, tipo, datos = heapq.heappop(self.cola_ev)
            if t > limite:
                heapq.heappush(self.cola_ev, (t, 0, tipo, datos))
                break
            self.ahora = t
            getattr(self, '_' + tipo)(*datos)
        return Resultado(self.politica.nombre, dict(self.fin), dict(self.compromiso), self.ops, self.movs, self.camiones,
                         self.material, self.palancas, self.paquetes, self.ing, self.log_estado)

    # ------------------------------------------------------------------ proyecto
    def _inicio(self, pid):
        p = self.P[pid]
        self.activos.add(pid)
        for j in (8, 9, 10):
            self.crews[(pid, j)] = Cuadrilla(n=float(p.crew[j - 1]), v=self.base)
        for c in p.conjuntos:
            self.conj[c.id] = c
            self._set(c.id, 'ESPERA', 'oficina')
        self.compromiso[pid] = self.politica.compromiso(self, p)
        # ingeniería: paquetes liberados a lo largo del trabajo de la oficina técnica (crew[0] proyectistas)
        horas_ing = p.hh[0] * self._ef(pid) / max(p.crew[0], 1.0)
        t0 = self.base.inicio_desde(self.ahora)
        atraso = {}
        for k, d in p.rfis:
            atraso[k] = atraso.get(k, 0.0) + d
        self.ing[pid] = (t0, self.base.avanzar(t0, horas_ing))
        for k in range(p.paquetes):
            frac = ((k + 1) / p.paquetes) ** 0.9
            t = self.base.avanzar(t0, horas_ing * frac)
            if atraso.get(k):
                t = self.base.avanzar(t, atraso[k] * 8.0)
            self.evento(t, 'paquete', pid, k, atraso.get(k, 0.0))
        for frac, ids in p.cambios:
            self.evento(self.base.avanzar(t0, horas_ing * (1 + frac * 0.6)), 'cambio', pid, tuple(ids))
        self._hh(pid, 1, p.hh[0] * self._ef(pid))
        self._hh(pid, 2, p.hh[1])
        self.evento(self.base.avanzar(self.ahora, self.revisar_cada * 8.0), 'revision', pid)

    def _paquete(self, pid, k, rfi):
        p = self.P[pid]
        self.paquetes.append((pid, k, self.ahora, rfi))
        llegada = self.base.avanzar(self.ahora, p.lead_compra[k] * self._ritmo(pid) * 8.0)
        kg = sum(c.kg for c in p.conjuntos if c.paquete == k and not c.adicional)
        self.material.append((pid, k, self.ahora, llegada, kg))
        self.evento(llegada, 'material', pid, k, False)

    def _cambio(self, pid, ids):
        p = self.P[pid]
        llegada = self.base.avanzar(self.ahora, p.lead_compra[p.paquetes - 1] * 8.0)
        self.material.append((pid, -1, self.ahora, llegada, sum(self.conj[i].kg for i in ids)))
        self.evento(llegada, 'material', pid, ids, True)

    def _material(self, pid, k, adicional):
        p = self.P[pid]
        lotes = [self.conj[i] for i in k] if adicional else [c for c in p.conjuntos if c.paquete == k and not c.adicional]
        for c in lotes:
            maqs = [o for o in ('sierra', 'cizalla', 'cnc', 'roscado') if o in c.hh]
            self.pend_hab[c.id] = len(maqs)
            self._set(c.id, 'HABILITADO', 'patio')
            if not maqs:
                self._hab_fin(c)
            for o in maqs:
                self._encolar(Op(next(self.opseq), pid, c.id, o, c.hh[o], recurso=f'maq{MAQ[o]}'))

    # ------------------------------------------------------------------ colas y despacho de recursos
    def _prio(self, op):
        c = self.conj[op.cid]
        return (self.compromiso.get(op.pid, FIN).toordinal(), op.pid, c.indice, op.id)

    def _encolar(self, op):
        q = op.recurso if op.recurso.startswith(('maq', 'grua')) else op.tipo if op.tipo in ('armado', 'soldeo', 'limpieza') \
            else 'soldeo' if op.tipo == 'retrabajo' else 'limpieza'
        if q in CREW_Q:
            heapq.heappush(self.colas[q].setdefault(op.pid, []), (self._prio(op), op))
        else:
            heapq.heappush(self.colas[q], (self._prio(op), op))
        self._despachar(q)

    def _despachar(self, q):
        cola = self.colas[q]
        if q.startswith('maq'):
            m = int(q[3])
            while cola and self.maq_libre[m]:
                _, op = heapq.heappop(cola)
                self.maq_libre[m] = False
                ini = self.v_maq[m].inicio_desde(self.ahora)
                fin = self.v_maq[m].avanzar(self.ahora, op.horas * self._ef(op.pid))
                self._empezar(op, ini, fin, op.recurso, 0, 1)
            return
        if q.startswith('grua'):
            g = int(q[4])
            while cola and self.grua_libre[g]:
                _, op = heapq.heappop(cola)
                self.grua_libre[g] = False
                ini = self.v_grua.inicio_desde(self.ahora)
                self._empezar(op, ini, self.v_grua.avanzar(self.ahora, op.horas), op.recurso, 0, 0)
            return
        pool = {'armado': self.mesas, 'soldeo': self.puestos, 'limpieza': self.cupos_limpieza}[q]
        if not pool or not cola:
            return
        orden = sorted((pid for pid, h in cola.items() if h), key=lambda pid: (self.compromiso.get(pid, FIN).toordinal(), pid))
        for pid in orden:
            h = cola[pid]
            while h and pool:
                pr, op = h[0]
                proc = OP_PROC[op.tipo]
                cr = self.crews.get((op.pid, proc))
                nec = 2 if op.tipo == 'armado' else 1
                if cr is None or cr.n - cr.ocupados < nec - 1e-9:
                    break
                heapq.heappop(h)
                est = min(pool)
                pool.discard(est)
                cr.ocupados += nec
                f = ausentismo(self.P[op.pid].semilla, op.pid, proc, fecha(self.ahora).toordinal(), cr.n)
                dur = op.horas * self._ef(op.pid) / nec * f
                ini = cr.v.inicio_desde(self.ahora)
                self._empezar(op, ini, cr.v.avanzar(self.ahora, dur), q, est, nec)
            if not pool:
                break

    def _empezar(self, op, ini, fin, recurso, estacion, personas):
        op.t_ini, op.t_fin, op.estacion, op.personas = ini, fin, estacion, personas
        op.recurso = recurso
        self.evento(fin, 'fin_op', op)

    def _fin_op(self, op):
        self.ops.append(op)
        c = self.conj[op.cid]
        t = op.tipo
        if op.recurso.startswith('maq'):
            m = int(op.recurso[3])
            self.maq_libre[m] = True
            self._hh(op.pid, OP_PROC[t], op.horas * self._ef(op.pid))      # el tareo cuenta las horas en obra, con ineficiencia
            self.pend_hab[c.id] -= 1
            if self.pend_hab[c.id] == 0:
                self._hab_fin(c)
            self._despachar(op.recurso)
            return
        if op.recurso.startswith('grua'):
            g = int(op.recurso[4])
            self.grua_libre[g] = True
            self.movs.append((op.pid, op.cid, g, op.tipo, op.t_ini, op.t_fin))
            self._llegada(c, op.tipo)
            self._despachar(op.recurso)
            return
        proc = OP_PROC[t]
        cr = self.crews[(op.pid, proc)]
        cr.ocupados -= op.personas
        self._hh(op.pid, proc, op.horas * self._ef(op.pid))
        pool = {'armado': self.mesas, 'soldeo': self.puestos, 'limpieza': self.cupos_limpieza}[op.recurso]
        pool.add(op.estacion)
        if t == 'armado':
            self._mover(c, 'puesto')
        elif t in ('soldeo', 'retrabajo'):
            if t == 'retrabajo':
                self.retrabajados.add(c.id)
            self._mover(c, 'limpieza')
        elif t in ('limpieza', 'reinspeccion'):
            if c.nc and t == 'limpieza' and c.id not in self.retrabajados:
                self._set(c.id, 'RETRABAJO', 'limpieza')
                self._encolar(Op(next(self.opseq), op.pid, c.id, 'retrabajo', c.hh.get('soldeo', 2.0) * 0.35))
            else:
                self._mover(c, 'patio')
        for q in CREW_Q:
            self._despachar(q)

    def _hab_fin(self, c):
        self._mover(c, 'buffer')

    def _mover(self, c, destino):
        g = 0 if destino == 'buffer' else 1
        self._set(c.id, 'MOVIMIENTO', destino)
        self._encolar(Op(next(self.opseq), c.pid, c.id, destino, MOV_H[destino], recurso=f'grua{g}'))

    def _llegada(self, c, destino):
        pid = c.pid
        if destino == 'buffer':
            if c.doblez:
                self._set(c.id, 'DOBLEZ', 'buffer')
                self.en_buffer_doblez.setdefault(pid, []).append(c.id)
                self._programar_doblez(pid)
            else:
                self._mover(c, 'mesa')
        elif destino == 'mesa':
            self._set(c.id, 'ARMADO', 'mesa')
            self._encolar(Op(next(self.opseq), pid, c.id, 'armado', c.hh.get('armado', 1.0)))
        elif destino == 'puesto':
            self._set(c.id, 'SOLDEO', 'puesto')
            self._encolar(Op(next(self.opseq), pid, c.id, 'soldeo', c.hh.get('soldeo', 1.0)))
        elif destino == 'limpieza':
            ya = c.id in self.retrabajados
            self._set(c.id, 'LIMPIEZA', 'limpieza')
            h = c.hh.get('limpieza', 0.5) * (0.5 if ya else 1.0)
            self._encolar(Op(next(self.opseq), pid, c.id, 'reinspeccion' if ya else 'limpieza', h))
        elif destino == 'patio':
            self._set(c.id, 'LISTO_PINTURA', 'patio')
            self.listos_pintura.setdefault(pid, []).append(c.id)
            self.evento(self._proximo_dia(10.0), 'despacho_pintura', pid)

    # ------------------------------------------------------------------ servicios externos y despachos
    def _proximo_dia(self, h, dia_semana=None):
        """Primer instante t >= ahora a las h horas de un día laborable (opcional: de ese día de la semana)."""
        i = bisect.bisect_left(LAB_ORD, fecha(self.ahora).toordinal())
        while i < len(LABORABLES):
            dd = LABORABLES[i]
            t = hora(dd, h)
            if t >= self.ahora and (dia_semana is None or dd.weekday() == dia_semana):
                return t
            i += 1
        return self.ahora + 24

    def _programar_doblez(self, pid):
        self.evento(self._proximo_dia(9.0, 1), 'envio_doblez', pid)          # envíos los martes a las 09:00

    def _envio_doblez(self, pid):
        lote = self.en_buffer_doblez.get(pid, [])
        if not lote:
            return
        self.en_buffer_doblez[pid] = []
        p = self.P[pid]
        k = self.envios_doblez.get(pid, 0)
        self.envios_doblez[pid] = k + 1
        dias = p.lead_doblez[min(k, len(p.lead_doblez) - 1)] * self._ritmo(pid)
        if self.expeditar.pop((pid, 6), False):
            dias *= 0.75
        vuelta = self.base.avanzar(self.ahora, dias * 8.0)
        kg = sum(self.conj[i].kg for i in lote)
        self.camiones.append((pid, 'doblez', self.ahora, vuelta, kg, len(lote)))
        for i in lote:
            self._set(i, 'DOBLEZ', 'externo')
        self.evento(vuelta, 'vuelta_doblez', pid, tuple(lote))

    def _vuelta_doblez(self, pid, lote):
        for i in lote:
            self._mover(self.conj[i], 'mesa')

    def _despacho_pintura(self, pid):
        lista = self.listos_pintura.get(pid, [])
        if not lista:
            return
        kg = sum(self.conj[i].kg for i in lista)
        p = self.P[pid]
        quedan = [c for c in p.conjuntos if self.estado_c[c.id]['etapa'] not in ('LISTO_PINTURA', 'PINTURA', 'PINTADO', 'ENTREGADO')]
        if kg < 12_000 and fecha(self.ahora).weekday() != 5 and quedan:
            self.evento(self._proximo_dia(10.0, 5), 'despacho_pintura', pid)   # a más tardar el sábado
            return
        self.listos_pintura[pid] = []
        while lista:
            carga, peso = [], 0.0
            while lista and (peso + self.conj[lista[0]].kg <= CAP_CAMION_PINTURA or not carga):
                peso += self.conj[lista[0]].kg
                carga.append(lista.pop(0))
            h_carga = 1.0 + peso / 10_000.0
            fin_carga = self.base.avanzar(self.ahora, h_carga)
            self._hh(pid, 11, 2 * h_carga)
            k = self.envios_pintura.get(pid, 0)
            self.envios_pintura[pid] = k + 1
            dias = p.lead_pintura[min(k, len(p.lead_pintura) - 1)] * self._ritmo(pid)
            if self.expeditar.pop((pid, 11), False):
                dias *= 0.75
            vuelta = self.base.avanzar(fin_carga, dias * 8.0)
            self.camiones.append((pid, 'pintura', fin_carga, vuelta, peso, len(carga)))
            for i in carga:
                self._set(i, 'PINTURA', 'externo')
            self.evento(vuelta, 'vuelta_pintura', pid, tuple(carga))

    def _vuelta_pintura(self, pid, carga):
        for i in carga:
            self._set(i, 'PINTADO', 'patio')
            self.pintados.setdefault(pid, []).append(i)
        self.evento(self._proximo_dia(8.0), 'despacho_obra', pid)

    def _despacho_obra(self, pid):
        lista = self.pintados.get(pid, [])
        if not lista:
            return
        p = self.P[pid]
        kg = sum(self.conj[i].kg for i in lista)
        resto = [c for c in p.conjuntos if self.estado_c[c.id]['etapa'] not in ('PINTADO', 'ENTREGADO')]
        if kg < 20_000 and resto:
            return
        self.pintados[pid] = []
        t = self.ahora
        while lista:
            carga, peso = [], 0.0
            while lista and (peso + self.conj[lista[0]].kg <= CAP_CAMION_OBRA or not carga):
                peso += self.conj[lista[0]].kg
                carga.append(lista.pop(0))
            h_carga = 2.0 + peso / 12_000.0
            t_fin = self.base.avanzar(t, h_carga)
            self._hh(pid, 13, 3 * h_carga)
            self.camiones.append((pid, 'obra', t, t_fin, peso, len(carga)))
            for i in carga:
                self._set(i, 'ENTREGADO', 'obra')
                self.entregados.setdefault(pid, []).append(i)
            t = t_fin
        if all(self.estado_c[c.id]['etapa'] == 'ENTREGADO' for c in p.conjuntos):
            self.fin[pid] = t
            self.activos.discard(pid)
            for j in (8, 9, 10):
                self.crews[(pid, j)].n = 0

    # ------------------------------------------------------------------ gestión
    def _revision(self, pid):
        if pid in self.fin:
            return
        p = self.P[pid]
        if self.politica.aplica_a is None or pid in self.politica.aplica_a:
            for pal in self.politica.revisar(self, p, self.ahora) or []:
                self.aplicar(pid, pal)
        self.evento(self.base.avanzar(self.ahora, self.revisar_cada * 8.0), 'revision', pid)

    def costo_hh(self, p):
        return FRAC_MO * 100.0 / max(float(p.hh_ratio.sum()), 1.0)

    def aplicar(self, pid, pal, dias=None):
        """Aplica una palanca desde ahora hasta la próxima revisión. Devuelve el costo (% del presupuesto)."""
        p = self.P[pid]
        dias = self.revisar_cada if dias is None else dias
        hasta = fecha(self.base.avanzar(self.ahora, dias * 8.0))
        desde = fecha(self.ahora)
        c_hh = self.costo_hh(p)
        costo = 0.0
        j = pal.proceso + 1
        if pal.tipo == 'personas' and j in (8, 9, 10):
            pool = CONTRATISTAS[p.contratista][2]
            usados = sum(self.crews[(q, jj)].n for q in self.activos for jj in (8, 9, 10)
                         if self.P[q].contratista == p.contratista and (q, jj) in self.crews)
            extra = max(0.0, min(pal.valor, pool - usados))
            if extra <= 0:
                return 0.0
            cr = self.crews[(pid, j)]
            restante = max(0.0, p.hh[j - 1] - self.hh_hecho.get((pid, j), 0.0))
            costo = PRIMA_CONTRATISTA * c_hh * restante * extra / (cr.n + extra)
            cr.n += extra
            pal = Palanca(pal.tipo, pal.proceso, int(extra))
        elif pal.tipo == 'horas_extra' and j in (8, 9, 10):
            cr = self.crews[(pid, j)]
            if not cr.propia:
                cr.v, cr.propia = Ventanas(self.base.intervalos()), True
            nuevas = ventanas_dia(desde, hasta, HORAS_EXTRA)
            cr.v.agregar(nuevas)
            costo = cr.n * len(nuevas) * (HORAS_EXTRA[1] - HORAS_EXTRA[0]) * c_hh * RECARGO_HE
        elif pal.tipo == 'turno2' and 3 <= j <= 6:
            m = j - 3
            nuevas = ventanas_dia(desde, hasta, SEGUNDO_TURNO)
            self.v_maq[m].agregar(nuevas)
            self.v_maq[m].quitar(self.paradas_maq[m])
            costo = len(nuevas) * (SEGUNDO_TURNO[1] - SEGUNDO_TURNO[0]) * c_hh
        elif pal.tipo == 'expeditar' and j in (7, 12):
            self.expeditar[(pid, j - 1)] = True
            costo = EXPEDITAR * 100.0
        elif pal.tipo == 'expeditar' and j == 2:
            if not self._expeditar_compras(pid):
                return 0.0
            costo = EXPEDITAR * 100.0
        else:
            return 0.0
        self.palancas.append((pid, self.ahora, pal, costo))
        for q in ('armado', 'soldeo', 'limpieza', 'maq0', 'maq1', 'maq2', 'maq3'):
            self._despachar(q)
        return costo

    def _expeditar_compras(self, pid):
        """Los pedidos de material pendientes del proyecto llegan un 25 % antes de lo que faltaba (gestión con el proveedor)."""
        cambio = False
        for i, (t, sq, tipo, datos) in enumerate(self.cola_ev):
            if tipo == 'material' and datos[0] == pid:
                nuevo = self.ahora + (t - self.ahora) * 0.75
                self.cola_ev[i] = (nuevo, sq, tipo, datos)
                cambio = True
        if cambio:
            heapq.heapify(self.cola_ev)
        return cambio

    # ------------------------------------------------------------------ estado (para las políticas)
    def _ef(self, pid):
        return self.efic.get(pid, 1.0) if isinstance(self.efic, dict) else self.efic

    def _ritmo(self, pid):
        """Los plazos de proveedores y servicios externos del proyecto se escalan con la raíz del factor calibrado
        (proyectos «lentos» también tuvieron proveedores y aprobaciones más lentas)."""
        return float(np.sqrt(self._ef(pid)))

    def _hh(self, pid, proc, horas):
        self.hh_hecho[(pid, proc)] = self.hh_hecho.get((pid, proc), 0.0) + horas

    def avance(self, pid):
        """Fracción hecha (13,) de cada proceso del proyecto, como la entendería el planificador."""
        p = self.P[pid]
        a = np.zeros(13)
        ini, fin = self.ing.get(pid, (self.ahora, self.ahora))
        a[0] = 1.0 if self.ahora >= fin else max(0.0, (self.ahora - ini) / max(fin - ini, 1e-9))
        tot_kg = sum(c.kg for c in p.conjuntos)
        llegado = sum(kg for q, k, t0, t1, kg in self.material if q == pid and t1 <= self.ahora)
        a[1] = min(1.0, llegado / max(tot_kg, 1.0))
        for j in (3, 4, 5, 6, 8, 9, 10):
            tot = p.hh[j - 1] * self._ef(pid)
            a[j - 1] = min(1.0, self.hh_hecho.get((pid, j), 0.0) / max(tot, 1e-9))
        etapas = [self.estado_c[c.id]['etapa'] for c in p.conjuntos]
        kg_et = lambda ok: sum(c.kg for c, e in zip(p.conjuntos, etapas) if e in ok) / max(tot_kg, 1.0)
        a[6] = 1.0 if not any(c.doblez for c in p.conjuntos) else kg_et({'ARMADO', 'SOLDEO', 'LIMPIEZA', 'RETRABAJO', 'LISTO_PINTURA',
                                                                          'PINTURA', 'PINTADO', 'ENTREGADO', 'MOVIMIENTO'})
        a[10] = kg_et({'PINTURA', 'PINTADO', 'ENTREGADO'})
        a[11] = kg_et({'PINTADO', 'ENTREGADO'})
        a[12] = kg_et({'ENTREGADO'})
        return np.clip(a, 0.0, 1.0)


def simular(proyectos, paradas, politica=None, eficiencia=1.0):
    return Gemelo(proyectos, paradas, politica, eficiencia).correr()
