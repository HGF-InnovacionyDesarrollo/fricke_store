"""Pruebas propias del módulo F+fetal: lo que hace y quién puede hacerlo.
Correr con `pytest modulos/monitoreo_fetal`.
Las reglas comunes (sesión, perfiles, ícono, diseño, Ley 21.719) ya las prueba tests/test_reglas_modulos.py.
"""
import pytest

from conftest import cliente, habilitar_modulo, nuevo_usuario

CLAVE = "monitoreo_fetal"
API = f"/api/m/{CLAVE}"


@pytest.fixture
def personas():
    habilitar_modulo(CLAVE, "admin", "funcionario")
    return (
        nuevo_usuario("admin", "Dra. Ana Jefa"),
        nuevo_usuario("funcionario", "Mat. Beto Clínico"),
        nuevo_usuario("dpd", "Carla Delegada"),
    )


def test_casos_docentes_y_clasificacion_normativa(personas):
    _, func, _ = personas
    tc = cliente(func)
    r = tc.get(f"{API}/casos-docentes")
    assert r.status_code == 200
    casos = r.json()
    assert len(casos) == 4
    por_escenario = {c["escenario"]: c for c in casos}
    assert por_escenario["normal_reactivo"]["categoria_figo"] == "I"
    assert por_escenario["taquisistolia_cat2"]["categoria_figo"] == "II"
    assert por_escenario["taquisistolia_cat2"]["riesgo_cat_ii"] == "con_rasgos_protectores"
    assert por_escenario["variables_recurrentes_cat2"]["categoria_figo"] == "II"
    assert por_escenario["variables_recurrentes_cat2"]["riesgo_cat_ii"] == "alto"
    assert por_escenario["patologico_cat3"]["categoria_figo"] == "III"
    assert por_escenario["patologico_cat3"]["hipoxia_tipificada"] == "aguda"


def test_funcionario_registra_simulacion_y_admin_modera(personas):
    admin, func, _ = personas
    tc_func = cliente(func)
    r = tc_func.post(
        f"{API}/simulaciones",
        json={
            "titulo": "Práctica trazado sospechoso con taquicardia",
            "escenario": "personalizado",
            "edad_gestacional_sem": 39,
            "linea_base_lpm": 170,
            "variabilidad_lpm": 10.0,
            "num_aceleraciones": 1,
            "num_desaceleraciones": 2,
            "tipo_desaceleracion": "variable",
            "duracion_max_decel_s": 45,
            "contracciones_10min": 4.0,
            "patron_sinusoidal": False,
            "nota_docente": "Evaluar hidratación y temperatura materna según Protocolo V2.",
        },
    )
    assert r.status_code == 200
    creada = r.json()
    assert creada["categoria_figo"] == "II"
    assert creada["riesgo_cat_ii"] == "alto"

    lista = tc_func.get(f"{API}/simulaciones").json()
    item = next(s for s in lista if s["id"] == creada["id"])
    assert item["autor"] == "Mat. Beto Clínico"
    assert item["puede_borrar"] is True

    # El administrador puede moderar/borrar simulaciones de otros funcionarios
    assert cliente(admin).delete(f"{API}/simulaciones/{creada['id']}").status_code == 200


def test_funcionario_no_borra_simulacion_ajena(personas):
    admin, func, _ = personas
    sid = cliente(admin).post(
        f"{API}/simulaciones",
        json={
            "titulo": "Simulación docente de jefatura",
            "edad_gestacional_sem": 38,
            "linea_base_lpm": 140,
            "variabilidad_lpm": 12.0,
        },
    ).json()["id"]
    assert cliente(func).delete(f"{API}/simulaciones/{sid}").status_code == 403


def test_validacion_de_campos_fuera_de_rango(personas):
    _, func, _ = personas
    assert cliente(func).post(f"{API}/simulaciones", json={"titulo": "x", "linea_base_lpm": 300}).status_code == 422


def test_mis_simulaciones_y_descarga_de_mis_datos_ley_21719(personas):
    _, func, _ = personas
    tc = cliente(func)
    tc.post(
        f"{API}/simulaciones",
        json={
            "titulo": "Ejercicio propio para portabilidad",
            "edad_gestacional_sem": 40,
            "linea_base_lpm": 135,
            "variabilidad_lpm": 15.0,
        },
    )
    mias = tc.get(f"{API}/simulaciones?mias=1").json()
    assert len(mias) >= 1 and all(s["autor_id"] == func["id"] for s in mias)
    exportado = tc.get("/api/cuenta/exportar").json()
    registros = exportado["modulos"][CLAVE]["datos"]["simulaciones_registradas"]
    assert any(r["titulo"] == "Ejercicio propio para portabilidad" for r in registros)
