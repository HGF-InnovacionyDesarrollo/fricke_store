"""Genera el instructivo de calibración de los sensores del Monitor T/H en Word,
sobre el formato institucional "Manual de Procedimientos Clínicos HGF Ver. 1".
Uso:  python docs/generar_instructivo_calibracion_word.py   (requiere python-docx)

Después de generarlo, abrirlo en Word y actualizar el índice (o dejar que este
script lo haga con Word si está instalado: ver actualizar_con_word()).
"""
import copy
import os
import re
import subprocess

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips

BASE = os.path.dirname(os.path.abspath(__file__))
PLANTILLA = os.path.join(BASE, "plantillas", "Formato_Manual_Procedimientos_Clinicos_HGF_v1.docx")
SALIDA = os.path.join(BASE, "Instructivo_calibracion_sensores_Monitor_TH.docx")

AZUL = "1F497D"     # colores de la plantilla
CELESTE = "D9E2F3"
NUM_VINETA = 18     # viñetas de la plantilla (Definiciones)
NUM_PROC = 24       # viñetas de los procedimientos (nivel 0 y 1)
CASILLA = "☐"

TITULO = "CALIBRACIÓN POR COMPARACIÓN DE LOS SENSORES DE TEMPERATURA Y HUMEDAD DEL MONITOR T/H"
TITULO_CORTO = "Calibración de sensores de temperatura y humedad (Monitor T/H)"
UNIDAD = "Unidad de Innovación y Desarrollo"

d = Document(PLANTILLA)
body = d.element.body


# ----------------------------------------------------------------- utilidades
def texto_runs(p, texto, tam=None, color=None, negrita=False):
    """Agrega runs a p; **así** va en negrita."""
    for i, trozo in enumerate(re.split(r"\*\*", texto)):
        if not trozo:
            continue
        r = p.add_run(trozo)
        r.bold = negrita or (i % 2 == 1) or None
        if tam:
            r.font.size = Pt(tam)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return p


def numerar(p, num_id, nivel=0):
    pPr = p._p.get_or_add_pPr()
    numPr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), str(nivel))
    nid = OxmlElement("w:numId")
    nid.set(qn("w:val"), str(num_id))
    numPr.append(ilvl)
    numPr.append(nid)
    pPr.append(numPr)


def sombrear(pPr_o_tcPr, color):
    """Fondo de un párrafo o celda (respeta el orden de elementos del esquema)."""
    for viejo in pPr_o_tcPr.findall(qn("w:shd")):
        pPr_o_tcPr.remove(viejo)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    siguiente = None
    for tag in ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark",
                "w:tabs", "w:suppressAutoHyphens", "w:spacing", "w:ind", "w:jc", "w:rPr"):
        siguiente = pPr_o_tcPr.find(qn(tag))
        if siguiente is not None:
            break
    if siguiente is not None:
        siguiente.addprevious(shd)
    else:
        pPr_o_tcPr.append(shd)


def h1(t):
    return d.add_paragraph(t, style="Heading 1")


def h2(t):
    return d.add_paragraph(t, style="Heading 2")


def parrafo(t, tam=None, color=None, despues=None, alinear=None):
    p = texto_runs(d.add_paragraph(), t, tam, color)
    if despues is not None:
        p.paragraph_format.space_after = Pt(despues)
    if alinear is not None:
        p.alignment = alinear
    return p


def nota(t):
    p = parrafo(t, tam=9, color="404040", despues=6)
    for r in p.runs:
        r.italic = True
    return p


def vinetas(items, num_id=NUM_VINETA, nivel=0):
    for t in items:
        p = texto_runs(d.add_paragraph(style="List Paragraph"), t)
        numerar(p, num_id, nivel)


def vacio():
    d.add_paragraph()


def bloque_procedimiento(objetivo, ejecuta, apoyo, supervisa, materiales, pasos, consideraciones):
    """Misma estructura que los procedimientos de la plantilla."""
    def etiqueta(t):
        p = d.add_paragraph(t, style="List Paragraph")
        numerar(p, NUM_PROC, 0)

    def separador():
        p = d.add_paragraph(style="List Paragraph")
        p.paragraph_format.left_indent = Twips(1440)

    for nombre, contenido in (("Objetivo", [objetivo]), ("Responsable de su ejecución", [ejecuta]),
                              ("Personal de apoyo (si aplica)", [apoyo]), ("Responsable de supervisar", [supervisa]),
                              ("Materiales:", materiales), ("Procedimiento:", pasos),
                              ("Consideraciones:", consideraciones)):
        etiqueta(nombre)
        vinetas(contenido, NUM_PROC, 1)
        if nombre != "Consideraciones:":
            separador()


