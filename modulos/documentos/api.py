"""API de F+docs, montada en /api/m/documentos/. Todo endpoint usa Depends(acceso(...)).

- Ver, buscar y descargar: documentos.ver (todos los perfiles con el módulo habilitado).
- Carpetas, subir, reemplazar, eliminar y papelera: documentos.administrar (se otorga persona a persona).
- Solo PDF, hasta 25 MB. El archivo viaja en base64 dentro del JSON (así usa el api() común, con su cabecera anti-CSRF).
- Eliminar no borra: el documento va a la papelera. Reemplazar deja la versión anterior en la papelera.
  depurar() borra lo que lleva más de 30 días ahí.
"""
import base64
import binascii
import hashlib
import unicodedata
from urllib.parse import quote

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from plataforma import ContextoModulo, acceso, bd_modulo, nombres_de

from .manifiesto import CLAVE

router = APIRouter()
VER = f"{CLAVE}.ver"
ADMIN = f"{CLAVE}.administrar"
DIAS_PAPELERA = 30
MAX_BYTES = 25 * 1024 * 1024
MAX_BASE64 = (MAX_BYTES + 2) // 3 * 4
MAX_RESULTADOS = 50


# ------------------------------------------------------------------ modelos
class NuevaCarpeta(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    padre_id: int | None = None


class CambioCarpeta(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    padre_id: int | None = None
    mover: bool = False                       # True: padre_id es el destino (None = inicio)


class ArchivoPdf(BaseModel):
    nombre_archivo: str = Field(min_length=1, max_length=200)
    contenido: str = Field(min_length=8, max_length=MAX_BASE64)   # PDF en base64


class NuevoDocumento(ArchivoPdf):
    titulo: str = Field(min_length=3, max_length=150)
    descripcion: str = Field(default="", max_length=500)
    carpeta_id: int | None = None


class CambioDocumento(BaseModel):
    titulo: str = Field(min_length=3, max_length=150)
    descripcion: str = Field(default="", max_length=500)
    carpeta_id: int | None = None


# ------------------------------------------------------------------ apoyo
def _pdf(a: ArchivoPdf) -> tuple[bytes, str, str]:
    """Decodifica y valida el PDF. Devuelve (bytes, nombre de archivo, sha256)."""
    try:
        datos = base64.b64decode(a.contenido, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, "No pudimos leer el archivo. Vuelve a elegirlo.")
    if len(datos) > MAX_BYTES:
        raise HTTPException(413, "El archivo pesa más de 25 MB.")
    if b"%PDF-" not in datos[:1024]:
        raise HTTPException(422, "El archivo no es un PDF. Solo se pueden subir documentos PDF.")
    nombre = a.nombre_archivo.replace("\\", "/").rsplit("/", 1)[-1].strip() or "documento.pdf"
    return datos, nombre[:200], hashlib.sha256(datos).hexdigest()


def _norm(texto: str) -> str:
    """Minúsculas y sin tildes, para buscar «protocolo caidas» y encontrar «Protocolo de caídas»."""
    t = unicodedata.normalize("NFD", texto or "").lower()
    return "".join(ch for ch in t if unicodedata.category(ch) != "Mn")


def _carpetas(c) -> dict[int, dict]:
    return {f["id"]: dict(f) for f in c.execute("SELECT id, padre_id, nombre FROM carpetas")}


def _ruta(carpetas: dict[int, dict], cid: int | None) -> list[dict]:
    """Camino desde el inicio hasta la carpeta (para las migas de pan y los resultados de búsqueda)."""
    ruta, vistos = [], set()
    while cid and cid in carpetas and cid not in vistos:
        vistos.add(cid)
        ruta.insert(0, {"id": cid, "nombre": carpetas[cid]["nombre"]})
        cid = carpetas[cid]["padre_id"]
    return ruta


def _exigir_carpeta(c, cid: int | None):
    if cid is not None and not c.execute("SELECT 1 FROM carpetas WHERE id=?", (cid,)).fetchone():
        raise HTTPException(404, "La carpeta no existe. Recarga la página.")


def _documento_activo(c, did: int):
    d = c.execute("SELECT * FROM documentos WHERE id=? AND eliminado_en IS NULL", (did,)).fetchone()
    if not d:
        raise HTTPException(404, "El documento no existe o está en la papelera.")
    return d


def _nombre_repetido(c, padre_id: int | None, nombre: str, excepto: int = 0) -> bool:
    return bool(c.execute(
        "SELECT 1 FROM carpetas WHERE COALESCE(padre_id, 0)=? AND lower(btrim(nombre))=lower(btrim(?)) AND id<>?",
        (padre_id or 0, nombre, excepto)).fetchone())


def _fila_documento(f: dict, nombres: dict, carpetas: dict | None = None) -> dict:
    d = {"id": f["id"], "titulo": f["titulo"], "descripcion": f["descripcion"], "carpeta_id": f["carpeta_id"],
         "actualizado_en": f["actualizado_en"], "actualizado_por": nombres.get(f["actualizado_por"], "—"),
         "tamano": f["tamano"], "nombre_archivo": f["nombre_archivo"], "versiones_anteriores": f.get("anteriores", 0)}
    if carpetas is not None:
        d["ruta"] = _ruta(carpetas, f["carpeta_id"])
    return d


_SQL_DOCS = """SELECT d.id, d.titulo, d.descripcion, d.carpeta_id, d.actualizado_en, d.actualizado_por,
                      v.tamano, v.nombre_archivo,
                      (SELECT count(*) FROM versiones a WHERE a.documento_id=d.id AND a.reemplazada_en IS NOT NULL) AS anteriores
               FROM documentos d JOIN versiones v ON v.documento_id=d.id AND v.reemplazada_en IS NULL
               WHERE d.eliminado_en IS NULL"""


def _pdf_respuesta(contenido: bytes, titulo: str, descargar: bool) -> Response:
    nombre = f"{titulo.strip()[:120]}.pdf"
    sin_tildes = "".join(ch for ch in unicodedata.normalize("NFD", nombre) if unicodedata.category(ch) != "Mn")
    ascii_ = "".join(ch if 32 <= ord(ch) < 127 and ch not in '"\\;' else "_" for ch in sin_tildes)
    modo = "attachment" if descargar else "inline"
    return Response(bytes(contenido), media_type="application/pdf", headers={
        "Content-Disposition": f"{modo}; filename=\"{ascii_}\"; filename*=UTF-8''{quote(nombre)}"})


# ------------------------------------------------------------------ explorar
@router.get("/carpetas/{cid}")
def ver_carpeta(cid: int, ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """Contenido de una carpeta (cid=0: el inicio): migas de pan, subcarpetas y documentos vigentes."""
    carpeta_id = cid or None
    with bd_modulo(CLAVE) as c:
        carpetas = _carpetas(c)
        if carpeta_id and carpeta_id not in carpetas:
            raise HTTPException(404, "La carpeta no existe o fue eliminada.")
        cuenta = {f["carpeta_id"]: f["n"] for f in c.execute(
            "SELECT carpeta_id, count(*) AS n FROM documentos WHERE eliminado_en IS NULL GROUP BY carpeta_id")}
        docs = [dict(f) for f in c.execute(
            _SQL_DOCS + " AND d.carpeta_id IS NOT DISTINCT FROM ? ORDER BY lower(d.titulo)", (carpeta_id,))]
    hijas = sorted((f for f in carpetas.values() if f["padre_id"] == carpeta_id), key=lambda f: _norm(f["nombre"]))
    nombres = nombres_de({d["actualizado_por"] for d in docs})
    return {
        "carpeta": {"id": cid, "nombre": carpetas[carpeta_id]["nombre"] if carpeta_id else "Inicio",
                    "padre_id": carpetas[carpeta_id]["padre_id"] if carpeta_id else None},
        "ruta": _ruta(carpetas, carpeta_id),
        "subcarpetas": [{"id": f["id"], "nombre": f["nombre"], "documentos": cuenta.get(f["id"], 0),
                         "subcarpetas": sum(1 for g in carpetas.values() if g["padre_id"] == f["id"])} for f in hijas],
        "documentos": [_fila_documento(d, nombres) for d in docs],
    }


@router.get("/arbol")
def arbol(ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """Todas las carpetas con su ruta completa (para elegir destino al subir o mover)."""
    with bd_modulo(CLAVE) as c:
        carpetas = _carpetas(c)
    lista = [{"id": cid, "padre_id": f["padre_id"], "ruta": " › ".join(p["nombre"] for p in _ruta(carpetas, cid))}
             for cid, f in carpetas.items()]
    return sorted(lista, key=lambda f: _norm(f["ruta"]))


@router.get("/buscar")
def buscar(q: str = "", ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """Busca en título, descripción, nombre del archivo y carpetas. Todas las palabras deben aparecer."""
    palabras = _norm(q[:200]).split()
    if not palabras:
        return {"documentos": [], "carpetas": [], "total": 0}
    with bd_modulo(CLAVE) as c:
        carpetas = _carpetas(c)
        docs = [dict(f) for f in c.execute(_SQL_DOCS)]
    encontrados = []
    for d in docs:
        ruta = " ".join(p["nombre"] for p in _ruta(carpetas, d["carpeta_id"]))
        titulo = _norm(d["titulo"])
        texto = " ".join((titulo, _norm(d["descripcion"]), _norm(d["nombre_archivo"]), _norm(ruta)))
        if all(p in texto for p in palabras):
            en_titulo = sum(p in titulo for p in palabras)
            encontrados.append((-en_titulo, titulo, d))
    encontrados.sort(key=lambda t: (t[0], t[1]))
    elegidos = [d for _, _, d in encontrados[:MAX_RESULTADOS]]
    nombres = nombres_de({d["actualizado_por"] for d in elegidos})
    carpetas_ok = [{"id": cid, "nombre": f["nombre"], "ruta": _ruta(carpetas, f["padre_id"])}
                   for cid, f in carpetas.items() if all(p in _norm(f["nombre"]) for p in palabras)]
    return {"documentos": [_fila_documento(d, nombres, carpetas) for d in elegidos],
            "carpetas": sorted(carpetas_ok, key=lambda f: _norm(f["nombre"]))[:20],
            "total": len(encontrados)}


@router.get("/documentos/{did}/archivo")
def archivo(did: int, descargar: bool = False, ctx: ContextoModulo = Depends(acceso(CLAVE, VER))):
    """El PDF vigente: se abre en el navegador o, con ?descargar=1, se descarga."""
    with bd_modulo(CLAVE) as c:
        d = _documento_activo(c, did)
        v = c.execute("SELECT contenido FROM versiones WHERE documento_id=? AND reemplazada_en IS NULL", (did,)).fetchone()
    if not v:
        raise HTTPException(404, "El documento no tiene archivo.")
    return _pdf_respuesta(v["contenido"], d["titulo"], descargar)


# ------------------------------------------------------------------ carpetas (administrar)
@router.post("/carpetas")
def crear_carpeta(d: NuevaCarpeta, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    nombre = d.nombre.strip()
    if not nombre:
        raise HTTPException(422, "Escribe el nombre de la carpeta.")
    try:
        with bd_modulo(CLAVE) as c:
            _exigir_carpeta(c, d.padre_id)
            if _nombre_repetido(c, d.padre_id, nombre):
                raise HTTPException(409, "Ya hay una carpeta con ese nombre aquí.")
            cid = c.execute("INSERT INTO carpetas (padre_id, nombre, creada_por) VALUES (?,?,?)",
                            (d.padre_id, nombre, ctx.usuario_id)).lastrowid
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Ya hay una carpeta con ese nombre aquí.")
    ctx.auditar(f"{CLAVE}_carpeta_creada", f"carpeta #{cid}")
    return {"id": cid}


@router.patch("/carpetas/{cid}")
def cambiar_carpeta(cid: int, d: CambioCarpeta, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    try:
        with bd_modulo(CLAVE) as c:
            carpetas = _carpetas(c)
            if cid not in carpetas:
                raise HTTPException(404, "La carpeta no existe. Recarga la página.")
            nombre = (d.nombre if d.nombre is not None else carpetas[cid]["nombre"]).strip()
            padre = d.padre_id if d.mover else carpetas[cid]["padre_id"]
            if not nombre:
                raise HTTPException(422, "Escribe el nombre de la carpeta.")
            if d.mover:
                _exigir_carpeta(c, padre)
                if padre is not None and cid in {p["id"] for p in _ruta(carpetas, padre)}:
                    raise HTTPException(422, "No puedes mover una carpeta dentro de sí misma.")
            if _nombre_repetido(c, padre, nombre, excepto=cid):
                raise HTTPException(409, "Ya hay una carpeta con ese nombre en ese lugar.")
            c.execute("UPDATE carpetas SET nombre=?, padre_id=? WHERE id=?", (nombre, padre, cid))
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Ya hay una carpeta con ese nombre en ese lugar.")
    ctx.auditar(f"{CLAVE}_carpeta_cambiada", f"carpeta #{cid}")
    return {"ok": True}


@router.delete("/carpetas/{cid}")
def eliminar_carpeta(cid: int, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    """Solo carpetas vacías. Los documentos de la papelera que estaban en ella, si se restauran, vuelven al inicio."""
    with bd_modulo(CLAVE) as c:
        if not c.execute("SELECT 1 FROM carpetas WHERE id=?", (cid,)).fetchone():
            raise HTTPException(404, "La carpeta no existe. Recarga la página.")
        if c.execute("SELECT 1 FROM carpetas WHERE padre_id=?", (cid,)).fetchone() or c.execute(
                "SELECT 1 FROM documentos WHERE carpeta_id=? AND eliminado_en IS NULL", (cid,)).fetchone():
            raise HTTPException(409, "La carpeta no está vacía. Mueve o elimina primero lo que tiene dentro.")
        c.execute("DELETE FROM carpetas WHERE id=?", (cid,))
    ctx.auditar(f"{CLAVE}_carpeta_eliminada", f"carpeta #{cid}")
    return {"ok": True}


# ------------------------------------------------------------------ documentos (administrar)
@router.post("/documentos")
def subir(d: NuevoDocumento, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    datos, nombre, huella = _pdf(d)
    titulo = d.titulo.strip()
    if len(titulo) < 3:
        raise HTTPException(422, "El título debe tener al menos 3 caracteres.")
    with bd_modulo(CLAVE) as c:
        _exigir_carpeta(c, d.carpeta_id)
        did = c.execute("INSERT INTO documentos (carpeta_id, titulo, descripcion, creado_por, actualizado_por) "
                        "VALUES (?,?,?,?,?)",
                        (d.carpeta_id, titulo, d.descripcion.strip(), ctx.usuario_id, ctx.usuario_id)).lastrowid
        c.execute("INSERT INTO versiones (documento_id, contenido, nombre_archivo, tamano, sha256, subida_por) "
                  "VALUES (?,?,?,?,?,?)", (did, datos, nombre, len(datos), huella, ctx.usuario_id))
    ctx.auditar(f"{CLAVE}_documento_subido", f"documento #{did}")
    return {"id": did}


@router.patch("/documentos/{did}")
def cambiar_documento(did: int, d: CambioDocumento, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    titulo = d.titulo.strip()
    if len(titulo) < 3:
        raise HTTPException(422, "El título debe tener al menos 3 caracteres.")
    with bd_modulo(CLAVE) as c:
        _documento_activo(c, did)
        _exigir_carpeta(c, d.carpeta_id)
        c.execute("UPDATE documentos SET titulo=?, descripcion=?, carpeta_id=?, actualizado_por=?, actualizado_en=now() "
                  "WHERE id=?", (titulo, d.descripcion.strip(), d.carpeta_id, ctx.usuario_id, did))
    ctx.auditar(f"{CLAVE}_documento_cambiado", f"documento #{did}")
    return {"ok": True}


@router.post("/documentos/{did}/version")
def reemplazar(did: int, d: ArchivoPdf, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    """Sube un PDF nuevo para el documento. El anterior queda 30 días en la papelera y se puede restaurar."""
    datos, nombre, huella = _pdf(d)
    with bd_modulo(CLAVE) as c:
        _documento_activo(c, did)
        c.execute("UPDATE versiones SET reemplazada_en=now(), reemplazada_por=? "
                  "WHERE documento_id=? AND reemplazada_en IS NULL", (ctx.usuario_id, did))
        vid = c.execute("INSERT INTO versiones (documento_id, contenido, nombre_archivo, tamano, sha256, subida_por) "
                        "VALUES (?,?,?,?,?,?)", (did, datos, nombre, len(datos), huella, ctx.usuario_id)).lastrowid
        c.execute("UPDATE documentos SET actualizado_por=?, actualizado_en=now() WHERE id=?", (ctx.usuario_id, did))
    ctx.auditar(f"{CLAVE}_documento_reemplazado", f"documento #{did}, versión #{vid}")
    return {"id": did, "version": vid}


@router.delete("/documentos/{did}")
def eliminar(did: int, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    with bd_modulo(CLAVE) as c:
        _documento_activo(c, did)
        c.execute("UPDATE documentos SET eliminado_en=now(), eliminado_por=? WHERE id=?", (ctx.usuario_id, did))
    ctx.auditar(f"{CLAVE}_documento_eliminado", f"documento #{did}")
    return {"ok": True}


# ------------------------------------------------------------------ papelera (administrar)
@router.get("/papelera")
def papelera(ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    """Documentos eliminados y versiones reemplazadas de los últimos 30 días, con los días que les quedan."""
    with bd_modulo(CLAVE) as c:
        carpetas = _carpetas(c)
        docs = [dict(f) for f in c.execute(
            """SELECT d.id, d.titulo, d.carpeta_id, d.eliminado_en AS fecha, d.eliminado_por AS por, v.tamano,
                      GREATEST(0, ? - floor(extract(epoch FROM now() - d.eliminado_en) / 86400))::int AS dias
               FROM documentos d LEFT JOIN versiones v ON v.documento_id=d.id AND v.reemplazada_en IS NULL
               WHERE d.eliminado_en IS NOT NULL ORDER BY d.eliminado_en DESC""", (DIAS_PAPELERA,))]
        vers = [dict(f) for f in c.execute(
            """SELECT v.id, v.documento_id, d.titulo, d.carpeta_id, v.nombre_archivo, v.tamano, v.subida_en,
                      v.reemplazada_en AS fecha, v.reemplazada_por AS por,
                      GREATEST(0, ? - floor(extract(epoch FROM now() - v.reemplazada_en) / 86400))::int AS dias
               FROM versiones v JOIN documentos d ON d.id=v.documento_id
               WHERE v.reemplazada_en IS NOT NULL AND d.eliminado_en IS NULL ORDER BY v.reemplazada_en DESC""",
            (DIAS_PAPELERA,))]
    nombres = nombres_de({f["por"] for f in docs + vers})
    for f in docs + vers:
        f["por"] = nombres.get(f["por"], "—")
        f["ruta"] = _ruta(carpetas, f["carpeta_id"])
    return {"documentos": docs, "versiones": vers, "dias_papelera": DIAS_PAPELERA}


@router.get("/papelera/documentos/{did}/archivo")
def archivo_eliminado(did: int, descargar: bool = False, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    with bd_modulo(CLAVE) as c:
        f = c.execute("""SELECT d.titulo, v.contenido FROM documentos d
                         JOIN versiones v ON v.documento_id=d.id AND v.reemplazada_en IS NULL
                         WHERE d.id=? AND d.eliminado_en IS NOT NULL""", (did,)).fetchone()
    if not f:
        raise HTTPException(404, "Ese documento ya no está en la papelera.")
    return _pdf_respuesta(f["contenido"], f["titulo"], descargar)


@router.get("/papelera/versiones/{vid}/archivo")
def archivo_version(vid: int, descargar: bool = False, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    with bd_modulo(CLAVE) as c:
        f = c.execute("""SELECT d.titulo, v.contenido FROM versiones v JOIN documentos d ON d.id=v.documento_id
                         WHERE v.id=? AND v.reemplazada_en IS NOT NULL""", (vid,)).fetchone()
    if not f:
        raise HTTPException(404, "Esa versión ya no está en la papelera.")
    return _pdf_respuesta(f["contenido"], f"{f['titulo']} (versión anterior)", descargar)


@router.post("/papelera/documentos/{did}/restaurar")
def restaurar_documento(did: int, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    """Vuelve a publicar el documento. Si su carpeta se eliminó, queda en el inicio."""
    with bd_modulo(CLAVE) as c:
        if not c.execute("SELECT 1 FROM documentos WHERE id=? AND eliminado_en IS NOT NULL", (did,)).fetchone():
            raise HTTPException(404, "Ese documento ya no está en la papelera.")
        c.execute("UPDATE documentos SET eliminado_en=NULL, eliminado_por=NULL, actualizado_por=?, actualizado_en=now() "
                  "WHERE id=?", (ctx.usuario_id, did))
    ctx.auditar(f"{CLAVE}_documento_restaurado", f"documento #{did}")
    return {"ok": True}


@router.post("/papelera/versiones/{vid}/restaurar")
def restaurar_version(vid: int, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    """La versión anterior vuelve a ser la vigente; la que estaba vigente pasa a la papelera."""
    with bd_modulo(CLAVE) as c:
        v = c.execute("""SELECT v.documento_id FROM versiones v JOIN documentos d ON d.id=v.documento_id
                         WHERE v.id=? AND v.reemplazada_en IS NOT NULL AND d.eliminado_en IS NULL""", (vid,)).fetchone()
        if not v:
            raise HTTPException(404, "Esa versión ya no está en la papelera.")
        did = v["documento_id"]
        c.execute("UPDATE versiones SET reemplazada_en=now(), reemplazada_por=? "
                  "WHERE documento_id=? AND reemplazada_en IS NULL", (ctx.usuario_id, did))
        c.execute("UPDATE versiones SET reemplazada_en=NULL, reemplazada_por=NULL WHERE id=?", (vid,))
        c.execute("UPDATE documentos SET actualizado_por=?, actualizado_en=now() WHERE id=?", (ctx.usuario_id, did))
    ctx.auditar(f"{CLAVE}_documento_restaurado", f"documento #{did}, versión #{vid}")
    return {"ok": True}


@router.delete("/papelera/documentos/{did}")
def borrar_documento(did: int, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    with bd_modulo(CLAVE) as c:
        n = c.execute("DELETE FROM documentos WHERE id=? AND eliminado_en IS NOT NULL", (did,)).rowcount
    if not n:
        raise HTTPException(404, "Ese documento ya no está en la papelera.")
    ctx.auditar(f"{CLAVE}_papelera_borrado", f"documento #{did}")
    return {"ok": True}


@router.delete("/papelera/versiones/{vid}")
def borrar_version(vid: int, ctx: ContextoModulo = Depends(acceso(CLAVE, ADMIN))):
    with bd_modulo(CLAVE) as c:
        n = c.execute("DELETE FROM versiones WHERE id=? AND reemplazada_en IS NOT NULL", (vid,)).rowcount
    if not n:
        raise HTTPException(404, "Esa versión ya no está en la papelera.")
    ctx.auditar(f"{CLAVE}_papelera_borrado", f"versión #{vid}")
    return {"ok": True}


# ------------------------------------------------------------------ Ley 21.719
def exportar_titular(usuario_id: int) -> dict:
    """Lo que el módulo guarda de la persona: qué carpetas creó y qué documentos subió, cambió o eliminó (sin los PDF)."""
    with bd_modulo(CLAVE) as c:
        return {
            "carpetas_creadas": [dict(f) for f in c.execute(
                "SELECT id, nombre, creada_en FROM carpetas WHERE creada_por=? ORDER BY id", (usuario_id,))],
            "documentos": [dict(f) for f in c.execute(
                """SELECT id, titulo,
                          CASE WHEN creado_por=? THEN creado_en END AS creado_en,
                          CASE WHEN actualizado_por=? THEN actualizado_en END AS ultimo_cambio_en,
                          CASE WHEN eliminado_por=? THEN eliminado_en END AS eliminado_en
                   FROM documentos WHERE ? IN (creado_por, actualizado_por, eliminado_por) ORDER BY id""",
                (usuario_id, usuario_id, usuario_id, usuario_id))],
            "versiones_subidas": [dict(f) for f in c.execute(
                "SELECT id, documento_id, nombre_archivo, tamano, subida_en FROM versiones WHERE subida_por=? ORDER BY id",
                (usuario_id,))],
            "versiones_reemplazadas": [dict(f) for f in c.execute(
                "SELECT id, documento_id, reemplazada_en FROM versiones WHERE reemplazada_por=? ORDER BY id",
                (usuario_id,))],
        }


def depurar() -> int:
    """Vacía la papelera: borra lo eliminado y las versiones reemplazadas hace más de 30 días."""
    with bd_modulo(CLAVE) as c:
        versiones = c.execute("DELETE FROM versiones WHERE reemplazada_en < now() - make_interval(days => ?)",
                              (DIAS_PAPELERA,)).rowcount
        documentos = c.execute("DELETE FROM documentos WHERE eliminado_en < now() - make_interval(days => ?)",
                               (DIAS_PAPELERA,)).rowcount
    return versiones + documentos
