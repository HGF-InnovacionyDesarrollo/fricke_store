"""API del módulo F+fetal, montada en /api/m/monitoreo_fetal/.
Todo endpoint usa Depends(acceso(...)) y registra acciones en la bitácora sin datos personales en el detalle.
Implementa el motor determinístico MEFI v2.0 (Protocolo V2 sept. 2025, ACOG CPG No. 10 2025, FIGO 2015 y NICE NG229)
sobre escenarios docentes y simulaciones de capacitación sin datos de pacientes.
"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from plataforma import ContextoModulo, acceso, bd_modulo, nombres_de

from .manifiesto import CLAVE

router = APIRouter()
DIAS_CONSERVACION = 365

# Umbrales normativos (FIGO 2015 / NICE NG229 / ACOG CPG No. 10 2025 / Protocolo V2 sept. 2025)
BASAL_MIN_NORMAL = 110
BASAL_MAX_NORMAL = 160
VARIABILIDAD_AUSENTE_MAX = 1.0
VARIABILIDAD_REDUCIDA_MAX = 5.0
VARIABILIDAD_NORMAL_MAX = 25.0
DESACEL_PROLONGADA_MIN_S = 120
DESACEL_MUY_PROLONGADA_S = 300


class NuevaSimulacion(BaseModel):
    titulo: str = Field(min_length=3, max_length=100)
    escenario: Literal[
        "normal_reactivo",
        "taquisistolia_cat2",
        "variables_recurrentes_cat2",
        "patologico_cat3",
        "personalizado",
    ] = "personalizado"
    edad_gestacional_sem: int = Field(default=39, ge=24, le=43)
    linea_base_lpm: int = Field(default=140, ge=50, le=220)
    variabilidad_lpm: float = Field(default=12.0, ge=0.0, le=60.0)
    num_aceleraciones: int = Field(default=2, ge=0, le=40)
    num_desaceleraciones: int = Field(default=0, ge=0, le=40)
    tipo_desaceleracion: Literal["ninguna", "precoz", "variable", "tardia", "prolongada"] = "ninguna"
    duracion_max_decel_s: int = Field(default=0, ge=0, le=600)
    contracciones_10min: float = Field(default=3.0, ge=0.0, le=15.0)
    patron_sinusoidal: bool = False
    nota_docente: str = Field(default="", max_length=600)


def evaluar_parametros_mefi(d: NuevaSimulacion) -> dict:
    """Motor determinístico MEFI v2.0: clasifica parámetros simulados según FIGO 2015,
    NICE NG229, ACOG CPG No. 10 (2025) y Protocolo Institucional V2 (sept. 2025)."""
    basal = d.linea_base_lpm
    var_lpm = float(d.variabilidad_lpm)
    n_acel = d.num_aceleraciones
    n_decel = d.num_desaceleraciones
    tipo_dec = "ninguna" if n_decel == 0 else d.tipo_desaceleracion
    dur_dec = 0 if n_decel == 0 else d.duracion_max_decel_s
    contr_10 = float(d.contracciones_10min)
    sinusoidal = bool(d.patron_sinusoidal)

    # 1. Variabilidad en 4 categorías NICHD/ACOG (Fase B5) y 3 categorías FIGO/NICE
    if var_lpm < VARIABILIDAD_AUSENTE_MAX:
        cat_nichd = "ausente"
        cat_var = "reducida"
    elif var_lpm <= VARIABILIDAD_REDUCIDA_MAX:
        cat_nichd = "minima"
        cat_var = "reducida"
    elif var_lpm <= VARIABILIDAD_NORMAL_MAX:
        cat_nichd = "moderada"
        cat_var = "normal"
    else:
        cat_nichd = "marcada"
        cat_var = "aumentada"

    taquisistolia = contr_10 >= 5.0
    tardias_o_variables = n_decel > 0 and tipo_dec in ("variable", "tardia", "prolongada")
    repetitivas = tardias_o_variables and n_decel >= 3
    muy_prolongada = n_decel > 0 and dur_dec >= DESACEL_MUY_PROLONGADA_S
    prolongada_2m = n_decel > 0 and dur_dec >= DESACEL_PROLONGADA_MIN_S

    # 2. Clasificación MEFI de alta sensibilidad (FIGO 2015 / NICE NG229)
    es_cat_iii = (
        sinusoidal
        or muy_prolongada
        or (cat_var == "reducida" and basal < 100)
        or (cat_var == "reducida" and tardias_o_variables)
    )
    if es_cat_iii:
        cat_figo = "III"
    elif (
        BASAL_MIN_NORMAL <= basal <= BASAL_MAX_NORMAL
        and cat_var == "normal"
        and not repetitivas
        and not prolongada_2m
        and not taquisistolia
    ):
        cat_figo = "I"
    else:
        cat_figo = "II"

    # 3. Clasificación ACOG CPG No. 10 estricta (Fase A5)
    if sinusoidal or (cat_nichd == "ausente" and (repetitivas or basal < BASAL_MIN_NORMAL)):
        cat_acog = "III"
    elif BASAL_MIN_NORMAL <= basal <= BASAL_MAX_NORMAL and cat_nichd == "moderada" and not tardias_o_variables:
        cat_acog = "I"
    else:
        cat_acog = "II"

    # 4. Estratificación Box 3 ACOG para Categoría II (Fase A2)
    alto_riesgo = (
        cat_var == "reducida"
        or basal > BASAL_MAX_NORMAL
        or repetitivas
        or (prolongada_2m and n_decel >= 2)
    )
    protector = cat_nichd == "moderada" and n_acel >= 1
    if cat_figo != "II":
        riesgo_cat_ii = "no_aplica"
    elif alto_riesgo:
        riesgo_cat_ii = "alto"
    elif protector:
        riesgo_cat_ii = "con_rasgos_protectores"
    else:
        riesgo_cat_ii = "intermedio"

    # 5. Tipificación determinística de hipoxia (Protocolo V2, Fase C2)
    if muy_prolongada or (dur_dec >= 180 and cat_var == "reducida"):
        hipoxia = "aguda"
    elif repetitivas and dur_dec >= 90 and contr_10 >= 4.5:
        hipoxia = "subaguda"
    elif n_acel == 0 and repetitivas and (basal > BASAL_MAX_NORMAL or cat_var == "reducida"):
        hipoxia = "progresiva"
    elif basal >= 150 and cat_var == "reducida" and n_acel == 0:
        hipoxia = "cronica"
    else:
        hipoxia = "sin_hipoxia"

    # 6. Conducta sugerida según Protocolo V2 (sept. 2025) y ACOG CPG No. 10 (2025) (Fase A1)
    criterio_acel = "10 lpm × 10 s (<32 sem)" if d.edad_gestacional_sem < 32 else "15 lpm × 15 s (≥32 sem)"
    if cat_figo == "I":
        conducta = (
            f"Categoría I (Normal, criterio reactividad {criterio_acel}): mantener vigilancia habitual según etapa "
            "del trabajo de parto y Protocolo V2. Sin intervenciones correctivas requeridas."
        )
    elif cat_figo == "II":
        conducta = (
            "Categoría II (Sospechoso): conducta sugerida — aviso inmediato al médico/a ginecobstetra residente de turno "
            "(Protocolo V2). Reanimación intrauterina: lateralización materna, hidratación EV/corrección de hipotensión, "
            "reducir o suspender oxitocina, evaluar amnioinfusión si hay desaceleraciones variables recurrentes, "
            "corregir causas maternas si hay taquicardia, O2 suplementario SOLO si SatO2 materna < 94 % (ACOG CPG No. 10), "
            "y tocolisis de acción rápida (nitroglicerina/fenoterol institucional; terbutalina ACOG) si persiste taquisistolía. "
            "Ventana de observación de 30 a 60 min (Protocolo V2) individualizada según rasgos del Box 3 ACOG."
        )
    else:
        conducta = (
            "Categoría III (Patológico): conducta sugerida — aviso inmediato y reanimación intrauterina urgente "
            "(lateralización, hidratación EV, suspensión inmediata de uterotónicos, O2 solo si SatO2 < 94 %, tocolisis "
            "de acción rápida ante taquisistolía/tétanos). Si no revierte en máximo 10 minutos (Protocolo V2) o ante "
            "sospecha de accidente agudo (rotura uterina, prolapso, sinusoidal > 30 min), proceder a parto expedito."
        )

    return {
        "categoria_nichd": cat_nichd,
        "categoria_figo": cat_figo,
        "categoria_acog": cat_acog,
        "riesgo_cat_ii": riesgo_cat_ii,
        "hipoxia_tipificada": hipoxia,
        "resumen_conducta": conducta,
    }


CASOS_DOCENTES = [
    {
        "escenario": "normal_reactivo",
        "titulo": "Caso docente 1: Trazado reactivo normocárdico",
        "descripcion": "Gestación de 39 semanas en fase activa sin oxitocina, con variabilidad moderada y aceleraciones presentes.",
        "edad_gestacional_sem": 39,
        "linea_base_lpm": 140,
        "variabilidad_lpm": 12.0,
        "num_aceleraciones": 3,
        "num_desaceleraciones": 0,
        "tipo_desaceleracion": "ninguna",
        "duracion_max_decel_s": 0,
        "contracciones_10min": 3.0,
        "patron_sinusoidal": False,
    },
    {
        "escenario": "taquisistolia_cat2",
        "titulo": "Caso docente 2: Taquisistolía con rasgos protectores",
        "descripcion": "Conducción oxitócica con 6 contracciones en 10 min, pero con variabilidad moderada y reactividad conservada.",
        "edad_gestacional_sem": 38,
        "linea_base_lpm": 135,
        "variabilidad_lpm": 14.0,
        "num_aceleraciones": 2,
        "num_desaceleraciones": 1,
        "tipo_desaceleracion": "precoz",
        "duracion_max_decel_s": 35,
        "contracciones_10min": 6.0,
        "patron_sinusoidal": False,
    },
    {
        "escenario": "variables_recurrentes_cat2",
        "titulo": "Caso docente 3: Variables recurrentes con criterios «60»",
        "descripcion": "Desaceleraciones variables repetitivas (>60 s) con pérdida de aceleraciones y ascenso de la línea base a taquicardia.",
        "edad_gestacional_sem": 40,
        "linea_base_lpm": 165,
        "variabilidad_lpm": 6.5,
        "num_aceleraciones": 0,
        "num_desaceleraciones": 5,
        "tipo_desaceleracion": "variable",
        "duracion_max_decel_s": 85,
        "contracciones_10min": 4.5,
        "patron_sinusoidal": False,
    },
    {
        "escenario": "patologico_cat3",
        "titulo": "Caso docente 4: Desaceleración muy prolongada con variabilidad ausente",
        "descripcion": "Bradicardia prolongada ≥5 minutos (320 s) con variabilidad indetectable (<1 lpm): emergencia obstétrica.",
        "edad_gestacional_sem": 39,
        "linea_base_lpm": 105,
        "variabilidad_lpm": 0.6,
        "num_aceleraciones": 0,
        "num_desaceleraciones": 2,
        "tipo_desaceleracion": "prolongada",
        "duracion_max_decel_s": 320,
        "contracciones_10min": 5.5,
        "patron_sinusoidal": False,
    },
]


@router.get("/casos-docentes")
def listar_casos_docentes(ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.ver"))):
    salida = []
    for c in CASOS_DOCENTES:
        ev = evaluar_parametros_mefi(NuevaSimulacion(**c))
        salida.append({**c, **ev})
    return salida


@router.get("/simulaciones")
def listar_simulaciones(mias: bool = False, ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.ver"))):
    with bd_modulo(CLAVE) as c:
        if mias:
            filas = [
                dict(f)
                for f in c.execute(
                    "SELECT * FROM simulaciones WHERE autor_id=? ORDER BY id DESC LIMIT 100",
                    (ctx.usuario_id,),
                )
            ]
        else:
            filas = [dict(f) for f in c.execute("SELECT * FROM simulaciones ORDER BY id DESC LIMIT 100")]
    autores = nombres_de({f["autor_id"] for f in filas})
    for f in filas:
        f["variabilidad_lpm"] = float(f["variabilidad_lpm"])
        f["contracciones_10min"] = float(f["contracciones_10min"])
        f["autor"] = autores.get(f["autor_id"], "—")
        f["puede_borrar"] = ctx.puede(f"{CLAVE}.moderar") or (
            f["autor_id"] == ctx.usuario_id and ctx.puede(f"{CLAVE}.simular")
        )
    return filas


@router.post("/simulaciones")
def crear_simulacion(d: NuevaSimulacion, ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.simular"))):
    ev = evaluar_parametros_mefi(d)
    tipo_dec = "ninguna" if d.num_desaceleraciones == 0 else d.tipo_desaceleracion
    dur_dec = 0 if d.num_desaceleraciones == 0 else d.duracion_max_decel_s
    with bd_modulo(CLAVE) as c:
        sid = c.execute(
            """INSERT INTO simulaciones (
                autor_id, titulo, escenario, edad_gestacional_sem, linea_base_lpm,
                variabilidad_lpm, categoria_nichd, num_aceleraciones, num_desaceleraciones,
                tipo_desaceleracion, duracion_max_decel_s, contracciones_10min,
                patron_sinusoidal, categoria_figo, categoria_acog, riesgo_cat_ii,
                hipoxia_tipificada, resumen_conducta, nota_docente
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ctx.usuario_id,
                d.titulo.strip(),
                d.escenario,
                d.edad_gestacional_sem,
                d.linea_base_lpm,
                d.variabilidad_lpm,
                ev["categoria_nichd"],
                d.num_aceleraciones,
                d.num_desaceleraciones,
                tipo_dec,
                dur_dec,
                d.contracciones_10min,
                d.patron_sinusoidal,
                ev["categoria_figo"],
                ev["categoria_acog"],
                ev["riesgo_cat_ii"],
                ev["hipoxia_tipificada"],
                ev["resumen_conducta"],
                d.nota_docente.strip(),
            ),
        ).lastrowid
    ctx.auditar(f"{CLAVE}_simulacion_creada", f"simulación #{sid}")
    return {"id": sid, **ev}