def ajustar_celda(celda, ancho):
    tcPr = celda._tc.get_or_add_tcPr()
    tcW = tcPr.find(qn("w:tcW"))
    if tcW is None:
        tcW = OxmlElement("w:tcW")
        tcPr.insert(0, tcW)
    tcW.set(qn("w:w"), str(ancho))
    tcW.set(qn("w:type"), "dxa")
    if tcPr.find(qn("w:vAlign")) is None:
        va = OxmlElement("w:vAlign")
        va.set(qn("w:val"), "center")
        tcPr.append(va)


def escribir_celda(celda, t, tam=9, negrita=False, color=None, centrar=False, fondo=None):
    p = celda.paragraphs[0]
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if centrar else WD_ALIGN_PARAGRAPH.LEFT
    texto_runs(p, t, tam, color, negrita)
    if fondo:
        sombrear(celda._tc.get_or_add_tcPr(), fondo)


def tabla(filas, anchos, encabezado=True, etiquetas=(), alto=None, tam=9, centrar=(), junto=False):
    """filas: lista de listas de texto. etiquetas: columnas con fondo celeste
    (formularios). alto: alto mínimo de fila en twips. junto: no separarla del párrafo siguiente."""
    t = d.add_table(rows=len(filas), cols=len(anchos))
    t.style = d.styles["Table Grid"]
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblPr = t._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    tblW.set(qn("w:w"), str(sum(anchos)))
    tblW.set(qn("w:type"), "dxa")
    for gc, a in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), anchos):
        gc.set(qn("w:w"), str(a))
    for i, fila in enumerate(filas):
        row = t.rows[i]
        if alto:
            row.height = Twips(alto)
        for j, txt in enumerate(fila):
            c = row.cells[j]
            ajustar_celda(c, anchos[j])
            if encabezado and i == 0:
                escribir_celda(c, txt, tam, True, "FFFFFF", True, AZUL)
            elif j in etiquetas:
                escribir_celda(c, txt, tam, True, AZUL, False, CELESTE)
            else:
                escribir_celda(c, txt, tam, centrar=j in centrar)
    if encabezado:
        trPr = t.rows[0]._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:tblHeader"))
    if junto:
        for f in t.rows:
            for c in f.cells:
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next = True
    separacion = d.add_paragraph()  # párrafo mínimo entre la tabla y lo que sigue
    separacion.paragraph_format.space_after = Pt(0)
    separacion.add_run().font.size = Pt(5)
    return t


def titulo_anexo(t, nueva_pagina=False):
    """Como un título 1 de la plantilla, pero sin número ni entrada en el índice."""
    p = d.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    sombrear(pPr, AZUL)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.page_break_before = nueva_pagina
    texto_runs(p, t, 12, "FFFFFF", True)


def subtitulo(t, nueva_pagina=False):
    p = texto_runs(d.add_paragraph(), t, 11, AZUL, True)
    p.paragraph_format.page_break_before = nueva_pagina
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True


def reemplazar_texto_celda(celda, nuevo):
    """Cambia el texto de una celda de la plantilla conservando su formato."""
    parrafos = celda.paragraphs
    runs = [r for p in parrafos for r in p.runs]
    if runs:
        runs[0].text = nuevo
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    for p in parrafos[1:]:
        if not p.runs:
            p._p.getparent().remove(p._p)


# ----------------------------------------------------------------- portada
portada, firmas = d.tables[0], d.tables[1]
reemplazar_texto_celda(portada.cell(0, 1), TITULO)
reemplazar_texto_celda(portada.cell(1, 1), "Manual de Procedimientos")
reemplazar_texto_celda(portada.cell(2, 1), "1")

