// Módulo de ejemplo. Patrón que deben seguir todos los módulos:
//  1. iniciarModulo(clave): exige sesión, resuelve el primer ingreso, pinta la cabecera y trae permisos.
//  2. api("/api/m/<clave>/..."): ya envía la cabecera anti-CSRF y maneja sesión expirada y pantalla bloqueada.
//  3. Todo texto que viene del servidor pasa por esc() antes de ir a innerHTML.
"use strict";

const CLAVE = "ejemplo";
const API = `/api/m/${CLAVE}`;

(async function () {
  const inicio = await iniciarModulo(CLAVE);
  if (!inicio) return;
  const { modulo } = inicio;

  const lista = document.getElementById("lista-avisos");
  const btnNuevo = document.getElementById("btn-nuevo");
  if (modulo.puede(`${CLAVE}.publicar`)) btnNuevo.classList.remove("oculto");

  async function cargar() {
    const avisos = await api(`${API}/avisos`);
    lista.innerHTML = avisos.length ? avisos.map((a) => `
      <article class="tarjeta-aviso">
        <h2>${esc(a.titulo)}</h2>
        <p>${esc(a.texto)}</p>
        <div class="pie-aviso"><span>${esc(a.autor)} · ${fechaLocal(a.creado_en)}</span>
          ${a.puede_borrar ? `<button class="btn btn-texto" data-borrar="${a.id}">Borrar</button>` : ""}</div>
      </article>`).join("") : `<div class="vacio">Aún no hay avisos.</div>`;
    lista.querySelectorAll("[data-borrar]").forEach((b) => b.onclick = async () => {
      const ok = await dialogo({ titulo: "¿Borrar este aviso?", html: "<p>No se puede deshacer.</p>",
        acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: false }, { texto: "Borrar", valor: true }] });
      if (!ok) return;
      try { await api(`${API}/avisos/${b.dataset.borrar}`, { metodo: "DELETE" }); toast("Aviso borrado."); cargar(); }
      catch (e) { toast(e.message); }
    });
  }

  btnNuevo.onclick = () => dialogo({
    titulo: "Nuevo aviso",
    html: `<div class="campo"><input id="av-titulo" placeholder=" " maxlength="80"><label for="av-titulo">Título</label></div>
           <div class="campo"><textarea id="av-texto" placeholder=" " maxlength="1000"></textarea><label for="av-texto">Texto</label></div>
           <div class="zona-error"></div>`,
    acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Publicar", alHacer: async (v) => {
      try {
        await api(`${API}/avisos`, { metodo: "POST", datos: {
          titulo: v.querySelector("#av-titulo").value, texto: v.querySelector("#av-texto").value } });
      } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
      toast("Aviso publicado."); cargar(); return true;
    } }],
  });

  cargar();
})();
