"""Identidad, ficha de tratamiento (Ley 21.719) y permisos del módulo F+docs.

Biblioteca de documentos institucionales en PDF (protocolos, normas, guías, instructivos), ordenados en carpetas.
Todos los funcionarios con acceso los ven y descargan; solo quien tiene el permiso documentos.administrar
crea carpetas, sube, reemplaza y elimina. Lo eliminado queda 30 días en la papelera y las versiones reemplazadas, 5 años en el historial.
"""
from plataforma import FichaTratamiento, Manifiesto

CLAVE = "documentos"

MANIFIESTO = Manifiesto(
    clave=CLAVE,
    nombre="F+docs",
    descripcion="Documentos institucionales del hospital en PDF, ordenados en carpetas y con buscador.",
    version="0.2.0",
    responsable="Unidad de Innovación y Desarrollo",
    familia=5,  # Familia 5: Personas y gestión (docs/diseno/, Parte 2). Pictograma folder-open de Lucide.
    orden=500,
    perfiles_iniciales=("admin", "funcionario"),
    tratamiento=FichaTratamiento(
        finalidad="Publicar los documentos institucionales del hospital y registrar quién creó cada carpeta "
                  "y quién subió, cambió o eliminó cada documento.",
        categorias_datos="identificación interna del funcionario que administra (id de usuario) y fechas de sus acciones; "
                         "los documentos son institucionales y no deben contener datos de personas",
        titulares="funcionarios del hospital con permiso para administrar documentos",
        base_licitud="funciones legales del hospital como órgano público (Ley 21.719 art. 20)",
        conservacion="mientras el documento esté publicado; lo eliminado queda 30 días en la papelera y las "
                     "versiones reemplazadas, 5 años en el historial; luego se borran",
        datos_sensibles=False,
    ),
    permisos={
        f"{CLAVE}.ver": "Ver, buscar y descargar documentos",
        f"{CLAVE}.administrar": "Crear carpetas, subir, reemplazar y eliminar documentos, y usar la papelera",
    },
    # Administrar se otorga persona a persona (gestionar.py permiso --rut … --permiso documentos.administrar).
    permisos_por_perfil={
        "funcionario": (f"{CLAVE}.ver",),
        "admin": (f"{CLAVE}.ver",),
    },
    acciones={
        f"{CLAVE}_carpeta_creada": "Carpeta creada (F+docs)",
        f"{CLAVE}_carpeta_cambiada": "Carpeta renombrada o movida (F+docs)",
        f"{CLAVE}_carpeta_eliminada": "Carpeta eliminada (F+docs)",
        f"{CLAVE}_documento_subido": "Documento subido (F+docs)",
        f"{CLAVE}_documento_cambiado": "Datos de un documento cambiados (F+docs)",
        f"{CLAVE}_documento_reemplazado": "Documento reemplazado por una versión nueva (F+docs)",
        f"{CLAVE}_documento_eliminado": "Documento enviado a la papelera (F+docs)",
        f"{CLAVE}_documento_restaurado": "Documento o versión restaurada desde la papelera (F+docs)",
        f"{CLAVE}_papelera_borrado": "Eliminado para siempre desde la papelera (F+docs)",
    },
)
