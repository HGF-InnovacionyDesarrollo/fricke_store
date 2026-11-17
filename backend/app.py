"""Ecosistema hospitalario — portal de acceso único.

Ejecutar:  python -m uvicorn app:app --app-dir backend --port 8090
"""
import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config as cfg
from plazos import sumar_corridos, sumar_habiles
from db import ahora, auditar, bd, inicializar, verificar_auditoria
from seguridad import (HASH_SEÑUELO, enmascarar_rut, formatear_rut, hash_clave, hash_token,
                       normalizar_rut, nuevo_token, problemas_clave, verificar_clave)

app = FastAPI(title=f"{cfg.NOMBRE_PRODUCTO} — {cfg.NOMBRE_INSTITUCION}", docs_url=None, redoc_url=None)
inicializar()

TIPOS_SOLICITUD = {
    "acceso": "Acceso a mis datos",
    "rectificacion": "Rectificación",
    "supresion": "Supresión",
    "oposicion": "Oposición",
    "portabilidad": "Portabilidad",
    "bloqueo": "Bloqueo temporal del tratamiento",
}


# ------------------------------------------------------------------ cabeceras de seguridad
@app.middleware("http")
async def cabeceras(request: Request, call_next):
    # Protección CSRF simple: toda escritura a la API debe venir con esta cabecera
    # (un formulario de otro sitio no puede ponerla) y la cookie es SameSite=Strict.
    if request.url.path.startswith("/api/") and request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.headers.get("x-ecosistema") != "1":
            return JSONResponse({"detail": "Solicitud no permitida."}, status_code=403)
    r = await call_next(request)
    r.headers["X-Content-Type-Options"] = "nosniff"
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["Referrer-Policy"] = "no-referrer"
    r.headers["Permissions-Policy"] = "camera=(), geolocation=(), microphone=()"
    r.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    if request.url.scheme == "https":
        r.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith("/api/"):
        r.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/static/"):
        r.headers["Cache-Control"] = "no-cache"  # revalida con ETag: las actualizaciones llegan al tiro
    return r


def ip_de(request: Request) -> str:
    return request.client.host if request.client else "?"


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


# ------------------------------------------------------------------ sesión
class Contexto:
    def __init__(self, usuario, sesion, ip):
        self.u, self.s, self.ip = usuario, sesion, ip


def _sesion(request: Request, permitir_bloqueada=False, tocar=True) -> Contexto:
    token = request.cookies.get(cfg.COOKIE_NOMBRE)
    if not token:
        raise HTTPException(401, "Sesión no iniciada.")
    th = hash_token(token)
    with bd() as c:
        s = c.execute("SELECT * FROM sesiones WHERE token_hash=?", (th,)).fetchone()
        if not s:
            raise HTTPException(401, "Sesión no válida.")
        now = datetime.now(timezone.utc)
        inactiva = now - _dt(s["ultima_actividad"]) > timedelta(minutes=cfg.SESION_INACTIVIDAD_MIN)
        if inactiva or now > _dt(s["expira"]):
            c.execute("DELETE FROM sesiones WHERE id=?", (s["id"],))
            c.commit()
            auditar("sesion_expirada", s["usuario_id"], "inactividad" if inactiva else "fin de turno", ip_de(request))
            raise HTTPException(401, "Tu sesión expiró.")
        u = c.execute("SELECT * FROM usuarios WHERE id=? AND activo=1", (s["usuario_id"],)).fetchone()
        if not u:
            raise HTTPException(401, "Cuenta deshabilitada.")
        if s["bloqueada"] and not permitir_bloqueada:
            raise HTTPException(423, "Pantalla bloqueada.")
        if tocar and not s["bloqueada"]:
            c.execute("UPDATE sesiones SET ultima_actividad=? WHERE id=?", (ahora(), s["id"]))
    return Contexto(u, s, ip_de(request))


def sesion(request: Request) -> Contexto:
    return _sesion(request)


def sesion_lista(request: Request) -> Contexto:
    """Sesión que además ya aceptó el aviso vigente y no tiene cambio de clave pendiente."""
    ctx = _sesion(request)
    if ctx.u["debe_cambiar_clave"]:
        raise HTTPException(428, "Debes cambiar tu contraseña.")
    if not _acepto_aviso(ctx.u["id"]):
        raise HTTPException(428, "Debes revisar el aviso de privacidad.")
    return ctx


