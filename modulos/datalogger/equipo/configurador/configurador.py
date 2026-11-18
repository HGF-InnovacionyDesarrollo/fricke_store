"""Monitor T/H Hospital Dr. Gustavo Fricke: aplicativo para instalar y configurar los monitores (Unidad de Innovación y Desarrollo).

Aplicativo de Windows para instalar el firmware y configurar los monitores de
temperatura y humedad (ESP32-C6) por USB, sin Arduino ni compilación:

- Equipo: código, número de serie, versión, hora, SD y respaldo de energía.
- Configuración: código (MTH-01...), modelo de pantalla y qué alarmas suenan.
- Sensores: nombre, área, corrección de calibración, fecha de calibración, ocultar.
- Firmware: instala el firmware incluido sin borrar la clave de firma, los sensores
  emparejados ni la red Zigbee (o borra todo, para un equipo nuevo).
- Registro: últimos eventos, exportar la clave de firma, guardar y cargar la
  configuración en un archivo.

Habla con el monitor con los comandos @ del firmware 2.0 (ver protocolo.md).
Se empaqueta en un .exe con construir.bat.
"""
import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
import unicodedata
from contextlib import redirect_stderr, redirect_stdout
from tkinter import filedialog, messagebox, ttk

import serial
import serial.tools.list_ports

TITULO = "Monitor T/H Hospital Dr. Gustavo Fricke"
VID_ESPRESSIF = 0x303A
AREAS = {"MED": "Medicamentos", "EST": "Material estéril"}
AREAS_INV = {v: k for k, v in AREAS.items()}
CORR_MAX_T, CORR_MAX_H = 3.0, 15.0


def recurso(*partes: str) -> str:
    """Ruta a un archivo incluido (funciona también dentro del .exe de PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *partes)


def version_firmware_incluido() -> str:
    try:
        with open(recurso("firmware", "version.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "?"


def texto_monitor(txt: str, largo: int) -> str:
    """Texto apto para la pantalla del monitor: sin tildes ni | " ; \\."""
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    for c in '|";\\':
        txt = txt.replace(c, " ")
    return " ".join(txt.split())[:largo]


# ======================= Comunicación con el monitor =======================

class ErrorMonitor(Exception):
    pass


class Monitor:
    """Puerto serie del monitor. Todas las llamadas se hacen desde el hilo de trabajo."""

    def __init__(self, registro):
        self.puerto = None
        self.ser = None
        self.registro = registro  # función para mostrar líneas en la consola

    def abrir(self, puerto: str):
        s = serial.Serial()
        s.port = puerto
        s.baudrate = 115200
        s.timeout = 0.2
        s.dtr = False  # sin esto el monitor se reiniciaría al abrir el puerto
        s.rts = False
        s.open()
        self.ser, self.puerto = s, puerto
        time.sleep(0.3)
        self.ser.reset_input_buffer()

    def cerrar(self):
        if self.ser:
            try:
                self.ser.close()
            except serial.SerialException:
                pass
        self.ser = None

    @property
    def abierto(self) -> bool:
        return self.ser is not None and self.ser.is_open

    def _leer_linea(self, hasta: float):
        buf = b""
        while time.time() < hasta:
            c = self.ser.read(1)
            if not c:
                continue
            if c == b"\n":
                linea = buf.decode("utf-8", "replace").strip()
                if linea and not linea.startswith("@"):
                    self.registro(linea)
                return linea
            buf += c
        return None

    def comando(self, cmd: str, fin=("@OK", "@ERROR", "@FIN"), espera=6.0) -> list[str]:
        """Envía un comando y devuelve las líneas @ de la respuesta, hasta una de 'fin'."""
        if not self.abierto:
            raise ErrorMonitor("No hay un monitor conectado.")
        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\n").encode("utf-8"))
        respuesta = []
        hasta = time.time() + espera
        while time.time() < hasta:
            linea = self._leer_linea(hasta)
            if linea is None:
                break
            if not linea.startswith("@"):
                continue
            respuesta.append(linea)
            if any(linea.startswith(f) for f in fin):
                break
        else:
            pass
        if not respuesta or not any(respuesta[-1].startswith(f) for f in fin):
            raise ErrorMonitor(f"El monitor no respondió a {cmd.split()[0]}. ¿Tiene el firmware 2.0 o posterior?")
        if respuesta[-1].startswith("@ERROR"):
            raise ErrorMonitor(respuesta[-1][7:] or "error del monitor")
        return respuesta

    @staticmethod
    def _json(linea: str) -> dict:
        return json.loads(linea.split(" ", 1)[1])

    def info(self) -> dict:
        return self._json(self.comando("@INFO?", fin=("@INFO", "@ERROR"))[-1])

    def info_antigua(self) -> str | None:
        """Firmware 1.x (sin comandos @): devuelve la línea 'Equipo ...' del comando EQUIPO."""
        self.ser.reset_input_buffer()
        self.ser.write(b"EQUIPO\n")
        hasta = time.time() + 3
        while time.time() < hasta:
            linea = self._leer_linea(hasta)
            if linea and linea.startswith("Equipo "):
                return linea
        return None

    def config(self) -> tuple[dict, list[dict]]:
        lineas = self.comando("@CFG?")
        equipo, sensores = {}, []
        for l in lineas:
            if l.startswith("@CFG_EQUIPO"):
                equipo = self._json(l)
            elif l.startswith("@CFG_SENSOR"):
                sensores.append(self._json(l))
        return equipo, sensores

    def sensores(self) -> list[dict]:
        return [self._json(l) for l in self.comando("@SENSORES?") if l.startswith("@SENSOR ")]

    def eventos(self) -> list[str]:
        return [l[4:] for l in self.comando("@EVENTOS?") if l.startswith("@EV ")]

    def clave(self) -> str:
        return self.comando("@CLAVE?", fin=("@CLAVE", "@ERROR"))[-1].split(" ", 1)[1]

    def poner_equipo(self, codigo: str, pantalla: int, buz_t: bool, buz_h: bool) -> bool:
        """Devuelve True si el monitor se reinicia (cambio de pantalla)."""
        r = self.comando(f"@EQUIPO_SET {codigo}|{pantalla}|{int(buz_t)}|{int(buz_h)}")
        return "REINICIO" in r[-1]

    def poner_sensor(self, s: dict):
        self.comando("@SENSOR_SET {ieee4}|{nombre}|{perfil}|{corr_t:.1f}|{corr_h:d}|{calibrado}|{oculto:d}".format(**s))

    def borrar_sensor(self, ieee4: str):
        self.comando(f"@SENSOR_DEL {ieee4}")

    def poner_hora(self):
        self.comando(f"@HORA {int(time.time())}")

    def emparejar(self):
        self.comando("@EMPAREJAR")

    def reiniciar(self):
        self.comando("@REINICIAR")


def puertos() -> list[tuple[str, str]]:
    """(puerto, descripción); primero los de Espressif (ESP32-C6 por USB)."""
    lista = []
    for p in serial.tools.list_ports.comports():
        esp = p.vid == VID_ESPRESSIF
        lista.append((not esp, p.device, f"{p.device} — {'ESP32 (Espressif)' if esp else p.description}"))
    lista.sort()
    return [(d, t) for _, d, t in lista]


