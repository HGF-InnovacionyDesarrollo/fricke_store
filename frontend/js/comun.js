// Utilidades compartidas: API, íconos, logotipo, sesión, bloqueo de pantalla, diálogos.
"use strict";

// Íconos de la interfaz: de línea, set Lucide (licencia ISC), retícula 24 y trazo 2 (docs/diseno/, Parte 3).
// Los nombres se mantienen; "apps" son los 9 puntos del menú de módulos (puntos rellenos, como en Google).
const LUCIDE = {
  mas: '<path d="M5 12h14M12 5v14"/>',
  mic: '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3"/>',
  chispa: '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0l1.58 6.14a2 2 0 0 0 1.44 1.44l6.14 1.58a.5.5 0 0 1 0 .96l-6.14 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/><path d="M20 3v4M22 5h-4M4 17v2M5 18H3"/>',
  enviar: '<path d="M14.54 21.69a.5.5 0 0 0 .94-.03l6.5-19a.5.5 0 0 0-.64-.63l-19 6.5a.5.5 0 0 0-.02.93l7.93 3.18a2 2 0 0 1 1.11 1.11z"/><path d="m21.85 2.15-10.94 10.94"/>',
  escudo: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
  candado: '<rect width="18" height="11" x="3" y="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  salir: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
  cerrar: '<path d="M18 6 6 18M6 6l12 12"/>',
  modulos: '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
  inicio: '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .71-1.53l7-6a2 2 0 0 1 2.58 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  persona: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  privacidad: '<rect width="20" height="12" x="2" y="6" rx="6"/><circle cx="16" cy="12" r="2"/>',
  descargar: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
  dispositivo: '<path d="M18 8V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h8M10 19v-4M7 19h5"/><rect width="6" height="10" x="16" y="12" rx="2"/>',
  historial: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5M12 7v5l4 2"/>',
  documento: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4M10 9H8M16 13H8M16 17H8"/>',
  alerta: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  flecha: '<path d="m9 18 6-6-6-6"/>',
  ayuda: '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01"/>',
};
const NUEVE_PUNTOS = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="6" cy="6" r="2"/><circle cx="12" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="18" cy="12" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="12" cy="18" r="2"/><circle cx="18" cy="18" r="2"/></svg>';

function icono(nombre) {
  if (nombre === "apps") return NUEVE_PUNTOS;
  const d = LUCIDE[nombre];
  return d ? `<svg class="linea" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${d}</svg>` : "";
}
function pintarIconos(raiz = document) {
  raiz.querySelectorAll("[data-icono]").forEach((el) => { el.innerHTML = icono(el.dataset.icono); });
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

class ErrorApi extends Error {
  constructor(status, mensaje) { super(mensaje); this.status = status; }
}

async function api(ruta, { metodo = "GET", datos } = {}) {
  const r = await fetch(ruta, {
    method: metodo,
    credentials: "same-origin",
    headers: { "X-Ecosistema": "1", ...(datos ? { "Content-Type": "application/json" } : {}) },
    body: datos ? JSON.stringify(datos) : undefined,
  });
  if (r.status === 401 && !ruta.startsWith("/api/auth/")) {
    location.href = "/ingresar?expirada=1";
    throw new ErrorApi(401, "Sesión expirada");
  }
  if (r.status === 423) { mostrarBloqueo(); throw new ErrorApi(423, "Pantalla bloqueada"); }
  const tipo = r.headers.get("content-type") || "";
  const cuerpo = tipo.includes("json") ? await r.json() : await r.text();
  if (!r.ok) {
    let msg = cuerpo && cuerpo.detail;
    if (Array.isArray(msg)) msg = "Revisa los datos ingresados.";
    throw new ErrorApi(r.status, msg || "Ocurrió un error. Intenta nuevamente.");
  }
  return cuerpo;
}

let CONFIG = null;
async function cargarConfig() {
  if (!CONFIG) CONFIG = await fetch("/api/config").then((r) => r.json());
  document.querySelectorAll("[data-cfg]").forEach((el) => { el.textContent = CONFIG[el.dataset.cfg] ?? ""; });
  document.querySelectorAll("[data-logo]").forEach((el) => {
    // isotipo (grilla de módulos con el símbolo del hospital) + nombre con degradado azul → menta
    el.innerHTML = `<img class="logo-icono" src="/marca/logo-icono.svg" alt=""><span class="logo-texto">${esc(CONFIG.producto)}</span>`;
    el.setAttribute("aria-label", CONFIG.producto);
  });
  return CONFIG;
}

function iniciales(nombre) {
  const p = (nombre || "?").trim().split(/\s+/);
  return (p[0][0] || "?").toUpperCase();
}

// Color estable por persona, como los avatares de Google
function colorAvatar(texto) {
  const paleta = ["#1565c0", "#13806f", "#0d47a1", "#00796b", "#3949ab", "#2b3440", "#1976d2", "#00695c", "#455a64", "#5e35b1"];
  let h = 0; for (const c of texto || "") h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return paleta[h % paleta.length];
}
function pintarAvatar(el, nombre) {
  el.textContent = iniciales(nombre);
  el.style.background = colorAvatar(nombre);
}

function toast(texto, ms = 4000) {
  document.querySelectorAll(".toast").forEach((t) => t.remove());
  const t = document.createElement("div");
  t.className = "toast"; t.setAttribute("role", "status");
  t.innerHTML = `<span>${esc(texto)}</span>`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), ms);
}

