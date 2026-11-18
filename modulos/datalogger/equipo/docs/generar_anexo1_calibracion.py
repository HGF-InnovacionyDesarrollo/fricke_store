"""Genera el Anexo 1 (formulario de calibración) del MTH-01 completado con los datos
del ensayo de octubre de 2026, a partir del instructivo en Word (que no se modifica).
Uso:  python docs/generar_anexo1_calibracion.py
"""
import copy
import os

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(BASE, "Instructivo_calibracion_sensores_Monitor_TH.docx")
SALIDA = os.path.join(BASE, "Anexo1_calibracion_MTH-01_2026-10.docx")

SENSORES = ["Medicamentos 1 (FFFF)", "Medicamentos 3 (D314)", "Medicamentos 2 (00E4)"]
# (fecha y hora del monitor, referencia, (T, hace) de cada sensor en el orden de SENSORES)
LECTURAS = [
    ("06/10 16:20", "22,9", [("22,8", "4"), ("22,8", "9"), ("22,8", "5")]),
    ("07/10 17:15", "23,2", [("23,4", "1"), ("23,7", "3"), ("23,6", "1")]),
    ("07/10 09:06", "21,6", [("21,4", "1"), ("21,5", "1"), ("21,1", "2")]),
    ("07/10 12:29", "22,6", [("22,4", "1"), ("22,5", "1"), ("22,6", "6")]),
    ("07/10 17:48", "23,7", [("22,9", "1"), ("23,5", "4"), ("23,1", "1")]),
    ("08/10 13:23", "22,6", [("22,4", "1"), ("22,6", "1"), ("22,8", "1")]),
    ("08/10 13:59", "22,8", [("22,5", "1"), ("22,8", "1"), ("22,8", "1")]),
    ("08/10 14:33", "22,8", [("22,5", "5"), ("22,8", "5"), ("22,8", "5")]),
    ("08/10 15:06", "23,0", [("23,0", "8"), ("22,8", "7"), ("22,8", "2")]),
    ("08/10 16:43", "23,2", [("23,0", "2"), ("23,3", "7"), ("22,8", "4")]),
]
NO_VALIDAS = {2, 5}  # N° de fila
# Resultados preliminares (8 comparaciones válidas): corrección, dispersión
RESULTADOS = [("+0,2", "0,3"), ("0,0", "0,3"), ("+0,1", "0,7")]

d = docx.Document(ORIGEN)
body = d.element.body


