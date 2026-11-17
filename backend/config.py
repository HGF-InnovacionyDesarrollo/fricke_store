"""Configuración del ecosistema. Todo se puede sobrescribir con variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATOS_DIR = BASE_DIR / "data"   # logs, respaldos y claves locales (nunca se versiona)

# Base de datos PostgreSQL. Desarrollo: docker compose up -d (ver docker-compose.yml).
# Producción: el servidor del hospital, con TLS (agregar ?sslmode=require) y una contraseña fuera del repositorio.
DATABASE_URL = os.environ.get("ECO_DATABASE_URL", "postgresql://fricke:fricke_desarrollo@localhost:5432/fricke_store")
ESQUEMA_PORTAL = "portal"          # núcleo; cada módulo usa su propio esquema m_<clave>
# Base SQLite de las versiones anteriores, solo para trasladar los datos (gestionar.py importar-sqlite)
SQLITE_ANTERIOR = Path(os.environ.get("ECO_DB", DATOS_DIR / "ecosistema.db"))

# Módulos del ecosistema: código en modulos/<clave>/, datos en el esquema m_<clave>
MODULOS_DIR = BASE_DIR / "modulos"
# Cada módulo usa un rol de PostgreSQL propio, dueño solo de su esquema (requiere CREATEROLE)
ROLES_POR_MODULO = os.environ.get("ECO_ROLES_POR_MODULO", "1") == "1"

# Identidad de la institución (aparece en la portada, el aviso de privacidad y la cuenta)
NOMBRE_INSTITUCION = os.environ.get("ECO_INSTITUCION", "Hospital Dr. Gustavo Fricke")
NOMBRE_PRODUCTO = os.environ.get("ECO_PRODUCTO", "Fricke Store")
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

# Solicitudes públicas (crear cuenta, recuperar clave): máximo por IP en la ventana indicada
LIMITE_PUBLICO = int(os.environ.get("ECO_LIMITE_PUBLICO", 5))
VENTANA_PUBLICO_MIN = int(os.environ.get("ECO_VENTANA_PUBLICO_MIN", 15))
# Si se define (p. ej. "hospitalfricke.cl"), las solicitudes de cuenta exigen correo de ese dominio
DOMINIO_CORREO = os.environ.get("ECO_DOMINIO_CORREO", "").strip().lower()

# Jefe superior del servicio: a quien se dirigen las solicitudes de derechos (Ley 21.719 art. 23)
JEFE_SERVICIO = os.environ.get("ECO_JEFE_SERVICIO", "Director(a) del Hospital Dr. Gustavo Fricke")

# Ley 21.663: el hospital figura como Operador de Importancia Vital (verificar Res. Ex. 87/2025 en el Diario Oficial).
# Como OIV, la actualización a ANCI se acorta a 24 h cuando se afecta el servicio esencial y se exige plan de acción.
ES_OIV = os.environ.get("ECO_ES_OIV", "1") == "1"

# Retención de la bitácora (días). Lo más antiguo se archiva sellado, sin romper la cadena.
RETENCION_BITACORA_DIAS = int(os.environ.get("ECO_RETENCION_BITACORA_DIAS", 1825))  # 5 años

# Copia de cada evento de auditoría en JSON por línea, para un SIEM. Vacío para desactivar.
_siem = os.environ.get("ECO_LOG_SIEM", str(DATOS_DIR / "logs" / "auditoria.jsonl"))
LOG_SIEM = Path(_siem) if _siem else None

# Respaldos
RESPALDOS_DIR = Path(os.environ.get("ECO_RESPALDOS_DIR", DATOS_DIR / "respaldos"))
RESPALDO_COPIA_EXTERNA = os.environ.get("ECO_RESPALDO_COPIA", "")      # p. ej. \\servidor\respaldos\fricke
RESPALDO_CLAVE_ARCHIVO = Path(os.environ.get("ECO_RESPALDO_CLAVE", DATOS_DIR / "respaldo.key"))
RESPALDOS_A_CONSERVAR = int(os.environ.get("ECO_RESPALDOS_CONSERVAR", 30))
RESPALDO_MAX_HORAS = int(os.environ.get("ECO_RESPALDO_MAX_HORAS", 26))   # alerta si el último es más antiguo
# Herramientas de PostgreSQL. Con Docker: ECO_PG_DUMP="docker exec -i fricke-db pg_dump" (y lo mismo para pg_restore)
PG_DUMP = os.environ.get("ECO_PG_DUMP", "pg_dump")
PG_RESTORE = os.environ.get("ECO_PG_RESTORE", "pg_restore")

# HTTPS (si se definen, servidor.py levanta TLS y el portal envía HSTS)
TLS_CERT = os.environ.get("ECO_TLS_CERT", "")
TLS_KEY = os.environ.get("ECO_TLS_KEY", "")

# Perfiles de acceso
ROLES = {
    "funcionario": "Funcionario",
    "admin": "Administrador",
    "dpd": "Delegado de Protección de Datos",
    "seguridad": "Delegado de Ciberseguridad",
}

# Contraseñas
CLAVE_LARGO_MIN = 15   # NIST SP 800-63B rev. 4 para un solo factor
CLAVE_LARGO_MAX = 128

# Versión vigente del aviso de privacidad. Al cambiarla, todos deben volver a leerlo.
VERSION_AVISO = os.environ.get("ECO_VERSION_AVISO", "2026-11b")

# Plazo de respuesta a solicitudes de derechos (Ley 21.719): 30 días corridos, prorrogables.
PLAZO_SOLICITUD_DIAS = 30