function fechaLocal(iso, conHora = true) {
  if (!iso) return "—";
  const d = new Date(iso.length <= 10 ? iso + "T12:00:00" : iso);
  return d.toLocaleString("es-CL", conHora
    ? { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }
    : { day: "numeric", month: "long", year: "numeric" });
}

function navegadorLegible(ua) {
  if (!ua) return "Navegador desconocido";
  const nav = /Edg\//.test(ua) ? "Edge" : /Chrome\//.test(ua) ? "Chrome" : /Firefox\//.test(ua) ? "Firefox" : /Safari\//.test(ua) ? "Safari" : "Navegador";
  const so = /Windows/.test(ua) ? "Windows" : /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iOS" : /Mac OS/.test(ua) ? "macOS" : /Linux/.test(ua) ? "Linux" : "";
  return so ? `${nav} en ${so}` : nav;
}

// ---------------------------------------------------------------- diálogos
function dialogo({ titulo, html, acciones = [], cerrable = true, clase = "" }) {
  return new Promise((resolver) => {
    const velo = document.createElement("div");
    velo.className = "velo";
    velo.innerHTML = `<div class="dialogo ${clase}" role="dialog" aria-modal="true" aria-labelledby="dlg-t">
      <h2 id="dlg-t">${esc(titulo)}</h2><div class="dlg-cuerpo">${html}</div>
      <div class="acciones"></div></div>`;
    const cont = velo.querySelector(".acciones");
    const cerrar = (v) => { velo.remove(); resolver(v); };
    acciones.forEach((a) => {
      const b = document.createElement("button");
      b.className = a.clase || "btn"; b.textContent = a.texto;
      if (a.tipo === "submit") b.type = "submit";
      b.addEventListener("click", async () => {
        if (!a.alHacer) return cerrar(a.valor);
        b.disabled = true;
        try { const r = await a.alHacer(velo); if (r !== false) cerrar(r ?? a.valor); }
        finally { b.disabled = false; }
      });
      cont.appendChild(b);
    });
    if (cerrable) {
      velo.addEventListener("click", (e) => { if (e.target === velo) cerrar(null); });
      velo.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrar(null); });
    }
    document.body.appendChild(velo);
    pintarIconos(velo);
    (velo.querySelector("input, textarea, select") || velo.querySelector("button"))?.focus();
  });
}

function mostrarErrorEn(contenedor, mensaje) {
  let e = contenedor.querySelector(".error-txt");
  if (!mensaje) { e?.remove(); return; }
  if (!e) { e = document.createElement("div"); e.className = "error-txt"; e.setAttribute("role", "alert"); contenedor.appendChild(e); }
  e.innerHTML = `${icono("alerta")}<span>${esc(mensaje)}</span>`;
}

