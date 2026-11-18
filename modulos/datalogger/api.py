"""API de F+data, montada en /api/m/datalogger/. Todo endpoint usa Depends(acceso(...)).

Los datos llegan al importar los CSV de la tarjeta SD de cada equipo (los Monitor T/H no tienen red). Cuando los
equipos puedan enviar datos solos, se necesitará una credencial de equipo común del portal (ver README).
"""
from __future__ import annotations

import csv
import io
import math
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from plataforma import ContextoModulo, acceso, bd_modulo, nombres_de

from .lectura_csv import hora_chile_a_utc, leer_archivo, utc_a_hora_chile, verificar_cadena
from .manifiesto import CLAVE

router = APIRouter()
ANIOS_CONSERVACION = 5
SIN_DATOS_MIN = 75          # igual que el firmware: los sensores reportan cada 40-60 min de noche
BATERIA_BAJA = 20
INTERVALO_MIN = 5           # una fila cada 5 min por sensor
MAX_DIAS_SERIE = 92
DELTA_H_R = 10_000.0        # ΔH/R = 83,144 kJ/mol ÷ 8,3144 J/(mol·K), valor estándar para la temperatura cinética media

VER, IMPORTAR, REVISAR, CONFIGURAR, EQUIPOS = (f"{CLAVE}.{p}" for p in ("ver", "importar", "revisar", "configurar", "equipos"))


# ------------------------------------------------------------------ utilidades
def _f(x):
    return None if x is None else float(x)


def _perfiles(c) -> dict[int, dict]:
    return {p["id"]: {k: (_f(v) if k[1:2] == "_" else v) for k, v in p.items()}
            for p in c.execute("SELECT * FROM perfiles ORDER BY id")}


def _estado_valor(v, p: dict | None, var: str) -> str:
    """normal | atencion | alarma | '' (sin perfil o sin valor). var: 't' o 'h'."""
    if v is None or not p:
        return ""
    amin, amax, vmin, vmax = (p[f"{var}_{k}"] for k in ("alarma_min", "alarma_max", "verde_min", "verde_max"))
    if (amin is not None and v < amin) or (amax is not None and v > amax):
        return "alarma"
    if (vmin is not None and v < vmin) or (vmax is not None and v > vmax):
        return "atencion"
    return "normal"


def _peor(*estados: str) -> str:
    for e in ("alarma", "atencion", "normal"):
        if e in estados:
            return e
    return ""


def _rango(desde: str | None, hasta: str | None, dias_defecto: int = 1) -> tuple[datetime, datetime]:
    """Fechas del navegador (AAAA-MM-DD, días completos en hora de Chile) → UTC."""
    try:
        h = date.fromisoformat(hasta) if hasta else None
        d = date.fromisoformat(desde) if desde else None
    except ValueError:
        raise HTTPException(422, "Revisa las fechas.")
    if h is None and d is None:
        fin = datetime.now(timezone.utc)
        return fin - timedelta(days=dias_defecto), fin
    h = h or date.today()
    d = d or h - timedelta(days=dias_defecto - 1)
    if d > h:
        raise HTTPException(422, "La fecha de inicio debe ser anterior a la de término.")
    if (h - d).days + 1 > MAX_DIAS_SERIE:
        raise HTTPException(422, f"Elige un período de hasta {MAX_DIAS_SERIE} días.")
    return hora_chile_a_utc(f"{d} 00:00:00"), hora_chile_a_utc(f"{h + timedelta(days=1)} 00:00:00")


def _sensor(c, sid: int) -> dict:
    s = c.execute("SELECT s.*, e.codigo AS equipo FROM sensores s JOIN equipos e ON e.id = s.equipo_id WHERE s.id=?",
                  (sid,)).fetchone()
    if not s:
        raise HTTPException(404, "El sensor no existe.")
    return dict(s)


