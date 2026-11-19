"""Genera logo_marca.h: el ícono de F+data siempre visible en la cabecera del Monitor T/H.

Según las directrices de diseño de Fricke Store (docs/diseno/, Parte 2): el ícono de módulo se
muestra a 24 px de lado como mínimo y con un área de resguardo de 0,25 × su lado (6 px) libre
alrededor; el firmware respeta ese margen al ubicarlo (ver dibujar() en Monitor_TH.ino).

La pantalla dibuja sobre un lienzo de colores indexados (máximo 256 colores en total, compartidos
con toda la interfaz), así que el degradado se reduce a pocos colores. A 24 px la diferencia no
se nota y el lienzo no se queda sin colores. Los píxeles transparentes (esquinas redondeadas)
no se dibujan, para que la baldosa quede bien sobre cualquier color de cabecera.

Uso (desde la carpeta del proyecto):
    python herramientas/generar_marca.py logo_marca.h [vista_previa.png]
Necesita junto al proyecto: logo_f-data.png (ícono del módulo, 512 px).
"""

import sys

from PIL import Image

ICONO_MODULO = "logo_f-data.png"  # docs/logo/modulos/f-data/f-data-512.png del portal
LADO = 24                          # mínimo de las directrices para el ícono en pantalla
COLORES = 32                       # colores del degradado y el pictograma tras reducirlos (de 256 del lienzo)
TRANSPARENTE = 0xFF


def rgb565(r: int, g: int, b: int) -> int:
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def generar(salida: str, vista: str | None) -> None:
    icono = Image.open(ICONO_MODULO).convert("RGBA").resize((LADO, LADO), Image.LANCZOS)
    alfa = icono.getchannel("A")
    reducido = icono.convert("RGB").quantize(colors=COLORES, method=Image.Quantize.MEDIANCUT)
    paleta = reducido.getpalette()[: COLORES * 3]
    indices = list(reducido.tobytes())
    pixeles = [i if a >= 128 else TRANSPARENTE for i, a in zip(indices, alfa.tobytes())]
    usados = sorted({i for i in pixeles if i != TRANSPARENTE})
    nuevo = {viejo: n for n, viejo in enumerate(usados)}
    pixeles = [nuevo.get(i, TRANSPARENTE) for i in pixeles]
    colores = [tuple(paleta[3 * i: 3 * i + 3]) for i in usados]

    with open(salida, "w", encoding="utf-8", newline="\n") as f:
        f.write("// Generado por herramientas/generar_marca.py — no editar a mano.\n")
        f.write("// Ícono de F+data (24 px, el mínimo de las directrices) para la cabecera de la pantalla.\n")
        f.write("#pragma once\n#include <Arduino.h>\n\n")
        f.write(f"#define MARCA_LADO {LADO}\n#define MARCA_TRANSPARENTE 0x{TRANSPARENTE:02X}\n\n")
        f.write(f"static const uint16_t MARCA_PALETA[{len(colores)}] = {{\n  ")
        f.write(", ".join(f"0x{rgb565(*c):04X}" for c in colores))
        f.write("};\n\n")
        f.write(f"static const uint8_t MARCA_PIXELES[{LADO} * {LADO}] PROGMEM = {{\n")
        for y in range(LADO):
            fila = pixeles[y * LADO:(y + 1) * LADO]
            f.write("  " + ", ".join(f"0x{p:02X}" for p in fila) + ",\n")
        f.write("};\n")

    if vista:  # sobre el color de la cabecera (--superficie), ampliado 8 veces para revisarlo
        img = Image.new("RGB", (LADO, LADO), (0x1D, 0x25, 0x30))
        for n, p in enumerate(pixeles):
            if p != TRANSPARENTE:
                img.putpixel((n % LADO, n // LADO), colores[p])
        img.resize((LADO * 8, LADO * 8), Image.NEAREST).save(vista)
    print(f"{salida}: {len(colores)} colores")


if __name__ == "__main__":
    generar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
