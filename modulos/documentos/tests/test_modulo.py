"""Pruebas propias de F+docs: lo que hace y quién puede hacerlo. Correr con `pytest modulos/documentos`.
Las reglas comunes (sesión, perfiles, ícono, diseño, Ley 21.719) ya las prueba tests/test_reglas_modulos.py."""
import base64

import pytest

import plataforma
from conftest import cliente, habilitar_modulo, nuevo_usuario
from db import ahora, bd

CLAVE = "documentos"
API = f"/api/m/{CLAVE}"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def b64(datos: bytes) -> str:
    return base64.b64encode(datos).decode()


def otorgar(usuario: dict, permiso: str):
    with bd() as c:
        c.execute("INSERT INTO permisos_usuario (usuario_id, permiso, otorgado_en) VALUES (?,?,?) ON CONFLICT DO NOTHING",
                  (usuario["id"], permiso, ahora()))


@pytest.fixture
def personas():
    habilitar_modulo(CLAVE, "admin", "funcionario")
    editora = nuevo_usuario("funcionario", "Ema Editora")
    otorgar(editora, f"{CLAVE}.administrar")
    return editora, nuevo_usuario("funcionario", "Leo Lector"), nuevo_usuario("admin", "Ada Admin")


def subir(tc, titulo="Protocolo de caídas", carpeta_id=None, datos=PDF, **extra):
    return tc.post(f"{API}/documentos", json={"titulo": titulo, "carpeta_id": carpeta_id,
                                              "nombre_archivo": "protocolo.pdf", "contenido": b64(datos), **extra})


def test_editora_organiza_y_lector_ve_y_descarga(personas):
    editora, lector, _ = personas
    te, tl = cliente(editora), cliente(lector)
    cid = te.post(f"{API}/carpetas", json={"nombre": "Calidad"}).json()["id"]
    sub = te.post(f"{API}/carpetas", json={"nombre": "Protocolos", "padre_id": cid}).json()["id"]
    did = subir(te, carpeta_id=sub, descripcion="Versión 2026").json()["id"]

    inicio = tl.get(f"{API}/carpetas/0").json()
    assert any(f["id"] == cid for f in inicio["subcarpetas"])
    contenido = tl.get(f"{API}/carpetas/{sub}").json()
    assert [r["nombre"] for r in contenido["ruta"]] == ["Calidad", "Protocolos"]
    doc = next(d for d in contenido["documentos"] if d["id"] == did)
    assert doc["actualizado_por"] == "Ema Editora" and doc["tamano"] == len(PDF)

    r = tl.get(f"{API}/documentos/{did}/archivo")
    assert r.status_code == 200 and r.content == PDF and r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("inline")
    assert tl.get(f"{API}/documentos/{did}/archivo?descargar=1").headers["content-disposition"].startswith("attachment")


def test_lector_y_admin_sin_permiso_no_administran(personas):
    editora, lector, admin = personas
    did = subir(cliente(editora)).json()["id"]
    for persona in (lector, admin):  # el perfil admin del portal tampoco administra documentos por defecto
        tc = cliente(persona)
        assert tc.post(f"{API}/carpetas", json={"nombre": "Mía"}).status_code == 403
        assert subir(tc).status_code == 403
        assert tc.delete(f"{API}/documentos/{did}").status_code == 403
        assert tc.get(f"{API}/papelera").status_code == 403
        assert tc.get(f"{API}/documentos/{did}/archivo").status_code == 200


def test_solo_pdf_y_validaciones(personas):
    editora, _, _ = personas
    te = cliente(editora)
    assert subir(te, datos=b"PK\x03\x04 esto es un docx").status_code == 422
    assert te.post(f"{API}/documentos", json={"titulo": "Malo", "nombre_archivo": "a.pdf",
                                              "contenido": "no es base64!"}).status_code == 422
    assert subir(te, titulo="ab").status_code == 422
    assert subir(te, carpeta_id=999999).status_code == 404


def test_carpetas_sin_nombres_repetidos_ni_ciclos_y_solo_vacias_se_eliminan(personas):
    editora, _, _ = personas
    te = cliente(editora)
    a = te.post(f"{API}/carpetas", json={"nombre": "Normas"}).json()["id"]
    assert te.post(f"{API}/carpetas", json={"nombre": " normas "}).status_code == 409
    b = te.post(f"{API}/carpetas", json={"nombre": "Hija", "padre_id": a}).json()["id"]
    assert te.patch(f"{API}/carpetas/{a}", json={"mover": True, "padre_id": b}).status_code == 422
    assert te.patch(f"{API}/carpetas/{b}", json={"nombre": "Circulares"}).status_code == 200
    assert te.delete(f"{API}/carpetas/{a}").status_code == 409          # tiene una subcarpeta
    did = subir(te, carpeta_id=b).json()["id"]
    assert te.delete(f"{API}/carpetas/{b}").status_code == 409          # tiene un documento
    te.delete(f"{API}/documentos/{did}")
    assert te.delete(f"{API}/carpetas/{b}").status_code == 200          # lo de la papelera no cuenta
    assert te.post(f"{API}/papelera/documentos/{did}/restaurar").status_code == 200
    assert any(d["id"] == did for d in te.get(f"{API}/carpetas/0").json()["documentos"])  # vuelve al inicio


