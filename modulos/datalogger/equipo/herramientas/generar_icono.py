"""Genera el logo del aplicativo Monitor T/H Hospital Dr. Gustavo Fricke (icono.ico + icono.png).

Termómetro (bulbo rojo) y gota de humedad sobre fondo azul, con una insignia de
engranaje (configuración) en los tamaños grandes. Colores del manual gráfico de
Gobierno de Chile (azul #0F69B4, rojo #EB3C46).

Uso:  python herramientas/generar_icono.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

AZUL = (15, 105, 180)
AZUL_OSC = (8, 62, 112)
ROJO = (235, 60, 70)
BLANCO = (255, 255, 255)
S = 1024  # lienzo de trabajo (se reduce con antialiasing)

SALIDA = Path(__file__).resolve().parent.parent / "configurador"


def fondo(d):
    # cuadrado redondeado con degradado vertical
    mascara = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((32, 32, S - 32, S - 32), 210, fill=255)
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        gd.line((0, y, S, y), fill=tuple(int(a + (b - a) * t) for a, b in zip(AZUL, AZUL_OSC)))
    d.paste(grad, (0, 0), mascara)


def termometro(d, cx, top, bottom, ancho, bulbo):
    # contorno blanco
    d.rounded_rectangle((cx - ancho / 2, top, cx + ancho / 2, bottom), ancho / 2, fill=BLANCO)
    d.ellipse((cx - bulbo, bottom - bulbo * 0.6, cx + bulbo, bottom + bulbo * 1.4), fill=BLANCO)
    # columna y bulbo rojos
    m = ancho * 0.24
    d.rounded_rectangle((cx - ancho / 2 + m, top + (bottom - top) * 0.38,
                         cx + ancho / 2 - m, bottom + 10), (ancho / 2 - m), fill=ROJO)
    b2 = bulbo - m * 1.1
    d.ellipse((cx - b2, bottom + bulbo * 0.4 - b2, cx + b2, bottom + bulbo * 0.4 + b2), fill=ROJO)


def gota(d, cx, cy, r, color):
    # círculo + triángulo tangente hacia arriba
    alto = r * 2.1
    ang = math.asin(r / alto)
    px, py = cx, cy - alto
    tx = r * math.cos(ang)
    ty = r * math.sin(ang)
    d.polygon([(px, py), (cx - tx, cy - ty), (cx + tx, cy - ty)], fill=color)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def engranaje(d, cx, cy, r, color, fondo_color):
    dientes = 8
    pts = []
    for i in range(dientes * 4):
        a = 2 * math.pi * i / (dientes * 4)
        rr = r if (i % 4) in (0, 1) else r * 0.78
        pts.append((cx + rr * math.cos(a + math.pi / 32), cy + rr * math.sin(a + math.pi / 32)))
    d.polygon(pts, fill=color)
    d.ellipse((cx - r * 0.34, cy - r * 0.34, cx + r * 0.34, cy + r * 0.34), fill=fondo_color)


def dibujar(con_insignia):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fondo(im)
    d = ImageDraw.Draw(im)
    termometro(d, cx=360, top=200, bottom=640, ancho=150, bulbo=125)
    gota(d, cx=660, cy=530, r=145, color=BLANCO)
    # brillo dentro de la gota
    d.ellipse((585, 490, 625, 570), fill=(200, 225, 245))
    if con_insignia:
        cx, cy, r = 815, 815, 150
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=BLANCO)
        engranaje(d, cx, cy, r * 0.72, AZUL, BLANCO)
    return im


def main():
    grande = dibujar(True)
    chico = dibujar(False)  # sin engranaje: a 16-32 px solo se ve ruido
    tam = [16, 24, 32, 48, 64, 128, 256]
    imgs = [(chico if t <= 32 else grande).resize((t, t), Image.LANCZOS) for t in tam]
    imgs[-1].save(SALIDA / "icono.ico", sizes=[(t, t) for t in tam], append_images=imgs[:-1])
    grande.resize((512, 512), Image.LANCZOS).save(SALIDA / "icono.png")
    # logo de la cabecera del aplicativo (1x y 2x para pantallas con escala)
    chico.resize((44, 44), Image.LANCZOS).save(SALIDA / "logo_app.png")
    chico.resize((88, 88), Image.LANCZOS).save(SALIDA / "logo_app_2x.png")
    print("Listo:", SALIDA / "icono.ico", SALIDA / "icono.png")


if __name__ == "__main__":
    main()
