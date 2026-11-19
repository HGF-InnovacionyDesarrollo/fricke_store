// F+docs según las directrices de diseño (docs/diseno/, Parte 3): iniciarModulo, cuatro estados, esc() y api().
// Pantallas: Documentos (/documentos/<carpeta>), Buscar (/buscar?q=…, a esta llega el botón de la pantalla de inicio),
// Papelera (solo con documentos.administrar) y Acerca del módulo. Solo PDF, hasta 25 MB.
"use strict";

const CLAVE = "documentos";
const API = `/api/m/${CLAVE}`;
const ADMIN = `${CLAVE}.administrar`;
const MAX_MB = 25;

// Íconos de línea de Lucide (ISC) que este módulo usa y la plataforma aún no trae.
Object.assign(LINEAS, {
  folder: '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  "folder-plus": '<path d="M12 10v6"/><path d="M9 13h6"/><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
  "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
  "file-up": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M12 12v6"/><path d="m15 15-3-3-3 3"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
  "ellipsis-vertical": '<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>',
  pencil: '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/>',
  "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  "chevron-right": '<path d="m9 18 6-6-6-6"/>',
  "external-link": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
  history: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
});

// ---------------------------------------------------------------- formato
function tamano(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024)).toLocaleString("es-CL")} KB`;
  return `${(bytes / 1048576).toLocaleString("es-CL", { maximumFractionDigits: 1 })} MB`;
}
const fechaCorta = (iso) => fechaLocal(iso).replace(/\.,? /, " ").replace(",", "");
function plural(n, uno, varios) { return `${n.toLocaleString("es-CL")} ${n === 1 ? uno : varios}`; }
function leerBase64(archivo) {
  return new Promise((ok, mal) => {
    const r = new FileReader();
    r.onload = () => ok(String(r.result).split(",", 2)[1] || "");
    r.onerror = () => mal(new Error("No pudimos leer el archivo."));
    r.readAsDataURL(archivo);
  });
}
function validarPdf(archivo) {
  if (!archivo) return "Elige un archivo PDF.";
  if (!/\.pdf$/i.test(archivo.name) && archivo.type !== "application/pdf") return "Solo se pueden subir documentos PDF.";
  if (archivo.size > MAX_MB * 1048576) return `El archivo pesa ${tamano(archivo.size)}. El máximo es ${MAX_MB} MB.`;
  return "";
}

(async function () {
  let pantalla = "documentos";
  let extra = [];
  let consulta = new URLSearchParams(location.search).get("q") || "";
  let carpetaActual = 0;
  const main = document.getElementById("contenido");

  const inicio = await iniciarModulo(CLAVE, {
    destinos: [
      { id: "documentos", etiqueta: "Documentos", icono: "folder" },
      { id: "buscar", etiqueta: "Buscar", icono: "search" },
      { id: "papelera", etiqueta: "Papelera", icono: "trash-2", permiso: ADMIN },
      { id: "acerca", etiqueta: "Acerca del módulo", icono: "info" },
    ],
    accion: { texto: "Subir PDF", icono: "upload", permiso: ADMIN, alHacer: () => subirDocumento() },
    buscar: { placeholder: "Buscar documentos", alBuscar: (q) => {
      consulta = q;
      if (pantalla === "buscar") { const i = document.getElementById("q"); if (i) i.value = q; pintarResultados(); }
      else ir("buscar");
    } },
    alNavegar: (id, resto) => { pantalla = id; extra = resto; repintar(); },
  });
  if (!inicio) return;
  const { modulo, ir } = inicio;
  const admin = modulo.puede(ADMIN);

  function repintar() {
    cerrarMenus();
    ({ documentos: pintarCarpeta, buscar: pintarBuscar, papelera: pintarPapelera, acerca: pintarAcerca }[pantalla]
      || pintarCarpeta)();
  }

  // ---------------------------------------------------------------- menú de acciones (⋮)
  function cerrarMenus() { document.querySelectorAll(".menu-acciones").forEach((m) => m.remove()); }
  function abrirMenu(boton, opciones) {
    const abierto = boton.getAttribute("aria-expanded") === "true";
    cerrarMenus();
    document.querySelectorAll("[aria-expanded='true'].btn-menu").forEach((b) => b.setAttribute("aria-expanded", "false"));
    if (abierto) return;
    const m = document.createElement("div");
    m.className = "menu-acciones"; m.setAttribute("role", "menu");
    m.innerHTML = opciones.map((o, i) => `<button role="menuitem" data-i="${i}" class="${o.peligro ? "peligro" : ""}">${linea(o.icono)}<span>${esc(o.texto)}</span></button>`).join("");
    boton.after(m);
    boton.setAttribute("aria-expanded", "true");
    const items = [...m.querySelectorAll("button")];
    items.forEach((b) => b.onclick = () => { cerrar(); opciones[Number(b.dataset.i)].alHacer(); });
    function cerrar() { m.remove(); boton.setAttribute("aria-expanded", "false"); }
    m.addEventListener("keydown", (e) => {
      const i = items.indexOf(document.activeElement);
      if (e.key === "Escape") { cerrar(); boton.focus(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
      else if (e.key === "Tab") cerrar();
    });
    items[0].focus();
  }
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".menu-acciones, .btn-menu")) {
      cerrarMenus();
      document.querySelectorAll(".btn-menu[aria-expanded='true']").forEach((b) => b.setAttribute("aria-expanded", "false"));
    }
  });

  // ---------------------------------------------------------------- filas
  function migas(ruta, enlazarUltima = false) {
    const pasos = [{ id: 0, nombre: "Inicio" }, ...ruta];
    return pasos.map((p, i) => (i === pasos.length - 1 && !enlazarUltima)
      ? `<span aria-current="page">${esc(p.nombre)}</span>`
      : `<a href="${modulo.url}documentos${p.id ? `/${p.id}` : ""}" data-carpeta="${p.id}">${esc(p.nombre)}</a>`)
      .join(`<span class="sep" aria-hidden="true">${linea("chevron-right")}</span>`);
  }
  function filaCarpeta(f) {
    const partes = [];
    if (f.subcarpetas) partes.push(plural(f.subcarpetas, "carpeta", "carpetas"));
    partes.push(plural(f.documentos, "documento", "documentos"));
    return `<li class="fila">
      <a class="fila-principal" href="${modulo.url}documentos/${f.id}" data-carpeta="${f.id}">
        <span class="fila-icono carpeta">${linea("folder")}</span>
        <span class="fila-texto"><span class="fila-titulo">${esc(f.nombre)}</span><span class="fila-meta">${esc(partes.join(" · "))}</span></span>
      </a>
      ${admin ? `<div class="fila-acciones"><button class="btn-icono btn-menu" aria-haspopup="menu" aria-expanded="false" data-menu-carpeta="${f.id}"
        aria-label="Más acciones para la carpeta ${esc(f.nombre)}" title="Más acciones">${linea("ellipsis-vertical")}</button></div>` : ""}
    </li>`;
  }
  function filaDocumento(d, { conRuta = false } = {}) {
    const meta = [`Actualizado el ${fechaCorta(d.actualizado_en)}`, tamano(d.tamano)];
    return `<li class="fila">
      <a class="fila-principal" href="${API}/documentos/${d.id}/archivo" target="_blank" rel="noopener"
         title="Abrir el PDF en una pestaña nueva">
        <span class="fila-icono">${linea("file-text")}</span>
        <span class="fila-texto"><span class="fila-titulo">${esc(d.titulo)}</span>
          ${d.descripcion ? `<span class="fila-desc">${esc(d.descripcion)}</span>` : ""}
          <span class="fila-meta">${esc(meta.join(" · "))}</span></span>
      </a>
      ${conRuta ? `<nav class="fila-ruta migas" aria-label="Ubicación de ${esc(d.titulo)}">${linea("folder")}${migas(d.ruta, true)}</nav>` : ""}
      <div class="fila-acciones">
        <a class="btn-icono" href="${API}/documentos/${d.id}/archivo?descargar=1" download aria-label="Descargar ${esc(d.titulo)}" title="Descargar">${linea("download")}</a>
        ${admin ? `<button class="btn-icono btn-menu" aria-haspopup="menu" aria-expanded="false" data-menu-doc="${d.id}"
          aria-label="Más acciones para ${esc(d.titulo)}" title="Más acciones">${linea("ellipsis-vertical")}</button>` : ""}
      </div>
    </li>`;
  }
  function conectarFilas(raiz, docs, carpetas) {
    raiz.querySelectorAll("a[data-carpeta]").forEach((a) => a.onclick = (e) => {
      if (e.ctrlKey || e.metaKey || e.shiftKey) return;
      e.preventDefault(); ir(`documentos${Number(a.dataset.carpeta) ? `/${a.dataset.carpeta}` : ""}`);
    });
    raiz.querySelectorAll("[data-menu-doc]").forEach((b) => b.onclick = () => {
      const d = docs.find((x) => x.id === Number(b.dataset.menuDoc));
      abrirMenu(b, [
        { texto: "Abrir en pestaña nueva", icono: "external-link", alHacer: () => window.open(`${API}/documentos/${d.id}/archivo`, "_blank", "noopener") },
        { texto: "Editar datos", icono: "pencil", alHacer: () => editarDocumento(d) },
        { texto: "Reemplazar PDF", icono: "file-up", alHacer: () => reemplazarDocumento(d) },
        { texto: "Enviar a la papelera", icono: "trash-2", peligro: true, alHacer: () => eliminarDocumento(d) },
      ]);
    });
    raiz.querySelectorAll("[data-menu-carpeta]").forEach((b) => b.onclick = () => {
      const f = carpetas.find((x) => x.id === Number(b.dataset.menuCarpeta));
      abrirMenu(b, [
        { texto: "Cambiar nombre o ubicación", icono: "pencil", alHacer: () => editarCarpeta(f) },
        { texto: "Eliminar carpeta", icono: "trash-2", peligro: true, alHacer: () => eliminarCarpeta(f) },
      ]);
    });
  }

  // ---------------------------------------------------------------- documentos (explorar carpetas)
  async function pintarCarpeta() {
    const cid = Number(extra[0]) || 0;
    carpetaActual = cid;
    main.innerHTML = `<nav class="migas" id="migas" aria-label="Ubicación"></nav>
      <div class="cabecera-pantalla"><h1 class="titulo-pantalla" id="titulo">Documentos</h1><span class="espacio"></span>
        ${admin ? `<button class="btn btn-borde" id="nueva-carpeta">${linea("folder-plus")}Nueva carpeta</button>` : ""}</div>
      <div id="lista"></div>`;
    if (admin) document.getElementById("nueva-carpeta").onclick = () => nuevaCarpeta(cid);
    const lista = document.getElementById("lista");
    cargando(true, lista);
    let r;
    try { r = await api(`${API}/carpetas/${cid}`); }
    catch (e) {
      cargando(false);
      if (e.status === 403) return estadoSinPermiso(lista, "Necesitas el permiso para ver los documentos.");
      if (e.status === 404) return estadoVacio(lista, "Esta carpeta ya no existe", "Puede que la hayan eliminado o movido.",
        { texto: "Ir al inicio", alHacer: () => ir("documentos") });
      return estadoError(lista, "No pudimos cargar los documentos.", pintarCarpeta);
    }
    cargando(false);
    if (pantalla !== "documentos" || carpetaActual !== cid) return;   // la persona ya navegó a otra parte
    document.getElementById("titulo").textContent = cid ? r.carpeta.nombre : "Documentos";
    const nav = document.getElementById("migas");
    if (cid) nav.innerHTML = migas(r.ruta); else nav.remove();
    if (!r.subcarpetas.length && !r.documentos.length) {
      return estadoVacio(lista, cid ? "Esta carpeta está vacía" : "Aún no hay documentos",
        admin ? "Sube un PDF o crea una carpeta para ordenar los documentos." : "Los documentos que publique el hospital aparecerán aquí.",
        admin ? { texto: "Subir PDF", alHacer: () => subirDocumento() } : null);
    }
    lista.innerHTML = `
      ${r.subcarpetas.length ? `<h2 class="titulo-seccion">Carpetas</h2><ul class="lista tarjeta">${r.subcarpetas.map(filaCarpeta).join("")}</ul>` : ""}
      ${r.documentos.length ? `<h2 class="titulo-seccion">Documentos</h2><ul class="lista tarjeta">${r.documentos.map((d) => filaDocumento(d)).join("")}</ul>` : ""}`;
    conectarFilas(main, r.documentos, r.subcarpetas);
  }

  // ---------------------------------------------------------------- buscar
  function pintarBuscar() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Buscar documentos</h1></div>
      <form class="buscador-grande" id="form-q" role="search">
        <label for="q" class="sr">Buscar documentos</label>
        ${linea("search")}
        <input id="q" type="search" autocomplete="off" maxlength="200" placeholder="Escribe parte del título, la descripción o la carpeta">
      </form>
      <div id="resultados" aria-live="polite"></div>`;
    const i = document.getElementById("q");
    i.value = consulta;
    let t;
    i.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { consulta = i.value.trim(); pintarResultados(); }, 250); });
    document.getElementById("form-q").onsubmit = (e) => { e.preventDefault(); consulta = i.value.trim(); pintarResultados(); };
    i.focus();
    pintarResultados();
  }
  let _busqueda = 0;
  async function pintarResultados() {
    const cont = document.getElementById("resultados");
    if (!cont) return;
    const q = consulta.trim();
    history.replaceState(null, "", `${modulo.url}buscar${q ? `?q=${encodeURIComponent(q)}` : ""}`);
    if (!q) {
      cont.innerHTML = `<p class="pista">Por ejemplo: «caídas», «lavado de manos» o el nombre de una carpeta. No importan las tildes ni las mayúsculas.</p>`;
      return;
    }
    const yo = ++_busqueda;
    cargando(true, cont);
    let r;
    try { r = await api(`${API}/buscar?q=${encodeURIComponent(q)}`); }
    catch (e) {
      cargando(false);
      if (e.status === 403) return estadoSinPermiso(cont, "Necesitas el permiso para ver los documentos.");
      return estadoError(cont, "No pudimos buscar los documentos.", pintarResultados);
    }
    cargando(false);
    if (yo !== _busqueda) return;   // llegó una búsqueda más nueva
    if (!r.documentos.length && !r.carpetas.length) {
      return estadoVacio(cont, "Sin resultados", `No hay documentos ni carpetas que coincidan con «${q}». Prueba con otra palabra.`);
    }
    const mas = r.total > r.documentos.length ? ` Se muestran los primeros ${r.documentos.length}; escribe algo más preciso para acotar.` : "";
    cont.innerHTML = `
      <p class="pista">${esc(plural(r.total, "documento encontrado", "documentos encontrados"))}.${esc(mas)}</p>
      ${r.carpetas.length ? `<h2 class="titulo-seccion">Carpetas</h2><ul class="lista tarjeta">${r.carpetas.map((f) => `<li class="fila">
          <a class="fila-principal" href="${modulo.url}documentos/${f.id}" data-carpeta="${f.id}">
            <span class="fila-icono carpeta">${linea("folder")}</span>
            <span class="fila-texto"><span class="fila-titulo">${esc(f.nombre)}</span>
              <span class="fila-meta">${esc(["Inicio", ...f.ruta.map((p) => p.nombre)].join(" › "))}</span></span></a></li>`).join("")}</ul>` : ""}
      ${r.documentos.length ? `<h2 class="titulo-seccion">Documentos</h2><ul class="lista tarjeta">${r.documentos.map((d) => filaDocumento(d, { conRuta: true })).join("")}</ul>` : ""}`;
    conectarFilas(cont, r.documentos, []);
  }

  // ---------------------------------------------------------------- papelera
  async function pintarPapelera() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Papelera</h1></div>
      <p class="aviso-suave">${linea("info")}<span>Lo que envías a la papelera se guarda 30 días. Las versiones reemplazadas quedan 5 años como
        historial, para saber qué versión estaba vigente en cada fecha. Después se borran solos. Mientras tanto puedes restaurarlos.</span></p>
      <div id="lista"></div>`;
    const lista = document.getElementById("lista");
    if (!admin) return estadoSinPermiso(lista, "Solo quienes administran documentos ven la papelera.");
    cargando(true, lista);
    let r;
    try { r = await api(`${API}/papelera`); }
    catch (e) {
      cargando(false);
      if (e.status === 403) return estadoSinPermiso(lista, "Solo quienes administran documentos ven la papelera.");
      return estadoError(lista, "No pudimos cargar la papelera.", pintarPapelera);
    }
    cargando(false);
    if (!r.documentos.length && !r.versiones.length) {
      return estadoVacio(lista, "La papelera está vacía", "Aquí aparecerán los documentos que elimines y las versiones que reemplaces.");
    }
    const quedan = (f) => f.dias <= 0 ? "Se borra hoy" : `Se borra en ${plural(f.dias, "día", "días")}`;
    const ubic = (f) => ["Inicio", ...f.ruta.map((p) => p.nombre)].join(" › ");
    const fila = (f, tipo) => {
      const url = `${API}/papelera/${tipo}/${f.id}/archivo`;
      const titulo = tipo === "versiones" ? `${f.titulo} · versión subida el ${fechaCorta(f.subida_en)}` : f.titulo;
      const meta = [`${tipo === "versiones" ? "Reemplazada" : "Eliminado"} el ${fechaCorta(f.fecha)} por ${f.por}`, ubic(f), tamano(f.tamano)];
      return `<li class="fila">
        <a class="fila-principal" href="${url}" target="_blank" rel="noopener" title="Abrir el PDF en una pestaña nueva">
          <span class="fila-icono">${linea(tipo === "versiones" ? "history" : "file-text")}</span>
          <span class="fila-texto"><span class="fila-titulo">${esc(titulo)}</span>
            <span class="fila-meta">${esc(meta.join(" · "))}</span>
            <span class="fila-meta quedan">${esc(quedan(f))}</span></span></a>
        <div class="fila-acciones">
          <button class="btn btn-texto" data-restaurar="${tipo}/${f.id}">${linea("rotate-ccw")}Restaurar</button>
          <button class="btn-icono" data-borrar="${tipo}/${f.id}" aria-label="Eliminar para siempre: ${esc(titulo)}" title="Eliminar para siempre">${linea("trash-2")}</button>
        </div></li>`;
    };
    lista.innerHTML = `
      ${r.documentos.length ? `<h2 class="titulo-seccion">Documentos eliminados</h2><ul class="lista tarjeta">${r.documentos.map((f) => fila(f, "documentos")).join("")}</ul>` : ""}
      ${r.versiones.length ? `<h2 class="titulo-seccion">Historial de versiones (5 años)</h2>
        <p class="pista">Restaurar una versión la vuelve a publicar; la que está publicada ahora pasa a la papelera.</p>
        <ul class="lista tarjeta">${r.versiones.map((f) => fila(f, "versiones")).join("")}</ul>` : ""}`;
    lista.querySelectorAll("[data-restaurar]").forEach((b) => b.onclick = async () => {
      b.disabled = true;
      try {
        await api(`${API}/papelera/${b.dataset.restaurar}/restaurar`, { metodo: "POST" });
        toast(b.dataset.restaurar.startsWith("versiones") ? "Versión restaurada. Ahora es la publicada." : "Documento restaurado.");
        pintarPapelera();
      } catch (e) { b.disabled = false; toast(e.message); }
    });
    lista.querySelectorAll("[data-borrar]").forEach((b) => b.onclick = async () => {
      const ok = await confirmarDestructivo({ titulo: "¿Eliminar para siempre?",
        texto: "El PDF se borrará del sistema y no se podrá recuperar.", verbo: "Eliminar para siempre" });
      if (!ok) return;
      try { await api(`${API}/papelera/${b.dataset.borrar}`, { metodo: "DELETE" }); toast("Eliminado para siempre."); pintarPapelera(); }
      catch (e) { toast(e.message); }
    });
  }

  // ---------------------------------------------------------------- acerca (transparencia: ficha de tratamiento)
  function pintarAcerca() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Acerca del módulo</h1></div>
      <section class="tarjeta ficha"><h2 class="titulo-seccion">${esc(modulo.nombre)}</h2>
        <dl><dt>Qué hace</dt><dd>${esc(modulo.descripcion)}</dd>
          <dt>Quién lo administra</dt><dd>Solo las personas con el permiso «Administrar documentos» crean carpetas, suben,
            reemplazan y eliminan. Si lo necesitas, pídelo a la Unidad de Innovación y Desarrollo.</dd>
          <dt>Archivos</dt><dd>Solo PDF, hasta ${MAX_MB} MB cada uno.</dd>
          <dt>Papelera e historial</dt><dd>Lo eliminado se guarda 30 días. Las versiones reemplazadas quedan 5 años como historial. Luego se borran.</dd>
          <dt>Para qué usa datos</dt><dd>${esc(modulo.finalidad)}</dd>
          <dt>Versión</dt><dd>${esc(modulo.version)}</dd></dl></section>`;
  }

  // ---------------------------------------------------------------- diálogos (administrar)
  async function opcionesCarpetas(elegida, excluir = null) {
    let arbol = [];
    try { arbol = await api(`${API}/arbol`); } catch (_) { /* queda solo el inicio */ }
    // Al mover una carpeta no se ofrece ella misma ni lo que tiene dentro.
    const fuera = new Set();
    if (excluir) {
      fuera.add(excluir);
      let cambio = true;
      while (cambio) { cambio = false; arbol.forEach((f) => { if (fuera.has(f.padre_id) && !fuera.has(f.id)) { fuera.add(f.id); cambio = true; } }); }
    }
    return [`<option value="0"${!elegida ? " selected" : ""}>Inicio</option>`,
      ...arbol.filter((f) => !fuera.has(f.id)).map((f) => `<option value="${f.id}"${f.id === elegida ? " selected" : ""}>Inicio › ${esc(f.ruta)}</option>`)].join("");
  }
  const AVISO_PDF = `<p class="aviso-suave chico">${linea("shield")}<span>Sube solo documentos institucionales. No subas documentos con datos de pacientes ni de otras personas.</span></p>`;

  async function subirDocumento() {
    const destino = pantalla === "documentos" ? carpetaActual : 0;
    const opciones = await opcionesCarpetas(destino);
    let archivo = null;
    dialogo({
      titulo: "Subir PDF",
      html: `${AVISO_PDF}
        <div class="elegir-archivo"><input type="file" id="sd-archivo" accept=".pdf,application/pdf" class="sr">
          <label for="sd-archivo" class="btn btn-borde">${linea("upload")}Elegir PDF</label>
          <span id="sd-nombre" class="fila-meta">Ningún archivo elegido (máximo ${MAX_MB} MB)</span></div>
        <div class="campo"><input id="sd-titulo" placeholder=" " maxlength="150"><label for="sd-titulo">Título</label>
          <div class="ayuda">Así lo verán y buscarán las personas. Por ejemplo: «Protocolo de prevención de caídas».</div></div>
        <div class="campo"><textarea id="sd-desc" placeholder=" " maxlength="500"></textarea><label for="sd-desc">Descripción (opcional)</label></div>
        <div class="campo"><select id="sd-carpeta">${opciones}</select><label for="sd-carpeta">Carpeta</label></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Subir documento", alHacer: async (v) => {
        const zona = v.querySelector(".zona-error");
        const problema = validarPdf(archivo);
        if (problema) { mostrarErrorEn(zona, problema); return false; }
        mostrarErrorEn(zona, "");
        try {
          await api(`${API}/documentos`, { metodo: "POST", datos: {
            titulo: v.querySelector("#sd-titulo").value, descripcion: v.querySelector("#sd-desc").value,
            carpeta_id: Number(v.querySelector("#sd-carpeta").value) || null,
            nombre_archivo: archivo.name, contenido: await leerBase64(archivo) } });
        } catch (e) { mostrarErrorEn(zona, e.status === 422 && e.message === "Revisa los datos ingresados." ? "Revisa el título: debe tener entre 3 y 150 caracteres." : e.message); return false; }
        toast("Documento subido.");
        const cid = Number(v.querySelector("#sd-carpeta").value) || 0;
        if (pantalla === "documentos" && cid === carpetaActual) pintarCarpeta(); else ir(`documentos${cid ? `/${cid}` : ""}`);
        return true;
      } }],
    });
    const input = document.getElementById("sd-archivo");
    input.onchange = () => {
      archivo = input.files[0] || null;
      const zona = input.closest(".dialogo").querySelector(".zona-error");
      document.getElementById("sd-nombre").textContent = archivo ? `${archivo.name} · ${tamano(archivo.size)}` : "Ningún archivo elegido";
      mostrarErrorEn(zona, validarPdf(archivo));
      const t = document.getElementById("sd-titulo");
      if (archivo && !t.value.trim()) t.value = archivo.name.replace(/\.pdf$/i, "").replace(/[_-]+/g, " ").trim().slice(0, 150);
    };
  }

  async function reemplazarDocumento(d) {
    let archivo = null;
    dialogo({
      titulo: "Reemplazar PDF",
      html: `<p class="dlg-texto">Sube la versión nueva de «${esc(d.titulo)}». La versión actual quedará 5 años en el historial por si necesitas volver a ella.</p>
        ${AVISO_PDF}
        <div class="elegir-archivo"><input type="file" id="rp-archivo" accept=".pdf,application/pdf" class="sr">
          <label for="rp-archivo" class="btn btn-borde">${linea("upload")}Elegir PDF</label>
          <span id="rp-nombre" class="fila-meta">Ningún archivo elegido (máximo ${MAX_MB} MB)</span></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Reemplazar PDF", alHacer: async (v) => {
        const zona = v.querySelector(".zona-error");
        const problema = validarPdf(archivo);
        if (problema) { mostrarErrorEn(zona, problema); return false; }
        try {
          await api(`${API}/documentos/${d.id}/version`, { metodo: "POST", datos: {
            nombre_archivo: archivo.name, contenido: await leerBase64(archivo) } });
        } catch (e) { mostrarErrorEn(zona, e.message); return false; }
        toast("PDF reemplazado. La versión anterior quedó en el historial."); repintar(); return true;
      } }],
    });
    const input = document.getElementById("rp-archivo");
    input.onchange = () => {
      archivo = input.files[0] || null;
      document.getElementById("rp-nombre").textContent = archivo ? `${archivo.name} · ${tamano(archivo.size)}` : "Ningún archivo elegido";
      mostrarErrorEn(input.closest(".dialogo").querySelector(".zona-error"), validarPdf(archivo));
    };
  }

  async function editarDocumento(d) {
    const opciones = await opcionesCarpetas(d.carpeta_id || 0);
    dialogo({
      titulo: "Editar datos del documento",
      html: `<div class="campo"><input id="ed-titulo" placeholder=" " maxlength="150" value="${esc(d.titulo)}"><label for="ed-titulo">Título</label></div>
        <div class="campo"><textarea id="ed-desc" placeholder=" " maxlength="500">${esc(d.descripcion)}</textarea><label for="ed-desc">Descripción (opcional)</label></div>
        <div class="campo"><select id="ed-carpeta">${opciones}</select><label for="ed-carpeta">Carpeta</label></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar cambios", alHacer: async (v) => {
        try {
          await api(`${API}/documentos/${d.id}`, { metodo: "PATCH", datos: {
            titulo: v.querySelector("#ed-titulo").value, descripcion: v.querySelector("#ed-desc").value,
            carpeta_id: Number(v.querySelector("#ed-carpeta").value) || null } });
        } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.status === 422 && e.message === "Revisa los datos ingresados." ? "El título debe tener entre 3 y 150 caracteres." : e.message); return false; }
        toast("Cambios guardados."); repintar(); return true;
      } }],
    });
  }

  async function eliminarDocumento(d) {
    try { await api(`${API}/documentos/${d.id}`, { metodo: "DELETE" }); }
    catch (e) { toast(e.message); return; }
    repintar();
    toast("Documento enviado a la papelera.", 8000);
    const t = document.querySelector(".toast");
    if (!t) return;
    const deshacer = document.createElement("button");
    deshacer.textContent = "Deshacer";
    deshacer.onclick = async () => {
      t.remove();
      try { await api(`${API}/papelera/documentos/${d.id}/restaurar`, { metodo: "POST" }); toast("Documento restaurado."); repintar(); }
      catch (e) { toast(e.message); }
    };
    t.appendChild(deshacer);
  }

  async function nuevaCarpeta(padre) {
    dialogo({
      titulo: "Nueva carpeta",
      html: `<div class="campo"><input id="nc-nombre" placeholder=" " maxlength="80"><label for="nc-nombre">Nombre de la carpeta</label></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Crear carpeta", alHacer: async (v) => {
        const nombre = v.querySelector("#nc-nombre").value.trim();
        if (!nombre) { mostrarErrorEn(v.querySelector(".zona-error"), "Escribe el nombre de la carpeta."); return false; }
        try { await api(`${API}/carpetas`, { metodo: "POST", datos: { nombre, padre_id: padre || null } }); }
        catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
        toast("Carpeta creada."); pintarCarpeta(); return true;
      } }],
    });
  }

  async function editarCarpeta(f) {
    const opciones = await opcionesCarpetas(carpetaActual, f.id);
    dialogo({
      titulo: "Cambiar nombre o ubicación",
      html: `<div class="campo"><input id="ec-nombre" placeholder=" " maxlength="80" value="${esc(f.nombre)}"><label for="ec-nombre">Nombre de la carpeta</label></div>
        <div class="campo"><select id="ec-padre">${opciones}</select><label for="ec-padre">Dentro de</label></div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar cambios", alHacer: async (v) => {
        try {
          await api(`${API}/carpetas/${f.id}`, { metodo: "PATCH", datos: {
            nombre: v.querySelector("#ec-nombre").value, mover: true, padre_id: Number(v.querySelector("#ec-padre").value) || null } });
        } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
        toast("Carpeta actualizada."); pintarCarpeta(); return true;
      } }],
    });
  }

  async function eliminarCarpeta(f) {
    if (f.documentos || f.subcarpetas) {
      return dialogo({ titulo: "La carpeta no está vacía",
        html: `<p class="dlg-texto">«${esc(f.nombre)}» tiene ${esc([f.subcarpetas ? plural(f.subcarpetas, "carpeta", "carpetas") : "", f.documentos ? plural(f.documentos, "documento", "documentos") : ""].filter(Boolean).join(" y "))}. Muévelos o envíalos a la papelera antes de eliminarla.</p>`,
        acciones: [{ texto: "Entendido", valor: null }] });
    }
    const ok = await confirmarDestructivo({ titulo: `¿Eliminar la carpeta «${f.nombre}»?`,
      texto: "La carpeta está vacía. Se elimina de inmediato y no pasa por la papelera.", verbo: "Eliminar carpeta" });
    if (!ok) return;
    try { await api(`${API}/carpetas/${f.id}`, { metodo: "DELETE" }); toast("Carpeta eliminada."); pintarCarpeta(); }
    catch (e) { toast(e.message); }
  }
})();
