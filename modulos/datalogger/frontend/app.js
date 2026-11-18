// F+data según las directrices de diseño (docs/diseno/, Parte 3): iniciarModulo, cuatro estados, esc() y api().
// Pantallas: Resumen (y detalle de un sensor en /resumen/<id>), Alarmas, Equipos y sensores, Eventos,
// Importaciones, Configurador (equipo conectado por USB, ver monitor_usb.js) y Acerca del módulo. Los gráficos son SVG propios: sin bibliotecas ni recursos de Internet.
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
  usb: '<circle cx="10" cy="7" r="1"/><circle cx="4" cy="20" r="1"/><path d="M4.7 19.3 19 5"/><path d="m21 3-3 1 2 2Z"/><path d="M9.26 7.68 5 12l2 5"/><path d="m10 14 5 2 3.5-3.5"/><path d="m18 12 1-1 1 1-1 1Z"/>',
  "refresh-cw": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
  "key-round": '<path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/><circle cx="16.5" cy="7.5" r=".5"/>',
  wifi: '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
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
      { id: "configurador", etiqueta: "Configurador", icono: "usb", permiso: `${CLAVE}.equipos` },
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
      sensores: pintarSensores, eventos: pintarEventos, importaciones: pintarImportaciones, configurador: pintarConfigurador,
      acerca: pintarAcerca }[pantalla];
    (p || pintarResumen)();
  }
  const coincide = (...textos) => !filtro || textos.join(" ").toLowerCase().includes(filtro);

  /** Carga con los cuatro estados. Devuelve los datos o null si ya pintó un estado de error o sin permiso. */
  async function cargar(contenedor, ruta, queCosa, reintentar) {
    cargando(true, contenedor);
    try { const d = await api(ruta); cargando(false); return d; }
    catch (e) {
      cargando(false);
      if (e.status === 403) estadoSinPermiso(contenedor, "Necesitas el permiso para ver F+data.");
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
    document.title = `${s.nombre} · F+data`;
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
      <p class="pie-informe">Informe generado el ${esc(fechaLocal(new Date().toISOString()))} desde F+data. Valores con la corrección de calibración ya aplicada.</p>`;
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

  // ---------------------------------------------------------------- configurador (equipo conectado por USB)
  // Lo mismo que el Configurador de Windows de Monitor_TH, salvo instalar firmware (eso sigue en la aplicación .exe).
  // La conexión la hace el navegador; al portal solo llega qué se cambió, para la bitácora.
  const AREAS = { MED: "Medicamentos", EST: "Material estéril" };
  const CORR_MAX_T = 3, CORR_MAX_H = 15;
  const consola = [];
  const usb = typeof MonitorUSB === "undefined" ? null : new MonitorUSB((l) => {
    consola.push(l); if (consola.length > 200) consola.shift();
    const c = document.getElementById("usb-consola");
    if (c) { c.textContent = consola.join("\n"); c.scrollTop = c.scrollHeight; }
  });
  let equipoUSB = null;            // { info, equipo, sensores, vivos, wifi } del monitor conectado
  let seccionUSB = "equipo";
  let ocupadoUSB = false;
  if (usb) usb.alDesconectar = () => { equipoUSB = null; toast("Se desconectó el monitor."); if (pantalla === "configurador") pintarConfigurador(); };

  const codigoBitacora = (c) => String(c || "").replace(/[^A-Za-z0-9 _.-]/g, "-").trim().slice(0, 16) || "sin-codigo";
  async function registrar(accion) {
    const i = equipoUSB?.info || {};
    try {
      await api(`${API}/configurador/registro`, { metodo: "POST", datos: { accion, equipo: codigoBitacora(i.codigo),
        serie: /^[0-9A-Fa-f]{8,32}$/.test(i.serie || "") ? i.serie : "", firmware: String(i.firmware || "").replace(/[^0-9A-Za-z._-]/g, "").slice(0, 16) } });
    } catch (_) { toast("El cambio se hizo en el monitor, pero no quedó en la bitácora del portal."); }
  }

  /** Ejecuta algo con el monitor: barra de progreso, mensaje de qué está haciendo y error legible. */
  async function conMonitor(descripcion, fn, despues = leerTodo) {
    if (ocupadoUSB) return;
    ocupadoUSB = true;
    const estado = document.getElementById("usb-estado");
    if (estado) estado.textContent = `${descripcion}…`;
    main.querySelectorAll(".zona-usb button").forEach((b) => { b.disabled = true; });
    cargando(true);
    let ok = true;
    try { await fn(); }
    catch (e) { ok = false; toast(e instanceof ErrorMonitor ? e.message : "No pudimos hablar con el monitor. Revisa el cable y vuelve a conectarlo."); }
    finally { cargando(false); ocupadoUSB = false; }
    if (pantalla !== "configurador") return;
    if (!ok || !usb.abierto) return pintarConfigurador();
    if (despues) return despues();
    // Sin volver a leer: la pantalla queda como está (por ejemplo, con los eventos recién leídos)
    main.querySelectorAll(".zona-usb button").forEach((b) => { b.disabled = false; });
    const i = equipoUSB?.info;
    if (estado && i) estado.textContent = `Serie ${i.serie} · Firmware ${i.firmware}`;
  }

  async function leerTodo() {
    await conMonitor("Leyendo el monitor", async () => {
      const info = await usb.info();
      const { equipo, sensores } = await usb.config();
      const vivos = await usb.sensores();
      const wifi = await usb.wifi();
      equipoUSB = { info, equipo, sensores, vivos, wifi };
    }, () => pintarConfigurador());
  }

  async function conectar() {
    if (usb.abierto) { await usb.cerrar(); equipoUSB = null; return pintarConfigurador(); }
    try { await usb.abrir(); }
    catch (e) {
      if (e?.name !== "NotFoundError") toast("No se pudo abrir el puerto. Cierra el Configurador de Windows u otro programa que lo esté usando.");
      return;
    }
    try { await usb.info(); }
    catch (_) {
      await usb.cerrar();
      return dialogo({ titulo: "El equipo no respondió", html: `<p class="dlg-texto">No responde como un Monitor T/H con firmware 2.0 o posterior.
        Si es un monitor con firmware antiguo, instálale el firmware nuevo con el Configurador de Windows y vuelve a intentarlo.</p>`,
        acciones: [{ texto: "Entendido", valor: null }] });
    }
    await leerTodo();
  }

  function pintarConfigurador() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Configurador de equipos</h1></div><div id="zona" class="zona-usb"></div>`;
    const zona = document.getElementById("zona");
    if (!modulo.puede(`${CLAVE}.equipos`)) return estadoSinPermiso(zona, "Necesitas el permiso para configurar equipos de F+data.");
    if (!usb || !MonitorUSB.disponible()) {
      return estadoVacio(zona, "Este navegador no se puede conectar por USB",
        "Abre F+data en Google Chrome o Microsoft Edge, en el PC donde está conectado el monitor. Si entras por una dirección que no es localhost, debe ser https.");
    }
    const i = equipoUSB?.info;
    zona.innerHTML = `<section class="tarjeta conexion">
        <div class="conexion-cab"><div><div class="sensor-nombre">${i ? `Equipo ${esc(i.codigo)}` : "Sin monitor conectado"}</div>
          <div class="sensor-sub" id="usb-estado" role="status">${i ? `Serie ${esc(i.serie)} · Firmware ${esc(i.firmware)}`
            : "Conecta el monitor al PC con el cable USB y pulsa «Conectar monitor». Elige el puerto que dice «USB JTAG/serial debug unit»."}</div></div>
          <button class="btn ${i ? "btn-borde" : ""}" id="usb-conectar">${linea("usb")}${i ? "Desconectar" : "Conectar monitor"}</button></div>
      </section><div id="usb-cuerpo"></div>`;
    document.getElementById("usb-conectar").onclick = conectar;
    const cuerpo = document.getElementById("usb-cuerpo");
    if (!i) {
      cuerpo.innerHTML = `<p class="aviso-suave">${linea("info")}<span>Desde aquí se hace lo mismo que con el Configurador de Windows: hora, sensores, calibración, alarmas, WiFi, eventos, respaldo y clave de firma.
        Para instalar o actualizar el firmware sigue usando el Configurador de Windows. Cada cambio queda en la bitácora del portal y en los eventos del monitor.</span></p>`;
      return;
    }
    const secciones = [["equipo", "Equipo"], ["config", "Configuración"], ["sensores", "Sensores"], ["registro", "Registro"]];
    cuerpo.innerHTML = `<div class="segmentos" role="group" aria-label="Sección del configurador">
      ${secciones.map(([id, t]) => `<button class="segmento" data-s="${id}" aria-pressed="${seccionUSB === id}">${t}</button>`).join("")}</div><div id="usb-seccion"></div>`;
    cuerpo.querySelectorAll("[data-s]").forEach((b) => b.onclick = () => { seccionUSB = b.dataset.s; pintarConfigurador(); });
    const sec = document.getElementById("usb-seccion");
    ({ equipo: seccionEquipo, config: seccionConfig, sensores: seccionSensoresUSB, registro: seccionRegistro }[seccionUSB])(sec);
  }

  const fila = (etq, valor, tono = "") => `<dt>${esc(etq)}</dt><dd class="${tono ? `tono-${tono}` : ""}">${tono === "alerta" ? linea("triangle-alert") : ""}${esc(valor)}</dd>`;

  function textoWifi(w) {
    if (w === null) return ["Este firmware no tiene WiFi (desde la versión 2.1).", ""];
    if (!w.configurado) return ["No configurado", ""];
    if (w.conectado) {
      const t = `Conectado a ${w.red} (IP ${w.ip}, señal ${w.rssi} dBm). Envíos correctos: ${w.envios_ok}, con falla: ${w.envios_falla}`;
      return w.servidor ? [t, "ok"] : [`${t}. Falta el servidor: no se envía nada`, "aviso"];
    }
    if (w.activo) return [`Sin conexión con ${w.red} (revisa la red y la clave)`, "alerta"];
    return [`Apagado (memoria libre ${w.memoria_libre || 0} bytes; ver eventos)`, "alerta"];
  }

  function seccionEquipo(sec) {
    const { info: i, wifi } = equipoUSB;
    const dif = Math.round(i.unix - Date.now() / 1000);
    const energia = { sin_divisor: ["No detecta cortes de luz (divisor no conectado)", ""], red: ["Con red eléctrica", "ok"],
      bateria: ["Sin luz: funcionando con batería", "alerta"] }[i.energia] || [String(i.energia), ""];
    sec.innerHTML = `<div class="acciones-informe">
        <button class="btn" id="u-leer">${linea("refresh-cw")}Actualizar</button>
        <button class="btn btn-borde" id="u-hora">${linea("clock")}Poner la hora del PC</button>
        <button class="btn btn-borde" id="u-emparejar">${linea("wifi")}Abrir red para emparejar (3 min)</button>
        <button class="btn btn-borde" id="u-reiniciar">${linea("refresh-cw")}Reiniciar monitor</button></div>
      <div class="grilla-usb">
        <section class="tarjeta ficha"><h2 class="titulo-seccion">Identificación</h2><dl>
          ${fila("Código", i.codigo)}${fila("Número de serie", i.serie)}${fila("Firmware", i.firmware)}
          ${fila("Pantalla", i.pantalla === 2 ? "2,4 pulgadas (240 × 320)" : "1,9 pulgadas (170 × 320)")}</dl></section>
        <section class="tarjeta ficha"><h2 class="titulo-seccion">Funcionamiento</h2><dl>
          ${i.hora_valida ? fila("Hora del monitor", `${i.hora} (diferencia con el PC: ${dif > 0 ? "+" : ""}${dif} s)`, Math.abs(dif) > 120 ? "alerta" : "")
            : fila("Hora del monitor", "Sin hora: pulsa «Poner la hora del PC» (sin hora no se graban datos)", "alerta")}
          ${i.sd ? fila("Tarjeta SD", "Grabando", "ok") : fila("Tarjeta SD", `No disponible (${i.pendientes} filas esperando en la memoria)`, "alerta")}
          ${fila("Respaldo de energía", `${energia[0]} (${i.energia_mv} mV)`, energia[1])}
          ${fila("Sensores emparejados", String(i.sensores))}
          ${fila("Emparejamiento", i.emparejando ? `Red abierta ${i.emparejando} s más` : "Red cerrada", i.emparejando ? "aviso" : "")}
          ${fila("WiFi", ...textoWifi(wifi))}</dl></section></div>
      <p class="aviso-suave">${linea("info")}<span>Para emparejar un sensor: pulsa «Abrir red para emparejar», acerca el sensor al monitor y mantén su botón unos 5 s hasta que el LED parpadee. Después, en Sensores, ponle nombre, tipo de almacenamiento y corrección.</span></p>`;
    document.getElementById("u-leer").onclick = () => leerTodo();
    document.getElementById("u-hora").onclick = () => conMonitor("Poniendo la hora", async () => { await usb.ponerHora(); await registrar("hora"); });
    document.getElementById("u-emparejar").onclick = () => conMonitor("Abriendo la red", async () => {
      await usb.emparejar(); await registrar("emparejar");
      toast("Red abierta por 3 minutos. Mantén el botón del sensor unos 5 s hasta que parpadee.", 8000);
    });
    document.getElementById("u-reiniciar").onclick = async () => {
      if (!await confirmarDestructivo({ titulo: "¿Reiniciar el monitor?", texto: "Vuelve en unos segundos. Después conviene pulsar el botón de cada sensor para que se reconecten de inmediato.", verbo: "Reiniciar monitor" })) return;
      await conMonitor("Reiniciando el monitor (vuelve en unos segundos)", async () => { await registrar("reiniciar"); await usb.reiniciarYReconectar(); });
    };
  }

  function seccionConfig(sec) {
    const { equipo: e, wifi } = equipoUSB;
    const [estadoWifi, tonoWifi] = textoWifi(wifi);
    sec.innerHTML = `<form class="tarjeta form-usb" id="f-equipo"><h2 class="titulo-seccion">Equipo</h2>
        <div class="campo"><input id="u-codigo" placeholder=" " maxlength="15" value="${esc(e.codigo || "")}" required><label for="u-codigo">Código del equipo</label>
          <div class="ayuda">Por ejemplo MTH-03. Aparece en la pantalla y en los registros. Letras, números y guion.</div></div>
        <fieldset class="grupo-opciones"><legend>Modelo de pantalla</legend>
          <label class="casilla"><input type="radio" name="u-pantalla" value="1" ${e.pantalla !== 2 ? "checked" : ""}> 1,9 pulgadas (170 × 320)</label>
          <label class="casilla"><input type="radio" name="u-pantalla" value="2" ${e.pantalla === 2 ? "checked" : ""}> 2,4 pulgadas (240 × 320)</label></fieldset>
        <fieldset class="grupo-opciones"><legend>Alarmas que suenan</legend>
          <label class="casilla"><input type="checkbox" id="u-buz-t" ${e.buzzer_temp ? "checked" : ""}> Temperatura</label>
          <label class="casilla"><input type="checkbox" id="u-buz-h" ${e.buzzer_hum ? "checked" : ""}> Humedad</label>
          <div class="ayuda">Las alarmas que no suenan igual se ven en la pantalla y quedan en los eventos. La alerta de la tarjeta SD suena siempre.</div></fieldset>
        <p class="sensor-sub">Si cambias el modelo de pantalla, el monitor se reinicia.</p>
        <div class="zona-error"></div><div class="pie-form"><button class="btn">Guardar en el monitor</button></div></form>
      <form class="tarjeta form-usb" id="f-wifi"><h2 class="titulo-seccion">WiFi (envío de lecturas)</h2>
        <p class="sensor-sub">Opcional, firmware 2.1 o posterior. Cada minuto el monitor envía sus lecturas al servidor. Sin WiFi funciona igual (pantalla, alarmas y SD).
          F+data todavía no recibe esos envíos: falta la credencial de equipo que debe preparar la Unidad de Innovación y Desarrollo.</p>
        <p class="estado-wifi ${tonoWifi ? `tono-${tonoWifi}` : ""}">${esc(estadoWifi)}</p>
        ${wifi === null ? "" : `<div class="campo"><input id="u-red" placeholder=" " maxlength="32" value="${esc(wifi.red || "")}" autocomplete="off"><label for="u-red">Red (nombre)</label></div>
        <div class="campo"><input id="u-clave" type="password" placeholder=" " maxlength="63" autocomplete="new-password"><label for="u-clave">Clave de la red</label>
          <div class="ayuda">En blanco se conserva la guardada.</div></div>
        <div class="campo"><input id="u-servidor" placeholder=" " maxlength="100" value="${esc(wifi.servidor || "")}" autocomplete="off" spellcheck="false"><label for="u-servidor">Servidor</label>
          <div class="ayuda">Por ejemplo http://192.168.0.3:8080/monitor</div></div>
        <div class="zona-error"></div><div class="pie-form"><button type="button" class="btn btn-texto" id="u-wifi-borrar">Desactivar WiFi</button><button class="btn">Guardar WiFi</button></div>`}</form>`;

    const fe = document.getElementById("f-equipo");
    fe.onsubmit = async (ev) => {
      ev.preventDefault();
      const zonaError = fe.querySelector(".zona-error");
      const codigo = textoMonitor(fe.querySelector("#u-codigo").value, 15);
      if (!codigo || !/^[A-Za-z0-9 _.-]+$/.test(codigo)) return mostrarErrorEn(zonaError, "Escribe el código del equipo con letras, números y guion (por ejemplo MTH-03).");
      mostrarErrorEn(zonaError, "");
      const nuevo = { codigo, pantalla: Number(fe.querySelector("[name=u-pantalla]:checked").value),
        buzzer_temp: fe.querySelector("#u-buz-t").checked, buzzer_hum: fe.querySelector("#u-buz-h").checked };
      const cambiaPantalla = nuevo.pantalla !== e.pantalla;
      if (cambiaPantalla && !await confirmarDestructivo({ titulo: "¿Cambiar el modelo de pantalla?", texto: "El monitor se reiniciará y vuelve en unos segundos. Después conviene pulsar el botón de cada sensor.", verbo: "Guardar y reiniciar" })) return;
      await conMonitor("Guardando en el monitor", async () => {
        if (cambiaPantalla) await usb.reiniciarYReconectar(() => usb.ponerEquipo(nuevo));
        else await usb.ponerEquipo(nuevo);
        equipoUSB.info.codigo = codigo;
        await registrar("equipo");
        toast("Configuración guardada en el monitor.");
      });
    };
    if (wifi === null) return;
    const fw = document.getElementById("f-wifi");
    fw.onsubmit = async (ev) => {
      ev.preventDefault();
      const zonaError = fw.querySelector(".zona-error");
      const red = fw.querySelector("#u-red").value.trim(), clave = fw.querySelector("#u-clave").value, servidor = fw.querySelector("#u-servidor").value.trim();
      const error = !red ? "Escribe el nombre de la red."
        : (red + clave + servidor).includes("|") ? "La red, la clave y el servidor no pueden tener el carácter |."
        : servidor && !/^https?:\/\//.test(servidor) ? "El servidor debe empezar con http:// o https:// (por ejemplo http://192.168.0.3:8080/monitor)."
        : !clave && red !== wifi.red ? "Escribe la clave de la red." : "";
      if (error) return mostrarErrorEn(zonaError, error);
      mostrarErrorEn(zonaError, "");
      await conMonitor("Guardando el WiFi y conectando", async () => {
        await usb.ponerWifi(red, clave, servidor);
        await registrar("wifi");
        await new Promise((r) => setTimeout(r, 8000));   // tiempo para que se conecte antes de volver a leer
      });
    };
    document.getElementById("u-wifi-borrar").onclick = async () => {
      if (!await confirmarDestructivo({ titulo: "¿Desactivar el WiFi?", texto: "Se borran la red, la clave y el servidor guardados en el monitor.", verbo: "Desactivar WiFi" })) return;
      await conMonitor("Desactivando el WiFi", async () => { await usb.borrarWifi(); await registrar("wifi_borrado"); });
    };
  }

  function sensoresUSB() {
    const { sensores: cfg, vivos } = equipoUSB;
    const porIeee = Object.fromEntries(cfg.map((s) => [s.ieee4, s]));
    const filas = vivos.map((v) => ({ ...v, cfg: porIeee[v.ieee4] || null, vivo: true }));
    cfg.filter((s) => !vivos.some((v) => v.ieee4 === s.ieee4)).forEach((s) => filas.push({ ieee4: s.ieee4, nombre: s.nombre, cfg: s, vivo: false }));
    return filas;
  }

  function seccionSensoresUSB(sec) {
    const filas = sensoresUSB();
    const corr = (c) => c ? `T ${c.corr_t >= 0 ? "+" : ""}${num(c.corr_t)} / HR ${c.corr_h >= 0 ? "+" : ""}${c.corr_h}` : "—";
    const edad = (e) => e === undefined || e < 0 ? "—" : e >= 60 ? `hace ${Math.floor(e / 60)} min` : "ahora";
    sec.innerHTML = `<div class="acciones-informe"><button class="btn" id="u-leer">${linea("refresh-cw")}Actualizar</button></div>
      ${!filas.length ? `<div id="vacio"></div>` : `<div class="tabla-envoltura tarjeta"><table class="tabla"><thead><tr><th scope="col">N.º</th><th scope="col">IEEE</th>
        <th scope="col">Nombre</th><th scope="col">Tipo</th><th scope="col">T (°C)</th><th scope="col">HR (%)</th><th scope="col">Batería</th>
        <th scope="col">Último dato</th><th scope="col">Corrección</th><th scope="col">Calibrado</th><th scope="col">Estado</th><th scope="col"><span class="sr">Acciones</span></th></tr></thead>
        <tbody>${filas.map((f) => `<tr class="${f.vivo ? "" : "apagado"}"><td>${f.n ?? "—"}</td><td>${esc(f.ieee4)}</td><td>${esc(f.nombre)}</td>
          <td>${f.cfg ? esc(AREAS[f.cfg.perfil] || f.cfg.perfil) : "Medicamentos (por defecto)"}</td>
          <td>${f.vivo ? num(f.t) : "—"}</td><td>${f.vivo ? num(f.h, 0) : "—"}</td><td>${f.vivo && f.bat !== null ? `${f.bat} %` : "—"}</td>
          <td class="nowrap">${f.vivo ? edad(f.edad) : "—"}</td><td class="nowrap">${corr(f.cfg)}</td><td>${esc(f.cfg?.calibrado || "—")}</td>
          <td>${f.vivo && f.alarma ? `<span class="chip-estado alarma">${linea("bell")}En alarma</span>` : f.vivo ? (f.cfg ? "Configurado" : "Sin configurar") : f.cfg.oculto ? "Oculto" : "No emparejado"}</td>
          <td class="nowrap"><button class="btn-icono" data-editar="${esc(f.ieee4)}" aria-label="Editar sensor ${esc(f.ieee4)}" title="Editar sensor">${linea("pencil")}</button>
            ${f.cfg ? `<button class="btn-icono" data-quitar="${esc(f.ieee4)}" aria-label="Quitar la configuración del sensor ${esc(f.ieee4)}" title="Quitar su configuración">${linea("trash")}</button>` : ""}</td></tr>`).join("")}</tbody></table></div>`}`;
    document.getElementById("u-leer").onclick = () => leerTodo();
    if (!filas.length) return estadoVacio(document.getElementById("vacio"), "El monitor no tiene sensores", "Empareja uno desde la sección Equipo con «Abrir red para emparejar».");
    sec.querySelectorAll("[data-editar]").forEach((b) => b.onclick = () => editarSensorUSB(filas.find((f) => f.ieee4 === b.dataset.editar)));
    sec.querySelectorAll("[data-quitar]").forEach((b) => b.onclick = async () => {
      if (!await confirmarDestructivo({ titulo: `¿Quitar la configuración del sensor ${b.dataset.quitar}?`, texto: "Vuelve al nombre y tipo por defecto y queda sin corrección de calibración.", verbo: "Quitar configuración" })) return;
      await conMonitor("Quitando la configuración", async () => { await usb.borrarSensor(b.dataset.quitar); await registrar("sensor_quitado"); });
    });
  }

  function editarSensorUSB(f) {
    const d = f.cfg || { ieee4: f.ieee4, nombre: f.nombre || "", perfil: "MED", corr_t: 0, corr_h: 0, calibrado: "", oculto: 0 };
    const decimal = (x) => String(x).replace(".", ",");
    dialogo({
      titulo: `Sensor ${d.ieee4}`,
      html: `<p class="dlg-texto">Los cambios se guardan en el monitor y quedan en sus eventos.</p>
        <div class="campo"><input id="us-nombre" placeholder=" " maxlength="30" value="${esc(d.nombre)}"><label for="us-nombre">Nombre en pantalla</label><div class="ayuda">Hasta 30 caracteres, sin tildes.</div></div>
        <div class="campo"><select id="us-perfil">${Object.entries(AREAS).map(([k, v]) => `<option value="${k}" ${d.perfil === k ? "selected" : ""}>${v}</option>`).join("")}</select><label for="us-perfil">Tipo de almacenamiento</label></div>
        <label class="casilla"><input type="checkbox" id="us-oculto" ${d.oculto ? "checked" : ""}> Oculto (fuera de servicio: el monitor lo ignora)</label>
        <div class="fila-campos"><div class="campo"><input id="us-ct" placeholder=" " inputmode="decimal" value="${esc(decimal(Number(d.corr_t).toFixed(1)))}"><label for="us-ct">Corrección de temperatura (°C)</label></div>
          <div class="campo"><input id="us-ch" placeholder=" " inputmode="numeric" value="${esc(String(d.corr_h))}"><label for="us-ch">Corrección de humedad (% HR, entero)</label></div></div>
        <div class="campo"><input id="us-cal" placeholder=" " maxlength="23" value="${esc(d.calibrado || "")}"><label for="us-cal">Fecha y nota de calibración</label><div class="ayuda">Por ejemplo: 2026-10-08 (solo T).</div></div>
        <p class="dlg-texto">La corrección se suma a lo que mide el sensor: es el promedio de (referencia − sensor) del formulario de calibración (Anexo 1). Límites: ±3 °C y ±15 % HR; si se necesita más, el sensor debe reemplazarse.</p>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar en el monitor", alHacer: async (v) => {
        const zonaError = v.querySelector(".zona-error");
        const ct = Number(v.querySelector("#us-ct").value.replace(",", ".")), ch = Number(v.querySelector("#us-ch").value.replace(",", "."));
        if (!Number.isFinite(ct) || !Number.isFinite(ch) || v.querySelector("#us-ct").value.trim() === "" || v.querySelector("#us-ch").value.trim() === "") {
          mostrarErrorEn(zonaError, "Las correcciones deben ser números (por ejemplo 0,2)."); return false;
        }
        if (Math.abs(ct) > CORR_MAX_T || Math.abs(ch) > CORR_MAX_H) {
          mostrarErrorEn(zonaError, "Corrección fuera del límite (±3 °C y ±15 % HR). Según el instructivo, el sensor debe reemplazarse."); return false;
        }
        const s = { ieee4: d.ieee4, nombre: textoMonitor(v.querySelector("#us-nombre").value, 30), perfil: v.querySelector("#us-perfil").value,
          corr_t: Math.round(ct * 10) / 10, corr_h: Math.trunc(ch), calibrado: textoMonitor(v.querySelector("#us-cal").value, 23), oculto: v.querySelector("#us-oculto").checked };
        conMonitor("Guardando el sensor", async () => { await usb.ponerSensor(s); await registrar("sensor"); toast("Sensor guardado en el monitor."); });
        return true;
      } }],
    });
  }

  function descargar(nombre, texto, tipo) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([texto], { type: tipo }));
    a.download = nombre;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  const nombreArchivo = (t) => t.replace(/[^A-Za-z0-9_.-]/g, "_");

  function seccionRegistro(sec) {
    sec.innerHTML = `<div class="acciones-informe">
        <button class="btn" id="u-eventos">${linea("history")}Ver últimos eventos</button>
        <button class="btn btn-borde" id="u-guardar">${linea("download")}Guardar configuración en archivo</button>
        <button class="btn btn-borde" id="u-cargar">${linea("upload")}Cargar configuración desde archivo</button>
        <button class="btn btn-borde" id="u-clave">${linea("key-round")}Ver clave de firma</button>
        <input type="file" id="u-archivo" accept=".json,application/json" class="oculto"></div>
      <section class="tarjeta bloque-usb"><h2 class="titulo-seccion">Eventos desde el último arranque del monitor</h2><pre class="texto-usb" id="usb-eventos">Pulsa «Ver últimos eventos».</pre></section>
      <section class="tarjeta bloque-usb"><h2 class="titulo-seccion">Consola del monitor</h2><p class="sensor-sub">Lo que el monitor escribe por USB.</p>
        <pre class="texto-usb tenue" id="usb-consola" tabindex="0" aria-label="Consola del monitor">${esc(consola.join("\n"))}</pre></section>`;
    document.getElementById("u-eventos").onclick = () => conMonitor("Leyendo eventos", async () => {
      const ev = await usb.eventos();
      document.getElementById("usb-eventos").textContent = ev.join("\n") || "(sin eventos)";
    }, null);
    document.getElementById("u-guardar").onclick = () => conMonitor("Leyendo la configuración", async () => {
      const { equipo, sensores } = await usb.config();
      const i = equipoUSB.info, hoy = new Date();
      const datos = { guardado: `${hoy.toLocaleDateString("sv-SE")} ${hoy.toLocaleTimeString("es-CL", { hourCycle: "h23" })}`, serie: i.serie, firmware: i.firmware, equipo, sensores };
      descargar(nombreArchivo(`config_${i.codigo}_${hoy.toLocaleDateString("sv-SE")}.json`), JSON.stringify(datos, null, 2), "application/json");
    }, null);
    const entrada = document.getElementById("u-archivo");
    document.getElementById("u-cargar").onclick = () => entrada.click();
    entrada.onchange = async () => {
      const archivo = entrada.files[0];
      entrada.value = "";
      if (!archivo) return;
      let datos;
      try {
        datos = JSON.parse(await archivo.text());
        if (!datos.equipo?.codigo || !Array.isArray(datos.sensores)) throw new Error();
      } catch (_) { return toast("El archivo no es una configuración válida del Monitor T/H."); }
      const i = equipoUSB.info;
      let texto = `Se aplicará al monitor conectado (${i.codigo}) la configuración de ${datos.equipo.codigo} con ${datos.sensores.length} ${datos.sensores.length === 1 ? "sensor" : "sensores"}.`;
      if (datos.serie && datos.serie !== i.serie) texto += ` Ojo: el archivo es de otra placa (serie ${datos.serie}). Las correcciones de calibración son de cada sensor: revisa que correspondan.`;
      if (!await confirmarDestructivo({ titulo: "¿Cargar la configuración?", texto, verbo: "Aplicar al monitor" })) return;
      const eq = datos.equipo;
      const nuevo = { codigo: textoMonitor(eq.codigo, 15), pantalla: Number(eq.pantalla) === 2 ? 2 : 1, buzzer_temp: !!eq.buzzer_temp, buzzer_hum: !!eq.buzzer_hum };
      await conMonitor("Aplicando la configuración", async () => {
        for (const s of datos.sensores) {
          if (!/^[0-9A-Fa-f]{4}$/.test(s.ieee4 || "") || Math.abs(s.corr_t) > CORR_MAX_T || Math.abs(s.corr_h) > CORR_MAX_H) continue;
          await usb.ponerSensor({ ieee4: s.ieee4, nombre: textoMonitor(s.nombre, 30), perfil: s.perfil === "EST" ? "EST" : "MED",
            corr_t: Number(s.corr_t) || 0, corr_h: Math.trunc(Number(s.corr_h) || 0), calibrado: textoMonitor(s.calibrado, 23), oculto: !!s.oculto });
        }
        if (nuevo.pantalla !== equipoUSB.equipo.pantalla) await usb.reiniciarYReconectar(() => usb.ponerEquipo(nuevo));
        else await usb.ponerEquipo(nuevo);
        equipoUSB.info.codigo = nuevo.codigo;
        await registrar("respaldo_aplicado");
        toast("Configuración aplicada.");
      });
    };
    document.getElementById("u-clave").onclick = async () => {
      if (!await confirmarDestructivo({ titulo: "¿Ver la clave de firma?", verbo: "Ver clave",
        texto: "Sirve para revisar que los archivos de la SD no fueron alterados (al importar archivos). Quien la tenga podría falsificar registros: guárdala en un lugar seguro y no la envíes por correo. Queda registrado en los eventos del monitor y en la bitácora del portal." })) return;
      await conMonitor("Leyendo la clave", async () => {
        const clave = await usb.clave();
        await registrar("clave_leida");
        const i = equipoUSB.info;
        dialogo({
          titulo: `Clave de firma de ${i.codigo}`,
          html: `<p class="dlg-texto">Serie ${esc(i.serie)}. Pégala en «Clave de firma» al importar los archivos de este equipo. F+data no la guarda.</p><pre class="texto-usb clave-usb">${esc(clave)}</pre>`,
          acciones: [
            { texto: "Descargar", clase: "btn btn-texto", alHacer: () => { descargar(nombreArchivo(`clave_${i.codigo}_${i.serie}.txt`), `Equipo ${i.codigo}  serie ${i.serie}\n${clave}\n`, "text/plain"); return false; } },
            { texto: "Copiar", clase: "btn btn-texto", alHacer: async () => { try { await navigator.clipboard.writeText(clave); toast("Clave copiada."); } catch (_) { toast("No se pudo copiar: selecciónala y cópiala a mano."); } return false; } },
            { texto: "Cerrar", valor: null },
          ],
        });
      }, null);
    };
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
