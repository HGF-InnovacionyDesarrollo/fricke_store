"""Identidad, ficha de tratamiento (Ley 21.719) y permisos del módulo F+mefi.

Módulo de simulación docente y evaluación determinística de parámetros cardiotocográficos
(Protocolo de Vigilancia del Bienestar Fetal Intraparto V2 sept. 2025, ACOG CPG No. 10 2025,
FIGO 2015 y NICE NG229). En esta etapa no almacena ni procesa datos de pacientes.
"""
from plataforma import FichaTratamiento, Manifiesto

CLAVE = "monitoreo_fetal"

MANIFIESTO = Manifiesto(
    clave=CLAVE,
    nombre="F+mefi",
    descripcion="Simulador docente y evaluador normativo de cardiotocografía intraparto (Protocolo V2, ACOG CPG No. 10 y FIGO 2015).",
    version="0.1.1",
    responsable="Unidad de Parto Integral (SAIP)",
    familia=2,  # Familia 2: Clínica (docs/diseno/, Parte 2)
    orden=210,
    perfiles_iniciales=("admin", "funcionario"),
    tratamiento=FichaTratamiento(
        finalidad="Registrar ejercicios de simulación y entrenamiento docente en interpretación cardiotocográfica realizados por funcionarios clínicos.",
        categorias_datos="identificación interna del funcionario autor (id de usuario), parámetros cardiotocográficos simulados y clasificación resultante",
        titulares="funcionarios del establecimiento",
        base_licitud="funciones legales de capacitación continua y calidad asistencial del órgano público (Ley 21.719 art. 20)",
        conservacion="365 días desde el registro de la simulación",
        datos_sensibles=False,
    ),
    permisos={
        f"{CLAVE}.ver": "Ver simulaciones docentes, casos de estudio y criterios normativos",
        f"{CLAVE}.simular": "Registrar simulaciones docentes propias y borrar las propias",
        f"{CLAVE}.moderar": "Borrar simulaciones docentes de otras personas",
    },
    permisos_por_perfil={
        "funcionario": (f"{CLAVE}.ver", f"{CLAVE}.simular"),
        "admin": (f"{CLAVE}.ver", f"{CLAVE}.simular", f"{CLAVE}.moderar"),
    },
    acciones={
        f"{CLAVE}_simulacion_creada": "Simulación registrada (F+mefi)",
        f"{CLAVE}_simulacion_borrada": "Simulación borrada (F+mefi)",
    },
)
