// Conexión por USB con un Monitor T/H desde el navegador (Web Serial, Chrome o Edge), con el mismo protocolo que el
// Configurador de Windows (Monitor_TH/configurador/protocolo.md, firmware 2.0 o posterior; WiFi desde 2.1).
// Cada comando es una línea que empieza con @; las líneas sin @ son mensajes de diagnóstico del monitor.
"use strict";

/** Texto apto para la pantalla del monitor: sin tildes ni | " ; \ (igual que texto_monitor del configurador). */
function textoMonitor(txt, largo) {
  return String(txt || "").normalize("NFKD").replace(/[^\x20-\x7e]/g, "").replace(/[|";\\]/g, " ")
    .split(/\s+/).filter(Boolean).join(" ").slice(0, largo);
}

class ErrorMonitor extends Error {}

class MonitorUSB {
  constructor(alDiagnostico = () => {}) {
    this.puerto = null;
    this.lector = null;
    this.pendiente = "";
    this.lineas = [];          // líneas @ recibidas que aún no se leen
    this.avisar = null;        // despierta a quien espera una línea
    this.alDiagnostico = alDiagnostico;
    this.alDesconectar = () => {};
    this.ocupado = Promise.resolve();
  }

  static disponible() { return typeof navigator !== "undefined" && "serial" in navigator && window.isSecureContext; }

  get abierto() { return !!this.puerto; }

  /** Pide al usuario el puerto (Chrome muestra la lista) o usa uno ya autorizado. */
  async abrir(puerto) {
    puerto = puerto || await navigator.serial.requestPort();
    await puerto.open({ baudRate: 115200, bufferSize: 8192 });
    // Sin esto el monitor se reiniciaría al abrir el puerto. Primero RTS y luego DTR, como el configurador.
    try { await puerto.setSignals({ requestToSend: false }); await puerto.setSignals({ dataTerminalReady: false }); } catch (_) { /* algunos adaptadores no lo permiten */ }
    this.puerto = puerto;
    this.idUSB = puerto.getInfo?.() || {};
    this.lineas = []; this.pendiente = "";
    this._leer();
    await new Promise((r) => setTimeout(r, 300));
    this.lineas = [];
  }

  async _leer() {
    const decodificador = new TextDecoder();
    while (this.puerto?.readable) {
      this.lector = this.puerto.readable.getReader();
      try {
        for (;;) {
          const { value, done } = await this.lector.read();
          if (done) break;
          this.pendiente += decodificador.decode(value, { stream: true });
          let i;
          while ((i = this.pendiente.indexOf("\n")) >= 0) {
            const linea = this.pendiente.slice(0, i).replace(/\r$/, "").trim();
            this.pendiente = this.pendiente.slice(i + 1);
            if (!linea) continue;
            if (linea.startsWith("@")) { this.lineas.push(linea); this.avisar?.(); }
            else this.alDiagnostico(linea);
          }
        }
      } catch (_) {
        break;   // se desconectó el cable o se reinició el monitor
      } finally {
        try { this.lector.releaseLock(); } catch (_) { /* nada */ }
        this.lector = null;
      }
      if (!this.cerrando) break;
    }
    if (!this.cerrando && this.puerto) { await this.cerrar(); if (!this.reiniciando) this.alDesconectar(); }
  }

  async cerrar() {
    this.cerrando = true;
    const p = this.puerto;
    this.puerto = null;
    try { await this.lector?.cancel(); } catch (_) { /* nada */ }
    try { await p?.close(); } catch (_) { /* nada */ }
    this.cerrando = false;
  }

  _siguiente(hasta) {
    if (this.lineas.length) return Promise.resolve(this.lineas.shift());
    return new Promise((resolver) => {
      const t = setTimeout(() => { this.avisar = null; resolver(null); }, Math.max(0, hasta - Date.now()));
      this.avisar = () => { clearTimeout(t); this.avisar = null; resolver(this.lineas.shift()); };
    });
  }

  /** Envía un comando y devuelve las líneas @ de la respuesta, hasta una que empiece con algo de «fin». */
  comando(cmd, fin = ["@OK", "@ERROR", "@FIN"], espera = 6000) {
    // Un comando a la vez: el monitor responde en orden y no hay forma de saber a qué pregunta corresponde una línea.
    const trabajo = this.ocupado.then(() => this._comando(cmd, fin, espera));
    this.ocupado = trabajo.catch(() => {});
    return trabajo;
  }

  async _comando(cmd, fin, espera) {
    if (!this.puerto?.writable) throw new ErrorMonitor("No hay un monitor conectado.");
    this.lineas = [];
    const escritor = this.puerto.writable.getWriter();
    try { await escritor.write(new TextEncoder().encode(cmd + "\n")); } finally { escritor.releaseLock(); }
    const respuesta = [], hasta = Date.now() + espera;
    while (Date.now() < hasta) {
      const linea = await this._siguiente(hasta);
      if (linea === null) break;
      respuesta.push(linea);
      if (fin.some((f) => linea.startsWith(f))) break;
    }
    const ultima = respuesta[respuesta.length - 1] || "";
    if (!fin.some((f) => ultima.startsWith(f))) {
      throw new ErrorMonitor(`El monitor no respondió a ${cmd.split(" ")[0]}. ¿Tiene el firmware 2.0 o posterior?`);
    }
    if (ultima.startsWith("@ERROR")) throw new ErrorMonitor(ultima.slice(7) || "El monitor rechazó el cambio.");
    return respuesta;
  }

  static _json(linea) { return JSON.parse(linea.slice(linea.indexOf(" ") + 1)); }

  async info() { return MonitorUSB._json((await this.comando("@INFO?", ["@INFO", "@ERROR"])).pop()); }

  async config() {
    let equipo = {};
    const sensores = [];
    for (const l of await this.comando("@CFG?")) {
      if (l.startsWith("@CFG_EQUIPO")) equipo = MonitorUSB._json(l);
      else if (l.startsWith("@CFG_SENSOR")) sensores.push(MonitorUSB._json(l));
    }
    return { equipo, sensores };
  }

  async sensores() { return (await this.comando("@SENSORES?")).filter((l) => l.startsWith("@SENSOR ")).map(MonitorUSB._json); }

  async eventos() { return (await this.comando("@EVENTOS?")).filter((l) => l.startsWith("@EV ")).map((l) => l.slice(4)); }

  async clave() { return (await this.comando("@CLAVE?", ["@CLAVE", "@ERROR"])).pop().split(" ")[1] || ""; }

  /** Devuelve true si el monitor se reinicia (cambió el modelo de pantalla). */
  async ponerEquipo({ codigo, pantalla, buzzer_temp, buzzer_hum }) {
    const r = await this.comando(`@EQUIPO_SET ${codigo}|${pantalla}|${buzzer_temp ? 1 : 0}|${buzzer_hum ? 1 : 0}`);
    return r[r.length - 1].includes("REINICIO");
  }

  ponerSensor(s) {
    return this.comando(`@SENSOR_SET ${s.ieee4}|${s.nombre}|${s.perfil}|${Number(s.corr_t).toFixed(1)}|${Math.trunc(s.corr_h)}|${s.calibrado || ""}|${s.oculto ? 1 : 0}`);
  }

  borrarSensor(ieee4) { return this.comando(`@SENSOR_DEL ${ieee4}`); }
  ponerHora() { return this.comando(`@HORA ${Math.floor(Date.now() / 1000)}`); }
  emparejar() { return this.comando("@EMPAREJAR"); }
  reiniciar() { return this.comando("@REINICIAR"); }

  /** Estado del WiFi (firmware 2.1 o posterior); null si el firmware no lo tiene. */
  async wifi() {
    try { return MonitorUSB._json((await this.comando("@WIFI?", ["@WIFI ", "@ERROR"], 3000)).pop()); }
    catch (_) { return null; }
  }

  ponerWifi(red, clave, servidor) { return this.comando(`@WIFI_SET ${red}|${clave}|${servidor}`); }
  borrarWifi() { return this.comando("@WIFI_BORRAR"); }

  /** Ejecuta algo que reinicia el monitor (por defecto @REINICIAR). El puerto USB desaparece y vuelve: espera ~6 s,
   *  lo vuelve a abrir y devuelve el nuevo @INFO. */
  async reiniciarYReconectar(cmd = () => this.reiniciar()) {
    this.reiniciando = true;
    try { await cmd(); return await this._reconectar(); }
    finally { this.reiniciando = false; }
  }

  async _reconectar() {
    const info = this.idUSB || {};
    await this.cerrar();
    await new Promise((r) => setTimeout(r, 6000));
    for (let i = 0; i < 20; i++) {
      const candidatos = (await navigator.serial.getPorts()).filter((p) => {
        const x = p.getInfo?.() || {};
        return !info.usbVendorId || (x.usbVendorId === info.usbVendorId && x.usbProductId === info.usbProductId);
      });
      for (const p of candidatos) {
        try { await this.abrir(p); return await this.info(); }
        catch (_) { await this.cerrar(); }
      }
      await new Promise((r) => setTimeout(r, 1000));
    }
    throw new ErrorMonitor("El monitor no volvió después de reiniciar. Pulsa «Conectar monitor» de nuevo.");
  }
}