def flashear(puerto: str, borrar_todo: bool, escribir):
    """Instala el firmware incluido con esptool. escribir(texto) recibe la salida."""
    import esptool

    texto = []

    class Salida:
        def write(self, t):
            texto.append(t)
            if t.strip():
                escribir(t.rstrip())

        def flush(self):
            pass

    base = ["--chip", "esp32c6", "--port", puerto, "--baud", "921600"]
    with redirect_stdout(Salida()), redirect_stderr(Salida()):
        # La partición del firmware depende del tamaño de la flash de la placa:
        # instalar la de 8 MB en una de 4 MB deja la red Zigbee y el respaldo fuera de la memoria.
        esptool.main(base + ["flash-id"])
        m = re.search(r"Detected flash size:\s*(\d+)MB", "".join(texto))
        mb = int(m.group(1)) if m else 0
        if mb >= 8:
            carpeta = "8MB"
        elif mb == 4:
            carpeta = "4MB"
        else:
            raise RuntimeError(f"No se pudo usar esta placa: flash de {mb or '¿?'} MB "
                               "(el firmware necesita 4 u 8 MB).")
        escribir(f"Placa con flash de {mb} MB: se instala el firmware para {carpeta}.")
        fw = lambda n: recurso("firmware", carpeta, n)
        if borrar_todo:
            esptool.main(base + ["erase-flash"])
        esptool.main(base + ["--before", "default-reset", "--after", "hard-reset", "write-flash", "-z",
                             "--flash-mode", "keep", "--flash-freq", "keep", "--flash-size", "keep",
                             "0x0", fw("bootloader.bin"), "0x8000", fw("partitions.bin"),
                             "0xe000", fw("boot_app0.bin"), "0x10000", fw("Monitor_TH.bin")])


# ======================= Interfaz =======================
#
# Sistema de diseño único para todas las vistas:
#   - Espacios: escala 4 / 8 / 16 / 24 px (E1..E4), multiplicada por la escala de
#     Windows (125 %, 150 %...) para que se vea igual en cualquier pantalla.
#   - Cada pestaña: título, descripción, contenido en tarjetas blancas y la barra
#     de acciones abajo (botón principal en azul, a la izquierda).
#   - Formularios con la columna de etiquetas del mismo ancho en todas las tarjetas.
#   - Colores del logo (azul y rojo de Gobierno de Chile) y estados en verde,
#     ámbar o rojo.

C = {
    "azul": "#0F69B4", "azul_osc": "#0A4F8A", "azul_claro": "#E7F0FA", "azul_texto": "#CFE2F3",
    "rojo": "#C62833", "rojo_claro": "#FDECEE",
    "verde": "#2E7D32", "verde_claro": "#E8F5E9",
    "ambar": "#9A5B00", "ambar_claro": "#FFF4E0",
    "fondo": "#F3F5F8", "tarjeta": "#FFFFFF", "borde": "#D9DFE6", "zebra": "#F7F9FB",
    "texto": "#1F2933", "tenue": "#5B6770", "gris": "#9AA4AE", "consola": "#FAFBFC",
}
E1, E2, E3, E4 = 4, 8, 16, 24
FUENTE = "Segoe UI"
MONO = "Consolas"
ANCHO_ETIQUETA = 190  # columna de etiquetas de todos los formularios
ESCALA = 1.0


def px(n: float) -> int:
    """Pixeles ajustados a la escala de pantalla de Windows."""
    return int(round(n * ESCALA))


