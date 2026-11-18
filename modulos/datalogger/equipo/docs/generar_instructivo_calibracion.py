"""Genera el PDF del instructivo de calibración por comparación de los sensores
del Monitor T/H.  Uso:  python docs/generar_instructivo_calibracion.py
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

BASE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE, "..", "LOGO HGF.png")
SALIDA = os.path.join(BASE, "Instructivo_calibracion_sensores_Monitor_TH.pdf")

AZUL = colors.HexColor("#1F4E79")
GRIS = colors.HexColor("#F2F2F2")

est = getSampleStyleSheet()
T = ParagraphStyle("t", parent=est["Title"], fontSize=16, textColor=AZUL, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=est["Heading2"], fontSize=12.5, textColor=AZUL, spaceBefore=10, spaceAfter=4)
H2 = ParagraphStyle("h2", parent=est["Heading3"], fontSize=11, textColor=AZUL, spaceBefore=6, spaceAfter=2)
P = ParagraphStyle("p", parent=est["BodyText"], fontSize=10, leading=13.5, spaceAfter=4)
PL = ParagraphStyle("pl", parent=P, leftIndent=14, bulletIndent=4)
CEL = ParagraphStyle("c", parent=P, fontSize=9, leading=11, spaceAfter=0)
CELC = ParagraphStyle("cc", parent=CEL, alignment=TA_CENTER)
NOTA = ParagraphStyle("n", parent=P, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"))


def lista(items):
    return [Paragraph(i, PL, bulletText="•") for i in items]


def tabla(datos, anchos, encabezado=True, alto=None):
    filas = [[Paragraph(str(c), CEL) if not isinstance(c, Paragraph) else c for c in f] for f in datos]
    t = Table(filas, colWidths=anchos, rowHeights=alto, repeatRows=1 if encabezado else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if encabezado:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), GRIS)]
    t.setStyle(TableStyle(estilo))
    return t


def encabezado_pagina(c, doc):
    c.saveState()
    ancho, alto = c._pagesize
    if os.path.exists(LOGO):
        c.drawImage(LOGO, 1.8 * cm, alto - 2.6 * cm, width=1.7 * cm, height=1.7 * cm, preserveAspectRatio=True,
                    mask="auto")
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(3.9 * cm, alto - 1.45 * cm, "Hospital Dr. Gustavo Fricke")
    c.setFont("Helvetica", 8.5)
    c.drawString(3.9 * cm, alto - 1.9 * cm, "Unidad de Innovación y Desarrollo")
    c.drawString(3.9 * cm, alto - 2.3 * cm, "Instructivo: Calibración por comparación de sensores del Monitor T/H")
    c.drawRightString(ancho - 1.8 * cm, alto - 1.45 * cm, "Versión 1.4 (borrador)")
    c.drawRightString(ancho - 1.8 * cm, alto - 1.9 * cm, "Fecha: octubre 2026")
    c.drawRightString(ancho - 1.8 * cm, alto - 2.3 * cm, f"Página {doc.page}")
    c.setStrokeColor(AZUL)
    c.setLineWidth(1)
    c.line(1.8 * cm, alto - 2.75 * cm, ancho - 1.8 * cm, alto - 2.75 * cm)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawCentredString(ancho / 2, 1.2 * cm, "Documento en borrador: debe ser revisado y aprobado por Farmacia, Esterilización y la Unidad de "
                                             "Calidad y Seguridad del Paciente antes de su uso.")
    c.restoreState()


s = []
s.append(Paragraph("Instructivo de calibración por comparación de los sensores de temperatura y humedad", T))
s.append(Paragraph("Monitor T/H – registrador de datos para áreas de almacenamiento de medicamentos y material estéril", ParagraphStyle(
    "st", parent=P, alignment=TA_CENTER, textColor=colors.HexColor("#555555"))))
s.append(Spacer(1, 6))

s.append(Paragraph("1. Objetivo", H1))
s.append(Paragraph(
    "Determinar la diferencia entre la lectura de cada sensor del Monitor T/H y un instrumento de referencia "
    "calibrado, y aplicar la corrección correspondiente, de modo que las mediciones registradas sean trazables a "
    "los patrones nacionales.", P))

s.append(Paragraph("2. Alcance", H1))
s.append(Paragraph(
    "Aplica a los sensores inalámbricos de temperatura y humedad relativa asociados al Monitor T/H instalados en "
    "áreas de almacenamiento a temperatura ambiente, según el perfil asignado a cada sensor:", P))
s.append(tabla([
    ["Perfil", "Área", "Temperatura", "Humedad relativa", "Protocolo"],
    ["MEDICAMENTOS", "Almacenamiento de medicamentos", "15 a 25 °C (hasta 30 °C por periodos breves)",
     "no mayor a 60 %", "APF 1.5"],
    ["MATERIAL ESTERIL", "Almacenamiento de material estéril", "18 a 24 °C", "30 % a 50 %", "APE 1.4"],
], [3.2 * cm, 4.2 * cm, 4.4 * cm, 2.8 * cm, 2.4 * cm]))
s.append(Paragraph("No aplica a refrigeradores.", P))

s.append(Paragraph("3. Marco de referencia", H1))
s += lista([
    "<b>Norma Técnica N° 147 (ISP)</b>, Buenas Prácticas de Almacenamiento y Distribución: los equipos de medición "
    "deben controlarse y calibrarse según un programa establecido, con certificados trazables a patrones nacionales.",
    "<b>Resolución Exenta N° 1539 (ISP)</b>: guía de calificación de áreas de almacenamiento con temperatura "
    "controlada (IQ/OQ/PQ, mapeo térmico).",
    "<b>Protocolo APF 1.5 (HGF)</b>, Almacenamiento y conservación de medicamentos: los dispositivos de medición "
    "deben contar con calibración al menos una vez al año.",
    "<b>Protocolo APE 1.4 (HGF)</b>, Almacenamiento y distribución de material estéril: define las condiciones de "
    "temperatura (18 a 24 °C) y humedad relativa (30 % a 50 %) del área de almacenamiento.",
    "<b>Norma técnica sobre esterilización y desinfección de alto nivel y uso de artículos médicos estériles "
    "(MINSAL, 2018)</b>, citada por el protocolo APE 1.4.",
    "<b>OMS, Informe Técnico N° 961, Anexo 9</b>, suplementos 6 (sistemas de monitoreo de temperatura y humedad en "
    "áreas fijas) y 8 (mapeo térmico).",
    "<b>Trazabilidad</b>: patrón nacional de temperatura (LCPN-T, CESMEC) y de humedad (ENAER), Red Nacional de "
    "Metrología del INN; laboratorios acreditados bajo NCh-ISO/IEC 17025.",
])

s.append(Paragraph("4. Exactitud del sistema", H1))
s.append(Paragraph(
    "La calibración corrige la diferencia sistemática (desplazamiento) de cada sensor, pero no mejora su exactitud "
    "más allá de lo que el sensor permite. El monitor admite sensores de distintos modelos; para cada uno se "
    "consideran las siguientes fuentes de error (los valores de los sensores en uso a octubre de 2026 se indican "
    "como referencia y son el margen mínimo a considerar):", P))
s.append(tabla([
    ["Fuente", "Sensores en uso (oct. 2026)", "Origen"],
    ["Exactitud declarada del sensor", "±1 °C y ±5 % HR", "Manual o ficha técnica del fabricante de cada modelo"],
    ["Paso de reporte: algunos sensores solo envían un dato nuevo cuando el valor cambia", "aprox. 0,5 °C y 5 % HR",
     "Observado en los registros del monitor (columna «Hora de la lectura»)"],
    ["Incertidumbre del instrumento de referencia", "según certificado", "Certificado de calibración"],
], [6.6 * cm, 4.2 * cm, 6.2 * cm]))
s.append(Spacer(1, 4))
s.append(Paragraph(
    "Con los sensores en uso, la exactitud esperable del sistema después de la corrección es del orden de "
    "<b>±0,5 a ±1 °C</b> y <b>±5 % HR</b>. Se recomienda que los responsables de cada área evalúen un "
    "<b>margen de guarda</b> en los límites de alarma (por ejemplo, considerar que una lectura de 29,5 °C podría "
    "corresponder a una temperatura real sobre 30 °C). Al incorporar un modelo nuevo, registrar su exactitud "
    "declarada en el Anexo B.", P))
s.append(Paragraph(
    "<b>Material estéril:</b> sus rangos son estrechos (6 °C de temperatura y 20 puntos de humedad). Con los "
    "sensores en uso, el error de humedad (±5 % HR) equivale a un cuarto de la banda permitida: una lectura de "
    "46 % HR podría corresponder a más de 50 % real. Para esta área se recomienda considerar sensores de mayor "
    "exactitud o, al menos, un margen de guarda explícito definido por la enfermera supervisora de Esterilización.",
    P))

s.append(Paragraph("5. Responsables", H1))
s.append(tabla([
    ["Rol", "Responsabilidad"],
    ["Químico farmacéutico (área de medicamentos) / Enfermera supervisora de Esterilización (área de material "
     "estéril) / Unidad de Calidad", "Aprobar el instructivo, validar los criterios de aceptación y firmar el "
                                     "registro de su área."],
    ["Ejecutor (Unidad de Innovación y Desarrollo o personal capacitado)", "Realizar la comparación, completar el "
                                                                           "formulario y calcular las correcciones."],
    ["Unidad de Innovación y Desarrollo", "Cargar las correcciones en el Monitor T/H y verificar su aplicación."],
], [6.5 * cm, 10.5 * cm]))

s.append(Paragraph("6. Materiales", H1))
s += lista([
    "<b>Termohigrómetro de referencia</b> con <b>certificado de calibración vigente</b> emitido por un laboratorio "
    "acreditado por el INN. Se recomienda resolución de 0,1 °C y 1 % HR, e incertidumbre declarada no mayor a "
    "±0,3 °C y ±3 % HR. Sin certificado vigente, la comparación no es válida para fines de auditoría.",
    "Monitor T/H con hora verificada y tarjeta micro SD funcionando (indicador «SD» en verde).",
    "Los sensores a calibrar, identificados por nombre y por los últimos 4 caracteres de su dirección IEEE "
    "(Anexo B).",
    "Formulario de registro (Anexo A) y lápiz.",
])

s.append(Paragraph("7. Condiciones del ensayo", H1))
s += lista([
    "Ambiente estable, idealmente la misma sala donde se usarán los sensores, entre 18 y 26 °C.",
    "Sin sol directo, sin corrientes de aire, lejos de equipos que emitan calor, puertas y ductos de climatización.",
    "Los sensores y la sonda de la referencia juntos, a la misma altura y a no más de 10 cm entre sí, sin tocarse.",
    "No manipular los sensores ni la referencia durante el ensayo: el calor de la mano altera la lectura por "
    "varios minutos.",
])

s.append(Paragraph("8. Procedimiento", H1))
s.append(Paragraph("8.1 Preparación", H2))
s += lista([
    "Verificar que el certificado de la referencia esté vigente y anotar sus datos en el formulario.",
    "Verificar que la hora del Monitor T/H sea correcta. <b>Todas las horas se anotan con el reloj del monitor</b>, "
    "para que coincidan con su registro.",
    "Confirmar que los sensores aparecen en pantalla con datos recientes y sin aviso de «sin datos».",
])
s.append(Paragraph("8.2 Estabilización (1 a 2 horas)", H2))
s.append(Paragraph(
    "Ubicar los sensores y la referencia según el punto 7 y esperar al menos 1 hora sin anotar lecturas (2 horas "
    "si los sensores venían de otro ambiente). La humedad relativa tarda más que la temperatura en igualarse.", P))
s.append(Paragraph("8.3 Comparación (3 horas)", H2))
s += lista([
    "<b>Cada 30 minutos</b> anotar en el formulario, con la hora del monitor: la lectura de la referencia "
    "(temperatura y humedad) y, al mismo tiempo, la <b>temperatura, humedad y antigüedad del dato</b> de cada "
    "sensor tal como las muestra la pantalla del monitor (la antigüedad es la indicación «hace N m»; «ahora» = 0). "
    "Se obtienen 6 a 7 lecturas.",
    "Opcional y recomendado: repetir la comparación en distintos momentos del día (mañana, mediodía y tarde) para "
    "verificar que la diferencia se mantiene en distintas temperaturas.",
    "Si la referencia registra datos automáticamente (datalogger), conservar su archivo en lugar de las "
    "anotaciones manuales.",
])
s.append(Paragraph("8.4 Cálculo de la corrección", H2))
s += lista([
    "Usar los valores de cada sensor anotados en el formulario. Se pueden contrastar con el archivo de datos del "
    "monitor (<i>datos/AAAA-MM-DD.csv</i> en la tarjeta SD), en la fila más cercana a cada hora anotada.",
    "<b>Usar solo lecturas frescas</b>: considerar una comparación solo si el dato del sensor tenía <b>10 minutos o "
    "menos</b> de antigüedad (columna «Dato de hace» del formulario, o columna «Hora de la lectura» del archivo); "
    "si no, el sensor puede estar mostrando un valor atrasado (hasta su paso de reporte). Se necesitan al menos 4 "
    "comparaciones válidas por sensor (extender el ensayo si faltan).",
    "Para cada lectura: <b>diferencia = valor de la referencia – valor del sensor</b>.",
    "<b>Corrección del sensor</b> = promedio de las diferencias (temperatura en °C con un decimal; humedad en % "
    "entero).",
    "<b>Dispersión</b> = diferencia máxima – diferencia mínima.",
])
s.append(KeepTogether([Paragraph("8.5 Criterios de aceptación (propuestos, a validar con los responsables de cada área)", H2),
tabla([
    ["Criterio", "Temperatura", "Humedad relativa", "Si no se cumple"],
    ["Dispersión de las diferencias", "máx. 0,8 °C", "máx. 6 % HR", "Repetir el ensayo con mejor estabilidad"],
    ["Magnitud de la corrección", "no mayor que la exactitud declarada (actuales: ±1,0 °C)",
     "no mayor que la exactitud declarada (actuales: ±5 % HR)", "Sensor fuera de especificación: reemplazar"],
    ["Verificación posterior (8.7)", "máx. 0,5 °C", "máx. 5 % HR", "Revisar la corrección cargada"],
], [4.3 * cm, 3.7 * cm, 3.7 * cm, 5.3 * cm]),
Paragraph("Los valores de dispersión y verificación consideran el paso de reporte de los sensores en uso; "
          "con sensores que reporten a intervalos fijos pueden exigirse valores menores.", NOTA)]))
s.append(Paragraph("8.6 Aplicación de la corrección", H2))
s.append(Paragraph(
    "La Unidad de Innovación y Desarrollo carga la corrección de cada sensor en la configuración del Monitor T/H. "
    "A partir de ese momento la pantalla, las alarmas y el archivo de datos usan el valor corregido, y cada "
    "arranque del monitor deja en el registro de eventos las correcciones vigentes.", P))
s.append(Paragraph("8.7 Verificación", H2))
s.append(Paragraph(
    "Con la corrección aplicada, mantener los sensores junto a la referencia al menos 1 hora más y anotar 2 "
    "lecturas frescas (ver 8.4). La diferencia debe cumplir el criterio de verificación del punto 8.5.", P))

s.append(Paragraph("9. Frecuencia", H1))
s += lista([
    "Una vez al año (Protocolo APF 1.5; se aplica la misma frecuencia a los sensores del área de material estéril).",
    "Al incorporar o reemplazar un sensor.",
    "Si el sensor sufre una caída o daño, o si se observan lecturas inconsistentes con otros instrumentos.",
])

s.append(Paragraph("10. Registros", H1))
s += lista([
    "Formulario del Anexo A completo y firmado.",
    "Copia del certificado de calibración vigente del instrumento de referencia.",
    "Copia de los archivos de datos y de eventos del monitor correspondientes al día del ensayo.",
    "Archivar junto a los registros del área por el plazo que defina la Unidad de Calidad.",
])

# ----------------- Anexo A: formulario (hoja horizontal) -----------------
s.append(NextPageTemplate("horizontal"))
s.append(PageBreak())
s.append(Paragraph("Anexo A. Formulario de registro de calibración por comparación", H1))
vacio = ""
s.append(tabla([
    ["Fecha", vacio, "Hora de inicio", vacio],
    ["Ejecutor", vacio, "Hora del monitor verificada", "[  ] Sí"],
    ["Área", "[  ] Medicamentos   [  ] Material estéril", "Sala / ubicación", vacio],
], [3 * cm, 5.5 * cm, 4 * cm, 4.5 * cm], encabezado=False, alto=0.65 * cm))
s.append(Spacer(1, 6))
s.append(Paragraph("Instrumento de referencia", H2))
s.append(tabla([
    ["Marca / modelo", vacio, "N° de serie", vacio],
    ["N° certificado", vacio, "Laboratorio", vacio],
    ["Fecha de calibración", vacio, "Vigente hasta", vacio],
    ["Incertidumbre T", vacio, "Incertidumbre HR", vacio],
], [3.4 * cm, 5.1 * cm, 3.4 * cm, 5.1 * cm], encabezado=False, alto=0.6 * cm))
s.append(Spacer(1, 6))
s.append(Paragraph("Lecturas cada 30 minutos (hora del monitor)", H2))
sens = "Sensor ______________"
cab1 = ["N°", "Hora", "Referencia", "", sens, "", "", sens, "", "", sens, "", ""]
cab2 = ["", "", "T (°C)", "HR (%)"] + ["T (°C)", "HR (%)", "Dato de hace (min)"] * 3
filas = [[Paragraph(c, CELC) for c in cab1], [Paragraph(c, CELC) for c in cab2]]
filas += [[Paragraph(str(i), CELC)] + [""] * 12 for i in range(1, 11)]
lect = Table(filas, colWidths=[1 * cm, 2 * cm, 1.8 * cm, 1.8 * cm] + [1.8 * cm, 1.8 * cm, 2.1 * cm] * 3,
             rowHeights=[0.6 * cm, 0.85 * cm] + [0.6 * cm] * 10, repeatRows=2)
lect.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
    ("BACKGROUND", (0, 0), (-1, 1), GRIS), ("BACKGROUND", (2, 2), (3, -1), colors.HexColor("#F7FAFD")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)), ("SPAN", (2, 0), (3, 0)),
    ("SPAN", (4, 0), (6, 0)), ("SPAN", (7, 0), (9, 0)), ("SPAN", (10, 0), (12, 0)),
    ("LINEAFTER", (3, 0), (3, -1), 1.2, AZUL), ("LINEAFTER", (6, 0), (6, -1), 1.2, AZUL),
    ("LINEAFTER", (9, 0), (9, -1), 1.2, AZUL),
]))
s.append(lect)
s.append(Paragraph("En «Sensor» escribir el nombre que muestra la pantalla. «Dato de hace»: la indicación «hace N m» "
                   "del sensor en la pantalla («ahora» = 0). Una comparación es válida si el dato tiene 10 minutos o "
                   "menos.", NOTA))
s.append(Spacer(1, 6))
s.append(Paragraph("Resultados por sensor", H2))
filas = [["Sensor (nombre / IEEE)", "Corrección T (°C)", "Dispersión T", "Corrección HR (%)", "Dispersión HR",
          "Acepta"]]
filas += [[vacio, vacio, vacio, vacio, vacio, "[  ] Sí [  ] No"] for _ in range(4)]
s.append(tabla(filas, [6.4 * cm, 3.4 * cm, 3 * cm, 3.4 * cm, 3 * cm, 3.6 * cm], alto=0.75 * cm))
s.append(Spacer(1, 6))
s.append(KeepTogether([
    Paragraph("Verificación con la corrección aplicada (punto 8.7)", H2),
    tabla([["Fecha / hora", vacio, "Resultado", "[  ] Cumple  [  ] No cumple"]],
          [3.5 * cm, 8.4 * cm, 3.5 * cm, 7.4 * cm], encabezado=False, alto=0.8 * cm),
    Spacer(1, 10),
    tabla([["Realizado por (nombre y firma)", "Revisado por responsable del área (QF o Esterilización) / Calidad"],
           [vacio, vacio]], [11.4 * cm, 11.4 * cm], alto=[0.7 * cm, 1.8 * cm]),
]))

# ----------------- Anexo B -----------------
s.append(Spacer(1, 12))
s.append(KeepTogether([
    Paragraph("Anexo B. Sensores del Monitor T/H (octubre 2026)", H1),
    tabla([["N°", "Nombre en pantalla", "IEEE (últimos 4)", "Perfil", "Exactitud declarada"],
           ["1", "Medicamentos 1", "FFFF", "MEDICAMENTOS", "±1 °C / ±5 % HR"],
           ["2", "Medicamentos 3", "D314", "MEDICAMENTOS", "±1 °C / ±5 % HR"],
           ["3", "Medicamentos 2", "00E4", "MEDICAMENTOS", "±1 °C / ±5 % HR"],
           ["", "", "", "", ""], ["", "", "", "", ""]], [1.2 * cm, 4.2 * cm, 3.2 * cm, 3.8 * cm, 4.6 * cm],
          alto=0.6 * cm),
    Spacer(1, 6),
    Paragraph("Nota: los sensores en uso reportan cuando el valor cambia (aprox. 0,5 °C o 5 % HR) o, si está "
              "estable, al menos cada 30 a 60 minutos. Por eso la comparación se hace sobre un periodo de 3 horas y "
              "no con una lectura aislada. Las filas en blanco son para sensores que se incorporen.", NOTA),
]))

doc = BaseDocTemplate(SALIDA, pagesize=letter, title="Instructivo de calibración de sensores – Monitor T/H",
                      author="Unidad de Innovación y Desarrollo – HGF")


def plantilla(nombre, tam):
    ancho, alto = tam
    marco = Frame(1.8 * cm, 1.8 * cm, ancho - 3.6 * cm, alto - 5.0 * cm, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    return PageTemplate(id=nombre, frames=[marco], pagesize=tam, onPage=encabezado_pagina)


doc.addPageTemplates([plantilla("vertical", letter), plantilla("horizontal", landscape(letter))])
doc.build(s)
print(SALIDA)
