"""Motor determinístico MEFI v2.0 en Python puro para F+mefi (Fricke Store).

Reproduce el pipeline completo de series de tiempo cardiotocográficas (FCF y UA)
de `clinical.py`, `ux_helpers.py` y `prompts.py` sin requerir dependencias fuera
de `requirements.txt` del portal (usa solo `math` y `statistics` de la biblioteca
estándar), garantizando que el CI de GitHub Actions de Fricke Store corra sin
dependencias externas adicionales.

Normativa integrada:
- Protocolo de Vigilancia del Bienestar Fetal Intraparto V2 (sept. 2025, HGF).
- ACOG Clinical Practice Guideline No. 10 (Obstet Gynecol 2025;146:583-599).
- FIGO 2015 y NICE NG229.
"""
from __future__ import annotations

import math
from statistics import median

BASAL_MIN_NORMAL = 110
BASAL_MAX_NORMAL = 160
VARIABILIDAD_AUSENTE_MAX_LPM = 1.0
VARIABILIDAD_REDUCIDA_MAX = 5.0
VARIABILIDAD_NORMAL_MAX = 25.0

UMBRAL_ACEL_DECEL = 15.0
DURACION_MIN_EVENTO_S = 15.0
UMBRAL_ACEL_PRETERMINO = 10.0
DURACION_MIN_ACEL_PRETERMINO_S = 10.0
ACELERACION_PROLONGADA_MIN_S = 120.0
DURACION_MAX_ACELERACION_S = 600.0

ONSET_ABRUPTO_MAX_S = 30.0
DESACEL_PROLONGADA_MIN_S = 120.0
DESACEL_MUY_PROLONGADA_S = 300.0
TOLERANCIA_COINCIDENCIA_S = 20.0

SINUSOIDAL_DURACION_MIN_S = 1200.0
SINUSOIDAL_FRECUENCIA_MIN_CPM = 3.0
SINUSOIDAL_FRECUENCIA_MAX_CPM = 5.0
SINUSOIDAL_AMPLITUD_MIN = 5.0
SINUSOIDAL_AMPLITUD_MAX = 15.0

TAQUISISTOLIA_VENTANA_ACOG_S = 1800.0
CRITERIO_60_PERSISTENCIA_S = 1800.0


def _mediana_movil(valores: list[float], ventana: int) -> list[float]:
    n = len(valores)
    if n == 0 or ventana <= 1:
        return list(valores)
    mitad = ventana // 2
    salida = []
    for i in range(n):
        ini = max(0, i - mitad)
        fin = min(n, i + mitad + 1)
        salida.append(float(median(valores[ini:fin])))
    return salida


def _media_movil(valores: list[float], ventana: int) -> list[float]:
    n = len(valores)
    if n == 0 or ventana <= 1:
        return list(valores)
    mitad = ventana // 2
    salida = []
    for i in range(n):
        ini = max(0, i - mitad)
        fin = min(n, i + mitad + 1)
        tramo = valores[ini:fin]
        salida.append(sum(tramo) / len(tramo))
    return salida