def _acepto_aviso(uid: int) -> bool:
    with bd() as c:
        return c.execute("SELECT 1 FROM aceptaciones_aviso WHERE usuario_id=? AND version=?",
                         (uid, cfg.VERSION_AVISO)).fetchone() is not None


def _poner_cookie(resp: Response, token: str, segura: bool = False):
    resp.set_cookie(cfg.COOKIE_NOMBRE, token, httponly=True, secure=cfg.COOKIE_SEGURA or segura,
                    samesite="strict", max_age=cfg.SESION_MAXIMA_HORAS * 3600, path="/")


# ------------------------------------------------------------------ autenticación
class Login(BaseModel):
    rut: str = Field(max_length=20)
    clave: str = Field(max_length=200)


ERROR_GENERICO = "RUT o contraseña incorrectos."


@app.post("/api/auth/login")
def login(datos: Login, request: Request, response: Response):
    ip = ip_de(request)
    rut = normalizar_rut(datos.rut)
    if not rut:
        raise HTTPException(400, "El RUT ingresado no es válido.")
    with bd() as c:
        u = c.execute("SELECT * FROM usuarios WHERE rut=?", (rut,)).fetchone()
        if not u or not u["activo"]:
            verificar_clave(datos.clave, HASH_SEÑUELO)  # mismo tiempo de respuesta
            auditar("login_fallido", None, f"rut {enmascarar_rut(rut)}", ip)
            raise HTTPException(401, ERROR_GENERICO)
        if u["bloqueado_hasta"] and _dt(u["bloqueado_hasta"]) > datetime.now(timezone.utc):
            auditar("login_rechazado_bloqueo", u["id"], None, ip)
            raise HTTPException(429, f"Cuenta bloqueada temporalmente por intentos fallidos. "
                                     f"Intenta en {cfg.BLOQUEO_MIN} minutos o llama a {cfg.MESA_AYUDA}.")
        if not verificar_clave(datos.clave, u["clave_hash"]):
            intentos = u["intentos_fallidos"] + 1
            bloqueo = None
            if intentos >= cfg.MAX_INTENTOS:
                bloqueo = (datetime.now(timezone.utc) + timedelta(minutes=cfg.BLOQUEO_MIN)).isoformat(timespec="seconds")
                intentos = 0
            c.execute("UPDATE usuarios SET intentos_fallidos=?, bloqueado_hasta=? WHERE id=?", (intentos, bloqueo, u["id"]))
            c.commit()
            auditar("login_fallido", u["id"], "cuenta bloqueada" if bloqueo else f"intento {intentos}", ip)
            raise HTTPException(401, ERROR_GENERICO)

        token = nuevo_token()
        now = datetime.now(timezone.utc)
        c.execute(
            "INSERT INTO sesiones (token_hash, usuario_id, creada, ultima_actividad, expira, ip, navegador) VALUES (?,?,?,?,?,?,?)",
            (hash_token(token), u["id"], ahora(), ahora(),
             (now + timedelta(hours=cfg.SESION_MAXIMA_HORAS)).isoformat(timespec="seconds"),
             ip, (request.headers.get("user-agent") or "")[:200]),
        )
        c.execute("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?", (u["id"],))
    auditar("login", u["id"], None, ip)
    _poner_cookie(response, token, segura=request.url.scheme == "https")
    return {"ok": True}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(cfg.COOKIE_NOMBRE)
    if token:
        with bd() as c:
            s = c.execute("SELECT usuario_id FROM sesiones WHERE token_hash=?", (hash_token(token),)).fetchone()
            c.execute("DELETE FROM sesiones WHERE token_hash=?", (hash_token(token),))
        if s:
            auditar("logout", s["usuario_id"], None, ip_de(request))
    response.delete_cookie(cfg.COOKIE_NOMBRE, path="/")
    return {"ok": True}


@app.post("/api/auth/bloquear")
def bloquear(request: Request):
    ctx = _sesion(request)
    with bd() as c:
        c.execute("UPDATE sesiones SET bloqueada=1 WHERE id=?", (ctx.s["id"],))
    auditar("pantalla_bloqueada", ctx.u["id"], None, ctx.ip)
    return {"ok": True}


class Desbloqueo(BaseModel):
    clave: str = Field(max_length=200)


