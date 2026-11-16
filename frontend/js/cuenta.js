"use strict";

const TIPOS = {
  rectificacion: ["Rectificación", "Corregir un dato inexacto o incompleto"],
  acceso: ["Acceso", "Saber qué datos tuyos se tratan, para qué y con quién se comparten"],
  supresion: ["Supresión", "Eliminar datos que ya no son necesarios"],
  oposicion: ["Oposición", "Oponerte a un uso específico de tus datos"],
  portabilidad: ["Portabilidad", "Recibir tus datos en un formato estructurado"],
  bloqueo: ["Bloqueo temporal", "Suspender el tratamiento mientras se resuelve otra solicitud"],
};
const ESTADOS = { recibida: "Recibida", en_revision: "En revisión", respondida: "Respondida", rechazada: "Rechazada" };

(async function () {
  pintarIconos();
  let yo;
  try { yo = await exigirSesion(); } catch (_) { return; }
  document.title = `Mi cuenta · ${CONFIG.producto}`;

  pintarAvatar(document.getElementById("avatar"), yo.nombre);
  pintarAvatar(document.getElementById("avatar-hero"), yo.nombre);
  document.getElementById("hola").textContent = `Hola, ${yo.nombre}`;
  const pon = (id, v) => { document.getElementById(id).textContent = v || "—"; };
  pon("d-rut", yo.rut); pon("d-nombre", yo.nombre); pon("d-correo", yo.correo);
  pon("d-cargo", yo.cargo); pon("d-unidad", yo.unidad); pon("d-rol", yo.rol === "admin" ? "Administrador" : "Funcionario");
  pon("txt-inactividad", `La sesión se cierra tras ${yo.inactividad_min} minutos sin actividad`);
  pon("txt-aviso", `Versión ${CONFIG.version_aviso} · Cómo tratamos tus datos`);

  // ---------- navegación por secciones
  const secciones = [...document.querySelectorAll(".contenido section")];
  const enlaces = [...document.querySelectorAll(".menu a")];
  const cargadas = new Set();
  function mostrar() {
    const s = (location.hash || "#inicio").slice(1);
    const sec = secciones.find((x) => x.dataset.sec === s) ? s : "inicio";
    secciones.forEach((x) => x.classList.toggle("activa", x.dataset.sec === sec));
    enlaces.forEach((a) => a.classList.toggle("activo", a.dataset.sec === sec));
    scrollTo(0, 0);
    if (!cargadas.has(sec)) { cargadas.add(sec); ({ seguridad: cargarSeguridad, privacidad: cargarSolicitudes }[sec] || (() => {}))(); }
  }
  addEventListener("hashchange", mostrar);
  mostrar();

  // ---------- seguridad
  document.getElementById("btn-clave").onclick = () => dialogoCambioClave().then((ok) => ok && cargarSeguridad());

  async function cargarSeguridad() {
    const [ses, act] = await Promise.all([api("/api/cuenta/sesiones"), api("/api/cuenta/actividad")]);
    const cont = document.getElementById("sesiones");
    cont.innerHTML = ses.map((s) => `
      <div class="fila"><span data-icono="dispositivo"></span>
        <span>${esc(navegadorLegible(s.navegador))} · ${esc(s.ip)}<small>Iniciada ${esc(fechaLocal(s.creada))} · última actividad ${esc(fechaLocal(s.ultima_actividad))}</small></span>
        ${s.actual ? '<span class="etiqueta">Este equipo</span>' : `<button class="btn btn-borde" data-cerrar="${s.id}">Cerrar</button>`}
      </div>`).join("");
    pintarIconos(cont);
    cont.querySelectorAll("[data-cerrar]").forEach((b) => b.onclick = async () => {
      await api(`/api/cuenta/sesiones/${b.dataset.cerrar}`, { metodo: "DELETE" });
      toast("Sesión cerrada."); cargarSeguridad();
    });

    const alerta = new Set(["login_fallido", "login_rechazado_bloqueo", "desbloqueo_fallido"]);
    const ca = document.getElementById("actividad");
    ca.innerHTML = act.length ? act.map((a) => `
      <div class="fila"><span data-icono="${alerta.has(a.accion) ? "alerta" : "historial"}"></span>
        <span>${esc(a.etiqueta)}<small>${esc(fechaLocal(a.ts))}${a.ip ? " · " + esc(a.ip) : ""}</small></span>
        ${alerta.has(a.accion) ? '<span class="etiqueta alerta">Revisar</span>' : ""}
      </div>`).join("") : '<div class="vacio">Sin actividad registrada.</div>';
    pintarIconos(ca);
  }

  // ---------- datos y privacidad
  document.getElementById("btn-exportar").addEventListener("click", () => toast("Preparando tu archivo…", 2500));
  document.getElementById("ir-rectificar").addEventListener("click", () => setTimeout(() => nuevaSolicitud("rectificacion"), 50));
  document.getElementById("btn-solicitud").onclick = () => nuevaSolicitud();

  function nuevaSolicitud(tipo = "rectificacion") {
    return dialogo({
      titulo: "Ejercer un derecho",
      html: `<div class="campo"><select id="sol-tipo">${Object.entries(TIPOS).map(([k, [n, d]]) =>
               `<option value="${k}" ${k === tipo ? "selected" : ""}>${esc(n)} — ${esc(d)}</option>`).join("")}</select><label for="sol-tipo">Tipo de solicitud</label></div>
             <div class="campo"><textarea id="sol-detalle" placeholder=" " maxlength="2000"></textarea><label for="sol-detalle">Cuéntanos qué necesitas</label>
               <div class="ayuda">Ej.: "Mi cargo aparece como TENS y soy enfermera". No incluyas datos de pacientes.</div></div>
             <div class="zona-error"></div>`,
      acciones: [
        { texto: "Cancelar", clase: "btn btn-texto", valor: false },
        { texto: "Enviar solicitud", alHacer: async (v) => {
            try {
              const r = await api("/api/cuenta/solicitudes", { metodo: "POST", datos: { tipo: v.querySelector("#sol-tipo").value, detalle: v.querySelector("#sol-detalle").value } });
              toast(`Solicitud #${r.id} enviada. Plazo de respuesta: ${fechaLocal(r.vence, false)}.`, 6000);
              cargarSolicitudes(); return true;
            } catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
          } },
      ],
    });
  }

  async function cargarSolicitudes() {
    const lista = await api("/api/cuenta/solicitudes");
    const c = document.getElementById("solicitudes");
    c.innerHTML = lista.map((s) => `
      <div class="fila"><span data-icono="documento"></span>
        <span>#${s.id} · ${esc(s.tipo_nombre)}<small>Enviada ${esc(fechaLocal(s.creada))} · responder antes del ${esc(fechaLocal(s.vence, false))}${s.respuesta ? "<br>Respuesta: " + esc(s.respuesta) : ""}</small></span>
        <span class="etiqueta">${esc(ESTADOS[s.estado] || s.estado)}</span>
      </div>`).join("");
    pintarIconos(c);
  }
})();
