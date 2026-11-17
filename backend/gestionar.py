"""Administración por consola (mientras no exista un módulo de administración).

  python backend/gestionar.py crear --rut 12.345.678-5 --nombre "Ana Pérez" --cargo "Enfermera" --unidad "UPC" [--admin]
  python backend/gestionar.py restablecer --rut 12.345.678-5     # nueva clave temporal
  python backend/gestionar.py desactivar --rut 12.345.678-5
  python backend/gestionar.py desbloquear --rut 12.345.678-5
  python backend/gestionar.py listar
  python backend/gestionar.py verificar-auditoria
  python backend/gestionar.py archivar-bitacora                  # según ECO_RETENCION_BITACORA_DIAS
  python backend/gestionar.py solicitudes                         # solicitudes de derechos pendientes

Módulos (ver docs/MODULOS.md):
  python backend/gestionar.py modulos                             # valida, migra y lista los módulos con código
  python backend/gestionar.py nuevo-modulo --clave farmacia --nombre "Farmacia"   # copia la plantilla
  python backend/gestionar.py permiso --rut 12.345.678-5 --permiso ejemplo.moderar [--revocar]
  python backend/gestionar.py depurar                             # aplica los plazos de conservación (a diario)

PostgreSQL:
  python backend/gestionar.py importar-sqlite [--origen data/ecosistema.db]   # traslado único desde la versión SQLite
"""
import argparse
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))

from db import ahora, auditar, bd, inicializar, verificar_auditoria  # noqa: E402
from seguridad import clave_temporal, formatear_rut, hash_clave, normalizar_rut  # noqa: E402


