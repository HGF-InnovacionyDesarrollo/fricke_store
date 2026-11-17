"""Base de datos PostgreSQL y bitácora de auditoría encadenada (a prueba de manipulación).

Una sola base con un esquema por dueño: "portal" para el núcleo y "m_<clave>" para cada módulo.
Las consultas se escriben con marcadores `?` (como en el resto del código); `Conexion` los traduce.
"""
import hashlib
import json
import re
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg_pool import ConnectionPool

from config import DATABASE_URL, ESQUEMA_PORTAL

GENESIS = "0" * 64
MIGRACIONES_PORTAL = Path(__file__).parent / "migraciones"
MIGRACION_VALIDA = re.compile(r"(\d{3})_[a-z0-9_]+\.sql")
_ID_AUDITORIA = 715_001  # llave del candado consultivo que serializa la bitácora entre procesos


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ filas y conexión
class Fila(dict):
    """Fila que se lee por nombre (f["rut"]) o por posición (f[0]), como sqlite3.Row."""
    __slots__ = ("_valores",)

    def __getitem__(self, k):
        if isinstance(k, int):
            return self._valores[k]
        return dict.__getitem__(self, k)


def _fabrica_filas(cursor):
    nombres = [d.name for d in cursor.description] if cursor.description else []

    def hacer(valores):
        f = Fila(zip(nombres, valores))
        f._valores = valores
        return f
    return hacer


def _sql(consulta: str) -> str:
    # Marcadores al estilo SQLite (?) → psycopg (%s). Los % literales se escapan antes.
    return consulta.replace("%", "%%").replace("?", "%s")


def _parametros(params):
    if params is None:
        return None
    return tuple(int(p) if isinstance(p, bool) else p for p in params)


class Cursor:
    def __init__(self, cur, lastrowid=None):
        self._cur, self.lastrowid = cur, lastrowid

    @property
    def rowcount(self) -> int:
        return self._cur.rowcount

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self._cur)


class Conexion:
    """Envoltorio mínimo sobre psycopg con la interfaz que usa el portal (execute, executemany, lastrowid)."""

    def __init__(self, conn: psycopg.Connection):
        self._c = conn

    def execute(self, consulta: str, params=None) -> Cursor:
        cur = self._c.cursor(row_factory=_fabrica_filas)
        q = consulta.strip().rstrip(";")
        devolver_id = q[:6].upper() == "INSERT" and " RETURNING " not in q.upper()
        if devolver_id:
            q += " RETURNING *"
        cur.execute(_sql(q), _parametros(params))
        lastrowid = None
        if devolver_id:
            fila = cur.fetchone()
            lastrowid = fila.get("id") if fila else None
        return Cursor(cur, lastrowid)

    def executemany(self, consulta: str, filas):
        with self._c.cursor() as cur:
            cur.executemany(_sql(consulta), [_parametros(f) for f in filas])

    def script(self, sql: str):
        """Ejecuta un archivo SQL completo (migraciones). Sin marcadores."""
        self._c.execute(sql)

    def commit(self):
        self._c.commit()

    def rollback(self):
        self._c.rollback()


_pool: ConnectionPool | None = None
_lock_pool = threading.Lock()


def _restablecer(conn: psycopg.Connection):
    # Al devolver una conexión al pool: sin rol de módulo y de vuelta al esquema del portal.
    conn.execute(f"RESET ROLE; SET search_path TO {ESQUEMA_PORTAL}")
    conn.commit()


def pool() -> ConnectionPool:
    global _pool
    with _lock_pool:
        if _pool is None:
            _pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=20, open=True,
                                   kwargs={"options": f"-c search_path={ESQUEMA_PORTAL} -c timezone=UTC", "connect_timeout": 10},
                                   reset=_restablecer)
        return _pool


