// Data+ según las directrices de diseño (docs/diseno/, Parte 3): iniciarModulo, cuatro estados, esc() y api().
// Pantallas: Resumen (y detalle de un sensor en /resumen/<id>), Alarmas, Equipos y sensores, Eventos,
// Importaciones y Acerca del módulo. Los gráficos son SVG propios: sin bibliotecas ni recursos de Internet.
"use strict";

const CLAVE = "datalogger";
const API = `/api/m/${CLAVE}`;

// Íconos de línea de Lucide (ISC) que este módulo usa y la plataforma aún no trae.
Object.assign(LINEAS, {
  "layout-dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
  bell: '<path d="M10.268 21a2 2 0 0 0 3.464 0"/><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"/>',
  cpu: '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
  history: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
  thermometer: '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
  droplet: '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
  "battery-low": '<rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><path d="M22 11v2M6 11v2"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  printer: '<path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  "triangle-alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  pencil: '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/>',
});

// ---------------------------------------------------------------- formato
const num = (v, dec = 1) => (v === null || v === undefined ? "—"
  : Number(v).toLocaleString("es-CL", { minimumFractionDigits: dec, maximumFractionDigits: dec }));
const hoyISO = (dias = 0) => { const d = new Date(Date.now() - dias * 864e5); return d.toLocaleDateString("sv-SE"); };
const ESTADOS = {
  normal: { texto: "En rango", icono: "check" },
  atencion: { texto: "Atención", icono: "triangle-alert" },
  alarma: { texto: "Alarma", icono: "bell" },
  "": { texto: "Sin rango", icono: "info" },
};
function chipEstado(estado) {
  const e = ESTADOS[estado] || ESTADOS[""];
  return `<span class="chip-estado ${esc(estado || "sin")}">${linea(e.icono)}${e.texto}</span>`;
}
function duracion(inicio, fin) {
  const min = Math.round(((fin ? new Date(fin) : new Date()) - new Date(inicio)) / 60000);
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60), m = min % 60;
  return h < 48 ? `${h} h${m ? ` ${m} min` : ""}` : `${Math.round(h / 24)} días`;
}
const UNIDAD = { temperatura: "°C", humedad: "%" };

