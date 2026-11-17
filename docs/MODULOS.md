# Directrices para módulos de Fricke Store

Todo módulo del ecosistema (SIMI, monitor de temperatura, equipos médicos, etc.) sigue estas reglas.
Existen para que cada módulo se vea y se comporte como parte del mismo portal, comparta el ingreso con RUT
y cumpla la **Ley 21.719** desde el primer día, sin que cada equipo tenga que reinventarlo.

La referencia viva es el módulo de ejemplo [`modulos/ejemplo/`](../modulos/ejemplo/) (Tablón de avisos).
Las palabras **debe** y **no debe** son obligatorias; **conviene** es una recomendación.

---

## 1. Crear un módulo

```bash
python backend/gestionar.py nuevo-modulo --clave farmacia --nombre "Farmacia"
```

Copia el ejemplo a `modulos/farmacia/` con la clave ya reemplazada. Luego:

1. Completar `manifiesto.py` (sección 3), sobre todo la **ficha de tratamiento**.
2. Reemplazar `migraciones/001_inicial.sql` por las tablas del módulo.
3. Escribir la API en `api.py` y la página en `frontend/`.
4. Reiniciar el portal: el módulo se registra solo, **inactivo**.
5. Revisar la lista de la sección 10 y publicarlo en **Administración › Módulos**.

`python backend/gestionar.py modulos` valida todos los módulos, aplica sus migraciones y muestra su estado.

## 2. Estructura de carpetas

```
modulos/<clave>/
  __init__.py              exporta MANIFIESTO, router y (si guarda datos de personas) exportar_titular y depurar
  manifiesto.py            identidad, ficha de tratamiento, permisos y acciones de bitácora
  api.py                   endpoints (APIRouter)
  migraciones/
    001_inicial.sql        esquema de su base propia
    002_<cambio>.sql       cada cambio posterior, en un archivo nuevo
  frontend/
    index.html             su página (obligatoria)
    app.js · app.css       su lógica y estilos
  README.md                (conviene) para qué sirve, quién lo pidió, cómo probarlo
```

- La **clave** es el nombre de la carpeta: minúsculas, números y `_` (`farmacia`, `control_temperatura`), máximo 40.
- Las carpetas que empiezan con `_` no se cargan (sirven para borradores).
- Un módulo **no debe** importar código de otro módulo. Lo común va en `backend/plataforma.py`.

## 3. Manifiesto

```python
MANIFIESTO = Manifiesto(
    clave="farmacia", nombre="Farmacia", descripcion="Una línea", version="0.1.0",
    responsable="Unidad de Farmacia", icono="documento", color="#1565c0", orden=100,
    perfiles_iniciales=("admin",),
    tratamiento=FichaTratamiento(
        finalidad="Para qué usa datos personales, en lenguaje simple.",
        categorias_datos="identificación del paciente, medicamentos dispensados",
        titulares="pacientes hospitalizados",
        base_licitud="funciones legales del hospital (Ley 21.719 art. 20) y prestación de salud",
        conservacion="15 años desde el egreso (ficha clínica, Ley 20.584)",
        datos_sensibles=True,
    ),
    permisos={"farmacia.ver": "Ver dispensaciones", "farmacia.dispensar": "Registrar dispensaciones"},
    permisos_por_perfil={"funcionario": ("farmacia.ver",), "admin": ("farmacia.ver", "farmacia.dispensar")},
    acciones={"farmacia_dispensacion_registrada": "Dispensación registrada (Farmacia)"},
)
```

- El portal **valida** el manifiesto al arrancar; si algo falta, el módulo no se carga y lo dice en consola.
- **Quién manda en qué**: el manifiesto (revisado en el repositorio) define la identidad y la ficha de tratamiento.
  El panel de administración define quién lo ve, si está activo, el orden y la aprobación de la EIPD. El panel
  no puede cambiar la ficha de un módulo con código.
- Subir `version` (semver) en cada entrega. El cambio queda en la bitácora.
- `perfiles_iniciales` solo se usa la primera vez que se registra; después se ajusta en el panel.
- Íconos disponibles: los de `ICONOS` en `frontend/js/comun.js`. Colores: los de la paleta de `base.css`.

## 4. Acceso, sesión y permisos

- El módulo **no debe** tener su propio login, usuarios ni contraseñas. Usa la sesión del portal.
- **Todo** endpoint debe declarar `Depends(acceso("<clave>", "<clave>.<permiso>"))`. Esa dependencia comprueba:
  sesión válida y no bloqueada, contraseña ya cambiada y aviso de privacidad leído, módulo activo, módulo
  habilitado para el perfil o la persona, EIPD aprobada si trata datos sensibles, y el permiso pedido.
- Los permisos se nombran `<clave>.<accion>` y se declaran en el manifiesto. Una persona tiene los de su perfil
  más los que se le otorguen uno a uno: `gestionar.py permiso --rut … --permiso farmacia.dispensar`.
