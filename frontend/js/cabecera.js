// Cabecera común del ecosistema: menú de puntos (módulos), tarjeta de cuenta y, en un módulo,
// el logotipo con el nombre del módulo. La usan la portada y TODOS los módulos (ver docs/MODULOS.md).
// Requiere comun.js y css/cabecera.css.
"use strict";

const _HTML_POPS = `
<div class="pop pop-apps oculto" id="pop-apps" role="dialog" aria-label="Módulos del ecosistema">
  <div class="apps-tarjeta" id="apps-lista"></div>
</div>
<div class="pop pop-cuenta oculto" id="pop-cuenta" role="dialog" aria-label="Tu cuenta">
  <div class="cuenta-cab">
    <span class="cuenta-rut" id="cuenta-rut"></span>
    <button class="btn-icono" id="cerrar-cuenta" aria-label="Cerrar"><span data-icono="cerrar"></span></button>
  </div>
  <div class="cuenta-centro">
    <span class="avatar grande" id="avatar-pop"></span>
    <p class="cuenta-hola" id="cuenta-hola"></p>
    <p class="cuenta-cargo" id="cuenta-cargo"></p>
    <a class="btn btn-borde" href="/cuenta">Gestionar tu cuenta</a>
  </div>
  <div class="cuenta-acciones">
    <a id="btn-admin" class="oculto" href="/admin"><span data-icono="escudo"></span><span>Administración<small>Usuarios, solicitudes, módulos y bitácora</small></span></a>
    <button id="btn-bloquear"><span data-icono="candado"></span><span>Bloquear pantalla<small>Ctrl + Alt + L</small></span></button>
    <button id="btn-salir"><span data-icono="salir"></span><span>Cerrar sesión</span></button>
  </div>
  <p class="cuenta-pie"><a href="/privacidad">Aviso de privacidad</a> · <a href="/cuenta#privacidad">Tus derechos</a></p>
</div>`;

const _HTML_BARRA_MODULO = `
<header class="barra-sup barra-modulo">
  <a class="marca-modulo" href="/" title="Volver a la portada">
    <span class="logo" data-logo></span>
    <span class="sep" aria-hidden="true"></span>
    <span class="nombre-modulo" id="nombre-modulo"></span>
  </a>
  <span class="espacio"></span>
  <button class="btn-icono" id="btn-apps" aria-label="Módulos del ecosistema" aria-haspopup="true" aria-expanded="false" title="Módulos del ecosistema"><span data-icono="apps"></span></button>
  <button class="btn-avatar" id="btn-cuenta" aria-label="Tu cuenta" aria-haspopup="true" aria-expanded="false"><span class="avatar" id="avatar-sup"></span></button>
</header>`;

/**
 * Pinta la cabecera y conecta sus paneles.
 * @param {object} yo  respuesta de exigirSesion()
 * @param {object} [opciones]
 * @param {object} [opciones.modulo]  respuesta de /api/modulos/<clave>/contexto (solo en módulos)
 */
