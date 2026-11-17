// Módulo de ejemplo según las directrices de diseño (docs/diseno/, Parte 3). Patrón para todo módulo:
//  1. iniciarModulo(clave, {destinos, accion, buscar, alNavegar}): sesión, barra superior, riel y direcciones.
//  2. Cada pantalla con datos maneja sus cuatro estados: cargando, vacío, error y sin permiso.
//  3. api("/api/m/<clave>/...") y esc() para todo texto que venga del servidor.
"use strict";

const CLAVE = "ejemplo";
const API = `/api/m/${CLAVE}`;

(async function () {
  let filtro = "";
  let pantalla = "todos";
  const main = document.getElementById("contenido");

  const inicio = await iniciarModulo(CLAVE, {
    destinos: [
      { id: "todos", etiqueta: "Todos los avisos", icono: "list" },
      { id: "mios", etiqueta: "Mis avisos", icono: "user", permiso: `${CLAVE}.publicar` },
      { id: "acerca", etiqueta: "Acerca del módulo", icono: "info" },
    ],
    accion: { texto: "Nuevo aviso", icono: "plus", permiso: `${CLAVE}.publicar`, alHacer: () => nuevoAviso() },
    buscar: { placeholder: "Buscar avisos", alBuscar: (q) => { filtro = q.toLowerCase(); if (pantalla !== "acerca") pintarLista(); } },
    alNavegar: (id) => { pantalla = id; id === "acerca" ? pintarAcerca() : pintarLista(); },
  });
  if (!inicio) return;
  const { modulo } = inicio;

  // ---------------------------------------------------------------- lista (todos o míos)
  async function pintarLista() {
    const mios = pantalla === "mios";
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">${mios ? "Mis avisos" : "Todos los avisos"}</h1></div>
      <p class="aviso-suave" style="max-width:760px">${linea("shield")}<span>No publiques datos de pacientes. Los avisos se eliminan solos al cumplir un año.</span></p>
      <div class="lista-avisos" id="lista" style="margin-top:16px"></div>`;
    const lista = document.getElementById("lista");
    cargando(true, lista);
    let avisos;
    try { avisos = await api(`${API}/avisos${mios ? "?mios=1" : ""}`); }
    catch (e) {
      cargando(false);
      if (e.status === 403) return estadoSinPermiso(lista, "Necesitas el permiso para ver avisos de este módulo.");
      return estadoError(lista, "No pudimos cargar los avisos.", pintarLista);
    }
    cargando(false);
    const visibles = filtro ? avisos.filter((a) => `${a.titulo} ${a.texto} ${a.autor}`.toLowerCase().includes(filtro)) : avisos;
    if (!visibles.length) {
      if (filtro) return estadoVacio(lista, "Sin resultados", `No hay avisos que coincidan con «${filtro}».`);
      return estadoVacio(lista, mios ? "Aún no publicas avisos" : "Aún no hay avisos",
        "Los avisos de la unidad aparecerán aquí.",
        modulo.puede(`${CLAVE}.publicar`) ? { texto: "Publicar el primero", alHacer: nuevoAviso } : null);
    }
    lista.innerHTML = visibles.map((a) => `
      <article class="tarjeta aviso">
        <h2>${esc(a.titulo)}</h2>
        <p>${esc(a.texto)}</p>
        <div class="pie-aviso"><span class="autor"><span class="avatar" data-nombre="${esc(a.autor)}"></span>${esc(a.autor)} · ${esc(fechaLocal(a.creado_en))}</span>
          ${a.puede_borrar ? `<button class="btn-icono" data-borrar="${a.id}" aria-label="Borrar aviso" title="Borrar aviso">${linea("trash-2")}</button>` : ""}</div>
      </article>`).join("");
    lista.querySelectorAll(".avatar[data-nombre]").forEach((el) => pintarAvatar(el, el.dataset.nombre));
    lista.querySelectorAll("[data-borrar]").forEach((b) => b.onclick = async () => {
      const ok = await confirmarDestructivo({ titulo: "¿Borrar este aviso?", texto: "Dejará de verse para todos. No se puede deshacer.", verbo: "Borrar aviso" });
      if (!ok) return;
      try { await api(`${API}/avisos/${b.dataset.borrar}`, { metodo: "DELETE" }); toast("Aviso borrado."); pintarLista(); }
      catch (e) { toast(e.message); }
    });
  }

  // ---------------------------------------------------------------- acerca (transparencia: ficha de tratamiento)
  function pintarAcerca() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Acerca del módulo</h1></div>
      <section class="tarjeta ficha"><h2 class="titulo-seccion">${esc(modulo.nombre)}</h2>
        <dl><dt>Qué hace</dt><dd>${esc(modulo.descripcion)}</dd>
          <dt>Para qué usa datos</dt><dd>${esc(modulo.finalidad)}</dd>
          <dt>Versión</dt><dd>${esc(modulo.version)}</dd></dl></section>`;
  }

  // ---------------------------------------------------------------- acción principal
  function nuevoAviso() {
    dialogo({
      titulo: "Nuevo aviso",
      html: `<div class="campo"><input id="av-titulo" placeholder=" " maxlength="80"><label for="av-titulo">Título</label></div>
             <div class="campo"><textarea id="av-texto" placeholder=" " maxlength="1000"></textarea><label for="av-texto">Texto</label>
               <div class="ayuda">No escribas nombres ni datos de pacientes.</div></div>
             <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Publicar aviso", alHacer: async (v) => {
        try {
          await api(`${API}/avisos`, { metodo: "POST", datos: {
            titulo: v.querySelector("#av-titulo").value, texto: v.querySelector("#av-texto").value } });
        } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
        toast("Aviso publicado."); if (pantalla === "acerca") inicio.ir("todos"); else pintarLista(); return true;
      } }],
    });
  }
})();