# Filas: 1-5 elaborado, 6-9 revisado, 10 aprobado. Se dejan 1 elaborador y 3 revisores.
filas_firmas = firmas.rows
personas = {
    1: ("", UNIDAD, "Octubre 2026"),
    6: ("", "Químico Farmacéutico, Unidad de Farmacia", ""),
    7: ("", "Enfermera Supervisora, Unidad de Esterilización", None),
    8: ("", "Unidad de Calidad y Seguridad del Paciente", None),
    10: ("", "Director", ""),
}
for i, (nombre, cargo, fecha) in personas.items():
    reemplazar_texto_celda(filas_firmas[i].cells[1], nombre)
    reemplazar_texto_celda(filas_firmas[i].cells[2], cargo)
    if fecha is not None:
        reemplazar_texto_celda(filas_firmas[i].cells[3], fecha)
for i in (9, 5, 4, 3, 2):  # de abajo hacia arriba (las celdas combinadas quedan en la primera fila)
    tr = filas_firmas[i]._tr
    tr.getparent().remove(tr)

# Encabezado de las páginas interiores
for celda in (c for t in d.sections[0].header.tables for f in t.rows for c in f.cells):
    for p in celda.paragraphs:
        for r in p.runs:
            if r.text == "Subdirección/Servicio/Unidad responsable":
                r.text = UNIDAD
            elif r.text == "Título del documento":
                r.text = TITULO_CORTO
            elif r.text.strip().startswith(": Enero 2019"):
                r.text = ": pendiente"

d.core_properties.title = TITULO_CORTO
d.core_properties.author = "Unidad de Innovación y Desarrollo – HGF"

# ----------------------------------------------------------------- cuerpo
# Se borra el contenido de ejemplo desde "Introducción" (se conserva la tabla de cambios).
inicio = next(p._p for p in d.paragraphs if p.style.name == "Heading 1")
tabla_cambios = copy.deepcopy(d.tables[-1]._tbl)
quitar, dentro = [], False
for el in body.iterchildren():
    if el is inicio:
        dentro = True
    if dentro and el.tag != qn("w:sectPr"):
        quitar.append(el)
for el in quitar:
    body.remove(el)

# 1 Introducción
h1("Introducción")
parrafo("El Monitor T/H registra en forma continua la temperatura y la humedad relativa de las áreas de "
        "almacenamiento de medicamentos y de material estéril del Hospital Dr. Gustavo Fricke, mediante sensores "
        "inalámbricos, y genera alarmas cuando los valores salen de los rangos definidos en los protocolos "
        "institucionales APF 1.5 y APE 1.4.")
parrafo("La Norma Técnica N° 147 del Instituto de Salud Pública exige que los equipos de medición se controlen y "
        "calibren según un programa establecido, con certificados trazables a patrones nacionales, y el protocolo "
        "APF 1.5 establece que los dispositivos de medición deben contar con calibración al menos una vez al año. "
        "Este documento describe la calibración por comparación de los sensores del Monitor T/H contra un "
        "instrumento de referencia calibrado, el cálculo de la corrección de cada sensor y su verificación.")

# 2 Objetivos
h1("Objetivos")
h2("Objetivo General")
parrafo("Determinar la diferencia entre la lectura de cada sensor del Monitor T/H y un instrumento de referencia "
        "calibrado, y aplicar la corrección correspondiente, de modo que las mediciones registradas sean trazables "
        "a los patrones nacionales.")
h2("Objetivos específicos")
for t in ["Determinar la corrección de temperatura y de humedad relativa de cada sensor respecto de un instrumento "
          "de referencia con calibración vigente.",
          "Evaluar si cada sensor cumple los criterios de aceptación definidos en este documento.",
          "Aplicar la corrección en el Monitor T/H y verificar su efecto.",
          "Dejar registros trazables de cada calibración para fines de auditoría."]:
    numerar(d.add_paragraph(t, style="List Paragraph"), 5)
vacio()

# 3 Alcance
h1("Alcance")
parrafo("Aplica a los sensores inalámbricos de temperatura y humedad relativa asociados al Monitor T/H instalados "
        "en áreas de almacenamiento a temperatura ambiente, según el perfil asignado a cada sensor:")
tabla([["Perfil", "Área", "Temperatura", "Humedad relativa", "Protocolo"],
       ["MEDICAMENTOS", "Almacenamiento de medicamentos", "15 a 25 °C (hasta 30 °C por periodos breves)",
        "No mayor a 60 %", "APF 1.5"],
       ["MATERIAL ESTÉRIL", "Almacenamiento de material estéril", "18 a 24 °C", "30 % a 50 %", "APE 1.4"]],
      [1700, 2100, 2200, 1500, 1100], centrar=(4,))
