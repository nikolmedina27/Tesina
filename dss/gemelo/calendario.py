"""Calendario laboral del gemelo: turnos, feriados de Perú y ventanas de trabajo por recurso.

El tiempo del gemelo se mide en horas desde EPOCA (2019-01-01 00:00). Cada recurso (máquina, cuadrilla, grúa)
trabaja solo dentro de sus ventanas: turno normal 07:00-15:00 de lunes a sábado, sin feriados; las palancas de
gestión agregan ventanas (horas extra 15:00-17:00, segundo turno 15:00-23:00) y las paradas de máquina las quitan.
`Ventanas.avanzar(t, h)` devuelve cuándo termina un trabajo de h horas que empieza en t.
"""
from datetime import date, timedelta

import numpy as np

EPOCA = date(2019, 1, 1)
FIN = date(2027, 12, 31)
TURNO = (7.0, 15.0)
HORAS_EXTRA = (15.0, 17.0)
SEGUNDO_TURNO = (15.0, 23.0)
GRUA = (6.0, 23.0)


def pascua(anio):
    """Domingo de Pascua (algoritmo de Gauss/Meeus)."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    mes = (h + l_ - 7 * m + 114) // 31
    dia = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def feriados(anio):
    """Feriados nacionales de Perú que paran la planta (los principales)."""
    fijos = [(1, 1), (5, 1), (6, 29), (7, 28), (7, 29), (8, 30), (10, 8), (11, 1), (12, 8), (12, 25)]
    p = pascua(anio)
    return {date(anio, m, d) for m, d in fijos} | {p - timedelta(days=3), p - timedelta(days=2)}


_FERIADOS = set().union(*(feriados(a) for a in range(EPOCA.year, FIN.year + 1)))


def es_laborable(d):
    return d.weekday() < 6 and d not in _FERIADOS


DIAS = [EPOCA + timedelta(days=i) for i in range((FIN - EPOCA).days + 1)]
LABORABLES = [d for d in DIAS if es_laborable(d)]
_IDX_DIA = {d: i for i, d in enumerate(DIAS)}


def hora(d, h=0.0):
    """Hora absoluta (desde EPOCA) de la fecha d a las h horas."""
    return (d - EPOCA).days * 24.0 + h


def fecha(t):
    """Fecha del instante t (horas desde EPOCA)."""
    return EPOCA + timedelta(days=int(t // 24))


def a_fecha(s):
    return date.fromisoformat(str(s)[:10])


def ventanas_dia(desde, hasta, tramo, dias=None):
    """Lista de ventanas (inicio, fin) del tramo horario en los días laborables entre desde y hasta (inclusive)."""
    dias = LABORABLES if dias is None else dias
    a, b = tramo
    return [(hora(d, a), hora(d, b)) for d in dias if desde <= d <= hasta]


class Ventanas:
    """Conjunto de intervalos de trabajo disjuntos y ordenados, con suma acumulada para avanzar en O(log n)."""

    def __init__(self, intervalos):
        self._fijar(intervalos)

    def _fijar(self, intervalos):
        iv = sorted((float(a), float(b)) for a, b in intervalos if b > a)
        fusion = []
        for a, b in iv:
            if fusion and a <= fusion[-1][1] + 1e-9:
                fusion[-1][1] = max(fusion[-1][1], b)
            else:
                fusion.append([a, b])
        arr = np.array(fusion, float) if fusion else np.zeros((0, 2))
        self.ini, self.fin = arr[:, 0].copy(), arr[:, 1].copy()
        largo = self.fin - self.ini
        self.cum = np.concatenate([[0.0], np.cumsum(largo)])          # horas antes de cada ventana

    def intervalos(self):
        return list(zip(self.ini.tolist(), self.fin.tolist()))

    def agregar(self, intervalos):
        self._fijar(self.intervalos() + list(intervalos))

    def quitar(self, intervalos):
        """Resta intervalos (paradas de máquina)."""
        out = self.intervalos()
        for a, b in sorted(intervalos):
            nuevo = []
            for x, y in out:
                if b <= x or a >= y:
                    nuevo.append((x, y))
                else:
                    if x < a:
                        nuevo.append((x, a))
                    if b < y:
                        nuevo.append((b, y))
            out = nuevo
        self._fijar(out)

    def acumulado(self, t):
        """Horas de trabajo disponibles entre el inicio del calendario y t."""
        i = int(np.searchsorted(self.ini, t, side='right')) - 1
        if i < 0:
            return 0.0
        return float(self.cum[i] + min(t, self.fin[i]) - self.ini[i])

    def inicio_desde(self, t):
        """Primer instante de trabajo >= t."""
        i = int(np.searchsorted(self.fin, t, side='right'))
        if i >= len(self.ini):
            return float('inf')
        return max(t, float(self.ini[i]))

    def avanzar(self, t, horas):
        """Instante en que se completan `horas` de trabajo empezando en t."""
        if horas <= 0:
            return self.inicio_desde(t)
        objetivo = self.acumulado(t) + horas
        j = int(np.searchsorted(self.cum[1:], objetivo - 1e-12, side='left'))
        if j >= len(self.ini):
            return float('inf')
        return float(self.ini[j] + objetivo - self.cum[j])

    def trabajado(self, t0, t1):
        return max(0.0, self.acumulado(t1) - self.acumulado(t0))

    def por_dia(self, t0, t1):
        """Horas trabajadas entre t0 y t1 repartidas por fecha: {fecha: horas}."""
        out = {}
        i = int(np.searchsorted(self.fin, t0, side='right'))
        while i < len(self.ini) and self.ini[i] < t1:
            a, b = max(self.ini[i], t0), min(self.fin[i], t1)
            if b > a:
                d = fecha(a)
                out[d] = out.get(d, 0.0) + (b - a)
            i += 1
        return out


def turno_base(desde=EPOCA, hasta=FIN, tramo=TURNO):
    return Ventanas(ventanas_dia(desde, hasta, tramo))