def test_buscar_sin_tildes_ni_mayusculas_y_por_carpeta(personas):
    editora, lector, _ = personas
    te, tl = cliente(editora), cliente(lector)
    cid = te.post(f"{API}/carpetas", json={"nombre": "Enfermería"}).json()["id"]
    did = subir(te, titulo="Prevención de caídas en adultos", carpeta_id=cid).json()["id"]
    otro = subir(te, titulo="Lavado de manos").json()["id"]
    r = tl.get(f"{API}/buscar", params={"q": "CAIDAS prevencion"}).json()
    assert did in [d["id"] for d in r["documentos"]] and otro not in [d["id"] for d in r["documentos"]]
    assert next(d for d in r["documentos"] if d["id"] == did)["ruta"] == [{"id": cid, "nombre": "Enfermería"}]
    assert did in [d["id"] for d in tl.get(f"{API}/buscar", params={"q": "enfermeria"}).json()["documentos"]]
    assert otro not in [d["id"] for d in tl.get(f"{API}/buscar", params={"q": "enfermeria"}).json()["documentos"]]
    assert tl.get(f"{API}/buscar", params={"q": "  "}).json()["total"] == 0
    te.delete(f"{API}/documentos/{did}")
    assert did not in [d["id"] for d in tl.get(f"{API}/buscar", params={"q": "caidas"}).json()["documentos"]]  # lo eliminado no aparece


def test_reemplazar_deja_la_version_anterior_en_la_papelera(personas):
    editora, lector, _ = personas
    te = cliente(editora)
    did = subir(te).json()["id"]
    nuevo = PDF + b"% version 2\n"
    assert te.post(f"{API}/documentos/{did}/version",
                   json={"nombre_archivo": "v2.pdf", "contenido": b64(nuevo)}).status_code == 200
    assert cliente(lector).get(f"{API}/documentos/{did}/archivo").content == nuevo
    pap = te.get(f"{API}/papelera").json()
    vieja = next(v for v in pap["versiones"] if v["documento_id"] == did)
    assert vieja["dias"] == 30 and vieja["por"] == "Ema Editora"
    assert te.get(f"{API}/papelera/versiones/{vieja['id']}/archivo").content == PDF
    # restaurar la anterior: vuelve a ser la vigente y la nueva pasa a la papelera
    assert te.post(f"{API}/papelera/versiones/{vieja['id']}/restaurar").status_code == 200
    assert cliente(lector).get(f"{API}/documentos/{did}/archivo").content == PDF
    pap = te.get(f"{API}/papelera").json()
    assert [v["id"] for v in pap["versiones"] if v["documento_id"] == did] != [vieja["id"]]
    otra = next(v for v in pap["versiones"] if v["documento_id"] == did)
    assert te.delete(f"{API}/papelera/versiones/{otra['id']}").status_code == 200
    assert not [v for v in te.get(f"{API}/papelera").json()["versiones"] if v["documento_id"] == did]


def test_eliminar_restaurar_y_borrar_para_siempre(personas):
    editora, lector, _ = personas
    te, tl = cliente(editora), cliente(lector)
    did = subir(te).json()["id"]
    assert te.delete(f"{API}/documentos/{did}").status_code == 200
    assert tl.get(f"{API}/documentos/{did}/archivo").status_code == 404
    assert any(d["id"] == did for d in te.get(f"{API}/papelera").json()["documentos"])
    assert te.get(f"{API}/papelera/documentos/{did}/archivo").content == PDF
    assert te.post(f"{API}/papelera/documentos/{did}/restaurar").status_code == 200
    assert tl.get(f"{API}/documentos/{did}/archivo").status_code == 200
    te.delete(f"{API}/documentos/{did}")
    assert te.delete(f"{API}/papelera/documentos/{did}").status_code == 200
    assert te.post(f"{API}/papelera/documentos/{did}/restaurar").status_code == 404


def test_depurar_vacia_la_papelera_a_los_30_dias(personas):
    editora, _, _ = personas
    te = cliente(editora)
    viejo, reciente = subir(te).json()["id"], subir(te).json()["id"]
    te.delete(f"{API}/documentos/{viejo}")
    te.delete(f"{API}/documentos/{reciente}")
    with plataforma.bd_modulo(CLAVE) as c:
        c.execute("UPDATE documentos SET eliminado_en = now() - interval '31 days' WHERE id=?", (viejo,))
    assert plataforma.REGISTRO[CLAVE].depurar() >= 1
    ids = [d["id"] for d in te.get(f"{API}/papelera").json()["documentos"]]
    assert viejo not in ids and reciente in ids


def test_bitacora_sin_contenido_y_descarga_de_mis_datos(personas):
    editora, _, _ = personas
    te = cliente(editora)
    did = subir(te, titulo="Manual secreto de prueba").json()["id"]
    with bd() as c:
        detalle = c.execute("SELECT detalle FROM auditoria WHERE accion=? ORDER BY id DESC LIMIT 1",
                            (f"{CLAVE}_documento_subido",)).fetchone()["detalle"]
    assert detalle == f"documento #{did}"
    datos = te.get("/api/cuenta/exportar").json()["modulos"][CLAVE]["datos"]
    assert any(d["id"] == did for d in datos["documentos"])
    assert all("contenido" not in v for v in datos["versiones_subidas"])
