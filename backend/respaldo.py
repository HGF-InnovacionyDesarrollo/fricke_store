"""Respaldos cifrados de Fricke Store (Ley 21.719 art. 14 quinquies; DS 7/2023 art. 11; Ley 21.663 art. 8).

  python backend/respaldo.py crear      # pg_dump de toda la base (portal y módulos), cifrado + copia externa + rotación
  python backend/respaldo.py probar     # lo restaura en una base temporal, verifica la bitácora y la borra
  python backend/respaldo.py listar
  python backend/respaldo.py restaurar ARCHIVO   # lo restaura en una base NUEVA, nunca pisa la actual

Necesita pg_dump y pg_restore de la misma versión mayor del servidor (ECO_PG_DUMP / ECO_PG_RESTORE;
con Docker: "docker exec -i fricke-db pg_dump"). El usuario de la base necesita CREATEDB para probar y restaurar.

Regla 3-2-1: la base viva, el respaldo local cifrado y una copia en otro equipo (ECO_RESPALDO_COPIA).
La clave de cifrado (data/respaldo.key) debe guardarse además FUERA del servidor (bóveda o sobre sellado):
sin ella los respaldos no se pueden abrir.
"""
import gzip
import hashlib
import json
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg  # noqa: E402
from cryptography.fernet import Fernet, InvalidToken  # noqa: E402

import config as cfg  # noqa: E402
from db import GENESIS, _hash_fila, auditar, guardar_ajuste, inicializar  # noqa: E402

SUFIJO = ".dump.gz.enc"


def _clave() -> Fernet:
    archivo = cfg.RESPALDO_CLAVE_ARCHIVO
    if not archivo.exists():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(Fernet.generate_key())
        print(f"Se generó una clave de cifrado nueva en {archivo}.")
        print("IMPORTANTE: guarda una copia de esta clave fuera del servidor; sin ella no se pueden restaurar los respaldos.")
    return Fernet(archivo.read_bytes().strip())


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _url_con_base(nombre: str) -> str:
    u = urlsplit(cfg.DATABASE_URL)
    return urlunsplit((u.scheme, u.netloc, "/" + nombre, u.query, u.fragment))


def _nombre_base() -> str:
    return urlsplit(cfg.DATABASE_URL).path.lstrip("/")


def _correr(comando: str, args: list[str], entrada: bytes | None = None) -> bytes:
    r = subprocess.run([*shlex.split(comando), *args], input=entrada, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"{comando} falló: {r.stderr.decode(errors='replace').strip()[:500]}")
    return r.stdout


def respaldos() -> list[Path]:
    return sorted(cfg.RESPALDOS_DIR.glob(f"fricke-*{SUFIJO}"))


