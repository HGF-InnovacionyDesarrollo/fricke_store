"""Base de datos SQLite y bitácora de auditoría encadenada (a prueba de manipulación)."""
import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DB_PATH

_lock_auditoria = threading.Lock()

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    rut TEXT UNIQUE NOT NULL,              -- normalizado: 12345678-5
    nombre TEXT NOT NULL,
    correo TEXT,
    cargo TEXT,
    unidad TEXT,
    rol TEXT NOT NULL DEFAULT 'funcionario',  -- funcionario | admin
    clave_hash TEXT NOT NULL,
    debe_cambiar_clave INTEGER NOT NULL DEFAULT 1,
    activo INTEGER NOT NULL DEFAULT 1,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TEXT,
    clave_cambiada_en TEXT,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sesiones (
    id INTEGER PRIMARY KEY,
    token_hash TEXT UNIQUE NOT NULL,       -- nunca se guarda el token en claro
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    creada TEXT NOT NULL,
    ultima_actividad TEXT NOT NULL,
    expira TEXT NOT NULL,                  -- límite absoluto (turno)
    ip TEXT,
    navegador TEXT,
    bloqueada INTEGER NOT NULL DEFAULT 0   -- pantalla bloqueada en estación compartida
);

CREATE TABLE IF NOT EXISTS aceptaciones_aviso (
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    version TEXT NOT NULL,
    aceptado_en TEXT NOT NULL,
    PRIMARY KEY (usuario_id, version)
);

CREATE TABLE IF NOT EXISTS solicitudes_derechos (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    tipo TEXT NOT NULL,          -- acceso | rectificacion | supresion | oposicion | portabilidad | bloqueo
    detalle TEXT,
    estado TEXT NOT NULL DEFAULT 'recibida',  -- recibida | en_revision | respondida | rechazada
    creada TEXT NOT NULL,
    vence TEXT NOT NULL,
    respuesta TEXT
);

-- Solicitudes de cuenta hechas desde la pantalla de ingreso. Un administrador las aprueba.
CREATE TABLE IF NOT EXISTS solicitudes_cuenta (
    id INTEGER PRIMARY KEY,
    rut TEXT NOT NULL,
    nombre TEXT NOT NULL,
    correo TEXT,
    cargo TEXT,
    unidad TEXT,
    motivo TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',   -- pendiente | aprobada | rechazada
    creada TEXT NOT NULL,
    ip TEXT,
    resuelta_por INTEGER REFERENCES usuarios(id),
    resuelta_en TEXT,
    nota TEXT
);

-- Pedidos de restablecimiento de contraseña (solo se guardan si el RUT existe).
CREATE TABLE IF NOT EXISTS solicitudes_clave (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    estado TEXT NOT NULL DEFAULT 'pendiente',   -- pendiente | atendida | descartada
    creada TEXT NOT NULL,
    ip TEXT,
    resuelta_por INTEGER REFERENCES usuarios(id),
    resuelta_en TEXT
);

-- Catálogo de módulos del ecosistema (vacío por ahora). Se habilitan por rol o por usuario.
CREATE TABLE IF NOT EXISTS modulos (
    id INTEGER PRIMARY KEY,
    clave TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    url TEXT NOT NULL,
    icono TEXT,                  -- nombre de icono o ruta a SVG
    color TEXT,
    orden INTEGER NOT NULL DEFAULT 100,
    activo INTEGER NOT NULL DEFAULT 1,
    -- Ficha de tratamiento: todo módulo declara qué datos usa y para qué antes de publicarse.
    finalidad TEXT NOT NULL,
    categorias_datos TEXT NOT NULL,        -- p. ej. "identificación del paciente, signos vitales"
    datos_sensibles INTEGER NOT NULL DEFAULT 0,   -- datos de salud u otros sensibles
    eipd_aprobada INTEGER NOT NULL DEFAULT 0,     -- evaluación de impacto aprobada por el DPD
    responsable TEXT                       -- unidad o persona dueña del módulo
);
CREATE TABLE IF NOT EXISTS modulos_rol (
    modulo_id INTEGER NOT NULL REFERENCES modulos(id),
    rol TEXT NOT NULL,
    PRIMARY KEY (modulo_id, rol)
);
CREATE TABLE IF NOT EXISTS modulos_usuario (
    modulo_id INTEGER NOT NULL REFERENCES modulos(id),
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    PRIMARY KEY (modulo_id, usuario_id)
);

-- Bitácora: cada fila incluye el hash de la anterior. Si alguien edita o borra una fila,
-- la cadena se rompe y `verificar_auditoria()` lo detecta.
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    ts TEXT NOT NULL,
    usuario_id INTEGER,
    accion TEXT NOT NULL,
    detalle TEXT,
    ip TEXT,
    hash_anterior TEXT NOT NULL,
    hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_auditoria_usuario ON auditoria(usuario_id, id);
"""

GENESIS = "0" * 64


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def conectar() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("PRAGMA journal_mode = WAL")
    return c


@contextmanager
def bd():
    c = conectar()
    try:
        yield c
        c.commit()
    finally:
        c.close()


def inicializar():
    with bd() as c:
        c.executescript(ESQUEMA)


def _hash_fila(anterior: str, ts: str, usuario_id, accion: str, detalle, ip) -> str:
    carga = json.dumps([anterior, ts, usuario_id, accion, detalle, ip], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(carga.encode()).hexdigest()


def auditar(accion: str, usuario_id: int | None = None, detalle: str | None = None, ip: str | None = None):
    with _lock_auditoria, bd() as c:
        fila = c.execute("SELECT hash FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()
        anterior = fila["hash"] if fila else GENESIS
        ts = ahora()
        h = _hash_fila(anterior, ts, usuario_id, accion, detalle, ip)
        c.execute(
            "INSERT INTO auditoria (ts, usuario_id, accion, detalle, ip, hash_anterior, hash) VALUES (?,?,?,?,?,?,?)",
            (ts, usuario_id, accion, detalle, ip, anterior, h),
        )


def verificar_auditoria() -> dict:
    with bd() as c:
        anterior = GENESIS
        n = 0
        for f in c.execute("SELECT * FROM auditoria ORDER BY id"):
            n += 1
            esperado = _hash_fila(anterior, f["ts"], f["usuario_id"], f["accion"], f["detalle"], f["ip"])
            if f["hash_anterior"] != anterior or f["hash"] != esperado:
                return {"integra": False, "registros": n, "falla_en_id": f["id"]}
            anterior = f["hash"]
        return {"integra": True, "registros": n, "ultimo_hash": anterior}