def activar_dpi():
    """Texto nítido en pantallas con escala (sin esto Windows estira la ventana y se ve borrosa)."""
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class Aplicacion(tk.Tk):
    def __init__(self):
        activar_dpi()
        super().__init__()
        global ESCALA
        ESCALA = max(1.0, self.winfo_fpixels("1i") / 96)
        self.title(TITULO)
        ancho = min(px(1120), self.winfo_screenwidth() - px(40))
        alto = min(px(800), self.winfo_screenheight() - px(80))
        self.geometry(f"{ancho}x{alto}")
        self.minsize(min(px(980), ancho), min(px(640), alto))
        try:
            self.iconbitmap(recurso("icono.ico"))
        except tk.TclError:
            pass
        self.trabajos: queue.Queue = queue.Queue()
        self.monitor = Monitor(self._consola)
        self.info: dict = {}
        self.cfg_equipo: dict = {}
        self.cfg_sensores: list[dict] = []
        self.vivos: list[dict] = []
        threading.Thread(target=self._hilo, daemon=True).start()
        self._estilos()
        self._construir()
        self._buscar_puertos()

    # ---------- hilo de trabajo: toda la comunicación serie pasa por aquí ----------
    def _hilo(self):
        while True:
            funcion, al_terminar, descripcion = self.trabajos.get()
            self.after(0, self._estado, descripcion + "…", "trabajando")
            try:
                resultado = funcion()
                error = None
            except Exception as e:  # se muestra al usuario
                resultado, error = None, e
            self.after(0, self._fin_trabajo, al_terminar, resultado, error)

    def trabajo(self, funcion, al_terminar=None, descripcion="Trabajando"):
        self.trabajos.put((funcion, al_terminar, descripcion))

    def _fin_trabajo(self, al_terminar, resultado, error):
        if error:
            self._estado(f"Error: {error}", "alerta")
            messagebox.showerror(TITULO, str(error))
        else:
            self._estado("Listo")
            if al_terminar:
                al_terminar(resultado)

    def _estado(self, texto, tipo="normal"):
        color = {"trabajando": C["azul"], "alerta": C["rojo"]}.get(tipo, C["tenue"])
        self.lbl_estado_punto.config(fg=color)
        self.lbl_estado.config(text=texto, fg=color if tipo != "normal" else C["texto"])

    def _consola(self, linea):
        self.after(0, self._agregar_consola, linea)

    def _agregar_consola(self, linea):
        self.txt_consola.configure(state="normal")
        self.txt_consola.insert("end", linea + "\n")
        if int(self.txt_consola.index("end-1c").split(".")[0]) > 2000:
            self.txt_consola.delete("1.0", "500.0")
        self.txt_consola.see("end")
        self.txt_consola.configure(state="disabled")

    # ---------- estilos ----------
    def _estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")  # el único tema de Windows que respeta colores y bordes
        self.configure(bg=C["fondo"])
        self.option_add("*TCombobox*Listbox.font", (FUENTE, 10))
        self.option_add("*TCombobox*Listbox.selectBackground", C["azul"])
        base = {"font": (FUENTE, 10), "background": C["fondo"], "foreground": C["texto"]}
        indicador = {"indicatorsize": px(15), "indicatormargin": (0, 0, px(E2), 0),
                     "indicatorbackground": C["tarjeta"], "indicatorforeground": "white",
                     "upperbordercolor": C["gris"], "lowerbordercolor": C["gris"]}

        def indicador_map(color):
            return {"indicatorbackground": [("selected", color), ("active", C["azul_claro"])],
                    "upperbordercolor": [("selected", color), ("active", C["azul"])],
                    "lowerbordercolor": [("selected", color), ("active", C["azul"])]}

        s.configure(".", **base, bordercolor=C["borde"], focuscolor=C["azul"], troughcolor=C["fondo"])
        s.configure("TFrame", background=C["fondo"])
        s.configure("Tarjeta.TFrame", background=C["tarjeta"])
        for nombre, fondo in (("", C["fondo"]), ("Tarjeta.", C["tarjeta"])):
            s.configure(f"{nombre}TLabel", background=fondo, foreground=C["texto"])
            s.configure(f"{nombre}Tenue.TLabel", background=fondo, foreground=C["tenue"])
            for w in ("TCheckbutton", "TRadiobutton"):
                s.configure(f"{nombre}{w}", background=fondo, padding=(0, px(E1)), **indicador)
                s.map(f"{nombre}{w}", background=[("active", fondo)], **indicador_map(C["azul"]))
        s.configure("Peligro.TCheckbutton", background=C["rojo_claro"], foreground=C["rojo"], padding=(0, px(E1)),
                    font=(FUENTE, 10, "bold"), **indicador)
        s.map("Peligro.TCheckbutton", background=[("active", C["rojo_claro"])], **indicador_map(C["rojo"]))
        s.configure("Titulo.TLabel", font=(FUENTE, 15, "bold"), foreground=C["texto"])
        s.configure("Seccion.TLabel", background=C["tarjeta"], font=(FUENTE, 11, "bold"), foreground=C["azul_osc"])
        s.configure("Valor.TLabel", background=C["tarjeta"], font=(FUENTE, 10, "bold"))
        s.configure("Grande.TLabel", background=C["tarjeta"], font=(FUENTE, 22, "bold"), foreground=C["azul"])

        # botones: secundario (blanco), principal (azul) y peligro (texto rojo)
        boton = {"padding": (px(E3), px(E2) - 2), "relief": "flat", "borderwidth": 1, "anchor": "center"}
        s.configure("TButton", **boton, background=C["tarjeta"], foreground=C["texto"], bordercolor=C["borde"],
                    lightcolor=C["tarjeta"], darkcolor=C["tarjeta"])
        s.map("TButton", background=[("disabled", C["fondo"]), ("pressed", C["borde"]), ("active", C["azul_claro"])],
              bordercolor=[("active", C["azul"])], foreground=[("disabled", C["gris"])])
        s.configure("Primario.TButton", **boton, background=C["azul"], foreground="white", bordercolor=C["azul"],
                    lightcolor=C["azul"], darkcolor=C["azul"], font=(FUENTE, 10, "bold"))
        s.map("Primario.TButton", background=[("disabled", C["gris"]), ("pressed", C["azul_osc"]),
                                              ("active", C["azul_osc"])],
              lightcolor=[("active", C["azul_osc"])], darkcolor=[("active", C["azul_osc"])],
              bordercolor=[("active", C["azul_osc"])], foreground=[("disabled", "white")])
        s.configure("Peligro.TButton", **boton, background=C["tarjeta"], foreground=C["rojo"], bordercolor=C["borde"],
                    lightcolor=C["tarjeta"], darkcolor=C["tarjeta"])
        s.map("Peligro.TButton", background=[("pressed", C["rojo_claro"]), ("active", C["rojo_claro"])],
              bordercolor=[("active", C["rojo"])])

        # campos
        campo = {"padding": (px(E2), px(E1) + 1), "fieldbackground": C["tarjeta"], "bordercolor": C["borde"],
                 "lightcolor": C["tarjeta"], "darkcolor": C["tarjeta"], "arrowsize": px(12)}
        s.configure("TEntry", **campo)
        s.configure("TCombobox", **campo, background=C["tarjeta"], arrowcolor=C["tenue"])
        for w in ("TEntry", "TCombobox"):
            s.map(w, bordercolor=[("focus", C["azul"])], lightcolor=[("focus", C["azul"])],
                  fieldbackground=[("readonly", C["tarjeta"])], selectbackground=[("readonly", C["tarjeta"])],
                  selectforeground=[("readonly", C["texto"])])

        # pestañas
        s.configure("TNotebook", background=C["tarjeta"], bordercolor=C["borde"], lightcolor=C["fondo"],
                    darkcolor=C["fondo"], borderwidth=1, tabmargins=(px(E3), px(E2), px(E3), 0))
        s.configure("TNotebook.Tab", padding=(px(E4), px(E2) + 2), font=(FUENTE, 10), background=C["tarjeta"],
                    foreground=C["tenue"], bordercolor=C["borde"], lightcolor=C["tarjeta"], darkcolor=C["tarjeta"])
        s.map("TNotebook.Tab", background=[("selected", C["fondo"]), ("active", C["azul_claro"])],
              foreground=[("selected", C["azul"])], font=[("selected", (FUENTE, 10, "bold"))],
              lightcolor=[("selected", C["fondo"])], darkcolor=[("selected", C["fondo"])],
              expand=[("selected", (0, 0, 0, 0))], padding=[("selected", (px(E4), px(E2) + 2))])
        # sin el rectángulo punteado de foco
        s.layout("TNotebook.Tab", [("Notebook.tab", {"sticky": "nswe", "children": [
            ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                ("Notebook.label", {"side": "top", "sticky": ""})]})]})])

        # tabla
        s.configure("Treeview", rowheight=px(30), background=C["tarjeta"], fieldbackground=C["tarjeta"],
                    bordercolor=C["tarjeta"], borderwidth=0, font=(FUENTE, 10))
        s.map("Treeview", background=[("selected", C["azul_claro"])], foreground=[("selected", C["texto"])])
        s.configure("Treeview.Heading", background=C["fondo"], foreground=C["tenue"], font=(FUENTE, 9, "bold"),
                    relief="flat", borderwidth=0, padding=(px(E2), px(E2)), lightcolor=C["fondo"],
                    darkcolor=C["fondo"], bordercolor=C["borde"])
        s.map("Treeview.Heading", background=[("active", C["azul_claro"])])
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        s.configure("Vertical.TScrollbar", background=C["fondo"], bordercolor=C["fondo"], arrowcolor=C["tenue"],
                    lightcolor=C["fondo"], darkcolor=C["fondo"], troughcolor=C["tarjeta"], gripcount=0)

    # ---------- piezas reutilizables ----------
    @staticmethod
    def _ajustable(lbl, margen=0):
        """El texto se reparte en líneas según el ancho disponible."""
        lbl.bind("<Configure>", lambda e: lbl.configure(wraplength=max(px(200), e.width - margen)))

    def _pagina(self, pestana: str, titulo: str, descripcion: str):
        """Pestaña con descripción, contenido y barra de acciones abajo. Devuelve (contenido, acciones).

        `titulo` documenta la vista en el código; no se muestra porque la pestaña ya lo dice."""
        f = ttk.Frame(self.nb, padding=(px(E4), px(E3), px(E4), px(E3)))
        self.nb.add(f, text=pestana)
        d = ttk.Label(f, text=descripcion, style="Tenue.TLabel", justify="left")
        d.pack(anchor="w", fill="x", pady=(0, px(E3)))
        self._ajustable(d)
        acciones = ttk.Frame(f)
        acciones.pack(side="bottom", fill="x", pady=(px(E3), 0))
        contenido = ttk.Frame(f)
        contenido.pack(fill="both", expand=True)
        return contenido, acciones

    def _tarjeta(self, padre, titulo: str | None = None, descripcion: str | None = None):
        """Tarjeta blanca con borde. Devuelve (marco para ubicarla, cuerpo para el contenido)."""
        marco = tk.Frame(padre, bg=C["tarjeta"], highlightbackground=C["borde"], highlightcolor=C["borde"],
                         highlightthickness=1)
        interior = ttk.Frame(marco, style="Tarjeta.TFrame", padding=px(E3))
        interior.pack(fill="both", expand=True)
        if titulo:
            ttk.Label(interior, text=titulo, style="Seccion.TLabel").pack(anchor="w")
        if descripcion:
            d = ttk.Label(interior, text=descripcion, style="Tarjeta.Tenue.TLabel", justify="left")
            d.pack(anchor="w", fill="x", pady=(px(2), 0))
            self._ajustable(d)
        cuerpo = ttk.Frame(interior, style="Tarjeta.TFrame")
        cuerpo.pack(fill="both", expand=True, pady=(px(E3) if titulo or descripcion else 0, 0))
        return marco, cuerpo

    def _nota(self, padre, texto: str, tipo: str = "info"):
        """Recuadro de ayuda (info, aviso o peligro) con una franja de color a la izquierda."""
        fondo, borde = {"info": (C["azul_claro"], C["azul"]), "aviso": (C["ambar_claro"], C["ambar"]),
                        "peligro": (C["rojo_claro"], C["rojo"])}[tipo]
        marco = tk.Frame(padre, bg=fondo)
        tk.Frame(marco, bg=borde, width=px(4)).pack(side="left", fill="y")
        lbl = tk.Label(marco, text=texto, bg=fondo, fg=C["texto"], font=(FUENTE, 10), justify="left", anchor="w")
        lbl.pack(side="left", fill="both", expand=True, padx=px(E3), pady=px(E2) + 2)
        self._ajustable(lbl, px(E2))
        return marco

    @staticmethod
    def _boton(padre, texto, comando, estilo="TButton"):
        b = ttk.Button(padre, text=texto, command=comando, style=estilo, cursor="hand2")
        b.pack(side="left", padx=(0, px(E2)))
        return b

    @staticmethod
    def _fila_form(cuerpo, fila: int, etiqueta: str, widget, ayuda: str | None = None):
        """Fila de formulario: etiqueta | campo | ayuda (misma columna de etiquetas en todo el aplicativo)."""
        cuerpo.columnconfigure(0, minsize=px(ANCHO_ETIQUETA))
        ttk.Label(cuerpo, text=etiqueta, style="Tarjeta.TLabel").grid(row=fila, column=0, sticky="w",
                                                                      pady=px(E1) + 2)
        if not ayuda:
            widget.grid(row=fila, column=1, sticky="w", pady=px(E1) + 2)
            return
        celda = ttk.Frame(cuerpo, style="Tarjeta.TFrame")
        celda.grid(row=fila, column=1, sticky="w", pady=px(E1) + 2)
        widget.pack(in_=celda, side="left")
        widget.lift(celda)
        ttk.Label(celda, text=ayuda, style="Tarjeta.Tenue.TLabel").pack(side="left", padx=(px(E2), 0))

    def _texto(self, padre, alto: int, tam: int = 9):
        """Cuadro de texto de solo lectura con barra de desplazamiento."""
        marco = tk.Frame(padre, bg=C["borde"], padx=1, pady=1)
        t = tk.Text(marco, height=alto, state="disabled", font=(MONO, tam), bg=C["consola"], fg=C["texto"],
                    relief="flat", borderwidth=0, padx=px(E2), pady=px(E2), wrap="none",
                    selectbackground=C["azul_claro"], selectforeground=C["texto"])
        barra = ttk.Scrollbar(marco, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        t.pack(side="left", fill="both", expand=True)
        marco.pack(fill="both", expand=True)
        return t

    # ---------- construcción de la ventana ----------
    def _construir(self):
        # cabecera azul con logo, nombre y estado de la conexión
        cab = tk.Frame(self, bg=C["azul"])
        cab.pack(fill="x")
        interior = tk.Frame(cab, bg=C["azul"])
        interior.pack(fill="x", padx=px(E4), pady=px(E3))
        try:
            self.img_logo = tk.PhotoImage(file=recurso("logo_app_2x.png" if ESCALA >= 1.5 else "logo_app.png"))
            tk.Label(interior, image=self.img_logo, bg=C["azul"]).pack(side="left")
        except tk.TclError:
            pass
        textos = tk.Frame(interior, bg=C["azul"])
        textos.pack(side="left", padx=(px(E3), 0))
        tk.Label(textos, text=TITULO, font=(FUENTE, 15, "bold"), fg="white", bg=C["azul"]).pack(anchor="w")
        tk.Label(textos, text="Unidad de Innovación y Desarrollo · instalación y configuración de los monitores",
                 font=(FUENTE, 10), fg=C["azul_texto"], bg=C["azul"]).pack(anchor="w")
        self.lbl_equipo = tk.Label(interior, font=(FUENTE, 10, "bold"), padx=px(E3), pady=px(E1) + 2)
        self.lbl_equipo.pack(side="right")
        self._chip("Sin conectar")

        # barra de conexión
        zona = ttk.Frame(self, padding=(px(E4), px(E3), px(E4), 0))
        zona.pack(fill="x")
        marco, c = self._tarjeta(zona)
        marco.pack(fill="x")
        ttk.Label(c, text="Puerto USB", style="Tarjeta.TLabel", font=(FUENTE, 10, "bold")).pack(side="left")
        self.cmb_puerto = ttk.Combobox(c, state="readonly", font=(FUENTE, 10))
        self.cmb_puerto.pack(side="left", fill="x", expand=True, padx=px(E3))
        b = ttk.Button(c, text="Buscar puertos", command=self._buscar_puertos, cursor="hand2")
        b.pack(side="left", padx=(0, px(E2)))
        self.btn_conectar = ttk.Button(c, text="Conectar", command=self._conectar, style="Primario.TButton",
                                       width=13, cursor="hand2")
        self.btn_conectar.pack(side="left")

        # pie con el estado del trabajo en curso (se arma antes para que quede abajo)
        pie = tk.Frame(self, bg=C["tarjeta"], highlightbackground=C["borde"], highlightthickness=1)
        pie.pack(side="bottom", fill="x")
        pi = tk.Frame(pie, bg=C["tarjeta"])
        pi.pack(fill="x", padx=px(E4), pady=px(E1) + 2)
        self.lbl_estado_punto = tk.Label(pi, text="●", bg=C["tarjeta"], fg=C["tenue"], font=(FUENTE, 9))
        self.lbl_estado_punto.pack(side="left")
        self.lbl_estado = tk.Label(pi, text="Listo", bg=C["tarjeta"], fg=C["texto"], font=(FUENTE, 9), anchor="w")
        self.lbl_estado.pack(side="left", padx=(px(E1), 0), fill="x", expand=True)
        tk.Label(pi, text=f"Firmware incluido {version_firmware_incluido()}", bg=C["tarjeta"], fg=C["tenue"],
                 font=(FUENTE, 9)).pack(side="right")

        # pestañas
        cont = ttk.Frame(self, padding=(px(E4), px(E3), px(E4), px(E3)))
        cont.pack(fill="both", expand=True)
        marco = tk.Frame(cont, bg=C["tarjeta"], highlightbackground=C["borde"], highlightthickness=1)
        marco.pack(fill="both", expand=True)
        self.nb = ttk.Notebook(marco)
        self.nb.pack(fill="both", expand=True)
        self._pestana_equipo()
        self._pestana_config()
        self._pestana_sensores()
        self._pestana_firmware()
        self._pestana_registro()

    def _chip(self, texto: str, tipo: str = "neutro"):
        """Indicador de conexión en la cabecera."""
        fondo, letra = {"ok": (C["verde_claro"], C["verde"]), "aviso": (C["ambar_claro"], C["ambar"]),
                        "neutro": (C["azul_osc"], "white")}[tipo]
        self.lbl_equipo.config(text="●  " + texto, bg=fondo, fg=letra)

    def _pestana_equipo(self):
        c, acc = self._pagina("Equipo", "Estado del equipo",
                              "Lo que informa el monitor conectado. «Actualizar» lo vuelve a leer.")
        self._boton(acc, "Actualizar", self._leer_todo, "Primario.TButton")
        self._boton(acc, "Poner la hora del PC", self._poner_hora)
        self._boton(acc, "Abrir red para emparejar (3 min)", self._emparejar)
        self._boton(acc, "Reiniciar monitor", self._reiniciar, "Peligro.TButton")

        c.columnconfigure(0, weight=2, uniform="col")
        c.columnconfigure(1, weight=3, uniform="col")
        self.campos_info = {}
        grupos = [("Identificación", [("codigo", "Código"), ("serie", "Número de serie"), ("firmware", "Firmware"),
                                      ("pantalla", "Pantalla")]),
                  ("Funcionamiento", [("hora", "Hora del monitor"), ("sd", "Tarjeta SD"),
                                      ("energia", "Respaldo de energía"), ("sensores", "Sensores emparejados"),
                                      ("emparejando", "Emparejamiento")])]
        for col, (titulo, filas) in enumerate(grupos):
            marco, cuerpo = self._tarjeta(c, titulo)
            marco.grid(row=0, column=col, sticky="nsew", padx=(0, px(E3)) if col == 0 else 0)
            cuerpo.columnconfigure(1, weight=1)
            for i, (clave, texto) in enumerate(filas):
                ttk.Label(cuerpo, text=texto, style="Tarjeta.Tenue.TLabel").grid(
                    row=i, column=0, sticky="nw", pady=px(E1) + 1, padx=(0, px(E3)))
                lbl = ttk.Label(cuerpo, text="—", style="Valor.TLabel", justify="left")
                lbl.grid(row=i, column=1, sticky="ew", pady=px(E1) + 1)
                self._ajustable(lbl)
                self.campos_info[clave] = lbl
        self._nota(c, "Para emparejar un sensor: pulse «Abrir red para emparejar», acerque el sensor al monitor y "
                      "mantenga su botón unos 5 s hasta que el LED parpadee. Después, en la pestaña Sensores, "
                      "póngale nombre, área y corrección.").grid(row=1, column=0, columnspan=2, sticky="ew",
                                                                  pady=(px(E3), 0))

    def _pestana_config(self):
        c, acc = self._pagina("Configuración", "Configuración del equipo",
                              "Se guarda en la memoria del monitor y queda registrada en sus eventos.")
        self._boton(acc, "Guardar en el monitor", self._guardar_equipo, "Primario.TButton")

        marco, cuerpo = self._tarjeta(c, "Equipo")
        marco.pack(fill="x")
        self.var_codigo = tk.StringVar()
        self._fila_form(cuerpo, 0, "Código del equipo", ttk.Entry(cuerpo, textvariable=self.var_codigo, width=18),
                        "Por ejemplo MTH-03. Aparece en la pantalla y en los registros.")
        self.var_pantalla = tk.IntVar(value=1)
        pf = ttk.Frame(cuerpo, style="Tarjeta.TFrame")
        ttk.Radiobutton(pf, text='1,9"  (170 × 320)', variable=self.var_pantalla, value=1,
                        style="Tarjeta.TRadiobutton").pack(side="left", padx=(0, px(E4)))
        ttk.Radiobutton(pf, text='2,4"  (240 × 320)', variable=self.var_pantalla, value=2,
                        style="Tarjeta.TRadiobutton").pack(side="left")
        self._fila_form(cuerpo, 1, "Modelo de pantalla", pf)
        self.var_buz_t = tk.BooleanVar()
        self.var_buz_h = tk.BooleanVar()
        af = ttk.Frame(cuerpo, style="Tarjeta.TFrame")
        ttk.Checkbutton(af, text="Temperatura", variable=self.var_buz_t, style="Tarjeta.TCheckbutton").pack(
            side="left", padx=(0, px(E4)))
        ttk.Checkbutton(af, text="Humedad", variable=self.var_buz_h, style="Tarjeta.TCheckbutton").pack(side="left")
        self._fila_form(cuerpo, 2, "Alarmas que suenan", af)
        ayuda = ttk.Label(cuerpo, style="Tarjeta.Tenue.TLabel", justify="left", text=(
            "Las alarmas que no suenan igual se ven en la pantalla y quedan en los eventos. La alerta de la "
            "tarjeta SD suena siempre."))
        ayuda.grid(row=3, column=1, sticky="ew")
        cuerpo.columnconfigure(1, weight=1)
        self._ajustable(ayuda)

        self._nota(c, "Si cambia el modelo de pantalla, el monitor se reinicia. Después conviene pulsar el botón de "
                      "cada sensor para que se reconecten de inmediato.", "aviso").pack(fill="x", pady=(px(E3), 0))

    def _pestana_sensores(self):
        c, acc = self._pagina("Sensores", "Sensores",
                              "Doble clic en un sensor para ponerle nombre, área, corrección de calibración u "
                              "ocultarlo.")
        self._boton(acc, "Editar sensor…", self._editar_sensor, "Primario.TButton")
        self._boton(acc, "Actualizar", self._leer_todo)
        self._boton(acc, "Quitar su configuración", self._borrar_sensor, "Peligro.TButton")
        leyenda = ttk.Frame(acc)
        leyenda.pack(side="right")
        for texto, color in (("En alarma", C["rojo"]), ("Oculto o no emparejado", C["gris"])):
            tk.Label(leyenda, text="●", fg=color, bg=C["fondo"], font=(FUENTE, 10)).pack(side="left")
            ttk.Label(leyenda, text=texto, style="Tenue.TLabel").pack(side="left", padx=(px(2), px(E3)))

        marco = tk.Frame(c, bg=C["tarjeta"], highlightbackground=C["borde"], highlightthickness=1)
        marco.pack(fill="both", expand=True)
        columnas = [("n", "N°", 34, "center"), ("ieee4", "IEEE", 54, "center"), ("nombre", "Nombre", 128, "w"),
                    ("area", "Área", 162, "w"), ("t", "T (°C)", 58, "e"), ("h", "HR (%)", 58, "e"),
                    ("bat", "Batería", 62, "e"), ("edad", "Último dato", 90, "w"),
                    ("corr", "Corrección", 108, "w"), ("calibrado", "Calibrado", 128, "w"),
                    ("estado", "Estado", 112, "w")]
        self.tabla = ttk.Treeview(marco, columns=[x[0] for x in columnas], show="headings", height=12,
                                  selectmode="browse")
        for col, titulo, ancho, ancla in columnas:
            self.tabla.heading(col, text=titulo, anchor=ancla)
            self.tabla.column(col, width=px(ancho), minwidth=px(40), anchor=ancla, stretch=col == "nombre")
        barra = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", lambda e: self._editar_sensor())
        self.tabla.tag_configure("zebra", background=C["zebra"])
        self.tabla.tag_configure("alarma", foreground=C["rojo"], font=(FUENTE, 10, "bold"))
        self.tabla.tag_configure("oculto", foreground=C["gris"])

    def _pestana_firmware(self):
        c, acc = self._pagina("Firmware", "Instalar firmware",
                              "Usa el puerto elegido arriba. No hace falta Arduino ni conexión a Internet.")
        self.btn_flashear = self._boton(acc, "Instalar firmware", self._flashear, "Primario.TButton")

        c.columnconfigure(1, weight=1)
        marco, cuerpo = self._tarjeta(c, "Firmware incluido")
        marco.grid(row=0, column=0, sticky="nsew", padx=(0, px(E3)))
        self.lbl_fw = ttk.Label(cuerpo, text=version_firmware_incluido(), style="Grande.TLabel")
        self.lbl_fw.pack(anchor="w")
        ttk.Label(cuerpo, text="versión", style="Tarjeta.Tenue.TLabel").pack(anchor="w")

        marco, cuerpo = self._tarjeta(c, "Qué se conserva")
        marco.grid(row=0, column=1, sticky="nsew")
        d = ttk.Label(cuerpo, style="Tarjeta.TLabel", justify="left", text=(
            "La clave de firma, los sensores emparejados, la red Zigbee y la configuración del equipo. Los "
            "monitores con firmware 1.x se actualizan igual: al arrancar con la versión nueva recuperan solos su "
            "configuración."))
        d.pack(fill="x")
        self._ajustable(d)

        peligro = tk.Frame(c, bg=C["rojo_claro"])
        peligro.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(px(E3), 0))
        tk.Frame(peligro, bg=C["rojo"], width=px(4)).pack(side="left", fill="y")
        pi = tk.Frame(peligro, bg=C["rojo_claro"])
        pi.pack(side="left", fill="x", expand=True, padx=px(E3), pady=px(E2))
        self.var_borrar = tk.BooleanVar()
        ttk.Checkbutton(pi, text="Equipo nuevo: borrar TODA la memoria antes de instalar",
                        variable=self.var_borrar, style="Peligro.TCheckbutton").pack(anchor="w")
        d = tk.Label(pi, bg=C["rojo_claro"], fg=C["texto"], font=(FUENTE, 10), justify="left", anchor="w", text=(
            "Borra la clave de firma, los sensores, la red y la configuración. Solo para placas nuevas: nunca en "
            "un monitor en servicio."))
        d.pack(fill="x")
        self._ajustable(d)

        marco, cuerpo = self._tarjeta(c, "Mensajes de la instalación")
        marco.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(px(E3), 0))
        c.rowconfigure(2, weight=1)
        self.txt_fw = self._texto(cuerpo, alto=6)

    def _pestana_registro(self):
        c, acc = self._pagina("Registro", "Registro y archivos",
                              "Eventos del monitor, respaldo de su configuración y clave para verificar los "
                              "registros de la SD.")
        self._boton(acc, "Ver últimos eventos", self._ver_eventos, "Primario.TButton")
        self._boton(acc, "Guardar configuración en archivo…", self._guardar_archivo)
        self._boton(acc, "Cargar configuración desde archivo…", self._cargar_archivo)
        self._boton(acc, "Exportar clave de firma…", self._exportar_clave, "Peligro.TButton")

        c.columnconfigure(0, weight=1)
        c.rowconfigure(0, weight=3)
        c.rowconfigure(1, weight=2)
        marco, cuerpo = self._tarjeta(c, "Eventos desde el último arranque del monitor")
        marco.grid(row=0, column=0, sticky="nsew")
        self.txt_eventos = self._texto(cuerpo, alto=6)
        marco, cuerpo = self._tarjeta(c, "Consola del monitor", "Lo que el monitor escribe por USB.")
        marco.grid(row=1, column=0, sticky="nsew", pady=(px(E3), 0))
        self.txt_consola = self._texto(cuerpo, alto=4, tam=8)
        self.txt_consola.configure(fg=C["tenue"])

    # ---------- conexión ----------
    def _buscar_puertos(self):
        self.lista_puertos = puertos()
        self.cmb_puerto["values"] = [t for _, t in self.lista_puertos]
        if self.lista_puertos:
            self.cmb_puerto.current(0)
        else:
            self.cmb_puerto.set("No se encontraron puertos: conecte el monitor por USB")

    def _puerto_elegido(self) -> str | None:
        i = self.cmb_puerto.current()
        return self.lista_puertos[i][0] if 0 <= i < len(self.lista_puertos) else None

    def _conectar(self):
        if self.monitor.abierto:
            self.trabajo(self.monitor.cerrar, lambda _: self._desconectado(), "Desconectando")
            return
        puerto = self._puerto_elegido()
        if not puerto:
            messagebox.showwarning(TITULO, "Elija el puerto del monitor.")
            return

        def conectar():
            self.monitor.abrir(puerto)
            try:
                return ("2", self.monitor.info())
            except ErrorMonitor:
                return ("1", self.monitor.info_antigua())

        self.trabajo(conectar, self._conectado, f"Conectando a {puerto}")

    def _conectado(self, r):
        version, datos = r
        self.btn_conectar.config(text="Desconectar", style="TButton")
        if version == "1":
            self._chip("Firmware anterior a 2.0: instale el nuevo" if datos else "No responde como un Monitor T/H",
                       "aviso")
            self._estado((datos or "El equipo no respondió") + " · instálele el firmware en esta pestaña", "alerta")
            self.nb.select(3)
            return
        self._mostrar_info(datos)
        self._leer_todo()

    def _desconectado(self):
        self.btn_conectar.config(text="Conectar", style="Primario.TButton")
        self._chip("Sin conectar")

    def _leer_todo(self):
        def leer():
            info = self.monitor.info()
            equipo, cfg = self.monitor.config()
            vivos = self.monitor.sensores()
            return info, equipo, cfg, vivos

        self.trabajo(leer, self._mostrar_todo, "Leyendo el monitor")

    def _mostrar_todo(self, r):
        info, self.cfg_equipo, self.cfg_sensores, self.vivos = r
        self._mostrar_info(info)
        self.var_codigo.set(self.cfg_equipo.get("codigo", ""))
        self.var_pantalla.set(self.cfg_equipo.get("pantalla", 1))
        self.var_buz_t.set(bool(self.cfg_equipo.get("buzzer_temp")))
        self.var_buz_h.set(bool(self.cfg_equipo.get("buzzer_hum")))
        self._llenar_tabla()

    def _valor(self, clave: str, texto: str, tipo: str = "normal"):
        color = {"ok": C["verde"], "alerta": C["rojo"], "aviso": C["ambar"], "tenue": C["tenue"]}.get(tipo, "")
        self.campos_info[clave].config(text=texto, foreground=color or C["texto"])

    def _mostrar_info(self, i: dict):
        self.info = i
        self._chip(f"{i['codigo']}  ·  serie {i['serie']}  ·  firmware {i['firmware']}", "ok")
        self._valor("codigo", i["codigo"])
        self._valor("serie", i["serie"])
        self._valor("firmware", i["firmware"])
        self._valor("pantalla", '2,4"  (240 × 320)' if i["pantalla"] == 2 else '1,9"  (170 × 320)')
        if i["hora_valida"]:
            dif = int(i["unix"] - time.time())
            self._valor("hora", f"{i['hora']}   (diferencia con el PC: {dif:+d} s)",
                        "alerta" if abs(dif) > 120 else "normal")
        else:
            self._valor("hora", "SIN HORA: pulse «Poner la hora del PC» (sin hora no se graban datos)", "alerta")
        if i["sd"]:
            self._valor("sd", "Grabando", "ok")
        else:
            self._valor("sd", f"NO DISPONIBLE ({i['pendientes']} filas esperando en la memoria)", "alerta")
        texto, tipo = {"sin_divisor": ("No detecta cortes de luz (divisor no conectado)", "tenue"),
                       "red": ("Con red eléctrica", "ok"),
                       "bateria": ("SIN LUZ: funcionando con batería", "alerta")}.get(i["energia"],
                                                                                     (i["energia"], "normal"))
        self._valor("energia", f"{texto}   ({i['energia_mv']} mV)", tipo)
        self._valor("sensores", str(i["sensores"]))
        if i["emparejando"]:
            self._valor("emparejando", f"Red abierta {i['emparejando']} s más", "aviso")
        else:
            self._valor("emparejando", "Red cerrada", "tenue")

    def _llenar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())
        cfg = {s["ieee4"]: s for s in self.cfg_sensores}
        vistos = set()
        for v in self.vivos:
            c = cfg.get(v["ieee4"])
            vistos.add(v["ieee4"])
            edad = v["edad"]
            edad_txt = "—" if edad < 0 else f"hace {edad // 60} min" if edad >= 60 else "ahora"
            fila = (v["n"], v["ieee4"], v["nombre"], AREAS.get(c["perfil"], "") if c else "Medicamentos (defecto)",
                    "—" if v["t"] is None else f"{v['t']:.1f}", "—" if v["h"] is None else f"{v['h']:.0f}",
                    "—" if v["bat"] is None else f"{v['bat']} %", edad_txt,
                    f"T {c['corr_t']:+.1f} / HR {c['corr_h']:+d}" if c else "—",
                    (c["calibrado"] or "—") if c else "—",
                    "Configurado" if c else "Sin configurar")
            self._fila_tabla(fila, v["ieee4"], "alarma" if v["alarma"] else None)
        for s in self.cfg_sensores:
            if s["ieee4"] in vistos:
                continue
            fila = ("", s["ieee4"], s["nombre"], AREAS.get(s["perfil"], ""), "—", "—", "—", "—",
                    f"T {s['corr_t']:+.1f} / HR {s['corr_h']:+d}", s["calibrado"] or "—",
                    "OCULTO" if s["oculto"] else "No emparejado")
            self._fila_tabla(fila, s["ieee4"], "oculto")

    def _fila_tabla(self, fila, iid, marca=None):
        tags = [] if len(self.tabla.get_children()) % 2 == 0 else ["zebra"]
        if marca:
            tags.append(marca)
        self.tabla.insert("", "end", iid=iid, values=fila, tags=tags)

    # ---------- acciones del equipo ----------
    def _requiere_conexion(self) -> bool:
        if not self.monitor.abierto or not self.info:
            messagebox.showwarning(TITULO, "Primero conecte un monitor con firmware 2.0 o posterior.")
            return False
        return True

    def _poner_hora(self):
        if self._requiere_conexion():
            self.trabajo(self.monitor.poner_hora, lambda _: self._leer_todo(), "Poniendo la hora")

    def _emparejar(self):
        if self._requiere_conexion():
            self.trabajo(self.monitor.emparejar, lambda _: (messagebox.showinfo(
                TITULO, "Red abierta por 3 minutos. Mantenga el botón del sensor ~5 s hasta que parpadee y "
                        "luego pulse Actualizar en la pestaña Sensores."), self._leer_todo()), "Abriendo la red")

    def _reiniciar(self):
        if self._requiere_conexion() and messagebox.askyesno(
                TITULO, "¿Reiniciar el monitor? Después conviene pulsar el botón de cada sensor."):
            self.trabajo(self._reiniciar_y_reconectar, lambda _: self._leer_todo(), "Reiniciando el monitor")

    def _reiniciar_y_reconectar(self, cmd=None):
        if cmd:
            cmd()
        else:
            self.monitor.reiniciar()
        puerto = self.monitor.puerto
        self.monitor.cerrar()
        time.sleep(6)
        for _ in range(20):
            try:
                self.monitor.abrir(puerto)
                self.monitor.info()
                return
            except Exception:
                self.monitor.cerrar()
                time.sleep(1)
        raise ErrorMonitor("El monitor no volvió después de reiniciar. Pulse Conectar de nuevo.")

    def _guardar_equipo(self):
        if not self._requiere_conexion():
            return
        codigo = texto_monitor(self.var_codigo.get(), 15)
        if not codigo:
            messagebox.showwarning(TITULO, "Escriba el código del equipo (por ejemplo MTH-03).")
            return
        pantalla, bt, bh = self.var_pantalla.get(), self.var_buz_t.get(), self.var_buz_h.get()
        cambia_pantalla = pantalla != self.cfg_equipo.get("pantalla")
        if cambia_pantalla and not messagebox.askyesno(
                TITULO, "Cambió el modelo de pantalla: el monitor se reiniciará. ¿Continuar?"):
            return

        def guardar():
            if cambia_pantalla:
                self._reiniciar_y_reconectar(lambda: self.monitor.poner_equipo(codigo, pantalla, bt, bh))
            else:
                self.monitor.poner_equipo(codigo, pantalla, bt, bh)

        self.trabajo(guardar, lambda _: (messagebox.showinfo(TITULO, "Configuración guardada."), self._leer_todo()),
                     "Guardando la configuración")

    # ---------- sensores ----------
    def _sensor_elegido(self) -> str | None:
        sel = self.tabla.selection()
        if not sel:
            messagebox.showinfo(TITULO, "Elija un sensor de la lista.")
            return None
        return sel[0]

    def _editar_sensor(self):
        if not self._requiere_conexion():
            return
        ieee4 = self._sensor_elegido()
        if not ieee4:
            return
        actual = next((s for s in self.cfg_sensores if s["ieee4"] == ieee4), None)
        vivo = next((v for v in self.vivos if v["ieee4"] == ieee4), None)
        datos = actual or {"ieee4": ieee4, "nombre": vivo["nombre"] if vivo else "", "perfil": "MED",
                           "corr_t": 0.0, "corr_h": 0, "calibrado": "", "oculto": 0}
        DialogoSensor(self, datos, self._guardar_sensor)

    def _guardar_sensor(self, s: dict):
        self.trabajo(lambda: self.monitor.poner_sensor(s), lambda _: self._leer_todo(), "Guardando el sensor")

    def _borrar_sensor(self):
        if not self._requiere_conexion():
            return
        ieee4 = self._sensor_elegido()
        if not ieee4:
            return
        if not any(s["ieee4"] == ieee4 for s in self.cfg_sensores):
            messagebox.showinfo(TITULO, "Ese sensor no tiene configuración.")
            return
        if messagebox.askyesno(TITULO, f"¿Quitar la configuración del sensor {ieee4}? Vuelve a nombre y área por "
                                       f"defecto y SIN corrección de calibración."):
            self.trabajo(lambda: self.monitor.borrar_sensor(ieee4), lambda _: self._leer_todo(), "Quitando")

    # ---------- firmware ----------
    def _escribir_fw(self, texto):
        def agregar():
            self.txt_fw.configure(state="normal")
            self.txt_fw.insert("end", texto + "\n")
            self.txt_fw.see("end")
            self.txt_fw.configure(state="disabled")
        self.after(0, agregar)

    def _flashear(self):
        puerto = self.monitor.puerto if self.monitor.abierto else self._puerto_elegido()
        if not puerto:
            messagebox.showwarning(TITULO, "Elija el puerto del monitor.")
            return
        borrar = self.var_borrar.get()
        aviso = (f"Se instalará el firmware {version_firmware_incluido()} en {puerto}.\n\n"
                 "IMPORTANTE: si el monitor está alimentado por el módulo UPS, desconecte antes la salida OUT+.\n\n")
        if borrar:
            aviso += ("SE BORRARÁ TODA LA MEMORIA: clave de firma, sensores emparejados, red Zigbee y configuración. "
                      "Los registros firmados anteriores ya no se podrán verificar con la clave nueva.\n\n")
        if not messagebox.askyesno(TITULO, aviso + "¿Continuar?", icon="warning"):
            return
        if borrar and not messagebox.askyesno(TITULO, "¿Seguro que quiere BORRAR TODO? Esto no se puede deshacer.",
                                              icon="warning"):
            return

        def instalar():
            self.monitor.cerrar()
            self._escribir_fw(f"--- Instalando en {puerto} ---")
            flashear(puerto, borrar, self._escribir_fw)
            self._escribir_fw("--- Firmware instalado. Esperando que el monitor arranque… ---")
            time.sleep(8)
            for _ in range(20):
                try:
                    self.monitor.abrir(puerto)
                    return self.monitor.info()
                except Exception:
                    self.monitor.cerrar()
                    time.sleep(1)
            return None

        def listo(info):
            self.btn_conectar.config(text="Desconectar" if self.monitor.abierto else "Conectar")
            if info:
                self._escribir_fw(f"Monitor {info['codigo']} con firmware {info['firmware']}.")
                messagebox.showinfo(TITULO, f"Firmware instalado: {info['codigo']}, versión {info['firmware']}.\n\n"
                                            "Pulse el botón de cada sensor para que se reconecten de inmediato.")
                self._mostrar_info(info)
                self._leer_todo()
            else:
                messagebox.showwarning(TITULO, "Se instaló, pero el monitor no respondió después. Pulse Conectar.")

        self.trabajo(instalar, listo, "Instalando el firmware")

    # ---------- registro y archivos ----------
    def _ver_eventos(self):
        if not self._requiere_conexion():
            return

        def mostrar(eventos):
            self.txt_eventos.configure(state="normal")
            self.txt_eventos.delete("1.0", "end")
            self.txt_eventos.insert("end", "\n".join(eventos) or "(sin eventos)")
            self.txt_eventos.configure(state="disabled")

        self.trabajo(self.monitor.eventos, mostrar, "Leyendo eventos")

    def _guardar_archivo(self):
        if not self._requiere_conexion():
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar configuración", defaultextension=".json", filetypes=[("Configuración", "*.json")],
            initialfile=f"config_{self.info.get('codigo', 'monitor')}_{time.strftime('%Y-%m-%d')}.json")
        if not ruta:
            return

        def guardar(r):
            equipo, sensores = r
            datos = {"guardado": time.strftime("%Y-%m-%d %H:%M:%S"), "serie": self.info.get("serie"),
                     "firmware": self.info.get("firmware"), "equipo": equipo, "sensores": sensores}
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            messagebox.showinfo(TITULO, f"Configuración guardada en:\n{ruta}")

        self.trabajo(self.monitor.config, guardar, "Leyendo la configuración")

    def _cargar_archivo(self):
        if not self._requiere_conexion():
            return
        ruta = filedialog.askopenfilename(title="Cargar configuración", filetypes=[("Configuración", "*.json")])
        if not ruta:
            return
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = json.load(f)
            equipo, sensores = datos["equipo"], datos["sensores"]
        except (OSError, ValueError, KeyError) as e:
            messagebox.showerror(TITULO, f"El archivo no es una configuración válida: {e}")
            return
        aviso = (f"Se aplicará al monitor conectado ({self.info.get('codigo')}) la configuración de "
                 f"{equipo.get('codigo')} con {len(sensores)} sensores.")
        if datos.get("serie") and datos["serie"] != self.info.get("serie"):
            aviso += ("\n\nOJO: el archivo es de OTRA placa (serie " + datos["serie"] + "). Las correcciones de "
                      "calibración son de cada sensor: revise que correspondan.")
        if not messagebox.askyesno(TITULO, aviso + "\n\n¿Continuar?"):
            return
        cambia_pantalla = equipo.get("pantalla") != self.cfg_equipo.get("pantalla")

        def aplicar():
            for s in sensores:
                self.monitor.poner_sensor(s)
            poner = lambda: self.monitor.poner_equipo(equipo["codigo"], equipo["pantalla"], equipo["buzzer_temp"],
                                                      equipo["buzzer_hum"])
            if cambia_pantalla:
                self._reiniciar_y_reconectar(poner)
            else:
                poner()

        self.trabajo(aplicar, lambda _: (messagebox.showinfo(TITULO, "Configuración aplicada."), self._leer_todo()),
                     "Aplicando la configuración")

    def _exportar_clave(self):
        if not self._requiere_conexion():
            return
        if not messagebox.askyesno(TITULO, (
                "La clave de firma permite verificar que los registros de la SD no fueron alterados "
                "(verificar_registro.py). Quien la tenga podría falsificar registros: guárdela en un lugar "
                "seguro. La exportación queda registrada en los eventos del monitor.\n\n¿Exportar?")):
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar clave de firma", defaultextension=".txt",
            initialfile=f"clave_{self.info.get('codigo')}_{self.info.get('serie')}.txt")
        if not ruta:
            return

        def guardar(clave):
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(f"Equipo {self.info.get('codigo')}  serie {self.info.get('serie')}\n{clave}\n")
            messagebox.showinfo(TITULO, f"Clave guardada en:\n{ruta}")

        self.trabajo(self.monitor.clave, guardar, "Leyendo la clave")


