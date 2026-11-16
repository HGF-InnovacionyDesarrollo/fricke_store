"use strict";

const ESTADOS_DERECHO = { recibida: "Recibida", en_revision: "En revisión", respondida: "Respondida", rechazada: "Rechazada" };
const ICONOS_MODULO = ["modulos", "documento", "persona", "escudo", "historial", "dispositivo", "inicio", "candado", "chispa"];
let ROLES = {}, MI_ROL = "", YO = null;

const $ = (s, r = document) => r.querySelector(s);
const hoyISO = () => new Date().toISOString().slice(0, 10);
const campo = (id, etiqueta, valor = "", extra = "") =>
  `<div class="campo ${extra.includes("ancho") ? "ancho" : ""}"><input id="${id}" placeholder=" " value="${esc(valor)}" ${extra.replace("ancho", "")}><label for="${id}">${etiqueta}</label></div>`;
const selectRol = (id, actual = "funcionario") =>
  `<div class="campo"><select id="${id}">${Object.entries(ROLES).map(([k, n]) => `<option value="${k}" ${k === actual ? "selected" : ""}>${esc(n)}</option>`).join("")}</select><label for="${id}">Perfil</label></div>`;
const vacio = (texto) => `<div class="vacio-tabla">${esc(texto)}</div>`;