def texto_de(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


# ---- Quedarse solo con el Anexo 1 ----
hijos = list(body)
i_anexo1 = next(i for i, el in enumerate(hijos) if el.tag == qn("w:p") and "Anexo 1. Formulario" in texto_de(el))
i_anexo2 = next(i for i, el in enumerate(hijos) if el.tag == qn("w:p") and "Anexo 2. Sensores" in texto_de(el))
sect_final = body.find(qn("w:sectPr"))
# Encabezado y pie de la primera sección (la sección horizontal los heredaba)
sect_vertical = [el for el in hijos[:i_anexo1] if el.tag == qn("w:p") and el.find(".//" + qn("w:sectPr")) is not None][-1]
refs = [r for r in sect_vertical.find(".//" + qn("w:sectPr"))
        if r.tag in (qn("w:headerReference"), qn("w:footerReference")) and r.get(qn("w:type")) == "default"]
for r in reversed(refs):
    sect_final.insert(0, copy.deepcopy(r))
for el in hijos[:i_anexo1] + hijos[i_anexo2:]:
    if el is not sect_final:
        body.remove(el)
titulo = body[0]
pPr = titulo.find(qn("w:pPr"))
if pPr is not None and pPr.find(qn("w:pageBreakBefore")) is not None:
    pPr.remove(pPr.find(qn("w:pageBreakBefore")))


# ---- Utilidades ----
def escribir(tc, texto, tam=9, negrita=False, tachado=False, color=None):
    """Escribe en la primera línea de una celda (conserva el formato del párrafo)."""
    p = tc.find(qn("w:p"))
    for r in p.findall(qn("w:r")):
        p.remove(r)
    par = docx.text.paragraph.Paragraph(p, None)
    run = par.add_run(texto)
    run.font.size = Pt(tam)
    run.bold = negrita or None
    run.font.strike = tachado or None
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def celdas(tabla, fila):
    return tabla._tbl.findall(qn("w:tr"))[fila].findall(qn("w:tc"))


def parrafo_tras(el, texto, tam=8.5, cursiva=True):
    p = OxmlElement("w:p")
    el.addnext(p)
    par = docx.text.paragraph.Paragraph(p, None)
    par.paragraph_format.space_after = Pt(2)
    r = par.add_run(texto)
    r.font.size = Pt(tam)
    r.italic = cursiva
    r.font.color.rgb = RGBColor.from_string("404040")
    return p


t_general, t_ref, t_lect, t_res, t_verif = d.tables[0], d.tables[1], d.tables[2], d.tables[3], d.tables[4]

# ---- Datos generales ----
f0 = celdas(t_general, 0)
escribir(f0[1], "06, 07 y 08-10-2026")
escribir(f0[3], "16:20 (06-10)")
escribir(f0[5], "MTH-01")
escribir(f0[7], "98A316FFFE9BB2EC", tam=8)
f2 = celdas(t_general, 2)
escribir(f2[1], "☒ Medicamentos     ☐ Material estéril")

# ---- Instrumento de referencia ----
datos_ref = [("T&D (TANDD) RTR502B", "3282013F"), ("LT/9097", "Laboratorios Davis S.A."),
             ("08-09-2026", "08-09-2027 (calibración anual, APF 1.5)"), ("±0,1 °C", "No aplica (solo temperatura)")]
for fila, (a, b) in enumerate(datos_ref):
    c = celdas(t_ref, fila)
    escribir(c[1], a)
    escribir(c[3], b)

# ---- Lecturas ----
cab = celdas(t_lect, 0)  # N°, Hora, Referencia, Sensor, Sensor, Sensor (celdas combinadas)
for tc, nombre in zip(cab[3:6], SENSORES):
    escribir(tc, nombre, negrita=True, color="1F497D")
filas_tr = t_lect._tbl.findall(qn("w:tr"))
# Filas 11 y 12 vacías para las lecturas pendientes
for n in (11, 12):
    nueva = copy.deepcopy(filas_tr[-1])
    t_lect._tbl.append(nueva)
    tcs = nueva.findall(qn("w:tc"))
    escribir(tcs[0], str(n))
    for tc in tcs[1:]:
        escribir(tc, "")
filas_tr = t_lect._tbl.findall(qn("w:tr"))
for n, (hora, ref, sens) in enumerate(LECTURAS, start=1):
    tcs = filas_tr[n + 1].findall(qn("w:tc"))
    tachar = n in NO_VALIDAS
    valores = [hora, ref, "—"]
    for t, hace in sens:
        valores += [t, "—", hace]
    for tc, v in zip(tcs[1:], valores):
        escribir(tc, v, tam=8 if tc is tcs[1] else 9, tachado=tachar and v != "—")
    if tachar:
        escribir(tcs[0], f"{n}*", negrita=True, color="C00000")
for n in (11, 12):  # en las filas pendientes, HR no se mide
    tcs = filas_tr[n + 1].findall(qn("w:tc"))
    for k in (3, 5, 8, 11):
        escribir(tcs[k], "—")

# Observaciones bajo la nota de la tabla
nota = t_lect._tbl.getnext()
while not texto_de(nota).startswith("En «Sensor»"):
    nota = nota.getnext()
obs = parrafo_tras(nota, "Observaciones: calibración solo de temperatura; la humedad relativa queda pendiente "
                         "(sin referencia de HR). Lecturas registradas entre el 06 y el 08-10-2026 en distintos "
                         "momentos del día; las filas 11 y 12 están pendientes.", cursiva=False)
obs = parrafo_tras(obs, "* Fila 2 no válida: los valores anotados (23,4 / 23,7 / 23,6) no coinciden con el registro "
                        "del monitor a las 17:15 del 07-10 (22,9 / 23,5 / 23,1); lectura no simultánea.")
parrafo_tras(obs, "* Fila 5 no válida: temperatura de la sala en aumento al momento de la lectura (los sensores "
                  "subieron 0,5 °C entre las 17:51 y las 17:54, según el registro del monitor).")

# Filas de lecturas más bajas para que las 12 quepan en la primera hoja
for tr in t_lect._tbl.findall(qn("w:tr"))[2:]:
    alto = tr.find(qn("w:trPr")).find(qn("w:trHeight"))
    alto.set(qn("w:val"), "250")
# Resultados en la misma hoja que las observaciones
for el in body:
    if el.tag == qn("w:p") and texto_de(el).startswith("Resultados por sensor"):
        ppr = el.find(qn("w:pPr"))
        if ppr is not None and ppr.find(qn("w:pageBreakBefore")) is not None:
            ppr.remove(ppr.find(qn("w:pageBreakBefore")))

# ---- Resultados (preliminares) ----
for fila, (nombre, (corr, disp)) in enumerate(zip(SENSORES, RESULTADOS), start=1):
    tcs = celdas(t_res, fila)
    escribir(tcs[0], nombre)
    escribir(tcs[1], corr)
    escribir(tcs[2], disp)
    escribir(tcs[3], "No medido")
    escribir(tcs[4], "No medido")
parrafo_tras(t_res._tbl, "Resultados preliminares con 8 comparaciones válidas por sensor (filas 2 y 5 excluidas); "
                         "se recalculan al completar las filas 11 y 12. Criterios (punto 6.2): dispersión máx. 0,8 °C; "
                         "corrección no mayor que la exactitud declarada (±1,0 °C).")

# Fila vacía sobrante de resultados (solo hay 3 sensores)
filas_res = t_res._tbl.findall(qn("w:tr"))
if len(filas_res) > 4 and not texto_de(filas_res[4]).replace("☐", "").replace("Sí", "").replace("No", "").strip():
    t_res._tbl.remove(filas_res[4])
# Filas de resultados más bajas para que las firmas quepan en la segunda hoja
for tr in t_res._tbl.findall(qn("w:tr"))[1:]:
    tr.find(qn("w:trPr")).find(qn("w:trHeight")).set(qn("w:val"), "320")
# Firmas: más bajas y sin partirse entre páginas
t_firmas = d.tables[6]
for tr in t_firmas._tbl.findall(qn("w:tr")):
    trPr = tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    for p in tr.iter(qn("w:p")):
        docx.text.paragraph.Paragraph(p, None).paragraph_format.keep_with_next = True
alto = t_firmas._tbl.findall(qn("w:tr"))[1].find(qn("w:trPr")).find(qn("w:trHeight"))
alto.set(qn("w:val"), "750")

# ---- Verificación: nombres de los sensores ----
for tc, nombre in zip(celdas(t_verif, 0)[3:6], SENSORES):
    escribir(tc, nombre, negrita=True, color="1F497D")

# Párrafos vacíos entre tablas: mínimos (con letra de 12 pt ocupaban media línea cada uno)
for el in body:
    if el.tag == qn("w:p") and not texto_de(el).strip():
        par = docx.text.paragraph.Paragraph(el, None)
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.space_before = Pt(0)
        rpr = el.get_or_add_pPr().get_or_add_rPr() if hasattr(el.get_or_add_pPr(), "get_or_add_rPr") else None
        if rpr is not None:
            sz = OxmlElement("w:sz")
            sz.set(qn("w:val"), "8")
            rpr.append(sz)
        for r in par.runs:
            r.font.size = Pt(4)

d.core_properties.title = "Anexo 1 – Calibración MTH-01 (octubre 2026)"
d.save(SALIDA)
print(SALIDA)
