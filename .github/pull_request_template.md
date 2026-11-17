## Qué hace este cambio

<!-- Módulo o cambio, para qué sirve y quién lo pidió. -->

## Checklist de las directrices (docs/diseno/, Parte 4, y docs/MODULOS.md)

**Ícono**
- [ ] La familia está elegida y el degradado coincide con la tabla de familias.
- [ ] El pictograma usa trazo 2 sobre la retícula de 24, sin texto y con tres elementos o menos.
- [ ] Se entiende a 24 px y no se confunde con otro módulo de la misma familia.
- [ ] El nombre tiene una o dos palabras, sin "Fricke", "App", "Sistema" ni siglas.
- [ ] Están todos los archivos del ícono (`backend/logo_modulo.py --verificar`).

**Interfaz**
- [ ] Usa `iniciarModulo(...)`: barra superior común, riel o pestañas, una acción principal como máximo.
- [ ] Cada pantalla con datos tiene estados de carga, vacío, error y sin permiso.
- [ ] Colores solo desde `base.css`; probado en modo claro y oscuro.
- [ ] Textos según las reglas de redacción, sin códigos de error a la vista.
- [ ] Se usa entero con teclado; probado a 360 y 1440 px.

**Datos y seguridad**
- [ ] No maneja datos de pacientes (primera etapa).
- [ ] Ficha de tratamiento completa en el manifiesto, con plazo de conservación.
- [ ] Todo endpoint usa `acceso(...)` con el permiso más acotado.
- [ ] Las acciones relevantes quedan en la bitácora, sin contenido ni RUT en el detalle.
- [ ] `exportar_titular` y `depurar` implementados si guarda datos de personas.
- [ ] No sube `data/`, contraseñas ni datos reales.
- [ ] `python backend/gestionar.py modulos` lo carga sin errores.

## Capturas

<!-- Modo claro y oscuro, a 360 y 1440 px. -->

## Aprobación

- [ ] Revisado y aprobado por la Unidad de Innovación y Desarrollo.
