// Utilidades compartidas: API, íconos, logotipo, sesión, bloqueo de pantalla, diálogos.
"use strict";

const ICONOS = {
  apps: '<svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="12" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="18" cy="12" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="12" cy="18" r="2"/><circle cx="18" cy="18" r="2"/></svg>',
  mas: '<svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>',
  mic: '<svg viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/></svg>',
  chispa: '<svg viewBox="0 0 24 24"><path d="M12 2.5l2.3 6.2 6.2 2.3-6.2 2.3L12 19.5l-2.3-6.2L3.5 11l6.2-2.3z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z"/></svg>',
  enviar: '<svg viewBox="0 0 24 24"><path d="M3.4 20.4l17.45-7.48a1 1 0 000-1.84L3.4 3.6a.993.993 0 00-1.39.91L2 9.12c0 .5.37.93.87.99L17 12 2.87 13.88c-.5.07-.87.5-.87 1l.01 4.61c0 .71.73 1.2 1.39.91z"/></svg>',
  escudo: '<svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>',
  candado: '<svg viewBox="0 0 24 24"><path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg>',
  salir: '<svg viewBox="0 0 24 24"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg>',
  cerrar: '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
  modulos: '<svg viewBox="0 0 24 24"><path d="M13 13v8h8v-8h-8zM3 21h8v-8H3v8zM3 3v8h8V3H3zm13.66-1.31L11 7.34 16.66 13l5.66-5.66-5.66-5.65z"/></svg>',
  inicio: '<svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
  persona: '<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>',
  privacidad: '<svg viewBox="0 0 24 24"><path d="M17 7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h10c2.76 0 5-2.24 5-5s-2.24-5-5-5zm0 8c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/></svg>',
  descargar: '<svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>',
  dispositivo: '<svg viewBox="0 0 24 24"><path d="M4 6h18V4H4c-1.1 0-2 .9-2 2v11H0v3h14v-3H4V6zm19 2h-6c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h6c.55 0 1-.45 1-1V9c0-.55-.45-1-1-1zm-1 9h-4v-7h4v7z"/></svg>',
  historial: '<svg viewBox="0 0 24 24"><path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>',
  documento: '<svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>',
  alerta: '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>',
  info: '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>',
  flecha: '<svg viewBox="0 0 24 24"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>',
  ayuda: '<svg viewBox="0 0 24 24"><path d="M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z"/></svg>',
};

function icono(nombre) { return ICONOS[nombre] || ""; }
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
    el.innerHTML = CONFIG.producto.split(/\s+/).map((p) => `<span class="palabra">${esc(p)}</span>`).join(" ");
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
    ? { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }
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
