"""Lectura de los CSV que graban los data logger en su tarjeta SD (Monitor T/H, firmware 1.x y 2.x).

Formatos que reconoce, por los nombres de las columnas (no por su posición):
  - datos:   Fecha y hora;[Monitor;]Sensor;Nombre;Almacenamiento;IEEE;Temperatura (°C);Humedad (%);
             [Corrección T (°C);Corrección HR (%);]Batería (%);Hora de la lectura;Firma
  - eventos: Fecha y hora;[Monitor;]Tipo;Detalle;Firma
  - los archivos antiguos (antes del 25 sep 2026) separados por coma y con punto decimal.

Cada fila termina en una firma HMAC-SHA256 (16 hex) encadenada con la fila anterior del mismo registro. Si
se entrega la clave de la placa, se verifica la cadena; la clave nunca se guarda ni va a la bitácora.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

CEROS = "0" * 16
_FECHA = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
_FIRMA = re.compile(r"[0-9a-f]{16}")


# ------------------------------------------------------------------ hora de Chile (la misma regla del firmware)
def _primer_sabado(anio: int, mes: int) -> datetime:
    d = datetime(anio, mes, 1)
    return d + timedelta(days=(5 - d.weekday()) % 7)


def hora_chile_a_utc(texto: str) -> datetime:
    """Hora local del equipo → UTC. El firmware usa TZ "<-04>4<-03>,M9.1.6/24,M4.1.6/24": horario de verano
    (UTC-3) desde el primer sábado de septiembre a las 24:00 hasta el primer sábado de abril a las 24:00."""
    local = datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
    inicio_verano = _primer_sabado(local.year, 9) + timedelta(days=1)   # sábado 24:00 = domingo 00:00
    fin_verano = _primer_sabado(local.year, 4) + timedelta(days=1)
    verano = local >= inicio_verano or local < fin_verano
    return (local + timedelta(hours=3 if verano else 4)).replace(tzinfo=timezone.utc)


def utc_a_hora_chile(utc: datetime) -> datetime:
    """UTC → hora local de Chile (sin zona), con la misma regla."""
    for horas in (3, 4):
        local = (utc.astimezone(timezone.utc) - timedelta(hours=horas)).replace(tzinfo=None)
        if hora_chile_a_utc(local.strftime("%Y-%m-%d %H:%M:%S")) == utc.astimezone(timezone.utc).replace(microsecond=0):
            return local
    return (utc.astimezone(timezone.utc) - timedelta(hours=3)).replace(tzinfo=None)


# ------------------------------------------------------------------ archivos
def _normalizar(columna: str) -> str:
    s = unicodedata.normalize("NFKD", columna).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s*\(.*?\)\s*", "", s).strip()


COLUMNAS_DATOS = {"fecha y hora": "fecha", "monitor": "monitor", "sensor": "numero", "nombre": "nombre",
                  "almacenamiento": "almacenamiento", "ieee": "ieee", "temperatura": "t", "humedad": "h",
                  "correccion t": "corr_t", "correccion hr": "corr_h", "bateria": "bateria",
                  "hora de la lectura": "hora_lectura", "firma": "firma"}
COLUMNAS_EVENTOS = {"fecha y hora": "fecha", "monitor": "monitor", "tipo": "tipo", "detalle": "detalle",
                    "firma": "firma"}


@dataclass
class Archivo:
    nombre: str
    tipo: str = ""                  # "datos" | "eventos" | "" (no reconocido)
    filas: list[dict] = field(default_factory=list)
    rechazadas: int = 0
    errores: list[str] = field(default_factory=list)
    con_monitor: bool = False
    # (cuerpo firmado, firma, número de línea) en el orden del archivo, para verificar la cadena
    cadena: list[tuple[str, str, int]] = field(default_factory=list)


def _numero(texto: str, decimal_coma: bool) -> float | None:
    texto = texto.strip()
    if not texto:
        return None
    return float(texto.replace(",", ".") if decimal_coma else texto)


def leer_archivo(nombre: str, contenido: str) -> Archivo:
    """Interpreta un CSV de la SD. No lanza errores: lo que no entiende queda en `errores` o `rechazadas`."""
    a = Archivo(nombre=nombre)
    lineas = contenido.lstrip("﻿").splitlines()
    if not lineas:
        a.errores.append("el archivo está vacío")
        return a
    separador = ";" if ";" in lineas[0] else ","
    decimal_coma = separador == ";"
    columnas = [_normalizar(c) for c in lineas[0].split(separador)]
    if "tipo" in columnas and "detalle" in columnas:
        a.tipo, mapa = "eventos", COLUMNAS_EVENTOS
    elif "ieee" in columnas and "temperatura" in columnas:
        a.tipo, mapa = "datos", COLUMNAS_DATOS
    else:
        a.errores.append("no parece un archivo de datos ni de eventos de un data logger")
        return a
    if columnas[-1] != "firma":
        a.errores.append("falta la columna Firma")
        a.tipo = ""
        return a
    campos = [mapa.get(c, "") for c in columnas]
    a.con_monitor = "monitor" in campos
    for n, linea in enumerate(lineas[1:], start=2):
        if not linea.strip():
            continue
        cuerpo, _, firma = linea.rpartition(separador)
        # El detalle de un evento podría traer el separador: se corta solo lo necesario desde la izquierda.
        valores = cuerpo.split(separador, len(campos) - 2) + [firma]
        if len(valores) != len(campos):
            a.rechazadas += 1
            continue
        crudo = dict(zip(campos, (v.strip() for v in valores)))
        try:
            fila = _fila_datos(crudo, decimal_coma) if a.tipo == "datos" else _fila_evento(crudo)
        except (ValueError, KeyError):
            a.rechazadas += 1
            continue
        fila["linea"] = n
        a.filas.append(fila)
        a.cadena.append((cuerpo, firma.strip(), n))
    return a


def _fecha(texto: str) -> datetime:
    if not _FECHA.fullmatch(texto):
        raise ValueError("fecha")
    return hora_chile_a_utc(texto)


def _firma(texto: str) -> str | None:
    return texto if _FIRMA.fullmatch(texto) else None


def _fila_datos(c: dict, decimal_coma: bool) -> dict:
    ieee = re.sub(r"[^0-9A-Fa-f]", "", c["ieee"]).upper()
    if len(ieee) != 16:
        raise ValueError("ieee")
    t, h = _numero(c.get("t", ""), decimal_coma), _numero(c.get("h", ""), decimal_coma)
    if t is not None and not -80 <= t <= 100 or h is not None and not 0 <= h <= 100:
        raise ValueError("fuera de rango físico")
    bat = _numero(c.get("bateria", ""), decimal_coma)
    hl = c.get("hora_lectura", "")
    return {
        "fecha": _fecha(c["fecha"]), "monitor": c.get("monitor", ""), "ieee": ieee,
        "numero": int(c["numero"]) if c.get("numero", "").isdigit() else None,
        "nombre": (c.get("nombre") or ieee[-4:])[:40], "almacenamiento": c.get("almacenamiento", ""),
        "t": t, "h": h, "bateria": int(bat) if bat is not None and 0 <= bat <= 100 else None,
        "hora_lectura": _fecha(hl) if hl else None,
        "corr_t": _numero(c.get("corr_t", ""), decimal_coma), "corr_h": _numero(c.get("corr_h", ""), decimal_coma),
        "firma": _firma(c["firma"]),
    }


def _fila_evento(c: dict) -> dict:
    tipo = c["tipo"].upper()
    if not re.fullmatch(r"[A-Z0-9_]{2,40}", tipo):
        raise ValueError("tipo")
    return {"fecha": _fecha(c["fecha"]), "monitor": c.get("monitor", ""), "tipo": tipo,
            "detalle": c.get("detalle", "")[:300], "firma": _firma(c["firma"])}


# ------------------------------------------------------------------ firmas
def firma(clave: bytes, previa: str, cuerpo: str) -> str:
    return hmac.new(clave, (previa + cuerpo).encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def verificar_cadena(clave: bytes, archivos: list[Archivo]) -> list[str]:
    """Verifica la cadena de firmas de un registro (datos o eventos de un mismo equipo), con los archivos en
    orden cronológico. La primera fila se acepta como inicio. Devuelve los problemas ("archivo, línea N")."""
    problemas, previa = [], None
    for a in archivos:
        for cuerpo, firmada, n in a.cadena:
            if previa is not None and firma(clave, previa, cuerpo) != firmada:
                problemas.append(f"{a.nombre}, línea {n}")
            previa = firmada
    return problemas
