"""Íconos de módulo según docs/diseno/ (Parte 2: baldosa de la grilla de Fricke Store, 5 familias).

  python backend/logo_modulo.py --nombre "Prevención de caídas" --familia 3 --pictograma footprints.svg
  python backend/logo_modulo.py --verificar prevencion-de-caidas --familia 3

El pictograma es un SVG de retícula 24 × 24 con trazo (por ejemplo, un ícono de Lucide, licencia ISC).
Genera en docs/logo/modulos/<nombre>/ todos los archivos de la entrega y copia el SVG a
frontend/img/modulos/<nombre>.svg, que es el que usa la app. No toca el logo de Fricke Store.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

RAIZ = Path(__file__).resolve().parent.parent
DIR_ENTREGA = RAIZ / "docs" / "logo" / "modulos"
DIR_APP = RAIZ / "frontend" / "img" / "modulos"
FUENTE = RAIZ / "frontend" / "fonts" / "outfit-500.woff2"

TINTA, BLANCO = "#2B3440", "#FFFFFF"
# Familia: (nombre, inicio del degradado, fin del degradado, color del pictograma)
FAMILIAS = {
    1: ("Atención y acceso", "#1565C0", "#1774B4", BLANCO),
    2: ("Clínica", "#1876B3", "#1C949C", BLANCO),
    3: ("Calidad y seguridad", "#1D969B", "#54A87C", TINTA),
    4: ("Operaciones y equipos", "#58A87A", "#C3AD55", TINTA),
    5: ("Personas y gestión", "#C7AD53", "#FCB040", TINTA),
}
TAMANOS_PNG = (48, 96, 192, 512)
ARCHIVOS = ("{n}.svg", "{n}-48.png", "{n}-96.png", "{n}-192.png", "{n}-512.png", "{n}-app-180.png", "{n}-horizontal.svg")
PALABRAS_PROHIBIDAS = ("fricke", "app", "sistema")
CONECTORES = {"de", "del", "la", "las", "el", "los", "y", "e", "a", "en", "con", "para"}
SVG_NS = "http://www.w3.org/2000/svg"


def slug(nombre: str) -> str:
    """Nombre de archivo: minúsculas, sin tildes, con guiones (prevencion-de-caidas)."""
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


NOMBRE_VALIDO = re.compile(r"F\+[a-zñáéíóúü]{2,12}")


def problemas_nombre(nombre: str) -> list[str]:
    """Regla de nombres (decisión del 18 nov 2026): «F+» y una palabra corta en minúsculas, sin espacios ni tildes de
    más: F+data, F+mefi, F+docs. La palabra dice qué hace el módulo; no lleva «fricke», «app» ni «sistema»."""
    nombre = (nombre or "").strip()
    if not nombre:
        return ["El nombre está vacío."]
    p = []
    if not NOMBRE_VALIDO.fullmatch(nombre):
        p.append("El nombre es «F+» y una palabra corta en minúsculas, sin espacios (ej.: «F+data», «F+docs»).")
    if any(x in nombre.lower() for x in PALABRAS_PROHIBIDAS):
        p.append("El nombre no lleva «Fricke», «App» ni «Sistema».")
    return p


# ------------------------------------------------------------------ construcción
def _pictograma(ruta: Path) -> str:
    """Toma los elementos de un SVG de 24 × 24 y les quita colores y grosores propios (los fija la baldosa)."""
    ET.register_namespace("", SVG_NS)
    raiz = ET.parse(ruta).getroot()
    vb = (raiz.get("viewBox") or "0 0 24 24").split()
    if [float(x) for x in vb] != [0, 0, 24, 24]:
        raise SystemExit("El pictograma debe usar viewBox 0 0 24 24 (retícula de 24, como Lucide).")
    partes = []
    for el in list(raiz):
        tag = el.tag.split("}")[-1]
        if tag in ("title", "desc", "metadata", "defs"):
            continue
        if tag == "text":
            raise SystemExit("El pictograma no puede tener texto.")
        for a in ("stroke", "stroke-width", "fill", "stroke-linecap", "stroke-linejoin", "class", "style"):
            el.attrib.pop(a, None)
        partes.append(ET.tostring(el, encoding="unicode").replace(f' xmlns="{SVG_NS}"', ""))
    if not partes or len(partes) > 3:
        raise SystemExit(f"El pictograma debe tener entre 1 y 3 elementos (tiene {len(partes)}).")
    return "".join(partes)


def svg_icono(familia: int, pictograma: str, titulo: str) -> str:
    _, ini, fin, color = FAMILIAS[familia]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" role="img" aria-label="{titulo}">'
            f'<title>{titulo}</title>'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'   # 135°: sup. izq. → inf. der.
            f'<stop offset="0" stop-color="{ini}"/><stop offset="1" stop-color="{fin}"/></linearGradient></defs>'
            f'<rect width="48" height="48" rx="12" fill="url(#g)"/>'
            f'<g transform="translate(12 12)" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{pictograma}</g></svg>\n')


def _texto_a_trazado(texto: str, alto_mayusculas: float, x: float, y_base: float, color: str) -> tuple[str, float]:
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    f = TTFont(FUENTE)
    escala = alto_mayusculas / f["OS/2"].sCapHeight
    cmap, glifos, hmtx = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
    trazos, avance = [], 0.0
    for ch in texto:
        nombre = cmap.get(ord(ch))
        if nombre is None:
            raise SystemExit(f"La fuente no tiene el carácter «{ch}».")
        pen = SVGPathPen(glifos)
        glifos[nombre].draw(TransformPen(pen, (escala, 0, 0, -escala, x + avance, y_base)))
        if pen.getCommands():
            trazos.append(pen.getCommands())
        avance += hmtx[nombre][0] * escala
    return f'<path fill="{color}" d="{" ".join(trazos)}"/>', avance


def svg_horizontal(familia: int, pictograma: str, nombre: str) -> str:
    """Ícono + nombre: altura de mayúsculas 0,4 × baldosa, separación 0,25 × baldosa, Outfit 500 en tinta."""
    lado = 48
    cap = 0.4 * lado
    x_texto = lado + 0.25 * lado
    trazo, ancho = _texto_a_trazado(nombre, cap, x_texto, lado / 2 + cap / 2, TINTA)
    icono = svg_icono(familia, pictograma, nombre)
    interior = icono[icono.index("<defs>"):icono.rindex("</svg>")]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x_texto + ancho:.1f} {lado}" role="img" '
            f'aria-label="{nombre}"><title>{nombre}</title>{interior}{trazo}</svg>\n')


def _png(svg: str, destino: Path, tam: int, fondo_blanco: bool = False):
    """Rasteriza con el navegador del equipo (Chrome o Edge sin interfaz), con fondo transparente."""
    navegadores = [shutil.which("chrome"), r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                   "/opt/pw-browsers/chromium", shutil.which("msedge"),
                   r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
    nav = next((n for n in navegadores if n and Path(n).exists()), None)
    if not nav:
        raise SystemExit("Para los PNG se necesita Chrome o Edge instalado.")
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "i.html"
        if fondo_blanco:  # pantalla de inicio del teléfono: baldosa con margen de resguardo 0,25 × lado
            lado = round(tam / 1.5)
            interior = svg.replace("<svg ", '<svg width="100%" height="100%" ', 1)
            cuerpo = (f'<div style="width:{tam}px;height:{tam}px;background:#fff;display:grid;place-items:center">'
                      f'<div style="width:{lado}px;height:{lado}px">{interior}</div></div>')
        else:
            cuerpo = svg.replace("<svg ", f'<svg width="{tam}" height="{tam}" ', 1)
        html.write_text(f'<!doctype html><html><body style="margin:0;background:transparent">{cuerpo}</body></html>',
                        encoding="utf-8")
        subprocess.run([nav, "--headless", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                        f"--user-data-dir={Path(tmp) / 'perfil'}", "--no-first-run", "--disable-extensions",
                        f"--window-size={tam},{tam}", f"--screenshot={destino}", html.as_uri()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        if not destino.exists():
            raise SystemExit(f"No se pudo generar {destino.name}.")


def generar(nombre: str, familia: int, pictograma_svg: Path) -> Path:
    if familia not in FAMILIAS:
        raise SystemExit("La familia va de 1 a 5 (ver docs/diseno/).")
    for p in problemas_nombre(nombre):
        print("Aviso:", p)
    n = slug(nombre)
    picto = _pictograma(pictograma_svg)
    carpeta = DIR_ENTREGA / n
    carpeta.mkdir(parents=True, exist_ok=True)
    DIR_APP.mkdir(parents=True, exist_ok=True)
    icono = svg_icono(familia, picto, nombre)
    (carpeta / f"{n}.svg").write_text(icono, encoding="utf-8")
    (carpeta / f"{n}-horizontal.svg").write_text(svg_horizontal(familia, picto, nombre), encoding="utf-8")
    for t in TAMANOS_PNG:
        _png(icono, carpeta / f"{n}-{t}.png", t)
    _png(icono, carpeta / f"{n}-app-180.png", 180, fondo_blanco=True)
    shutil.copy2(carpeta / f"{n}.svg", DIR_APP / f"{n}.svg")
    print(f"Ícono de «{nombre}» (familia {familia}: {FAMILIAS[familia][0]}) en {carpeta}")
    return carpeta


# ------------------------------------------------------------------ verificación
def verificar(n: str, familia: int) -> list[str]:
    """Revisa lo que se puede revisar automáticamente de la checklist de la guía."""
    if familia not in FAMILIAS:
        return ["la familia va de 1 a 5 (docs/diseno/)."]
    _, ini, fin, color = FAMILIAS[familia]
    app = DIR_APP / f"{n}.svg"
    if not app.exists():
        return [f"falta frontend/img/modulos/{n}.svg (generarlo con backend/logo_modulo.py)."]
    svg = app.read_text(encoding="utf-8")
    errores = []
    if 'viewBox="0 0 48 48"' not in svg:
        errores.append("el ícono debe tener viewBox 0 0 48 48.")
    if not re.search(r'<rect[^>]*width="48"[^>]*height="48"[^>]*rx="12"', svg):
        errores.append("la baldosa debe ser de 48 × 48 con radio 12.")
    paradas = [c.upper() for c in re.findall(r'stop-color="(#[0-9a-fA-F]{6})"', svg)]
    if paradas != [ini, fin] or 'x1="0" y1="0" x2="1" y2="1"' not in svg:
        errores.append(f"el degradado debe ir de {ini} a {fin} a 135° (familia {familia}).")
    if f'stroke="{color}"' not in svg or 'stroke-width="2"' not in svg:
        errores.append(f"el pictograma va con trazo 2 en {'blanco' if color == BLANCO else 'tinta #2B3440'}.")
    if re.search(r"<text|<filter", svg):
        errores.append("el ícono no lleva texto ni efectos.")
    if "stroke-dasharray" in svg:
        errores.append("el pictograma es el provisional de nuevo-modulo: reemplázalo por uno propio (Lucide).")
    faltan = [a.format(n=n) for a in ARCHIVOS if not (DIR_ENTREGA / n / a.format(n=n)).exists()]
    if faltan:
        errores.append(f"faltan archivos de la entrega en docs/logo/modulos/{n}/: {', '.join(faltan)}.")
    return errores


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nombre")
    ap.add_argument("--familia", type=int, required=True)
    ap.add_argument("--pictograma", type=Path)
    ap.add_argument("--verificar", metavar="NOMBRE-DE-ARCHIVO")
    a = ap.parse_args()
    if a.verificar:
        e = verificar(a.verificar, a.familia)
        print("\n".join(e) if e else "Cumple lo que se revisa automáticamente. Falta verlo en claro y oscuro y la aprobación de la Unidad.")
        sys.exit(1 if e else 0)
    if not (a.nombre and a.pictograma):
        ap.error("--nombre y --pictograma son obligatorios para generar.")
    generar(a.nombre, a.familia, a.pictograma)