def _percentil(valores: list[float], p: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * (p / 100.0)
    f = int(math.floor(k))
    c = int(math.ceil(k))
    if f == c:
        return float(ordenados[f])
    return float(ordenados[f] * (c - k) + ordenados[c] * (k - f))


def calcular_linea_base(tiempos: list[float], fcf: list[float], confiable: list[bool]) -> float:
    pts = [float(v) for v, ok in zip(fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    if not pts:
        raise ValueError("No hay puntos de FCF confiables para calcular la línea base.")
    basal = float(median(pts))
    for _ in range(5):
        estables = [v for v in pts if abs(v - basal) < UMBRAL_ACEL_DECEL]
        if len(estables) < max(10, int(len(pts) * 0.2)):
            break
        nueva = float(median(estables))
        if abs(nueva - basal) < 0.5:
            basal = nueva
            break
        basal = nueva
    return float(round(basal / 5.0) * 5)


def _agrupar_eventos(tiempos: list[float], mascara: list[bool]) -> list[tuple[float, float]]:
    eventos: list[tuple[float, float]] = []
    en_ev = False
    ini = 0.0
    prev_t = 0.0
    for t, act in zip(tiempos, mascara):
        if act and not en_ev:
            en_ev = True
            ini = float(t)
        elif not act and en_ev:
            en_ev = False
            eventos.append((ini, float(prev_t)))
        prev_t = float(t)
    if en_ev:
        eventos.append((ini, float(prev_t)))
    return eventos


def detectar_aceleraciones(
    tiempos: list[float],
    fcf: list[float],
    confiable: list[bool],
    basal: float,
    edad_gestacional_sem: int = 39,
) -> list[dict]:
    ts = [float(t) for t, v, ok in zip(tiempos, fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    vs = [float(v) for v, ok in zip(fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    if not ts:
        return []
    es_pret = edad_gestacional_sem < 32
    umbral = UMBRAL_ACEL_PRETERMINO if es_pret else UMBRAL_ACEL_DECEL
    dur_min = DURACION_MIN_ACEL_PRETERMINO_S if es_pret else DURACION_MIN_EVENTO_S

    mascara = [v >= basal + umbral for v in vs]
    eventos = []
    for ini, fin in _agrupar_eventos(ts, mascara):
        dur = fin - ini
        if dur < dur_min or dur > DURACION_MAX_ACELERACION_S:
            continue
        tramo = [v for t, v in zip(ts, vs) if ini <= t <= fin]
        amp = max(tramo) - basal if tramo else umbral
        es_prol = dur >= ACELERACION_PROLONGADA_MIN_S
        eventos.append({
            "inicio_s": round(ini, 1),
            "fin_s": round(fin, 1),
            "duracion_s": round(dur, 1),
            "amplitud_max_lpm": round(amp, 1),
            "prolongada": es_prol,
            "etiqueta": "aceleración prolongada" if es_prol else "aceleración",
        })
    return eventos


def detectar_contracciones(tiempos: list[float], ua: list[float]) -> list[float]:
    if len(tiempos) < 20 or not ua:
        return []
    dt = float(median([tiempos[i + 1] - tiempos[i] for i in range(len(tiempos) - 1) if tiempos[i + 1] > tiempos[i]] or [1.0]))
    if dt <= 0:
        dt = 1.0
    n_corta = max(3, int(round(7.0 / dt)) | 1)
    n_suave = max(5, int(round(20.0 / dt)) | 1)
    n_tono = max(n_suave, int(round(240.0 / dt)) | 1)

    suave = _media_movil(_mediana_movil(ua, n_corta), n_suave)
    tono = _mediana_movil(suave, n_tono)
    detrend = [max(0.0, s - b) for s, b in zip(suave, tono)]
    escala = _percentil(detrend, 95) - _percentil(detrend, 20)
    if escala < 3.0:
        return []
    umbral = max(4.0, 0.25 * escala)
    sep_min_s = 45.0

    picos: list[float] = []
    n = len(detrend)
    ventana_pico = max(2, int(round(12.0 / dt)))
    for i in range(ventana_pico, n - ventana_pico):
        val = detrend[i]
        if val < umbral:
            continue
        vecinos = detrend[i - ventana_pico : i + ventana_pico + 1]
        if val >= max(vecinos):
            t_p = float(tiempos[i])
            if not picos or (t_p - picos[-1]) >= sep_min_s:
                picos.append(round(t_p, 1))
    return picos


def detectar_desaceleraciones(
    tiempos: list[float],
    fcf: list[float],
    confiable: list[bool],
    basal: float,
    picos_ua: list[float],
) -> list[dict]:
    ts = [float(t) for t, v, ok in zip(tiempos, fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    vs = [float(v) for v, ok in zip(fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    if not ts:
        return []
    dt = float(median([ts[i + 1] - ts[i] for i in range(len(ts) - 1) if ts[i + 1] > ts[i]] or [1.0]))
    mascara = [v <= basal - UMBRAL_ACEL_DECEL for v in vs]
    eventos = []
    for ini, fin in _agrupar_eventos(ts, mascara):
        dur = fin - ini
        if dur < DURACION_MIN_EVENTO_S:
            continue
        pares = [(t, v) for t, v in zip(ts, vs) if ini <= t <= fin]
        if not pares:
            continue
        t_nadir, nadir_lpm = min(pares, key=lambda x: x[1])
        onset = t_nadir - ini
        abrupta = onset < ONSET_ABRUPTO_MAX_S

        if not picos_ua:
            tipo = "variable" if abrupta else "indeterminada"
        else:
            pico_cercano = min(picos_ua, key=lambda p: abs(p - t_nadir))
            desfase = t_nadir - pico_cercano
            if abrupta:
                tipo = "variable"
            elif abs(desfase) <= TOLERANCIA_COINCIDENCIA_S:
                tipo = "precoz"
            elif desfase > TOLERANCIA_COINCIDENCIA_S:
                tipo = "tardia"
            else:
                tipo = "variable"

        es_prol = dur >= DESACEL_PROLONGADA_MIN_S
        muy_prol = dur >= DESACEL_MUY_PROLONGADA_S
        amp_caida = basal - nadir_lpm

        # Fase B6: variabilidad intra-desaceleración en eventos >= 2 min
        var_intra_lpm = None
        var_red_intra = False
        if es_prol and len(pares) >= 4:
            vals_tramo = [v for _, v in pares]
            win_med = max(3, int(round(20.0 / max(0.25, dt))) | 1)
            tend = _mediana_movil(vals_tramo, win_med)
            osc = [v - m for v, m in zip(vals_tramo, tend)]
            rango_b = max(vals_tramo) - min(vals_tramo)
            rango_d = max(osc) - min(osc)
            var_intra_lpm = round(min(rango_b, rango_d), 1)
            var_red_intra = var_intra_lpm < VARIABILIDAD_REDUCIDA_MAX

        # Fase C1: Criterios «60» en desaceleraciones variables
        crit_60: list[str] = []
        if tipo == "variable":
            if dur > 60.0:
                crit_60.append("duración >60s")
            if nadir_lpm < 60.0:
                crit_60.append("nadir <60 lpm")
            if amp_caida > 60.0:
                crit_60.append("caída >60 lpm")

        eventos.append({
            "inicio_s": round(ini, 1),
            "fin_s": round(fin, 1),
            "duracion_s": round(dur, 1),
            "nadir_lpm": round(nadir_lpm, 1),
            "amplitud_max_lpm": round(amp_caida, 1),
            "tipo": tipo,
            "prolongada": es_prol,
            "muy_prolongada": muy_prol,
            "variabilidad_intra_lpm": var_intra_lpm,
            "variabilidad_reducida_intra_evento": var_red_intra,
            "criterios_60_cumplidos": crit_60,
            "num_criterios_60": len(crit_60),
        })
    return eventos


def calcular_variabilidad(
    tiempos: list[float],
    fcf: list[float],
    confiable: list[bool],
    eventos_excluir: list[dict],
    ventana_s: float = 60.0,
) -> dict:
    pares = [(float(t), float(v)) for t, v, ok in zip(tiempos, fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    if not pares:
        return {"amplitud_media_lpm": 0.0, "categoria": "reducida", "categoria_nichd": "ausente", "ventanas_evaluadas": 0}

    filtrados = [
        (t, v)
        for t, v in pares
        if not any((ev["inicio_s"] - ventana_s) <= t <= (ev["fin_s"] + ventana_s) for ev in eventos_excluir)
    ]
    if not filtrados:
        filtrados = pares

    bins: dict[int, list[float]] = {}
    for t, v in filtrados:
        b = int(t // ventana_s)
        bins.setdefault(b, []).append(v)

    amps = [max(vs) - min(vs) for vs in bins.values() if len(vs) >= 2]
    amp_repr = float(median(amps)) if amps else 0.0

    if amp_repr < VARIABILIDAD_REDUCIDA_MAX:
        cat = "reducida"
    elif amp_repr <= VARIABILIDAD_NORMAL_MAX:
        cat = "normal"
    else:
        cat = "aumentada"

    if amp_repr < VARIABILIDAD_AUSENTE_MAX_LPM:
        cat_nichd = "ausente"
    elif amp_repr <= VARIABILIDAD_REDUCIDA_MAX:
        cat_nichd = "minima"
    elif amp_repr <= VARIABILIDAD_NORMAL_MAX:
        cat_nichd = "moderada"
    else:
        cat_nichd = "marcada"

    return {
        "amplitud_media_lpm": round(amp_repr, 1),
        "categoria": cat,
        "categoria_nichd": cat_nichd,
        "ventanas_evaluadas": len(amps),
    }


def detectar_patron_sinusoidal(tiempos: list[float], fcf: list[float], confiable: list[bool]) -> dict:
    pares = [(float(t), float(v)) for t, v, ok in zip(tiempos, fcf, confiable) if ok and 50.0 <= float(v) <= 220.0]
    if len(pares) < 30:
        return {"presente": False, "motivo": "datos insuficientes", "duracion_evaluada_min": 0.0}
    ts = [t for t, _ in pares]
    vs = [v for _, v in pares]
    dt = float(median([ts[i + 1] - ts[i] for i in range(len(ts) - 1) if ts[i + 1] > ts[i]] or [1.0]))
    dur_total = (ts[-1] - ts[0]) + dt
    if dur_total < SINUSOIDAL_DURACION_MIN_S - 1e-6:
        return {
            "presente": False,
            "motivo": "tramo confiable menor a 20 minutos (ACOG Tabla 1)",
            "duracion_evaluada_min": round(dur_total / 60.0, 1),
        }

    win = max(3, int(round(20.0 / max(0.25, dt))) | 1)
    tend = _mediana_movil(vs, win)
    osc = [v - m for v, m in zip(vs, tend)]
    media_osc = sum(osc) / len(osc)
    osc = [x - media_osc for x in osc]
    amp = (_percentil(osc, 95) - _percentil(osc, 5)) / 2.0

    # Evaluar energía espectral por Goertzel/DFT discreta entre 1 y 12 cpm
    energia_total = 0.0
    energia_banda = 0.0
    mejor_e = -1.0
    f_dom = 4.0
    n = len(osc)
    paso = max(1, n // 600)
    osc_sub = osc[::paso]
    ts_sub = ts[::paso]
    for f_cpm_10 in range(10, 121, 5):
        f_cpm = f_cpm_10 / 10.0
        w = 2.0 * math.pi * (f_cpm / 60.0)
        re_s = sum(x * math.cos(w * t) for x, t in zip(osc_sub, ts_sub))
        im_s = sum(x * math.sin(w * t) for x, t in zip(osc_sub, ts_sub))
        mag = math.hypot(re_s, im_s)
        energia_total += mag
        if SINUSOIDAL_FRECUENCIA_MIN_CPM <= f_cpm <= SINUSOIDAL_FRECUENCIA_MAX_CPM:
            energia_banda += mag
            if mag > mejor_e:
                mejor_e = mag
                f_dom = f_cpm

    prop = (energia_banda / energia_total) if energia_total > 0 else 0.0
    presente = prop >= 0.42 and (SINUSOIDAL_AMPLITUD_MIN <= amp <= SINUSOIDAL_AMPLITUD_MAX)
    return {
        "presente": bool(presente),
        "frecuencia_dominante_cpm": round(f_dom, 2),
        "amplitud_lpm": round(amp, 1),
        "duracion_evaluada_min": round(dur_total / 60.0, 1),
    }


def _hay_repetitivas(decels: list[dict], ventana_s: float = 1200.0, minimo: int = 3) -> bool:
    if len(decels) < minimo:
        return False
    inicios = sorted(float(d["inicio_s"]) for d in decels)
    for i in range(len(inicios) - minimo + 1):
        if inicios[i + minimo - 1] - inicios[i] <= ventana_s:
            return True
    return False


def analizar_trazado_completo(
    tiempos: list[float],
    fcf: list[float],
    fcf_confiable: list[bool],
    ua: list[float],
    metadatos: dict | None = None,
) -> dict:
    """Ejecuta el pipeline completo de MEFI v2.0 sobre las curvas digitalizadas
    y devuelve todos los parámetros, clasificaciones, tabla de desaceleraciones
    e informe clínico estructurado por protocolo."""
    meta = metadatos or {}
    eg_sem = int(meta.get("edad_gestacional_sem") or 39)

    basal = calcular_linea_base(tiempos, fcf, fcf_confiable)
    picos_ua = detectar_contracciones(tiempos, ua)
    acels = detectar_aceleraciones(tiempos, fcf, fcf_confiable, basal, edad_gestacional_sem=eg_sem)
    decels = detectar_desaceleraciones(tiempos, fcf, fcf_confiable, basal, picos_ua)
    variabilidad = calcular_variabilidad(tiempos, fcf, fcf_confiable, acels + decels)
    sinusoidal = detectar_patron_sinusoidal(tiempos, fcf, fcf_confiable)

    t_min = float(min(tiempos)) if tiempos else 0.0
    t_max = float(max(tiempos)) if tiempos else 0.0
    dur_s = max(1.0, t_max - t_min)
    dur_min = dur_s / 60.0
    num_contr = len(picos_ua)
    por_10min = round(num_contr / (dur_min / 10.0), 1) if dur_min > 0 else 0.0

    # Fase B4: Taquisistolía en ventana móvil de 30 min + respaldo global
    evaluada_30m = dur_s >= TAQUISISTOLIA_VENTANA_ACOG_S - 1.0
    por_10min_30m = None
    taq_acog_30m = False
    if evaluada_30m:
        if not picos_ua:
            por_10min_30m = 0.0
        else:
            max_ini = max(t_min, t_max - TAQUISISTOLIA_VENTANA_ACOG_S)
            cands = sorted({t_min, max_ini} | {min(max(t_min, p), max_ini) for p in picos_ua})
            max_c = max(sum(1 for p in picos_ua if w0 - 1e-6 <= p <= w0 + TAQUISISTOLIA_VENTANA_ACOG_S + 1e-6) for w0 in cands)
            por_10min_30m = round(max_c / 3.0, 1)
            taq_acog_30m = por_10min_30m > 5.0
    taq_global = por_10min >= 5.0
    taquisistolia = bool(taq_global or taq_acog_30m)

    area_decel = round(sum(float(d["duracion_s"]) * float(d["amplitud_max_lpm"]) for d in decels))
    tardias_o_var = [d for d in decels if d["tipo"] in ("tardia", "variable", "indeterminada")]
    repetitivas = _hay_repetitivas(tardias_o_var)
    hay_muy_prol = any(d["muy_prolongada"] for d in decels)

    cat_var = variabilidad["categoria"]
    cat_nichd = variabilidad["categoria_nichd"]

    # Clasificación MEFI (FIGO 2015 / NICE NG229)
    semaforo = {
        "linea_base": "verde" if BASAL_MIN_NORMAL <= basal <= BASAL_MAX_NORMAL else "amarillo",
        "variabilidad": {"normal": "verde", "aumentada": "amarillo", "reducida": "rojo"}[cat_var],
        "desaceleraciones": "verde",
        "contracciones": "amarillo" if taquisistolia else "verde",
    }
    razones_figo: list[str] = []
    es_patologico = False
    if sinusoidal["presente"]:
        es_patologico = True
        razones_figo.append("Patrón sinusoidal presente.")
    if hay_muy_prol:
        es_patologico = True
        razones_figo.append("Desaceleración prolongada ≥5 minutos.")
    if cat_var == "reducida" and basal < 100:
        es_patologico = True
        razones_figo.append("Línea base <100 lpm con variabilidad reducida.")
    if cat_var == "reducida" and len(tardias_o_var) >= 1:
        es_patologico = True
        razones_figo.append("Variabilidad reducida junto a desaceleraciones tardías/variables.")

    if es_patologico:
        cat_figo = "III"
        desc_figo = "Patológico"
        semaforo["desaceleraciones"] = "rojo"
    elif (
        BASAL_MIN_NORMAL <= basal <= BASAL_MAX_NORMAL
        and cat_var == "normal"
        and not repetitivas
        and not taquisistolia
    ):
        cat_figo = "I"
        desc_figo = "Normal"
        razones_figo = (
            [f"{len(tardias_o_var)} desaceleración(es) aislada(s), no repetitivas."]
            if tardias_o_var
            else ["Sin hallazgos anormales."]
        )
    else:
        cat_figo = "II"
        desc_figo = "Sospechoso"
        if tardias_o_var:
            semaforo["desaceleraciones"] = "amarillo"
            razones_figo.append(
                f"{len(tardias_o_var)} desaceleración(es) tardía(s)/variable(s) "
                f"{'repetitivas' if repetitivas else 'sin criterio patológico'}."
            )
        if basal < BASAL_MIN_NORMAL or basal > BASAL_MAX_NORMAL:
            razones_figo.append(f"Línea base fuera de rango normal ({basal:.0f} lpm).")
        if cat_var != "normal":
            razones_figo.append(f"Variabilidad {cat_var} (NICHD: {cat_nichd}).")
        if taquisistolia:
            razones_figo.append(f"Taquisistolía ({por_10min}/10 min global).")

    # Fase A5: ACOG CPG No. 10 estricta
    if sinusoidal["presente"] or (cat_nichd == "ausente" and (repetitivas or basal < BASAL_MIN_NORMAL)):
        cat_acog = "III"
    elif BASAL_MIN_NORMAL <= basal <= BASAL_MAX_NORMAL and cat_nichd == "moderada" and not tardias_o_var:
        cat_acog = "I"
    else:
        cat_acog = "II"

    # Fase A2: Subclasificador Box 3 ACOG para Categoría II
    rasgos_alto = []
    if cat_var == "reducida":
        rasgos_alto.append(f"Variabilidad {cat_nichd} (≤5 lpm)")
    if basal > BASAL_MAX_NORMAL:
        rasgos_alto.append(f"Taquicardia fetal ({basal:.0f} lpm)")
    if repetitivas:
        rasgos_alto.append("Desaceleraciones tardías/variables recurrentes")
    if sum(1 for d in decels if d["prolongada"]) > 1:
        rasgos_alto.append("Más de una desaceleración prolongada (≥2 min)")

    rasgos_prot = []
    if cat_nichd == "moderada":
        rasgos_prot.append("Variabilidad moderada conservada (5–25 lpm)")
    if len(acels) >= 1:
        rasgos_prot.append(f"Presencia de aceleraciones ({len(acels)} eventos)")

    if rasgos_alto:
        nivel_riesgo_cat2 = "alto"
    elif rasgos_prot:
        nivel_riesgo_cat2 = "con_rasgos_protectores"
    else:
        nivel_riesgo_cat2 = "intermedio"

    # Fase A3: Sospecha de FCF materna
    coinc_materna = 0
    for ac in acels:
        t_med = 0.5 * (ac["inicio_s"] + ac["fin_s"])
        if any(abs(p - t_med) <= TOLERANCIA_COINCIDENCIA_S for p in picos_ua):
            coinc_materna += 1
    sospecha_fcf_materna = coinc_materna >= 2

    # Fase C1: Criterios «60»
    ev_c60 = [d for d in decels if d["tipo"] == "variable" and d["num_criterios_60"] >= 2]
    lapso_c60_s = (max(d["fin_s"] for d in ev_c60) - min(d["inicio_s"] for d in ev_c60)) if ev_c60 else 0.0
    alerta_c60 = len(ev_c60) >= 1 and lapso_c60_s > CRITERIO_60_PERSISTENCIA_S

    # Fase C2: Tipificación determinística de hipoxia
    t_desacel_s = sum(d["duracion_s"] for d in decels)
    prop_desacel = t_desacel_s / dur_s if dur_s > 0 else 0.0
    if hay_muy_prol or any(d["duracion_s"] >= 180.0 and d["variabilidad_reducida_intra_evento"] for d in decels):
        hipoxia_codigo = "aguda"
        hipoxia_texto = "Hipoxia Aguda (Protocolo V2): evento prolongado ≥5 min o ≥3 min con variabilidad intra-evento reducida."
    elif prop_desacel > 0.50:
        hipoxia_codigo = "subaguda"
        hipoxia_texto = f"Hipoxia Subaguda (Protocolo V2): el feto pasa más tiempo desacelerando ({prop_desacel * 100:.0f}%) que en línea basal."
    elif len(acels) == 0 and (repetitivas or len(tardias_o_var) >= 2) and (basal > BASAL_MAX_NORMAL or cat_var == "reducida"):
        hipoxia_codigo = "progresiva"
        hipoxia_texto = "Hipoxia Progresiva (Protocolo V2): ausencia de aceleraciones + desaceleraciones repetitivas + taquicardia o variabilidad reducida."
    elif basal >= 150.0 and cat_var == "reducida" and len(acels) == 0:
        hipoxia_codigo = "cronica"
        hipoxia_texto = "Hipoxia Crónica / Preexistente (Protocolo V2): línea base en límite alto con variabilidad reducida y sin aceleraciones."
    else:
        hipoxia_codigo = "sin_hipoxia"
        hipoxia_texto = "Sin signos de hipoxia evolutiva (Protocolo V2): sin criterios para hipoxia aguda, subaguda, progresiva ni crónica."

    # Calidad de lectura
    n_conf = sum(1 for ok in fcf_confiable if ok)
    pct_directa = round((n_conf / len(fcf_confiable)) * 100.0, 1) if fcf_confiable else 100.0

    # Conducta sugerida (Fase A1)
    if cat_figo == "I":
        conducta = (
            "Categoría I (Normal): alta probabilidad de bienestar fetal (VPN >96 %). "
            "Conducta sugerida: mantener vigilancia obstétrica habitual según etapa del parto y Protocolo V2."
        )
    elif cat_figo == "II":
        conducta = (
            "Categoría II (Sospechoso): conducta sugerida — aviso inmediato al médico/a ginecobstetra residente de turno "
            "(responsabilidad de la matrón/a según Protocolo V2). Maniobras de reanimación intrauterina: "
            "1) Lateralización materna; 2) Hidratación EV y corrección de hipotensión; 3) Reducir o suspender oxitocina; "
            "4) Evaluar amnioinfusión ante desaceleraciones variables recurrentes; 5) Corregir fisiopatología materna si hay taquicardia; "
            "6) Oxígeno suplementario SOLO si existe hipoxia materna (SatO2 < 94 %, ACOG CPG No. 10); "
            "7) Tocolisis de acción rápida (nitroglicerina/fenoterol institucional; terbutalina ACOG) si persiste taquisistolía. "
            "Ventana de observación de 30 a 60 min (Protocolo V2) matizada por el Box 3 ACOG."
        )
    else:
        conducta = (
            "Categoría III (Patológico): conducta sugerida — aviso inmediato al residente ginecobstetra y reanimación urgente "
            "(lateralización, hidratación EV, suspensión inmediata de oxitocina, O2 solo si SatO2 < 94 %, tocolisis de acción rápida "
            "ante taquisistolía/tétanos antes del parto). Si no revierte en máximo 10 minutos (Protocolo V2) o ante bradicardia por "
            "sospecha de rotura uterina / sinusoidal > 30 min, proceder a interrupción expedita del embarazo."
        )

    # Informe clínico estructurado en las 4 dimensiones
    ctx_partes = [f"EG: {eg_sem} sem"]
    if meta.get("contexto_clinico"):
        ctx_partes.append(f"Contexto: {meta['contexto_clinico']}")
    if meta.get("uso_oxitocina"):
        ctx_partes.append(f"Oxitocina: {meta['uso_oxitocina']}")
    if meta.get("meconio"):
        ctx_partes.append(f"Líquido amniótico: {meta['meconio']}")
    if meta.get("patologia_antenatal"):
        ctx_partes.append(f"Patología antenatal: {meta['patologia_antenatal']}")
    if meta.get("comparacion_mefi_previos"):
        ctx_partes.append(f"Comparación MEFI previos: {meta['comparacion_mefi_previos']}")

    informe_secciones = {
        "contexto": " · ".join(ctx_partes),
        "seccion_1": (
            f"FCF basal: {basal:.0f} lpm · Variabilidad: {variabilidad['amplitud_media_lpm']} lpm "
            f"(FIGO/NICE: {cat_var} · NICHD/ACOG: {cat_nichd}) · Aceleraciones: {len(acels)} · "
            f"Desaceleraciones: {len(decels)} (área acumulada: {area_decel} lpm·s) · "
            f"Contracciones: {num_contr} ({por_10min}/10 min global"
            + (f", {por_10min_30m}/10 min en ventana 30 min" if por_10min_30m is not None else "")
            + f") · Sinusoidal: {'Presente' if sinusoidal['presente'] else 'No detectado'}."
        ),
        "seccion_2": (
            f"Categoría MEFI (FIGO 2015 / NICE NG229): Categoría {cat_figo} ({desc_figo}) — {'; '.join(razones_figo)} · "
            f"Lectura ACOG CPG No. 10 estricta: Categoría {cat_acog} "
            f"({'concordante con MEFI' if cat_acog == cat_figo else 'difiere de MEFI de alta sensibilidad'}) · "
            f"Riesgo Box 3 ACOG: {nivel_riesgo_cat2.replace('_', ' ').upper()}."
        ),
        "seccion_3": (
            f"{hipoxia_texto} · "
            + (
                f"Marcador Criterios «60»: {len(ev_c60)} desaceleración(es) variable(s) con ≥2 criterios «60» "
                f"({'ACTIVO >30 min' if alerta_c60 else '<30 min'})."
                if ev_c60
                else "Sin desaceleraciones variables con ≥2 criterios «60»."
            )
        ),
        "seccion_4": conducta,
        "disclaimer": (
            "Nota reguladora: ACOG CPG No. 10 (2025) recomienda en contra de depender primariamente de sistemas "
            "computarizados para interpretar y manejar la FCF (evidencia moderada; ref. ensayo INFANT, Lancet 2017). "
            "Herramienta docente y de apoyo con validación humana obligatoria."
        ),
    }

    tipo_predominante = "ninguna"
    dur_max_dec = 0
    if decels:
        dur_max_dec = int(round(max(d["duracion_s"] for d in decels)))
        if any(d["prolongada"] for d in decels):
            tipo_predominante = "prolongada"
        elif any(d["tipo"] == "tardia" for d in decels):
            tipo_predominante = "tardia"
        elif any(d["tipo"] == "variable" for d in decels):
            tipo_predominante = "variable"
        else:
            tipo_predominante = "precoz"

    return {
        "calidad_lectura": {
            "pct_directa": pct_directa,
            "pct_interpolado": round(max(0.0, 100.0 - pct_directa), 1),
            "duracion_min": round(dur_min, 1),
        },
        "linea_base_lpm": int(round(basal)),
        "variabilidad": variabilidad,
        "aceleraciones": acels,
        "desaceleraciones": decels,
        "area_desaceleraciones_lpm_s": area_decel,
        "contracciones": {
            "num": num_contr,
            "por_10min": por_10min,
            "por_10min_ventana_30m": por_10min_30m,
            "tachisistolia": taquisistolia,
        },
        "patron_sinusoidal": sinusoidal,
        "semaforo_nice": semaforo,
        "categoria_figo": cat_figo,
        "descripcion_figo": desc_figo,
        "razones_figo": razones_figo,
        "categoria_acog": cat_acog,
        "riesgo_cat_ii": nivel_riesgo_cat2 if cat_figo == "II" else "no_aplica",
        "razones_riesgo_cat_ii": rasgos_alto + [f"Protector: {r}" for r in rasgos_prot],
        "sospecha_fcf_materna": {
            "sospecha": sospecha_fcf_materna,
            "coincidencias": coinc_materna,
            "mensaje": (
                f"Se detectaron {coinc_materna} aceleraciones coincidentes con picos de contracción. "
                "Verifique pulso materno con pulsioxímetro (Supuesto 5 Protocolo V2 / ACOG)."
                if sospecha_fcf_materna
                else ""
            ),
        },
        "criterios_60": {
            "alerta_activa": alerta_c60,
            "num_eventos": len(ev_c60),
            "lapso_min": round(lapso_c60_s / 60.0, 1),
        },
        "hipoxia_tipificada": hipoxia_codigo,
        "hipoxia_resumen": hipoxia_texto,
        "resumen_conducta": conducta,
        "informe": informe_secciones,
        "resumen_para_guardar": {
            "edad_gestacional_sem": max(24, min(43, eg_sem)),
            "linea_base_lpm": max(50, min(220, int(round(basal)))),
            "variabilidad_lpm": max(0.0, min(60.0, float(variabilidad["amplitud_media_lpm"]))),
            "num_aceleraciones": min(40, len(acels)),
            "num_desaceleraciones": min(40, len(decels)),
            "tipo_desaceleracion": tipo_predominante,
            "duracion_max_decel_s": min(600, dur_max_dec),
            "contracciones_10min": max(0.0, min(15.0, float(por_10min))),
            "patron_sinusoidal": bool(sinusoidal["presente"]),
        },
    }