def _rut(texto):
    r = normalizar_rut(texto)
    if not r:
        sys.exit(f"RUT no válido: {texto}")
    return r


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    inicializar()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crear")
    c.add_argument("--rut", required=True)
    c.add_argument("--nombre", required=True)
    c.add_argument("--correo")
    c.add_argument("--cargo")
    c.add_argument("--unidad")
    c.add_argument("--admin", action="store_true")
    c.add_argument("--dpd", action="store_true", help="perfil Delegado de Protección de Datos")
    for nombre in ("restablecer", "desactivar", "desbloquear"):
        sub.add_parser(nombre).add_argument("--rut", required=True)
    sub.add_parser("listar")
    sub.add_parser("verificar-auditoria")
    sub.add_parser("archivar-bitacora", help="archiva lo más antiguo que la retención configurada")
    sub.add_parser("solicitudes")
    sub.add_parser("modulos")
    im = sub.add_parser("importar-sqlite", help="traslada los datos de la base SQLite anterior a PostgreSQL")
    im.add_argument("--origen", help="ruta del ecosistema.db (por defecto data/ecosistema.db)")
    sub.add_parser("depurar", help="aplica el plazo de conservación de cada módulo")
    nm = sub.add_parser("nuevo-modulo", help="crea modulos/<clave>/ a partir del módulo de ejemplo")
    nm.add_argument("--clave", required=True)
    nm.add_argument("--nombre", required=True)
    pm = sub.add_parser("permiso", help="otorga o revoca un permiso interno de módulo a una persona")
    pm.add_argument("--rut", required=True)
    pm.add_argument("--permiso", required=True)
    pm.add_argument("--revocar", action="store_true")
    a = p.parse_args()

    if a.cmd == "crear":
        rut, clave = _rut(a.rut), clave_temporal()
        with bd() as db:
            if db.execute("SELECT 1 FROM usuarios WHERE rut=?", (rut,)).fetchone():
                sys.exit("Ya existe un usuario con ese RUT.")
            uid = db.execute(
                "INSERT INTO usuarios (rut, nombre, correo, cargo, unidad, rol, clave_hash, creado_en) VALUES (?,?,?,?,?,?,?,?)",
                (rut, a.nombre, a.correo, a.cargo, a.unidad, "admin" if a.admin else "dpd" if a.dpd else "funcionario", hash_clave(clave), ahora()),
            ).lastrowid
        auditar("usuario_creado", uid, "consola")
        print(f"Usuario creado: {formatear_rut(rut)} - {a.nombre}")
        print(f"Clave temporal (entregar en persona; se pide cambiarla al primer ingreso): {clave}")

    elif a.cmd == "restablecer":
        rut, clave = _rut(a.rut), clave_temporal()
        with bd() as db:
            u = db.execute("SELECT id FROM usuarios WHERE rut=?", (rut,)).fetchone() or sys.exit("No existe.")
            db.execute("UPDATE usuarios SET clave_hash=?, debe_cambiar_clave=1, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?",
                       (hash_clave(clave), u["id"]))
            db.execute("DELETE FROM sesiones WHERE usuario_id=?", (u["id"],))
        auditar("clave_restablecida", u["id"], "consola")
        print(f"Clave temporal: {clave}")

    elif a.cmd in ("desactivar", "desbloquear"):
        rut = _rut(a.rut)
        with bd() as db:
            u = db.execute("SELECT id FROM usuarios WHERE rut=?", (rut,)).fetchone() or sys.exit("No existe.")
            if a.cmd == "desactivar":
                db.execute("UPDATE usuarios SET activo=0 WHERE id=?", (u["id"],))
                db.execute("DELETE FROM sesiones WHERE usuario_id=?", (u["id"],))
            else:
                db.execute("UPDATE usuarios SET intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?", (u["id"],))
        auditar(f"usuario_{a.cmd.rstrip('r')}do", u["id"], "consola")
        print("Listo.")

    elif a.cmd == "listar":
        with bd() as db:
            for u in db.execute("SELECT * FROM usuarios ORDER BY nombre"):
                estado = "activo" if u["activo"] else "INACTIVO"
                print(f"{formatear_rut(u['rut']):>13}  {u['nombre']:<30} {u['rol']:<12} {estado}")

    elif a.cmd == "verificar-auditoria":
        r = verificar_auditoria()
        print("Bitácora íntegra." if r["integra"] else f"¡ALERTA! Bitácora alterada en el registro #{r['falla_en_id']}.")
        print(r)

    elif a.cmd == "archivar-bitacora":
        import config as cfg
        from db import archivar_auditoria
        r = archivar_auditoria(cfg.RETENCION_BITACORA_DIAS, cfg.DATOS_DIR / "archivo_bitacora")
        print(r)
        print(verificar_auditoria())

    elif a.cmd == "solicitudes":
        with bd() as db:
            for s in db.execute("SELECT s.*, u.nombre FROM solicitudes_derechos s JOIN usuarios u ON u.id=s.usuario_id "
                                "WHERE estado IN ('recibida','en_revision') ORDER BY vence"):
                print(f"#{s['id']} {s['tipo']:<14} {s['nombre']:<28} vence {s['vence']}  {s['detalle'] or ''}")


    elif a.cmd == "modulos":
        import plataforma
        reg = plataforma.cargar_modulos()
        with bd() as db:
            filas = {f["clave"]: f for f in db.execute("SELECT * FROM modulos")}
        for clave, mod in reg.items():
            f, m = filas.get(clave), mod.manifiesto
            estado = ("activo" if f["activo"] else "inactivo") if f else "?"
            eipd = (" · EIPD " + ("aprobada" if f["eipd_aprobada"] else "PENDIENTE")) if m.tratamiento.datos_sensibles else ""
            print(f"{clave:<20} v{m.version:<8} {estado:<9} {m.nombre}{eipd}")
        if not reg:
            print("No hay módulos con código en modulos/.")

    elif a.cmd == "depurar":
        import plataforma
        plataforma.cargar_modulos()
        print(plataforma.depurar_todos() or "Ningún módulo define depurar().")

    elif a.cmd == "importar-sqlite":
        _importar_sqlite(a.origen)

    elif a.cmd == "nuevo-modulo":
        _nuevo_modulo(a.clave, a.nombre)

    elif a.cmd == "permiso":
        import plataforma
        reg = plataforma.cargar_modulos()
        clave_mod = a.permiso.split(".")[0]
        if clave_mod not in reg or a.permiso not in reg[clave_mod].manifiesto.permisos:
            sys.exit(f"Permiso desconocido: {a.permiso}")
        rut = _rut(a.rut)
        with bd() as db:
            u = db.execute("SELECT id FROM usuarios WHERE rut=?", (rut,)).fetchone() or sys.exit("No existe.")
            if a.revocar:
                db.execute("DELETE FROM permisos_usuario WHERE usuario_id=? AND permiso=?", (u["id"], a.permiso))
            else:
                db.execute("INSERT INTO permisos_usuario (usuario_id, permiso, otorgado_en) VALUES (?,?,?) ON CONFLICT DO NOTHING",
                           (u["id"], a.permiso, ahora()))
        auditar("permiso_revocado" if a.revocar else "permiso_otorgado", u["id"], f"{a.permiso} (consola)")
        print("Listo.")


