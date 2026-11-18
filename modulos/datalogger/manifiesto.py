"""Identidad, ficha de tratamiento (Ley 21.719) y permisos de F+data.

F+data recibe y muestra lo que registran los data logger del hospital (hoy, los Monitor T/H de temperatura y
humedad). Los datos de las mediciones no son datos personales; lo único personal que guarda es qué funcionario
importó cada archivo y quién revisó cada alarma, para la trazabilidad que piden las pautas de acreditación.
"""
from plataforma import FichaTratamiento, Manifiesto

CLAVE = "datalogger"

MANIFIESTO = Manifiesto(
    clave=CLAVE,
    nombre="F+data",
    descripcion="Temperatura y humedad de los data logger del hospital: valores, alarmas, revisiones e informes.",
    version="0.2.2",
    responsable="Unidad de Innovación y Desarrollo",
    familia=4,  # Operaciones y equipos (docs/diseno/, Parte 2)
    orden=200,
    perfiles_iniciales=("admin",),
    tratamiento=FichaTratamiento(
        finalidad=("Registrar las condiciones de almacenamiento que miden los data logger y dejar constancia de "
                   "qué funcionario importó cada archivo y quién revisó cada alarma y qué hizo."),
        categorias_datos=("identificación del funcionario (id interno) que importa archivos o revisa alarmas, "
                          "acción registrada en la revisión y su fecha"),
        titulares="funcionarios del hospital",
        base_licitud="funciones legales del hospital como órgano público (Ley 21.719 art. 20)",
        conservacion="5 años desde la fecha de la medición, de la importación o de la revisión",
        datos_sensibles=False,
    ),
    permisos={
        f"{CLAVE}.ver": "Ver valores, gráficos, alarmas e informes",
        f"{CLAVE}.importar": "Importar los archivos de la tarjeta SD de los equipos",
        f"{CLAVE}.revisar": "Registrar la revisión de una alarma y la acción tomada",
        f"{CLAVE}.configurar": "Cambiar la ubicación de los sensores y dejarlos fuera de servicio",
        f"{CLAVE}.equipos": "Configurar los equipos conectados por USB (hora, sensores, calibración, WiFi y clave)",
    },
    permisos_por_perfil={
        "funcionario": (f"{CLAVE}.ver",),
        "admin": (f"{CLAVE}.ver", f"{CLAVE}.importar", f"{CLAVE}.revisar", f"{CLAVE}.configurar", f"{CLAVE}.equipos"),
    },
    acciones={
        f"{CLAVE}_importacion_realizada": "Archivos de data logger importados (F+data)",
        f"{CLAVE}_alarma_revisada": "Revisión de alarma registrada (F+data)",
        f"{CLAVE}_sensor_actualizado": "Sensor actualizado (F+data)",
        f"{CLAVE}_lecturas_exportadas": "Mediciones descargadas (F+data)",
        f"{CLAVE}_equipo_configurado": "Equipo configurado por USB (F+data)",
    },
)