parrafo("No aplica a refrigeradores ni a equipos de cadena de frío.")

# 4 Definiciones
h1("Definiciones")
vinetas([
    "**Calibración por comparación:** determinación de la diferencia entre la lectura de un sensor y la de un "
    "instrumento de referencia, ubicados juntos en el mismo ambiente.",
    "**Instrumento de referencia:** termohigrómetro con certificado de calibración vigente emitido por un "
    "laboratorio acreditado, trazable a los patrones nacionales.",
    "**Corrección:** valor que se suma a la lectura de un sensor para igualarla a la referencia; es el promedio "
    "de las diferencias (referencia – sensor).",
    "**Dispersión:** diferencia máxima menos diferencia mínima de las comparaciones de un sensor; indica si el "
    "ensayo se hizo en condiciones estables.",
    "**Lectura fresca:** dato del sensor con 10 minutos o menos de antigüedad al momento de anotarlo (indicación "
    "«hace N m» en la pantalla del monitor; «ahora» = 0).",
    "**Paso de reporte:** cambio mínimo del valor que hace que un sensor envíe un dato nuevo (aproximadamente "
    "0,5 °C o 5 % HR en los sensores en uso).",
    "**Margen de guarda:** distancia que se deja respecto de un límite de alarma para considerar el error del "
    "sensor.",
    "**Trazabilidad metrológica:** propiedad de una medición de poder relacionarse con un patrón nacional mediante "
    "una cadena ininterrumpida de calibraciones documentadas.",
])
h2("Abreviaturas")
vinetas([
    "**APE 1.4:** protocolo institucional de almacenamiento y distribución de material estéril.",
    "**APF 1.5:** protocolo institucional de almacenamiento y conservación de medicamentos.",
    "**HR:** humedad relativa.",
    "**IEEE:** dirección única de cada sensor inalámbrico (se usan sus últimos 4 caracteres para identificarlo).",
    "**INN:** Instituto Nacional de Normalización.",
    "**ISP:** Instituto de Salud Pública de Chile.",
    "**LCPN-T:** Laboratorio Custodio del Patrón Nacional de Temperatura.",
    "**OMS:** Organización Mundial de la Salud.",
    "**QF:** químico farmacéutico.",
    "**SD:** tarjeta de memoria micro SD del monitor, donde se guardan los registros.",
], 19)
vacio()

# 5 Responsabilidades
h1("Responsabilidades")
tabla([["Rol", "Responsabilidad"],
       ["Químico farmacéutico (área de medicamentos), enfermera supervisora de Esterilización (área de material "
        "estéril) y Unidad de Calidad y Seguridad del Paciente",
        "Aprobar este documento, validar los criterios de aceptación y firmar el registro de su área."],
       ["Ejecutor (Unidad de Innovación y Desarrollo o personal capacitado)",
        "Realizar la comparación, completar el formulario (Anexo 1) y calcular las correcciones."],
       ["Unidad de Innovación y Desarrollo", "Cargar las correcciones en el Monitor T/H y verificar su aplicación."]],
      [3600, 5000], tam=10)

# 6 Exactitud y criterios
h1("Exactitud del sistema y criterios de aceptación")
h2("Fuentes de error")
parrafo("La calibración corrige la diferencia sistemática (desplazamiento) de cada sensor, pero no mejora su "
        "exactitud más allá de lo que el sensor permite. El monitor admite sensores de distintos modelos; para cada "
        "uno se consideran las siguientes fuentes de error (los valores de los sensores en uso a octubre de 2026 se "
        "indican como referencia y son el margen mínimo a considerar):")
tabla([["Fuente", "Sensores en uso (oct. 2026)", "Origen"],
       ["Exactitud declarada del sensor", "±1 °C y ±5 % HR", "Manual o ficha técnica del fabricante de cada modelo"],
       ["Paso de reporte: algunos sensores solo envían un dato nuevo cuando el valor cambia",
        "Aprox. 0,5 °C y 5 % HR", "Observado en los registros del monitor (columna «Hora de la lectura»)"],
       ["Incertidumbre del instrumento de referencia", "Según certificado", "Certificado de calibración"]],
      [3400, 2200, 3000])
