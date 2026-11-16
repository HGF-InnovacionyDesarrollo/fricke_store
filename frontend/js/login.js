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

  document.getElementById("olvide").onclick = () => dialogo({
    titulo: "¿Olvidaste tu contraseña?",
    html: `<p style="margin:0;color:var(--texto-2)">Por seguridad, las contraseñas se restablecen en forma presencial o por llamada verificada.<br><br>
      Comunícate con <b>${esc(CONFIG.mesa_ayuda)}</b>. Te entregarán una contraseña temporal que deberás cambiar al ingresar.</p>`,
    acciones: [{ texto: "Entendido" }],
  });

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
