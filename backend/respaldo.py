"""Respaldos cifrados de Fricke Store (Ley 21.719 art. 14 quinquies; DS 7/2023 art. 11; Ley 21.663 art. 8).

  python backend/respaldo.py crear      # respaldo cifrado + copia externa + rotación (programar a diario)
  python backend/respaldo.py probar     # descifra el último, verifica integridad y la cadena de la bitácora
  python backend/respaldo.py listar
  python backend/respaldo.py restaurar ARCHIVO   # deja la base restaurada junto a la actual, nunca la pisa

Regla 3-2-1: la base viva, el respaldo local cifrado y una copia en otro equipo (ECO_RESPALDO_COPIA).
La clave de cifrado (data/respaldo.key) debe guardarse además FUERA del servidor (bóveda o sobre sellado):
sin ella los respaldos no se pueden abrir.
"""
import gzip
import hashlib
import json
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from cryptography.fernet import Fernet, InvalidToken  # noqa: E402

import config as cfg  # noqa: E402
from db import GENESIS, _hash_fila, auditar, guardar_ajuste, inicializar  # noqa: E402

SUFIJO = ".db.gz.enc"


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


def respaldos() -> list[Path]:
    return sorted(cfg.RESPALDOS_DIR.glob(f"ecosistema-*{SUFIJO}"))


def crear() -> Path:
    inicializar()
    cfg.RESPALDOS_DIR.mkdir(parents=True, exist_ok=True)
    sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = cfg.RESPALDOS_DIR / f"ecosistema-{sello}{SUFIJO}"
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "copia.db"
        origen = sqlite3.connect(cfg.DB_PATH)
        dst = sqlite3.connect(copia)
        origen.backup(dst)  # copia consistente aunque el portal esté funcionando
        dst.close()
        origen.close()
        datos = gzip.compress(copia.read_bytes(), compresslevel=9)
    destino.write_bytes(_clave().encrypt(datos))
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
    # Rotación local
    for viejo in respaldos()[:-cfg.RESPALDOS_A_CONSERVAR]:
        viejo.unlink(missing_ok=True)
        viejo.with_suffix(viejo.suffix + ".sha256").unlink(missing_ok=True)
    guardar_ajuste("ultimo_respaldo", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    auditar("respaldo_realizado", None, f"{destino.name} sha256 {huella[:16]}…{externa}")
    print(f"Respaldo creado: {destino} ({destino.stat().st_size // 1024} KB){externa}")
    return destino


def _verificar_cadena(conn: sqlite3.Connection) -> dict:
    conn.row_factory = sqlite3.Row
    f = conn.execute("SELECT valor FROM ajustes WHERE clave='ancla_auditoria'").fetchone()
    anterior = f["valor"] if f else GENESIS
    n = 0
    for r in conn.execute("SELECT * FROM auditoria ORDER BY id"):
        n += 1
        if r["hash_anterior"] != anterior or r["hash"] != _hash_fila(anterior, r["ts"], r["usuario_id"], r["accion"], r["detalle"], r["ip"]):
            return {"integra": False, "registros": n, "falla_en_id": r["id"]}
        anterior = r["hash"]
    return {"integra": True, "registros": n}


def _descifrar(archivo: Path, destino: Path):
    esperado = archivo.with_suffix(archivo.suffix + ".sha256")
    if esperado.exists() and esperado.read_text(encoding="utf-8").split()[0] != _sha256(archivo):
        raise SystemExit(f"El archivo {archivo.name} no coincide con su huella SHA-256: está dañado o fue alterado.")
    try:
        destino.write_bytes(gzip.decompress(_clave().decrypt(archivo.read_bytes())))
    except InvalidToken:
        raise SystemExit("No se pudo descifrar: la clave no corresponde a este respaldo.")


def probar(archivo: Path | None = None):
    archivo = archivo or (respaldos() or [None])[-1]
    if not archivo:
        raise SystemExit("No hay respaldos para probar.")
    with tempfile.TemporaryDirectory() as tmp:
        restaurada = Path(tmp) / "prueba.db"
        try:
            _descifrar(archivo, restaurada)
            conn = sqlite3.connect(restaurada)
            integridad = conn.execute("PRAGMA integrity_check").fetchone()[0]
            usuarios = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
            cadena = _verificar_cadena(conn)
            conn.close()
        except SystemExit as e:
            auditar("respaldo_fallido", None, f"prueba de {archivo.name}: {e}")
            raise
    ok = integridad == "ok" and cadena["integra"]
    detalle = f"{archivo.name}: integridad {integridad}, {usuarios} usuarios, bitácora {'íntegra' if cadena['integra'] else 'ALTERADA'} ({cadena['registros']} registros)"
    if ok:
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
    destino = cfg.DB_PATH.with_name(f"restaurada-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db")
    _descifrar(archivo, destino)
    auditar("respaldo_probado", None, f"restauración manual de {archivo.name} en {destino.name}")
    print(f"Base restaurada en {destino}.\nPara usarla: detén el portal, renombra {cfg.DB_PATH.name} (consérvalo) "
          f"y renombra {destino.name} a {cfg.DB_PATH.name}. Luego vuelve a iniciar.")


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
