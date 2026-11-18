"""Caja para el Monitor T/H (montaje en pared, pantalla vertical).

Se ejecuta dentro de Blender (Scripting > Run Script, o exec(open(ruta).read())).
Genera dos piezas para imprimir, más modelos de referencia de los componentes
(colección "Referencia", no se exportan):

  - Cuerpo: fondo + 4 paredes, abierto por delante. Se atornilla a la pared.
  - Tapa:   frente con la ventana de la pantalla, rejilla del buzzer y el
            módulo SD. Se atornilla al cuerpo con 4 tornillos M3.
  - Boton:  botón impreso que empuja el pulsador desde el costado derecho.

Unidades: 1 unidad de Blender = 1 mm (los STL quedan en mm).

Ejes (mirando la caja de frente, colgada en la pared):
  X: de izquierda a derecha | Z: de abajo hacia arriba
  Y: profundidad; y=0 es la cara interior de la tapa, y=FONDO la cara
     interior de la pared del fondo. La tapa queda en y<0.
Todas las posiciones de componentes son "interiores": x=0 es la cara interior
de la pared izquierda y z=0 la del piso.

Medidas estimadas de fotos con regla (±1 mm): conviene imprimir primero solo
la tapa y comprobar la ventana y los agujeros de la pantalla.
"""

import bpy
import math
import os

# ======================= Medidas generales =======================
ANCHO = 76.0      # interior, X
ALTO = 100.0      # interior, Z
FONDO = 40.0      # interior, Y
PARED = 2.5       # espesor de paredes, fondo y tapa

# Torres de las esquinas para los tornillos de la tapa (M3 autorroscante)
TORRE = 7.0
TORRE_AGUJERO = 2.8     # diámetro guía para M3 autorroscante
TORRE_PROF = 14.0
TAPA_AGUJERO = 3.4      # paso del M3 en la tapa

# ======================= Pantalla 1,9" (en la tapa) =======================
PANT_PCB = (29.0, 62.0)             # ancho, alto de la placa
PANT_X = ANCHO / 2                  # centro de la placa
PANT_Z_ARRIBA = 92.0                # borde superior de la placa (lado de los pines)
PANT_VIDRIO = (25.8, 49.7)          # vidrio del panel
PANT_VIDRIO_DESDE_ARRIBA = 5.8      # del borde superior de la placa al vidrio
PANT_ACTIVA = (22.7, 42.7)          # área visible
PANT_ACTIVA_DESDE_ARRIBA = 7.4      # del borde superior de la placa al área visible
PANT_VENTANA_MARGEN = 0.5           # la ventana es el área visible + este margen por lado
PANT_AGUJEROS = (25.0, 57.5)        # separación entre centros (ancho, alto)
PANT_BOLSILLO = 0.8                 # rebaje en la tapa donde se asienta el vidrio
# Del frente del vidrio a la cara delantera de la placa azul. MEDIR: define la
# altura de los postes para que el vidrio quede apoyado contra la tapa.
PANT_VIDRIO_A_PCB = 2.5                 # medido
PANT_POSTE_ALTO = max(0.0, PANT_VIDRIO_A_PCB - PANT_BOLSILLO)  # desde la cara interior de la tapa
PANT_POSTE_D = 4.5
PANT_POSTE_AGUJERO = 1.6            # guía para M2 autorroscante

# ======================= Buzzer (en la tapa) =======================
BUZZER_X, BUZZER_Z = ANCHO / 2, 14.0
BUZZER_D = 12.0
BUZZER_ANILLO_ALTO = 5.0

# ======================= Módulo SD (en la tapa, contra la pared izquierda) ====
SD_MODULO = (20.0, 17.0)            # largo (X, con el lector), alto (Z)
SD_Z = 72.0                         # borde inferior del módulo
SD_RANURA = (14.0, 5.5)             # alto (Z) y profundidad (Y) de la ranura en la pared
SD_REBORDE = 2.0                    # reborde exterior que protege la tarjeta

