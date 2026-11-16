"use strict";

(async function () {
  pintarIconos();
  let yo;
  try { yo = await exigirSesion(); } catch (_) { return; }
  document.title = `${CONFIG.producto} · ${CONFIG.institucion}`;

  // ---------- cuenta
  pintarAvatar(document.getElementById("avatar-sup"), yo.nombre);
  pintarAvatar(document.getElementById("avatar-pop"), yo.nombre);
  document.getElementById("btn-cuenta").title = `${yo.nombre}\n${yo.rut}`;
  document.getElementById("cuenta-rut").textContent = yo.rut;
  document.getElementById("cuenta-hola").textContent = `¡Hola, ${yo.nombre.split(" ")[0]}!`;
  document.getElementById("cuenta-cargo").textContent = [yo.cargo, yo.unidad].filter(Boolean).join(" · ");

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

  // ---------- módulos (solo los que el usuario tiene habilitados)
  const lista = document.getElementById("apps-lista");
  try {
    const mods = await api("/api/modulos");
    if (!mods.length) {
      lista.innerHTML = `<div class="apps-vacio">
          <div class="ilus">${icono("modulos")}</div>
          <h3>Aún no hay módulos</h3>
          <p>Las soluciones del hospital se irán sumando aquí. Solo verás las que correspondan a tu función.</p>
        </div>`;
    } else {
      lista.innerHTML = `<div class="apps-grilla">${mods.map((m) => `
        <a class="app" href="${esc(m.url)}" title="${esc(m.descripcion || m.nombre)}">
          <span class="app-icono" style="background:${esc(m.color || "#1565c0")}">${icono(m.icono) || esc(m.nombre[0])}</span>
          <span>${esc(m.nombre)}</span></a>`).join("")}</div>`;
    }
  } catch (_) {
    lista.innerHTML = `<div class="apps-vacio"><p>No se pudieron cargar los módulos.</p></div>`;
  }

  // ---------- asistente (maqueta)
  const portada = document.getElementById("portada"), chat = document.getElementById("chat"), hilo = document.getElementById("chat-hilo");
  async function preguntar(texto) {
    texto = texto.trim();
    if (!texto) return;
    portada.classList.add("oculto"); chat.classList.remove("oculto");
    hilo.insertAdjacentHTML("beforeend", `<div class="msj yo">${esc(texto)}</div>`);
    const r = document.createElement("div");
    r.className = "msj ia";
    r.innerHTML = `<span class="chispa">${icono("chispa")}</span><div class="escribiendo">Pensando…</div>`;
    hilo.appendChild(r);
    r.scrollIntoView({ behavior: "smooth", block: "end" });
    try {
      const { respuesta } = await api("/api/asistente", { metodo: "POST", datos: { texto } });
      await new Promise((ok) => setTimeout(ok, 500));
      r.querySelector("div").className = ""; r.querySelector("div").textContent = respuesta;
    } catch (e) { r.querySelector("div").textContent = e.message; }
    document.getElementById("pregunta-chat").focus();
  }
  document.getElementById("form-pregunta").onsubmit = (e) => { e.preventDefault(); preguntar(e.target.pregunta.value); };
  document.getElementById("form-chat").onsubmit = (e) => {
    e.preventDefault(); const i = document.getElementById("pregunta-chat"); preguntar(i.value); i.value = "";
  };
  document.querySelectorAll(".sugerencia").forEach((b) => b.addEventListener("click", () => {
    const i = document.getElementById("pregunta"); i.value = b.dataset.texto; i.focus();
  }));
  document.getElementById("pregunta").focus();
})();
