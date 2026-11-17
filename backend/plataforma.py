"""Plataforma de módulos del ecosistema de la red: lo que todo módulo usa y debe cumplir.

Un módulo es una carpeta `modulos/<clave>/` con:
  __init__.py            exporta MANIFIESTO y router (y, opcional, exportar_titular / depurar)
  migraciones/NNN_*.sql  tablas de su esquema propio en PostgreSQL (m_<clave>)
  frontend/index.html    su página, servida en /m/<clave>/

El portal descubre los módulos al arrancar, valida el manifiesto, aplica las migraciones, los registra
en la tabla `modulos` (ficha de tratamiento incluida) y monta su API en /api/m/<clave>/.
Las reglas completas están en docs/MODULOS.md.
"""
from __future__ import annotations

import importlib
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, Request
from html import escape

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import config as cfg
from db import ahora, aplicar_migraciones, auditar, bd
from establecimiento import textos
from logo_modulo import FAMILIAS, problemas_nombre, slug, verificar as verificar_logo

CLAVE_VALIDA = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")
ACCION_VALIDA = re.compile(r"[a-z][a-z0-9_]{2,60}")
# RUT con o sin puntos (12.345.678-5, 12345678-5): no debe llegar nunca al detalle de la bitácora.
_PARECE_RUT = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b")


# ------------------------------------------------------------------ manifiesto
@dataclass(frozen=True)
class FichaTratamiento:
    """Ley 21.719: qué datos personales usa el módulo, de quién, para qué y por cuánto tiempo."""
    finalidad: str                      # para qué (mín. 10 caracteres, lenguaje simple)
    categorias_datos: str               # p. ej. "identificación del paciente, signos vitales"
    titulares: str                      # de quién: "funcionarios", "pacientes hospitalizados", ...
    base_licitud: str                   # p. ej. "funciones legales del hospital (art. 20 Ley 21.719)"
    conservacion: str                   # p. ej. "5 años desde el egreso" (lo aplica depurar())
    datos_sensibles: bool = False       # datos de salud u otros sensibles: exige EIPD aprobada por el DPD
    destinatarios: str = "Ninguno fuera del hospital"


@dataclass(frozen=True)
class Manifiesto:
    clave: str                          # igual al nombre de la carpeta: minúsculas, números y _
    nombre: str                         # como aparece en el menú de puntos (máx. 60)
    descripcion: str                    # una línea (máx. 200)
    version: str                        # semver: 0.1.0
    responsable: str                    # unidad dueña del módulo
    tratamiento: FichaTratamiento
    # Ícono según docs/diseno/: familia de color (1 a 5) y archivo en frontend/img/modulos/.
    familia: int = 0                    # 1 Atención y acceso · 2 Clínica · 3 Calidad y seguridad · 4 Operaciones y equipos · 5 Personas y gestión
    logo: str = ""                      # nombre del archivo sin .svg; por defecto, el nombre del módulo en minúsculas y con guiones
    orden: int = 100
    # Perfiles que lo ven en el menú la PRIMERA vez que se registra. Después lo administra el panel.
    perfiles_iniciales: tuple[str, ...] = ()
    # Permisos internos: {"<clave>.<accion>": "Descripción"}; y cuáles trae cada perfil.
    permisos: dict[str, str] = field(default_factory=dict)
    permisos_por_perfil: dict[str, tuple[str, ...]] = field(default_factory=dict)
    # Etiquetas legibles de las acciones que el módulo deja en la bitácora (se ven en Mi cuenta).
    acciones: dict[str, str] = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"/m/{self.clave}/"

    @property
    def archivo_logo(self) -> str:
        return self.logo or slug(self.nombre)

    @property
    def icono(self) -> str:
        return f"/static/img/modulos/{self.archivo_logo}.svg"

    @property
    def color(self) -> str:
        return FAMILIAS[self.familia][1] if self.familia in FAMILIAS else "#1565c0"


@dataclass
class ModuloCargado:
    manifiesto: Manifiesto
    carpeta: Path
    paquete: object
    exportar_titular: Callable[[int], dict] | None = None
    depurar: Callable[[], int] | None = None


REGISTRO: dict[str, ModuloCargado] = {}
_SESION_LISTA = None  # la entrega app.py al cargar los módulos (evita importar app desde aquí)