# ======================= Pulsador (pared derecha) =======================
BOTON_Z, BOTON_Y = 61.0, 10.0
BOTON_AGUJERO = 9.0                 # agujero en la pared
BOTON_TALLO = 8.4                   # diámetro del botón impreso
BOTON_PESTANA = 11.5                # pestaña interior que evita que se salga
BOTON_ARO = 14.0                    # aro exterior (el botón queda 1,5 mm hundido)
PULSADOR = (12.0, 7.3)              # TS0719: lado, alto

# ======================= ESP32-C6 (fondo, izquierda) =======================
ESP_X = 8.0                         # borde izquierdo de la placa
ESP_PCB = (25.4, 55.0)              # ancho, largo de la placa (sin antena ni USB)
ESP_Z_USB = 3.0                     # boca de los USB-C (placa vertical, USB abajo)
ESP_USB_SOBRESALE = 2.0
ESP_ANTENA = 7.5
ESP_CINTA = 3.0                     # cinta doble contacto entre el módulo y el fondo
USB_RANURA = (26.0, 8.0)            # ancho (X) y profundidad (Y) de la ranura en el piso

# ======================= Placa de conexiones 4x4 y RTC (fondo, derecha) ====
PLACA = (40.0, 40.0)
PLACA_X, PLACA_Z = 35.0, 52.0       # esquina inferior izquierda
PLACA_POSTE_ALTO = 5.0
PLACA_POSTE_INSET = 2.5
RTC = (38.0, 22.0)
RTC_X, RTC_Z = 36.0, 20.0

# ======================= Montaje en pared (ojos de cerradura) ==============
OJOS = [(20.0, 80.0), (55.0, 5.0)]  # (x, z) del agujero grande
OJO_CABEZA = 8.5
OJO_RANURA = 4.5
OJO_LARGO = 8.0

# ======================= Ventilación =======================
VENT_Z = [9.0, 14.0, 19.0, 85.0, 90.0]
VENT_Y = (15.0, 30.0)
VENT_ALTO = 2.0

CARPETA_STL = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals()
                           else r"C:\Users\usuariohgf\Documents\Desarrollos\Monitor_TH\caja", "stl")


# ======================= Utilidades =======================

def _coleccion(nombre):
    col = bpy.data.collections.get(nombre)
    if col is None:
        col = bpy.data.collections.new(nombre)
        bpy.context.scene.collection.children.link(col)
    return col


def caja(nombre, x0, x1, y0, y1, z0, z1, col="Trabajo"):
    """Prisma entre dos esquinas (coordenadas interiores)."""
    xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    v = [(x, y, z) for x in xs for y in ys for z in zs]
    caras = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(v, [], caras)
    malla.update()
    obj = bpy.data.objects.new(nombre, malla)
    _coleccion(col).objects.link(obj)
    return obj