@router.delete("/simulaciones/{sid}")
def borrar_simulacion(sid: int, ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.ver"))):
    with bd_modulo(CLAVE) as c:
        s = c.execute("SELECT autor_id FROM simulaciones WHERE id=?", (sid,)).fetchone()
        if not s:
            raise HTTPException(404, "La simulación no existe.")
        propio = s["autor_id"] == ctx.usuario_id and ctx.puede(f"{CLAVE}.simular")
        if not (propio or ctx.puede(f"{CLAVE}.moderar")):
            raise HTTPException(403, "Solo puedes borrar tus propias simulaciones.")
        c.execute("DELETE FROM simulaciones WHERE id=?", (sid,))
    ctx.auditar(f"{CLAVE}_simulacion_borrada", f"simulación #{sid}{'' if propio else ' (moderación)'}")
    return {"ok": True}


# ------------------------------------------------------------------ Ley 21.719 (obligatorios si guarda datos de personas)
def exportar_titular(usuario_id: int) -> dict:
    """Lo que este módulo guarda de la persona (como funcionario). Se suma a 'Descargar mis datos' en Mi cuenta."""
    with bd_modulo(CLAVE) as c:
        return {
            "simulaciones_registradas": [
                dict(f)
                for f in c.execute(
                    """SELECT id, titulo, escenario, categoria_figo, categoria_acog,
                              riesgo_cat_ii, hipoxia_tipificada, nota_docente, creado_en
                       FROM simulaciones WHERE autor_id=? ORDER BY id""",
                    (usuario_id,),
                )
            ]
        }


def depurar() -> int:
    """Aplica el plazo de conservación declarado en la ficha (365 días). Devuelve cuántos registros eliminó."""
    with bd_modulo(CLAVE) as c:
        return c.execute(
            "DELETE FROM simulaciones WHERE creado_en < now() - make_interval(days => ?)",
            (DIAS_CONSERVACION,),
        ).rowcount