# ------------------------------------------------------------------ resumen
@router.get("/resumen")
def resumen(ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """Último valor de cada sensor activo con su estado, agrupado por equipo."""
    with bd_modulo(CLAVE) as c:
        perfiles = _perfiles(c)
        filas = [dict(f) for f in c.execute("""
            SELECT s.id, s.nombre, s.ubicacion, s.perfil_id, s.equipo_id, e.codigo AS equipo,
                   l.fecha, l.temperatura, l.humedad, l.bateria, l.hora_lectura
            FROM sensores s JOIN equipos e ON e.id = s.equipo_id
            LEFT JOIN LATERAL (SELECT * FROM lecturas WHERE sensor_id = s.id ORDER BY fecha DESC LIMIT 1) l ON TRUE
            WHERE s.activo ORDER BY e.codigo, s.numero NULLS LAST, s.nombre""")]
        pendientes = c.execute("SELECT count(*) FROM excursiones e JOIN sensores s ON s.id = e.sensor_id "
                               "WHERE e.revisada_por IS NULL AND s.activo").fetchone()[0]
        ultima = c.execute("SELECT creado_en, hasta FROM importaciones ORDER BY id DESC LIMIT 1").fetchone()
    equipos: dict[str, dict] = {}
    for f in filas:
        p = perfiles.get(f["perfil_id"])
        t, h = _f(f["temperatura"]), _f(f["humedad"])
        sin_datos = bool(f["fecha"] and f["hora_lectura"]
                         and f["fecha"] - f["hora_lectura"] > timedelta(minutes=SIN_DATOS_MIN))
        estado_t, estado_h = _estado_valor(t, p, "t"), _estado_valor(h, p, "h")
        equipos.setdefault(f["equipo"], {"codigo": f["equipo"], "sensores": []})["sensores"].append({
            "id": f["id"], "nombre": f["nombre"], "ubicacion": f["ubicacion"],
            "perfil": p["nombre"] if p else None, "fecha": f["fecha"], "hora_lectura": f["hora_lectura"],
            "temperatura": t, "humedad": h, "bateria": f["bateria"],
            "estado_t": estado_t, "estado_h": estado_h, "estado": _peor(estado_t, estado_h),
            "sin_datos": sin_datos, "bateria_baja": f["bateria"] is not None and f["bateria"] < BATERIA_BAJA,
        })
    return {"equipos": list(equipos.values()), "alarmas_pendientes": pendientes,
            "ultima_importacion": dict(ultima) if ultima else None}


# ------------------------------------------------------------------ serie, estadísticas e informe
def _estadisticas(valores: list[float], kelvin: bool = False) -> dict:
    if not valores:
        return {"n": 0}
    est = {"n": len(valores), "min": min(valores), "max": max(valores),
           "promedio": round(sum(valores) / len(valores), 2)}
    if kelvin:  # temperatura cinética media (MKT, USP <1079.2>)
        media = sum(math.exp(-DELTA_H_R / (v + 273.15)) for v in valores) / len(valores)
        est["mkt"] = round(DELTA_H_R / -math.log(media) - 273.15, 2)
    return est


@router.get("/sensores/{sid}/serie")
def serie(sid: int, desde: str | None = None, hasta: str | None = None,
          ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """Mediciones del período con estadísticas: mín., máx., promedio, MKT, tiempo en rango y huecos."""
    ini, fin = _rango(desde, hasta)
    with bd_modulo(CLAVE) as c:
        s = _sensor(c, sid)
        p = _perfiles(c).get(s["perfil_id"])
        lecturas = [dict(f) for f in c.execute(
            "SELECT fecha, temperatura, humedad, bateria, hora_lectura FROM lecturas "
            "WHERE sensor_id=? AND fecha >= ? AND fecha < ? ORDER BY fecha", (sid, ini, fin))]
        excursiones = _excursiones(c, "sensor_id=? AND inicio < ? AND (fin IS NULL OR fin >= ?)", (sid, fin, ini))
    for f in lecturas:
        f["temperatura"], f["humedad"] = _f(f["temperatura"]), _f(f["humedad"])
    ts = [f["temperatura"] for f in lecturas if f["temperatura"] is not None]
    hs = [f["humedad"] for f in lecturas if f["humedad"] is not None]
    huecos = []
    for a, b in zip(lecturas, lecturas[1:]):
        if b["fecha"] - a["fecha"] > timedelta(minutes=3 * INTERVALO_MIN):
            huecos.append({"desde": a["fecha"], "hasta": b["fecha"]})
    def en_rango(valores, var):
        return round(100 * sum(_estado_valor(v, p, var) != "alarma" for v in valores) / len(valores), 1) if valores and p else None
    if lecturas:
        esperadas = int((lecturas[-1]["fecha"] - lecturas[0]["fecha"]).total_seconds() // (INTERVALO_MIN * 60)) + 1
        cobertura = round(100 * min(1, len(lecturas) / esperadas), 1)
    else:
        cobertura = None
    return {
        "sensor": s, "perfil": p, "desde": ini, "hasta": fin, "lecturas": lecturas,
        "temperatura": {**_estadisticas(ts, kelvin=True), "en_rango": en_rango(ts, "t")},
        "humedad": {**_estadisticas(hs), "en_rango": en_rango(hs, "h")},
        "cobertura": cobertura, "huecos": huecos[:200], "excursiones": excursiones,
    }


@router.get("/sensores/{sid}/csv")
def descargar(sid: int, desde: str | None = None, hasta: str | None = None,
              ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """Las mediciones del período en CSV para Excel en español (separador ;, coma decimal)."""
    ini, fin = _rango(desde, hasta)
    with bd_modulo(CLAVE) as c:
        s = _sensor(c, sid)
        filas = c.execute("SELECT fecha, temperatura, humedad, bateria, hora_lectura FROM lecturas "
                          "WHERE sensor_id=? AND fecha >= ? AND fecha < ? ORDER BY fecha", (sid, ini, fin)).fetchall()
    def hora(d):
        return utc_a_hora_chile(d).strftime("%Y-%m-%d %H:%M") if d else ""
    def num(x):
        return "" if x is None else str(x).replace(".", ",")
    salida = io.StringIO()
    w = csv.writer(salida, delimiter=";", lineterminator="\r\n")
    w.writerow(["Fecha y hora", "Equipo", "Sensor", "Ubicación", "Temperatura (°C)", "Humedad (%)",
                "Batería (%)", "Hora de la lectura"])
    for f in filas:
        w.writerow([hora(f["fecha"]), s["equipo"], s["nombre"], s["ubicacion"], num(f["temperatura"]),
                    num(f["humedad"]), "" if f["bateria"] is None else f["bateria"], hora(f["hora_lectura"])])
    ctx.auditar(f"{CLAVE}_lecturas_exportadas", f"sensor #{sid}, {len(filas)} mediciones")
    nombre = f"data-{s['equipo']}-{s['ieee'][-4:]}-{ini.date()}.csv"
    return Response("﻿" + salida.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


# ------------------------------------------------------------------ alarmas (excursiones) y su revisión
def _excursiones(c, donde: str, params: tuple) -> list[dict]:
    filas = [dict(f) for f in c.execute(f"""
        SELECT x.*, s.nombre AS sensor, s.ubicacion, e.codigo AS equipo,
               (SELECT max(fecha) FROM lecturas WHERE sensor_id = x.sensor_id) AS ultimo_dato FROM excursiones x
        JOIN sensores s ON s.id = x.sensor_id JOIN equipos e ON e.id = s.equipo_id
        WHERE {donde} ORDER BY x.inicio DESC LIMIT 500""", params)]
    nombres = nombres_de({f["revisada_por"] for f in filas if f["revisada_por"]})
    for f in filas:
        f["extremo"], f["limite"] = _f(f["extremo"]), _f(f["limite"])
        f["revisor"] = nombres.get(f["revisada_por"]) if f["revisada_por"] else None
    return filas


@router.get("/alarmas")
def alarmas(pendientes: bool = True, ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    with bd_modulo(CLAVE) as c:
        return _excursiones(c, "s.activo AND (x.revisada_por IS NULL OR ?::int = 0)", (pendientes,))


class Revision(BaseModel):
    accion: str = Field(min_length=3, max_length=500)


@router.post("/alarmas/{xid}/revision")
def revisar(xid: int, d: Revision, ctx: ContextoModulo = Depends(acceso(CLAVE, REVISAR))):
    with bd_modulo(CLAVE) as c:
        x = c.execute("SELECT revisada_por FROM excursiones WHERE id=?", (xid,)).fetchone()
        if not x:
            raise HTTPException(404, "La alarma no existe.")
        if x["revisada_por"]:
            raise HTTPException(409, "Esta alarma ya tiene una revisión registrada.")
        c.execute("UPDATE excursiones SET revisada_por=?, revisada_en=now(), accion=? WHERE id=?",
                  (ctx.usuario_id, d.accion.strip(), xid))
    ctx.auditar(f"{CLAVE}_alarma_revisada", f"alarma #{xid}")
    return {"ok": True}


def recalcular_excursiones(c, sensor_id: int, desde: datetime):
    """Recalcula los períodos fuera del rango de alarma desde `desde` (un día antes, para no cortar uno en curso).
    Las revisiones ya registradas se conservan."""
    s = c.execute("SELECT perfil_id FROM sensores WHERE id=?", (sensor_id,)).fetchone()
    p = _perfiles(c).get(s["perfil_id"]) if s else None
    if not p:
        return
    ventana = desde - timedelta(days=1)
    abierta = c.execute("SELECT min(inicio) FROM excursiones WHERE sensor_id=? AND inicio < ? AND (fin IS NULL OR fin >= ?)",
                        (sensor_id, ventana, ventana)).fetchone()[0]
    if abierta:
        ventana = abierta
    c.execute("DELETE FROM excursiones WHERE sensor_id=? AND inicio >= ? AND revisada_por IS NULL", (sensor_id, ventana))
    lecturas = c.execute("SELECT fecha, temperatura, humedad FROM lecturas WHERE sensor_id=? AND fecha >= ? ORDER BY fecha",
                         (sensor_id, ventana)).fetchall()
    for variable, col, var in (("temperatura", "temperatura", "t"), ("humedad", "humedad", "h")):
        actual = None
        for f in lecturas:
            v = _f(f[col])
            if v is None:
                continue
            sentido = None
            if p[f"{var}_alarma_max"] is not None and v > p[f"{var}_alarma_max"]:
                sentido = "alta"
            elif p[f"{var}_alarma_min"] is not None and v < p[f"{var}_alarma_min"]:
                sentido = "baja"
            if actual and sentido != actual["sentido"]:
                actual["fin"] = f["fecha"]
                _guardar_excursion(c, sensor_id, variable, actual)
                actual = None
            if sentido and not actual:
                actual = {"sentido": sentido, "inicio": f["fecha"], "fin": None, "extremo": v,
                          "limite": p[f"{var}_alarma_{'max' if sentido == 'alta' else 'min'}"]}
            elif actual:
                actual["extremo"] = max(actual["extremo"], v) if sentido == "alta" else min(actual["extremo"], v)
        if actual:
            _guardar_excursion(c, sensor_id, variable, actual)


def _guardar_excursion(c, sensor_id, variable, x):
    c.execute("""INSERT INTO excursiones (sensor_id, variable, sentido, inicio, fin, extremo, limite)
                 VALUES (?,?,?,?,?,?,?) ON CONFLICT (sensor_id, variable, inicio)
                 DO UPDATE SET fin = EXCLUDED.fin, extremo = EXCLUDED.extremo, sentido = EXCLUDED.sentido""",
              (sensor_id, variable, x["sentido"], x["inicio"], x["fin"], x["extremo"], x["limite"]))


# ------------------------------------------------------------------ equipos y sensores
@router.get("/sensores")
def sensores(ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    with bd_modulo(CLAVE) as c:
        perfiles = _perfiles(c)
        equipos = [dict(e) for e in c.execute("""
            SELECT e.*, (SELECT max(l.fecha) FROM lecturas l JOIN sensores s ON s.id = l.sensor_id
                         WHERE s.equipo_id = e.id) AS ultimo_dato
            FROM equipos e ORDER BY codigo""")]
        lista = [dict(s) for s in c.execute("""
            SELECT s.*, (SELECT max(fecha) FROM lecturas WHERE sensor_id = s.id) AS ultimo_dato
            FROM sensores s ORDER BY s.numero NULLS LAST, s.nombre""")]
    for s in lista:
        s["perfil"] = perfiles.get(s["perfil_id"], {}).get("nombre")
    for e in equipos:
        e["sensores"] = [s for s in lista if s["equipo_id"] == e["id"]]
    return {"equipos": equipos, "perfiles": list(perfiles.values())}


class CambioSensor(BaseModel):
    ubicacion: str = Field(default="", max_length=80)
    activo: bool = True


@router.put("/sensores/{sid}")
def actualizar_sensor(sid: int, d: CambioSensor, ctx: ContextoModulo = Depends(acceso(CLAVE, CONFIGURAR))):
    with bd_modulo(CLAVE) as c:
        _sensor(c, sid)
        c.execute("UPDATE sensores SET ubicacion=?, activo=(?::int = 1) WHERE id=?", (d.ubicacion.strip(), d.activo, sid))
    ctx.auditar(f"{CLAVE}_sensor_actualizado", f"sensor #{sid}{'' if d.activo else ' (fuera de servicio)'}")
    return {"ok": True}


# ------------------------------------------------------------------ configurador por USB
# La conexión con el equipo la hace el navegador (Web Serial): el portal no ve el puerto USB. Este endpoint solo deja
# constancia en la bitácora de lo que se cambió y actualiza la serie y el firmware del equipo si ya existe.
ACCIONES_USB = {
    "hora": "hora puesta desde el PC",
    "emparejar": "red abierta para emparejar",
    "reiniciar": "reiniciado",
    "equipo": "configuración del equipo guardada",
    "sensor": "configuración de un sensor guardada",
    "sensor_quitado": "configuración de un sensor quitada",
    "wifi": "WiFi guardado",
    "wifi_borrado": "WiFi desactivado",
    "clave_leida": "clave de firma leída",
    "respaldo_aplicado": "configuración cargada desde un archivo",
}


class AccionUSB(BaseModel):
    equipo: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9 _.-]+$")
    serie: str = Field(default="", max_length=32, pattern=r"^([0-9A-Fa-f]{8,32})?$")
    firmware: str = Field(default="", max_length=16, pattern=r"^[0-9A-Za-z._-]*$")
    accion: str = Field(max_length=20)


@router.post("/configurador/registro")
def registrar_accion_usb(d: AccionUSB, ctx: ContextoModulo = Depends(acceso(CLAVE, EQUIPOS))):
    if d.accion not in ACCIONES_USB:
        raise HTTPException(422, "Acción no reconocida.")
    codigo = d.equipo.strip()
    with bd_modulo(CLAVE) as c:
        if d.serie or d.firmware:
            c.execute("UPDATE equipos SET serie=COALESCE(NULLIF(?, ''), serie), firmware=COALESCE(NULLIF(?, ''), firmware) "
                      "WHERE codigo=?", (d.serie.upper(), d.firmware, codigo))
    ctx.auditar(f"{CLAVE}_equipo_configurado", f"equipo {codigo}: {ACCIONES_USB[d.accion]}")
    return {"ok": True}


# ------------------------------------------------------------------ eventos de los equipos
@router.get("/eventos")
def eventos(equipo: str | None = None, tipo: str | None = None, desde: str | None = None, hasta: str | None = None,
            ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    ini, fin = _rango(desde, hasta, dias_defecto=30)
    donde, params = ["ev.fecha >= ?", "ev.fecha < ?"], [ini, fin]
    if equipo:
        donde.append("e.codigo = ?"); params.append(equipo[:16])
    if tipo:
        donde.append("ev.tipo = ?"); params.append(tipo[:40].upper())
    with bd_modulo(CLAVE) as c:
        filas = [dict(f) for f in c.execute(f"""
            SELECT ev.id, ev.fecha, ev.tipo, ev.detalle, e.codigo AS equipo FROM eventos ev
            JOIN equipos e ON e.id = ev.equipo_id WHERE {' AND '.join(donde)} ORDER BY ev.fecha DESC LIMIT 1000""",
            tuple(params))]
        tipos = [f[0] for f in c.execute("SELECT DISTINCT tipo FROM eventos ORDER BY tipo")]
    return {"eventos": filas, "tipos": tipos}


# ------------------------------------------------------------------ importación de la tarjeta SD
class ArchivoSD(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    contenido: str = Field(max_length=4_000_000)


class Importacion(BaseModel):
    archivos: list[ArchivoSD] = Field(min_length=1, max_length=62)
    equipo: str = Field(default="", max_length=16, pattern=r"^[A-Za-z0-9_-]*$")   # solo para archivos sin columna Monitor
    clave: str = Field(default="", max_length=64, pattern=r"^[0-9a-fA-F]*$")      # clave de firma: no se guarda


@router.get("/importaciones")
def importaciones(ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    with bd_modulo(CLAVE) as c:
        filas = [dict(f) for f in c.execute("SELECT * FROM importaciones ORDER BY id DESC LIMIT 200")]
    nombres = nombres_de({f["usuario_id"] for f in filas})
    for f in filas:
        f["usuario"] = nombres.get(f["usuario_id"], "—")
    return filas


def _equipo_id(c, codigo: str) -> int:
    fila = c.execute("SELECT id FROM equipos WHERE codigo=?", (codigo,)).fetchone()
    if fila:
        return fila["id"]
    return c.execute("INSERT INTO equipos (codigo) VALUES (?)", (codigo,)).lastrowid


@router.post("/importaciones")
def importar(d: Importacion, ctx: ContextoModulo = Depends(acceso(CLAVE, IMPORTAR))):
    if d.clave and len(d.clave) != 64:
        raise HTTPException(422, "La clave de firma tiene 64 caracteres (0-9 y a-f).")
    leidos = [leer_archivo(a.nombre, a.contenido) for a in d.archivos]
    errores = [f"{a.nombre}: {e}" for a in leidos for e in a.errores]
    validos = [a for a in leidos if a.tipo and a.filas]
    if not validos:
        raise HTTPException(422, errores[0] if errores else "Los archivos no traen mediciones ni eventos.")
    for a in validos:
        if not a.con_monitor:
            if not d.equipo:
                raise HTTPException(422, f"{a.nombre} es de un formato antiguo sin la columna Monitor: "
                                         "elige a qué equipo pertenece.")
            for f in a.filas:
                f["monitor"] = d.equipo
        for f in a.filas:
            if not f["monitor"]:
                f["monitor"] = d.equipo or "SIN-CODIGO"

    # Cadena de firmas: por equipo y registro, con los archivos en orden cronológico
    problemas: list[str] = []
    if d.clave:
        grupos: dict[tuple, list] = {}
        for a in validos:
            grupos.setdefault((a.filas[0]["monitor"], a.tipo), []).append(a)
        for archivos in grupos.values():
            archivos.sort(key=lambda a: a.filas[0]["fecha"])
            problemas += verificar_cadena(bytes.fromhex(d.clave), archivos)

    nuevas = repetidas = eventos_nuevos = 0
    rechazadas = sum(a.rechazadas for a in leidos)
    fechas = [f["fecha"] for a in validos for f in a.filas]
    with bd_modulo(CLAVE) as c:
        perfiles = {p["nombre"].lower(): pid for pid, p in _perfiles(c).items()}
        iid = c.execute("INSERT INTO importaciones (usuario_id, archivos, firmas, problemas_firma, desde, hasta) "
                        "VALUES (?,?,?,?,?,?)",
                        (ctx.usuario_id, len(d.archivos),
                         "sin_verificar" if not d.clave else ("con_problemas" if problemas else "correctas"),
                         len(problemas), min(fechas), max(fechas))).lastrowid
        equipos: dict[str, int] = {}
        sensores: dict[str, int] = {}
        primera_nueva: dict[int, datetime] = {}
        for a in sorted(validos, key=lambda a: a.filas[0]["fecha"]):
            for f in a.filas:
                eid = equipos.get(f["monitor"]) or equipos.setdefault(f["monitor"], _equipo_id(c, f["monitor"]))
                if a.tipo == "eventos":
                    r = c.execute("INSERT INTO eventos (equipo_id, fecha, tipo, detalle, firma, importacion_id) "
                                  "VALUES (?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                                  (eid, f["fecha"], f["tipo"], f["detalle"], f["firma"], iid))
                    eventos_nuevos += r.lastrowid is not None
                    if f["tipo"] == "ARRANQUE":
                        _datos_equipo(c, eid, f["detalle"])
                    continue
                sid = sensores.get(f["ieee"])
                if sid is None:
                    sid = sensores[f["ieee"]] = _sensor_id(c, f, eid, perfiles)
                r = c.execute("""INSERT INTO lecturas (sensor_id, fecha, temperatura, humedad, bateria, hora_lectura,
                                                       corr_t, corr_h, firma, importacion_id)
                                 VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT (sensor_id, fecha) DO NOTHING""",
                              (sid, f["fecha"], f["t"], f["h"], f["bateria"], f["hora_lectura"], f["corr_t"],
                               f["corr_h"], f["firma"], iid))
                if r.lastrowid is None:
                    repetidas += 1
                else:
                    nuevas += 1
                    primera_nueva[sid] = min(primera_nueva.get(sid, f["fecha"]), f["fecha"])
        for sid, desde in primera_nueva.items():
            recalcular_excursiones(c, sid, desde)
        c.execute("UPDATE importaciones SET lecturas_nuevas=?, lecturas_repetidas=?, eventos_nuevos=?, "
                  "filas_rechazadas=? WHERE id=?", (nuevas, repetidas, eventos_nuevos, rechazadas, iid))
    ctx.auditar(f"{CLAVE}_importacion_realizada", f"importación #{iid}")
    return {"id": iid, "lecturas_nuevas": nuevas, "lecturas_repetidas": repetidas, "eventos_nuevos": eventos_nuevos,
            "filas_rechazadas": rechazadas, "archivos_no_reconocidos": errores,
            "firmas": None if not d.clave else {"problemas": len(problemas), "detalle": problemas[:20]}}


def _sensor_id(c, f: dict, equipo_id: int, perfiles: dict[str, int]) -> int:
    """Crea el sensor la primera vez; después actualiza equipo, número, nombre y tipo según el último archivo."""
    perfil = perfiles.get(f["almacenamiento"].lower())
    fila = c.execute("SELECT id FROM sensores WHERE ieee=?", (f["ieee"],)).fetchone()
    if fila:
        c.execute("UPDATE sensores SET equipo_id=?, numero=?, nombre=?, perfil_id=coalesce(?, perfil_id) WHERE id=?",
                  (equipo_id, f["numero"], f["nombre"], perfil, fila["id"]))
        return fila["id"]
    return c.execute("INSERT INTO sensores (ieee, equipo_id, numero, nombre, perfil_id) VALUES (?,?,?,?,?)",
                     (f["ieee"], equipo_id, f["numero"], f["nombre"], perfil)).lastrowid


def _datos_equipo(c, equipo_id: int, detalle: str):
    """El evento ARRANQUE trae "MTH-01 serie 98A316FFFE9BB2EC firmware 2.0, motivo: ..."."""
    partes = detalle.replace(",", " ").split()
    for clave_dato, col in (("serie", "serie"), ("firmware", "firmware")):
        if clave_dato in partes and partes.index(clave_dato) + 1 < len(partes):
            valor = partes[partes.index(clave_dato) + 1][:20]
            if col == "serie" and not (8 <= len(valor) <= 32 and all(ch in "0123456789ABCDEF" for ch in valor)):
                continue
            c.execute(f"UPDATE equipos SET {col}=? WHERE id=?", (valor, equipo_id))


# ------------------------------------------------------------------ Ley 21.719 (guarda ids de funcionarios)
def exportar_titular(usuario_id: int) -> dict:
    """Lo que F+data guarda de la persona. Se suma a 'Descargar mis datos' en Mi cuenta."""
    with bd_modulo(CLAVE) as c:
        return {
            "importaciones": [dict(f) for f in c.execute(
                "SELECT id, creado_en, archivos, lecturas_nuevas, eventos_nuevos FROM importaciones "
                "WHERE usuario_id=? ORDER BY id", (usuario_id,))],
            "revisiones_de_alarmas": [dict(f) for f in c.execute(
                "SELECT id, revisada_en, accion FROM excursiones WHERE revisada_por=? ORDER BY id", (usuario_id,))],
        }


def depurar() -> int:
    """Aplica el plazo de conservación (5 años). Devuelve cuántos registros eliminó."""
    plazo = (ANIOS_CONSERVACION * 365 + 1,)
    limite = "now() - make_interval(days => ?)"
    with bd_modulo(CLAVE) as c:
        n = c.execute(f"DELETE FROM excursiones WHERE coalesce(revisada_en, inicio) < {limite} "
                      f"AND coalesce(fin, inicio) < {limite}", plazo * 2).rowcount
        n += c.execute(f"DELETE FROM lecturas WHERE fecha < {limite}", plazo).rowcount
        n += c.execute(f"DELETE FROM eventos WHERE fecha < {limite}", plazo).rowcount
        n += c.execute(f"""DELETE FROM importaciones i WHERE creado_en < {limite}
                           AND NOT EXISTS (SELECT 1 FROM lecturas WHERE importacion_id = i.id)
                           AND NOT EXISTS (SELECT 1 FROM eventos WHERE importacion_id = i.id)""", plazo).rowcount
        return n
