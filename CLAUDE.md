# Fricke Store — notas para asistentes de código

- Portal FastAPI + PostgreSQL (esquema `portal` + uno por módulo `m_<clave>`; desarrollo con `docker compose up -d`) del Hospital Dr. Gustavo Fricke (puerto 8090). Todo en español de Chile.
- Plataforma de la red: un código, una instalación por establecimiento (`ECO_ESTABLECIMIENTO`, carpeta `establecimientos/`). Nada propio de un hospital va fijo en el código: va en `establecimientos/<clave>/`. Ver `docs/RED.md`.
- Antes de crear o cambiar un módulo, leer y seguir `docs/MODULOS.md`. Partir con `python backend/gestionar.py nuevo-modulo`.
- Lo común a los módulos está en `backend/plataforma.py` (backend) y `frontend/js/cabecera.js` (cabecera).
- Nunca subir `data/` (bases, claves, respaldos). Cumplimiento normativo en `docs/CUMPLIMIENTO.md`.
- Diseño: todo módulo sigue `docs/diseno/` (PDF oficiales + resumen en README). Ante dudas, manda el PDF.