def _sesion_base(request: Request):
    if _SESION_LISTA is None:
        raise HTTPException(503, "Los módulos aún no están disponibles.")
    return _SESION_LISTA(request)


def _validar(m: Manifiesto, carpeta: Path) -> list[str]:
    errores = []
    if m.clave != carpeta.name or not CLAVE_VALIDA.fullmatch(m.clave) or len(m.clave) > 40:
        errores.append("la clave debe ser igual al nombre de la carpeta (minúsculas, números y _).")
    if not (2 <= len(m.nombre) <= 60):
        errores.append("el nombre debe tener entre 2 y 60 caracteres.")
    if len(m.descripcion) > 200:
        errores.append("la descripción no puede pasar de 200 caracteres.")
    if not re.fullmatch(r"\d+\.\d+\.\d+", m.version):
        errores.append("la versión debe ser semver (0.1.0).")
    # Directrices de logos de módulos (docs/diseno/)
    if m.familia not in FAMILIAS:
        errores.append("falta 'familia' (1 a 5) según las directrices de logos de módulos.")
    else:
        errores += [f"logo: {e}" for e in verificar_logo(m.archivo_logo, m.familia) if not e.startswith("faltan archivos")]
    errores += [f"nombre: {e}" for e in problemas_nombre(m.nombre)]
    t = m.tratamiento
    for nombre, valor, minimo in (("finalidad", t.finalidad, 10), ("categorias_datos", t.categorias_datos, 3),
                                  ("titulares", t.titulares, 3), ("base_licitud", t.base_licitud, 5),
                                  ("conservacion", t.conservacion, 3), ("responsable", m.responsable, 3)):
        if len((valor or "").strip()) < minimo:
            errores.append(f"falta '{nombre}' en el manifiesto (ficha de tratamiento).")
    roles = set(cfg.ROLES)
    if any(r not in roles for r in m.perfiles_iniciales) or any(r not in roles for r in m.permisos_por_perfil):
        errores.append(f"perfil desconocido; los válidos son {sorted(roles)}.")
    for p in m.permisos:
        if not p.startswith(m.clave + "."):
            errores.append(f"el permiso '{p}' debe empezar con '{m.clave}.'.")
    for perfil, ps in m.permisos_por_perfil.items():
        for p in ps:
            if p not in m.permisos:
                errores.append(f"el perfil '{perfil}' trae el permiso '{p}', que no está declarado.")
    for a in m.acciones:
        if not a.startswith(m.clave + "_") or not ACCION_VALIDA.fullmatch(a):
            errores.append(f"la acción '{a}' debe empezar con '{m.clave}_' (minúsculas y _).")
    if not (carpeta / "frontend" / "index.html").exists():
        errores.append("falta frontend/index.html.")
    return errores


# ------------------------------------------------------------------ base de datos del módulo
def esquema_de(clave: str) -> str:
    return f"m_{clave}"


def rol_de(clave: str) -> str:
    return f"{cfg.ESTABLECIMIENTO}_m_{clave}"


_ROLES_ACTIVOS: dict[str, str | None] = {}


def _preparar_rol(clave: str) -> str | None:
    """Cada módulo trabaja con un rol propio, dueño solo de su esquema: aunque tenga un error,
    no puede leer ni modificar las tablas del portal ni las de otro módulo.
    Si el usuario de la base no puede crear roles, se avisa y se sigue sin aislamiento (solo desarrollo)."""
    if not cfg.ROLES_POR_MODULO:
        return None
    rol = rol_de(clave)
    try:
        with bd() as c:
            if not c.execute("SELECT 1 FROM pg_roles WHERE rolname=?", (rol,)).fetchone():
                c.execute(f'CREATE ROLE "{rol}" NOLOGIN')
            c.execute(f'GRANT "{rol}" TO CURRENT_USER')
        return rol
    except Exception as e:  # noqa: BLE001
        print(f"[módulos] '{clave}': sin rol propio ({type(e).__name__}: {e}). "
              "En producción el usuario de la base debe tener CREATEROLE.", file=sys.stderr)
        return None


@contextmanager
def bd_modulo(clave: str):
    """Conexión al esquema del módulo (m_<clave>) con su rol. Confirma al salir sin error; si hay excepción, revierte."""
    with bd(esquema=esquema_de(clave), rol=_ROLES_ACTIVOS.get(clave)) as c:
        yield c


