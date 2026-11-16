"""Gestión del ecosistema: solicitudes públicas (crear cuenta, recuperar clave) y consola de administración.

Se importa al final de app.py, cuando la sesión y los helpers ya están definidos.
"""
import re
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

import config as cfg
from app import TIPOS_SOLICITUD, Contexto, ETIQUETAS_ACCION, ip_de, sesion_lista
from db import ahora, auditar, bd, verificar_auditoria
from seguridad import clave_temporal, enmascarar_rut, formatear_rut, hash_clave, normalizar_rut

router = APIRouter()

MENSAJE_CUENTA = ("Recibimos tu solicitud. Un administrador la revisará y te contactará para entregarte "
                  "tu contraseña temporal en forma presencial.")
MENSAJE_CLAVE = ("Si el RUT corresponde a una cuenta activa, avisamos a la Mesa de ayuda. Te contactarán "
                 "para entregarte una contraseña temporal; ten a mano tu cédula de identidad.")


# ------------------------------------------------------------------ límite por IP (endpoints públicos)
_intentos: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def limitar(request: Request, clave: str):
    ip = ip_de(request)
    ventana = cfg.VENTANA_PUBLICO_MIN * 60
    with _lock:
        q = _intentos[f"{clave}:{ip}"]
        ahora_s = time.monotonic()
        while q and ahora_s - q[0] > ventana:
            q.popleft()
        if len(q) >= cfg.LIMITE_PUBLICO:
            raise HTTPException(429, f"Demasiadas solicitudes desde este equipo. Intenta en {cfg.VENTANA_PUBLICO_MIN} minutos.")
        q.append(ahora_s)


def _texto(v: str | None, largo: int) -> str:
    return re.sub(r"\s+", " ", (v or "")).strip()[:largo]


def _validar_correo(correo: str) -> str:
    correo = correo.strip().lower()
    if correo and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", correo):
        raise HTTPException(400, "El correo no es válido.")
    if cfg.DOMINIO_CORREO and not correo.endswith("@" + cfg.DOMINIO_CORREO):
        raise HTTPException(400, f"Usa tu correo institucional (@{cfg.DOMINIO_CORREO}).")
    return correo


# ------------------------------------------------------------------ público
class SolicitudCuenta(BaseModel):
    rut: str = Field(max_length=20)
    nombre: str = Field(max_length=120)
    correo: str = Field(default="", max_length=120)
    cargo: str = Field(default="", max_length=80)
    unidad: str = Field(default="", max_length=80)
    motivo: str = Field(default="", max_length=500)


@router.post("/api/publico/solicitar-cuenta")
def solicitar_cuenta(s: SolicitudCuenta, request: Request):
    limitar(request, "cuenta")
    rut = normalizar_rut(s.rut)
    if not rut:
        raise HTTPException(400, "El RUT ingresado no es válido.")
    nombre = _texto(s.nombre, 120)
    if len(nombre.split()) < 2:
        raise HTTPException(400, "Escribe tu nombre y apellido.")
    correo = _validar_correo(s.correo)
    ip = ip_de(request)
    with bd() as c:
        existe = c.execute("SELECT 1 FROM usuarios WHERE rut=?", (rut,)).fetchone()
        pendiente = c.execute("SELECT 1 FROM solicitudes_cuenta WHERE rut=? AND estado='pendiente'", (rut,)).fetchone()
        if not existe and not pendiente:
            c.execute("INSERT INTO solicitudes_cuenta (rut, nombre, correo, cargo, unidad, motivo, creada, ip) VALUES (?,?,?,?,?,?,?,?)",
                      (rut, nombre, correo, _texto(s.cargo, 80), _texto(s.unidad, 80), _texto(s.motivo, 500), ahora(), ip))
    # Misma respuesta siempre: no revela si el RUT ya tiene cuenta.
    auditar("solicitud_cuenta", None, f"rut {enmascarar_rut(rut)}" + (" (duplicada)" if existe or pendiente else ""), ip)
    return {"mensaje": MENSAJE_CUENTA}


class SolicitudClave(BaseModel):
    rut: str = Field(max_length=20)


