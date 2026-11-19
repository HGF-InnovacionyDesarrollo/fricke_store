"""Pruebas propias de F+data: lo que hace y quién puede hacerlo. Correr con `pytest modulos/datalogger`.
Las reglas comunes (sesión, perfiles, ícono, diseño, Ley 21.719) ya las prueba tests/test_reglas_modulos.py."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import app as portal
from conftest import cliente, habilitar_modulo, nuevo_usuario
from modulos.datalogger.lectura_csv import firma, hora_chile_a_utc, leer_archivo, utc_a_hora_chile

CLAVE = "datalogger"
API = f"/api/m/{CLAVE}"
LLAVE = bytes(range(32))
ENC_DATOS = ("Fecha y hora;Monitor;Sensor;Nombre;Almacenamiento;IEEE;Temperatura (°C);Humedad (%);"
             "Corrección T (°C);Corrección HR (%);Batería (%);Hora de la lectura;Firma")
ENC_EVENTOS = "Fecha y hora;Monitor;Tipo;Detalle;Firma"


def firmado(encabezado: str, filas: list[str], llave: bytes = LLAVE) -> str:
    """Un CSV como lo graba el equipo: BOM, encabezado y cada fila con su firma encadenada."""
    previa, lineas = "0" * 16, []
    for cuerpo in filas:
        previa = firma(llave, previa, cuerpo)
        lineas.append(f"{cuerpo};{previa}")
    return "﻿" + "\n".join([encabezado, *lineas]) + "\n"


def datos_dia(dia: str, temperaturas: list[float], equipo: str = "MTH-91", ieee: str = "A4:C1:38:80:C7:47:91:01",
              almacenamiento: str = "Medicamentos") -> str:
    inicio = datetime.fromisoformat(f"{dia} 08:00:00")
    filas = []
    for i, t in enumerate(temperaturas):
        h = (inicio + timedelta(minutes=5 * i)).strftime("%Y-%m-%d %H:%M:%S")
        filas.append(f"{h};{equipo};1;Bodega 1;{almacenamiento};{ieee};{str(t).replace('.', ',')};45;0,2;0;80;{h}")
    return firmado(ENC_DATOS, filas)


@pytest.fixture
def personas():
    habilitar_modulo(CLAVE, "admin", "funcionario")
    return nuevo_usuario("admin", "Ana Encargada"), nuevo_usuario("funcionario", "Beto Lector")


def importar(tc, archivos, **extra):
    return tc.post(f"{API}/importaciones", json={"archivos": [{"nombre": n, "contenido": c} for n, c in archivos], **extra})


# ------------------------------------------------------------------ lectura de archivos y hora de Chile
def test_hora_de_chile_con_horario_de_verano():
    assert hora_chile_a_utc("2026-09-30 00:00:00") == datetime(2026, 9, 30, 3, tzinfo=timezone.utc)   # verano UTC-3
    assert hora_chile_a_utc("2026-07-01 12:00:00") == datetime(2026, 7, 1, 16, tzinfo=timezone.utc)   # invierno UTC-4
    assert utc_a_hora_chile(datetime(2026, 7, 1, 16, tzinfo=timezone.utc)) == datetime(2026, 7, 1, 12)


def test_lee_formato_antiguo_con_coma():
    a = leer_archivo("datos-2026-09-24.csv", "Fecha y hora,Sensor,Nombre,Almacenamiento,IEEE,Temperatura (°C),"
                     "Humedad (%),Batería (%),Hora de la lectura,Firma\n2026-09-24 10:00:00,1,S1,Medicamentos,"
                     "A4:C1:38:80:C7:47:FF:FF,21.5,40,90,2026-09-24 09:58:00,0123456789abcdef\n")
    assert a.tipo == "datos" and not a.con_monitor and a.filas[0]["t"] == 21.5


def test_rechaza_archivo_que_no_es_de_un_equipo(personas):
    admin, _ = personas
    r = importar(cliente(admin), [("planilla.csv", "Nombre;Edad\nx;1\n")])
    assert r.status_code == 422


# ------------------------------------------------------------------ importación, resumen y alarmas
def test_importa_muestra_y_detecta_alarma(personas):
    admin, func = personas
    tc = cliente(admin)
    temps = [21.0, 21.5, 31.2, 32.0, 25.0, 22.0]          # dos lecturas sobre 30 °C (Medicamentos)
    eventos = firmado(ENC_EVENTOS, ["2026-10-10 07:59:00;MTH-91;ARRANQUE;MTH-91 serie 98A316FFFE9BB2EC firmware 2.0, motivo: encendido"])
    r = importar(tc, [("2026-10-10.csv", datos_dia("2026-10-10", temps)), ("eventos.csv", eventos)], clave=LLAVE.hex())
    assert r.status_code == 200, r.text
    assert r.json()["lecturas_nuevas"] == 6 and r.json()["eventos_nuevos"] == 1
    assert r.json()["firmas"]["problemas"] == 0

    # Importar lo mismo otra vez no duplica
    r2 = importar(tc, [("2026-10-10.csv", datos_dia("2026-10-10", temps))])
    assert r2.json()["lecturas_nuevas"] == 0 and r2.json()["lecturas_repetidas"] == 6

    resumen = cliente(func).get(f"{API}/resumen").json()
    equipo = next(e for e in resumen["equipos"] if e["codigo"] == "MTH-91")
    assert equipo["sensores"][0]["temperatura"] == 22.0 and equipo["sensores"][0]["estado"] == "normal"

    alarmas = cliente(func).get(f"{API}/alarmas").json()
    x = next(a for a in alarmas if a["equipo"] == "MTH-91")
    assert x["variable"] == "temperatura" and x["sentido"] == "alta" and x["extremo"] == 32.0 and x["fin"]

    sid = equipo["sensores"][0]["id"]
    serie = cliente(func).get(f"{API}/sensores/{sid}/serie?desde=2026-10-10&hasta=2026-10-10").json()
    assert serie["temperatura"]["max"] == 32.0 and serie["temperatura"]["n"] == 6
    assert serie["temperatura"]["mkt"] > serie["temperatura"]["promedio"]
    assert serie["cobertura"] == 100.0

    sensores = cliente(func).get(f"{API}/sensores").json()
    assert next(e for e in sensores["equipos"] if e["codigo"] == "MTH-91")["serie"] == "98A316FFFE9BB2EC"


def test_firma_alterada_se_informa(personas):
    admin, _ = personas
    csv = datos_dia("2026-10-11", [20.0, 20.5, 21.0], ieee="A4:C1:38:80:C7:47:91:02")
    alterado = csv.replace(";20,5;", ";19,5;")              # alguien editó una fila
    r = importar(cliente(admin), [("2026-10-11.csv", alterado)], clave=LLAVE.hex())
    assert r.status_code == 200 and r.json()["firmas"]["problemas"] == 1


def test_formato_sin_monitor_pide_equipo(personas):
    admin, _ = personas
    csv = datos_dia("2026-10-12", [20.0], ieee="A4:C1:38:80:C7:47:91:03").replace(";MTH-91;", ";")
    csv = csv.replace("Fecha y hora;Monitor;", "Fecha y hora;")
    tc = cliente(admin)
    assert importar(tc, [("2026-10-12.csv", csv)]).status_code == 422
    assert importar(tc, [("2026-10-12.csv", csv)], equipo="MTH-92").status_code == 200


def test_revision_de_alarma_y_permisos(personas):
    admin, func = personas
    tc = cliente(admin)
    importar(tc, [("d.csv", datos_dia("2026-10-13", [21.0, 14.0, 21.0], ieee="A4:C1:38:80:C7:47:91:04"))])
    x = next(a for a in tc.get(f"{API}/alarmas").json() if a["sentido"] == "baja" and a["extremo"] == 14.0)
    # El funcionario ve, pero no revisa, no importa ni configura
    tf = cliente(func)
    assert tf.post(f"{API}/alarmas/{x['id']}/revision", json={"accion": "Revisé"}).status_code == 403
    assert importar(tf, [("d.csv", "x")]).status_code == 403
    assert tf.put(f"{API}/sensores/{x['sensor_id']}", json={"ubicacion": "Bodega"}).status_code == 403
    # La encargada revisa una vez
    r = tc.post(f"{API}/alarmas/{x['id']}/revision", json={"accion": "Se trasladó el stock a la bodega 2."})
    assert r.status_code == 200
    assert tc.post(f"{API}/alarmas/{x['id']}/revision", json={"accion": "Otra vez"}).status_code == 409
    revisada = next(a for a in tc.get(f"{API}/alarmas?pendientes=0").json() if a["id"] == x["id"])
    assert revisada["revisor"] == "Ana Encargada"
    # Va en "Descargar mis datos"
    datos = tc.get("/api/cuenta/exportar").json()["modulos"][CLAVE]["datos"]
    assert any(rv["id"] == x["id"] for rv in datos["revisiones_de_alarmas"])


def test_sensor_fuera_de_servicio_no_aparece_en_resumen(personas):
    admin, _ = personas
    tc = cliente(admin)
    importar(tc, [("d.csv", datos_dia("2026-10-14", [21.0], equipo="MTH-93", ieee="A4:C1:38:80:C7:47:91:05"))])
    sid = next(e for e in tc.get(f"{API}/resumen").json()["equipos"] if e["codigo"] == "MTH-93")["sensores"][0]["id"]
    assert tc.put(f"{API}/sensores/{sid}", json={"ubicacion": "Farmacia central", "activo": False}).status_code == 200
    assert not any(e["codigo"] == "MTH-93" for e in tc.get(f"{API}/resumen").json()["equipos"])


def test_descarga_csv(personas):
    admin, func = personas
    importar(cliente(admin), [("d.csv", datos_dia("2026-10-15", [21.3, 21.4], ieee="A4:C1:38:80:C7:47:91:06"))])
    sid = next(s["id"] for e in cliente(func).get(f"{API}/sensores").json()["equipos"] for s in e["sensores"]
               if s["ieee"].endswith("9106"))
    r = cliente(func).get(f"{API}/sensores/{sid}/csv?desde=2026-10-15&hasta=2026-10-15")
    assert r.status_code == 200 and "21,3" in r.text and "2026-10-15 08:00" in r.text


# ------------------------------------------------------------------ configurador por USB (solo bitácora)
def test_configurador_registra_en_bitacora(personas):
    admin, func = personas
    tc = cliente(admin)
    importar(tc, [("d.csv", datos_dia("2026-10-16", [21.0], equipo="MTH-94", ieee="A4:C1:38:80:C7:47:91:07"))])
    accion = {"equipo": "MTH-94", "serie": "98A316FFFE9BB2EC", "firmware": "2.1", "accion": "sensor"}
    # El funcionario no configura equipos
    assert cliente(func).post(f"{API}/configurador/registro", json=accion).status_code == 403
    assert tc.post(f"{API}/configurador/registro", json=accion).status_code == 200
    assert tc.post(f"{API}/configurador/registro", json={**accion, "accion": "borrar_todo"}).status_code == 422
    assert tc.post(f"{API}/configurador/registro", json={**accion, "equipo": "MTH|94"}).status_code == 422
    equipo = next(e for e in tc.get(f"{API}/sensores").json()["equipos"] if e["codigo"] == "MTH-94")
    assert equipo["serie"] == "98A316FFFE9BB2EC" and equipo["firmware"] == "2.1"
    # Un equipo que el portal aún no conoce no se crea: solo queda en la bitácora
    assert tc.post(f"{API}/configurador/registro", json={**accion, "equipo": "MTH-99"}).status_code == 200
    assert not any(e["codigo"] == "MTH-99" for e in tc.get(f"{API}/sensores").json()["equipos"])


# ------------------------------------------------------------------ envío por WiFi (firmware 2.1)
def envio(codigo="MTH-95", unix=None, edad=30, temp=21.4, hum=48, ieee="A4C13880C7479501"):
    return {"monitor": codigo, "serie": "E8F60AFFFEF7EE48", "firmware": "2.1", "seq": 3,
            "unix": int(unix if unix is not None else datetime.now(timezone.utc).timestamp()),
            "uptime_s": 200, "rssi": -48, "heap": 85000, "zb_reportes": 4, "envios_ok": 2, "envios_falla": 0,
            "sensores": [{"n": 1, "ieee": ieee, "nombre": "Sensor 1", "temp": temp, "hum": hum, "edad_s": edad,
                          "bat": 90, "alarma_t": 0, "alarma_h": 0},
                         {"n": 2, "ieee": "A4C13880C7479502", "nombre": "Sensor 2", "temp": None, "hum": None,
                          "edad_s": 0, "bat": -1, "alarma_t": 0, "alarma_h": 0}]}


def test_envio_wifi_con_credencial_de_equipo(personas):
    admin, func = personas
    tc = cliente(admin)
    # Solo quien configura equipos habilita el envío
    assert cliente(func).post(f"{API}/envio-wifi", json={"equipo": "MTH-95"}).status_code == 403
    r = tc.post(f"{API}/envio-wifi", json={"equipo": "MTH-95"})
    assert r.status_code == 200 and len(r.json()["secreto"]) == 24
    secreto = r.json()["secreto"]

    equipo = TestClient(portal.app)  # un aparato: sin cookie ni cabecera anti-CSRF
    assert equipo.post(f"{API}/equipo", json=envio()).status_code == 401
    assert equipo.post(f"{API}/equipo", json=envio(), auth=("equipo", "otra-clave")).status_code == 401
    r = equipo.post(f"{API}/equipo", json=envio(), auth=("equipo", secreto))  # Basic, como lo arma el ESP32
    assert r.status_code == 200 and r.json()["lecturas_nuevas"] == 1
    # El envío siguiente (un minuto después, mismo reporte del sensor) no repite la lectura
    otro = envio(unix=datetime.now(timezone.utc).timestamp() + 60, edad=91)
    assert equipo.post(f"{API}/equipo", json=otro, headers={"Authorization": f"Bearer {secreto}"}).json()["lecturas_nuevas"] == 0
    # La credencial es de un equipo: no sirve para mandar datos a nombre de otro
    assert equipo.post(f"{API}/equipo", json=envio("MTH-96"), auth=("equipo", secreto)).status_code == 403

    resumen = tc.get(f"{API}/resumen").json()
    eq = next(e for e in resumen["equipos"] if e["codigo"] == "MTH-95")
    s1 = next(s for s in eq["sensores"] if s["nombre"] == "Sensor 1")
    assert s1["origen"] == "wifi" and s1["temperatura"] == 21.4 and eq["wifi"]["conectado"]
    # El detalle muestra lo recibido como "en vivo", fuera de las estadísticas oficiales (SD)
    serie = tc.get(f"{API}/sensores/{s1['id']}/serie").json()
    assert len(serie["en_vivo"]) == 1 and serie["temperatura"]["n"] == 0

    lista = tc.get(f"{API}/envio-wifi").json()
    cred = next(e for e in lista["equipos"] if e["equipo"] == "MTH-95")
    assert cred["ultimo_uso"] and cred["wifi_rssi"] == -48 and lista["ruta"] == f"{API}/equipo"
    # Un sensor que solo llega por WiFi no trae tipo de almacenamiento: se fija en Sensores y entonces tiene estado
    med = next(p for p in tc.get(f"{API}/sensores").json()["perfiles"] if p["clave"] == "MED")
    assert tc.put(f"{API}/sensores/{s1['id']}", json={"ubicacion": "Farmacia", "activo": True, "perfil_id": 9999}).status_code == 422
    assert tc.put(f"{API}/sensores/{s1['id']}", json={"ubicacion": "Farmacia", "activo": True, "perfil_id": med["id"]}).status_code == 200
    assert tc.put(f"{API}/sensores/{s1['id']}", json={"ubicacion": "Farmacia", "activo": True}).status_code == 200  # sin perfil_id: no cambia
    eq = next(e for e in tc.get(f"{API}/resumen").json()["equipos"] if e["codigo"] == "MTH-95")
    assert next(s for s in eq["sensores"] if s["id"] == s1["id"])["perfil"] == "Medicamentos"
    # Anulada, deja de servir
    assert tc.delete(f"{API}/envio-wifi/{cred['id']}").status_code == 200
    assert equipo.post(f"{API}/equipo", json=envio(), auth=("equipo", secreto)).status_code == 401


def test_envio_wifi_tolera_valores_raros_de_un_sensor(personas):
    """Un valor fuera de rango (por ejemplo batería en escala 0-200) no debe hacer rechazar todo el envío."""
    admin, _ = personas
    secreto = cliente(admin).post(f"{API}/envio-wifi", json={"equipo": "MTH-98"}).json()["secreto"]
    d = envio("MTH-98", ieee="A4C13880C7479598")
    d["sensores"][0]["bat"] = 200
    d["sensores"][0]["edad_s"] = 12.0
    d["rssi"] = 5
    d["sensores"][0]["ieee"] = "A4:C1:38:80:C7:47:95:98"  # así la manda el firmware (con ':')
    d["sensores"][1]["ieee"] = "A4:C1:38:80:C7:47:95:99"
    r = TestClient(portal.app).post(f"{API}/equipo", json=d, auth=("equipo", secreto))
    assert r.status_code == 200 and r.json()["lecturas_nuevas"] == 1
    # Un formato realmente inválido sí se rechaza
    d["monitor"] = "mal nombre!"
    assert TestClient(portal.app).post(f"{API}/equipo", json=d, auth=("equipo", secreto)).status_code == 422


def test_envio_wifi_con_sesion_sigue_exigiendo_cabecera_anti_csrf(personas):
    admin, _ = personas
    secreto = cliente(admin).post(f"{API}/envio-wifi", json={"equipo": "MTH-97"}).json()["secreto"]
    navegador = TestClient(portal.app)
    navegador.post("/api/auth/login", json={"rut": admin["rut"], "clave": "frase de prueba muy larga y segura"},
                   headers={"X-Ecosistema": "1"})
    r = navegador.post(f"{API}/equipo", json=envio("MTH-97"), auth=("equipo", secreto))
    assert r.status_code == 403


def test_envio_wifi_genera_alarma_sin_esperar_la_sd(personas):
    admin, _ = personas
    tc = cliente(admin)
    secreto = tc.post(f"{API}/envio-wifi", json={"equipo": "MTH-90"}).json()["secreto"]
    equipo = TestClient(portal.app)
    ieee = "A4C13880C7479090"
    assert equipo.post(f"{API}/equipo", json=envio("MTH-90", ieee=ieee), auth=("equipo", secreto)).status_code == 200
    sid = next(s["id"] for e in tc.get(f"{API}/sensores").json()["equipos"] for s in e["sensores"] if s["ieee"] == ieee)
    med = next(p for p in tc.get(f"{API}/sensores").json()["perfiles"] if p["clave"] == "MED")
    tc.put(f"{API}/sensores/{sid}", json={"ubicacion": "Farmacia", "activo": True, "perfil_id": med["id"]})
    antes = len(tc.get(f"{API}/alarmas").json())
    # 35 °C en Medicamentos (alarma sobre 30 °C): la alarma aparece con el envío, sin importar la SD
    caliente = envio("MTH-90", unix=datetime.now(timezone.utc).timestamp() + 120, edad=5, temp=35, ieee=ieee)
    assert equipo.post(f"{API}/equipo", json=caliente, auth=("equipo", secreto)).json()["lecturas_nuevas"] == 1
    alarmas = tc.get(f"{API}/alarmas").json()
    assert len(alarmas) == antes + 1
    assert any(float(a["extremo"]) == 35 for a in alarmas)


def test_envio_wifi_no_se_adueña_de_sensores_de_otro_equipo_activo(personas):
    admin, _ = personas
    tc = cliente(admin)
    s_a = tc.post(f"{API}/envio-wifi", json={"equipo": "MTH-88"}).json()["secreto"]
    s_b = tc.post(f"{API}/envio-wifi", json={"equipo": "MTH-89"}).json()["secreto"]
    equipo = TestClient(portal.app)
    ieee = "A4C13880C7478888"
    assert equipo.post(f"{API}/equipo", json=envio("MTH-88", ieee=ieee), auth=("equipo", s_a)).status_code == 200
    r = equipo.post(f"{API}/equipo", json=envio("MTH-89", ieee=ieee, edad=1), auth=("equipo", s_b))
    assert r.status_code == 200 and r.json()["lecturas_nuevas"] == 0
    dueño = next(e["codigo"] for e in tc.get(f"{API}/sensores").json()["equipos"] for s in e["sensores"] if s["ieee"] == ieee)
    assert dueño == "MTH-88"


def test_envio_wifi_informa_que_la_sd_no_graba(personas):
    """Firmware 2.2: el equipo cuenta en cada envío si su SD graba; F+data lo muestra sin esperar la importación."""
    admin, _ = personas
    tc = cliente(admin)
    secreto = tc.post(f"{API}/envio-wifi", json={"equipo": "MTH-87"}).json()["secreto"]
    equipo = TestClient(portal.app)
    ieee = "A4C13880C7478787"
    sin_sd = {**envio("MTH-87", ieee=ieee), "sd": 0, "sd_fuera_s": 900, "pendientes": 12}
    assert equipo.post(f"{API}/equipo", json=sin_sd, auth=("equipo", secreto)).status_code == 200
    eq = next(e for e in tc.get(f"{API}/resumen").json()["equipos"] if e["codigo"] == "MTH-87")
    assert eq["wifi"]["sd"]["ok"] is False and eq["wifi"]["sd"]["pendientes"] == 12 and eq["wifi"]["sd"]["fuera_desde"]
    # Vuelve a grabar
    con_sd = {**envio("MTH-87", ieee=ieee, edad=1), "sd": 1, "sd_fuera_s": 0, "pendientes": 0}
    equipo.post(f"{API}/equipo", json=con_sd, auth=("equipo", secreto))
    eq = next(e for e in tc.get(f"{API}/resumen").json()["equipos"] if e["codigo"] == "MTH-87")
    assert eq["wifi"]["sd"]["ok"] is True and eq["wifi"]["sd"]["fuera_desde"] is None
    # Un equipo con firmware anterior (sin el campo) no muestra aviso
    secreto2 = tc.post(f"{API}/envio-wifi", json={"equipo": "MTH-86"}).json()["secreto"]
    equipo.post(f"{API}/equipo", json=envio("MTH-86", ieee="A4C13880C7478686"), auth=("equipo", secreto2))
    eq = next(e for e in tc.get(f"{API}/resumen").json()["equipos"] if e["codigo"] == "MTH-86")
    assert eq["wifi"]["sd"] is None
