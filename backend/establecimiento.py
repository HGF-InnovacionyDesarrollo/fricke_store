"""Establecimiento de la red que atiende esta instalación.

La plataforma es una sola (mismo código para toda la red) y cada hospital corre su propia instalación,
con su base de datos, sus usuarios y su marca. Lo propio de cada uno vive en
`establecimientos/<clave>/establecimiento.json` y `establecimientos/<clave>/marca/`.
Se elige con la variable de entorno ECO_ESTABLECIMIENTO (por defecto "fricke").
"""
import json
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "establecimientos"
CLAVE = os.environ.get("ECO_ESTABLECIMIENTO", "fricke").strip().lower()

OBLIGATORIOS = ("clave", "producto", "institucion", "unidad_desarrolladora", "jefe_servicio", "correo_dpd", "mesa_ayuda")
_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
_VARIABLE = re.compile(r"--[a-z][a-z0-9-]{1,30}")


def _cargar(clave: str) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,30}", clave):
        raise SystemExit(f"ECO_ESTABLECIMIENTO no válido: {clave!r}")
    archivo = RAIZ / clave / "establecimiento.json"
    if not archivo.exists():
        disponibles = sorted(p.parent.name for p in RAIZ.glob("*/establecimiento.json"))
        raise SystemExit(f"No existe el establecimiento '{clave}'. Disponibles: {', '.join(disponibles)}")
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    faltan = [k for k in OBLIGATORIOS if not str(datos.get(k, "")).strip()]
    if faltan or datos["clave"] != clave:
        raise SystemExit(f"establecimientos/{clave}/establecimiento.json incompleto: falta {', '.join(faltan) or 'clave igual a la carpeta'}")
    for modo, variables in datos.get("colores", {}).items():
        if modo not in ("claro", "oscuro"):
            raise SystemExit(f"colores.{modo}: usa 'claro' u 'oscuro'.")
        for k, v in variables.items():
            if not _VARIABLE.fullmatch(k) or not _COLOR.fullmatch(v):
                raise SystemExit(f"colores.{modo}: '{k}: {v}' no es una variable CSS con color #RRGGBB.")
    red_archivo = RAIZ / "red.json"
    datos["red"] = json.loads(red_archivo.read_text(encoding="utf-8")) if red_archivo.exists() else {}
    datos["carpeta_marca"] = RAIZ / clave / "marca"
    return datos


EST = _cargar(CLAVE)


def tema_css() -> str:
    """Colores del establecimiento: se cargan después de base.css y reemplazan sus variables."""
    c = EST.get("colores", {})

    def bloque(sel, variables):
        return f"{sel} {{ {' '.join(f'{k}: {v};' for k, v in variables.items())} }}\n" if variables else ""
    css = bloque(":root", c.get("claro", {}))
    if c.get("oscuro"):
        css += "@media (prefers-color-scheme: dark) {\n  " + bloque(':root:not([data-theme="light"])', c["oscuro"]) + "}\n"
        css += bloque(':root[data-theme="dark"]', c["oscuro"])
    return css


def textos() -> dict:
    """Marcadores {{...}} que se reemplazan en las páginas HTML al servirlas."""
    return {
        "producto": EST["producto"],
        "institucion": EST["institucion"],
        "unidad": EST["unidad_desarrolladora"],
        "unidad_detalle": EST.get("unidad_desarrolladora_detalle", ""),
    }