parrafo("Con los sensores en uso, la exactitud esperable del sistema después de la corrección es del orden de "
        "**±0,5 a ±1 °C** y **±5 % HR**. Se recomienda que los responsables de cada área evalúen un **margen de "
        "guarda** en los límites de alarma (por ejemplo, considerar que una lectura de 29,5 °C podría corresponder a "
        "una temperatura real sobre 30 °C). Al incorporar un modelo nuevo, registrar su exactitud declarada en el "
        "Anexo 2.")
parrafo("**Material estéril:** sus rangos son estrechos (6 °C de temperatura y 20 puntos de humedad). Con los "
        "sensores en uso, el error de humedad (±5 % HR) equivale a un cuarto de la banda permitida: una lectura de "
        "46 % HR podría corresponder a más de 50 % real. Para esta área se recomienda considerar sensores de mayor "
        "exactitud o, al menos, un margen de guarda explícito definido por la enfermera supervisora de "
        "Esterilización.")
h2("Criterios de aceptación")
parrafo("Criterios propuestos, a validar con los responsables de cada área:").paragraph_format.keep_with_next = True
tabla([["Criterio", "Temperatura", "Humedad relativa", "Si no se cumple"],
       ["Dispersión de las diferencias", "Máximo 0,8 °C", "Máximo 6 % HR", "Repetir el ensayo con mejor estabilidad"],
       ["Magnitud de la corrección", "No mayor que la exactitud declarada (actuales: ±1,0 °C)",
        "No mayor que la exactitud declarada (actuales: ±5 % HR)", "Sensor fuera de especificación: reemplazar"],
       ["Verificación posterior (procedimiento 4)", "Máximo 0,5 °C", "Máximo 5 % HR",
        "Revisar la corrección cargada"]],
      [2300, 2100, 2100, 2100], junto=True)
nota("Los valores de dispersión y verificación consideran el paso de reporte de los sensores en uso; con sensores "
     "que reporten a intervalos fijos pueden exigirse valores menores.")

# 7 Procedimientos
h1("Procedimientos")
EJECUTOR = "Ejecutor: Unidad de Innovación y Desarrollo o personal capacitado."
SUPERVISOR = ("Químico farmacéutico (área de medicamentos) o enfermera supervisora de Esterilización (área de "
              "material estéril).")

h2("Preparación y estabilización")
bloque_procedimiento(
    "Dejar los sensores y el instrumento de referencia en condiciones estables y verificadas antes de comparar "
    "sus lecturas.",
    EJECUTOR,
    "Personal del área para el acceso a la sala.",
    SUPERVISOR,
    ["**Termohigrómetro de referencia** con **certificado de calibración vigente** emitido por un laboratorio "
     "acreditado por el INN. Se recomienda resolución de 0,1 °C y 1 % HR, e incertidumbre declarada no mayor a "
     "±0,3 °C y ±3 % HR.",
     "Monitor T/H con hora verificada y tarjeta micro SD funcionando (indicador «SD» en verde).",
     "Los sensores a calibrar, identificados por nombre y por los últimos 4 caracteres de su dirección IEEE "
     "(Anexo 2).",
     "Formulario de registro (Anexo 1) y lápiz."],
    ["Verificar que el certificado de la referencia esté vigente y anotar sus datos en el formulario.",
     "Verificar que la hora del Monitor T/H sea correcta. **Todas las horas se anotan con el reloj del monitor**, "
     "para que coincidan con su registro.",
     "Confirmar que los sensores aparecen en pantalla con datos recientes y sin aviso de «sin datos».",
     "Ubicar los sensores y la sonda de la referencia juntos, a la misma altura y a no más de 10 cm entre sí, sin "
     "tocarse.",
     "Esperar al menos **1 hora** sin anotar lecturas (**2 horas** si los sensores venían de otro ambiente). La "
     "humedad relativa tarda más que la temperatura en igualarse."],
    ["Ambiente estable, idealmente la misma sala donde se usarán los sensores, entre 18 y 26 °C.",
     "Sin sol directo, sin corrientes de aire, lejos de equipos que emitan calor, puertas y ductos de "
     "climatización.",
     "Sin certificado vigente de la referencia, la comparación no es válida para fines de auditoría."])