def crear() -> Path:
    inicializar()
    cfg.RESPALDOS_DIR.mkdir(parents=True, exist_ok=True)
    sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = cfg.RESPALDOS_DIR / f"fricke-{sello}{SUFIJO}"
    # Formato custom: copia consistente aunque el portal esté funcionando; incluye el portal y todos los esquemas m_*.
    volcado = _correr(cfg.PG_DUMP, ["--format=custom", "--no-password", f"--dbname={cfg.DATABASE_URL}"])
    destino.write_bytes(_clave().encrypt(gzip.compress(volcado, compresslevel=9)))
    huella = _sha256(destino)
    destino.with_suffix(destino.suffix + ".sha256").write_text(f"{huella}  {destino.name}\n", encoding="utf-8")
    externa = ""
    if cfg.RESPALDO_COPIA_EXTERNA:
        try:
            dir_ext = Path(cfg.RESPALDO_COPIA_EXTERNA)
            dir_ext.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destino, dir_ext / destino.name)
            shutil.copy2(destino.with_suffix(destino.suffix + ".sha256"), dir_ext)
            externa = " · copia externa OK"
        except OSError as e:
            externa = f" · COPIA EXTERNA FALLÓ: {e}"
    for viejo in respaldos()[:-cfg.RESPALDOS_A_CONSERVAR]:
        viejo.unlink(missing_ok=True)
        viejo.with_suffix(viejo.suffix + ".sha256").unlink(missing_ok=True)
    guardar_ajuste("ultimo_respaldo", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    auditar("respaldo_realizado", None, f"{destino.name} sha256 {huella[:16]}…{externa}")
    print(f"Respaldo creado: {destino} ({destino.stat().st_size // 1024} KB){externa}")
    return destino


def _descifrar(archivo: Path) -> bytes:
    esperado = archivo.with_suffix(archivo.suffix + ".sha256")
    if esperado.exists() and esperado.read_text(encoding="utf-8").split()[0] != _sha256(archivo):
        raise SystemExit(f"El archivo {archivo.name} no coincide con su huella SHA-256: está dañado o fue alterado.")
    try:
        return gzip.decompress(_clave().decrypt(archivo.read_bytes()))
    except InvalidToken:
        raise SystemExit("No se pudo descifrar: la clave no corresponde a este respaldo.")


def _restaurar_en(nombre: str, volcado: bytes):
    with psycopg.connect(cfg.DATABASE_URL, autocommit=True) as c:
        c.execute(f'CREATE DATABASE "{nombre}"')
    _correr(cfg.PG_RESTORE, ["--no-password", "--exit-on-error", f"--dbname={_url_con_base(nombre)}"], volcado)


def _borrar_base(nombre: str):
    with psycopg.connect(cfg.DATABASE_URL, autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')


def _verificar(nombre: str) -> dict:
    with psycopg.connect(_url_con_base(nombre)) as conn:
        f = conn.execute("SELECT valor FROM portal.ajustes WHERE clave='ancla_auditoria'").fetchone()
        anterior, n = (f[0] if f else GENESIS), 0
        for (id_, ts, uid, accion, detalle, ip, h_ant, h) in conn.execute(
                "SELECT id, ts, usuario_id, accion, detalle, ip, hash_anterior, hash FROM portal.auditoria ORDER BY id"):
            n += 1
            if h_ant != anterior or h != _hash_fila(anterior, ts, uid, accion, detalle, ip):
                return {"integra": False, "registros": n, "falla_en_id": id_}
            anterior = h
        usuarios = conn.execute("SELECT COUNT(*) FROM portal.usuarios").fetchone()[0]
        esquemas = [r[0] for r in conn.execute(
            "SELECT nspname FROM pg_namespace WHERE starts_with(nspname, 'm_') ORDER BY 1")]
    return {"integra": True, "registros": n, "usuarios": usuarios, "modulos": esquemas}


def probar(archivo: Path | None = None):
    archivo = archivo or (respaldos() or [None])[-1]
    if not archivo:
        raise SystemExit("No hay respaldos para probar.")
    temporal = f"{_nombre_base()}_prueba_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        _restaurar_en(temporal, _descifrar(archivo))
        r = _verificar(temporal)
    except SystemExit as e:
        auditar("respaldo_fallido", None, f"prueba de {archivo.name}: {e}")
        raise
    finally:
        _borrar_base(temporal)
    detalle = (f"{archivo.name}: restaurado en base temporal, {r.get('usuarios', '?')} usuarios, "
               f"{len(r.get('modulos', []))} módulos, bitácora {'íntegra' if r['integra'] else 'ALTERADA'} "
               f"({r['registros']} registros)")
    if r["integra"]:
        guardar_ajuste("ultima_prueba_restauracion", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        auditar("respaldo_probado", None, detalle)
        print("Prueba de restauración EXITOSA — " + detalle)
    else:
        auditar("respaldo_fallido", None, detalle)
        raise SystemExit("Prueba de restauración FALLIDA — " + detalle)


def restaurar(nombre: str):
    archivo = Path(nombre)
    if not archivo.exists():
        archivo = cfg.RESPALDOS_DIR / nombre
    nueva = f"{_nombre_base()}_restaurada_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    _restaurar_en(nueva, _descifrar(archivo))
    auditar("respaldo_probado", None, f"restauración manual de {archivo.name} en la base {nueva}")
    print(f"Respaldo restaurado en la base nueva '{nueva}' (la actual no se tocó).\n"
          f"Para usarla: detén el portal, cambia el nombre de la base en ECO_DATABASE_URL a '{nueva}' y vuelve a iniciar.")


def listar():
    for r in respaldos():
        print(f"{r.name}  {r.stat().st_size // 1024:>7} KB")
    print(json.dumps({"total": len(respaldos())}))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "crear":
        crear()
    elif cmd == "probar":
        probar(Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif cmd == "listar":
        listar()
    elif cmd == "restaurar" and len(sys.argv) > 2:
        restaurar(sys.argv[2])
    else:
        print(__doc__)