// ---------------------------------------------------------------- cambio de contraseña
function dialogoCambioClave({ obligatorio = false } = {}) {
  return dialogo({
    titulo: obligatorio ? "Crea tu contraseña" : "Cambiar contraseña",
    cerrable: !obligatorio,
    html: `${obligatorio ? `<p style="margin:0 0 20px;color:var(--texto-2)">Estás usando una contraseña temporal. Crea una personal para continuar.</p>` : ""}
      <form class="form-clave" autocomplete="on">
        <div class="campo"><input type="password" id="cc-actual" placeholder=" " autocomplete="current-password" required><label for="cc-actual">${obligatorio ? "Contraseña temporal" : "Contraseña actual"}</label></div>
        <div class="campo"><input type="password" id="cc-nueva" placeholder=" " autocomplete="new-password" required><label for="cc-nueva">Nueva contraseña</label>
          <div class="ayuda">Mínimo 15 caracteres. Usa una frase fácil de recordar (puedes usar espacios). No uses tu RUT, tu nombre ni contraseñas comunes.</div></div>
        <div class="campo"><input type="password" id="cc-repite" placeholder=" " autocomplete="new-password" required><label for="cc-repite">Confirmar</label></div>
        <div class="zona-error"></div>
      </form>`,
    acciones: [
      ...(obligatorio ? [{ texto: "Cerrar sesión", clase: "btn btn-texto", alHacer: async () => { await cerrarSesion(); return false; } }]
                      : [{ texto: "Cancelar", clase: "btn btn-texto", valor: false }]),
      { texto: "Guardar", alHacer: async (v) => {
          const actual = v.querySelector("#cc-actual").value, nueva = v.querySelector("#cc-nueva").value;
          const zona = v.querySelector(".zona-error");
          if (nueva !== v.querySelector("#cc-repite").value) { mostrarErrorEn(zona, "Las contraseñas no coinciden."); return false; }
          try { await api("/api/auth/cambiar-clave", { metodo: "POST", datos: { actual, nueva } }); }
          catch (e) { mostrarErrorEn(zona, e.message); return false; }
          toast("Contraseña actualizada. Se cerraron tus otras sesiones.");
          return true;
        } },
    ],
  });
}

// ---------------------------------------------------------------- aviso de privacidad (primer ingreso)
function dialogoAviso() {
  return dialogo({
    titulo: "Antes de comenzar",
    cerrable: false,
    html: `<p style="margin:0 0 16px;color:var(--texto-2)">Te contamos en simple cómo ${esc(CONFIG.institucion)} trata tus datos en este ecosistema
      (Ley 21.719 sobre Protección de Datos Personales).</p>
      <ul class="resumen-aviso">
        <li>${icono("persona")}<div><b>Qué datos usamos</b><br>Tu RUT, nombre, cargo, unidad y correo institucional, además de un registro de tus accesos (fecha, hora, equipo e IP).</div></li>
        <li>${icono("escudo")}<div><b>Para qué</b><br>Solo para darte acceso a las herramientas del hospital, proteger la información clínica y poder auditar quién accedió a qué.</div></li>
        <li>${icono("candado")}<div><b>Cómo los cuidamos</b><br>Contraseña cifrada, cierre automático por inactividad, registro inalterable y sin cookies de terceros ni publicidad.</div></li>
        <li>${icono("privacidad")}<div><b>Tus derechos</b><br>Puedes ver, descargar, corregir u oponerte al uso de tus datos desde <i>Mi cuenta › Datos y privacidad</i>.</div></li>
      </ul>
      <p style="margin:16px 0 0;font-size:13px"><a href="/privacidad" target="_blank" rel="noopener">Leer el aviso de privacidad completo</a> · versión ${esc(CONFIG.version_aviso)}</p>`,
    acciones: [{ texto: "Entendido", alHacer: async () => { await api("/api/privacidad/aceptar", { metodo: "POST" }); return true; } }],
  });
}

// ---------------------------------------------------------------- sesión e inactividad
async function cerrarSesion(motivo) {
  try { await api("/api/auth/logout", { metodo: "POST" }); } catch (_) { /* nada */ }
  location.href = "/ingresar" + (motivo ? `?${motivo}=1` : "");
}

async function bloquearPantalla() {
  await api("/api/auth/bloquear", { metodo: "POST" });
  mostrarBloqueo();
}