h2("Comparación de lecturas")
bloque_procedimiento(
    "Obtener lecturas simultáneas de la referencia y de cada sensor durante 3 horas.",
    EJECUTOR,
    "No aplica.",
    SUPERVISOR,
    ["Los mismos del procedimiento anterior, ya estabilizados.", "Formulario de registro (Anexo 1)."],
    ["**Cada 30 minutos** anotar en el formulario, con la hora del monitor, la lectura de la referencia "
     "(temperatura y humedad).",
     "Al mismo tiempo, anotar la **temperatura, la humedad y la antigüedad del dato** de cada sensor tal como las "
     "muestra la pantalla del monitor (la antigüedad es la indicación «hace N m»; «ahora» = 0).",
     "Continuar durante 3 horas, hasta obtener 6 a 7 lecturas."],
    ["No manipular los sensores ni la referencia durante el ensayo: el calor de la mano altera la lectura por "
     "varios minutos.",
     "Opcional y recomendado: repetir la comparación en distintos momentos del día (mañana, mediodía y tarde) para "
     "verificar que la diferencia se mantiene en distintas temperaturas.",
     "Si la referencia registra datos automáticamente (datalogger), conservar su archivo en lugar de las "
     "anotaciones manuales."])

h2("Cálculo de la corrección")
bloque_procedimiento(
    "Calcular la corrección de cada sensor y evaluar si cumple los criterios de aceptación.",
    EJECUTOR,
    "No aplica.",
    SUPERVISOR,
    ["Formulario de registro (Anexo 1) completo.",
     "Opcional: archivo de datos del monitor (datos/AAAA-MM-DD.csv en la tarjeta SD) del día del ensayo."],
    ["Usar los valores de cada sensor anotados en el formulario. Se pueden contrastar con el archivo de datos del "
     "monitor, en la fila más cercana a cada hora anotada.",
     "**Usar solo lecturas frescas:** considerar una comparación solo si el dato del sensor tenía **10 minutos o "
     "menos** de antigüedad (columna «Dato de hace» del formulario, o columna «Hora de la lectura» del archivo).",
     "Para cada lectura: **diferencia = valor de la referencia – valor del sensor**.",
     "**Corrección del sensor** = promedio de las diferencias (temperatura en °C con un decimal; humedad en % "
     "entero).",
     "**Dispersión** = diferencia máxima – diferencia mínima.",
     "Comparar con los criterios de aceptación (punto 6.2) y anotar el resultado en el formulario."],
    ["Se necesitan al menos **4 comparaciones válidas** por sensor; si faltan, extender el ensayo.",
     "Un dato con más de 10 minutos puede estar atrasado hasta el paso de reporte del sensor."])

h2("Aplicación y verificación de la corrección")
bloque_procedimiento(
    "Cargar la corrección de cada sensor en el monitor y confirmar que las lecturas corregidas coinciden con la "
    "referencia.",
    "Unidad de Innovación y Desarrollo.",
    "Ejecutor de la comparación.",
    SUPERVISOR,
    ["Monitor T/H, sensores e instrumento de referencia.", "Formulario de registro (Anexo 1)."],
    ["Cargar la corrección de cada sensor en la configuración del Monitor T/H. Desde ese momento la pantalla, las "
     "alarmas y el archivo de datos usan el valor corregido, y cada arranque del monitor deja en el registro de "
     "eventos las correcciones vigentes.",
     "Mantener los sensores junto a la referencia al menos 1 hora más y anotar 2 lecturas frescas.",
     "Verificar que la diferencia cumpla el criterio de verificación (punto 6.2) y registrarlo en el formulario.",
     "Firmar el formulario y entregarlo al responsable del área para su revisión."],
    ["Si la verificación no se cumple, revisar la corrección cargada y repetir la verificación."])
vacio()

# 8 Frecuencia
h1("Frecuencia")
vinetas(["Una vez al año (protocolo APF 1.5; se aplica la misma frecuencia a los sensores del área de material "
         "estéril).",
         "Al incorporar o reemplazar un sensor.",
         "Si el sensor sufre una caída o daño, o si se observan lecturas inconsistentes con otros instrumentos."])

