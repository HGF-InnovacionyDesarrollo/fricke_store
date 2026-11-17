"""Reglas que TODO módulo debe cumplir (docs/MODULOS.md y docs/diseno/). Se aplican solas a cada carpeta de
modulos/: un módulo nuevo queda cubierto sin escribir nada. Si una falla, el mensaje dice qué regla y dónde."""
import json
import re
from pathlib import Path

import pytest

from conftest import RAIZ, cliente, deshabilitar_modulo, habilitar_modulo, nuevo_usuario
import app as portal
import plataforma
from logo_modulo import problemas_nombre, verificar as verificar_logo

CARPETAS = sorted(p for p in (RAIZ / "modulos").iterdir()
                  if p.is_dir() and (p / "__init__.py").exists() and not p.name.startswith("_"))
CLAVES = [p.name for p in CARPETAS]


def rutas_api(clave: str):
    """(método, ruta de ejemplo) de cada endpoint del módulo, con los parámetros reemplazados por 1."""
    for r in portal.app.routes:
        ruta = getattr(r, "path", "")
        if ruta.startswith(f"/api/m/{clave}/"):
            for metodo in sorted(getattr(r, "methods", []) - {"HEAD", "OPTIONS"}):
                yield metodo, re.sub(r"\{[^}]+\}", "1", ruta)


def pedir(tc, metodo, ruta):
    return tc.request(metodo, ruta, json={} if metodo in ("POST", "PUT", "PATCH") else None)


@pytest.fixture(params=CLAVES)
def modulo(request):
    clave = request.param
    assert clave in plataforma.REGISTRO, (
        f"El módulo '{clave}' no se cargó. Ejecuta `python backend/gestionar.py modulos` para ver el motivo.")
    return plataforma.REGISTRO[clave]


# ------------------------------------------------------------------ identidad y diseño
def test_nombre_cumple_directrices(modulo):
    assert problemas_nombre(modulo.manifiesto.nombre) == []


def test_icono_y_archivos_de_entrega(modulo):
    m = modulo.manifiesto
    assert verificar_logo(m.archivo_logo, m.familia) == [], "Genera el ícono con backend/logo_modulo.py (docs/diseno/)."


def test_pagina_usa_el_esqueleto_comun(modulo):
    html = (modulo.carpeta / "frontend" / "index.html").read_text(encoding="utf-8")
    for requerido in ("/static/css/base.css", "/marca/tema.css", "/static/css/cabecera.css", "/static/css/modulo.css",
                      "/static/js/comun.js", "/static/js/cabecera.js", "/static/js/modulo.js", 'lang="es-CL"'):
        assert requerido in html, f"index.html debe incluir {requerido}"
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html), "Sin scripts en línea: la CSP los bloquea."
    js = "".join(p.read_text(encoding="utf-8") for p in (modulo.carpeta / "frontend").glob("*.js"))
    assert "iniciarModulo(" in js, "La página debe arrancar con iniciarModulo(...)."


def test_sin_colores_fijos_ni_recursos_externos(modulo):
    for archivo in (modulo.carpeta / "frontend").rglob("*"):
        if archivo.suffix not in (".css", ".js", ".html"):
            continue
        texto = re.sub(r"/\*.*?\*/|<!--.*?-->", "", archivo.read_text(encoding="utf-8"), flags=re.S)
        if archivo.suffix == ".css":
            colores = re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(", texto)
            assert not colores, f"{archivo.name}: colores fijos {colores[:3]}; usa las variables de base.css."
        externos = re.findall(r"""(?:src|href|url\()\s*=?\s*["']?(https?://[^"')\s]+)""", texto)
        assert not externos, f"{archivo.name}: recursos de Internet {externos[:2]}; todo se sirve desde el portal."


# ------------------------------------------------------------------ acceso y permisos
def test_todo_endpoint_exige_sesion(modulo):
    anonimo = cliente()
    rutas = list(rutas_api(modulo.manifiesto.clave))
    for metodo, ruta in rutas:
        r = pedir(anonimo, metodo, ruta)
        assert r.status_code == 401, f"{metodo} {ruta} respondió {r.status_code} sin sesión; debe usar acceso(...)."


def test_modulo_inactivo_o_sin_perfil_niega_acceso(modulo):
    clave = modulo.manifiesto.clave
    persona = nuevo_usuario("funcionario")
    tc = cliente(persona)
    habilitar_modulo(clave, "admin")            # activo, pero no para este perfil
    for metodo, ruta in rutas_api(clave):
        assert pedir(tc, metodo, ruta).status_code == 403, f"{metodo} {ruta} no respetó los perfiles habilitados."
    deshabilitar_modulo(clave)                  # suspendido
    for metodo, ruta in rutas_api(clave):
        assert pedir(tc, metodo, ruta).status_code == 403, f"{metodo} {ruta} respondió estando suspendido."


def test_pagina_y_contexto_con_acceso(modulo):
    clave = modulo.manifiesto.clave
    persona = nuevo_usuario("funcionario")
    habilitar_modulo(clave, "funcionario")
    tc = cliente(persona)
    assert tc.get(f"/m/{clave}/").status_code == 200
    ctx = tc.get(f"/api/modulos/{clave}/contexto").json()
    assert ctx["clave"] == clave and ctx["icono"].endswith(".svg")
    deshabilitar_modulo(clave)


# ------------------------------------------------------------------ Ley 21.719
def test_exportar_y_depurar(modulo):
    persona = nuevo_usuario("funcionario")
    if modulo.exportar_titular:
        datos = modulo.exportar_titular(persona["id"])
        assert isinstance(datos, dict)
        json.dumps(datos, default=str)          # debe poder ir en "Descargar mis datos"
    if modulo.depurar:
        assert isinstance(modulo.depurar(), int)


def test_guarda_datos_de_personas_implica_exportar_y_depurar(modulo):
    sql = "".join(p.read_text(encoding="utf-8") for p in (modulo.carpeta / "migraciones").glob("*.sql")).lower()
    if re.search(r"\b(usuario_id|autor_id|funcionario_id)\b", sql):
        assert modulo.exportar_titular, "Guarda datos de personas: falta exportar_titular()."
        assert modulo.depurar, "Guarda datos de personas: falta depurar() según el plazo de conservación."


def test_migraciones_sin_transacciones_propias(modulo):
    for p in (modulo.carpeta / "migraciones").glob("*.sql"):
        texto = re.sub(r"--.*", "", p.read_text(encoding="utf-8")).upper()
        assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", texto), f"{p.name}: el portal ya usa una transacción."
        assert "PORTAL." not in texto, f"{p.name}: un módulo no toca el esquema del portal."
