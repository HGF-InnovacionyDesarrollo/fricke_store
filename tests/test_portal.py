"""Comportamientos del portal en los que se apoyan todos los módulos: ingreso, segundo factor, bitácora."""
import time

import pytest

from conftest import CLAVE, cliente, habilitar_modulo, nuevo_usuario
import mfa
import plataforma
from db import verificar_auditoria


def test_ingreso_con_clave_incorrecta_no_revela_nada(funcionario):
    r = cliente().post("/api/auth/login", json={"rut": funcionario["rut"], "clave": "no es la clave"})
    assert r.status_code == 401 and r.json()["detail"] == "RUT o contraseña incorrectos."


def test_escritura_sin_cabecera_anti_csrf_rechazada(funcionario):
    from fastapi.testclient import TestClient
    import app as portal
    r = TestClient(portal.app).post("/api/auth/login", json={"rut": funcionario["rut"], "clave": CLAVE})
    assert r.status_code == 403


def test_funcionario_no_entra_a_la_administracion(funcionario):
    tc = cliente(funcionario)
    assert tc.get("/api/admin/usuarios").status_code == 403
    assert tc.get("/api/admin/auditoria").status_code == 403


def test_bitacora_integra_y_exportable(admin):
    tc = cliente(admin)
    assert verificar_auditoria()["integra"]
    r = tc.get("/api/admin/auditoria/exportar?desde=2020-01-01")
    assert r.status_code == 200 and r.text.startswith("﻿N°;Fecha")
    assert tc.get("/api/admin/auditoria?desde=2026-13-40").status_code == 400


def test_bitacora_de_modulo_rechaza_rut_y_acciones_no_declaradas():
    clave = next(iter(plataforma.REGISTRO))
    accion = next(iter(plataforma.REGISTRO[clave].manifiesto.acciones))
    with pytest.raises(ValueError):
        plataforma.auditar_modulo(clave, accion, None, "paciente 12.345.678-5")
    with pytest.raises(ValueError):
        plataforma.auditar_modulo(clave, f"{clave}_accion_inventada", None, "x")


def test_modulo_con_datos_de_pacientes_no_se_carga():
    from pathlib import Path
    m = plataforma.Manifiesto(
        clave="ejemplo", nombre="Tablón de avisos", descripcion="x", version="0.1.0", responsable="Unidad", familia=5,
        tratamiento=plataforma.FichaTratamiento(finalidad="Registrar caídas de pacientes", categorias_datos="clínicos",
                                                titulares="pacientes", base_licitud="salud", conservacion="15 años"))
    assert any("pacientes" in e for e in plataforma._validar(m, Path("modulos/ejemplo")))


def test_segundo_factor_exigido_por_un_administrador(admin, funcionario):
    assert cliente(admin).patch(f"/api/admin/usuarios/{funcionario['id']}", json={"mfa_exigido": True}).status_code == 200
    tc = cliente()
    assert tc.post("/api/auth/login", json={"rut": funcionario["rut"], "clave": CLAVE}).json()["mfa"] == 2
    assert tc.get("/api/me").status_code == 401                       # nada sin el segundo factor
    secreto = tc.get("/api/auth/mfa/configurar").json()["secreto"].replace(" ", "")
    paso = int(time.time()) // mfa.PASO
    r = tc.post("/api/auth/mfa/configurar", json={"codigo": mfa._codigo(secreto, paso)})
    respaldo = r.json()["codigos_respaldo"]
    assert len(respaldo) == 8 and tc.get("/api/me").status_code == 200

    otro = cliente()
    assert otro.post("/api/auth/login", json={"rut": funcionario["rut"], "clave": CLAVE}).json()["mfa"] == 1
    assert otro.post("/api/auth/mfa/verificar", json={"codigo": mfa._codigo(secreto, paso)}).status_code == 400  # ya usado
    assert otro.post("/api/auth/mfa/verificar", json={"codigo": respaldo[0]}).json()["respaldo_usado"]


def test_modulos_visibles_solo_para_su_perfil(funcionario):
    clave = next(iter(plataforma.REGISTRO))
    habilitar_modulo(clave, "admin")
    assert all(m["clave"] != clave for m in cliente(funcionario).get("/api/modulos").json())
    habilitar_modulo(clave, "funcionario")
    assert any(m["clave"] == clave for m in cliente(funcionario).get("/api/modulos").json())


def test_panel_activa_modulo_con_guion_bajo_en_la_clave(admin):
    """Las claves de módulo llevan guion bajo (monitoreo_fetal): el panel debe poder activarlos."""
    tc = cliente(admin)
    m = next(x for x in tc.get("/api/admin/modulos").json() if x["clave"] == "monitoreo_fetal")
    r = tc.put(f"/api/admin/modulos/{m['id']}", json={**m, "activo": True})
    assert r.status_code == 200, r.text
    assert next(x for x in tc.get("/api/admin/modulos").json() if x["clave"] == "monitoreo_fetal")["activo"]
    tc.put(f"/api/admin/modulos/{m['id']}", json={**m, "activo": False})
