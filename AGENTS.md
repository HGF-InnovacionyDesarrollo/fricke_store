# Fricke Store — notas para asistentes de código

Este archivo lo leen solos los asistentes de código al abrir el proyecto (Antigravity y otros lo leen como
`AGENTS.md`; Claude Code, a través de `CLAUDE.md`). Si tu asistente no lo leyó solo, pídele que lo lea antes de empezar. Resume las reglas obligatorias para desarrollar
en Fricke Store; el detalle está en los documentos enlazados, que son la fuente de verdad. Si algo aquí contradice
esos documentos, mandan ellos (y en diseño, manda el PDF de `docs/diseno/`).

## Qué es

- Portal FastAPI + PostgreSQL (esquema `portal` + uno por módulo `m_<clave>`; desarrollo con `docker compose up -d`) del Hospital Dr. Gustavo Fricke (puerto 8090). Todo en español de Chile.
- Plataforma de la red: un código, una instalación por establecimiento (`ECO_ESTABLECIMIENTO`, carpeta `establecimientos/`). Cada hospital tiene su propia marca, usuarios, datos y base. Nada propio de un hospital va fijo en el código: va en `establecimientos/<clave>/`. Ver `docs/RED.md`.
- Lo común a los módulos está en `backend/plataforma.py` (backend) y `frontend/js/cabecera.js` (cabecera común).

## Cómo hablar con la persona

- Español de Chile, simple y sin jerga: quien pide puede no ser técnico. Explica las decisiones técnicas en palabras sencillas.
- Di "módulos", nunca "subproyectos".

## Preparar el PC (una vez)

Guía completa para colaboradores: `docs/COLABORAR.md`. En corto: Git, Python 3.12+, Docker Desktop abierto, luego
`pip install -r requirements.txt`, `docker compose up -d` (base PostgreSQL vacía y propia), crear una cuenta de prueba
con `python backend/gestionar.py crear --rut 11.111.111-1 --nombre "..." --admin`, ejecutar `iniciar.bat` y abrir
http://localhost:8090. Usar siempre RUT de prueba, nunca datos reales.

## Módulos: camino obligatorio

- Para crear o cambiar un módulo, seguir SIEMPRE la guía `/nuevo-modulo` (`.claude/skills/nuevo-modulo/SKILL.md`, la fuente única), aunque la persona no la nombre ("haz una app para…"). En Claude Code es el comando `/nuevo-modulo`; en Antigravity está como habilidad en `.agents/skills/nuevo-modulo/`; en cualquier otro asistente, leer ese archivo y seguir sus pasos en orden. Guía paso a paso con todas las reglas de `docs/MODULOS.md` y `docs/diseno/`.
- Antes de programar, preguntar: para qué sirve y quién lo usa, qué datos guarda y de quién, cuánto tiempo se conservan, familia de color (1 a 5), nombre y pictograma.
- Trabajar en una rama propia `modulo/<clave>` creada desde `main` al día, y crear el módulo solo con `python backend/gestionar.py nuevo-modulo --clave <clave> --nombre "<Nombre>" --familia <N> --pictograma <archivo.svg>`. Nunca crear la carpeta a mano ni copiar otro módulo.
- Estructura según `docs/MODULOS.md`: `modulos/<clave>/` con `manifiesto.py` (identidad, ficha de tratamiento, permisos, acciones de bitácora), `api.py`, `migraciones/NNN_*.sql` (esquema PostgreSQL propio y rol propio por módulo; cada cambio en un archivo nuevo) y `frontend/`. Un módulo no importa código de otro módulo.
- Sin login propio: todo endpoint usa `Depends(acceso("<clave>", "<clave>.<permiso>"))` y toda acción relevante queda en la bitácora, sin RUT en el detalle.
- Tocar solo `modulos/<clave>/` y su ícono (`docs/logo/modulos/<nombre>/`, `frontend/img/modulos/<nombre>.svg`). Cambiar algo común (`backend/`, `frontend/`, `docs/`) se conversa antes con la Unidad de Innovación y Desarrollo.

## Datos personales y Ley 21.719

- **En esta primera etapa ningún módulo maneja datos de pacientes.** Si la idea los necesita, detenerse y proponer una versión sin ellos (el portal no carga un módulo cuya ficha los mencione).
- La Ley 21.719 rige desde el 1 dic 2026: ficha de tratamiento completa en el manifiesto (finalidad, categorías, titulares, base de licitud, plazo de conservación), mínimo de datos, permisos mínimos por perfil, y derechos del titular (`exportar_titular`, `depurar`) si guarda datos de personas. Ver `docs/MODULOS.md` §7 y `docs/CUMPLIMIENTO.md`.
- Nunca poner datos de personas en la dirección, el título de la pestaña ni el almacenamiento del navegador.

## Diseño (obligatorio)

- Todo módulo sigue `docs/diseno/` (PDF oficiales + resumen en `README.md`). Ante dudas, manda el PDF.
- Ícono: baldosa 48 × 48 con el degradado de una de las 5 familias (1 Atención y acceso, 2 Clínica, 3 Calidad y seguridad, 4 Operaciones y equipos, 5 Personas y gestión) y pictograma de línea de Lucide (máx. 3 elementos, sin texto).
- Nombre: una o dos palabras, mayúscula solo inicial, sin "Fricke", "App", "Sistema" ni siglas.
- Interfaz dentro de la carcasa común (barra superior, riel lateral, dirección `/m/<modulo>/<pantalla>`), colores solo desde las variables de `base.css`, cuatro estados (cargando, vacío, error, sin permiso), WCAG 2.2 AA, probado a 360 y 1440 px en modo claro y oscuro.
- **El logo de Fricke Store no se modifica nunca.**
- Proponer antes de aplicar cambios de diseño que afecten a más de un módulo.

## Pruebas y entrega

- Pruebas: `pip install -r requirements-dev.txt` y `pytest` (necesita Docker Desktop abierto). Las reglas comunes de módulos están en `tests/test_reglas_modulos.py` y se aplican solas a todo módulo; además van las pruebas propias en `modulos/<clave>/tests/`. `python backend/gestionar.py modulos` valida que el módulo cargue.
- `main` está protegida: todo cambio entra por *pull request* y debe pasar el chequeo "Pruebas y directrices" (`.github/workflows/revision.yml`). No subir directo a `main`.
- En el *pull request*, completar con honestidad la checklist de `.github/pull_request_template.md` y adjuntar capturas claro/oscuro a 360 y 1440 px. Subir `version` del manifiesto en cada entrega.

## Nunca

- Nunca subir `data/` (bases, claves, respaldos), contraseñas, claves ni datos reales de personas.
- Nunca tocar el logo de Fricke Store ni fijar en el código algo propio de un hospital.
- Nunca saltarse la guía `/nuevo-modulo`, las pruebas ni el *pull request*, sea cual sea el asistente o editor.
