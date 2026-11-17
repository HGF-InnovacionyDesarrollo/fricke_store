// Esqueleto común de los módulos (docs/diseno/, Parte 3): barra superior, riel lateral o pestañas,
// direcciones por pantalla (/m/<modulo>/<pantalla>), acción principal y los cuatro estados de una pantalla.
// Requiere comun.js y cabecera.js; estilos en css/modulo.css.
"use strict";

// ---------------------------------------------------------------- íconos de línea (Lucide, ISC: retícula 24, trazo 2)
const LINEAS = {
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  "circle-help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  plus: '<path d="M5 12h14M12 5v14"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  "arrow-left": '<path d="m12 19-7-7 7-7M19 12H5"/>',
  "trash-2": '<path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
  "lock": '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  "inbox": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
  "cloud-off": '<path d="m2 2 20 20M5.78 5.78A7 7 0 0 0 9 19h8.5a4.5 4.5 0 0 0 1.31-.2M21.53 15.1A4.5 4.5 0 0 0 17.5 10h-1.79A7 7 0 0 0 9.14 5.06"/>',
};
function linea(nombre) {
  const d = LINEAS[nombre];
  return d ? `<svg class="linea" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>` : "";
}
function pintarLineas(raiz = document) {
  raiz.querySelectorAll("[data-linea]").forEach((el) => { el.innerHTML = linea(el.dataset.linea); });
}

// ---------------------------------------------------------------- estados de una pantalla
let _tCarga;
/** Barra de progreso fina bajo la barra superior; si tarda más de 1 s, filas grises en `contenedor`. */
function cargando(activo, contenedor) {
  const barra = document.getElementById("progreso");
  clearTimeout(_tCarga);
  barra?.classList.toggle("oculto", !activo);
  if (activo && contenedor) {
    _tCarga = setTimeout(() => { contenedor.innerHTML = `<div class="esqueleto">${"<div></div>".repeat(4)}</div>`; }, 1000);
  }
}
/** Vacío: qué aparecerá ahí y cómo empezar. `accion` = {texto, alHacer} (opcional). */
function estadoVacio(contenedor, titulo, texto, accion) {
  contenedor.innerHTML = `<div class="estado">${linea("inbox")}<h2>${esc(titulo)}</h2><p>${esc(texto)}</p>
    ${accion ? `<button class="btn">${esc(accion.texto)}</button>` : ""}</div>`;
  if (accion) contenedor.querySelector("button").onclick = accion.alHacer;
}
/** Error: qué pasó y qué hacer, con "Reintentar". */
function estadoError(contenedor, texto, reintentar) {
  contenedor.innerHTML = `<div class="estado">${linea("cloud-off")}<h2>${esc(texto)}</h2>
    <p>Revisa tu conexión e inténtalo de nuevo. Si sigue pasando, llama a ${esc(CONFIG.mesa_ayuda)}.</p>
    <button class="btn btn-borde">Reintentar</button></div>`;
  contenedor.querySelector("button").onclick = reintentar;
}
/** Sin permiso: qué perfil se necesita y a quién pedirlo, sin mostrar datos. */
function estadoSinPermiso(contenedor, texto) {
  contenedor.innerHTML = `<div class="estado">${linea("lock")}<h2>No tienes acceso a esta sección</h2>
    <p>${esc(texto || "Tu perfil no tiene el permiso necesario.")} Si lo necesitas para tu trabajo, pídelo a tu jefatura
    o a ${esc(CONFIG.mesa_ayuda)}.</p></div>`;
}
/** Confirmación de algo que no se puede deshacer: acción en rojo con el verbo exacto. */
function confirmarDestructivo({ titulo, texto, verbo }) {
  return dialogo({ titulo, html: `<p class="dlg-texto">${esc(texto)}</p>`,
    acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: false }, { texto: verbo, clase: "btn btn-peligro", valor: true }] });
}

// ---------------------------------------------------------------- arranque del módulo
/**
 * @param {string} clave
 * @param {object} op
 * @param {Array<{id:string, etiqueta:string, icono:string, permiso?:string}>} op.destinos  3 a 7 → riel; 1 o 2 → pestañas
 * @param {{texto:string, icono:string, permiso?:string, alHacer:Function}} [op.accion]  acción principal (una por módulo)
 * @param {{placeholder:string, alBuscar:Function}} [op.buscar]  buscador de la barra superior
 * @param {(pantalla:string, extra:string[]) => void} op.alNavegar  pinta la pantalla pedida
 * @returns {Promise<{yo, modulo, ir:(pantalla:string)=>void} | null>}
 */