@router.post("/api/publico/recuperar-clave")
def recuperar_clave(s: SolicitudClave, request: Request):
    limitar(request, "clave")
    rut = normalizar_rut(s.rut)
    if not rut:
        raise HTTPException(400, "El RUT ingresado no es válido.")
    ip = ip_de(request)
    with bd() as c:
        u = c.execute("SELECT id FROM usuarios WHERE rut=? AND activo=1", (rut,)).fetchone()
        if u and not c.execute("SELECT 1 FROM solicitudes_clave WHERE usuario_id=? AND estado='pendiente'", (u["id"],)).fetchone():
            c.execute("INSERT INTO solicitudes_clave (usuario_id, creada, ip) VALUES (?,?,?)", (u["id"], ahora(), ip))
    auditar("solicitud_clave", u["id"] if u else None, None if u else f"rut {enmascarar_rut(rut)} sin cuenta", ip)
    return {"mensaje": MENSAJE_CLAVE}


# ------------------------------------------------------------------ permisos
def solo_admin(ctx: Contexto = Depends(sesion_lista)) -> Contexto:
    if ctx.u["rol"] != "admin":
        raise HTTPException(403, "Necesitas perfil de administrador.")
    return ctx


def admin_o_dpd(ctx: Contexto = Depends(sesion_lista)) -> Contexto:
    if ctx.u["rol"] not in ("admin", "dpd"):
        raise HTTPException(403, "Necesitas perfil de administrador o de Delegado de Protección de Datos.")
    return ctx


def _usuario_dict(u) -> dict:
    return {
        "id": u["id"], "rut": formatear_rut(u["rut"]), "nombre": u["nombre"], "correo": u["correo"],
        "cargo": u["cargo"], "unidad": u["unidad"], "rol": u["rol"], "activo": bool(u["activo"]),
        "debe_cambiar_clave": bool(u["debe_cambiar_clave"]), "bloqueado_hasta": u["bloqueado_hasta"],
        "creado_en": u["creado_en"], "clave_cambiada_en": u["clave_cambiada_en"],
    }


# ------------------------------------------------------------------ resumen
@router.get("/api/admin/resumen")
def resumen(ctx: Contexto = Depends(admin_o_dpd)):
    with bd() as c:
        n = lambda q: c.execute(q).fetchone()[0]  # noqa: E731
        return {
            "rol": ctx.u["rol"],
            "roles": cfg.ROLES,
            "usuarios_activos": n("SELECT COUNT(*) FROM usuarios WHERE activo=1"),
            "sesiones_abiertas": n("SELECT COUNT(DISTINCT usuario_id) FROM sesiones"),
            "solicitudes_cuenta": n("SELECT COUNT(*) FROM solicitudes_cuenta WHERE estado='pendiente'"),
            "solicitudes_clave": n("SELECT COUNT(*) FROM solicitudes_clave WHERE estado='pendiente'"),
            "derechos_pendientes": n("SELECT COUNT(*) FROM solicitudes_derechos WHERE estado IN ('recibida','en_revision')"),
            "derechos_vencidos": n("SELECT COUNT(*) FROM solicitudes_derechos WHERE estado IN ('recibida','en_revision') AND vence < date('now')"),
            "modulos": n("SELECT COUNT(*) FROM modulos"),
            "fallidos_24h": n("SELECT COUNT(*) FROM auditoria WHERE accion='login_fallido' AND ts > datetime('now','-1 day')"),
        }


# ------------------------------------------------------------------ usuarios
@router.get("/api/admin/usuarios")
def listar_usuarios(q: str = "", ctx: Contexto = Depends(solo_admin)):
    patron = f"%{q.strip()}%"
    rut_q = re.sub(r"[^0-9kK]", "", q)
    with bd() as c:
        filas = c.execute(
            """SELECT * FROM usuarios WHERE nombre LIKE ? OR unidad LIKE ? OR cargo LIKE ?
               OR (? <> '' AND replace(rut,'-','') LIKE ?) ORDER BY activo DESC, nombre LIMIT 300""",
            (patron, patron, patron, rut_q, f"%{rut_q}%"),
        ).fetchall()
        sesiones = {r[0] for r in c.execute("SELECT DISTINCT usuario_id FROM sesiones")}
    return [{**_usuario_dict(u), "en_linea": u["id"] in sesiones} for u in filas]