@app.post("/api/auth/desbloquear")
def desbloquear(datos: Desbloqueo, request: Request, response: Response):
    ctx = _sesion(request, permitir_bloqueada=True, tocar=False)
    if not verificar_clave(datos.clave, ctx.u["clave_hash"]):
        auditar("desbloqueo_fallido", ctx.u["id"], None, ctx.ip)
        raise HTTPException(401, "Contraseña incorrecta.")
    with bd() as c:
        c.execute("UPDATE sesiones SET bloqueada=0, ultima_actividad=? WHERE id=?", (ahora(), ctx.s["id"]))
    auditar("pantalla_desbloqueada", ctx.u["id"], None, ctx.ip)
    return {"ok": True}


class CambioClave(BaseModel):
    actual: str = Field(max_length=200)
    nueva: str = Field(max_length=200)


@app.post("/api/auth/cambiar-clave")
def cambiar_clave(datos: CambioClave, ctx: Contexto = Depends(sesion)):
    if not verificar_clave(datos.actual, ctx.u["clave_hash"]):
        raise HTTPException(400, "La contraseña actual no es correcta.")
    if datos.actual == datos.nueva:
        raise HTTPException(400, "La nueva contraseña debe ser distinta de la actual.")
    probs = problemas_clave(datos.nueva, ctx.u["rut"], ctx.u["nombre"])
    if probs:
        raise HTTPException(400, " ".join(probs))
    with bd() as c:
        c.execute("UPDATE usuarios SET clave_hash=?, debe_cambiar_clave=0, clave_cambiada_en=? WHERE id=?",
                  (hash_clave(datos.nueva), ahora(), ctx.u["id"]))
        # Cierra todas las demás sesiones abiertas con la clave anterior
        c.execute("DELETE FROM sesiones WHERE usuario_id=? AND id<>?", (ctx.u["id"], ctx.s["id"]))
    auditar("clave_cambiada", ctx.u["id"], None, ctx.ip)
    return {"ok": True}


# ------------------------------------------------------------------ portal
@app.get("/api/salud")
def salud():
    """Para monitores de disponibilidad (Uptime Kuma, Zabbix): no expone datos."""
    try:
        with bd() as c:
            c.execute("SELECT 1").fetchone()
        return {"estado": "ok", "ts": ahora()}
    except Exception:
        return JSONResponse({"estado": "error"}, status_code=503)


@app.get("/api/config")
def configuracion_publica():
    return {
        "institucion": cfg.NOMBRE_INSTITUCION,
        "producto": cfg.NOMBRE_PRODUCTO,
        "mesa_ayuda": cfg.MESA_AYUDA,
        "correo_dpd": cfg.CORREO_DPD,
        "version_aviso": cfg.VERSION_AVISO,
        "inactividad_min": cfg.SESION_INACTIVIDAD_MIN,
        "jefe_servicio": cfg.JEFE_SERVICIO,
        "clave_largo_min": cfg.CLAVE_LARGO_MIN,
    }


def _datos_publicos(u) -> dict:
    return {
        "rut": formatear_rut(u["rut"]),
        "nombre": u["nombre"],
        "correo": u["correo"],
        "cargo": u["cargo"],
        "unidad": u["unidad"],
        "rol": u["rol"],
    }


@app.get("/api/me")
def yo(request: Request):
    ctx = _sesion(request, permitir_bloqueada=True)
    if ctx.s["bloqueada"]:
        # Con la pantalla bloqueada solo se muestra el nombre (quien mira la pantalla no ve más).
        return {"bloqueada": True, "nombre": ctx.u["nombre"]}
    return {
        "bloqueada": False,
        "id": ctx.u["id"],
        **_datos_publicos(ctx.u),
        "debe_cambiar_clave": bool(ctx.u["debe_cambiar_clave"]),
        "debe_aceptar_aviso": not _acepto_aviso(ctx.u["id"]),
        "inactividad_min": cfg.SESION_INACTIVIDAD_MIN,
        "rol_nombre": cfg.ROLES.get(ctx.u["rol"], ctx.u["rol"]),
        "puede_administrar": ctx.u["rol"] in ("admin", "dpd", "seguridad"),
    }


