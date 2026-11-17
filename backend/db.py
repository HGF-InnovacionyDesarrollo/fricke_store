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
-- Permisos internos de un módulo dados a una persona puntual (además de los que trae su perfil).
CREATE TABLE IF NOT EXISTS permisos_usuario (
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    permiso TEXT NOT NULL,                 -- "<clave>.<accion>", declarado en el manifiesto
    otorgado_por INTEGER REFERENCES usuarios(id),
    otorgado_en TEXT NOT NULL,
    PRIMARY KEY (usuario_id, permiso)
);

-- Ajustes del sistema (contención, último respaldo, ancla de la bitácora, etc.)
CREATE TABLE IF NOT EXISTS ajustes (
    clave TEXT PRIMARY KEY,
    valor TEXT,
    actualizado TEXT
);

-- Registro de incidentes de seguridad y vulneraciones de datos (Ley 21.663 y Ley 21.719 art. 14 sexies)
CREATE TABLE IF NOT EXISTS incidentes (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    detectado_en TEXT NOT NULL,          -- UTC: desde aquí corren los plazos
    registrado_por INTEGER REFERENCES usuarios(id),
    registrado_en TEXT NOT NULL,
    severidad TEXT NOT NULL DEFAULT 'media',   -- baja | media | alta | critica
    afecta_servicio_esencial INTEGER NOT NULL DEFAULT 0,
    afecta_datos_personales INTEGER NOT NULL DEFAULT 0,
    afecta_datos_sensibles INTEGER NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'abierto',   -- abierto | contenido | cerrado
    alerta_anci_en TEXT,
    actualizacion_anci_en TEXT,
    informe_final_en TEXT,
    plan_accion_en TEXT,
    agencia_notificada_en TEXT,
    titulares_notificados_en TEXT,
    cerrado_en TEXT,
    notas TEXT
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


# Columnas agregadas después de la primera versión (migración simple e idempotente)
MIGRACIONES = {
    "solicitudes_derechos": {
        "acuse_en": "TEXT",
        "prorrogada": "INTEGER NOT NULL DEFAULT 0",
        "prorroga_motivo": "TEXT",
        "respondida_en": "TEXT",
        "respuesta_hash": "TEXT",
    },
    "modulos": {
        "origen": "TEXT NOT NULL DEFAULT 'manual'",   # manual (panel) | codigo (carpeta modulos/)
        "version": "TEXT",
    },
}


def inicializar():
    with bd() as c:
        c.executescript(ESQUEMA)
        for tabla, columnas in MIGRACIONES.items():
            existentes = {r["name"] for r in c.execute(f"PRAGMA table_info({tabla})")}
            for col, tipo in columnas.items():
                if col not in existentes:
                    c.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")


def leer_ajuste(clave: str, defecto=None):
    with bd() as c:
        f = c.execute("SELECT valor FROM ajustes WHERE clave=?", (clave,)).fetchone()
    return f["valor"] if f else defecto


def guardar_ajuste(clave: str, valor):
    with bd() as c:
        c.execute("INSERT INTO ajustes (clave, valor, actualizado) VALUES (?,?,?) "
                  "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor, actualizado=excluded.actualizado",
                  (clave, None if valor is None else str(valor), ahora()))


def _hash_fila(anterior: str, ts: str, usuario_id, accion: str, detalle, ip) -> str:
    carga = json.dumps([anterior, ts, usuario_id, accion, detalle, ip], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(carga.encode()).hexdigest()


def auditar(accion: str, usuario_id: int | None = None, detalle: str | None = None, ip: str | None = None):
    with _lock_auditoria, bd() as c:
        fila = c.execute("SELECT hash FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()
        nuevo_id = None
        if fila:
            anterior = fila["hash"]
        else:
            # Tabla vacía (inicio o tras archivar todo): continúa desde el ancla y sin reutilizar números.
            a = {r["clave"]: r["valor"] for r in c.execute(
                "SELECT clave, valor FROM ajustes WHERE clave IN ('ancla_auditoria','ultimo_id_archivado')")}
            anterior = a.get("ancla_auditoria") or GENESIS
            nuevo_id = int(a.get("ultimo_id_archivado") or 0) + 1
        ts = ahora()
        h = _hash_fila(anterior, ts, usuario_id, accion, detalle, ip)
        c.execute(
            "INSERT INTO auditoria (id, ts, usuario_id, accion, detalle, ip, hash_anterior, hash) VALUES (?,?,?,?,?,?,?,?)",
            (nuevo_id, ts, usuario_id, accion, detalle, ip, anterior, h),
        )
        _espejo_siem(ts, usuario_id, accion, detalle, ip, h)


def _espejo_siem(ts, usuario_id, accion, detalle, ip, h):
    """Copia cada evento como una línea JSON para que un SIEM (Wazuh, Graylog) la recoja."""
    from config import LOG_SIEM
    if not LOG_SIEM:
        return
    try:
        LOG_SIEM.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_SIEM, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": ts, "app": "fricke-store", "usuario_id": usuario_id, "accion": accion,
                                 "detalle": detalle, "ip": ip, "hash": h}, ensure_ascii=False) + "\n")
    except OSError:
        pass  # el espejo nunca debe impedir registrar en la bitácora principal


def verificar_auditoria() -> dict:
    # Si se archivaron registros antiguos, la cadena continúa desde el ancla guardada.
    ancla = leer_ajuste("ancla_auditoria", GENESIS)
    with bd() as c:
        anterior = ancla
        n = 0
        for f in c.execute("SELECT * FROM auditoria ORDER BY id"):
            n += 1
            esperado = _hash_fila(anterior, f["ts"], f["usuario_id"], f["accion"], f["detalle"], f["ip"])
            if f["hash_anterior"] != anterior or f["hash"] != esperado:
                return {"integra": False, "registros": n, "falla_en_id": f["id"]}
            anterior = f["hash"]
        return {"integra": True, "registros": n, "ultimo_hash": anterior}


def archivar_auditoria(dias: int, carpeta) -> dict:
    """Mueve a un archivo sellado los registros más antiguos que `dias`, sin romper la cadena:
    el hash del último registro archivado queda como ancla para verificar lo que sigue."""
    from datetime import timedelta
    from pathlib import Path
    limite = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat(timespec="seconds")
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    with _lock_auditoria, bd() as c:
        filas = c.execute("SELECT * FROM auditoria WHERE ts < ? ORDER BY id", (limite,)).fetchall()
        if not filas:
            return {"archivados": 0}
        archivo = carpeta / f"bitacora-hasta-{filas[-1]['ts'][:10]}-id{filas[-1]['id']}.jsonl"
        with open(archivo, "w", encoding="utf-8") as fh:
            for f in filas:
                fh.write(json.dumps(dict(f), ensure_ascii=False) + "\n")
        sello = hashlib.sha256(archivo.read_bytes()).hexdigest()
        c.execute("DELETE FROM auditoria WHERE id <= ?", (filas[-1]["id"],))
        c.execute("INSERT OR REPLACE INTO ajustes (clave, valor, actualizado) VALUES ('ancla_auditoria', ?, ?)",
                  (filas[-1]["hash"], ahora()))
        c.execute("INSERT OR REPLACE INTO ajustes (clave, valor, actualizado) VALUES ('ultimo_id_archivado', ?, ?)",
                  (str(filas[-1]["id"]), ahora()))
    auditar("bitacora_archivada", None, f"{len(filas)} registros en {archivo.name} sha256 {sello}")
    return {"archivados": len(filas), "archivo": str(archivo), "sha256": sello}
