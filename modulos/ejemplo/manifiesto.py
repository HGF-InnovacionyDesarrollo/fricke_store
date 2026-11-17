"""Identidad, ficha de tratamiento (Ley 21.719) y permisos del módulo.

Cambiar la ficha de un módulo con datos sensibles deja su evaluación de impacto (EIPD) como pendiente:
el DPD debe volver a aprobarla en Administración › Módulos antes de que reaparezca en el menú.
"""
from plataforma import FichaTratamiento, Manifiesto

CLAVE = "ejemplo"

MANIFIESTO = Manifiesto(
    clave=CLAVE,
    nombre="Tablón de avisos",
    descripcion="Módulo de ejemplo: avisos internos de la unidad.",
    version="0.1.0",
    responsable="Unidad de Innovación y Desarrollo",
    familia=5,  # 1 a 5 según docs/diseno/ (Parte 2). Ícono: backend/logo_modulo.py → frontend/img/modulos/
    orden=900,
    perfiles_iniciales=("admin",),
    tratamiento=FichaTratamiento(
        finalidad="Publicar avisos internos de la unidad y registrar quién los publicó.",
        categorias_datos="identificación del funcionario autor (id interno), texto del aviso",
        titulares="funcionarios del hospital",
        base_licitud="funciones legales del hospital como órgano público (Ley 21.719 art. 20)",
        conservacion="365 días desde la publicación",
        datos_sensibles=False,
    ),
    permisos={
        f"{CLAVE}.ver": "Ver los avisos",
        f"{CLAVE}.publicar": "Publicar avisos y borrar los propios",
        f"{CLAVE}.moderar": "Borrar avisos de otras personas",
    },
    permisos_por_perfil={
        "funcionario": (f"{CLAVE}.ver",),
        "admin": (f"{CLAVE}.ver", f"{CLAVE}.publicar", f"{CLAVE}.moderar"),
    },
    acciones={
        f"{CLAVE}_aviso_publicado": "Aviso publicado (Tablón de avisos)",
        f"{CLAVE}_aviso_borrado": "Aviso borrado (Tablón de avisos)",
    },
)
