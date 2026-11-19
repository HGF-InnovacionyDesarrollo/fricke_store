"""Comportamientos del portal en los que se apoyan todos los módulos: ingreso, segundo factor, bitácora."""
import time

import pytest

from conftest import CLAVE, cliente, habilitar_modulo, nuevo_usuario
import mfa
import app as portal
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
        clave="ejemplo", nombre="F+avisos", descripcion="x", version="0.1.0", responsable="Unidad", familia=5,
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


def test_puerta_para_equipos_solo_deja_pasar_envios_de_equipos():
    """Con HTTPS, el puerto HTTP solo acepta POST a /api/m/<clave>/equipo (desde las redes permitidas)."""
    from fastapi.testclient import TestClient
    from puerta_equipos import puerta_equipos
    puerta = TestClient(puerta_equipos(portal.app, 8443, redes=""), follow_redirects=False)
    r = puerta.get("/ingresar")
    assert r.status_code == 301 and r.headers["location"].startswith("https://") and ":8443/ingresar" in r.headers["location"]
    assert puerta.post("/api/auth/login", json={}).status_code == 301
    assert puerta.get("/api/m/datalogger/equipo").status_code == 301
    assert puerta.post("/api/m/datalogger/equipo", json={}).status_code == 401   # llega al portal: falta la credencial
    lejos = TestClient(puerta_equipos(portal.app, 8443, redes="10.99.0.0/16"), follow_redirects=False)
    assert lejos.post("/api/m/datalogger/equipo", json={}).status_code == 403    # el cliente de prueba no está en esa red


def _con_mfa(admin, persona) -> str:
    """Activa el segundo factor de `persona` y devuelve su secreto."""
    cliente(admin).patch(f"/api/admin/usuarios/{persona['id']}", json={"mfa_exigido": True})
    tc = cliente()
    tc.post("/api/auth/login", json={"rut": persona["rut"], "clave": CLAVE})
    secreto = tc.get("/api/auth/mfa/configurar").json()["secreto"].replace(" ", "")
    tc.post("/api/auth/mfa/configurar", json={"codigo": mfa._codigo(secreto, int(time.time()) // mfa.PASO)})
    return secreto


def test_codigos_del_segundo_factor_no_se_prueban_sin_limite(admin, funcionario):
    """Volver a ingresar la contraseña no reinicia el contador: a los 5 códigos malos la cuenta se bloquea."""
    _con_mfa(admin, funcionario)
    for i in range(5):
        tc = cliente()
        assert tc.post("/api/auth/login", json={"rut": funcionario["rut"], "clave": CLAVE}).json()["mfa"] == 1
        r = tc.post("/api/auth/mfa/verificar", json={"codigo": "000000" if i % 2 else "111111"})
        assert r.status_code in (400, 401)
    assert "bloqueada" in r.json()["detail"]
    assert cliente().post("/api/auth/login", json={"rut": funcionario["rut"], "clave": CLAVE}).status_code == 429


def test_pantalla_bloqueada_no_permite_probar_claves_sin_limite(funcionario):
    tc = cliente(funcionario)
    assert tc.post("/api/auth/bloquear").status_code == 200
    for _ in range(4):
        assert tc.post("/api/auth/desbloquear", json={"clave": "otra clave cualquiera"}).json()["detail"] == "Contraseña incorrecta."
    r = tc.post("/api/auth/desbloquear", json={"clave": "otra clave cualquiera"})
    assert r.status_code == 401 and "bloqueada" in r.json()["detail"]
    assert tc.get("/api/me").status_code == 401                         # la sesión se cerró
    assert tc.post("/api/auth/login", json={"rut": funcionario["rut"], "clave": CLAVE}).status_code == 429


def test_demasiados_fallos_desde_un_equipo_frenan_el_ingreso():
    portal._FALLOS_IP.clear()
    try:
        tc = cliente()
        personas = [nuevo_usuario() for _ in range(4)]
        for i in range(portal.cfg.MAX_FALLOS_IP):
            tc.post("/api/auth/login", json={"rut": personas[i % 4]["rut"], "clave": "no es la clave correcta"})
        # Ni con la clave correcta: ese equipo está probando claves contra varias cuentas
        assert tc.post("/api/auth/login", json={"rut": personas[0]["rut"], "clave": CLAVE}).status_code == 429
    finally:
        portal._FALLOS_IP.clear()


def test_solo_el_dpd_aprueba_la_evaluacion_de_impacto(admin):
    dpd = nuevo_usuario("dpd", "Dora Delegada")
    ta, td = cliente(admin), cliente(dpd)
    m = next(x for x in ta.get("/api/admin/modulos").json() if x["clave"] == "monitoreo_fetal")
    assert ta.put(f"/api/admin/modulos/{m['id']}", json={**m, "eipd_aprobada": True}).status_code == 200
    assert not next(x for x in ta.get("/api/admin/modulos").json() if x["id"] == m["id"])["eipd_aprobada"]
    assert td.put(f"/api/admin/modulos/{m['id']}", json={**m, "eipd_aprobada": True}).status_code == 200
    assert next(x for x in ta.get("/api/admin/modulos").json() if x["id"] == m["id"])["eipd_aprobada"]
    # El administrador puede seguir editando lo suyo sin borrar la aprobación del DPD
    assert ta.put(f"/api/admin/modulos/{m['id']}", json={**m, "eipd_aprobada": False, "orden": 211}).status_code == 200
    assert next(x for x in ta.get("/api/admin/modulos").json() if x["id"] == m["id"])["eipd_aprobada"]
    td.put(f"/api/admin/modulos/{m['id']}", json={**m, "eipd_aprobada": False})


def test_depuracion_registrada_y_ancla_externa_de_la_bitacora(admin):
    """depurar deja constancia (el panel avisa si no corre) y el ancla externa detecta una bitácora reescrita."""
    import db
    plataforma.depurar_todos()
    assert db.leer_ajuste("ultima_depuracion")
    assert db.anclar_auditoria()["hash"]
    assert verificar_auditoria()["integra"]
    with db.bd() as c:   # alguien reescribe el último registro anclado y recalcula su hash para que la cadena calce
        f = c.execute("SELECT * FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()
        nuevo = db._hash_fila(f["hash_anterior"], f["ts"], f["usuario_id"], f["accion"], "otro detalle", f["ip"])
        c.execute("UPDATE auditoria SET detalle='otro detalle', hash=? WHERE id=?", (nuevo, f["id"]))
    try:
        r = verificar_auditoria()
        assert not r["integra"] and r["falla_en_id"] == f["id"]
    finally:
        with db.bd() as c:
            c.execute("UPDATE auditoria SET detalle=?, hash=? WHERE id=?", (f["detalle"], f["hash"], f["id"]))