# 9 Registros
h1("Registros")
vinetas(["Formulario del Anexo 1 completo y firmado.",
         "Copia del certificado de calibración vigente del instrumento de referencia.",
         "Copia de los archivos de datos y de eventos del monitor correspondientes al día del ensayo.",
         "Archivar junto a los registros del área por el plazo que defina la Unidad de Calidad y Seguridad del "
         "Paciente."])
vacio()

# 10 Anexos
h1("Anexos")
for t in ["Anexo 1: Formulario de registro de calibración por comparación (al final del documento).",
          "Anexo 2: Sensores del Monitor T/H (al final del documento)."]:
    numerar(d.add_paragraph(t, style="List Paragraph"), NUM_VINETA)

# 11 Referencias
h1("Referencias")
for t in ["Instituto de Salud Pública de Chile. Norma Técnica N° 147: Buenas prácticas de almacenamiento y "
          "distribución para droguerías y depósitos de productos farmacéuticos de uso humano.",
          "Instituto de Salud Pública de Chile. Resolución Exenta N° 1539: Guía de calificación de áreas de "
          "almacenamiento con temperatura controlada.",
          "Hospital Dr. Gustavo Fricke. Protocolo APF 1.5: Almacenamiento y conservación de medicamentos.",
          "Hospital Dr. Gustavo Fricke. Protocolo APE 1.4: Almacenamiento y distribución de material estéril.",
          "Ministerio de Salud de Chile (2018). Norma técnica sobre esterilización y desinfección de alto nivel y uso "
          "de artículos médicos estériles.",
          "Organización Mundial de la Salud. Informe Técnico N° 961, Anexo 9: Model guidance for the storage and "
          "transport of time- and temperature-sensitive pharmaceutical products; suplementos 6 (sistemas de "
          "monitoreo de temperatura y humedad) y 8 (mapeo térmico).",
          "Instituto Nacional de Normalización. Red Nacional de Metrología: patrón nacional de temperatura (LCPN-T, "
          "CESMEC) y de humedad (ENAER); NCh-ISO/IEC 17025 (acreditación de laboratorios de ensayo y "
          "calibración)."]:
    numerar(d.add_paragraph(t, style="List Paragraph"), NUM_VINETA)
vacio()

# 12 Tabla de cambios
h1("Tabla de cambios")
body.insert(len(body) - 1, tabla_cambios)
cambios = d.tables[-1]
reemplazar_texto_celda(cambios.cell(1, 2), "Octubre 2026")
for j, txt in ((0, "Elaboración del documento"), (1, UNIDAD)):
    if not cambios.cell(1, j).text:
        escribir_celda(cambios.cell(1, j), txt, 10, centrar=True)

# ----------------------------------------------------------------- anexos (hoja horizontal)
sec = d.add_section(WD_SECTION.NEW_PAGE)
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = d.sections[0].page_height, d.sections[0].page_width
sec.different_first_page_header_footer = False
sec.header.is_linked_to_previous = True
sec.footer.is_linked_to_previous = True
sec.left_margin = sec.right_margin = Twips(1134)

titulo_anexo("Anexo 1. Formulario de registro de calibración por comparación")
caja = CASILLA
tabla([["Fecha", "", "Hora de inicio", ""],
       ["Ejecutor", "", "Hora del monitor verificada", f"{caja} Sí"],
       ["Área", f"{caja} Medicamentos     {caja} Material estéril", "Sala / ubicación", ""]],
      [1800, 4600, 2600, 4600], encabezado=False, etiquetas=(0, 2), alto=290)
subtitulo("Instrumento de referencia")
tabla([["Marca / modelo", "", "N° de serie", ""],
       ["N° certificado", "", "Laboratorio", ""],
       ["Fecha de calibración", "", "Vigente hasta", ""],
       ["Incertidumbre T", "", "Incertidumbre HR", ""]],
      [2200, 4600, 2200, 4600], encabezado=False, etiquetas=(0, 2), alto=280)

subtitulo("Lecturas cada 30 minutos (hora del monitor)")
sens = "Sensor ______________"
cab1 = ["N°", "Hora", "Referencia", "", sens, "", "", sens, "", "", sens, "", ""]
cab2 = ["", "", "T (°C)", "HR (%)"] + ["T (°C)", "HR (%)", "Dato de hace (min)"] * 3
anchos = [600, 1100, 1000, 1000] + [1000, 1000, 1300] * 3
lect = tabla([cab1, cab2] + [[str(i)] + [""] * 12 for i in range(1, 11)], anchos, alto=290,
             centrar=(0,))
