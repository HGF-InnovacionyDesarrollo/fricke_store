---
name: nuevo-modulo
description: Crea o modifica un módulo de Fricke Store siguiendo todas las directrices del ecosistema (docs/MODULOS.md, docs/diseno/, Ley 21.719). Úsalo SIEMPRE que alguien pida crear, agregar, construir o cambiar un módulo, una funcionalidad dentro de modulos/, o "una app para" una unidad del hospital, aunque no nombre este comando.
---

# Crear o modificar un módulo de Fricke Store

Sigue estos pasos en orden. No te saltes ninguno ni pidas permiso para seguir las reglas: son obligatorias.
Habla con la persona en español de Chile, en simple (puede no ser técnica). Las reglas completas están en
`docs/MODULOS.md` y `docs/diseno/README.md` (ante dudas de diseño manda el PDF de `docs/diseno/`); léelas antes de empezar.

## 1. Entender el módulo (preguntar antes de programar)

Pregunta solo lo que falte, todo en un mensaje:

- **Para qué sirve y quién lo usa** (qué perfil: funcionario, administrador, DPD, seguridad).
- **Qué datos guarda** y **de quién**. Si involucra **datos de pacientes, detente**: en esta etapa no se permiten
  (el portal no carga el módulo). Propón una versión sin datos de pacientes o deja la idea registrada para más adelante.
- **Cuánto tiempo deben guardarse** los datos (plazo de conservación).
- **Familia de color** del ícono (propón una con su motivo, la persona confirma):
  1 Atención y acceso · 2 Clínica · 3 Calidad y seguridad · 4 Operaciones y equipos · 5 Personas y gestión.
- **Nombre**: una o dos palabras, mayúscula solo inicial, sin "Fricke", "App", "Sistema" ni siglas.
- **Pictograma**: propón un ícono de [Lucide](https://lucide.dev) (metáfora concreta, máximo 3 elementos, sin texto)
  distinto de los otros módulos de la misma familia. Guarda su SVG de 24 × 24 en `modulos/<clave>/pictograma.svg`
  (Lucide es ISC: deja el comentario de atribución).

## 2. Crear desde el molde

```bash
git checkout main && git pull
git checkout -b modulo/<clave>
python backend/gestionar.py nuevo-modulo --clave <clave> --nombre "<Nombre>" --familia <N> --pictograma <archivo.svg>
```

Nunca crees la carpeta a mano ni copies otro módulo: el molde trae ícono, esqueleto, permisos, bitácora y pruebas.

## 3. Completar el módulo

- **`manifiesto.py`**: ficha de tratamiento completa (finalidad, categorías, titulares, base de licitud, conservación),
  permisos `<clave>.<accion>` con el mínimo necesario por perfil, y cada acción de bitácora con su etiqueta.
- **`migraciones/001_inicial.sql`**: reemplaza las tablas del ejemplo. Tipos de PostgreSQL (`BIGINT GENERATED ALWAYS
  AS IDENTITY`, `TIMESTAMPTZ`, `CHECK`), personas por `usuarios.id` (nunca RUT ni nombre copiados), sin
  `BEGIN/COMMIT`, sin nombrar esquemas. Si cambia algo ya aplicado, se agrega `002_…sql`: nunca se edita una migración.
- **`api.py`**: cada endpoint con `Depends(acceso(CLAVE, "<clave>.<permiso>"))`; `bd_modulo(CLAVE)` para datos;
  `ctx.auditar(...)` con el id, nunca contenido ni RUT; `exportar_titular` y `depurar` si guarda datos de personas.
- **`frontend/`**: `iniciarModulo(CLAVE, {destinos, accion, buscar, alNavegar})` (3 a 7 destinos → riel; menos → pestañas;
  una acción principal como máximo), los cuatro estados (`cargando`, `estadoVacio`, `estadoError`, `estadoSinPermiso`),
  `confirmarDestructivo` para lo que no se deshace, `.titulo-pantalla`, `.tarjeta`, íconos `linea(...)` de Lucide,
  colores solo con variables de `base.css`, todo texto del servidor con `esc()`.
- **Redacción**: tutear, frases cortas, botones con verbo y objeto ("Guardar cambios"), errores sin códigos,
  fechas "17 nov 2026" y horas 14:30.
- **Pruebas propias** en `modulos/<clave>/tests/test_modulo.py`: adapta las del ejemplo a la API real (qué hace y
  quién puede hacerlo, incluido un perfil sin permiso).

No modifiques `backend/`, `frontend/` común, `docs/` ni otros módulos. Si el módulo necesita algo común que no
existe (correo, adjuntos, reportes, unidades), no lo improvises: avisa a la persona que hay que pedirlo a la
Unidad de Innovación y Desarrollo.

## 4. Verificar antes de entregar

1. `python backend/gestionar.py modulos` → el módulo carga sin errores.
2. `pytest` → todo en verde (necesita Docker Desktop abierto). Si una regla falla, corrige el módulo, nunca la prueba.
3. Levanta el portal (`iniciar.bat`), activa el módulo en *Administración › Módulos* para un perfil y revísalo en el
   navegador: modo claro y oscuro, 1440 px y 360 px, con teclado, estados vacío y de error. Toma capturas.
4. `python backend/logo_modulo.py --verificar <nombre-del-icono> --familia <N>` → sin observaciones.

## 5. Entregar

```bash
git add modulos/<clave> docs/logo/modulos/<nombre-del-icono> frontend/img/modulos/<nombre-del-icono>.svg
git commit -m "feat(<clave>): <qué hace>"
git push -u origin modulo/<clave>
```

Abre el pull request hacia `main`. La plantilla trae la checklist de las directrices: márcala con honestidad, adjunta
las capturas y explica en una línea lo que no se pudo revisar automáticamente. Dile a la persona que la Unidad lo
revisará y que la revisión automática de GitHub debe quedar en verde.
