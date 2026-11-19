// Módulo F+mefi — Simulador docente y evaluador determinístico MEFI v2.0
// (Protocolo Institucional V2 sept. 2025, ACOG CPG No. 10 2025, FIGO 2015 y NICE NG229).
// Sin datos de pacientes: uso exclusivo para entrenamiento y simulación de funcionarios clínicos.
"use strict";

const CLAVE = "monitoreo_fetal";
const API = `/api/m/${CLAVE}`;

const ETIQUETA_RIESGO = {
  no_aplica: "No aplica",
  con_rasgos_protectores: "Box 3 ACOG: Con rasgos protectores",
  intermedio: "Box 3 ACOG: Riesgo intermedio",
  alto: "Box 3 ACOG: Alto riesgo",
};

const ETIQUETA_HIPOXIA = {
  sin_hipoxia: "Sin signos de hipoxia evolutiva",
  aguda: "Hipoxia aguda (Protocolo V2)",
  subaguda: "Hipoxia subaguda (Protocolo V2)",
  progresiva: "Hipoxia progresiva (Protocolo V2)",
  cronica: "Hipoxia crónica preexistente (Protocolo V2)",
};

(async function () {
  let filtro = "";
  let pantalla = "mias";
  const main = document.getElementById("contenido");

  const inicio = await iniciarModulo(CLAVE, {
    destinos: [
      // Cada persona ve sus propias simulaciones; las de todos, solo quien modera (privacidad entre colegas).
      { id: "mias", etiqueta: "Mías", icono: "user", permiso: `${CLAVE}.simular` },
      { id: "todas", etiqueta: "Todas", icono: "list", permiso: `${CLAVE}.moderar` },
      { id: "casos", etiqueta: "Casos", icono: "inbox" },
      { id: "acerca", etiqueta: "Acerca", icono: "info" },
    ],
    accion: { texto: "Nueva simulación", icono: "plus", permiso: `${CLAVE}.simular`, alHacer: () => nuevaSimulacion() },
    buscar: {
      placeholder: "Buscar simulaciones",
      alBuscar: (q) => {
        filtro = q.toLowerCase();
        if (pantalla === "todas" || pantalla === "mias") pintarSimulaciones();
      },
    },
    alNavegar: (id) => {
      pantalla = id;
      if (id === "casos") pintarCasosDocentes();
      else if (id === "acerca") pintarAcerca();
      else pintarSimulaciones();
    },
  });
  if (!inicio) return;
  const { modulo } = inicio;

  function claseCategoria(cat) {
    if (cat === "I") return "cat-i";
    if (cat === "III") return "cat-iii";
    return "cat-ii";
  }

  // ---------------------------------------------------------------- lista de simulaciones
  async function pintarSimulaciones() {
    const mias = pantalla !== "todas" || !modulo.puede(`${CLAVE}.moderar`);
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">${mias ? "Mis simulaciones" : "Simulaciones de la unidad"}</h1></div>
      <p class="aviso-suave" style="max-width:840px">${linea("shield")}<span>Entorno exclusivo de simulación docente (Protocolo V2 / ACOG CPG No. 10 / FIGO 2015). No escribas nombres, RUT ni otros datos de pacientes en el título ni en la nota. Los ejercicios se depuran automáticamente al cumplir un año.</span></p>
      <div class="lista-simulaciones" id="lista" style="margin-top:16px"></div>`;
    const lista = document.getElementById("lista");
    cargando(true, lista);
    let filas;
    try {
      filas = await api(`${API}/simulaciones${mias ? "?mias=1" : ""}`);
    } catch (e) {
      cargando(false);
      if (e.status === 403) return estadoSinPermiso(lista, "Necesitas permiso para consultar las simulaciones de este módulo.");
      return estadoError(lista, "No pudimos cargar las simulaciones.", pintarSimulaciones);
    }
    cargando(false);
    const visibles = filtro
      ? filas.filter((s) => `${s.titulo} ${s.autor} ${s.categoria_figo} ${s.nota_docente}`.toLowerCase().includes(filtro))
      : filas;

    if (!visibles.length) {
      if (filtro) return estadoVacio(lista, "Sin resultados", `No hay simulaciones que coincidan con «${filtro}».`);
      return estadoVacio(
        lista,
        mias ? "Aún no registras simulaciones" : "Aún no hay simulaciones registradas",
        "Crea una simulación con parámetros cardiotocográficos o carga uno de los casos docentes de estudio.",
        modulo.puede(`${CLAVE}.simular`) ? { texto: "Registrar primera simulación", alHacer: () => nuevaSimulacion() } : null
      );
    }

    lista.innerHTML = visibles
      .map(
        (s) => `
      <article class="tarjeta simulacion">
        <div class="fila-cabecera-tarjeta">
          <h2>${esc(s.titulo)}</h2>
          <div class="chips-normativos">
            <span class="chip-cat ${claseCategoria(s.categoria_figo)}">MEFI / FIGO Categoría ${esc(s.categoria_figo)}</span>
            <span class="chip-cat">ACOG estricta: Cat. ${esc(s.categoria_acog)}</span>
            ${s.riesgo_cat_ii !== "no_aplica" ? `<span class="chip-cat">${esc(ETIQUETA_RIESGO[s.riesgo_cat_ii] || s.riesgo_cat_ii)}</span>` : ""}
            <span class="chip-cat">${esc(ETIQUETA_HIPOXIA[s.hipoxia_tipificada] || s.hipoxia_tipificada)}</span>
          </div>
        </div>
        <div class="metricas-grid">
          <div class="metrica-item">Edad gestacional<strong>${esc(String(s.edad_gestacional_sem))} sem</strong></div>
          <div class="metrica-item">Línea base FCF<strong>${esc(String(s.linea_base_lpm))} lpm</strong></div>
          <div class="metrica-item">Variabilidad NICHD<strong>${esc(String(s.variabilidad_lpm))} lpm (${esc(s.categoria_nichd)})</strong></div>
          <div class="metrica-item">Aceleraciones<strong>${esc(String(s.num_aceleraciones))} eventos</strong></div>
          <div class="metrica-item">Desaceleraciones<strong>${esc(String(s.num_desaceleraciones))} (${esc(s.tipo_desaceleracion)}, máx ${esc(String(s.duracion_max_decel_s))} s)</strong></div>
          <div class="metrica-item">Dinámica uterina<strong>${esc(String(s.contracciones_10min))} / 10 min</strong></div>
        </div>
        <div class="conducta-box">${esc(s.resumen_conducta)}</div>
        ${s.nota_docente ? `<p>${esc(s.nota_docente)}</p>` : ""}
        <div class="pie-simulacion">
          <span class="autor"><span class="avatar" data-nombre="${esc(s.autor)}"></span>${esc(s.autor)} · ${esc(fechaLocal(s.creado_en))}</span>
          ${s.puede_borrar ? `<button class="btn-icono" data-borrar="${s.id}" aria-label="Borrar simulación" title="Borrar simulación">${linea("trash-2")}</button>` : ""}
        </div>
      </article>`
      )
      .join("");

    lista.querySelectorAll(".avatar[data-nombre]").forEach((el) => pintarAvatar(el, el.dataset.nombre));
    lista.querySelectorAll("[data-borrar]").forEach((b) => {
      b.onclick = async () => {
        const ok = await confirmarDestructivo({
          titulo: "¿Borrar esta simulación?",
          texto: "Se eliminará del registro docente de la unidad. No se puede deshacer.",
          verbo: "Borrar simulación",
        });
        if (!ok) return;
        try {
          await api(`${API}/simulaciones/${b.dataset.borrar}`, { metodo: "DELETE" });
          toast("Simulación borrada.");
          pintarSimulaciones();
        } catch (e) {
          toast(e.message);
        }
      };
    });
  }

  // ---------------------------------------------------------------- casos docentes preconfigurados
  async function pintarCasosDocentes() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Casos docentes de entrenamiento</h1></div>
      <p class="aviso-suave" style="max-width:960px">${linea("info")}<span>Escenarios sintéticos validados según el Protocolo de Vigilancia del Bienestar Fetal Intraparto V2 (sept. 2025), ACOG CPG No. 10 (2025) y FIGO 2015. Puedes cargar cualquiera en el simulador con un clic.</span></p>
      <div class="grilla-casos" id="grilla-casos"></div>`;
    const contenedor = document.getElementById("grilla-casos");
    cargando(true, contenedor);
    let casos;
    try {
      casos = await api(`${API}/casos-docentes`);
    } catch (e) {
      cargando(false);
      if (e.status === 403) return estadoSinPermiso(contenedor, "Necesitas permiso para ver los casos docentes.");
      return estadoError(contenedor, "No pudimos cargar los casos docentes.", pintarCasosDocentes);
    }
    cargando(false);
    if (!casos.length) {
      return estadoVacio(contenedor, "Sin casos docentes", "Los escenarios de estudio aparecerán aquí.");
    }
    contenedor.innerHTML = casos
      .map(
        (c, idx) => `
      <article class="tarjeta caso-docente">
        <div class="chips-normativos">
          <span class="chip-cat ${claseCategoria(c.categoria_figo)}">Categoría FIGO ${esc(c.categoria_figo)}</span>
          <span class="chip-cat">ACOG: Cat. ${esc(c.categoria_acog)}</span>
          <span class="chip-cat">${esc(ETIQUETA_HIPOXIA[c.hipoxia_tipificada] || c.hipoxia_tipificada)}</span>
        </div>
        <h2>${esc(c.titulo)}</h2>
        <p>${esc(c.descripcion)}</p>
        <div class="metricas-grid">
          <div class="metrica-item">Basal FCF<strong>${esc(String(c.linea_base_lpm))} lpm</strong></div>
          <div class="metrica-item">Variabilidad<strong>${esc(String(c.variabilidad_lpm))} lpm (${esc(c.categoria_nichd)})</strong></div>
          <div class="metrica-item">Desaceleraciones<strong>${esc(String(c.num_desaceleraciones))} (${esc(c.tipo_desaceleracion)})</strong></div>
          <div class="metrica-item">Contracciones<strong>${esc(String(c.contracciones_10min))} / 10m</strong></div>
        </div>
        <div class="conducta-box">${esc(c.resumen_conducta)}</div>
        ${modulo.puede(`${CLAVE}.simular`) ? `<button class="btn btn-borde" data-cargar-caso="${idx}">Simular este escenario</button>` : ""}
      </article>`
      )
      .join("");

    contenedor.querySelectorAll("[data-cargar-caso]").forEach((btn) => {
      btn.onclick = () => nuevaSimulacion(casos[Number(btn.dataset.cargarCaso)]);
    });
  }

  // ---------------------------------------------------------------- acerca del módulo
  function pintarAcerca() {
    main.innerHTML = `<div class="cabecera-pantalla"><h1 class="titulo-pantalla">Acerca del módulo</h1></div>
      <section class="tarjeta ficha"><h2 class="titulo-seccion">${esc(modulo.nombre)} (Motor determinístico v2.0)</h2>
        <dl>
          <dt>Qué hace</dt><dd>${esc(modulo.descripcion)}</dd>
          <dt>Base normativa</dt><dd>Protocolo de Vigilancia del Bienestar Fetal Intraparto V2 (sept. 2025) · ACOG Clinical Practice Guideline No. 10 (2025) · FIGO 2015 · NICE NG229.</dd>
          <dt>Validación científica</dt><dd>Motor determinístico validado contra 552 registros intraparto CTU-UHB (pH de cordón &lt; 7,05): sensibilidad 95,0 % y valor predictivo negativo (VPN) 96,6 %.</dd>
          <dt>Aviso regulador</dt><dd>Herramienta docente y de apoyo a la decisión clínica; no reemplaza el juicio profesional presencial (ACOG CPG No. 10 / Ensayo INFANT, Lancet 2017).</dd>
          <dt>Para qué usa datos</dt><dd>${esc(modulo.finalidad)}</dd>
          <dt>Versión</dt><dd>${esc(modulo.version)}</dd>
        </dl>
      </section>`;
  }

  // ---------------------------------------------------------------- diálogo de nueva simulación
  function nuevaSimulacion(preset = null) {
    const p = preset || {
      titulo: "",
      escenario: "personalizado",
      edad_gestacional_sem: 39,
      linea_base_lpm: 140,
      variabilidad_lpm: 12,
      num_aceleraciones: 2,
      num_desaceleraciones: 0,
      tipo_desaceleracion: "ninguna",
      duracion_max_decel_s: 0,
      contracciones_10min: 3.0,
      patron_sinusoidal: false,
      nota_docente: "",
    };
    dialogo({
      titulo: preset ? "Simular escenario docente" : "Nueva simulación cardiotocográfica",
      html: `<div class="campo"><input id="sim-titulo" placeholder=" " maxlength="100" value="${esc(p.titulo)}"><label for="sim-titulo">Título del ejercicio docente</label></div>
             <div class="grilla-campos-dlg">
               <div class="campo"><input id="sim-eg" type="number" min="24" max="43" placeholder=" " value="${esc(String(p.edad_gestacional_sem))}"><label for="sim-eg">Edad gestacional (sem)</label></div>
               <div class="campo"><input id="sim-basal" type="number" min="50" max="220" step="5" placeholder=" " value="${esc(String(p.linea_base_lpm))}"><label for="sim-basal">Línea base FCF (lpm)</label></div>
               <div class="campo"><input id="sim-var" type="number" min="0" max="60" step="0.5" placeholder=" " value="${esc(String(p.variabilidad_lpm))}"><label for="sim-var">Variabilidad (lpm)</label></div>
               <div class="campo"><input id="sim-acel" type="number" min="0" max="40" placeholder=" " value="${esc(String(p.num_aceleraciones))}"><label for="sim-acel">N° aceleraciones</label></div>
               <div class="campo"><input id="sim-decel" type="number" min="0" max="40" placeholder=" " value="${esc(String(p.num_desaceleraciones))}"><label for="sim-decel">N° desaceleraciones</label></div>
               <div class="campo">
                 <select id="sim-tipo-dec">
                   <option value="ninguna" ${p.tipo_desaceleracion === "ninguna" ? "selected" : ""}>Ninguna</option>
                   <option value="precoz" ${p.tipo_desaceleracion === "precoz" ? "selected" : ""}>Precoz (cefálica)</option>
                   <option value="variable" ${p.tipo_desaceleracion === "variable" ? "selected" : ""}>Variable (cordón)</option>
                   <option value="tardia" ${p.tipo_desaceleracion === "tardia" ? "selected" : ""}>Tardía (uteroplacentaria)</option>
                   <option value="prolongada" ${p.tipo_desaceleracion === "prolongada" ? "selected" : ""}>Prolongada (≥2 min)</option>
                 </select>
                 <label for="sim-tipo-dec">Tipo de desaceleración</label>
               </div>
               <div class="campo"><input id="sim-dur-dec" type="number" min="0" max="600" step="5" placeholder=" " value="${esc(String(p.duracion_max_decel_s))}"><label for="sim-dur-dec">Duración máx. desacel. (s)</label></div>
               <div class="campo"><input id="sim-ua" type="number" min="0" max="15" step="0.5" placeholder=" " value="${esc(String(p.contracciones_10min))}"><label for="sim-ua">Contracciones / 10 min</label></div>
             </div>
             <label class="check" style="margin:4px 0 16px"><input id="sim-sin" type="checkbox" ${p.patron_sinusoidal ? "checked" : ""}><span>Patrón sinusoidal presente (3–5 cpm por ≥20 min)</span></label>
             <div class="campo"><textarea id="sim-nota" placeholder=" " maxlength="600">${esc(p.nota_docente || "")}</textarea><label for="sim-nota">Reflexión docente / conducta propuesta</label>
               <div class="ayuda">No escribas nombres, RUT ni datos de pacientes.</div></div>
             <div class="zona-error"></div>`,
      acciones: [
        { texto: "Cancelar", clase: "btn btn-texto", valor: null },
        {
          texto: "Evaluar y guardar simulación",
          alHacer: async (v) => {
            try {
              await api(`${API}/simulaciones`, {
                metodo: "POST",
                datos: {
                  titulo: v.querySelector("#sim-titulo").value,
                  escenario: p.escenario || "personalizado",
                  edad_gestacional_sem: Number(v.querySelector("#sim-eg").value),
                  linea_base_lpm: Number(v.querySelector("#sim-basal").value),
                  variabilidad_lpm: Number(v.querySelector("#sim-var").value),
                  num_aceleraciones: Number(v.querySelector("#sim-acel").value),
                  num_desaceleraciones: Number(v.querySelector("#sim-decel").value),
                  tipo_desaceleracion: v.querySelector("#sim-tipo-dec").value,
                  duracion_max_decel_s: Number(v.querySelector("#sim-dur-dec").value),
                  contracciones_10min: Number(v.querySelector("#sim-ua").value),
                  patron_sinusoidal: v.querySelector("#sim-sin").checked,
                  nota_docente: v.querySelector("#sim-nota").value,
                },
              });
            } catch (e) {
              mostrarErrorEn(v.querySelector(".zona-error"), e.message);
              return false;
            }
            toast("Simulación evaluada y registrada.");
            if (pantalla === "casos" || pantalla === "acerca") inicio.ir("todas");
            else pintarSimulaciones();
            return true;
          },
        },
      ],
    });
  }
})();
