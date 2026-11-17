"""API del módulo, montada en /api/m/ejemplo/. Todo endpoint usa Depends(acceso(...))."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from plataforma import ContextoModulo, acceso, bd_modulo, nombres_de

from .manifiesto import CLAVE

router = APIRouter()
DIAS_CONSERVACION = 365


class NuevoAviso(BaseModel):
    titulo: str = Field(min_length=3, max_length=80)
    texto: str = Field(min_length=3, max_length=1000)


@router.get("/avisos")
def listar(ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.ver"))):
    with bd_modulo(CLAVE) as c:
        filas = [dict(f) for f in c.execute("SELECT * FROM avisos ORDER BY id DESC LIMIT 100")]
    autores = nombres_de({f["autor_id"] for f in filas})
    for f in filas:
        f["autor"] = autores.get(f["autor_id"], "—")
        f["puede_borrar"] = ctx.puede(f"{CLAVE}.moderar") or (
            f["autor_id"] == ctx.usuario_id and ctx.puede(f"{CLAVE}.publicar"))
    return filas


@router.post("/avisos")
def publicar(d: NuevoAviso, ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.publicar"))):
    with bd_modulo(CLAVE) as c:
        aid = c.execute("INSERT INTO avisos (autor_id, titulo, texto) VALUES (?,?,?)",
                        (ctx.usuario_id, d.titulo.strip(), d.texto.strip())).lastrowid
    # A la bitácora va QUÉ se hizo y sobre qué id, nunca el contenido.
    ctx.auditar(f"{CLAVE}_aviso_publicado", f"aviso #{aid}")
    return {"id": aid}


@router.delete("/avisos/{aid}")
def borrar(aid: int, ctx: ContextoModulo = Depends(acceso(CLAVE, f"{CLAVE}.ver"))):
    with bd_modulo(CLAVE) as c:
        a = c.execute("SELECT autor_id FROM avisos WHERE id=?", (aid,)).fetchone()
        if not a:
            raise HTTPException(404, "El aviso no existe.")
        propio = a["autor_id"] == ctx.usuario_id and ctx.puede(f"{CLAVE}.publicar")
        if not (propio or ctx.puede(f"{CLAVE}.moderar")):
            raise HTTPException(403, "Solo puedes borrar tus propios avisos.")
        c.execute("DELETE FROM avisos WHERE id=?", (aid,))
    ctx.auditar(f"{CLAVE}_aviso_borrado", f"aviso #{aid}{'' if propio else ' (moderación)'}")
    return {"ok": True}


# ------------------------------------------------------------------ Ley 21.719 (obligatorios si guarda datos de personas)
def exportar_titular(usuario_id: int) -> dict:
    """Lo que este módulo guarda de la persona. Se suma a 'Descargar mis datos' en Mi cuenta."""
    with bd_modulo(CLAVE) as c:
        return {"avisos_publicados": [dict(f) for f in c.execute(
            "SELECT id, titulo, texto, creado_en FROM avisos WHERE autor_id=? ORDER BY id", (usuario_id,))]}


def depurar() -> int:
    """Aplica el plazo de conservación declarado en la ficha. Devuelve cuántos registros eliminó."""
    with bd_modulo(CLAVE) as c:
        return c.execute("DELETE FROM avisos WHERE creado_en < now() - make_interval(days => ?)",
                         (DIAS_CONSERVACION,)).rowcount
