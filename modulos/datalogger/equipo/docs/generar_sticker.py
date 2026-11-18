"""Genera el sticker con las instrucciones de uso del Monitor T/H (75 x 38 mm, para
la cara superior de la caja) y una hoja carta con varias copias para imprimir en
papel adhesivo.  Uso:  python docs/generar_sticker.py
"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

BASE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE, "..", "LOGO HGF.png")
SALIDA = os.path.join(BASE, "Sticker_instrucciones_Monitor_TH.pdf")
SALIDA_HOJA = os.path.join(BASE, "Sticker_instrucciones_Monitor_TH_hoja_carta.pdf")

ANCHO, ALTO = 75 * mm, 38 * mm
CODIGO = "MTH-01"  # MONITOR_CODIGO de config.h
AZUL = colors.HexColor("#1F497D")
GRIS_TEXTO = colors.HexColor("#222222")
# Colores de la pantalla
VERDE, AMARILLO, ROJO, GRIS = (colors.HexColor(c) for c in ("#2E9E44", "#F2C200", "#D62828", "#8A8A8A"))


def texto(c, x, y, t, tam, negrita=False, color=GRIS_TEXTO):
    c.setFont("Helvetica-Bold" if negrita else "Helvetica", tam)
    c.setFillColor(color)
    c.drawString(x, y, t)


def linea_mixta(c, x, y, partes, tam):
    """partes: [(texto, negrita), ...] en una sola línea."""
    for t, negrita in partes:
        fuente = "Helvetica-Bold" if negrita else "Helvetica"
        c.setFont(fuente, tam)
        c.setFillColor(GRIS_TEXTO)
        c.drawString(x, y, t)
        x += c.stringWidth(t, fuente, tam)


def sticker(c, x0, y0, borde=True):
    c.saveState()
    c.translate(x0, y0)
    if borde:  # línea de corte: segmentada, gris medio, esquinas redondeadas
        c.setStrokeColor(colors.HexColor("#808080"))
        c.setLineWidth(0.5)
        c.setDash(2, 1.5)
        c.roundRect(0, 0, ANCHO, ALTO, 2 * mm)
        c.setDash()

    # Encabezado: logo + título sobre franja azul
    m = 2.5 * mm
    c.setFillColor(AZUL)
    c.roundRect(m, ALTO - m - 8.5 * mm, ANCHO - 2 * m, 8.5 * mm, 1.2 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.roundRect(m + 0.6 * mm, ALTO - m - 7.9 * mm, 7.3 * mm, 7.3 * mm, 0.8 * mm, stroke=0, fill=1)
    c.drawImage(LOGO, m + 0.8 * mm, ALTO - m - 7.7 * mm, 6.9 * mm, 6.9 * mm, preserveAspectRatio=True, mask="auto")
    texto(c, m + 9.6 * mm, ALTO - m - 4.0 * mm, "MONITOR DE TEMPERATURA Y HUMEDAD", 6.4, True, colors.white)
    # Código del equipo, recuadrado a la derecha del título
    c.setFont("Helvetica-Bold", 6.4)
    w = c.stringWidth(CODIGO, "Helvetica-Bold", 6.4) + 2 * mm
    xc = ANCHO - m - 0.8 * mm - w
    c.setFillColor(colors.white)
    c.roundRect(xc, ALTO - m - 4.75 * mm, w, 3.3 * mm, 0.6 * mm, stroke=0, fill=1)
    c.setFillColor(AZUL)
    c.drawString(xc + 1 * mm, ALTO - m - 4.0 * mm, CODIGO)
    texto(c, m + 9.6 * mm, ALTO - m - 6.9 * mm, "Hospital Dr. Gustavo Fricke · Unidad de Innovación y Desarrollo", 4.6,
          False, colors.white)

    # Columna izquierda: pulsador
    xi, y = m, ALTO - m - 12.2 * mm
    texto(c, xi, y, "PULSADOR (costado derecho)", 5.4, True, AZUL)
    tam, paso = 5.0, 2.45 * mm
    filas = [
        [("1 toque: ", True), ("silencia la alarma 30 min", False)],
        [("", False), ("o cambia de página", False)],
        [("Mantener 3 s: ", True), ("retirar la tarjeta SD", False)],
        [("", False), ("(esperar «Puede retirar»)", False)],
        [("2 toques: ", True), ("emparejar sensor (técnico)", False)],
    ]
    for f in filas:
        y -= paso
        linea_mixta(c, xi + (3 * mm if not f[0][0] else 0), y, f, tam)

    # Columna derecha: colores
    xd = m + 37.5 * mm
    y = ALTO - m - 12.2 * mm
    texto(c, xd, y, "COLORES EN PANTALLA", 5.4, True, AZUL)
    for color, t in ((VERDE, "En rango"), (AMARILLO, "Atención: cerca del límite"),
                     (ROJO, "ALARMA: fuera de rango"), (GRIS, "Sin datos del sensor")):
        y -= paso
        c.setFillColor(color)
        c.roundRect(xd, y - 0.25 * mm, 3.2 * mm, 2.0 * mm, 0.4 * mm, stroke=0, fill=1)
        texto(c, xd + 4.2 * mm, y, t, tam, color == ROJO)
    y -= paso
    linea_mixta(c, xd, y, [("Pitido cada 10 s: ", True), ("revisar la SD", False)], tam)

    # Separador vertical
    c.setStrokeColor(colors.HexColor("#C8D3E3"))
    c.setLineWidth(0.4)
    c.line(m + 36 * mm, ALTO - m - 10.3 * mm, m + 36 * mm, m + 6.6 * mm)

    # Pie: corte de luz y advertencia
    c.setFillColor(colors.HexColor("#FDF1D2"))
    c.roundRect(m, m, ANCHO - 2 * m, 5.6 * mm, 1 * mm, stroke=0, fill=1)
    linea_mixta(c, m + 1.5 * mm, m + 3.3 * mm,
                [("Tras un corte de luz: ", True), ("dar un toque al botón de cada sensor.", False)], 5.0)
    linea_mixta(c, m + 1.5 * mm, m + 1.0 * mm,
                [("No desconectar ni sacar la SD sin el pulsador. ", True), ("Dudas: anexo 320665.", False)],
                4.6)
    c.restoreState()


# Sticker suelto a tamaño real, con 3 mm alrededor para que se vea la línea de corte
MARGEN = 3 * mm
c = canvas.Canvas(SALIDA, pagesize=(ANCHO + 2 * MARGEN, ALTO + 2 * MARGEN))
c.setTitle("Sticker de instrucciones – Monitor T/H")
sticker(c, MARGEN, MARGEN)
c.showPage()
c.save()

# Hoja carta: 2 columnas x 6 filas, con 6 mm entre copias
c = canvas.Canvas(SALIDA_HOJA, pagesize=letter)
c.setTitle("Stickers de instrucciones – Monitor T/H (hoja carta)")
pw, ph = letter
sep = 6 * mm
cols, filas = 2, 6
x_ini = (pw - (cols * ANCHO + (cols - 1) * sep)) / 2
y_ini = (ph - (filas * ALTO + (filas - 1) * sep)) / 2
for i in range(cols):
    for j in range(filas):
        sticker(c, x_ini + i * (ANCHO + sep), y_ini + j * (ALTO + sep))
c.setFont("Helvetica", 7)
c.setFillColor(colors.HexColor("#777777"))
c.drawCentredString(pw / 2, 8 * mm, "Imprimir al 100 % (tamaño real, sin «ajustar a la página»). Recortar por la línea segmentada: 75 × 38 mm.")
c.showPage()
c.save()
print(SALIDA)
print(SALIDA_HOJA)