for j, txt in enumerate(cab2):  # segunda fila de encabezado con el mismo estilo
    escribir_celda(lect.cell(1, j), txt, 9, True, "FFFFFF", True, AZUL)
lect.rows[1]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
for a, b in ((0, 0), (1, 1)):
    lect.cell(0, a).merge(lect.cell(1, b))
for a, b in ((2, 3), (4, 6), (7, 9), (10, 12)):
    lect.cell(0, a).merge(lect.cell(0, b))
for celda, txt in ((lect.cell(0, 0), "N°"), (lect.cell(0, 1), "Hora"), (lect.cell(0, 2), "Referencia"),
                   (lect.cell(0, 4), sens), (lect.cell(0, 7), sens), (lect.cell(0, 10), sens)):
    for p in celda.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    escribir_celda(celda, txt, 9, True, "FFFFFF", True)
for i in range(2, 12):  # columnas de la referencia en celeste
    for j in (2, 3):
        sombrear(lect.cell(i, j)._tc.get_or_add_tcPr(), "EEF3FA")
nota("En «Sensor» escribir el nombre que muestra la pantalla. «Dato de hace»: la indicación «hace N m» del sensor "
     "en la pantalla («ahora» = 0). Una comparación es válida si el dato tiene 10 minutos o menos.")

subtitulo("Resultados por sensor", nueva_pagina=True)
tabla([["Sensor (nombre / IEEE)", "Corrección T (°C)", "Dispersión T", "Corrección HR (%)", "Dispersión HR",
        "Acepta"]] + [["", "", "", "", "", f"{caja} Sí   {caja} No"] for _ in range(4)],
      [3600, 2000, 1800, 2000, 1800, 2400], alto=420, centrar=(5,))
subtitulo("Verificación con la corrección aplicada (procedimiento 4)")
tabla([["Fecha / hora", "", "Resultado", f"{caja} Cumple     {caja} No cumple"]],
      [2000, 4800, 2000, 4800], encabezado=False, etiquetas=(0, 2), alto=460)
tabla([["Realizado por (nombre y firma)", "Revisado por responsable del área (QF o Esterilización) / Calidad"],
       ["", ""]], [6800, 6800], alto=420)
d.tables[-1].rows[1].height = Twips(1000)

# Anexo 2 en página aparte
titulo_anexo("Anexo 2. Sensores del Monitor T/H (octubre 2026)", nueva_pagina=True)
tabla([["N°", "Nombre en pantalla", "IEEE (últimos 4)", "Perfil", "Exactitud declarada", "Ubicación"],
       ["1", "Medicamentos 1", "FFFF", "MEDICAMENTOS", "±1 °C / ±5 % HR", ""],
       ["2", "Medicamentos 3", "D314", "MEDICAMENTOS", "±1 °C / ±5 % HR", ""],
       ["3", "Medicamentos 2", "00E4", "MEDICAMENTOS", "±1 °C / ±5 % HR", ""]] + [[""] * 6 for _ in range(4)],
      [700, 2600, 1800, 2300, 2400, 3800], alto=400, centrar=(0, 2))
nota("Los sensores en uso reportan cuando el valor cambia (aprox. 0,5 °C o 5 % HR) o, si está estable, al menos "
     "cada 30 a 60 minutos. Por eso la comparación se hace sobre un periodo de 3 horas y no con una lectura "
     "aislada. Las filas en blanco son para sensores que se incorporen.")

d.save(SALIDA)
print(SALIDA)


# ----------------------------------------------------------------- índice
def actualizar_con_word(ruta):
    """Actualiza el índice y los números de página con Word (si está instalado)."""
    ps = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          f"$d = $w.Documents.Open('{ruta}'); foreach ($t in $d.TablesOfContents) {{ $t.Update() }}; "
          f"$d.Fields.Update() | Out-Null; $d.Save(); "
          f"try {{ $d.Close() }} catch {{}}; try {{ $w.Quit() }} catch {{}}")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=180)
        print("índice actualizado con Word")
    except Exception as e:  # sin Word: actualizar el índice a mano (clic derecho > Actualizar campos)
        print("no se pudo actualizar el índice con Word:", e)


actualizar_con_word(SALIDA)