- Mínimo privilegio: el perfil `admin` administra el portal, no ve datos clínicos por defecto. Solo se le dan
  permisos de un módulo si su función lo requiere.
- La API vive en `/api/m/<clave>/…` y la página en `/m/<clave>/`. Así hereda la protección CSRF, las cabeceras
  de seguridad y `Cache-Control: no-store` del portal.
- Si un módulo tiene que correr fuera del portal (otro lenguaje, otro servidor), se conversa antes: se expondrá
  un endpoint de verificación de sesión en vez de duplicar el login.

## 5. Base de datos

- El ecosistema usa **una base PostgreSQL**. El núcleo vive en el esquema `portal` y cada módulo en **su propio
  esquema** `m_<clave>`, creado y administrado por un **rol propio** (`fricke_m_<clave>`). Se abre con `bd_modulo(CLAVE)`,
  que ya fija el esquema y el rol: el módulo no puede leer ni modificar las tablas del portal ni las de otro módulo.
- Para datos del portal (nombres de funcionarios, etc.) se usan las funciones de `plataforma.py`, nunca SQL directo.
- **Migraciones numeradas** `001_…sql`, `002_…sql`, sin saltos. El portal las aplica en orden y guarda la huella
  SHA-256 de cada una. **Una migración aplicada no se edita**: si cambió, el módulo no arranca. Los cambios van
  en una migración nueva. Los archivos no deben incluir `BEGIN`/`COMMIT`: el portal ya los envuelve en una transacción.
- Tipos de PostgreSQL: `BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` para ids, `TIMESTAMPTZ` para fechas,
  `BOOLEAN`, `NUMERIC` para montos, `JSONB` solo si de verdad no hay estructura. Restricciones `NOT NULL`, `CHECK`,
  `UNIQUE` y llaves foráneas **dentro** del esquema del módulo. Índices para las búsquedas frecuentes.
- No se nombra el esquema en el SQL (`avisos`, no `m_ejemplo.avisos`): `bd_modulo` ya lo fija.
- Personas: se guarda `usuarios.id` del portal (p. ej. `autor_id`), **nunca** el RUT, el nombre ni el correo
  copiados. Para mostrar nombres se usa `nombres_de(ids)`.
- Pacientes: si el módulo los necesita, se guarda lo mínimo y se declara en la ficha. Conviene un identificador
  interno y no el RUT en cada tabla.
- Fechas en `TIMESTAMPTZ` (la conexión trabaja en UTC); el navegador las muestra en hora de Chile con `fechaLocal()`.
- Consultas siempre con parámetros (`?`), nunca armando SQL con texto del usuario.
- Respaldos: `backend/respaldo.py crear` hace un `pg_dump` de toda la base (portal y todos los esquemas de módulos),
  cifrado, y `probar` lo restaura en una base temporal para verificarlo. No hay que hacer nada extra.

## 6. Bitácora y auditoría

- Toda acción que crea, cambia, borra, exporta o **consulta datos de pacientes** debe quedar en la bitácora
  central encadenada con `ctx.auditar("<clave>_<accion>", "detalle")`.
- La acción debe estar declarada en `acciones` del manifiesto (con su etiqueta legible, que la persona verá en
  *Mi cuenta › Actividad*). Si no está declarada, `auditar` lanza un error.
- El detalle dice **qué se hizo y sobre qué id**, nunca el contenido: `"dispensación #812"`, no el medicamento ni
  el paciente. Un detalle con algo que parezca un RUT se rechaza.
- No se registran contraseñas, tokens ni texto libre escrito por la persona.

## 7. Ley 21.719 (protección de datos)

Cada módulo que guarde datos de personas **debe**:

1. **Ficha de tratamiento** completa en el manifiesto. Se consulta en `GET /api/admin/modulos/registro-tratamiento`
   y es la base del Registro de Actividades de Tratamiento del DPD.
2. **Datos sensibles** (salud, biometría, etc.): marcar `datos_sensibles=True`. El módulo no aparece ni responde
   hasta que el DPD apruebe la **evaluación de impacto (EIPD)** en el panel. Si después cambia la ficha, la EIPD
   vuelve a pendiente sola.
3. **`exportar_titular(usuario_id) -> dict`**: lo que el módulo guarda de esa persona (como funcionario). Se suma
   automáticamente a *Mi cuenta › Descargar mis datos* (derechos de acceso y portabilidad).
4. **`depurar() -> int`**: borra lo que superó el plazo de `conservacion` y devuelve cuántos registros eliminó.
   Se ejecuta con `gestionar.py depurar` (programarlo a diario junto al respaldo) y queda en la bitácora.