(async function () {
  let filtro = "";
  let pantalla = "resumen";
  let extra = [];
  const main = document.getElementById("contenido");

  const inicio = await iniciarModulo(CLAVE, {
    destinos: [
      { id: "resumen", etiqueta: "Resumen", icono: "layout-dashboard" },
      { id: "alarmas", etiqueta: "Alarmas", icono: "bell" },
      { id: "sensores", etiqueta: "Sensores", icono: "cpu" },
      { id: "eventos", etiqueta: "Eventos", icono: "history" },
      { id: "importaciones", etiqueta: "Archivos", icono: "upload" },
      { id: "acerca", etiqueta: "Acerca del módulo", icono: "info" },
    ],
    accion: { texto: "Importar archivos", icono: "upload", permiso: `${CLAVE}.importar`, alHacer: () => importarArchivos() },
    buscar: { placeholder: "Buscar sensores", alBuscar: (q) => { filtro = q.toLowerCase(); repintar(); } },
    alNavegar: (id, resto) => { pantalla = id; extra = resto; repintar(); },
  });
  if (!inicio) return;
  const { modulo, ir } = inicio;

  function repintar() {
    const p = { resumen: extra[0] ? () => pintarSensor(Number(extra[0])) : pintarResumen, alarmas: pintarAlarmas,
      sensores: pintarSensores, eventos: pintarEventos, importaciones: pintarImportaciones, acerca: pintarAcerca }[pantalla];
    (p || pintarResumen)();
  }
  const coincide = (...textos) => !filtro || textos.join(" ").toLowerCase().includes(filtro);

  /** Carga con los cuatro estados. Devuelve los datos o null si ya pintó un estado de error o sin permiso. */
  async function cargar(contenedor, ruta, queCosa, reintentar) {
    cargando(true, contenedor);
    try { const d = await api(ruta); cargando(false); return d; }
    catch (e) {
      cargando(false);
      if (e.status === 403) estadoSinPermiso(contenedor, "Necesitas el permiso para ver Data+.");
      else if (e.status === 404) estadoVacio(contenedor, "No lo encontramos", "Puede que se haya quitado. Vuelve al resumen.");
      else estadoError(contenedor, `No pudimos cargar ${queCosa}.`, reintentar);
      return null;
    }
  }

  // ---------------------------------------------------------------- resumen
  async function pintarResumen() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Resumen</h1></div><div id="zona"></div>`;
    const zona = document.getElementById("zona");
    const d = await cargar(zona, `${API}/resumen`, "el resumen", pintarResumen);
    if (!d) return;
    const ult = d.ultima_importacion;
    const atrasada = !ult || Date.now() - new Date(ult.hasta) > 864e5;
    let html = `<p class="aviso-suave aviso-datos">${linea(atrasada ? "clock" : "info")}<span>${ult
      ? `Los datos llegan cuando se importa la tarjeta SD de cada equipo. Última importación: ${esc(fechaLocal(ult.creado_en))}, con datos hasta el ${esc(fechaLocal(ult.hasta))}.${atrasada ? " <b>Puede haber mediciones más recientes en los equipos.</b>" : ""}`
      : "Aún no se importan datos. Los datos llegan cuando se importa la tarjeta SD de cada equipo."}</span></p>`;
    if (d.alarmas_pendientes) {
      html += `<button class="tarjeta aviso-alarmas" id="ir-alarmas">${linea("bell")}<span><b>${d.alarmas_pendientes} ${d.alarmas_pendientes === 1 ? "alarma" : "alarmas"} sin revisar</b><br>Revisa qué pasó y registra la acción tomada.</span></button>`;
    }
    const equipos = d.equipos.map((e) => ({ ...e, sensores: e.sensores.filter((s) => coincide(s.nombre, s.ubicacion, e.codigo, s.perfil)) }))
      .filter((e) => e.sensores.length);
    if (!equipos.length) {
      zona.innerHTML = html + `<div id="vacio"></div>`;
      const v = document.getElementById("vacio");
      if (filtro) estadoVacio(v, "Sin resultados", `No hay sensores que coincidan con «${filtro}».`);
      else estadoVacio(v, "Aún no hay sensores", "Aparecerán aquí al importar los archivos de la tarjeta SD de un equipo.",
        modulo.puede(`${CLAVE}.importar`) ? { texto: "Importar archivos", alHacer: importarArchivos } : null);
    } else {
      html += equipos.map((e) => `<section class="grupo-equipo"><h2 class="titulo-seccion">Equipo ${esc(e.codigo)}</h2>
        <div class="grilla-sensores">${e.sensores.map(tarjetaSensor).join("")}</div></section>`).join("");
      zona.innerHTML = html;
    }
    document.getElementById("ir-alarmas")?.addEventListener("click", () => ir("alarmas"));
    zona.querySelectorAll("[data-sensor]").forEach((b) => b.onclick = () => ir(`resumen/${b.dataset.sensor}`));
  }

  function tarjetaSensor(s) {
    const avisos = [];
    if (s.sin_datos) avisos.push(`${linea("clock")}El sensor no reportaba hace más de 75 min`);
    if (s.bateria_baja) avisos.push(`${linea("battery-low")}Batería baja (${s.bateria} %)`);
    return `<button class="tarjeta sensor estado-${esc(s.estado || "sin")}" data-sensor="${s.id}" aria-label="Ver ${esc(s.nombre)}">
      <div class="sensor-cab"><span class="sensor-nombre">${esc(s.nombre)}</span>${chipEstado(s.estado)}</div>
      <div class="sensor-sub">${esc([s.ubicacion, s.perfil].filter(Boolean).join(" · ") || "Sin ubicación")}</div>
      <div class="sensor-valores">
        <span class="valor ${esc(s.estado_t)}">${linea("thermometer")}<b>${num(s.temperatura)}</b> °C</span>
        <span class="valor ${esc(s.estado_h)}">${linea("droplet")}<b>${num(s.humedad, 0)}</b> %</span>
      </div>
      ${avisos.map((a) => `<div class="sensor-aviso">${a}</div>`).join("")}
      <div class="sensor-pie">${s.fecha ? `Último dato: ${esc(fechaLocal(s.fecha))}` : "Sin mediciones"}</div>
    </button>`;
  }

  // ---------------------------------------------------------------- detalle de un sensor (gráfico e informe)
  async function pintarSensor(sid, desde = hoyISO(6), hasta = hoyISO()) {
    main.innerHTML = `<div class="cabecera-pantalla"><button class="btn-icono" id="volver" aria-label="Volver al resumen" title="Volver al resumen">${linea("arrow-left")}</button>
        <h1 class="titulo-pantalla" id="titulo-sensor">Sensor</h1></div>
      <form class="filtros" id="periodo">
        <div class="campo"><input type="date" id="desde" value="${esc(desde)}" max="${hoyISO()}" required><label for="desde">Desde</label></div>
        <div class="campo"><input type="date" id="hasta" value="${esc(hasta)}" max="${hoyISO()}" required><label for="hasta">Hasta</label></div>
        <div class="atajos">
          <button type="button" class="btn btn-borde" data-dias="1">Hoy</button>
          <button type="button" class="btn btn-borde" data-dias="7">7 días</button>
          <button type="button" class="btn btn-borde" data-dias="30">30 días</button>
          <button class="btn">Ver período</button>
        </div>
      </form>
      <div id="zona"></div>`;
    document.getElementById("volver").onclick = () => ir("resumen");
    const f = document.getElementById("periodo");
    f.onsubmit = (e) => { e.preventDefault(); pintarSensor(sid, f.desde.value, f.hasta.value); };
    f.querySelectorAll("[data-dias]").forEach((b) => b.onclick = () => pintarSensor(sid, hoyISO(b.dataset.dias - 1), hoyISO()));
    const zona = document.getElementById("zona");
    const q = `desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}`;
    const d = await cargar(zona, `${API}/sensores/${sid}/serie?${q}`, "las mediciones", () => pintarSensor(sid, desde, hasta));
    if (!d) return;
    const s = d.sensor, p = d.perfil;
    document.getElementById("titulo-sensor").textContent = s.nombre;
    document.title = `${s.nombre} · Data+`;
    const sub = [s.ubicacion, `Equipo ${s.equipo}`, p ? `${p.nombre} (${p.referencia})` : "Sin tipo de almacenamiento"].filter(Boolean).join(" · ");
    if (!d.lecturas.length) {
      zona.innerHTML = `<p class="sensor-sub">${esc(sub)}</p><div id="vacio"></div>`;
      return estadoVacio(document.getElementById("vacio"), "Sin mediciones en este período", "Elige otro período o importa los archivos de la tarjeta SD de este equipo.");
    }
    const T = d.temperatura, H = d.humedad;
    zona.innerHTML = `<p class="sensor-sub">${esc(sub)}</p>
      <div class="acciones-informe">
        <a class="btn btn-borde" href="${API}/sensores/${sid}/csv?${q}" download>${linea("download")}Descargar mediciones</a>
        <button class="btn btn-borde" id="imprimir">${linea("printer")}Imprimir informe</button>
      </div>
      <div class="grilla-estad">
        ${estad("Temperatura mínima", `${num(T.min)} °C`)}${estad("Temperatura máxima", `${num(T.max)} °C`)}
        ${estad("Promedio", `${num(T.promedio)} °C`)}${estad("Temperatura cinética media", `${num(T.mkt)} °C`, "Resume el efecto del calor en el período (USP 1079.2).")}
        ${estad("Tiempo sin alarma de temperatura", T.en_rango === null ? "—" : `${num(T.en_rango)} %`)}
        ${estad("Humedad mín. / máx.", `${num(H.min, 0)} / ${num(H.max, 0)} %`)}
        ${estad("Registro completo", d.cobertura === null ? "—" : `${num(d.cobertura)} %`, d.huecos.length ? `${d.huecos.length} ${d.huecos.length === 1 ? "hueco" : "huecos"} de más de 15 min` : "Sin huecos de más de 15 min")}
      </div>
      <section class="tarjeta bloque-grafico"><h2 class="titulo-seccion">Temperatura (°C)</h2>${grafico(d, "temperatura", "t")}</section>
      ${H.n ? `<section class="tarjeta bloque-grafico"><h2 class="titulo-seccion">Humedad relativa (%)</h2>${grafico(d, "humedad", "h")}</section>` : ""}
      <section class="bloque-excursiones"><h2 class="titulo-seccion">Alarmas del período</h2>
        ${d.excursiones.length ? `<div class="lista">${d.excursiones.map(tarjetaAlarma).join("")}</div>` : `<p class="sensor-sub">No hubo valores fuera del rango de alarma.</p>`}</section>
      <p class="pie-informe">Informe generado el ${esc(fechaLocal(new Date().toISOString()))} desde Data+. Valores con la corrección de calibración ya aplicada.</p>`;
    document.getElementById("imprimir").onclick = () => print();
    activarRevisiones(zona, () => pintarSensor(sid, desde, hasta));
  }
  const estad = (etiqueta, valor, ayuda = "") => `<div class="tarjeta estad"><div class="estad-etq">${esc(etiqueta)}</div>
    <div class="estad-valor">${esc(valor)}</div>${ayuda ? `<div class="estad-ayuda">${esc(ayuda)}</div>` : ""}</div>`;

  /** Gráfico de línea en SVG: banda verde del rango normal, líneas de alarma y cortes donde faltan datos. */
  function grafico(d, campo, v) {
    const puntos = d.lecturas.filter((l) => l[campo] !== null).map((l) => ({ t: new Date(l.fecha).getTime(), y: l[campo] }));
    const p = d.perfil || {};
    const limites = [p[`${v}_alarma_min`], p[`${v}_alarma_max`], p[`${v}_verde_min`], p[`${v}_verde_max`]].filter((x) => x !== null && x !== undefined);
    const ys = puntos.map((q) => q.y).concat(limites);
    let ymin = Math.min(...ys), ymax = Math.max(...ys);
    const margen = Math.max(1, (ymax - ymin) * 0.1); ymin -= margen; ymax += margen;
    const t0 = new Date(d.desde).getTime(), t1 = Math.min(new Date(d.hasta).getTime(), Date.now());
    // El ancho del dibujo sigue al de la pantalla, para que el texto se lea igual en un teléfono (360 px) y en 1440 px.
    const W = Math.round(Math.min(1200, Math.max(280, main.clientWidth - 64))), H = W < 600 ? 200 : 260, L = 44, R = 12, A = 12, B = 28;
    const marcas = W < 600 ? 3 : 5;
    const x = (t) => L + (W - L - R) * (t - t0) / Math.max(1, t1 - t0);
    const y = (val) => A + (H - A - B) * (1 - (val - ymin) / (ymax - ymin));
    let tramos = [], actual = [];
    puntos.forEach((q, i) => {
      if (i && q.t - puntos[i - 1].t > 15 * 60000) { tramos.push(actual); actual = []; }
      actual.push(`${x(q.t).toFixed(1)},${y(q.y).toFixed(1)}`);
    });
    tramos.push(actual);
    const vmin = p[`${v}_verde_min`] ?? ymin, vmax = p[`${v}_verde_max`] ?? ymax;
    const banda = limites.length ? `<rect class="banda-ok" x="${L}" width="${W - L - R}" y="${y(Math.min(vmax, ymax)).toFixed(1)}" height="${(y(Math.max(vmin, ymin)) - y(Math.min(vmax, ymax))).toFixed(1)}"/>` : "";
    const alarmas = [p[`${v}_alarma_min`], p[`${v}_alarma_max`]].filter((a) => a !== null && a !== undefined)
      .map((a) => `<line class="lim-alarma" x1="${L}" x2="${W - R}" y1="${y(a).toFixed(1)}" y2="${y(a).toFixed(1)}"/><text class="etq-lim" x="${W - R - 4}" y="${(y(a) - 4).toFixed(1)}" text-anchor="end">Alarma ${num(a, v === "t" ? 1 : 0)}</text>`).join("");
    const pasos = 4, ejeY = Array.from({ length: pasos + 1 }, (_, i) => ymin + (ymax - ymin) * i / pasos)
      .map((val) => `<line class="rejilla" x1="${L}" x2="${W - R}" y1="${y(val).toFixed(1)}" y2="${y(val).toFixed(1)}"/><text class="etq-eje" x="${L - 6}" y="${(y(val) + 4).toFixed(1)}" text-anchor="end">${num(val, v === "t" ? 1 : 0)}</text>`).join("");
    const dias = (t1 - t0) / 864e5;
    const ejeX = Array.from({ length: marcas }, (_, i) => t0 + (t1 - t0) * i / (marcas - 1)).map((t) => {
      const f = new Date(t);
      const etq = dias <= 2 ? f.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
        : f.toLocaleDateString("es-CL", { day: "numeric", month: "short" });
      return `<text class="etq-eje" x="${x(t).toFixed(1)}" y="${H - 8}" text-anchor="${t === t0 ? "start" : t === t1 ? "end" : "middle"}">${esc(etq)}</text>`;
    }).join("");
    const resumen = `${campo === "temperatura" ? "Temperatura" : "Humedad"} entre ${num(Math.min(...puntos.map((q) => q.y)), 1)} y ${num(Math.max(...puntos.map((q) => q.y)), 1)}`;
    return `<svg class="grafico" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(resumen)}">${banda}${ejeY}${alarmas}
      ${tramos.filter((t) => t.length).map((t) => t.length === 1 ? `<circle class="serie" cx="${t[0].split(",")[0]}" cy="${t[0].split(",")[1]}" r="2"/>` : `<polyline class="serie" points="${t.join(" ")}"/>`).join("")}${ejeX}</svg>
      <div class="leyenda"><span><i class="m-serie"></i>Medición</span>${limites.length ? `<span><i class="m-banda"></i>Rango normal</span><span><i class="m-alarma"></i>Límite de alarma</span>` : ""}</div>`;
  }

  // ---------------------------------------------------------------- alarmas
  let soloPendientes = true;
  async function pintarAlarmas() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Alarmas</h1></div>
      <div class="segmentos" role="group" aria-label="Qué alarmas mostrar">
        <button class="segmento" data-p="1" aria-pressed="${soloPendientes}">Sin revisar</button>
        <button class="segmento" data-p="0" aria-pressed="${!soloPendientes}">Todas</button></div>
      <p class="sensor-sub">Cada alarma es un período en que un sensor estuvo fuera del rango de alarma de su tipo de almacenamiento.</p>
      <div id="zona"></div>`;
    main.querySelectorAll(".segmento").forEach((b) => b.onclick = () => { soloPendientes = b.dataset.p === "1"; pintarAlarmas(); });
    const zona = document.getElementById("zona");
    const lista = await cargar(zona, `${API}/alarmas?pendientes=${soloPendientes ? 1 : 0}`, "las alarmas", pintarAlarmas);
    if (!lista) return;
    const visibles = lista.filter((a) => coincide(a.sensor, a.ubicacion, a.equipo));
    if (!visibles.length) {
      if (filtro) return estadoVacio(zona, "Sin resultados", `No hay alarmas de sensores que coincidan con «${filtro}».`);
      return estadoVacio(zona, soloPendientes ? "No hay alarmas sin revisar" : "Aún no hay alarmas",
        "Cuando un sensor salga del rango de alarma, aparecerá aquí para que registres qué se hizo.");
    }
    zona.innerHTML = `<div class="lista">${visibles.map(tarjetaAlarma).join("")}</div>`;
    activarRevisiones(zona, pintarAlarmas);
  }

  function tarjetaAlarma(a) {
    const u = UNIDAD[a.variable], dec = a.variable === "temperatura" ? 1 : 0;
    const que = `${a.variable === "temperatura" ? "Temperatura" : "Humedad"} ${a.sentido === "alta" ? "sobre" : "bajo"} ${num(a.limite, dec)} ${u}`;
    return `<article class="tarjeta alarma">
      <div class="alarma-cab"><span class="alarma-que">${linea(a.variable === "temperatura" ? "thermometer" : "droplet")}${esc(que)}</span>
        ${a.revisada_por ? `<span class="chip-estado normal">${linea("check")}Revisada</span>` : `<span class="chip-estado alarma">${linea("bell")}Sin revisar</span>`}</div>
      <div class="alarma-sensor">${esc(a.sensor)}${a.ubicacion ? ` · ${esc(a.ubicacion)}` : ""} · Equipo ${esc(a.equipo)}</div>
      <dl class="alarma-datos"><dt>Desde</dt><dd>${esc(fechaLocal(a.inicio))}</dd>
        <dt>Hasta</dt><dd>${a.fin ? esc(fechaLocal(a.fin)) : `Seguía fuera de rango en el último dato importado (${esc(fechaLocal(a.ultimo_dato))})`}</dd>
        <dt>Duración</dt><dd>${esc(duracion(a.inicio, a.fin || a.ultimo_dato))}${a.fin ? "" : " o más"}</dd>
        <dt>Valor extremo</dt><dd>${num(a.extremo, dec)} ${u}</dd></dl>
      ${a.revisada_por ? `<div class="alarma-revision"><b>Revisión de ${esc(a.revisor || "—")}, ${esc(fechaLocal(a.revisada_en))}:</b> ${esc(a.accion)}</div>`
        : modulo.puede(`${CLAVE}.revisar`) ? `<div class="alarma-pie"><button class="btn btn-borde" data-revisar="${a.id}">Registrar revisión</button></div>` : ""}
    </article>`;
  }

  function activarRevisiones(raiz, despues) {
    raiz.querySelectorAll("[data-revisar]").forEach((b) => b.onclick = () => dialogo({
      titulo: "Registrar revisión",
      html: `<p class="dlg-texto">Anota qué se revisó y qué se hizo con lo almacenado (por ejemplo, traslado, cuarentena o aviso a Farmacia).</p>
        <div class="campo"><textarea id="rv-accion" placeholder=" " maxlength="500"></textarea><label for="rv-accion">Acción tomada</label>
        <div class="ayuda">No escribas nombres ni datos de pacientes. La revisión queda con tu nombre y no se puede editar.</div></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar revisión", alHacer: async (v) => {
        try { await api(`${API}/alarmas/${b.dataset.revisar}/revision`, { metodo: "POST", datos: { accion: v.querySelector("#rv-accion").value } }); }
        catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
        toast("Revisión guardada."); despues(); return true;
      } }],
    }));
  }

  // ---------------------------------------------------------------- equipos y sensores
  async function pintarSensores() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Equipos y sensores</h1></div><div id="zona"></div>`;
    const zona = document.getElementById("zona");
    const d = await cargar(zona, `${API}/sensores`, "los equipos", pintarSensores);
    if (!d) return;
    const editar = modulo.puede(`${CLAVE}.configurar`);
    const equipos = d.equipos.map((e) => ({ ...e, sensores: e.sensores.filter((s) => coincide(s.nombre, s.ubicacion, e.codigo, s.ieee)) }))
      .filter((e) => e.sensores.length || coincide(e.codigo));
    if (!equipos.length) {
      if (filtro) return estadoVacio(zona, "Sin resultados", `No hay sensores que coincidan con «${filtro}».`);
      return estadoVacio(zona, "Aún no hay equipos", "Cada equipo aparece la primera vez que se importan sus archivos.");
    }
    zona.innerHTML = equipos.map((e) => `<section class="tarjeta equipo">
      <h2 class="titulo-seccion">Equipo ${esc(e.codigo)}</h2>
      <p class="sensor-sub">Serie ${esc(e.serie || "sin informar")} · Firmware ${esc(e.firmware || "sin informar")} · Último dato ${esc(fechaLocal(e.ultimo_dato))}</p>
      <div class="tabla-envoltura"><table class="tabla"><thead><tr><th scope="col">N.º</th><th scope="col">Sensor</th><th scope="col">Identificador</th>
        <th scope="col">Tipo</th><th scope="col">Ubicación</th><th scope="col">Estado</th>${editar ? '<th scope="col"><span class="sr">Acciones</span></th>' : ""}</tr></thead>
      <tbody>${e.sensores.map((s) => `<tr><td>${s.numero ?? "—"}</td><td>${esc(s.nombre)}</td><td>…${esc(s.ieee.slice(-4))}</td>
        <td>${esc(s.perfil || "—")}</td><td>${esc(s.ubicacion || "—")}</td><td>${s.activo ? "En servicio" : "Fuera de servicio"}</td>
        ${editar ? `<td><button class="btn-icono" data-editar="${s.id}" aria-label="Editar ${esc(s.nombre)}" title="Editar sensor">${linea("pencil")}</button></td>` : ""}</tr>`).join("")}</tbody></table></div>
    </section>`).join("");
    const todos = d.equipos.flatMap((e) => e.sensores);
    zona.querySelectorAll("[data-editar]").forEach((b) => b.onclick = () => editarSensor(todos.find((s) => s.id === Number(b.dataset.editar))));
  }

  function editarSensor(s) {
    dialogo({
      titulo: `Editar ${s.nombre}`,
      html: `<p class="dlg-texto">El nombre y el tipo de almacenamiento se cambian en el equipo, con el Configurador.</p>
        <div class="campo"><input id="es-ubic" placeholder=" " maxlength="80" value="${esc(s.ubicacion)}"><label for="es-ubic">Ubicación</label>
          <div class="ayuda">Por ejemplo: Farmacia central, bodega 2.</div></div>
        <label class="casilla"><input type="checkbox" id="es-fuera" ${s.activo ? "" : "checked"}> Fuera de servicio (no aparece en el resumen ni en las alarmas)</label>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar cambios", alHacer: async (v) => {
        try {
          await api(`${API}/sensores/${s.id}`, { metodo: "PUT", datos: { ubicacion: v.querySelector("#es-ubic").value, activo: !v.querySelector("#es-fuera").checked } });
        } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
        toast("Cambios guardados."); pintarSensores(); return true;
      } }],
    });
  }

  // ---------------------------------------------------------------- eventos de los equipos
  const TIPOS_LEGIBLES = { ARRANQUE: "Arranque", ALARMA_TEMP: "Alarma de temperatura", ALARMA_TEMP_FIN: "Fin de alarma de temperatura",
    ALARMA_HUM: "Alarma de humedad", ALARMA_HUM_FIN: "Fin de alarma de humedad", ALARMA_SILENCIADA: "Alarma silenciada",
    CORTE_ENERGIA: "Corte de luz", ENERGIA_RESTABLECIDA: "Luz restablecida", SENSOR_SIN_DATOS: "Sensor sin datos",
    SIN_REGISTRO: "Filas no registradas", SD_FALLA_PROLONGADA: "Falla de la tarjeta SD", CALIBRACION: "Calibración",
    BATERIA_BAJA: "Batería baja", HORA_CORREGIDA: "Hora corregida", RTC_AUSENTE: "Reloj sin respuesta",
    RTC_RECUPERADO: "Reloj recuperado", SD_ERROR: "Error de la tarjeta SD", SD_INSERTADA: "Tarjeta SD insertada",
    SD_DESMONTADA: "Tarjeta SD retirada", SENSOR_PRIMER_REPORTE: "Primer dato del sensor", RED_AL_ARRANCAR: "Sensores en la red",
    SENSOR_RECUPERADO: "Sensor recuperado", CONFIG_EQUIPO: "Configuración del equipo", CONFIG_SENSOR: "Configuración de sensor" };
  async function pintarEventos(desde = hoyISO(29), hasta = hoyISO(), tipo = "") {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Eventos de los equipos</h1></div>
      <form class="filtros" id="f-ev">
        <div class="campo"><input type="date" id="desde" value="${esc(desde)}" required><label for="desde">Desde</label></div>
        <div class="campo"><input type="date" id="hasta" value="${esc(hasta)}" required><label for="hasta">Hasta</label></div>
        <div class="campo"><select id="tipo"><option value="">Todos</option></select><label for="tipo">Tipo de evento</label></div>
        <div class="atajos"><button class="btn">Ver eventos</button></div></form><div id="zona"></div>`;
    const f = document.getElementById("f-ev");
    f.onsubmit = (e) => { e.preventDefault(); pintarEventos(f.desde.value, f.hasta.value, f.tipo.value); };
    const zona = document.getElementById("zona");
    const q = `desde=${encodeURIComponent(desde)}&hasta=${encodeURIComponent(hasta)}${tipo ? `&tipo=${encodeURIComponent(tipo)}` : ""}`;
    const d = await cargar(zona, `${API}/eventos?${q}`, "los eventos", () => pintarEventos(desde, hasta, tipo));
    if (!d) return;
    f.tipo.innerHTML = `<option value="">Todos</option>` + d.tipos.map((t) => `<option value="${esc(t)}" ${t === tipo ? "selected" : ""}>${esc(TIPOS_LEGIBLES[t] || t)}</option>`).join("");
    const visibles = d.eventos.filter((e) => coincide(e.equipo, e.tipo, e.detalle));
    if (!visibles.length) return estadoVacio(zona, "Sin eventos en este período", "Los eventos llegan junto con los archivos de la carpeta «eventos» de la tarjeta SD.");
    zona.innerHTML = `<div class="tabla-envoltura tarjeta"><table class="tabla"><thead><tr><th scope="col">Fecha</th><th scope="col">Equipo</th><th scope="col">Evento</th><th scope="col">Detalle</th></tr></thead>
      <tbody>${visibles.map((e) => `<tr><td class="nowrap">${esc(fechaLocal(e.fecha))}</td><td>${esc(e.equipo)}</td><td>${esc(TIPOS_LEGIBLES[e.tipo] || e.tipo)}</td><td>${esc(e.detalle)}</td></tr>`).join("")}</tbody></table></div>`;
  }

  // ---------------------------------------------------------------- importaciones
  async function pintarImportaciones() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Archivos importados</h1></div>
      <p class="aviso-suave">${linea("info")}<span>Para importar, saca la tarjeta SD del equipo (mantén el pulsador 3 s), cópiala al PC y elige los archivos de las carpetas «datos» y «eventos». No abras ni guardes los CSV en Excel antes: cambia las firmas.</span></p>
      <div id="zona"></div>`;
    const zona = document.getElementById("zona");
    const lista = await cargar(zona, `${API}/importaciones`, "las importaciones", pintarImportaciones);
    if (!lista) return;
    if (!lista.length) return estadoVacio(zona, "Aún no hay importaciones", "Aquí verás quién importó cada lote de archivos y qué se encontró.",
      modulo.puede(`${CLAVE}.importar`) ? { texto: "Importar archivos", alHacer: importarArchivos } : null);
    const FIRMAS = { sin_verificar: "Sin verificar", correctas: "Correctas", con_problemas: "Con problemas" };
    zona.innerHTML = `<div class="tabla-envoltura tarjeta"><table class="tabla"><thead><tr><th scope="col">Fecha</th><th scope="col">Por</th><th scope="col">Archivos</th>
      <th scope="col">Mediciones nuevas</th><th scope="col">Repetidas</th><th scope="col">Eventos</th><th scope="col">Rechazadas</th><th scope="col">Firmas</th><th scope="col">Datos desde / hasta</th></tr></thead>
      <tbody>${lista.map((i) => `<tr><td class="nowrap">${esc(fechaLocal(i.creado_en))}</td><td>${esc(i.usuario)}</td><td>${i.archivos}</td><td>${i.lecturas_nuevas}</td>
        <td>${i.lecturas_repetidas}</td><td>${i.eventos_nuevos}</td><td>${i.filas_rechazadas}</td>
        <td>${esc(FIRMAS[i.firmas])}${i.problemas_firma ? ` (${i.problemas_firma})` : ""}</td><td class="nowrap">${esc(fechaLocal(i.desde))} – ${esc(fechaLocal(i.hasta))}</td></tr>`).join("")}</tbody></table></div>`;
  }

  function importarArchivos() {
    dialogo({
      titulo: "Importar archivos",
      html: `<p class="dlg-texto">Elige los CSV de las carpetas «datos» y «eventos» de la tarjeta SD (hasta 62 archivos por vez). Lo que ya estaba importado no se duplica.</p>
        <div class="campo-archivo"><label for="im-arch">Archivos CSV</label><input type="file" id="im-arch" accept=".csv,text/csv" multiple></div>
        <div class="campo"><input id="im-equipo" placeholder=" " maxlength="16"><label for="im-equipo">Código del equipo (opcional)</label>
          <div class="ayuda">Solo para archivos antiguos sin la columna Monitor. Por ejemplo: MTH-01.</div></div>
        <div class="campo"><input id="im-clave" type="password" placeholder=" " maxlength="64" autocomplete="off" spellcheck="false"><label for="im-clave">Clave de firma (opcional)</label>
          <div class="ayuda">Con la clave del equipo se revisa que nadie editó, borró ni insertó filas. No se guarda.</div></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Importar archivos", alHacer: async (v) => {
        const archivos = [...v.querySelector("#im-arch").files];
        const zonaError = v.querySelector(".zona-error");
        if (!archivos.length) { mostrarErrorEn(zonaError, "Elige al menos un archivo."); return false; }
        if (archivos.length > 62) { mostrarErrorEn(zonaError, "Elige hasta 62 archivos por vez."); return false; }
        if (archivos.some((a) => a.size > 4e6)) { mostrarErrorEn(zonaError, "Cada archivo debe pesar menos de 4 MB."); return false; }
        let r;
        try {
          const datos = { archivos: await Promise.all(archivos.map(async (a) => ({ nombre: a.name.slice(0, 120), contenido: await a.text() }))),
            equipo: v.querySelector("#im-equipo").value.trim(), clave: v.querySelector("#im-clave").value.trim() };
          r = await api(`${API}/importaciones`, { metodo: "POST", datos });
        } catch (e) { mostrarErrorEn(zonaError, e.message); return false; }
        resultadoImportacion(r);
        return true;
      } }],
    });
  }

  function resultadoImportacion(r) {
    const firmas = r.firmas === null ? "No se verificaron (sin clave)."
      : r.firmas.problemas ? `Hay ${r.firmas.problemas} ${r.firmas.problemas === 1 ? "fila con firma que no coincide" : "filas con firmas que no coinciden"}: se editaron, borraron o insertaron filas. ${r.firmas.detalle.map(esc).join("; ")}`
        : "Correctas: nadie modificó los archivos.";
    dialogo({
      titulo: "Importación lista",
      html: `<dl class="resultado"><dt>Mediciones nuevas</dt><dd>${r.lecturas_nuevas}</dd><dt>Ya importadas</dt><dd>${r.lecturas_repetidas}</dd>
        <dt>Eventos nuevos</dt><dd>${r.eventos_nuevos}</dd><dt>Filas que no se pudieron leer</dt><dd>${r.filas_rechazadas}</dd>
        <dt>Firmas</dt><dd>${firmas}</dd></dl>
        ${r.archivos_no_reconocidos.length ? `<p class="dlg-texto">No se importaron: ${r.archivos_no_reconocidos.map(esc).join("; ")}.</p>` : ""}`,
      acciones: [{ texto: "Ver resumen", valor: null, alHacer: () => { ir("resumen"); } }],
    });
  }

  // ---------------------------------------------------------------- acerca (transparencia)
  async function pintarAcerca() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Acerca del módulo</h1></div>
      <section class="tarjeta ficha"><h2 class="titulo-seccion">${esc(modulo.nombre)}</h2>
        <dl><dt>Qué hace</dt><dd>${esc(modulo.descripcion)}</dd>
          <dt>Cómo llegan los datos</dt><dd>Importando los archivos de la tarjeta SD de cada equipo. Los valores ya traen la corrección de calibración.</dd>
          <dt>Para qué usa datos</dt><dd>${esc(modulo.finalidad)}</dd>
          <dt>Cuánto se guardan</dt><dd>5 años. Después se eliminan solos.</dd>
          <dt>Versión</dt><dd>${esc(modulo.version)}</dd></dl></section>
      <section class="tarjeta ficha" id="rangos"><h2 class="titulo-seccion">Rangos por tipo de almacenamiento</h2><div id="zona"></div></section>`;
    const zona = document.getElementById("zona");
    const d = await cargar(zona, `${API}/sensores`, "los rangos", pintarAcerca);
    if (!d) return;
    const r = (a, b, u, dec) => a === null && b === null ? "—" : a === null ? `hasta ${num(b, dec)} ${u}` : b === null ? `desde ${num(a, dec)} ${u}` : `${num(a, dec)} a ${num(b, dec)} ${u}`;
    const fuera = (a, b, u, dec) => [a !== null ? `bajo ${num(a, dec)} ${u}` : "", b !== null ? `sobre ${num(b, dec)} ${u}` : ""].filter(Boolean).join(" o ");
    zona.innerHTML = `<div class="tabla-envoltura"><table class="tabla"><thead><tr><th scope="col">Tipo</th><th scope="col">Temperatura normal</th><th scope="col">Alarma de temperatura</th>
      <th scope="col">Humedad normal</th><th scope="col">Alarma de humedad</th></tr></thead><tbody>
      ${d.perfiles.map((p) => `<tr><td>${esc(p.nombre)}<br><small>${esc(p.referencia)}</small></td><td>${r(p.t_verde_min, p.t_verde_max, "°C", 1)}</td>
        <td>${fuera(p.t_alarma_min, p.t_alarma_max, "°C", 1)}</td><td>${r(p.h_verde_min, p.h_verde_max, "%", 0)}</td><td>${fuera(p.h_alarma_min, p.h_alarma_max, "%", 0)}</td></tr>`).join("")}
      </tbody></table></div><p class="sensor-sub">Entre el rango normal y el de alarma, el valor se marca como «Atención».</p>`;
  }
})();