@app.post("/api/privacidad/aceptar")
def aceptar_aviso(ctx: Contexto = Depends(sesion)):
    with bd() as c:
        c.execute("INSERT OR IGNORE INTO aceptaciones_aviso VALUES (?,?,?)", (ctx.u["id"], cfg.VERSION_AVISO, ahora()))
    auditar("aviso_privacidad_leido", ctx.u["id"], cfg.VERSION_AVISO, ctx.ip)
    return {"ok": True}


@app.get("/api/modulos")
def modulos(ctx: Contexto = Depends(sesion_lista)):
    """Solo los módulos que este usuario puede usar (mínimo privilegio)."""
    with bd() as c:
        filas = c.execute(
            """SELECT DISTINCT m.clave, m.nombre, m.descripcion, m.url, m.icono, m.color, m.orden
               FROM modulos m
               LEFT JOIN modulos_rol r ON r.modulo_id=m.id AND r.rol=?
               LEFT JOIN modulos_usuario mu ON mu.modulo_id=m.id AND mu.usuario_id=?
               WHERE m.activo=1 AND (r.rol IS NOT NULL OR mu.usuario_id IS NOT NULL)
                 -- privacidad por diseño: un módulo con datos sensibles no aparece sin evaluación de impacto
                 AND (m.datos_sensibles=0 OR m.eipd_aprobada=1)
               ORDER BY m.orden, m.nombre""",
            (ctx.u["rol"], ctx.u["id"]),
        ).fetchall()
    return [dict(f) for f in filas]


class Pregunta(BaseModel):
    texto: str = Field(max_length=2000)


@app.post("/api/asistente")
def asistente(p: Pregunta, ctx: Contexto = Depends(sesion_lista)):
    """Maqueta del asistente. No guarda el texto de la pregunta (minimización)."""
    auditar("asistente_consulta", ctx.u["id"], f"{len(p.texto)} caracteres", ctx.ip)
    return {"respuesta": "El asistente de IA del hospital aún está en construcción. "
                         "Pronto podrás consultar protocolos, procedimientos y documentos institucionales desde aquí."}


# ------------------------------------------------------------------ mi cuenta (derechos del titular)
ETIQUETAS_ACCION = {
    "login": "Inicio de sesión",
    "logout": "Cierre de sesión",
    "login_fallido": "Intento de acceso fallido",
    "login_rechazado_bloqueo": "Acceso rechazado (cuenta bloqueada)",
    "sesion_expirada": "Sesión cerrada automáticamente",
    "pantalla_bloqueada": "Pantalla bloqueada",
    "pantalla_desbloqueada": "Pantalla desbloqueada",
    "desbloqueo_fallido": "Desbloqueo fallido",
    "clave_cambiada": "Contraseña cambiada",
    "aviso_privacidad_leido": "Aviso de privacidad revisado",
    "datos_exportados": "Descarga de mis datos",
    "solicitud_derecho": "Solicitud de derechos enviada",
    "sesion_cerrada_remota": "Sesión cerrada desde Mi cuenta",
    "asistente_consulta": "Consulta al asistente",
    "usuario_creado": "Cuenta creada",
    "usuario_editado": "Datos de la cuenta modificados",
    "usuario_desbloqueado": "Cuenta desbloqueada por un administrador",
    "clave_restablecida": "Contraseña restablecida por un administrador",
    "sesiones_cerradas_admin": "Sesiones cerradas por un administrador",
    "solicitud_clave": "Pedido de nueva contraseña",
    "solicitud_cuenta": "Solicitud de cuenta",
    "solicitud_cuenta_rechazada": "Solicitud de cuenta rechazada",
    "solicitud_clave_descartada": "Pedido de contraseña descartado",
    "solicitud_derecho_en_revision": "Solicitud de derechos en revisión",
    "solicitud_derecho_respondida": "Solicitud de derechos respondida",
    "solicitud_derecho_rechazada": "Solicitud de derechos rechazada",
    "modulo_guardado": "Módulo guardado",
    "auditoria_consultada": "Bitácora consultada",
    "solicitud_derecho_prorrogada": "Solicitud de derechos prorrogada",
    "incidente_registrado": "Incidente de seguridad registrado",
    "incidente_actualizado": "Incidente de seguridad actualizado",
    "contencion_cerrar_sesiones": "Contención: todas las sesiones cerradas",
    "contencion_forzar_cambio_privilegiadas": "Contención: cambio de clave forzado a cuentas privilegiadas",
    "contencion_suspender_modulos": "Contención: módulos suspendidos",
    "contencion_reanudar_modulos": "Contención: módulos reanudados",
    "contencion_pausar_formularios": "Contención: formularios públicos pausados",
    "contencion_reanudar_formularios": "Contención: formularios públicos reanudados",
    "contencion_rechazada": "Contención rechazada (contraseña incorrecta)",
    "respaldo_realizado": "Respaldo realizado",
    "respaldo_probado": "Restauración de respaldo probada",
    "respaldo_fallido": "Respaldo o prueba fallida",
    "bitacora_archivada": "Bitácora antigua archivada",
    "modulo_registrado": "Módulo registrado desde el código",
    "modulo_actualizado": "Módulo actualizado desde el código",
    "modulo_depurado": "Datos de un módulo eliminados por plazo de conservación",
    "permiso_otorgado": "Permiso de módulo otorgado",
    "permiso_revocado": "Permiso de módulo revocado",
}


