"use strict";

// Validación local del RUT (módulo 11) y formato mientras se escribe.
function dvRut(cuerpo) {
  let s = 0, f = 2;
  for (let i = cuerpo.length - 1; i >= 0; i--) { s += +cuerpo[i] * f; f = f === 7 ? 2 : f + 1; }
  const r = 11 - (s % 11);
  return r === 11 ? "0" : r === 10 ? "K" : String(r);
}
function limpiarRut(v) { return v.replace(/[^0-9kK]/g, "").toUpperCase(); }
function formatearRut(v) {
  const l = limpiarRut(v);
  if (l.length < 2) return l;
  const cuerpo = l.slice(0, -1).replace(/^0+/, ""), dv = l.slice(-1);
  return cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "-" + dv;
}
function rutValido(v) {
  const l = limpiarRut(v);
  if (l.length < 8) return false;
  const cuerpo = l.slice(0, -1);
  return /^\d+$/.test(cuerpo) && dvRut(cuerpo) === l.slice(-1);
}

(async function () {
  pintarIconos();
  await cargarConfig();
  document.title = `Iniciar sesión · ${CONFIG.producto}`;
  if (new URLSearchParams(location.search).has("expirada")) document.getElementById("aviso-expirada").classList.remove("oculto");

  const rut = document.getElementById("rut"), clave = document.getElementById("clave");
  const campoRut = document.getElementById("campo-rut"), zona = document.getElementById("error-login");

  rut.addEventListener("input", () => {
    const fin = rut.selectionStart === rut.value.length;
    rut.value = formatearRut(rut.value);
    if (fin) rut.setSelectionRange(rut.value.length, rut.value.length);
    campoRut.classList.remove("error"); mostrarErrorEn(zona, "");
  });
  rut.addEventListener("blur", () => { if (rut.value && !rutValido(rut.value)) { campoRut.classList.add("error"); mostrarErrorEn(zona, "Revisa el RUT: el dígito verificador no coincide."); } });
  document.getElementById("ver-clave").onchange = (e) => { clave.type = e.target.checked ? "text" : "password"; };

  // Formatea el RUT en cualquier campo marcado con data-rut dentro de un diálogo.
  function activarRut(raiz) {
    raiz.querySelectorAll("[data-rut]").forEach((i) => i.addEventListener("input", () => { i.value = formatearRut(i.value); }));
  }
  function confirmacion(titulo, mensaje) {
    return dialogo({ titulo, html: `<div class="aviso-suave">${icono("escudo")}<span>${esc(mensaje)}</span></div>`, acciones: [{ texto: "Entendido" }] });
  }

  document.getElementById("olvide").onclick = () => {
    dialogo({
      titulo: "Recuperar tu contraseña",
      html: `<p class="dlg-texto">Por seguridad, las contraseñas no se envían por correo: la Mesa de ayuda te entregará una temporal después de verificar tu identidad.</p>
        <div class="campo"><input id="rc-rut" data-rut placeholder=" " maxlength="12" value="${esc(rut.value)}"><label for="rc-rut">Tu RUT</label></div>
        <div class="zona-error"></div>
        <p class="dlg-texto" style="font-size:13px;margin:0">¿Urgente? Llama a <b>${esc(CONFIG.mesa_ayuda)}</b>.</p>`,
      acciones: [
        { texto: "Cancelar", clase: "btn btn-texto", valor: null },
        { texto: "Enviar pedido", alHacer: async (v) => {
            const r = v.querySelector("#rc-rut").value;
            if (!rutValido(r)) { mostrarErrorEn(v.querySelector(".zona-error"), "Ingresa un RUT válido."); return false; }
            try { const res = await api("/api/publico/recuperar-clave", { metodo: "POST", datos: { rut: r } }); return res.mensaje; }
            catch (e) { mostrarErrorEn(v.querySelector(".zona-error"), e.message); return false; }
          } },
      ],
    }).then((msg) => msg && confirmacion("Pedido enviado", msg));
    activarRut(document.querySelector(".velo"));
  };

  document.getElementById("crear-cuenta").onclick = () => {
    dialogo({
      titulo: "Solicitar una cuenta",
      html: `<p class="dlg-texto">Para funcionarios y funcionarias de ${esc(CONFIG.institucion)}. Un administrador revisará tu solicitud y te entregará tu contraseña temporal en forma presencial.</p>
        <div class="dlg-grid">
          <div class="campo"><input id="sc-rut" data-rut placeholder=" " maxlength="12" value="${esc(rut.value)}"><label for="sc-rut">RUT</label></div>
          <div class="campo"><input id="sc-nombre" placeholder=" " maxlength="120" autocomplete="name"><label for="sc-nombre">Nombre y apellido</label></div>
          <div class="campo ancho"><input id="sc-correo" type="email" placeholder=" " maxlength="120" autocomplete="email"><label for="sc-correo">Correo institucional</label></div>
          <div class="campo"><input id="sc-cargo" placeholder=" " maxlength="80"><label for="sc-cargo">Cargo</label></div>
          <div class="campo"><input id="sc-unidad" placeholder=" " maxlength="80"><label for="sc-unidad">Unidad o servicio</label></div>
          <div class="campo ancho"><textarea id="sc-motivo" placeholder=" " maxlength="500"></textarea><label for="sc-motivo">¿Para qué necesitas acceso? (opcional)</label></div>
        </div>
        <div class="zona-error"></div>
        <p style="font-size:12px;color:var(--texto-3);margin:4px 0 0">Usaremos estos datos solo para evaluar y crear tu cuenta. <a href="/privacidad" target="_blank" rel="noopener">Aviso de privacidad</a>.</p>`,
      acciones: [
        { texto: "Cancelar", clase: "btn btn-texto", valor: null },
        { texto: "Enviar solicitud", alHacer: async (v) => {
            const val = (id) => v.querySelector(id).value.trim();
            const zonaE = v.querySelector(".zona-error");
            if (!rutValido(val("#sc-rut"))) { mostrarErrorEn(zonaE, "Ingresa un RUT válido."); return false; }
            if (val("#sc-nombre").split(/\s+/).length < 2) { mostrarErrorEn(zonaE, "Escribe tu nombre y apellido."); return false; }
            if (!val("#sc-correo")) { mostrarErrorEn(zonaE, "Escribe tu correo institucional."); return false; }
            try {
              const res = await api("/api/publico/solicitar-cuenta", { metodo: "POST", datos: {
                rut: val("#sc-rut"), nombre: val("#sc-nombre"), correo: val("#sc-correo"),
                cargo: val("#sc-cargo"), unidad: val("#sc-unidad"), motivo: val("#sc-motivo") } });
              return res.mensaje;
            } catch (e) { mostrarErrorEn(zonaE, e.message); return false; }
          } },
      ],
    }).then((msg) => msg && confirmacion("Solicitud enviada", msg));
    activarRut(document.querySelector(".velo"));
  };

  document.getElementById("form-login").onsubmit = async (e) => {
    e.preventDefault();
    mostrarErrorEn(zona, "");
    if (!rutValido(rut.value)) { campoRut.classList.add("error"); mostrarErrorEn(zona, "Ingresa un RUT válido."); rut.focus(); return; }
    if (!clave.value) { mostrarErrorEn(zona, "Ingresa tu contraseña."); clave.focus(); return; }
    const btn = document.getElementById("btn-ingresar");
    btn.disabled = true;
    try {
      await api("/api/auth/login", { metodo: "POST", datos: { rut: rut.value, clave: clave.value } });
      location.replace("/");
    } catch (err) {
      mostrarErrorEn(zona, err.message);
      clave.value = ""; clave.focus();
    } finally { btn.disabled = false; }
  };
})();
