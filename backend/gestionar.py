"""Administración por consola (mientras no exista un módulo de administración).

  python backend/gestionar.py crear --rut 12.345.678-5 --nombre "Ana Pérez" --cargo "Enfermera" --unidad "UPC" [--admin]
  python backend/gestionar.py restablecer --rut 12.345.678-5     # nueva clave temporal
  python backend/gestionar.py desactivar --rut 12.345.678-5
  python backend/gestionar.py desbloquear --rut 12.345.678-5
  python backend/gestionar.py listar
  python backend/gestionar.py verificar-auditoria
  python backend/gestionar.py solicitudes                         # solicitudes de derechos pendientes
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
    for nombre in ("restablecer", "desactivar", "desbloquear"):
        sub.add_parser(nombre).add_argument("--rut", required=True)
    sub.add_parser("listar")
    sub.add_parser("verificar-auditoria")
    sub.add_parser("solicitudes")
    a = p.parse_args()

    if a.cmd == "crear":
        rut, clave = _rut(a.rut), clave_temporal()
        with bd() as db:
            if db.execute("SELECT 1 FROM usuarios WHERE rut=?", (rut,)).fetchone():
                sys.exit("Ya existe un usuario con ese RUT.")
            uid = db.execute(
                "INSERT INTO usuarios (rut, nombre, correo, cargo, unidad, rol, clave_hash, creado_en) VALUES (?,?,?,?,?,?,?,?)",
                (rut, a.nombre, a.correo, a.cargo, a.unidad, "admin" if a.admin else "funcionario", hash_clave(clave), ahora()),
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

    elif a.cmd == "solicitudes":
        with bd() as db:
            for s in db.execute("SELECT s.*, u.nombre FROM solicitudes_derechos s JOIN usuarios u ON u.id=s.usuario_id "
                                "WHERE estado IN ('recibida','en_revision') ORDER BY vence"):
                print(f"#{s['id']} {s['tipo']:<14} {s['nombre']:<28} vence {s['vence']}  {s['detalle'] or ''}")


if __name__ == "__main__":
    main()
