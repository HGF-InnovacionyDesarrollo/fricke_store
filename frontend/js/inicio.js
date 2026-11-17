"use strict";

(async function () {
  pintarIconos();
  let yo;
  try { yo = await exigirSesion(); } catch (_) { return; }
  document.title = `${CONFIG.producto} · ${CONFIG.institucion}`;

  await iniciarCabecera(yo);

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