TABLAS_PORTAL = ["usuarios", "sesiones", "aceptaciones_aviso", "solicitudes_derechos", "solicitudes_cuenta",
                 "solicitudes_clave", "modulos", "modulos_rol", "modulos_usuario", "permisos_usuario", "ajustes",
                 "incidentes", "auditoria"]


def _importar_sqlite(origen: str | None):
    """Copia tal cual (mismos ids y textos) cada tabla del portal desde SQLite. La bitácora conserva su
    cadena de hashes porque se calculó sobre esos mismos textos. Solo funciona sobre un portal vacío."""
    import sqlite3
    from pathlib import Path
    import config as cfg
    ruta = Path(origen) if origen else cfg.SQLITE_ANTERIOR
    if not ruta.exists():
        sys.exit(f"No existe {ruta}.")
    with bd() as db:
        if db.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone() or db.execute("SELECT 1 FROM auditoria LIMIT 1").fetchone():
            sys.exit("PostgreSQL ya tiene datos: la importación solo se hace una vez, sobre un portal vacío.")
    src = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    existentes = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    resumen = {}
    with bd() as db:
        for tabla in TABLAS_PORTAL:
            if tabla not in existentes:
                continue
            destino = {r["column_name"] for r in db.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema=? AND table_name=?",
                (cfg.ESQUEMA_PORTAL, tabla))}
            cols = [r[1] for r in src.execute(f"PRAGMA table_info({tabla})") if r[1] in destino]
            filas = [tuple(f[c] for c in cols) for f in src.execute(f"SELECT {', '.join(cols)} FROM {tabla}")]
            if filas:
                db.executemany(f"INSERT INTO {tabla} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", filas)
            if "id" in cols:
                db.execute(f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                           f"GREATEST((SELECT COALESCE(MAX(id), 0) FROM {tabla}), 1))")
            resumen[tabla] = len(filas)
    src.close()
    for t, n in resumen.items():
        print(f"{t:<22} {n:>7} filas")
    r = verificar_auditoria()
    print("Bitácora íntegra tras el traslado." if r["integra"] else f"¡ALERTA! La bitácora no verifica (registro #{r['falla_en_id']}).")
    auditar("datos_importados_sqlite", None, f"{sum(resumen.values())} filas desde {ruta.name}")
    print(f"Listo. Conserva {ruta} como respaldo hasta confirmar que todo funciona; después guárdalo cifrado o elimínalo.")


def _nuevo_modulo(clave: str, nombre: str):
    import re
    import shutil
    import config as cfg
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", clave) or len(clave) > 40:
        sys.exit("La clave usa minúsculas, números y _ (ej.: farmacia, control_temperatura).")
    origen, destino = cfg.MODULOS_DIR / "ejemplo", cfg.MODULOS_DIR / clave
    if destino.exists():
        sys.exit(f"Ya existe {destino}.")
    shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("__pycache__"))
    for archivo in destino.rglob("*"):
        if archivo.is_file() and archivo.suffix in (".py", ".js", ".html", ".css", ".sql", ".md"):
            t = archivo.read_text(encoding="utf-8")
            t = t.replace('CLAVE = "ejemplo"', f'CLAVE = "{clave}"').replace("/m/ejemplo/", f"/m/{clave}/")
            t = t.replace('const CLAVE = "ejemplo";', f'const CLAVE = "{clave}";').replace("Tablón de avisos", nombre)
            archivo.write_text(t, encoding="utf-8")
    print(f"Módulo creado en {destino}.")
    print("Siguientes pasos: completa la ficha de tratamiento en manifiesto.py, reemplaza las tablas de "
          "migraciones/001_inicial.sql y la API de api.py, y revisa la lista de docs/MODULOS.md antes de publicarlo.")


if __name__ == "__main__":
    main()