let _nombreBloqueo = "";
function mostrarBloqueo(nombre) {
  if (nombre) _nombreBloqueo = nombre;
  if (document.querySelector(".bloqueo")) return;
  document.querySelectorAll(".pop").forEach((p) => p.classList.add("oculto"));
  document.querySelectorAll(".velo").forEach((p) => p.remove());
  const b = document.createElement("div");
  b.className = "bloqueo";
  b.innerHTML = `<form class="caja" autocomplete="off">
      <div class="avatar grande"></div>
      <h2>${esc(_nombreBloqueo || "Pantalla bloqueada")}</h2>
      <p>Pantalla bloqueada. Ingresa tu contraseña para continuar.</p>
      <div class="campo"><input type="password" id="bq-clave" placeholder=" " autocomplete="current-password" required><label for="bq-clave">Contraseña</label></div>
      <div class="zona-error" style="margin:-8px 0 16px"></div>
      <div class="fila"><button type="button" class="btn btn-texto" id="bq-otro">No soy yo · Cerrar sesión</button><button class="btn">Desbloquear</button></div>
    </form>`;
  document.body.appendChild(b);
  pintarAvatar(b.querySelector(".avatar"), _nombreBloqueo);
  b.querySelector("#bq-otro").onclick = () => cerrarSesion();
  b.querySelector("form").onsubmit = async (e) => {
    e.preventDefault();
    try {
      await api("/api/auth/desbloquear", { metodo: "POST", datos: { clave: b.querySelector("#bq-clave").value } });
      b.remove(); reiniciarInactividad();
    } catch (err) { mostrarErrorEn(b.querySelector(".zona-error"), err.message); b.querySelector("#bq-clave").select(); }
  };
  b.querySelector("#bq-clave").focus();
}

// El servidor cierra la sesión tras N minutos sin solicitudes. El navegador avisa un minuto antes
// y, mientras la persona está trabajando, mantiene la sesión viva con un pulso cada 2 minutos.
let _limiteMs = 15 * 60e3, _ultimaActividad = Date.now(), _ultimoPulso = Date.now(), _avisoInactividad = null;
function vigilarInactividad(minutos) {
  _limiteMs = minutos * 60e3;
  ["pointerdown", "keydown", "wheel", "touchstart"].forEach((ev) => addEventListener(ev, alActuar, { passive: true }));
  setInterval(revisarInactividad, 5000);
}
function alActuar() {
  if (document.querySelector(".bloqueo")) return;
  _ultimaActividad = Date.now();
  if (_avisoInactividad) { _avisoInactividad.remove(); _avisoInactividad = null; }
  if (Date.now() - _ultimoPulso > 120e3) { _ultimoPulso = Date.now(); api("/api/me").catch(() => {}); }
}
function reiniciarInactividad() { _ultimaActividad = Date.now(); _ultimoPulso = 0; alActuar(); }
function revisarInactividad() {
  if (document.querySelector(".bloqueo")) return;
  const restante = _limiteMs - (Date.now() - _ultimaActividad);
  if (restante <= 0) return cerrarSesion("expirada");
  if (restante <= 60e3 && !_avisoInactividad) {
    _avisoInactividad = document.createElement("div");
    _avisoInactividad.className = "toast"; _avisoInactividad.setAttribute("role", "alert");
    _avisoInactividad.innerHTML = `<span>Tu sesión se cerrará en menos de un minuto por inactividad.</span><button>Seguir conectado</button>`;
    _avisoInactividad.querySelector("button").onclick = () => { _ultimoPulso = 0; alActuar(); };
    document.body.appendChild(_avisoInactividad);
  }
}

// Atajo: Win+L no llega al navegador, así que usamos Ctrl+Alt+L para bloquear.
addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.altKey && e.key.toLowerCase() === "l" && document.body.dataset.sesion === "1") {
    e.preventDefault(); bloquearPantalla();
  }
});

// Carga /api/me y resuelve los pasos obligatorios del primer ingreso.
async function exigirSesion() {
  await cargarConfig();
  let yo = await api("/api/me");
  document.body.dataset.sesion = "1";
  if (yo.bloqueada) { mostrarBloqueo(yo.nombre); await esperarDesbloqueo(); yo = await api("/api/me"); }
  _nombreBloqueo = yo.nombre;
  if (yo.debe_cambiar_clave) await dialogoCambioClave({ obligatorio: true });
  if (yo.debe_aceptar_aviso) await dialogoAviso();
  vigilarInactividad(yo.inactividad_min);
  return yo;
}
function esperarDesbloqueo() {
  return new Promise((ok) => {
    const t = setInterval(() => { if (!document.querySelector(".bloqueo")) { clearInterval(t); ok(); } }, 200);
  });
}