class NuevoUsuario(BaseModel):
    rut: str = Field(max_length=20)
    nombre: str = Field(max_length=120)
    correo: str = Field(default="", max_length=120)
    cargo: str = Field(default="", max_length=80)
    unidad: str = Field(default="", max_length=80)
    rol: str = "funcionario"


def _crear_usuario(c, rut, nombre, correo, cargo, unidad, rol) -> tuple[int, str]:
    if rol not in cfg.ROLES:
        raise HTTPException(400, "Perfil no válido.")
    if c.execute("SELECT 1 FROM usuarios WHERE rut=?", (rut,)).fetchone():
        raise HTTPException(409, "Ya existe una cuenta con ese RUT.")
    clave = clave_temporal()
    uid = c.execute(
        "INSERT INTO usuarios (rut, nombre, correo, cargo, unidad, rol, clave_hash, creado_en) VALUES (?,?,?,?,?,?,?,?)",
        (rut, nombre, correo or None, cargo or None, unidad or None, rol, hash_clave(clave), ahora()),
    ).lastrowid
    return uid, clave


@router.post("/api/admin/usuarios")
def crear_usuario(d: NuevoUsuario, ctx: Contexto = Depends(solo_admin)):
    rut = normalizar_rut(d.rut)
    if not rut:
        raise HTTPException(400, "El RUT ingresado no es válido.")
    nombre = _texto(d.nombre, 120)
    if not nombre:
        raise HTTPException(400, "Falta el nombre.")
    with bd() as c:
        uid, clave = _crear_usuario(c, rut, nombre, _validar_correo(d.correo), _texto(d.cargo, 80), _texto(d.unidad, 80), d.rol)
    auditar("usuario_creado", uid, f"por usuario #{ctx.u['id']}", ctx.ip)
    return {"id": uid, "rut": formatear_rut(rut), "nombre": nombre, "clave_temporal": clave}


class CambiosUsuario(BaseModel):
    nombre: str | None = Field(default=None, max_length=120)
    correo: str | None = Field(default=None, max_length=120)
    cargo: str | None = Field(default=None, max_length=80)
    unidad: str | None = Field(default=None, max_length=80)
    rol: str | None = None
    activo: bool | None = None


@router.patch("/api/admin/usuarios/{uid}")
def editar_usuario(uid: int, d: CambiosUsuario, ctx: Contexto = Depends(solo_admin)):
    cambios = {k: v for k, v in d.model_dump().items() if v is not None}
    if uid == ctx.u["id"] and (cambios.get("activo") is False or cambios.get("rol", "admin") != "admin"):
        raise HTTPException(400, "No puedes desactivar tu propia cuenta ni quitarte el perfil de administrador.")
    if "rol" in cambios and cambios["rol"] not in cfg.ROLES:
        raise HTTPException(400, "Perfil no válido.")
    if "correo" in cambios:
        cambios["correo"] = _validar_correo(cambios["correo"]) or None
    for k in ("nombre", "cargo", "unidad"):
        if k in cambios:
            cambios[k] = _texto(cambios[k], 120) or None
    if cambios.get("nombre", "x") is None:
        raise HTTPException(400, "El nombre no puede quedar vacío.")
    if "activo" in cambios:
        cambios["activo"] = int(cambios["activo"])
    if not cambios:
        return {"ok": True}
    with bd() as c:
        if not c.execute("SELECT 1 FROM usuarios WHERE id=?", (uid,)).fetchone():
            raise HTTPException(404, "No existe la cuenta.")
        sets = ", ".join(f"{k}=?" for k in cambios)
        c.execute(f"UPDATE usuarios SET {sets} WHERE id=?", (*cambios.values(), uid))
        if cambios.get("activo") == 0 or "rol" in cambios:
            c.execute("DELETE FROM sesiones WHERE usuario_id=?", (uid,))
    auditar("usuario_editado", uid, f"{', '.join(cambios)} por usuario #{ctx.u['id']}", ctx.ip)
    return {"ok": True}