function formatoRut(v) {
  const l = v.replace(/[^0-9kK]/g, "").toUpperCase();
  if (l.length < 2) return l;
  return l.slice(0, -1).replace(/^0+/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "-" + l.slice(-1);
}

// Muestra una contraseña temporal una sola vez, con botón para copiar.
function mostrarClave({ nombre, rut, clave_temporal }) {
  return dialogo({
    titulo: "Contraseña temporal",
    cerrable: false,
    html: `<p style="margin:0;color:var(--texto-2)">Para <b>${esc(nombre || "")}</b> ${rut ? "(" + esc(rut) + ")" : ""}</p>
      <div class="clave-temporal"><code id="ct">${esc(clave_temporal)}</code><button class="btn btn-borde" id="copiar">Copiar</button></div>
      <div class="aviso-suave">${icono("escudo")}<span>Entrégala en persona o por llamada verificada. No la envíes por chat ni correo. Se pedirá cambiarla al ingresar y no se volverá a mostrar.</span></div>`,
    acciones: [{ texto: "Listo" }],
  }).finally(() => {});
}
document.addEventListener("click", (e) => {
  if (e.target.id === "copiar") {
    navigator.clipboard?.writeText($("#ct").textContent).then(() => { e.target.textContent = "Copiada"; });
  }
});

(async function () {
  pintarIconos();
  try { YO = await exigirSesion(); } catch (_) { return; }
  if (!YO.puede_administrar) { location.replace("/"); return; }
  document.title = `Administración · ${CONFIG.producto}`;
  pintarAvatar($("#avatar"), YO.nombre);

  const resumen = await api("/api/admin/resumen");
  ROLES = resumen.roles; MI_ROL = resumen.rol;
  document.querySelectorAll("[data-rol]").forEach((el) => { if (el.dataset.rol !== MI_ROL) el.remove(); });
  pintarContadores(resumen);

  // ---------- navegación
  const secciones = [...document.querySelectorAll(".contenido section")];
  const cargadores = { resumen: cargarResumen, usuarios: cargarUsuarios, solicitudes: cargarSolicitudes, claves: cargarClaves,
                       derechos: cargarDerechos, modulos: cargarModulos, bitacora: cargarBitacora };
  function mostrar() {
    const disponibles = [...document.querySelectorAll(".menu a")].map((a) => a.dataset.sec);
    let s = (location.hash || "#resumen").slice(1);
    if (!disponibles.includes(s)) s = "resumen";
    secciones.forEach((x) => x.classList.toggle("activa", x.dataset.sec === s));
    document.querySelectorAll(".menu a").forEach((a) => a.classList.toggle("activo", a.dataset.sec === s));
    scrollTo(0, 0);
    cargadores[s]();
  }
  addEventListener("hashchange", mostrar);
  mostrar();

  async function refrescarContadores() { pintarContadores(await api("/api/admin/resumen")); }
  function pintarContadores(r) {
    document.querySelectorAll("[data-cont]").forEach((b) => { const n = r[b.dataset.cont]; b.textContent = n ? n : ""; });
  }

  // ---------- resumen
  async function cargarResumen() {
    const r = await api("/api/admin/resumen");
    pintarContadores(r);
    const m = [
      ["Cuentas activas", r.usuarios_activos], ["Personas conectadas", r.sesiones_abiertas],
      ["Módulos", r.modulos], ["Accesos fallidos (24 h)", r.fallidos_24h, r.fallidos_24h >= 10],
    ];
    $("#metricas").innerHTML = m.map(([t, v, a]) => `<div class="metrica ${a ? "alerta" : ""}"><span>${t}</span><b>${v}</b></div>`).join("");
    const tareas = [
      MI_ROL === "admin" && r.solicitudes_cuenta && [`${r.solicitudes_cuenta} solicitud(es) de cuenta por revisar`, "#solicitudes", "documento"],
      MI_ROL === "admin" && r.solicitudes_clave && [`${r.solicitudes_clave} pedido(s) de contraseña`, "#claves", "candado"],
      r.derechos_pendientes && [`${r.derechos_pendientes} solicitud(es) de derechos abiertas${r.derechos_vencidos ? ` · ${r.derechos_vencidos} vencida(s)` : ""}`, "#derechos", "escudo"],
    ].filter(Boolean);
    $("#pendientes").innerHTML = `<div class="tarjeta lista"><h2>Tareas pendientes</h2>${tareas.length
      ? tareas.map(([t, h, i]) => `<a class="fila accion" href="${h}"><span data-icono="${i}"></span><span>${esc(t)}</span><span data-icono="flecha"></span></a>`).join("")
      : '<div class="vacio">No hay tareas pendientes.</div>'}</div>`;
    pintarIconos($("#pendientes"));
  }

  // ---------- usuarios
  let temporizador;
  $("#buscar-usuario")?.addEventListener("input", () => { clearTimeout(temporizador); temporizador = setTimeout(cargarUsuarios, 250); });
  $("#btn-nuevo-usuario")?.addEventListener("click", () => editarUsuario(null));

  async function cargarUsuarios() {
    if (MI_ROL !== "admin") return;
    const lista = await api(`/api/admin/usuarios?q=${encodeURIComponent($("#buscar-usuario").value)}`);
    const ahora = new Date();
    $("#tabla-usuarios").innerHTML = `<div class="tfila cab-tabla t-usuarios"><span>Persona</span><span>Unidad y cargo</span><span>Perfil</span><span>Estado</span><span></span></div>` +
      (lista.length ? lista.map((u) => {
        const bloqueada = u.bloqueado_hasta && new Date(u.bloqueado_hasta) > ahora;
        const chips = [
          u.activo ? '<span class="chip ok">Activa</span>' : '<span class="chip alerta">Desactivada</span>',
          bloqueada && '<span class="chip alerta">Bloqueada</span>',
          u.debe_cambiar_clave && '<span class="chip acento">Clave temporal</span>',
          u.en_linea && '<span class="chip info">En línea</span>',
        ].filter(Boolean).join("");
        return `<div class="tfila t-usuarios"><span>${esc(u.nombre)}<small>${esc(u.rut)}${u.correo ? " · " + esc(u.correo) : ""}</small></span>
          <span>${esc(u.unidad || "—")}<small>${esc(u.cargo || "")}</small></span>
          <span>${esc(ROLES[u.rol] || u.rol)}</span><span class="chips">${chips}</span>
          <span class="acciones-fila"><button class="btn btn-borde" data-u="${u.id}">Gestionar</button></span></div>`;
      }).join("") : vacio("No hay cuentas que coincidan."));
    $("#tabla-usuarios").querySelectorAll("[data-u]").forEach((b) => b.onclick = () => editarUsuario(lista.find((u) => u.id === +b.dataset.u)));
  }

  function editarUsuario(u) {
    const nuevo = !u;
    const esYo = u && u.id === YO.id;
    const bloqueada = u && u.bloqueado_hasta && new Date(u.bloqueado_hasta) > new Date();
    dialogo({
      titulo: nuevo ? "Crear cuenta" : u.nombre,
      clase: "amplio",
      html: `${nuevo ? "" : `<p class="subtitulo">${esc(u.rut)} · creada ${esc(fechaLocal(u.creado_en, false))}</p>`}
        <div class="dlg-grid">
          ${nuevo ? campo("eu-rut", "RUT", "", 'maxlength="12" data-rut') : ""}
          ${campo("eu-nombre", "Nombre y apellido", u?.nombre, 'maxlength="120"')}
          ${campo("eu-correo", "Correo institucional", u?.correo || "", 'type="email" maxlength="120"')}
          ${campo("eu-cargo", "Cargo", u?.cargo || "", 'maxlength="80"')}
          ${campo("eu-unidad", "Unidad o servicio", u?.unidad || "", 'maxlength="80"')}
          ${selectRol("eu-rol", u?.rol)}
        </div>
        ${nuevo ? "" : `<div class="dlg-acciones-extra">
          <button class="btn btn-borde" data-accion="restablecer">Restablecer contraseña</button>
          ${bloqueada ? '<button class="btn btn-borde" data-accion="desbloquear">Desbloquear</button>' : ""}
          ${u.en_linea && !esYo ? '<button class="btn btn-borde" data-accion="cerrar">Cerrar sus sesiones</button>' : ""}
          ${esYo ? "" : `<button class="btn btn-borde" data-accion="activo">${u.activo ? "Desactivar cuenta" : "Reactivar cuenta"}</button>`}
        </div>`}
        <div class="zona-error"></div>`,
      acciones: [
        { texto: "Cancelar", clase: "btn btn-texto", valor: null },
        { texto: nuevo ? "Crear y generar contraseña" : "Guardar cambios", alHacer: async (v) => {
            const val = (id) => v.querySelector(id)?.value.trim();
            const datos = { nombre: val("#eu-nombre"), correo: val("#eu-correo"), cargo: val("#eu-cargo"), unidad: val("#eu-unidad"), rol: val("#eu-rol") };
            try {
              if (nuevo) {
                const r = await api("/api/admin/usuarios", { metodo: "POST", datos: { ...datos, rut: val("#eu-rut") } });
                setTimeout(() => mostrarClave(r), 50);
              } else {
                await api(`/api/admin/usuarios/${u.id}`, { metodo: "PATCH", datos });
                toast("Cambios guardados.");
              }
              cargarUsuarios(); return true;
            } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
          } },
      ],
    });
    const velo = [...document.querySelectorAll(".velo")].pop();
    velo.querySelectorAll("[data-rut]").forEach((i) => i.addEventListener("input", () => { i.value = formatoRut(i.value); }));
    velo.querySelectorAll("[data-accion]").forEach((b) => b.onclick = async () => {
      const zona = velo.querySelector(".zona-error");
      try {
        if (b.dataset.accion === "restablecer") {
          if (!confirm(`¿Restablecer la contraseña de ${u.nombre}? Se cerrarán sus sesiones abiertas.`)) return;
          const r = await api(`/api/admin/usuarios/${u.id}/restablecer`, { metodo: "POST" });
          velo.remove(); mostrarClave({ ...u, ...r });
        } else if (b.dataset.accion === "desbloquear") {
          await api(`/api/admin/usuarios/${u.id}/desbloquear`, { metodo: "POST" }); velo.remove(); toast("Cuenta desbloqueada.");
        } else if (b.dataset.accion === "cerrar") {
          const r = await api(`/api/admin/usuarios/${u.id}/cerrar-sesiones`, { metodo: "POST" }); velo.remove(); toast(`${r.cerradas} sesión(es) cerrada(s).`);
        } else if (b.dataset.accion === "activo") {
          if (u.activo && !confirm(`¿Desactivar la cuenta de ${u.nombre}? No podrá ingresar hasta que la reactives.`)) return;
          await api(`/api/admin/usuarios/${u.id}`, { metodo: "PATCH", datos: { activo: !u.activo } });
          velo.remove(); toast(u.activo ? "Cuenta desactivada." : "Cuenta reactivada.");
        }
        cargarUsuarios();
      } catch (e) { mostrarErrorEn(zona, e.message); }
    });
  }

  // ---------- solicitudes de cuenta
  let estadoSolicitudes = "pendiente";
  document.querySelectorAll("#filtro-solicitudes button").forEach((b) => b.onclick = () => {
    estadoSolicitudes = b.dataset.estado;
    document.querySelectorAll("#filtro-solicitudes button").forEach((x) => x.classList.toggle("activo", x === b));
    cargarSolicitudes();
  });
  async function cargarSolicitudes() {
    if (MI_ROL !== "admin") return;
    const lista = await api(`/api/admin/solicitudes-cuenta?estado=${estadoSolicitudes}`);
    $("#tabla-solicitudes").innerHTML = `<div class="tfila cab-tabla t-solicitudes"><span>Persona</span><span>Unidad y cargo</span><span>Motivo</span><span></span></div>` +
      (lista.length ? lista.map((s) => `<div class="tfila t-solicitudes">
          <span>${esc(s.nombre)}<small>${esc(s.rut)}${s.correo ? " · " + esc(s.correo) : ""}</small></span>
          <span>${esc(s.unidad || "—")}<small>${esc(s.cargo || "")}</small></span>
          <span>${esc(s.motivo || "—")}<small>Enviada ${esc(fechaLocal(s.creada))}${s.resuelta_en ? ` · ${s.estado} por ${esc(s.resuelta_por_nombre || "—")}` : ""}${s.nota ? " · " + esc(s.nota) : ""}</small></span>
          <span class="acciones-fila">${s.estado === "pendiente" ? `<button class="btn btn-texto" data-rechazar="${s.id}">Rechazar</button><button class="btn" data-aprobar="${s.id}">Aprobar</button>` : `<span class="chip ${s.estado === "aprobada" ? "ok" : "alerta"}">${s.estado === "aprobada" ? "Aprobada" : "Rechazada"}</span>`}</span>
        </div>`).join("") : vacio(estadoSolicitudes === "pendiente" ? "No hay solicitudes pendientes." : "Sin registros."));
    $("#tabla-solicitudes").querySelectorAll("[data-aprobar]").forEach((b) => b.onclick = () => {
      const s = lista.find((x) => x.id === +b.dataset.aprobar);
      dialogo({
        titulo: "Aprobar solicitud",
        html: `<p class="subtitulo">${esc(s.nombre)} · ${esc(s.rut)}</p>${selectRol("ap-rol")}<div class="zona-error"></div>`,
        acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Crear cuenta", alHacer: async (v) => {
          try { const r = await api(`/api/admin/solicitudes-cuenta/${s.id}/aprobar`, { metodo: "POST", datos: { rol: v.querySelector("#ap-rol").value } });
                setTimeout(() => mostrarClave(r), 50); cargarSolicitudes(); refrescarContadores(); return true; }
          catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; } } }],
      });
    });
    $("#tabla-solicitudes").querySelectorAll("[data-rechazar]").forEach((b) => b.onclick = () => dialogo({
      titulo: "Rechazar solicitud",
      html: `<div class="campo"><textarea id="rz-nota" placeholder=" " maxlength="500"></textarea><label for="rz-nota">Motivo (queda en el registro)</label></div><div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Rechazar", alHacer: async (v) => {
        try { await api(`/api/admin/solicitudes-cuenta/${b.dataset.rechazar}/rechazar`, { metodo: "POST", datos: { nota: v.querySelector("#rz-nota").value } });
              toast("Solicitud rechazada."); cargarSolicitudes(); refrescarContadores(); return true; }
        catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; } } }],
    }));
  }

  // ---------- pedidos de contraseña
  async function cargarClaves() {
    if (MI_ROL !== "admin") return;
    const lista = await api("/api/admin/solicitudes-clave");
    $("#tabla-claves").innerHTML = `<div class="tfila cab-tabla t-claves"><span>Persona</span><span>Unidad y cargo</span><span>Pedido</span><span></span></div>` +
      (lista.length ? lista.map((s) => `<div class="tfila t-claves">
          <span>${esc(s.nombre)}<small>${esc(s.rut)}</small></span>
          <span>${esc(s.unidad || "—")}<small>${esc(s.cargo || "")}</small></span>
          <span>${esc(fechaLocal(s.creada))}<small>desde ${esc(s.ip || "?")}</small></span>
          <span class="acciones-fila"><button class="btn btn-texto" data-descartar="${s.id}">Descartar</button><button class="btn" data-restablecer="${s.usuario_id}">Identidad verificada · Restablecer</button></span>
        </div>`).join("") : vacio("No hay pedidos de contraseña."));
    $("#tabla-claves").querySelectorAll("[data-restablecer]").forEach((b) => b.onclick = async () => {
      const s = lista.find((x) => x.usuario_id === +b.dataset.restablecer);
      const r = await api(`/api/admin/usuarios/${s.usuario_id}/restablecer`, { metodo: "POST" });
      mostrarClave({ ...s, ...r }); cargarClaves(); refrescarContadores();
    });
    $("#tabla-claves").querySelectorAll("[data-descartar]").forEach((b) => b.onclick = async () => {
      await api(`/api/admin/solicitudes-clave/${b.dataset.descartar}/descartar`, { metodo: "POST" }); cargarClaves(); refrescarContadores();
    });
  }

  // ---------- derechos
  let estadoDerechos = "abiertas";
  document.querySelectorAll("#filtro-derechos button").forEach((b) => b.onclick = () => {
    estadoDerechos = b.dataset.estado;
    document.querySelectorAll("#filtro-derechos button").forEach((x) => x.classList.toggle("activo", x === b));
    cargarDerechos();
  });
  async function cargarDerechos() {
    const lista = await api(`/api/admin/derechos?estado=${estadoDerechos}`);
    const hoy = hoyISO();
    $("#tabla-derechos").innerHTML = `<div class="tfila cab-tabla t-derechos"><span>Titular</span><span>Solicitud</span><span>Plazo</span><span></span></div>` +
      (lista.length ? lista.map((s) => {
        const abierta = ["recibida", "en_revision"].includes(s.estado);
        const vencida = abierta && s.vence < hoy;
        return `<div class="tfila t-derechos">
          <span>${esc(s.nombre)}<small>${esc(s.rut)}</small></span>
          <span>#${s.id} · ${esc(s.tipo_nombre)}<small>${esc(s.detalle || "Sin detalle")}${s.respuesta ? "<br>Respuesta: " + esc(s.respuesta) : ""}</small></span>
          <span>${esc(fechaLocal(s.vence, false))}<small><span class="chip ${vencida ? "alerta" : abierta ? "acento" : "ok"}">${vencida ? "Vencida" : esc(ESTADOS_DERECHO[s.estado])}</span></small></span>
          <span class="acciones-fila">${abierta ? `<button class="btn btn-borde" data-d="${s.id}">Responder</button>` : ""}</span></div>`;
      }).join("") : vacio("No hay solicitudes abiertas."));
    $("#tabla-derechos").querySelectorAll("[data-d]").forEach((b) => b.onclick = () => {
      const s = lista.find((x) => x.id === +b.dataset.d);
      dialogo({
        titulo: `Solicitud #${s.id} · ${s.tipo_nombre}`,
        clase: "amplio",
        html: `<p class="subtitulo">${esc(s.nombre)} · ${esc(s.rut)} · vence ${esc(fechaLocal(s.vence, false))}</p>
          <div class="aviso-suave" style="margin-bottom:18px">${icono("documento")}<span>${esc(s.detalle || "Sin detalle")}</span></div>
          <div class="campo"><select id="rd-estado"><option value="en_revision">En revisión</option><option value="respondida" selected>Respondida</option><option value="rechazada">Rechazada (fundada)</option></select><label for="rd-estado">Estado</label></div>
          <div class="campo"><textarea id="rd-resp" placeholder=" " maxlength="3000" style="height:140px">${esc(s.respuesta || "")}</textarea><label for="rd-resp">Respuesta para la persona</label>
            <div class="ayuda">La persona la verá en Mi cuenta › Datos y privacidad.</div></div>
          <div class="zona-error"></div>`,
        acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar", alHacer: async (v) => {
          try { await api(`/api/admin/derechos/${s.id}`, { metodo: "POST", datos: { estado: v.querySelector("#rd-estado").value, respuesta: v.querySelector("#rd-resp").value } });
                toast("Solicitud actualizada."); cargarDerechos(); refrescarContadores(); return true; }
          catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; } } }],
      });
    });
  }

  // ---------- módulos
  $("#btn-nuevo-modulo")?.addEventListener("click", () => editarModulo(null));
  async function cargarModulos() {
    const lista = await api("/api/admin/modulos");
    $("#tabla-modulos").innerHTML = `<div class="tfila cab-tabla t-modulos"><span></span><span>Módulo</span><span>Ficha de tratamiento</span><span>Estado</span><span></span></div>` +
      (lista.length ? lista.map((m) => {
        const visible = m.activo && (!m.datos_sensibles || m.eipd_aprobada) && m.roles.length;
        return `<div class="tfila t-modulos">
          <span class="mod-icono" style="background:${esc(m.color)}">${icono(m.icono) || esc(m.nombre[0])}</span>
          <span>${esc(m.nombre)}<small>${esc(m.url)} · ${m.roles.map((r) => esc(ROLES[r] || r)).join(", ") || "sin perfiles"}</small></span>
          <span>${esc(m.finalidad)}<small>${esc(m.categorias_datos)}</small></span>
          <span class="chips">${visible ? '<span class="chip ok">Visible</span>' : '<span class="chip">Oculto</span>'}${m.datos_sensibles ? `<span class="chip ${m.eipd_aprobada ? "info" : "alerta"}">${m.eipd_aprobada ? "EIPD aprobada" : "EIPD pendiente"}</span>` : ""}</span>
          <span class="acciones-fila"><button class="btn btn-borde" data-m="${m.id}">Editar</button></span></div>`;
      }).join("") : vacio("Aún no hay módulos. Agrega el primero para que aparezca en el menú de puntos."));
    $("#tabla-modulos").querySelectorAll("[data-m]").forEach((b) => b.onclick = () => editarModulo(lista.find((m) => m.id === +b.dataset.m)));
  }

  function editarModulo(m) {
    const soloDpd = MI_ROL === "dpd";
    dialogo({
      titulo: m ? `Editar ${m.nombre}` : "Agregar módulo",
      clase: "amplio",
      html: `<div class="dlg-grid">
          ${campo("em-nombre", "Nombre", m?.nombre || "", 'maxlength="60"')}
          ${campo("em-clave", "Clave (sin espacios)", m?.clave || "", 'maxlength="40" pattern="[a-z0-9-]+"')}
          ${campo("em-url", "Dirección (URL)", m?.url || "", 'maxlength="300" ancho')}
          ${campo("em-desc", "Descripción corta", m?.descripcion || "", 'maxlength="200" ancho')}
          <div class="campo"><select id="em-icono">${ICONOS_MODULO.map((i) => `<option ${m?.icono === i ? "selected" : ""}>${i}</option>`).join("")}</select><label for="em-icono">Ícono</label></div>
          <div class="campo"><input id="em-color" type="color" value="${esc(m?.color || "#1565c0")}" style="padding-top:22px"><label for="em-color">Color</label></div>
        </div>
        <p class="subtitulo">¿Quiénes lo ven en el menú?</p>
        <div class="check-lista">${Object.entries(ROLES).map(([k, n]) => `<label class="check"><input type="checkbox" value="${k}" class="em-rol" ${m?.roles.includes(k) ? "checked" : ""}> ${esc(n)}</label>`).join("")}</div>
        <p class="subtitulo">Ficha de tratamiento (Ley 21.719)</p>
        <div class="campo"><textarea id="em-fin" placeholder=" " maxlength="500">${esc(m?.finalidad || "")}</textarea><label for="em-fin">Finalidad: para qué usa datos personales</label></div>
        <div class="campo"><input id="em-cat" placeholder=" " maxlength="500" value="${esc(m?.categorias_datos || "")}"><label for="em-cat">Categorías de datos (ej.: identificación del paciente, signos vitales)</label></div>
        ${campo("em-resp", "Unidad responsable", m?.responsable || "", 'maxlength="120"')}
        <div class="check-lista">
          <label class="check"><input type="checkbox" id="em-sens" ${m?.datos_sensibles ? "checked" : ""}> Trata datos de salud u otros sensibles</label>
          <label class="check"><input type="checkbox" id="em-eipd" ${m?.eipd_aprobada ? "checked" : ""}> Evaluación de impacto aprobada por el DPD</label>
          <label class="check"><input type="checkbox" id="em-activo" ${m ? (m.activo ? "checked" : "") : "checked"}> Activo</label>
        </div>
        <div class="zona-error"></div>`,
      acciones: [{ texto: "Cancelar", clase: "btn btn-texto", valor: null }, { texto: "Guardar módulo", alHacer: async (v) => {
        const val = (id) => v.querySelector(id).value.trim();
        const datos = {
          nombre: val("#em-nombre"), clave: val("#em-clave"), url: val("#em-url"), descripcion: val("#em-desc"),
          icono: val("#em-icono"), color: val("#em-color"), finalidad: val("#em-fin"), categorias_datos: val("#em-cat"),
          responsable: val("#em-resp"), datos_sensibles: v.querySelector("#em-sens").checked,
          eipd_aprobada: v.querySelector("#em-eipd").checked, activo: v.querySelector("#em-activo").checked,
          orden: m?.orden ?? 100, roles: [...v.querySelectorAll(".em-rol:checked")].map((c) => c.value),
        };
        try {
          await api(m ? `/api/admin/modulos/${m.id}` : "/api/admin/modulos", { metodo: m ? "PUT" : "POST", datos });
          toast("Módulo guardado."); cargarModulos(); return true;
        } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
      } }],
    });
    if (soloDpd) [...document.querySelectorAll(".velo")].pop().querySelectorAll(".dlg-grid input, .dlg-grid select").forEach((i) => { i.disabled = true; });
  }

  // ---------- bitácora
  let tBit;
  $("#buscar-bitacora").addEventListener("input", () => { clearTimeout(tBit); tBit = setTimeout(cargarBitacora, 300); });
  $("#btn-integridad").onclick = async () => {
    const r = await api("/api/admin/auditoria/integridad");
    dialogo({
      titulo: r.integra ? "Bitácora íntegra" : "Bitácora alterada",
      html: r.integra
        ? `<div class="aviso-suave">${icono("escudo")}<span>Se verificaron ${r.registros} registros encadenados. Ninguno fue modificado ni borrado.</span></div>
           <p style="font-size:12px;color:var(--texto-3);margin:14px 0 0;overflow-wrap:anywhere">Último sello: <code>${esc(r.ultimo_hash)}</code><br>Guarda este sello fuera del servidor para poder comprobar más adelante que nada cambió.</p>`
        : `<div class="aviso-suave">${icono("alerta")}<span>La cadena se rompe en el registro #${r.falla_en_id}. Alguien modificó o borró registros. Informa al DPD y a seguridad de la información.</span></div>`,
      acciones: [{ texto: "Cerrar" }],
    });
  };
  async function cargarBitacora() {
    const lista = await api(`/api/admin/auditoria?q=${encodeURIComponent($("#buscar-bitacora").value)}&limite=300`);
    const alerta = new Set(["login_fallido", "login_rechazado_bloqueo", "desbloqueo_fallido"]);
    $("#tabla-bitacora").innerHTML = `<div class="tfila cab-tabla t-bitacora"><span>Fecha</span><span>Evento</span><span>Persona</span><span>Detalle</span><span>IP</span></div>` +
      (lista.length ? lista.map((a) => `<div class="tfila t-bitacora">
          <span>${esc(fechaLocal(a.ts))}</span>
          <span>${alerta.has(a.accion) ? '<span class="chip alerta">' + esc(a.etiqueta) + "</span>" : esc(a.etiqueta)}</span>
          <span>${esc(a.nombre || "—")}<small>${esc(a.rut || "")}</small></span>
          <span><small>${esc(a.detalle || "")}</small></span><span><small>${esc(a.ip || "")}</small></span></div>`).join("") : vacio("Sin registros."));
  }
})();
