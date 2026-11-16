"""Cálculo de plazos legales: días corridos y días hábiles (Chile).

Los feriados se calculan para cualquier año: fijos, Viernes y Sábado Santo, y los que la ley traslada a lunes.
Para casos dudosos (feriados regionales, elecciones), revisar el calendario oficial; ante la duda el plazo
calculado aquí es igual o más corto que el real, nunca más largo.
"""
from datetime import date, timedelta

FIJOS = {(1, 1), (5, 1), (5, 21), (6, 29), (7, 16), (8, 15), (9, 18), (9, 19), (10, 12), (10, 31), (11, 1), (12, 8), (12, 25)}


def _pascua(anio: int) -> date:
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def feriados(anio: int) -> set[date]:
    fs = {date(anio, m, d) for m, d in FIJOS}
    p = _pascua(anio)
    fs |= {p - timedelta(days=2), p - timedelta(days=1)}
    fs.add(date(anio, 6, 20) if anio >= 2021 else date(anio, 6, 21))  # Día de los Pueblos Indígenas (aprox. solsticio)
    return fs


def es_habil(d: date) -> bool:
    return d.weekday() < 5 and d not in feriados(d.year)


def sumar_habiles(desde: date, n: int) -> date:
    d, cuenta = desde, 0
    while cuenta < n:
        d += timedelta(days=1)
        if es_habil(d):
            cuenta += 1
    return d


def sumar_corridos(desde: date, n: int) -> date:
    return desde + timedelta(days=n)