def _restablecer(c, uid: int) -> str:
    clave = clave_temporal()
    n = c.execute("UPDATE usuarios SET clave_hash=?, debe_cambiar_clave=1, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?",
                  (hash_clave(clave), uid)).rowcount
    if not n:
        raise HTTPException(404, "No existe la cuenta.")
    c.execute("DELETE FROM sesiones WHERE usuario_id=?", (uid,))
    return clave


@router.post("/api/admin/usuarios/{uid}/restablecer")
def restablecer(uid: int, ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        clave = _restablecer(c, uid)
        c.execute("UPDATE solicitudes_clave SET estado='atendida', resuelta_por=?, resuelta_en=? WHERE usuario_id=? AND estado='pendiente'",
                  (ctx.u["id"], ahora(), uid))
    auditar("clave_restablecida", uid, f"por usuario #{ctx.u['id']}", ctx.ip)
    return {"clave_temporal": clave}


@router.post("/api/admin/usuarios/{uid}/desbloquear")
def desbloquear(uid: int, ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        c.execute("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?", (uid,))
    auditar("usuario_desbloqueado", uid, f"por usuario #{ctx.u['id']}", ctx.ip)
    return {"ok": True}


@router.post("/api/admin/usuarios/{uid}/cerrar-sesiones")
def cerrar_sesiones(uid: int, ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        n = c.execute("DELETE FROM sesiones WHERE usuario_id=? AND id<>?", (uid, ctx.s["id"])).rowcount
    auditar("sesiones_cerradas_admin", uid, f"{n} sesiones, por usuario #{ctx.u['id']}", ctx.ip)
    return {"cerradas": n}


# ------------------------------------------------------------------ solicitudes de cuenta
@router.get("/api/admin/solicitudes-cuenta")
def listar_solicitudes_cuenta(estado: str = "pendiente", ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        filas = c.execute("""SELECT s.*, u.nombre AS resuelta_por_nombre FROM solicitudes_cuenta s
                             LEFT JOIN usuarios u ON u.id=s.resuelta_por
                             WHERE (?='todas' OR s.estado=?) ORDER BY s.id DESC LIMIT 200""", (estado, estado)).fetchall()
    return [{**dict(f), "rut": formatear_rut(f["rut"])} for f in filas]


class Aprobacion(BaseModel):
    rol: str = "funcionario"


@router.post("/api/admin/solicitudes-cuenta/{sid}/aprobar")
def aprobar_cuenta(sid: int, d: Aprobacion, ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        s = c.execute("SELECT * FROM solicitudes_cuenta WHERE id=? AND estado='pendiente'", (sid,)).fetchone()
        if not s:
            raise HTTPException(404, "La solicitud no existe o ya fue resuelta.")
        uid, clave = _crear_usuario(c, s["rut"], s["nombre"], s["correo"], s["cargo"], s["unidad"], d.rol)
        c.execute("UPDATE solicitudes_cuenta SET estado='aprobada', resuelta_por=?, resuelta_en=? WHERE id=?",
                  (ctx.u["id"], ahora(), sid))
    auditar("usuario_creado", uid, f"solicitud #{sid} aprobada por usuario #{ctx.u['id']}", ctx.ip)
    return {"id": uid, "rut": formatear_rut(s["rut"]), "nombre": s["nombre"], "clave_temporal": clave}


class Rechazo(BaseModel):
    nota: str = Field(default="", max_length=500)


@router.post("/api/admin/solicitudes-cuenta/{sid}/rechazar")
def rechazar_cuenta(sid: int, d: Rechazo, ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        n = c.execute("UPDATE solicitudes_cuenta SET estado='rechazada', resuelta_por=?, resuelta_en=?, nota=? WHERE id=? AND estado='pendiente'",
                      (ctx.u["id"], ahora(), _texto(d.nota, 500), sid)).rowcount
    if not n:
        raise HTTPException(404, "La solicitud no existe o ya fue resuelta.")
    auditar("solicitud_cuenta_rechazada", None, f"solicitud #{sid} por usuario #{ctx.u['id']}", ctx.ip)
    return {"ok": True}


# ------------------------------------------------------------------ solicitudes de contraseña
@router.get("/api/admin/solicitudes-clave")
def listar_solicitudes_clave(ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        filas = c.execute("""SELECT s.id, s.creada, s.ip, u.id AS usuario_id, u.rut, u.nombre, u.unidad, u.cargo
                             FROM solicitudes_clave s JOIN usuarios u ON u.id=s.usuario_id
                             WHERE s.estado='pendiente' ORDER BY s.id""").fetchall()
    return [{**dict(f), "rut": formatear_rut(f["rut"])} for f in filas]


@router.post("/api/admin/solicitudes-clave/{sid}/descartar")
def descartar_clave(sid: int, ctx: Contexto = Depends(solo_admin)):
    with bd() as c:
        c.execute("UPDATE solicitudes_clave SET estado='descartada', resuelta_por=?, resuelta_en=? WHERE id=?", (ctx.u["id"], ahora(), sid))
    auditar("solicitud_clave_descartada", None, f"#{sid} por usuario #{ctx.u['id']}", ctx.ip)
    return {"ok": True}


# ------------------------------------------------------------------ derechos Ley 21.719
@router.get("/api/admin/derechos")
def listar_derechos(estado: str = "abiertas", ctx: Contexto = Depends(admin_o_dpd)):
    filtro = "s.estado IN ('recibida','en_revision')" if estado == "abiertas" else "1=1"
    with bd() as c:
        filas = c.execute(f"""SELECT s.*, u.nombre, u.rut FROM solicitudes_derechos s JOIN usuarios u ON u.id=s.usuario_id
                              WHERE {filtro} ORDER BY s.vence, s.id LIMIT 300""").fetchall()
    return [{**dict(f), "rut": formatear_rut(f["rut"]), "tipo_nombre": TIPOS_SOLICITUD.get(f["tipo"], f["tipo"])} for f in filas]


class RespuestaDerecho(BaseModel):
    estado: str
    respuesta: str = Field(default="", max_length=3000)


@router.post("/api/admin/derechos/{sid}")
def responder_derecho(sid: int, d: RespuestaDerecho, ctx: Contexto = Depends(admin_o_dpd)):
    if d.estado not in ("en_revision", "respondida", "rechazada"):
        raise HTTPException(400, "Estado no válido.")
    if d.estado in ("respondida", "rechazada") and len(d.respuesta.strip()) < 10:
        raise HTTPException(400, "Escribe una respuesta fundada para la persona.")
    with bd() as c:
        s = c.execute("SELECT usuario_id FROM solicitudes_derechos WHERE id=?", (sid,)).fetchone()
        if not s:
            raise HTTPException(404, "No existe la solicitud.")
        c.execute("UPDATE solicitudes_derechos SET estado=?, respuesta=? WHERE id=?", (d.estado, d.respuesta.strip() or None, sid))
    auditar("solicitud_derecho_" + d.estado, s["usuario_id"], f"#{sid} por usuario #{ctx.u['id']}", ctx.ip)
    return {"ok": True}


# ------------------------------------------------------------------ módulos
class Modulo(BaseModel):
    clave: str = Field(max_length=40)
    nombre: str = Field(max_length=60)
    descripcion: str = Field(default="", max_length=200)
    url: str = Field(max_length=300)
    icono: str = Field(default="modulos", max_length=40)
    color: str = Field(default="#1565c0", max_length=7)
    orden: int = 100
    activo: bool = True
    finalidad: str = Field(max_length=500)
    categorias_datos: str = Field(max_length=500)
    datos_sensibles: bool = False
    eipd_aprobada: bool = False
    responsable: str = Field(default="", max_length=120)
    roles: list[str] = []


def _validar_modulo(m: Modulo):
    if not re.fullmatch(r"[a-z0-9-]{2,40}", m.clave):
        raise HTTPException(400, "La clave usa solo minúsculas, números y guiones.")
    if not (m.url.startswith("/") or m.url.startswith("https://") or m.url.startswith("http://")):
        raise HTTPException(400, "La URL debe empezar con / o con http(s)://.")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", m.color):
        raise HTTPException(400, "Color no válido.")
    if len(m.finalidad.strip()) < 10 or len(m.categorias_datos.strip()) < 3:
        raise HTTPException(400, "Describe la finalidad y las categorías de datos (ficha de tratamiento).")
    if any(r not in cfg.ROLES for r in m.roles):
        raise HTTPException(400, "Perfil no válido.")


@router.get("/api/admin/modulos")
def listar_modulos(ctx: Contexto = Depends(admin_o_dpd)):
    with bd() as c:
        mods = [dict(f) for f in c.execute("SELECT * FROM modulos ORDER BY orden, nombre")]
        for m in mods:
            m["roles"] = [r[0] for r in c.execute("SELECT rol FROM modulos_rol WHERE modulo_id=?", (m["id"],))]
            for k in ("activo", "datos_sensibles", "eipd_aprobada"):
                m[k] = bool(m[k])
    return mods


def _guardar_modulo(m: Modulo, ctx: Contexto, mid: int | None):
    _validar_modulo(m)
    campos = m.model_dump(exclude={"roles"})
    for k in ("activo", "datos_sensibles", "eipd_aprobada"):
        campos[k] = int(campos[k])
    with bd() as c:
        if mid is None:
            if c.execute("SELECT 1 FROM modulos WHERE clave=?", (m.clave,)).fetchone():
                raise HTTPException(409, "Ya existe un módulo con esa clave.")
            cols = ", ".join(campos)
            mid = c.execute(f"INSERT INTO modulos ({cols}) VALUES ({', '.join('?' * len(campos))})", tuple(campos.values())).lastrowid
        else:
            previo = c.execute("SELECT eipd_aprobada FROM modulos WHERE id=?", (mid,)).fetchone()
            if not previo:
                raise HTTPException(404, "No existe el módulo.")
            c.execute(f"UPDATE modulos SET {', '.join(f'{k}=?' for k in campos)} WHERE id=?", (*campos.values(), mid))
        c.execute("DELETE FROM modulos_rol WHERE modulo_id=?", (mid,))
        c.executemany("INSERT INTO modulos_rol VALUES (?,?)", [(mid, r) for r in set(m.roles)])
    auditar("modulo_guardado", ctx.u["id"], f"{m.clave} (EIPD {'aprobada' if m.eipd_aprobada else 'pendiente'})", ctx.ip)
    return {"id": mid}


@router.post("/api/admin/modulos")
def crear_modulo(m: Modulo, ctx: Contexto = Depends(solo_admin)):
    return _guardar_modulo(m, ctx, None)


@router.put("/api/admin/modulos/{mid}")
def editar_modulo(mid: int, m: Modulo, ctx: Contexto = Depends(admin_o_dpd)):
    return _guardar_modulo(m, ctx, mid)


# ------------------------------------------------------------------ bitácora
@router.get("/api/admin/auditoria")
def ver_auditoria(q: str = "", accion: str = "", limite: int = 200, ctx: Contexto = Depends(admin_o_dpd)):
    limite = max(1, min(limite, 1000))
    with bd() as c:
        filas = c.execute(
            """SELECT a.id, a.ts, a.accion, a.detalle, a.ip, u.nombre, u.rut FROM auditoria a
               LEFT JOIN usuarios u ON u.id=a.usuario_id
               WHERE (?='' OR a.accion=?) AND (?='' OR u.nombre LIKE ? OR a.detalle LIKE ? OR a.ip LIKE ?)
               ORDER BY a.id DESC LIMIT ?""",
            (accion, accion, q, f"%{q}%", f"%{q}%", f"%{q}%", limite),
        ).fetchall()
    auditar("auditoria_consultada", ctx.u["id"], (q or accion or "sin filtro")[:80], ctx.ip)
    return [{**dict(f), "rut": formatear_rut(f["rut"]) if f["rut"] else None,
             "etiqueta": ETIQUETAS_ACCION.get(f["accion"], f["accion"].replace("_", " ").capitalize())} for f in filas]


@router.get("/api/admin/auditoria/integridad")
def integridad(ctx: Contexto = Depends(admin_o_dpd)):
    return verificar_auditoria()