@app.get("/api/cuenta/actividad")
def actividad(ctx: Contexto = Depends(sesion_lista)):
    with bd() as c:
        filas = c.execute("SELECT ts, accion, detalle, ip FROM auditoria WHERE usuario_id=? ORDER BY id DESC LIMIT 50",
                          (ctx.u["id"],)).fetchall()
    return [{**dict(f), "etiqueta": ETIQUETAS_ACCION.get(f["accion"], f["accion"])} for f in filas]


@app.get("/api/cuenta/sesiones")
def sesiones(ctx: Contexto = Depends(sesion_lista)):
    with bd() as c:
        filas = c.execute("SELECT id, creada, ultima_actividad, ip, navegador FROM sesiones WHERE usuario_id=? ORDER BY ultima_actividad DESC",
                          (ctx.u["id"],)).fetchall()
    return [{**dict(f), "actual": f["id"] == ctx.s["id"]} for f in filas]


@app.delete("/api/cuenta/sesiones/{sid}")
def cerrar_sesion_remota(sid: int, ctx: Contexto = Depends(sesion_lista)):
    with bd() as c:
        n = c.execute("DELETE FROM sesiones WHERE id=? AND usuario_id=?", (sid, ctx.u["id"])).rowcount
    if n:
        auditar("sesion_cerrada_remota", ctx.u["id"], None, ctx.ip)
    return {"ok": bool(n)}


