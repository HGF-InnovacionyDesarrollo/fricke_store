"""Genera logo_pantalla.h: la pantalla de presentación del Monitor T/H (170x320, RGB565), según
las directrices de diseño de Fricke Store (docs/diseno/ del repositorio fricke_store):

- Al centro, el ícono y el nombre de F+data, el módulo de Fricke Store que recibe estos datos
  (combinación "Ícono + nombre" de la Parte 2: nombre a la derecha en Outfit Medium, altura de
  mayúsculas 0,4 × baldosa, separación 0,25 × baldosa, en #E6ECF3 sobre fondo oscuro).
- Abajo y más chico, "Funciona con" y el logo completo de Fricke Store en su versión oscura, tal
  cual (sin recortar, recolorear ni deformar) y nunca a menos de 24 px de alto.
- Fondo #141A22 (el fondo oscuro permitido) y texto en la tipografía del sistema (Segoe UI).

Uso (desde la carpeta del proyecto):
    python herramientas/generar_logo.py logo_fricke_store_oscuro.png logo_pantalla.h [vista_previa.png]
    python herramientas/generar_logo.py logo_fricke_store_oscuro.png logo_pantalla_240.h [vista_previa.png] --ancho 240

--ancho 240 es para la pantalla de 2,4" (modelo de pantalla 2 en el Configurador).
Necesita junto al proyecto: logo_f-data.png (ícono del módulo) y outfit-500.ttf (fuente de marca).
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

ANCHO, ALTO = 170, 320  # --ancho cambia ANCHO
FONDO = (0x14, 0x1A, 0x22)     # --fondo (modo oscuro)
TEXTO = (0xE6, 0xEC, 0xF3)     # --texto
TEXTO_2 = (0xC3, 0xCC, 0xD6)   # --texto-2
TEXTO_3 = (0x8D, 0x98, 0xA5)   # --texto-3
NOMBRE_MODULO = "F+data"
ICONO_MODULO = "logo_f-data.png"      # baldosa de F+data (docs/logo/modulos/f-data/f-data-512.png del portal)
FUENTE_MARCA = "outfit-500.ttf"       # Outfit Medium: solo para el nombre del módulo (licencia SIL OFL)
RESPALDO = "Funciona con"             # sobre el logo de Fricke Store
FUENTES = [r"C:\Windows\Fonts\segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
# El firmware escribe "Equipo MTH-01  v2.1" en y = 212 (1,9") o 228 (2,4"): esa franja queda libre
# (ver dibujar() en Monitor_TH.ino).


def fuente(tam: int):
    for ruta in FUENTES:
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def centrado(dibujo, y: int, texto: str, f, color) -> None:
    ancho = dibujo.textlength(texto, font=f)
    dibujo.text(((ANCHO - ancho) / 2, y), texto, font=f, fill=color)


def componer(ruta_logo: str) -> Image.Image:
    """Ícono + nombre de F+data al centro y, abajo y más chico, "Funciona con" + logo de Fricke Store."""
    pantalla = Image.new("RGB", (ANCHO, ALTO), FONDO)
    dibujo = ImageDraw.Draw(pantalla)
    grande = ANCHO >= 200

    # 1) Ícono + nombre (Parte 2, "Ícono + nombre"): nombre a la derecha, altura de mayúsculas
    #    0,4 × baldosa, separación 0,25 × baldosa, Outfit Medium en #E6ECF3 (modo oscuro).
    baldosa = 64 if grande else 48
    icono = Image.open(ICONO_MODULO).convert("RGBA").resize((baldosa, baldosa), Image.LANCZOS)
    tam = 10
    while True:  # tamaño de letra cuya altura de mayúsculas sea 0,4 × baldosa
        f = ImageFont.truetype(FUENTE_MARCA, tam)
        alto_mayus = -f.getbbox("H", anchor="ls")[1]
        if alto_mayus >= 0.4 * baldosa:
            break
        tam += 1
    ancho_nombre = dibujo.textlength(NOMBRE_MODULO, font=f)
    separacion = round(0.25 * baldosa)
    total = baldosa + separacion + ancho_nombre
    x = round((ANCHO - total) / 2)
    y_icono = 92 if not grande else 84
    pantalla.paste(icono, (x, y_icono), icono)
    linea_base = y_icono + baldosa / 2 + alto_mayus / 2
    dibujo.text((x + baldosa + separacion, linea_base), NOMBRE_MODULO, font=f, fill=TEXTO, anchor="ls")

    # 2) Qué es, en la tipografía de la interfaz
    tam_ui = 15 if grande else 12
    fu = fuente(tam_ui)
    y = y_icono + baldosa + 20
    for linea in ["Monitor de temperatura", "y humedad"]:
        centrado(dibujo, y, linea, fu, TEXTO_2)
        y += tam_ui + 4

    # 3) Abajo: "Funciona con" y el logo de Fricke Store completo (versión oscura, sin modificar,
    #    nunca menos de 24 px de alto).
    logo = Image.open(ruta_logo).convert("RGBA")
    alto_logo = 30 if grande else 24
    ancho_logo = round(logo.width * alto_logo / logo.height)
    logo = logo.resize((ancho_logo, alto_logo), Image.LANCZOS)
    y_logo = ALTO - 16 - alto_logo
    pantalla.paste(logo, ((ANCHO - ancho_logo) // 2, y_logo), logo)
    fp = fuente(11 if not grande else 12)
    centrado(dibujo, y_logo - 18, RESPALDO, fp, TEXTO_3)
    return pantalla


def a_rgb565(imagen: Image.Image) -> list[int]:
    datos = imagen.get_flattened_data() if hasattr(imagen, "get_flattened_data") else imagen.getdata()
    return [((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3) for r, g, b in datos]


def main() -> None:
    global ANCHO
    args = sys.argv[1:]
    if "--ancho" in args:
        i = args.index("--ancho")
        ANCHO = int(args[i + 1])
        del args[i:i + 2]
    ruta_logo, ruta_h = args[0], args[1]
    pantalla = componer(ruta_logo)
    if len(args) > 2:
        pantalla.save(args[2])

    valores = a_rgb565(pantalla)
    with open(ruta_h, "w", encoding="utf-8") as h:
        h.write("// Generado por herramientas/generar_logo.py — no editar a mano.\n")
        h.write("// Pantalla de presentación: F+data y, abajo, \"Funciona con\" Fricke Store.\n")
        h.write("#pragma once\n#include <Arduino.h>\n\n")
        # Un arreglo por ancho (LOGO_PANTALLA_170, LOGO_PANTALLA_240): el firmware incluye los dos
        # y usa el de la pantalla configurada.
        h.write(f"static const uint16_t LOGO_PANTALLA_{ANCHO}[{ANCHO} * {ALTO}] PROGMEM = {{\n")
        for i in range(0, len(valores), 16):
            h.write("  " + ", ".join(f"0x{v:04X}" for v in valores[i:i + 16]) + ",\n")
        h.write("};\n")
    print(f"{ruta_h}: {len(valores)} pixeles ({len(valores) * 2} bytes)")


if __name__ == "__main__":
    main()