async function iniciarModulo(clave, { destinos = [], accion = null, buscar = null, alNavegar } = {}) {
  pintarIconos();
  let yo;
  try { yo = await exigirSesion(); } catch (_) { return null; }
  let modulo;
  try {
    modulo = await api(`/api/modulos/${encodeURIComponent(clave)}/contexto`);
  } catch (e) {
    await iniciarCabecera(yo);
    estadoSinPermiso(document.querySelector("main"), "Este módulo no está habilitado para tu perfil o está suspendido.");
    return null;
  }
  modulo.url = `/m/${clave}/`;
  modulo.puede = (permiso) => !permiso || modulo.permisos.includes(permiso);
  await iniciarCabecera(yo, { modulo });
  pintarLineas(document.body);

  // Ayuda: qué es el módulo, para qué usa datos y a quién llamar
  document.getElementById("btn-ayuda").onclick = () => dialogo({
    titulo: `Ayuda · ${modulo.nombre}`,
    html: `<p class="dlg-texto">${esc(modulo.descripcion)}</p>
      <p class="dlg-texto"><b>Para qué usa datos personales:</b> ${esc(modulo.finalidad || "")}</p>
      <p class="dlg-texto">¿Tienes un problema? Llama a <b>${esc(CONFIG.mesa_ayuda)}</b>.
      <a href="/privacidad" target="_blank" rel="noopener">Aviso de privacidad</a></p>`,
    acciones: [{ texto: "Cerrar ayuda", clase: "btn btn-texto", valor: null }],
  });

  // Buscador de la barra superior (dice qué busca)
  if (buscar) {
    const f = document.getElementById("form-buscar"), i = document.getElementById("buscar-modulo");
    f.classList.remove("oculto");
    i.placeholder = buscar.placeholder;
    i.setAttribute("aria-label", buscar.placeholder);
    let t;
    i.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => buscar.alBuscar(i.value.trim()), 250); });
    f.onsubmit = (e) => { e.preventDefault(); buscar.alBuscar(i.value.trim()); };
  }

  // Navegación: riel (3 a 7 destinos) o pestañas (1 o 2); barra inferior en teléfono (por CSS)
  const visibles = destinos.filter((d) => modulo.puede(d.permiso));
  const main = document.querySelector("main");
  const marco = document.createElement("div");
  marco.className = "modulo-marco";
  main.parentNode.insertBefore(marco, main);
  const usarRiel = visibles.length >= 3;
  const nav = document.createElement("nav");
  nav.setAttribute("aria-label", `Secciones de ${modulo.nombre}`);
  const accionVisible = accion && modulo.puede(accion.permiso);
  if (usarRiel) {
    nav.className = "riel";
    nav.innerHTML = `${accionVisible ? `<button class="accion-principal" id="accion-principal">${linea(accion.icono)}<span>${esc(accion.texto)}</span></button>` : ""}
      ${visibles.map((d) => `<a class="destino" href="${modulo.url}${d.id}" data-id="${esc(d.id)}">${linea(d.icono)}<span>${esc(d.etiqueta)}</span></a>`).join("")}`;
    marco.appendChild(nav);
    const btnRiel = document.getElementById("btn-riel");
    btnRiel.classList.remove("oculto");
    let contraido = false;
    try { contraido = localStorage.getItem(`riel:${clave}`) === "1"; } catch (_) { /* sin almacenamiento */ }
    const aplicar = () => { marco.classList.toggle("contraido", contraido); btnRiel.setAttribute("aria-expanded", String(!contraido)); };
    btnRiel.onclick = () => { contraido = !contraido; aplicar(); try { localStorage.setItem(`riel:${clave}`, contraido ? "1" : "0"); } catch (_) { /* nada */ } };
    aplicar();
  } else if (visibles.length) {
    nav.className = "pestanas";
    nav.innerHTML = visibles.map((d) => `<a class="destino" href="${modulo.url}${d.id}" data-id="${esc(d.id)}">${esc(d.etiqueta)}</a>`).join("");
    main.prepend(nav);
    if (accionVisible) nav.insertAdjacentHTML("beforeend", `<button class="btn" id="accion-principal">${linea(accion.icono)}${esc(accion.texto)}</button>`);
  }
  marco.appendChild(main);
  if (accionVisible) document.getElementById("accion-principal").onclick = accion.alHacer;

  // Direcciones propias por pantalla: el botón Atrás funciona y los enlaces se pueden compartir
  function pantallaActual() {
    const resto = location.pathname.slice(modulo.url.length).split("/").filter(Boolean);
    return { id: resto[0] || visibles[0]?.id || "", extra: resto.slice(1) };
  }
  function pintar() {
    const { id, extra } = pantallaActual();
    nav.querySelectorAll(".destino").forEach((a) => {
      const activo = a.dataset.id === id;
      a.classList.toggle("activo", activo);
      if (activo) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    alNavegar?.(id, extra);
  }
  function ir(pantalla) { history.pushState(null, "", modulo.url + pantalla); pintar(); main.focus({ preventScroll: true }); }
  nav.addEventListener("click", (e) => {
    const a = e.target.closest("a.destino");
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;
    e.preventDefault(); ir(a.dataset.id);
  });
  addEventListener("popstate", pintar);
  main.tabIndex = -1;
  setTimeout(pintar, 0);  // después de que el módulo reciba { modulo, ir }
  return { yo, modulo, ir };
}