async function iniciarCabecera(yo, { modulo } = {}) {
  if (!document.querySelector(".barra-sup")) document.body.insertAdjacentHTML("afterbegin", _HTML_BARRA_MODULO);
  if (!document.getElementById("pop-cuenta")) document.body.insertAdjacentHTML("beforeend", _HTML_POPS);
  pintarIconos(document.querySelector(".barra-sup"));
  pintarIconos(document.getElementById("pop-cuenta"));
  await cargarConfig();  // vuelve a pintar el logotipo recién insertado

  if (modulo) {
    document.getElementById("nombre-modulo").textContent = modulo.nombre;
    document.title = `${modulo.nombre} · ${CONFIG.producto}`;
  }

  // ---------- cuenta
  pintarAvatar(document.getElementById("avatar-sup"), yo.nombre);
  pintarAvatar(document.getElementById("avatar-pop"), yo.nombre);
  document.getElementById("btn-cuenta").title = `${yo.nombre}\n${yo.rut}`;
  document.getElementById("cuenta-rut").textContent = yo.rut;
  document.getElementById("cuenta-hola").textContent = `¡Hola, ${yo.nombre.split(" ")[0]}!`;
  document.getElementById("cuenta-cargo").textContent = [yo.cargo, yo.unidad].filter(Boolean).join(" · ");
  if (yo.puede_administrar) document.getElementById("btn-admin").classList.remove("oculto");

  // ---------- paneles flotantes
  const pops = { "btn-apps": "pop-apps", "btn-cuenta": "pop-cuenta" };
  function cerrarPops() {
    Object.entries(pops).forEach(([b, p]) => {
      document.getElementById(p).classList.add("oculto");
      document.getElementById(b).setAttribute("aria-expanded", "false");
    });
  }
  function abrirPop(idBoton) {
    const boton = document.getElementById(idBoton), pop = document.getElementById(pops[idBoton]);
    const yaAbierto = !pop.classList.contains("oculto");
    cerrarPops();
    if (yaAbierto) return;
    pop.classList.remove("oculto");
    const r = boton.getBoundingClientRect();
    pop.style.top = `${r.bottom + 6 + scrollY}px`;
    pop.style.right = `${Math.max(8, document.documentElement.clientWidth - r.right - 4)}px`;
    boton.setAttribute("aria-expanded", "true");
    pop.querySelector("a, button")?.focus({ preventScroll: true });
  }
  Object.keys(pops).forEach((b) => document.getElementById(b).addEventListener("click", (e) => { e.stopPropagation(); abrirPop(b); }));
  Object.values(pops).forEach((p) => document.getElementById(p).addEventListener("click", (e) => e.stopPropagation()));
  document.addEventListener("click", cerrarPops);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrarPops(); });
  document.getElementById("cerrar-cuenta").onclick = cerrarPops;
  document.getElementById("btn-salir").onclick = () => cerrarSesion();
  document.getElementById("btn-bloquear").onclick = () => { cerrarPops(); bloquearPantalla(); };

  // ---------- módulos (solo los que la persona tiene habilitados)
  const lista = document.getElementById("apps-lista");
  try {
    const mods = await api("/api/modulos");
    lista.innerHTML = mods.length
      ? `<div class="apps-grilla">${mods.map((m) => `
          <a class="app${modulo && m.clave === modulo.clave ? " actual" : ""}" href="${esc(m.url)}" title="${esc(m.descripcion || m.nombre)}">
            <span class="app-icono" style="background:${esc(m.color || "#1565c0")}">${icono(m.icono) || esc(m.nombre[0])}</span>
            <span>${esc(m.nombre)}</span></a>`).join("")}</div>`
      : `<div class="apps-vacio">
          <div class="ilus">${icono("modulos")}</div>
          <h3>Aún no hay módulos</h3>
          <p>Las soluciones del hospital se irán sumando aquí. Solo verás las que correspondan a tu función.</p>
        </div>`;
  } catch (_) {
    lista.innerHTML = `<div class="apps-vacio"><p>No se pudieron cargar los módulos.</p></div>`;
  }
}

/**
 * Arranque estándar de la página de un módulo: sesión, primer ingreso, cabecera y permisos.
 * Devuelve { yo, modulo } o null si la persona no tiene acceso (ya se le mostró el aviso).
 */
async function iniciarModulo(clave) {
  pintarIconos();
  let yo;
  try { yo = await exigirSesion(); } catch (_) { return null; }
  let modulo;
  try {
    modulo = await api(`/api/modulos/${encodeURIComponent(clave)}/contexto`);
  } catch (e) {
    await iniciarCabecera(yo);
    document.querySelector("main").innerHTML = `<div class="sin-acceso">${icono("candado")}
      <h1>No tienes acceso a este módulo</h1><p>${esc(e.message)}</p>
      <p>Si lo necesitas para tu trabajo, pídelo a tu jefatura o a ${esc(CONFIG.mesa_ayuda)}.</p>
      <a class="btn" href="/">Volver a la portada</a></div>`;
    return null;
  }
  await iniciarCabecera(yo, { modulo });
  modulo.puede = (permiso) => modulo.permisos.includes(permiso);
  return { yo, modulo };
}
