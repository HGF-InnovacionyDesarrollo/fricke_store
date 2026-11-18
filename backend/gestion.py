"""Gestión del ecosistema: solicitudes públicas (crear cuenta, recuperar clave) y consola de administración.

Se importa al final de app.py, cuando la sesión y los helpers ya están definidos.
"""
import hashlib
import re
from datetime import date
import threading
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

import config as cfg
from app import TIPOS_SOLICITUD, Contexto, ETIQUETAS_ACCION, ip_de, sesion_lista
from db import ahora, auditar, bd, guardar_ajuste, leer_ajuste, verificar_auditoria
from plazos import sumar_corridos
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
    if formularios_pausados():
        raise HTTPException(503, "Este formulario está pausado temporalmente por seguridad. Llama a la Mesa de ayuda.")
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
    if formularios_pausados():
        raise HTTPException(503, "Este formulario está pausado temporalmente por seguridad. Llama a la Mesa de ayuda.")
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


def perfiles(*roles):
    def dep(ctx: Contexto = Depends(sesion_lista)) -> Contexto:
        if ctx.u["rol"] not in roles:
            raise HTTPException(403, "Tu perfil no tiene acceso a esta sección.")
        return ctx
    return dep


auditoria_o_gestion = perfiles("admin", "dpd", "seguridad")
seguridad_o_admin = perfiles("admin", "seguridad")


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
        "mfa_activo": bool(u["mfa_activo"]), "mfa_exigido": bool(u["mfa_exigido"]),
        "mfa_por_perfil": u["rol"] in cfg.MFA_PERFILES,
    }


# ------------------------------------------------------------------ resumen
@router.get("/api/admin/resumen")
def resumen(ctx: Contexto = Depends(auditoria_o_gestion)):
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
            "derechos_vencidos": n("SELECT COUNT(*) FROM solicitudes_derechos WHERE estado IN ('recibida','en_revision') AND vence < to_char(CURRENT_DATE, 'YYYY-MM-DD')"),
            "modulos": n("SELECT COUNT(*) FROM modulos"),
            "fallidos_24h": n("SELECT COUNT(*) FROM auditoria WHERE accion='login_fallido' AND ts::timestamptz > now() - interval '1 day'"),
            "incidentes_abiertos": n("SELECT COUNT(*) FROM incidentes WHERE estado<>'cerrado'"),
            "alertas": alertas_seguridad(c),
            "respaldo": estado_respaldo(),
            "contencion": estado_contencion(),
        }


