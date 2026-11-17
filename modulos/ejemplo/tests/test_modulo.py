"""Pruebas propias del módulo: lo que hace y quién puede hacerlo. Correr con `pytest modulos/ejemplo`.
Las reglas comunes (sesión, perfiles, ícono, diseño, Ley 21.719) ya las prueba tests/test_reglas_modulos.py."""
import pytest

from conftest import cliente, habilitar_modulo, nuevo_usuario

CLAVE = "ejemplo"
API = f"/api/m/{CLAVE}"


@pytest.fixture
def personas():
    habilitar_modulo(CLAVE, "admin", "funcionario")
    return nuevo_usuario("admin", "Ana Jefa"), nuevo_usuario("funcionario", "Beto Lector")


def test_admin_publica_y_funcionario_lee(personas):
    admin, func = personas
    r = cliente(admin).post(f"{API}/avisos", json={"titulo": "Turnos de diciembre", "texto": "Ya están publicados."})
    assert r.status_code == 200
    avisos = cliente(func).get(f"{API}/avisos").json()
    aviso = next(a for a in avisos if a["id"] == r.json()["id"])
    assert aviso["autor"] == "Ana Jefa" and aviso["puede_borrar"] is False


def test_funcionario_no_publica_ni_borra_lo_ajeno(personas):
    admin, func = personas
    aid = cliente(admin).post(f"{API}/avisos", json={"titulo": "Aviso", "texto": "Texto del aviso"}).json()["id"]
    tc = cliente(func)
    assert tc.post(f"{API}/avisos", json={"titulo": "Hola", "texto": "No debería"}).status_code == 403
    assert tc.delete(f"{API}/avisos/{aid}").status_code == 403


def test_validacion_de_campos(personas):
    admin, _ = personas
    assert cliente(admin).post(f"{API}/avisos", json={"titulo": "x", "texto": "y"}).status_code == 422


def test_mis_avisos_y_descarga_de_mis_datos(personas):
    admin, _ = personas
    tc = cliente(admin)
    tc.post(f"{API}/avisos", json={"titulo": "Solo mío", "texto": "Texto propio"})
    assert all(a["autor_id"] == admin["id"] for a in tc.get(f"{API}/avisos?mios=1").json())
    datos = tc.get("/api/cuenta/exportar").json()
    assert any(a["titulo"] == "Solo mío" for a in datos["modulos"][CLAVE]["datos"]["avisos_publicados"])