@app.get("/api/cuenta/exportar")
def exportar(ctx: Contexto = Depends(sesion_lista)):
    """Derecho de acceso y portabilidad: todo lo que el ecosistema guarda de la persona, en JSON."""
    uid = ctx.u["id"]
    with bd() as c:
        datos = {
            "generado_en": ahora(),
            "responsable": cfg.NOMBRE_INSTITUCION,
            "titular": {**_datos_publicos(ctx.u), "cuenta_creada": ctx.u["creado_en"],
                        "clave_cambiada_en": ctx.u["clave_cambiada_en"]},
            "avisos_privacidad_revisados": [dict(f) for f in c.execute(
                "SELECT version, aceptado_en FROM aceptaciones_aviso WHERE usuario_id=?", (uid,))],
            "sesiones_activas": [dict(f) for f in c.execute(
                "SELECT creada, ultima_actividad, ip, navegador FROM sesiones WHERE usuario_id=?", (uid,))],
            "registro_de_actividad": [dict(f) for f in c.execute(
                "SELECT ts, accion, detalle, ip FROM auditoria WHERE usuario_id=? ORDER BY id", (uid,))],
            "solicitudes_de_derechos": [dict(f) for f in c.execute(
                "SELECT tipo, detalle, estado, creada, vence, respuesta FROM solicitudes_derechos WHERE usuario_id=?", (uid,))],
            "nota": "La contraseña no se incluye: se guarda solo como hash irreversible.",
        }
    datos["modulos"] = exportar_modulos(uid)
    auditar("datos_exportados", uid, None, ctx.ip)
    return Response(json.dumps(datos, ensure_ascii=False, indent=2), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="mis_datos.json"'})


class Solicitud(BaseModel):
    tipo: str
    detalle: str = Field(default="", max_length=2000)


@app.post("/api/cuenta/solicitudes")
def nueva_solicitud(s: Solicitud, ctx: Contexto = Depends(sesion_lista)):
    if s.tipo not in TIPOS_SOLICITUD:
        raise HTTPException(400, "Tipo de solicitud no válido.")
    if s.tipo != "acceso" and len(s.detalle.strip()) < 5:
        raise HTTPException(400, "Cuéntanos qué datos o tratamiento afecta tu solicitud.")
    hoy = datetime.now(timezone.utc).date()
    # Ley 21.719 art. 11: 30 días corridos; el bloqueo temporal se responde en 2 días hábiles.
    vence = (sumar_habiles(hoy, 2) if s.tipo == "bloqueo" else sumar_corridos(hoy, cfg.PLAZO_SOLICITUD_DIAS)).isoformat()
    acuse = ahora()
    with bd() as c:
        sid = c.execute("INSERT INTO solicitudes_derechos (usuario_id, tipo, detalle, creada, vence, acuse_en) VALUES (?,?,?,?,?,?)",
                        (ctx.u["id"], s.tipo, s.detalle.strip(), acuse, vence, acuse)).lastrowid
    auditar("solicitud_derecho", ctx.u["id"], f"#{sid} {s.tipo} · acuse de recibo emitido · vence {vence}", ctx.ip)
    return {"id": sid, "vence": vence, "acuse_en": acuse, "dirigida_a": cfg.JEFE_SERVICIO,
            "plazo": "2 días hábiles" if s.tipo == "bloqueo" else f"{cfg.PLAZO_SOLICITUD_DIAS} días corridos"}


@app.get("/api/cuenta/solicitudes")
def mis_solicitudes(ctx: Contexto = Depends(sesion_lista)):
    with bd() as c:
        filas = c.execute("SELECT id, tipo, detalle, estado, creada, vence, respuesta, acuse_en, prorrogada, "
                          "prorroga_motivo, respondida_en FROM solicitudes_derechos "
                          "WHERE usuario_id=? ORDER BY id DESC", (ctx.u["id"],)).fetchall()
    return [{**dict(f), "tipo_nombre": TIPOS_SOLICITUD[f["tipo"]]} for f in filas]


# ------------------------------------------------------------------ administración y solicitudes públicas
# Se importa aquí porque gestion.py usa la sesión y los helpers definidos arriba.
from gestion import router as router_gestion  # noqa: E402

app.include_router(router_gestion)


# ------------------------------------------------------------------ módulos del ecosistema (carpeta modulos/)
from plataforma import REGISTRO, acceso, cargar_modulos, exportar_titular as exportar_modulos  # noqa: E402

cargar_modulos(app, sesion_lista, ETIQUETAS_ACCION)


@app.get("/api/modulos/{clave}/contexto")
def contexto_modulo(clave: str, request: Request):
    """Lo que la cabecera común necesita para pintar un módulo: su identidad y los permisos de la persona."""
    if clave not in REGISTRO:
        raise HTTPException(404, "Módulo no encontrado.")
    ctx = acceso(clave)(sesion_lista(request))
    m = REGISTRO[clave].manifiesto
    return {"clave": m.clave, "nombre": m.nombre, "descripcion": m.descripcion, "icono": m.icono,
            "color": m.color, "version": m.version, "permisos": sorted(ctx.permisos),
            "datos_sensibles": m.tratamiento.datos_sensibles}


# ------------------------------------------------------------------ páginas
def _pagina(nombre: str):
    return FileResponse(cfg.FRONTEND_DIR / nombre, headers={"Cache-Control": "no-store"})


@app.get("/")
def inicio(request: Request):
    if not request.cookies.get(cfg.COOKIE_NOMBRE):
        return RedirectResponse("/ingresar")
    return _pagina("index.html")


@app.get("/ingresar")
def pagina_login():
    return _pagina("login.html")


@app.get("/cuenta")
def pagina_cuenta(request: Request):
    if not request.cookies.get(cfg.COOKIE_NOMBRE):
        return RedirectResponse("/ingresar")
    return _pagina("cuenta.html")


@app.get("/admin")
def pagina_admin(request: Request):
    if not request.cookies.get(cfg.COOKIE_NOMBRE):
        return RedirectResponse("/ingresar")
    return _pagina("admin.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(cfg.FRONTEND_DIR / "favicon.ico", media_type="image/x-icon")


@app.get("/privacidad")
def pagina_privacidad():
    return _pagina("privacidad.html")


app.mount("/static", StaticFiles(directory=cfg.FRONTEND_DIR), name="static")