def migrar(clave: str, carpeta: Path) -> list[str]:
    """Crea el esquema y el rol del módulo y aplica sus migraciones pendientes (ver db.aplicar_migraciones)."""
    _ROLES_ACTIVOS[clave] = _preparar_rol(clave)
    return aplicar_migraciones(esquema_de(clave), carpeta / "migraciones", _ROLES_ACTIVOS[clave])


# ------------------------------------------------------------------ registro en el portal
CAMPOS_DE_CODIGO = ("nombre", "descripcion", "url", "icono", "color", "finalidad", "categorias_datos",
                    "datos_sensibles", "responsable")


def _ficha_texto(m: Manifiesto) -> str:
    t = m.tratamiento
    return (f"{t.categorias_datos} · Titulares: {t.titulares} · Base: {t.base_licitud} · "
            f"Conservación: {t.conservacion} · Destinatarios: {t.destinatarios}")


def _registrar(m: Manifiesto):
    """Crea o actualiza la fila del módulo. El código manda en la ficha; el panel manda en quién lo ve,
    si está activo y en la aprobación de la EIPD. Si la ficha cambia, la EIPD vuelve a quedar pendiente."""
    campos = {
        "nombre": m.nombre, "descripcion": m.descripcion, "url": m.url, "icono": m.icono, "color": m.color,
        "finalidad": m.tratamiento.finalidad.strip(), "categorias_datos": _ficha_texto(m),
        "datos_sensibles": int(m.tratamiento.datos_sensibles), "responsable": m.responsable,
    }
    with bd() as c:
        previo = c.execute("SELECT * FROM modulos WHERE clave=?", (m.clave,)).fetchone()
        if not previo:
            # Se registra inactivo: un administrador lo publica desde el panel cuando esté listo.
            cols = {**campos, "clave": m.clave, "orden": m.orden, "activo": 0, "origen": "codigo", "version": m.version}
            mid = c.execute(f"INSERT INTO modulos ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                            tuple(cols.values())).lastrowid
            c.executemany("INSERT INTO modulos_rol VALUES (?,?)", [(mid, r) for r in set(m.perfiles_iniciales)])
            evento = ("modulo_registrado", f"{m.clave} v{m.version} (inactivo hasta publicarlo)")
        else:
            ficha_cambio = any(str(previo[k]) != str(campos[k]) for k in ("finalidad", "categorias_datos", "datos_sensibles"))
            cambios = [k for k in CAMPOS_DE_CODIGO if str(previo[k]) != str(campos[k])]
            if not cambios and previo["version"] == m.version and previo["origen"] == "codigo":
                return
            extra = {"eipd_aprobada": 0} if ficha_cambio and m.tratamiento.datos_sensibles else {}
            todo = {**campos, **extra, "origen": "codigo", "version": m.version}
            c.execute(f"UPDATE modulos SET {', '.join(f'{k}=?' for k in todo)} WHERE id=?", (*todo.values(), previo["id"]))
            evento = ("modulo_actualizado", f"{m.clave} v{previo['version'] or '?'} → v{m.version}"
                      + (" · ficha de tratamiento modificada" if ficha_cambio else "")
                      + (" · EIPD vuelve a pendiente" if extra else ""))
    auditar(evento[0], None, evento[1])


# ------------------------------------------------------------------ páginas con los datos del establecimiento
_CACHE_HTML: dict[Path, str] = {}


def pagina_html(ruta: Path) -> HTMLResponse:
    """Sirve una página reemplazando {{producto}}, {{institucion}}, {{unidad}} y {{unidad_detalle}}."""
    if ruta not in _CACHE_HTML:
        html = ruta.read_text(encoding="utf-8")
        for k, v in textos().items():
            html = html.replace("{{" + k + "}}", escape(v))
        _CACHE_HTML[ruta] = html
    return HTMLResponse(_CACHE_HTML[ruta], headers={"Cache-Control": "no-store"})


# ------------------------------------------------------------------ carga
def cargar_modulos(app: FastAPI | None = None, sesion_lista=None, etiquetas: dict | None = None) -> dict[str, ModuloCargado]:
    """Descubre, valida, migra, registra y monta cada módulo de modulos/. Un módulo con errores
    no se monta (y se informa en consola), pero no impide que arranque el portal.
    Sin `app` (consola: gestionar.py) solo valida, migra y registra."""
    global _SESION_LISTA
    if sesion_lista is not None:
        _SESION_LISTA = sesion_lista
    raiz = cfg.MODULOS_DIR
    if not raiz.exists():
        return REGISTRO
    if str(raiz.parent) not in sys.path:
        sys.path.insert(0, str(raiz.parent))
    for carpeta in sorted(p for p in raiz.iterdir() if p.is_dir() and (p / "__init__.py").exists()):
        if carpeta.name.startswith("_"):
            continue  # plantillas y borradores
        try:
            paquete = importlib.import_module(f"{raiz.name}.{carpeta.name}")
            m: Manifiesto = getattr(paquete, "MANIFIESTO")
            errores = _validar(m, carpeta)
            if errores:
                raise RuntimeError("; ".join(errores))
            migrar(m.clave, carpeta)
            _registrar(m)
        except Exception as e:  # noqa: BLE001
            print(f"[módulos] '{carpeta.name}' NO se cargó: {e}", file=sys.stderr)
            continue
        cargado = ModuloCargado(m, carpeta, paquete, getattr(paquete, "exportar_titular", None),
                                getattr(paquete, "depurar", None))
        REGISTRO[m.clave] = cargado
        if etiquetas is not None:
            etiquetas.update(m.acciones)
        if app is None:
            continue
        router = getattr(paquete, "router", None)
        if router is not None:
            app.include_router(router, prefix=f"/api/m/{m.clave}", tags=[m.clave])
        _montar_paginas(app, cargado)
    return REGISTRO


def _montar_paginas(app: FastAPI, mod: ModuloCargado):
    clave, front = mod.manifiesto.clave, mod.carpeta / "frontend"

    def pagina(request: Request):
        if not request.cookies.get(cfg.COOKIE_NOMBRE):
            return RedirectResponse("/ingresar")
        return pagina_html(front / "index.html")

    def pantalla(request: Request, ruta: str):
        # Cada pantalla tiene su dirección (/m/<clave>/<pantalla>[/<id>]); el navegador decide qué pintar.
        if not re.fullmatch(r"[a-z0-9-]+(/[A-Za-z0-9-]+)*", ruta):
            return RedirectResponse(f"/m/{clave}/")
        return pagina(request)

    app.add_api_route(f"/m/{clave}/", pagina, methods=["GET"], include_in_schema=False)
    app.add_api_route(f"/m/{clave}", lambda: RedirectResponse(f"/m/{clave}/"), methods=["GET"], include_in_schema=False)
    app.mount(f"/m/{clave}/static", StaticFiles(directory=front), name=f"m-{clave}")  # antes que las pantallas
    app.add_api_route(f"/m/{clave}/{{ruta:path}}", pantalla, methods=["GET"], include_in_schema=False)


# ------------------------------------------------------------------ acceso y permisos
class ContextoModulo:
    """Lo que recibe cada endpoint de un módulo: la persona, su sesión y sus permisos en el módulo."""

    def __init__(self, base, clave: str, permisos: set[str]):
        self.u, self.s, self.ip = base.u, base.s, base.ip
        self.clave, self.permisos = clave, permisos

    @property
    def usuario_id(self) -> int:
        return self.u["id"]

    def puede(self, permiso: str) -> bool:
        return permiso in self.permisos

    def auditar(self, accion: str, detalle: str | None = None):
        auditar_modulo(self.clave, accion, self.usuario_id, detalle, self.ip)


def permisos_de(clave: str, usuario) -> set[str]:
    m = REGISTRO[clave].manifiesto
    propios = set(m.permisos_por_perfil.get(usuario["rol"], ()))
    with bd() as c:
        propios |= {f["permiso"] for f in c.execute(
            "SELECT permiso FROM permisos_usuario WHERE usuario_id=? AND permiso LIKE ?", (usuario["id"], clave + ".%"))}
    return propios & set(m.permisos)


def puede_ver(clave: str, usuario) -> bool:
    """Mismas reglas que el menú de puntos: activo, habilitado para el perfil o la persona, y con EIPD si es sensible."""
    with bd() as c:
        return c.execute(
            """SELECT 1 FROM modulos m
               LEFT JOIN modulos_rol r ON r.modulo_id=m.id AND r.rol=?
               LEFT JOIN modulos_usuario mu ON mu.modulo_id=m.id AND mu.usuario_id=?
               WHERE m.clave=? AND m.activo=1 AND (r.rol IS NOT NULL OR mu.usuario_id IS NOT NULL)
                 AND (m.datos_sensibles=0 OR m.eipd_aprobada=1)""",
            (usuario["rol"], usuario["id"], clave)).fetchone() is not None


def acceso(clave: str, permiso: str | None = None):
    """Dependencia FastAPI para TODOS los endpoints de un módulo:

        @router.get("/notas")
        def listar(ctx: ContextoModulo = Depends(acceso("ejemplo", "ejemplo.ver"))): ...
    """
    def dep(base=Depends(_sesion_base)) -> ContextoModulo:
        if clave not in REGISTRO or not puede_ver(clave, base.u):
            raise HTTPException(403, "No tienes acceso a este módulo o está suspendido.")
        permisos = permisos_de(clave, base.u)
        if permiso and permiso not in permisos:
            raise HTTPException(403, "Tu perfil no tiene permiso para esta acción.")
        return ContextoModulo(base, clave, permisos)
    return dep


def nombres_de(ids) -> dict[int, str]:
    """Nombres de funcionarios por id, para mostrar autores sin copiar datos del portal al módulo."""
    ids = [int(i) for i in set(ids) if i is not None]
    if not ids:
        return {}
    with bd() as c:
        return {f["id"]: f["nombre"] for f in c.execute(
            f"SELECT id, nombre FROM usuarios WHERE id IN ({','.join('?' * len(ids))})", ids)}


# ------------------------------------------------------------------ bitácora
def auditar_modulo(clave: str, accion: str, usuario_id: int | None, detalle: str | None = None, ip: str | None = None):
    """Registra en la bitácora central encadenada. La acción debe estar declarada en el manifiesto y
    el detalle no puede contener RUT ni datos clínicos: se registra QUÉ se hizo y sobre qué id, no el contenido."""
    m = REGISTRO[clave].manifiesto if clave in REGISTRO else None
    if m is None or accion not in m.acciones:
        raise ValueError(f"Acción de bitácora no declarada en el manifiesto de '{clave}': {accion}")
    if detalle and _PARECE_RUT.search(detalle):
        raise ValueError("El detalle de la bitácora no puede incluir un RUT. Registra el id interno.")
    auditar(accion, usuario_id, (detalle or "")[:300] or None, ip)


# ------------------------------------------------------------------ Ley 21.719: titulares y conservación
def exportar_titular(usuario_id: int) -> dict:
    """Junta lo que cada módulo guarda de la persona (derecho de acceso y portabilidad)."""
    salida = {}
    for clave, mod in REGISTRO.items():
        if mod.exportar_titular:
            try:
                salida[clave] = {"modulo": mod.manifiesto.nombre, "datos": mod.exportar_titular(usuario_id)}
            except Exception as e:  # noqa: BLE001
                salida[clave] = {"modulo": mod.manifiesto.nombre, "error": f"no se pudo exportar ({type(e).__name__})"}
    return salida


def depurar_todos() -> dict[str, int]:
    """Aplica el plazo de conservación de cada módulo (programar a diario junto con el respaldo)."""
    resultado = {}
    for clave, mod in REGISTRO.items():
        if mod.depurar:
            n = mod.depurar()
            resultado[clave] = n
            if n:
                auditar("modulo_depurado", None, f"{clave}: {n} registros eliminados por plazo de conservación")
    return resultado


def fichas() -> list[dict]:
    """Registro de actividades de tratamiento de los módulos (para el DPD)."""
    out = []
    for clave, mod in REGISTRO.items():
        m, t = mod.manifiesto, mod.manifiesto.tratamiento
        out.append({"clave": clave, "nombre": m.nombre, "version": m.version, "responsable": m.responsable,
                    "finalidad": t.finalidad, "categorias_datos": t.categorias_datos, "titulares": t.titulares,
                    "base_licitud": t.base_licitud, "conservacion": t.conservacion,
                    "datos_sensibles": t.datos_sensibles, "destinatarios": t.destinatarios,
                    "permisos": m.permisos, "permisos_por_perfil": {k: list(v) for k, v in m.permisos_por_perfil.items()}})
    return out
