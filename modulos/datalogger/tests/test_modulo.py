"""Pruebas propias de Data+: lo que hace y quién puede hacerlo. Correr con `pytest modulos/datalogger`.
Las reglas comunes (sesión, perfiles, ícono, diseño, Ley 21.719) ya las prueba tests/test_reglas_modulos.py."""
from datetime import datetime, timedelta, timezone

import pytest

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