def cilindro(nombre, eje, centro, d, desde, hasta, seg=48, col="Trabajo"):
    """Cilindro de diámetro d a lo largo de 'x', 'y' o 'z'. centro = coordenadas
    de los otros dos ejes (en orden x,y,z omitiendo el eje)."""
    r = d / 2
    v = []
    for a in (desde, hasta):
        for i in range(seg):
            t = 2 * math.pi * i / seg
            p, q = centro[0] + r * math.cos(t), centro[1] + r * math.sin(t)
            v.append((a, p, q) if eje == "x" else (p, a, q) if eje == "y" else (p, q, a))
    caras = [tuple(range(seg))[::-1], tuple(range(seg, 2 * seg))]
    caras += [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(v, [], caras)
    malla.update()
    # normales hacia afuera
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(malla)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(nombre, malla)
    _coleccion(col).objects.link(obj)
    return obj


def prisma(nombre, puntos_xy, z0, z1, col="Trabajo"):
    """Prisma de base poligonal (puntos X,Y en orden antihorario) entre z0 y z1."""
    n = len(puntos_xy)
    v = [(x, y, z0) for x, y in puntos_xy] + [(x, y, z1) for x, y in puntos_xy]
    caras = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    caras += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(v, [], caras)
    malla.update()
    obj = bpy.data.objects.new(nombre, malla)
    _coleccion(col).objects.link(obj)
    return obj


def tronco(nombre, cx, cz, ax0, az0, y0, ax1, az1, y1, col="Trabajo"):
    """Tronco de pirámide rectangular a lo largo de Y: semiancho ax/az en y0 y en y1."""
    v = [(cx + sx * ax, y, cz + sz * az)
         for (ax, az, y) in ((ax0, az0, y0), (ax1, az1, y1))
         for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    caras = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata(v, [], caras)
    malla.update()
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(malla)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(nombre, malla)
    _coleccion(col).objects.link(obj)
    return obj


def _booleana(obj, otro, op):
    mod = obj.modifiers.new("b", "BOOLEAN")
    mod.operation = op
    mod.solver = "EXACT"
    mod.object = otro
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(otro, do_unlink=True)


def restar(obj, *cortes):
    for c in cortes:
        _booleana(obj, c, "DIFFERENCE")


def unir(obj, *piezas):
    for p in piezas:
        _booleana(obj, p, "UNION")


def material(nombre, rgba):
    m = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    m.diffuse_color = rgba
    return m


def pintar(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


# ======================= Limpieza y unidades =======================

def preparar_escena():
    esc = bpy.context.scene
    esc.unit_settings.system = "METRIC"
    esc.unit_settings.scale_length = 0.001
    esc.unit_settings.length_unit = "MILLIMETERS"
    for nombre in ("Trabajo", "Piezas", "Referencia"):
        col = bpy.data.collections.get(nombre)
        if col:
            for o in list(col.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(col)
    for obj in list(bpy.data.objects):
        if obj.type == "MESH" and obj.name.startswith(("Cube", "Cuerpo", "Tapa", "Boton")):
            bpy.data.objects.remove(obj, do_unlink=True)


def mover_a(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    _coleccion(col).objects.link(obj)


# ======================= Cuerpo =======================

def construir_cuerpo():
    W, H, D, t = ANCHO, ALTO, FONDO, PARED
    cuerpo = caja("Cuerpo", -t, W + t, 0, D + t, -t, H + t)
    restar(cuerpo, caja("hueco", 0, W, -1, D, 0, H))

    # Torres de las esquinas con agujero guía para M3
    torres, agujeros = [], []
    for x0 in (0, W - TORRE):
        for z0 in (0, H - TORRE):
            torres.append(caja("torre", x0, x0 + TORRE, 0, D, z0, z0 + TORRE))
            agujeros.append(cilindro("guia", "y", (x0 + TORRE / 2, z0 + TORRE / 2), TORRE_AGUJERO, -1, TORRE_PROF))
    unir(cuerpo, *torres)
    restar(cuerpo, *agujeros)

    # Ranura de la SD en la pared izquierda (abierta hacia la tapa) con reborde exterior
    zc = SD_Z + SD_MODULO[1] / 2
    rz = SD_RANURA[0] / 2
    reborde = caja("reborde", -t - SD_REBORDE, -t + 0.01, 0, SD_RANURA[1] + 2, zc - rz - 2, zc + rz + 2)
    unir(cuerpo, reborde)
    restar(cuerpo, caja("ranura_sd", -t - SD_REBORDE - 1, 0.5, -1, SD_RANURA[1], zc - rz, zc + rz))

    # Pulsador: agujero, aro exterior y soporte interior en U (abierto arriba)
    aro = cilindro("aro", "x", (BOTON_Y, BOTON_Z), BOTON_ARO, W + t - 0.01, W + t + 1.5)
    unir(cuerpo, aro)
    restar(cuerpo, cilindro("agujero_boton", "x", (BOTON_Y, BOTON_Z), BOTON_AGUJERO, W - 1, W + t + 2))
    lado = PULSADOR[0] + 0.4
    pestana = 2.0
    fondo_pulsador = W - pestana - 0.2 - PULSADOR[1]          # cara trasera del pulsador
    soporte = caja("soporte", fondo_pulsador - 2, W, BOTON_Y - lado / 2 - 1.6, BOTON_Y + lado / 2 + 1.6,
                   BOTON_Z - lado / 2 - 1.6, BOTON_Z + lado / 2 + 2)
    # Cuña a 45° bajo el soporte (hacia el fondo): la caja se imprime apoyada en
    # el fondo y el soporte quedaría en el aire sin ella.
    y_sop = BOTON_Y + lado / 2 + 1.6
    ancho_sop = W - (fondo_pulsador - 2)
    cuna = prisma("cuna", [(fondo_pulsador - 2, y_sop - 0.01), (W, y_sop - 0.01), (W, y_sop + ancho_sop)],
                  BOTON_Z - lado / 2 - 1.6, BOTON_Z + lado / 2 + 2)
    unir(cuerpo, soporte, cuna)
    restar(cuerpo,
           caja("hueco_pulsador", fondo_pulsador, W - 0.01, BOTON_Y - lado / 2, BOTON_Y + lado / 2,
                BOTON_Z - lado / 2, BOTON_Z + lado / 2 + 10),
           caja("paso_cables", fondo_pulsador - 3, fondo_pulsador + 1, BOTON_Y - 3, BOTON_Y + 3,
                BOTON_Z - 3, BOTON_Z + lado / 2 + 10))

    # USB-C por el piso, bajo el ESP32
    ux = ESP_X + ESP_PCB[0] / 2
    pcb_y = D - ESP_CINTA - 3.2 - 1.6            # cara de los pines de la placa
    usb_y = pcb_y + 1.6 + 1.6                     # eje de los conectores (lado componentes)
    restar(cuerpo, caja("ranura_usb", ux - USB_RANURA[0] / 2, ux + USB_RANURA[0] / 2,
                        usb_y - USB_RANURA[1] / 2, usb_y + USB_RANURA[1] / 2, -t - 1, 0.5))

    # Marco guía para la cinta del módulo del ESP32 (módulo de 18 x 25,5 mm)
    mx0 = ESP_X + (ESP_PCB[0] - 18) / 2 - 0.5
    mz1 = ESP_Z_USB + ESP_USB_SOBRESALE + ESP_PCB[1] + ESP_ANTENA + 0.5
    marco = caja("marco_esp", mx0 - 1, mx0 + 19 + 1, D - 1.5, D + 0.01, mz1 - 26.5, mz1 + 1)
    restar(marco, caja("hueco_marco", mx0, mx0 + 19, D - 2, D + 1, mz1 - 25.5, mz1))
    unir(cuerpo, marco)

    # Postes M2 para la placa de conexiones 4x4
    postes, guias = [], []
    for dx in (PLACA_POSTE_INSET, PLACA[0] - PLACA_POSTE_INSET):
        for dz in (PLACA_POSTE_INSET, PLACA[1] - PLACA_POSTE_INSET):
            c = (PLACA_X + dx, PLACA_Z + dz)
            postes.append(cilindro("poste", "y", c, 5.0, D - PLACA_POSTE_ALTO, D + 0.01))
            guias.append(cilindro("guia_poste", "y", c, 1.8, D - PLACA_POSTE_ALTO - 1, D - 0.5))
    unir(cuerpo, *postes)
    restar(cuerpo, *guias)

    # Esquineros para el RTC (se fija con cinta doble contacto)
    esquineros = []
    for (x, z, sx, sz) in ((RTC_X, RTC_Z, -1, -1), (RTC_X + RTC[0], RTC_Z, 1, -1),
                           (RTC_X, RTC_Z + RTC[1], -1, 1), (RTC_X + RTC[0], RTC_Z + RTC[1], 1, 1)):
        x0, z0 = x + sx * 0.3, z + sz * 0.3
        esquineros.append(caja("esq_a", x0, x0 + sx * 1.2, D - 3, D + 0.01, z0 + sz * 1.2, z0 - sz * 5))
        esquineros.append(caja("esq_b", x0, x0 - sx * 5, D - 3, D + 0.01, z0, z0 + sz * 1.2))
    unir(cuerpo, *esquineros)

    # Ojos de cerradura para colgar (el tornillo entra por el agujero grande y sube)
    for (x, z) in OJOS:
        unir(cuerpo, caja("pad_ojo", x - 7, x + 7, D - 3, D + 0.01, z - 6, z + OJO_LARGO + 6))
        restar(cuerpo,
               cilindro("ojo_cabeza", "y", (x, z), OJO_CABEZA, D - 3.5, D + t + 1),
               caja("ojo_ranura", x - OJO_RANURA / 2, x + OJO_RANURA / 2, D - 0.5, D + t + 1, z, z + OJO_LARGO),
               caja("ojo_canal", x - OJO_CABEZA / 2, x + OJO_CABEZA / 2, D - 3.5, D - 1.0, z, z + OJO_LARGO),
               cilindro("ojo_fin", "y", (x, z + OJO_LARGO), OJO_CABEZA, D - 3.5, D - 1.0),
               cilindro("ojo_fin2", "y", (x, z + OJO_LARGO), OJO_RANURA, D - 1.1, D + t + 1))

    # Ventilación en ambos costados
    cortes = []
    for z in VENT_Z:
        for x0, x1 in ((-t - 1, 1), (W - 1, W + t + 1)):
            cortes.append(caja("vent", x0, x1, VENT_Y[0], VENT_Y[1], z, z + VENT_ALTO))
    restar(cuerpo, *cortes)

    mover_a(cuerpo, "Piezas")
    return cuerpo


# ======================= Tapa =======================

def construir_tapa():
    W, H, t = ANCHO, ALTO, PARED
    tapa = caja("Tapa", -t, W + t, -t, 0, -t, H + t)

    # Ventana de la pantalla con bisel a 45° en todo el grosor que queda delante
    # del vidrio: el marco no tapa los bordes aunque se mire de lado.
    act_arriba = PANT_Z_ARRIBA - PANT_ACTIVA_DESDE_ARRIBA
    vx = PANT_ACTIVA[0] / 2 + PANT_VENTANA_MARGEN
    v0, v1 = act_arriba - PANT_ACTIVA[1] - PANT_VENTANA_MARGEN, act_arriba + PANT_VENTANA_MARGEN
    vz = (v1 - v0) / 2
    extra = (t - PANT_BOLSILLO) + 0.5          # ensanche a 45° hasta pasar la cara frontal
    restar(tapa,
           caja("ventana", PANT_X - vx, PANT_X + vx, -t - 1, 1, v0, v1),
           tronco("bisel", PANT_X, (v0 + v1) / 2, vx, vz, -PANT_BOLSILLO + 0.01,
                  vx + extra, vz + extra, -t - 0.5))

    # Rebaje para el vidrio
    vid_arriba = PANT_Z_ARRIBA - PANT_VIDRIO_DESDE_ARRIBA
    gx = PANT_VIDRIO[0] / 2 + 0.3
    restar(tapa, caja("bolsillo", PANT_X - gx, PANT_X + gx, -PANT_BOLSILLO, 1,
                      vid_arriba - PANT_VIDRIO[1] - 0.3, vid_arriba + 0.3))

    # Postes M2 de la pantalla
    zc = PANT_Z_ARRIBA - PANT_PCB[1] / 2
    postes, guias = [], []
    for dx in (-PANT_AGUJEROS[0] / 2, PANT_AGUJEROS[0] / 2):
        for dz in (-PANT_AGUJEROS[1] / 2, PANT_AGUJEROS[1] / 2):
            postes.append(cilindro("poste_pant", "y", (PANT_X + dx, zc + dz), PANT_POSTE_D, -0.01, PANT_POSTE_ALTO))
            guias.append(cilindro("guia_pant", "y", (PANT_X + dx, zc + dz), PANT_POSTE_AGUJERO, -1.5, PANT_POSTE_ALTO + 1))
    unir(tapa, *postes)
    restar(tapa, *guias)

    # Rejilla y anillo del buzzer
    agujeros = [cilindro("rej", "y", (BUZZER_X, BUZZER_Z), 1.8, -t - 1, 1)]
    for i in range(6):
        a = math.pi / 3 * i
        agujeros.append(cilindro("rej", "y", (BUZZER_X + 3.5 * math.cos(a), BUZZER_Z + 3.5 * math.sin(a)),
                                 1.8, -t - 1, 1))
    restar(tapa, *agujeros)
    anillo = cilindro("anillo", "y", (BUZZER_X, BUZZER_Z), BUZZER_D + 2.8, -0.01, BUZZER_ANILLO_ALTO)
    restar(anillo, cilindro("hueco_anillo", "y", (BUZZER_X, BUZZER_Z), BUZZER_D + 0.4, -1, BUZZER_ANILLO_ALTO + 1))
    unir(tapa, anillo)

    # Guías del módulo SD (el lector toca la pared izquierda)
    z0, z1 = SD_Z, SD_Z + SD_MODULO[1]
    unir(tapa,
         caja("guia_sd_abajo", 0.3, 12, -0.01, 3, z0 - 1.5, z0 - 0.3),
         caja("guia_sd_arriba", 0.3, 12, -0.01, 3, z1 + 0.3, z1 + 1.5))

    # Agujeros de los tornillos M3
    agujeros = []
    for x in (TORRE / 2, W - TORRE / 2):
        for z in (TORRE / 2, H - TORRE / 2):
            agujeros.append(cilindro("m3", "y", (x, z), TAPA_AGUJERO, -t - 1, 1))
    restar(tapa, *agujeros)

    mover_a(tapa, "Piezas")
    return tapa


# ======================= Botón =======================

def construir_boton():
    W, t = ANCHO, PARED
    tallo = cilindro("Boton", "x", (BOTON_Y, BOTON_Z), BOTON_TALLO, W - 0.01, W + t)
    unir(tallo, cilindro("pestana", "x", (BOTON_Y, BOTON_Z), BOTON_PESTANA, W - 2.0, W))
    mover_a(tallo, "Piezas")
    return tallo


# ======================= Referencias (no se imprimen) =======================

def referencias():
    D = FONDO
    gris, azul, negro, verde, dorado = (material("ref_gris", (0.6, 0.6, 0.6, 1)), material("ref_azul", (0.1, 0.3, 0.8, 1)),
                                        material("ref_negro", (0.05, 0.05, 0.05, 1)), material("ref_verde", (0.1, 0.6, 0.2, 1)),
                                        material("ref_dorado", (0.8, 0.6, 0.1, 1)))
    zc = PANT_Z_ARRIBA - PANT_PCB[1] / 2
    pcb_y = -PANT_BOLSILLO + PANT_VIDRIO_A_PCB
    pcb_pant = caja("Ref_pantalla_pcb", PANT_X - 14.5, PANT_X + 14.5, pcb_y, pcb_y + 1.6, zc - 31, zc + 31,
                    col="Referencia")
    pintar(pcb_pant, azul)
    vid_arriba = PANT_Z_ARRIBA - PANT_VIDRIO_DESDE_ARRIBA
    vidrio = caja("Ref_pantalla_vidrio", PANT_X - 12.9, PANT_X + 12.9, -PANT_BOLSILLO, pcb_y, vid_arriba - 49.7,
                  vid_arriba,
                  col="Referencia")
    pintar(vidrio, negro)
    pines = caja("Ref_pantalla_dupont", PANT_X - 10, PANT_X + 10, pcb_y + 1.6, pcb_y + 20, PANT_Z_ARRIBA - 4, PANT_Z_ARRIBA - 1.5,
                 col="Referencia")
    pintar(pines, gris)

    pcb_y = D - ESP_CINTA - 3.2 - 1.6
    z0 = ESP_Z_USB + ESP_USB_SOBRESALE
    esp = caja("Ref_esp32", ESP_X, ESP_X + ESP_PCB[0], pcb_y, pcb_y + 1.6, z0, z0 + ESP_PCB[1], col="Referencia")
    pintar(esp, negro)
    modulo = caja("Ref_esp32_modulo", ESP_X + 3.7, ESP_X + 21.7, pcb_y + 1.6, pcb_y + 4.8,
                  z0 + ESP_PCB[1] + ESP_ANTENA - 25.5, z0 + ESP_PCB[1] + ESP_ANTENA, col="Referencia")
    pintar(modulo, gris)
    usb = caja("Ref_esp32_usb", ESP_X + 2, ESP_X + 23.4, pcb_y + 1.6, pcb_y + 4.8, ESP_Z_USB, ESP_Z_USB + 7,
               col="Referencia")
    pintar(usb, gris)
    dupont = caja("Ref_esp32_dupont", ESP_X, ESP_X + ESP_PCB[0], pcb_y - 22, pcb_y, z0 + 2, z0 + ESP_PCB[1] - 2,
                  col="Referencia")
    pintar(dupont, gris)

    placa = caja("Ref_placa_4x4", PLACA_X, PLACA_X + PLACA[0], D - PLACA_POSTE_ALTO - 1.6, D - PLACA_POSTE_ALTO,
                 PLACA_Z, PLACA_Z + PLACA[1], col="Referencia")
    pintar(placa, verde)
    rtc = caja("Ref_rtc", RTC_X, RTC_X + RTC[0], D - 14, D, RTC_Z, RTC_Z + RTC[1], col="Referencia")
    pintar(rtc, azul)
    sd = caja("Ref_sd", 0.3, 0.3 + SD_MODULO[0], 0, 3.6, SD_Z, SD_Z + SD_MODULO[1], col="Referencia")
    pintar(sd, azul)
    tarjeta = caja("Ref_tarjeta_sd", -7.2, 3, 1.7, 2.7, SD_Z + 3, SD_Z + 14, col="Referencia")
    pintar(tarjeta, dorado)
    buz = cilindro("Ref_buzzer", "y", (BUZZER_X, BUZZER_Z), BUZZER_D, 0, 8.5, col="Referencia")
    pintar(buz, negro)
    lado = PULSADOR[0]
    fondo_pulsador = ANCHO - 2.2 - PULSADOR[1]
    puls = caja("Ref_pulsador", fondo_pulsador, fondo_pulsador + PULSADOR[1], BOTON_Y - lado / 2, BOTON_Y + lado / 2,
                BOTON_Z - lado / 2, BOTON_Z + lado / 2, col="Referencia")
    pintar(puls, negro)


def exportar_stl():
    os.makedirs(CARPETA_STL, exist_ok=True)
    rutas = []
    for nombre in ("Cuerpo", "Tapa", "Boton"):
        bpy.ops.object.select_all(action="DESELECT")
        obj = bpy.data.objects[nombre]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        ruta = os.path.join(CARPETA_STL, f"{nombre.lower()}.stl")
        bpy.ops.wm.stl_export(filepath=ruta, export_selected_objects=True, apply_modifiers=True)
        rutas.append(ruta)
    return rutas


def limpiar(obj):
    """Fusiona vértices duplicados y quita caras degeneradas que dejan las booleanas."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.001)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    malas = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(obj.data)
    bm.free()
    return malas


def construir_todo():
    preparar_escena()
    pieza = material("pieza", (0.85, 0.85, 0.82, 1))
    for obj in (construir_cuerpo(), construir_tapa(), construir_boton()):
        pintar(obj, pieza)
        print(obj.name, "aristas no manifold:", limpiar(obj))
    referencias()
    tc = bpy.data.collections.get("Trabajo")
    if tc and not tc.objects:
        bpy.data.collections.remove(tc)


if __name__ == "__main__":
    construir_todo()