5. **Minimización**: pedir y guardar solo lo necesario para la finalidad declarada. Nada de "por si acaso".
6. **Transparencia**: si la página recibe texto libre, mostrar un aviso como el del ejemplo
   ("No publiques datos de pacientes…") cuando no corresponda que los haya.
7. **Sin terceros**: no se cargan scripts, fuentes, analítica ni imágenes desde Internet. La CSP del portal lo
   bloquea igual. Si un módulo necesita un servicio externo (p. ej. un modelo de IA), requiere EIPD y contrato.

Las solicitudes de rectificación, supresión, oposición o bloqueo llegan al DPD por el portal; el responsable
del módulo debe poder ejecutarlas a mano mientras no exista un hook automático.

## 8. Apariencia (marca Fricke Store)

- La página debe cargar `/static/css/base.css`, `/static/css/cabecera.css`, `/static/js/comun.js` y
  `/static/js/cabecera.js`, y arrancar con `iniciarModulo("<clave>")`. Eso pinta la cabecera común (logo actual,
  nombre del módulo, menú de puntos, tarjeta de cuenta), exige sesión, resuelve el primer ingreso, activa el
  bloqueo de pantalla (`Ctrl+Alt+L`) y el cierre por inactividad, y entrega los permisos (`modulo.puede(...)`).
- Contenido dentro de `<main class="modulo-cuerpo">`.
- Colores **solo** con las variables de `base.css` (`--primario`, `--acento`, `--texto-2`, `--borde`…). Nunca
  colores fijos: así funcionan el modo oscuro y cualquier ajuste de marca.
- Reutilizar los componentes existentes: `.btn`, `.btn-texto`, `.btn-borde`, `.campo` (etiqueta flotante),
  `.aviso-suave`, `dialogo()`, `toast()`, `mostrarErrorEn()`.
- Llamadas al servidor con `api(ruta, {metodo, datos})`: agrega la cabecera anti-CSRF y maneja sesión expirada
  y pantalla bloqueada.
- Todo texto del servidor pasa por `esc()` antes de ir a `innerHTML`. Sin `eval`, sin scripts en línea (la CSP los bloquea).
- Accesibilidad (WCAG 2.1 AA, Ley 21.180 de transformación digital): `lang="es-CL"`, enlace "Saltar al contenido",
  etiquetas en cada campo, foco visible, contraste AA, usable con teclado y a 360 px de ancho.

## 9. Convenciones de código

- Idioma: **español de Chile** en código, comentarios, mensajes y nombres de tablas, igual que el portal.
- Python 3.12+, FastAPI y Pydantic con `Field(max_length=…)` en cada texto que entra. Funciones cortas;
  comentarios que expliquen el porqué.
- Mensajes de error claros para la persona, sin detalles técnicos ni datos de otras personas.
- JavaScript sin dependencias ni compilación: archivos `.js` con `"use strict"`.
- Sin secretos en el repositorio: se configuran con variables de entorno `ECO_<CLAVE>_…` y se documentan en el README del módulo.
- Nunca se sube `data/` (bases, claves, respaldos).
- Commits en español con prefijo: `feat(farmacia): …`, `fix(farmacia): …`, `docs: …`.

## 10. Lista antes de publicar un módulo

- [ ] `gestionar.py modulos` lo carga sin errores.
- [ ] Ficha de tratamiento completa y revisada con el responsable del proceso.
- [ ] `datos_sensibles` marcado si corresponde, y EIPD aprobada por el DPD.
- [ ] Todos los endpoints con `acceso(...)` y el permiso más acotado posible.
- [ ] Acciones relevantes en la bitácora, sin contenido ni RUT en el detalle.
- [ ] `exportar_titular` y `depurar` implementados si guarda datos de personas.
- [ ] Página con la cabecera común, probada en modo oscuro, con teclado y en pantalla angosta.
- [ ] Respaldo y prueba de restauración (`respaldo.py crear` y `probar`) incluyen su base.
- [ ] Perfiles que lo verán definidos en *Administración › Módulos* y módulo marcado como activo.

## Referencia rápida de `plataforma.py`

| Elemento | Uso |
|---|---|
| `Manifiesto`, `FichaTratamiento` | Declaración del módulo. |
| `acceso(clave, permiso)` | Dependencia obligatoria de cada endpoint; entrega un `ContextoModulo`. |
| `ctx.usuario_id`, `ctx.puede(p)`, `ctx.auditar(accion, detalle)` | Persona, permisos y bitácora. |
| `bd_modulo(clave)` | Conexión al esquema `m_<clave>` con el rol del módulo (confirma al salir, revierte si hay error). |
| `ahora()` | Fecha y hora UTC ISO-8601. |
| `nombres_de(ids)` | Nombres de funcionarios para mostrar, sin copiarlos. |
| `GET /api/modulos/<clave>/contexto` | Identidad del módulo y permisos de la persona (lo usa `iniciarModulo`). |