@contextmanager
def bd(esquema: str | None = None, rol: str | None = None):
    """Conexión del pool. Confirma al salir sin error; si hay excepción, revierte.
    Con `esquema`/`rol` la conexión queda acotada a un módulo (ver plataforma.bd_modulo)."""
    with pool().connection() as conn:
        if rol:
            conn.execute(f'SET ROLE "{rol}"')
        if esquema:
            conn.execute(f'SET search_path TO "{esquema}"')
        c = Conexion(conn)
        try:
            yield c
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# ------------------------------------------------------------------ migraciones numeradas
def aplicar_migraciones(esquema: str, carpeta: Path, rol: str | None = None) -> list[str]:
    """Aplica en orden las migraciones NNN_*.sql pendientes del esquema. Una migración ya aplicada no
    se puede editar: si su contenido cambió, se detiene (los cambios van en una migración nueva)."""
    archivos = sorted(p for p in Path(carpeta).glob("*.sql") if MIGRACION_VALIDA.fullmatch(p.name))
    numeros = [int(p.name[:3]) for p in archivos]
    if numeros != list(range(1, len(numeros) + 1)):
        raise RuntimeError(f"migraciones de '{esquema}' mal numeradas: deben ser 001, 002, 003… sin saltos.")
    aplicadas = []
    with bd() as c:
        c.execute(f'CREATE SCHEMA IF NOT EXISTS "{esquema}"' + (f' AUTHORIZATION "{rol}"' if rol else ""))
    with bd(esquema=esquema, rol=rol) as c:
        c.script("CREATE TABLE IF NOT EXISTS _migraciones (version INTEGER PRIMARY KEY, archivo TEXT NOT NULL, "
                 "sha256 TEXT NOT NULL, aplicada_en TEXT NOT NULL)")
        c.commit()
        # Candado por esquema: si dos procesos arrancan a la vez, solo uno migra.
        c.execute("SELECT pg_advisory_xact_lock(hashtext(?))", (esquema,))
        hechas = {f["version"]: f for f in c.execute("SELECT * FROM _migraciones")}
        for p in archivos:
            v, sql = int(p.name[:3]), p.read_text(encoding="utf-8")
            huella = hashlib.sha256(sql.encode()).hexdigest()
            if v in hechas:
                if hechas[v]["sha256"] != huella:
                    raise RuntimeError(f"la migración {p.name} de '{esquema}' cambió después de aplicarse; "
                                       "no se editan migraciones aplicadas, se agrega una nueva.")
                continue
            c.script(sql)
            c.execute("INSERT INTO _migraciones VALUES (?,?,?,?)", (v, p.name, huella, ahora()))
            aplicadas.append(p.name)
    return aplicadas


def inicializar():
    aplicar_migraciones(ESQUEMA_PORTAL, MIGRACIONES_PORTAL)


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
    with bd() as c:
        c.execute("SELECT pg_advisory_xact_lock(?)", (_ID_AUDITORIA,))
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
        if nuevo_id is None:
            c.execute("INSERT INTO auditoria (ts, usuario_id, accion, detalle, ip, hash_anterior, hash) VALUES (?,?,?,?,?,?,?)",
                      (ts, usuario_id, accion, detalle, ip, anterior, h))
        else:
            c.execute("INSERT INTO auditoria (id, ts, usuario_id, accion, detalle, ip, hash_anterior, hash) VALUES (?,?,?,?,?,?,?,?)",
                      (nuevo_id, ts, usuario_id, accion, detalle, ip, anterior, h))
            c.execute("SELECT setval(pg_get_serial_sequence('auditoria', 'id'), ?)", (nuevo_id,))
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
    with bd() as c:
        c.execute("SELECT pg_advisory_xact_lock(?)", (_ID_AUDITORIA,))
        filas = c.execute("SELECT * FROM auditoria WHERE ts < ? ORDER BY id", (limite,)).fetchall()
        if not filas:
            return {"archivados": 0}
        archivo = carpeta / f"bitacora-hasta-{filas[-1]['ts'][:10]}-id{filas[-1]['id']}.jsonl"
        with open(archivo, "w", encoding="utf-8") as fh:
            for f in filas:
                fh.write(json.dumps(dict(f), ensure_ascii=False) + "\n")
        sello = hashlib.sha256(archivo.read_bytes()).hexdigest()
        c.execute("DELETE FROM auditoria WHERE id <= ?", (filas[-1]["id"],))
        c.execute("INSERT INTO ajustes (clave, valor, actualizado) VALUES ('ancla_auditoria', ?, ?) "
                  "ON CONFLICT (clave) DO UPDATE SET valor=excluded.valor, actualizado=excluded.actualizado",
                  (filas[-1]["hash"], ahora()))
        c.execute("INSERT INTO ajustes (clave, valor, actualizado) VALUES ('ultimo_id_archivado', ?, ?) "
                  "ON CONFLICT (clave) DO UPDATE SET valor=excluded.valor, actualizado=excluded.actualizado",
                  (str(filas[-1]["id"]), ahora()))
    auditar("bitacora_archivada", None, f"{len(filas)} registros en {archivo.name} sha256 {sello}")
    return {"archivados": len(filas), "archivo": str(archivo), "sha256": sello}