# ------------------------------------------------------------------ usuarios
@router.get("/api/admin/usuarios")
def listar_usuarios(q: str = "", ctx: Contexto = Depends(solo_admin)):
    patron = f"%{q.strip()}%"
    rut_q = re.sub(r"[^0-9kK]", "", q)
    with bd() as c:
        filas = c.execute(
            """SELECT * FROM usuarios WHERE nombre ILIKE ? OR unidad ILIKE ? OR cargo ILIKE ?
               OR (? <> '' AND replace(rut,'-','') ILIKE ?) ORDER BY activo DESC, nombre LIMIT 300""",
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
    mfa_exigido: bool | None = None


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
    if "mfa_exigido" in cambios:
        cambios["mfa_exigido"] = int(cambios["mfa_exigido"])
    if not cambios:
        return {"ok": True}
    with bd() as c:
        if not c.execute("SELECT 1 FROM usuarios WHERE id=?", (uid,)).fetchone():
            raise HTTPException(404, "No existe la cuenta.")
        sets = ", ".join(f"{k}=?" for k in cambios)
        c.execute(f"UPDATE usuarios SET {sets} WHERE id=?", (*cambios.values(), uid))
        if cambios.get("activo") == 0 or "rol" in cambios:
            c.execute("DELETE FROM sesiones WHERE usuario_id=?", (uid,))
    if "mfa_exigido" in cambios:
        auditar("mfa_exigido" if cambios["mfa_exigido"] else "mfa_no_exigido", uid, f"por usuario #{ctx.u['id']}", ctx.ip)
    otros = [k for k in cambios if k != "mfa_exigido"]
    if otros:
        auditar("usuario_editado", uid, f"{', '.join(otros)} por usuario #{ctx.u['id']}", ctx.ip)
    return {"ok": True}


@router.post("/api/admin/usuarios/{uid}/mfa-restablecer")
def restablecer_mfa(uid: int, ctx: Contexto = Depends(solo_admin)):
    """Para quien perdió o cambió el celular: borra su configuración; al ingresar la vuelve a crear
    (si le es obligatoria). Verificar identidad antes, igual que con la contraseña."""
    with bd() as c:
        n = c.execute("UPDATE usuarios SET mfa_secreto=NULL, mfa_activo=0, mfa_activado_en=NULL, mfa_ultimo_paso=NULL "
                      "WHERE id=?", (uid,)).rowcount
        if not n:
            raise HTTPException(404, "No existe la cuenta.")
        c.execute("DELETE FROM mfa_respaldo WHERE usuario_id=?", (uid,))
        c.execute("DELETE FROM sesiones WHERE usuario_id=?", (uid,))
    auditar("mfa_restablecido", uid, f"por usuario #{ctx.u['id']}", ctx.ip)
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
    estado: str                      # en_revision | prorrogar | respondida | rechazada
    respuesta: str = Field(default="", max_length=3000)


LEYENDA_RECLAMO = ("Conforme al artículo 11 de la Ley 21.719, si no estás conforme con esta respuesta puedes reclamar "
                   "ante la Agencia de Protección de Datos Personales dentro de 30 días hábiles desde que la recibas.")


@router.post("/api/admin/derechos/{sid}")
def responder_derecho(sid: int, d: RespuestaDerecho, ctx: Contexto = Depends(admin_o_dpd)):
    if d.estado not in ("en_revision", "prorrogar", "respondida", "rechazada"):
        raise HTTPException(400, "Estado no válido.")
    texto = d.respuesta.strip()
    with bd() as c:
        s = c.execute("SELECT * FROM solicitudes_derechos WHERE id=?", (sid,)).fetchone()
        if not s:
            raise HTTPException(404, "No existe la solicitud.")
        if s["estado"] in ("respondida", "rechazada"):
            raise HTTPException(409, "La solicitud ya fue cerrada; su respuesta quedó respaldada y no se modifica.")
        if d.estado == "prorrogar":
            # Art. 11: una sola prórroga de hasta 30 días corridos, informando al titular.
            if s["tipo"] == "bloqueo":
                raise HTTPException(400, "El bloqueo temporal no admite prórroga (2 días hábiles).")
            if s["prorrogada"]:
                raise HTTPException(400, "La ley permite prorrogar una sola vez.")
            if len(texto) < 10:
                raise HTTPException(400, "Explica a la persona el motivo de la prórroga.")
            nuevo_vence = sumar_corridos(date.fromisoformat(s["vence"]), cfg.PLAZO_SOLICITUD_DIAS).isoformat()
            c.execute("UPDATE solicitudes_derechos SET prorrogada=1, prorroga_motivo=?, vence=?, estado='en_revision' WHERE id=?",
                      (texto, nuevo_vence, sid))
            detalle = f"#{sid} prorrogada hasta {nuevo_vence} por usuario #{ctx.u['id']}"
            accion = "solicitud_derecho_prorrogada"
        elif d.estado == "en_revision":
            c.execute("UPDATE solicitudes_derechos SET estado='en_revision' WHERE id=?", (sid,))
            detalle, accion = f"#{sid} por usuario #{ctx.u['id']}", "solicitud_derecho_en_revision"
        else:
            if len(texto) < 10:
                raise HTTPException(400, "Escribe una respuesta fundada para la persona.")
            if d.estado == "rechazada" and LEYENDA_RECLAMO not in texto:
                texto = f"{texto}\n\n{LEYENDA_RECLAMO}"
            # Respaldo íntegro de la respuesta (art. 11): su hash queda sellado en la bitácora encadenada.
            huella = hashlib.sha256(texto.encode()).hexdigest()
            c.execute("UPDATE solicitudes_derechos SET estado=?, respuesta=?, respondida_en=?, respuesta_hash=? WHERE id=?",
                      (d.estado, texto, ahora(), huella, sid))
            detalle = f"#{sid} por usuario #{ctx.u['id']} · sha256 {huella}"
            if d.estado == "rechazada" and s["tipo"] == "bloqueo":
                detalle += " · comunicar el rechazo del bloqueo a la Agencia"
            accion = "solicitud_derecho_" + d.estado
    auditar(accion, s["usuario_id"], detalle, ctx.ip)
    return {"ok": True, "avisar_agencia": d.estado == "rechazada" and s["tipo"] == "bloqueo"}


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
    categorias_datos: str = Field(max_length=1000)
    datos_sensibles: bool = False
    eipd_aprobada: bool = False
    responsable: str = Field(default="", max_length=120)
    roles: list[str] = []


def _validar_modulo(m: Modulo):
    # Los módulos con código usan guion bajo en su clave (ej.: monitoreo_fetal), igual que plataforma.CLAVE_VALIDA.
    if not re.fullmatch(r"[a-z0-9_-]{2,40}", m.clave):
        raise HTTPException(400, "La clave usa solo minúsculas, números, guiones y guiones bajos.")
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
            previo = c.execute("SELECT eipd_aprobada, origen, clave FROM modulos WHERE id=?", (mid,)).fetchone()
            if not previo:
                raise HTTPException(404, "No existe el módulo.")
            if previo["origen"] == "codigo":
                # La ficha y la identidad de un módulo con código las define su manifiesto (revisado en el
                # repositorio). Desde el panel solo se decide quién lo ve, si está activo, el orden y la EIPD.
                from plataforma import CAMPOS_DE_CODIGO
                for k in (*CAMPOS_DE_CODIGO, "clave"):
                    campos.pop(k, None)
                m.clave = previo["clave"]
            c.execute(f"UPDATE modulos SET {', '.join(f'{k}=?' for k in campos)} WHERE id=?", (*campos.values(), mid))
        c.execute("DELETE FROM modulos_rol WHERE modulo_id=?", (mid,))
        c.executemany("INSERT INTO modulos_rol VALUES (?,?)", [(mid, r) for r in set(m.roles)])
    auditar("modulo_guardado", ctx.u["id"], f"{m.clave} (EIPD {'aprobada' if m.eipd_aprobada else 'pendiente'})", ctx.ip)
    return {"id": mid}


@router.get("/api/admin/modulos/registro-tratamiento")
def registro_tratamiento(ctx: Contexto = Depends(auditoria_o_gestion)):
    """Fichas de tratamiento completas de los módulos con código (base del Registro de Actividades de Tratamiento)."""
    from plataforma import fichas
    return fichas()


@router.post("/api/admin/modulos")
def crear_modulo(m: Modulo, ctx: Contexto = Depends(solo_admin)):
    return _guardar_modulo(m, ctx, None)


@router.put("/api/admin/modulos/{mid}")
def editar_modulo(mid: int, m: Modulo, ctx: Contexto = Depends(admin_o_dpd)):
    return _guardar_modulo(m, ctx, mid)


# ------------------------------------------------------------------ bitácora
@router.get("/api/admin/auditoria")
def ver_auditoria(q: str = "", accion: str = "", desde: str = "", hasta: str = "", limite: int = 200,
                  ctx: Contexto = Depends(auditoria_o_gestion)):
    """Bitácora con filtros. `desde` y `hasta` son fechas AAAA-MM-DD en hora de Chile, ambas incluidas."""
    filas = _consultar_auditoria(q, accion, desde, hasta, max(1, min(limite, 1000)))
    auditar("auditoria_consultada", ctx.u["id"], _texto_filtro(q, accion, desde, hasta), ctx.ip)
    return [_fila_bitacora(f) for f in filas]


MAX_EXPORTAR = 50_000


@router.get("/api/admin/auditoria/exportar")
def exportar_auditoria(q: str = "", accion: str = "", desde: str = "", hasta: str = "",
                       ctx: Contexto = Depends(auditoria_o_gestion)):
    """Descarga en CSV (se abre en Excel) de lo filtrado. Incluye RUT e IP: la descarga queda en la bitácora."""
    import csv
    import io
    from zoneinfo import ZoneInfo
    filas = _consultar_auditoria(q, accion, desde, hasta, MAX_EXPORTAR)
    chile = ZoneInfo("America/Santiago")

    def celda(v):
        v = "" if v is None else str(v)
        return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v  # evita fórmulas al abrir en Excel

    salida = io.StringIO()
    w = csv.writer(salida, delimiter=";", lineterminator="\r\n")  # ; es el separador de Excel en Chile
    w.writerow(["N°", "Fecha (hora de Chile)", "Evento", "Código", "Persona", "RUT", "Detalle", "IP", "Hash"])
    for f in filas:
        d = _fila_bitacora(f)
        fecha = datetime.fromisoformat(f["ts"]).astimezone(chile).strftime("%d-%m-%Y %H:%M:%S")
        w.writerow([f["id"], fecha, *(celda(x) for x in (d["etiqueta"], f["accion"], f["nombre"], d["rut"], f["detalle"], f["ip"], f["hash"]))])
    filtro = _texto_filtro(q, accion, desde, hasta)
    auditar("auditoria_exportada", ctx.u["id"], f"{len(filas)} registros · {filtro}"[:200], ctx.ip)
    nombre = f"bitacora_{cfg.ESTABLECIMIENTO}_{desde or 'inicio'}_{hasta or date.today().isoformat()}.csv"
    # El BOM inicial hace que Excel reconozca las tildes.
    return Response("\ufeff" + salida.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


def _texto_filtro(q, accion, desde, hasta) -> str:
    t = " · ".join(x for x in (q, accion, f"desde {desde}" if desde else "", f"hasta {hasta}" if hasta else "") if x)
    return (t or "sin filtro")[:120]


def _fila_bitacora(f) -> dict:
    return {**dict(f), "rut": formatear_rut(f["rut"]) if f["rut"] else None,
            "etiqueta": ETIQUETAS_ACCION.get(f["accion"], f["accion"].replace("_", " ").capitalize())}


def _consultar_auditoria(q: str, accion: str, desde: str, hasta: str, limite: int):
    for f in (desde, hasta):
        try:
            if f:
                date.fromisoformat(f)
        except ValueError:
            raise HTTPException(400, "Fecha no válida.")
    if desde and hasta and desde > hasta:
        raise HTTPException(400, "La fecha «desde» no puede ser posterior a «hasta».")
    with bd() as c:
        filas = c.execute(
            """SELECT a.id, a.ts, a.accion, a.detalle, a.ip, a.hash, u.nombre, u.rut FROM auditoria a
               LEFT JOIN usuarios u ON u.id=a.usuario_id
               WHERE (?='' OR a.accion=?) AND (?='' OR u.nombre ILIKE ? OR a.detalle ILIKE ? OR a.ip ILIKE ?)
                 AND (?='' OR (a.ts::timestamptz AT TIME ZONE 'America/Santiago')::date >= ?::date)
                 AND (?='' OR (a.ts::timestamptz AT TIME ZONE 'America/Santiago')::date <= ?::date)
               ORDER BY a.id DESC LIMIT ?""",
            (accion, accion, q, f"%{q}%", f"%{q}%", f"%{q}%", desde, desde or None, hasta, hasta or None, limite),
        ).fetchall()
    return filas


@router.get("/api/admin/auditoria/integridad")
def integridad(ctx: Contexto = Depends(auditoria_o_gestion)):
    return verificar_auditoria()


# ------------------------------------------------------------------ alertas (monitoreo dentro del portal)
def _ts_sql(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def estado_respaldo() -> dict:
    ultimo, prueba = leer_ajuste("ultimo_respaldo"), leer_ajuste("ultima_prueba_restauracion")
    atrasado = True
    if ultimo:
        atrasado = datetime.now(timezone.utc) - datetime.fromisoformat(ultimo) > timedelta(hours=cfg.RESPALDO_MAX_HORAS)
    return {"ultimo": ultimo, "ultima_prueba": prueba, "atrasado": atrasado}


def estado_contencion() -> dict:
    return {"modulos_suspendidos": leer_ajuste("modulos_suspendidos") is not None,
            "formularios_pausados": leer_ajuste("formularios_pausados") == "1"}


def alertas_seguridad(c) -> list[dict]:
    """Señales para detectar a tiempo (Ley 21.663: alerta temprana a ANCI en 3 horas)."""
    ahora_dt = datetime.now(timezone.utc)

    def hace(**kw):
        return _ts_sql(ahora_dt - timedelta(**kw))

    al = []
    fallidos = c.execute("SELECT COUNT(*) FROM auditoria WHERE accion='login_fallido' AND ts > ?", (hace(minutes=15),)).fetchone()[0]
    if fallidos >= 10:
        al.append({"nivel": "alta", "texto": f"{fallidos} intentos de acceso fallidos en los últimos 15 minutos. Posible ataque de fuerza bruta."})
    bloqueos = c.execute("SELECT COUNT(*) FROM usuarios WHERE bloqueado_hasta > ?", (_ts_sql(ahora_dt),)).fetchone()[0]
    if bloqueos >= 3:
        al.append({"nivel": "media", "texto": f"{bloqueos} cuentas bloqueadas por intentos fallidos en este momento."})
    ips = c.execute("SELECT COUNT(DISTINCT ip) FROM auditoria WHERE accion='login_fallido' AND ts > ?", (hace(hours=1),)).fetchone()[0]
    if ips >= 5:
        al.append({"nivel": "media", "texto": f"Intentos fallidos desde {ips} direcciones distintas en la última hora."})
    madrugada = c.execute("""SELECT COUNT(*) FROM auditoria a JOIN usuarios u ON u.id=a.usuario_id
                             WHERE a.accion='login' AND u.rol IN ('admin','dpd','seguridad') AND a.ts > ?
                             AND EXTRACT(HOUR FROM a.ts::timestamptz AT TIME ZONE 'America/Santiago') < 6""", (hace(hours=24),)).fetchone()[0]
    if madrugada:
        al.append({"nivel": "baja", "texto": f"{madrugada} ingreso(s) de cuentas privilegiadas de madrugada (00:00-06:00, hora de Chile) en las últimas 24 h."})
    vencen = c.execute("SELECT COUNT(*) FROM solicitudes_derechos WHERE estado IN ('recibida','en_revision') AND vence <= to_char(CURRENT_DATE + 5, 'YYYY-MM-DD')").fetchone()[0]
    if vencen:
        al.append({"nivel": "media", "texto": f"{vencen} solicitud(es) de derechos vencen en 5 días o menos."})
    for inc in c.execute("SELECT * FROM incidentes WHERE estado<>'cerrado'").fetchall():
        for p in plazos_incidente(inc):
            if p["vencido"]:
                al.append({"nivel": "alta", "texto": f"Incidente #{inc['id']}: venció el plazo de «{p['nombre']}»."})
    r = estado_respaldo()
    if r["atrasado"]:
        al.append({"nivel": "alta" if r["ultimo"] else "media",
                   "texto": "No hay respaldos registrados." if not r["ultimo"] else f"El último respaldo tiene más de {cfg.RESPALDO_MAX_HORAS} horas."})
    if not r["ultima_prueba"] or datetime.now(timezone.utc) - datetime.fromisoformat(r["ultima_prueba"]) > timedelta(days=92):
        al.append({"nivel": "media", "texto": "No se ha probado una restauración de respaldo en los últimos 3 meses."})
    return al


# ------------------------------------------------------------------ incidentes (Ley 21.663 y Ley 21.719)
def plazos_incidente(inc) -> list[dict]:
    """Ley 21.663 art. 9: alerta 3 h; actualización 72 h (24 h si un OIV ve afectado su servicio esencial);
    informe final 15 días corridos; plan de acción del OIV 7 días corridos.
    Ley 21.719 art. 14 sexies: Agencia "sin dilaciones indebidas" y titulares si hay datos sensibles
    (aquí se usa 72 h como meta interna, no como plazo legal)."""
    det = datetime.fromisoformat(inc["detectado_en"])
    base = datetime.fromisoformat(inc["alerta_anci_en"]) if inc["alerta_anci_en"] else det
    oiv_esencial = cfg.ES_OIV and inc["afecta_servicio_esencial"]
    pasos = [
        ("alerta_anci_en", "Alerta temprana a ANCI (CSIRT Nacional)", det + timedelta(hours=3), True),
        ("actualizacion_anci_en", "Actualización a ANCI", det + timedelta(hours=24 if oiv_esencial else 72), True),
        ("plan_accion_en", "Plan de acción a ANCI (OIV)", base + timedelta(days=7), cfg.ES_OIV),
        ("informe_final_en", "Informe final a ANCI", base + timedelta(days=15), True),
        ("agencia_notificada_en", "Aviso a la Agencia de Protección de Datos", det + timedelta(hours=72), bool(inc["afecta_datos_personales"])),
        ("titulares_notificados_en", "Aviso a las personas afectadas", det + timedelta(hours=72), bool(inc["afecta_datos_sensibles"])),
    ]
    ahora_dt = datetime.now(timezone.utc)
    return [{"campo": campo, "nombre": nombre, "limite": _ts_sql(limite), "hecho_en": inc[campo],
             "vencido": not inc[campo] and ahora_dt > limite,
             "meta_interna": campo in ("agencia_notificada_en", "titulares_notificados_en")}
            for campo, nombre, limite, aplica in pasos if aplica]


class Incidente(BaseModel):
    titulo: str = Field(max_length=150)
    descripcion: str = Field(default="", max_length=4000)
    detectado_en: str | None = None
    severidad: str = "media"
    afecta_servicio_esencial: bool = False
    afecta_datos_personales: bool = False
    afecta_datos_sensibles: bool = False


def _incidente_dict(inc) -> dict:
    d = dict(inc)
    for k in ("afecta_servicio_esencial", "afecta_datos_personales", "afecta_datos_sensibles"):
        d[k] = bool(d[k])
    d["plazos"] = plazos_incidente(inc)
    return d


@router.get("/api/admin/incidentes")
def listar_incidentes(ctx: Contexto = Depends(auditoria_o_gestion)):
    with bd() as c:
        filas = c.execute("""SELECT i.*, u.nombre AS registrado_por_nombre FROM incidentes i
                             LEFT JOIN usuarios u ON u.id=i.registrado_por ORDER BY (i.estado='cerrado'), i.id DESC""").fetchall()
    return {"es_oiv": cfg.ES_OIV, "incidentes": [_incidente_dict(f) for f in filas]}


@router.post("/api/admin/incidentes")
def crear_incidente(d: Incidente, ctx: Contexto = Depends(seguridad_o_admin)):
    if d.severidad not in ("baja", "media", "alta", "critica"):
        raise HTTPException(400, "Severidad no válida.")
    if len(d.titulo.strip()) < 5:
        raise HTTPException(400, "Describe brevemente el incidente.")
    try:
        detectado = (datetime.fromisoformat(d.detectado_en) if d.detectado_en else datetime.now(timezone.utc))
        if detectado.tzinfo is None:
            raise ValueError
        detectado = detectado.astimezone(timezone.utc)
    except ValueError:
        raise HTTPException(400, "Fecha de detección no válida.")
    if detectado > datetime.now(timezone.utc) + timedelta(minutes=5):
        raise HTTPException(400, "La detección no puede estar en el futuro.")
    with bd() as c:
        iid = c.execute("""INSERT INTO incidentes (titulo, descripcion, detectado_en, registrado_por, registrado_en, severidad,
                           afecta_servicio_esencial, afecta_datos_personales, afecta_datos_sensibles) VALUES (?,?,?,?,?,?,?,?,?)""",
                        (d.titulo.strip(), d.descripcion.strip(), _ts_sql(detectado), ctx.u["id"], ahora(), d.severidad,
                         int(d.afecta_servicio_esencial), int(d.afecta_datos_personales or d.afecta_datos_sensibles),
                         int(d.afecta_datos_sensibles))).lastrowid
    auditar("incidente_registrado", ctx.u["id"], f"#{iid} {d.severidad}: {d.titulo.strip()[:80]}", ctx.ip)
    return {"id": iid}


class HitoIncidente(BaseModel):
    hito: str
    nota: str = Field(default="", max_length=1000)


HITOS = {"alerta_anci_en", "actualizacion_anci_en", "plan_accion_en", "informe_final_en",
         "agencia_notificada_en", "titulares_notificados_en", "contenido", "cerrado", "nota"}


@router.post("/api/admin/incidentes/{iid}/hito")
def marcar_hito(iid: int, d: HitoIncidente, ctx: Contexto = Depends(seguridad_o_admin)):
    if d.hito not in HITOS:
        raise HTTPException(400, "Hito no válido.")
    with bd() as c:
        inc = c.execute("SELECT * FROM incidentes WHERE id=?", (iid,)).fetchone()
        if not inc:
            raise HTTPException(404, "No existe el incidente.")
        if inc["estado"] == "cerrado":
            raise HTTPException(409, "El incidente está cerrado.")
        nota = f"[{ahora()[:16].replace('T', ' ')} UTC · {ctx.u['nombre']}] {d.hito}: {d.nota.strip()}" if d.nota.strip() else None
        notas = "\n".join(x for x in (inc["notas"], nota) if x)
        if d.hito == "nota":
            if not nota:
                raise HTTPException(400, "Escribe la nota.")
            c.execute("UPDATE incidentes SET notas=? WHERE id=?", (notas, iid))
        elif d.hito == "contenido":
            c.execute("UPDATE incidentes SET estado='contenido', notas=? WHERE id=?", (notas, iid))
        elif d.hito == "cerrado":
            pendientes = [p["nombre"] for p in plazos_incidente(inc) if not p["hecho_en"]]
            if pendientes and len(d.nota.strip()) < 10:
                raise HTTPException(400, "Quedan reportes sin marcar: " + ", ".join(pendientes) + ". Justifica el cierre en la nota.")
            c.execute("UPDATE incidentes SET estado='cerrado', cerrado_en=?, notas=? WHERE id=?", (ahora(), notas, iid))
        else:
            c.execute(f"UPDATE incidentes SET {d.hito}=?, notas=? WHERE id=?", (ahora(), notas, iid))
    auditar("incidente_actualizado", ctx.u["id"], f"#{iid} {d.hito}", ctx.ip)
    return {"ok": True}


# ------------------------------------------------------------------ contención (ANCI, Instrucción General N° 4)
class Confirmacion(BaseModel):
    clave: str = Field(max_length=200)
    motivo: str = Field(default="", max_length=500)


ACCIONES_CONTENCION = {"cerrar-sesiones", "forzar-cambio-privilegiadas", "suspender-modulos", "reanudar-modulos",
                       "pausar-formularios", "reanudar-formularios"}


@router.post("/api/admin/contencion/{accion}")
def contencion(accion: str, d: Confirmacion, ctx: Contexto = Depends(seguridad_o_admin)):
    from seguridad import verificar_clave
    if accion not in ACCIONES_CONTENCION:
        raise HTTPException(404, "Acción no válida.")
    if not verificar_clave(d.clave, ctx.u["clave_hash"]):
        auditar("contencion_rechazada", ctx.u["id"], f"{accion}: contraseña incorrecta", ctx.ip)
        raise HTTPException(401, "Contraseña incorrecta.")
    if len(d.motivo.strip()) < 5:
        raise HTTPException(400, "Indica el motivo (queda en la bitácora).")
    res = {}
    if accion == "suspender-modulos" and leer_ajuste("modulos_suspendidos") is not None:
        raise HTTPException(409, "Los módulos ya están suspendidos.")
    if accion == "reanudar-modulos" and leer_ajuste("modulos_suspendidos") is None:
        raise HTTPException(409, "No hay módulos suspendidos.")
    guardados = leer_ajuste("modulos_suspendidos")
    with bd() as c:
        if accion == "cerrar-sesiones":
            res["sesiones_cerradas"] = c.execute("DELETE FROM sesiones WHERE id<>?", (ctx.s["id"],)).rowcount
        elif accion == "forzar-cambio-privilegiadas":
            res["cuentas"] = c.execute("UPDATE usuarios SET debe_cambiar_clave=1 WHERE rol IN ('admin','dpd','seguridad')").rowcount
            c.execute("""DELETE FROM sesiones WHERE id<>? AND usuario_id IN
                         (SELECT id FROM usuarios WHERE rol IN ('admin','dpd','seguridad'))""", (ctx.s["id"],))
        elif accion == "suspender-modulos":
            activos = [r[0] for r in c.execute("SELECT id FROM modulos WHERE activo=1")]
            c.execute("UPDATE modulos SET activo=0")
            c.execute("INSERT INTO ajustes (clave, valor, actualizado) VALUES ('modulos_suspendidos', ?, ?) "
                      "ON CONFLICT (clave) DO UPDATE SET valor=excluded.valor, actualizado=excluded.actualizado",
                      (",".join(map(str, activos)), ahora()))
            res["modulos"] = len(activos)
        elif accion == "reanudar-modulos":
            ids = [int(x) for x in (guardados or "").split(",") if x]
            c.executemany("UPDATE modulos SET activo=1 WHERE id=?", [(i,) for i in ids])
            c.execute("DELETE FROM ajustes WHERE clave='modulos_suspendidos'")
            res["modulos"] = len(ids)
        else:
            c.execute("INSERT INTO ajustes (clave, valor, actualizado) VALUES ('formularios_pausados', ?, ?) "
                      "ON CONFLICT (clave) DO UPDATE SET valor=excluded.valor, actualizado=excluded.actualizado",
                      ("1" if accion == "pausar-formularios" else "0", ahora()))
    auditar("contencion_" + accion.replace("-", "_"), ctx.u["id"], d.motivo.strip()[:300], ctx.ip)
    return {"ok": True, **res}


def formularios_pausados() -> bool:
    return leer_ajuste("formularios_pausados") == "1"