class DialogoSensor(tk.Toplevel):
    def __init__(self, padre, datos: dict, al_guardar):
        super().__init__(padre)
        self.title(f"Sensor {datos['ieee4']}")
        self.resizable(False, False)
        self.transient(padre)
        self.configure(bg=C["fondo"])
        try:
            self.iconbitmap(recurso("icono.ico"))
        except tk.TclError:
            pass
        self.al_guardar = al_guardar
        self.ieee4 = datos["ieee4"]
        f = ttk.Frame(self, padding=px(E4))
        f.pack(fill="both", expand=True)
        ttk.Label(f, text=f"Sensor {datos['ieee4']}", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(f, text="Los cambios se guardan en el monitor y quedan en sus eventos.",
                  style="Tenue.TLabel").pack(anchor="w", pady=(px(E1), px(E3)))

        self.var_nombre = tk.StringVar(value=datos["nombre"])
        self.var_area = tk.StringVar(value=AREAS.get(datos["perfil"], "Medicamentos"))
        self.var_ct = tk.StringVar(value=f"{datos['corr_t']:.1f}".replace(".", ","))
        self.var_ch = tk.StringVar(value=str(datos["corr_h"]))
        self.var_cal = tk.StringVar(value=datos["calibrado"])
        self.var_oculto = tk.BooleanVar(value=bool(datos["oculto"]))

        marco, c = padre._tarjeta(f, "Identificación")
        marco.pack(fill="x")
        padre._fila_form(c, 0, "Nombre en pantalla", ttk.Entry(c, textvariable=self.var_nombre, width=32),
                         "Máx. 30, sin tildes")
        padre._fila_form(c, 1, "Área", ttk.Combobox(c, textvariable=self.var_area, values=list(AREAS.values()),
                                                    state="readonly", width=20))
        oc = ttk.Checkbutton(c, text="Oculto (fuera de servicio: el monitor lo ignora)", variable=self.var_oculto,
                             style="Tarjeta.TCheckbutton")
        padre._fila_form(c, 2, "Estado", oc)

        marco, c = padre._tarjeta(f, "Calibración")
        marco.pack(fill="x", pady=(px(E3), 0))
        padre._fila_form(c, 0, "Corrección de temperatura", ttk.Entry(c, textvariable=self.var_ct, width=8), "°C")
        padre._fila_form(c, 1, "Corrección de humedad", ttk.Entry(c, textvariable=self.var_ch, width=8),
                         "% HR, entero")
        padre._fila_form(c, 2, "Fecha y nota", ttk.Entry(c, textvariable=self.var_cal, width=26),
                         "Ej.: 2026-10-08 (solo T)")
        padre._nota(f, "La corrección se SUMA a lo que mide el sensor: es el promedio de (referencia − sensor) del "
                       "formulario de calibración (Anexo 1). Límites: ±3 °C y ±15 % HR.").pack(fill="x",
                                                                                         pady=(px(E3), 0))
        b = ttk.Frame(f)
        b.pack(fill="x", pady=(px(E3), 0))
        ttk.Button(b, text="Guardar en el monitor", command=self._guardar, style="Primario.TButton",
                   cursor="hand2").pack(side="right")
        ttk.Button(b, text="Cancelar", command=self.destroy, cursor="hand2").pack(side="right", padx=(0, px(E2)))
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._guardar())
        self.update_idletasks()
        x = padre.winfo_rootx() + (padre.winfo_width() - self.winfo_width()) // 2
        y = padre.winfo_rooty() + (padre.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.grab_set()

    def _guardar(self):
        nombre = texto_monitor(self.var_nombre.get(), 30)
        try:
            ct = float(self.var_ct.get().replace(",", "."))
            ch = int(float(self.var_ch.get().replace(",", ".")))
        except ValueError:
            messagebox.showerror(TITULO, "Las correcciones deben ser números (por ejemplo 0,2).", parent=self)
            return
        if abs(ct) > CORR_MAX_T or abs(ch) > CORR_MAX_H:
            messagebox.showerror(TITULO, "Corrección fuera del límite (±3 °C / ±15 % HR). Según el instructivo, "
                                         "un sensor con una corrección así debe reemplazarse.", parent=self)
            return
        self.al_guardar({"ieee4": self.ieee4, "nombre": nombre, "perfil": AREAS_INV[self.var_area.get()],
                         "corr_t": round(ct, 1), "corr_h": ch, "calibrado": texto_monitor(self.var_cal.get(), 23),
                         "oculto": int(self.var_oculto.get())})
        self.destroy()


if __name__ == "__main__":
    Aplicacion().mainloop()
