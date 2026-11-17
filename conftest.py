"""Entorno de pruebas: una base PostgreSQL desechable, creada al empezar y borrada al terminar.

  pytest                  # todas las pruebas (portal, plataforma y cada módulo)
  pytest modulos/ejemplo  # solo un módulo
  pytest tests            # solo el portal y las reglas comunes

Necesita PostgreSQL corriendo (en desarrollo: docker compose up -d). Nunca toca la base de trabajo.
"""
import itertools
import os
import sys
import tempfile
from pathlib import Path

import psycopg
import pytest

RAIZ = Path(__file__).resolve().parent
BASE_PRUEBAS = "fricke_pruebas"
URL_ADMIN = os.environ.get("ECO_PRUEBAS_ADMIN_URL", "postgresql://fricke:fricke_desarrollo@127.0.0.1:5432/postgres")
CLAVE = "frase de prueba muy larga y segura"

# --- la base y la configuración se fijan ANTES de importar el portal (config.py las lee al importarse)
with psycopg.connect(URL_ADMIN, autocommit=True) as _c:
    _c.execute(f'DROP DATABASE IF EXISTS "{BASE_PRUEBAS}" WITH (FORCE)')
    _c.execute(f'CREATE DATABASE "{BASE_PRUEBAS}"')
os.environ.update({
    "ECO_DATABASE_URL": URL_ADMIN.rsplit("/", 1)[0] + "/" + BASE_PRUEBAS,
    "ECO_DATOS_DIR": tempfile.mkdtemp(prefix="fricke-pruebas-"),
    "ECO_LOG_SIEM": "",
    "ECO_MFA_PERFILES": "",      # el segundo factor se prueba aparte, exigiéndolo a una persona
    "ECO_ESTABLECIMIENTO": "fricke",
})
sys.path.insert(0, str(RAIZ / "backend"))
sys.path.insert(0, str(RAIZ))

from fastapi.testclient import TestClient  # noqa: E402

import app as portal  # noqa: E402  (crea el esquema y carga los módulos)
import config as cfg  # noqa: E402
import plataforma  # noqa: E402
from db import ahora, bd  # noqa: E402
from seguridad import _dv, hash_clave  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    from db import pool
    pool().close()
    with psycopg.connect(URL_ADMIN, autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{BASE_PRUEBAS}" WITH (FORCE)')


_correlativo = itertools.count(10_000_001)


def nuevo_usuario(rol: str = "funcionario", nombre: str = "Persona Prueba") -> dict:
    """Crea una cuenta lista para usar (clave definitiva y aviso leído). Devuelve id, rut y rol."""
    cuerpo = str(next(_correlativo))
    rut = f"{cuerpo}-{_dv(cuerpo)}"
    with bd() as c:
        uid = c.execute("INSERT INTO usuarios (rut, nombre, rol, clave_hash, debe_cambiar_clave, creado_en) "
                        "VALUES (?,?,?,?,0,?)", (rut, nombre, rol, hash_clave(CLAVE), ahora())).lastrowid
        c.execute("INSERT INTO aceptaciones_aviso VALUES (?,?,?)", (uid, cfg.VERSION_AVISO, ahora()))
    return {"id": uid, "rut": rut, "rol": rol}


def cliente(usuario: dict | None = None) -> TestClient:
    """Navegador de prueba; con `usuario`, ya ingresado. Envía la cabecera anti-CSRF del portal."""
    tc = TestClient(portal.app, headers={"X-Ecosistema": "1"})
    if usuario:
        r = tc.post("/api/auth/login", json={"rut": usuario["rut"], "clave": CLAVE})
        assert r.status_code == 200, r.text
        assert r.json()["mfa"] == 0, "la cuenta de prueba no debería pedir segundo factor"
    return tc


def habilitar_modulo(clave: str, *roles: str):
    """Publica el módulo para los perfiles indicados (como lo haría un administrador en el panel)."""
    with bd() as c:
        mid = c.execute("SELECT id FROM modulos WHERE clave=?", (clave,)).fetchone()["id"]
        c.execute("UPDATE modulos SET activo=1, eipd_aprobada=1 WHERE id=?", (mid,))
        c.execute("DELETE FROM modulos_rol WHERE modulo_id=?", (mid,))
        c.executemany("INSERT INTO modulos_rol VALUES (?,?)", [(mid, r) for r in roles])


def deshabilitar_modulo(clave: str):
    with bd() as c:
        c.execute("UPDATE modulos SET activo=0 WHERE clave=?", (clave,))


@pytest.fixture
def admin():
    return nuevo_usuario("admin", "Ana Administradora")


@pytest.fixture
def funcionario():
    return nuevo_usuario("funcionario", "Beto Funcionario")
