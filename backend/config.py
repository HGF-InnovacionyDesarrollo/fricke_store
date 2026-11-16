"""Configuración del ecosistema. Todo se puede sobrescribir con variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DB_PATH = Path(os.environ.get("ECO_DB", BASE_DIR / "data" / "ecosistema.db"))

# Identidad de la institución (aparece en la portada, el aviso de privacidad y la cuenta)
NOMBRE_INSTITUCION = os.environ.get("ECO_INSTITUCION", "Hospital")
NOMBRE_PRODUCTO = os.environ.get("ECO_PRODUCTO", "Ecosistema")
CORREO_DPD = os.environ.get("ECO_CORREO_DPD", "protecciondedatos@hospital.cl")  # Delegado de Protección de Datos
MESA_AYUDA = os.environ.get("ECO_MESA_AYUDA", "Anexo 0000 · Mesa de ayuda TI")

# Sesión
SESION_INACTIVIDAD_MIN = int(os.environ.get("ECO_INACTIVIDAD_MIN", 15))  # cierre por inactividad
SESION_MAXIMA_HORAS = int(os.environ.get("ECO_SESION_MAX_H", 12))       # duración de un turno
COOKIE_SEGURA = os.environ.get("ECO_COOKIE_SEGURA", "0") == "1"         # poner 1 al servir por HTTPS
COOKIE_NOMBRE = "eco_sesion"

# Intentos de acceso
MAX_INTENTOS = int(os.environ.get("ECO_MAX_INTENTOS", 5))
BLOQUEO_MIN = int(os.environ.get("ECO_BLOQUEO_MIN", 15))

# Contraseñas
CLAVE_LARGO_MIN = 10

# Versión vigente del aviso de privacidad. Al cambiarla, todos deben volver a leerlo.
VERSION_AVISO = os.environ.get("ECO_VERSION_AVISO", "2026-11")

# Plazo de respuesta a solicitudes de derechos (Ley 21.719): 30 días corridos, prorrogables.
PLAZO_SOLICITUD_DIAS = 30
