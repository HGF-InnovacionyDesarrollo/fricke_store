# Directrices de diseño

Documentos oficiales de diseño del ecosistema, entregados por la Unidad de Innovación y Desarrollo (17 nov 2026).
**Son obligatorios para todo módulo** y prevalecen sobre cualquier otra indicación de diseño en este repositorio,
salvo las reglas posteriores de la Unidad que se listan en este archivo.

## Reglas posteriores de la Unidad

| Fecha | Regla |
|---|---|
| 18 nov 2026 | Todo módulo se llama **«F+» y su nombre corto**, en una palabra y en minúsculas: `F+data`, `F+farmacia`. Reemplaza la regla de nombre de los PDF («una o dos palabras, mayúscula solo inicial»). La revisión automática rechaza otro formato. |

| Documento | Contenido |
|---|---|
| [Directrices de diseño - Fricke Store.pdf](Directrices%20de%20diseño%20-%20Fricke%20Store.pdf) | Documento maestro. Parte 1: logo, uso junto al logo del Hospital, paleta y tipografía. Parte 2: logos de módulos. Parte 3: interfaz de módulos (navegación, componentes, estados, redacción, accesibilidad, uso en unidades clínicas, tamaños de pantalla). Parte 4: entrega y checklist de aprobación. |
| [Directrices de diseño - Logos de módulos.pdf](Directrices%20de%20diseño%20-%20Logos%20de%20módulos.pdf) | Detalle de los íconos de módulo (también resumido en la Parte 2 del maestro). |

## Lo esencial (resumen; ante cualquier duda manda el PDF)

**Íconos de módulo.** Baldosa 48 × 48, radio 12, degradado a 135° de su familia, pictograma de línea (Lucide, trazo 2,
máx. 3 elementos, sin texto) centrado en una caja de 24. Cinco familias:

| Familia | Degradado | Pictograma |
|---|---|---|
| 1 Atención y acceso | #1565C0 → #1774B4 | Blanco |
| 2 Clínica | #1876B3 → #1C949C | Blanco |
| 3 Calidad y seguridad | #1D969B → #54A87C | Tinta #2B3440 |
| 4 Operaciones y equipos | #58A87A → #C3AD55 | Tinta #2B3440 |
| 5 Personas y gestión | #C7AD53 → #FCB040 | Tinta #2B3440 |

Nombre en Outfit 500, tinta, sin degradado. **Nombre: «F+» y el nombre corto del módulo**, en una sola palabra y en minúsculas (ej.: `F+data`, `F+farmacia`); sin «fricke», «app» ni «sistema». Regla de la Unidad del 18 nov 2026: reemplaza la regla de nombre de los PDF de diseño. El archivo del ícono queda como `f-<nombre>` (ej.: `f-data.svg`).
Archivos en `docs/logo/modulos/<nombre>/` y copia en `frontend/img/modulos/<nombre>.svg`.

**Interfaz.** Como una app de Google Workspace sobre Material Design 3, sobria:
- Barra superior común (ícono y nombre, buscador, ayuda, menú de 9 puntos, avatar); el módulo no agrega su propio menú de cuenta.
- Riel lateral con 3 a 7 destinos (pestañas si son menos; barra inferior en teléfono), destino activo en píldora `--primario-suave`,
  un botón de acción principal como máximo, cada pantalla con su dirección `/m/<modulo>/<pantalla>`.
- Colores solo desde las variables de `base.css`; degradados solo en logos e íconos; color de familia solo en el ícono.
- Escala tipográfica: título de pantalla 22/28, diálogo 24/32, sección 16/24 (500), cuerpo 14/20, etiqueta 12/16 (500); títulos sin negrita.
- Espaciado en múltiplos de 4; radios: píldora (botones, chips), 12 (tarjetas), 8 (menús), 28 (diálogos), 4 (campos).
- Cuatro estados en toda pantalla con datos: cargando, vacío, error y sin permiso.
- Redacción: tutear, español de Chile, botones con verbo y objeto, errores sin códigos, fechas "17 nov 2026" y horas 14:30.
- WCAG 2.2 AA, teclado completo, zonas de clic ≥ 40 px (48 en táctil), probado a 360 y 1440 px.
- Datos de pacientes nunca en la dirección, el título de la pestaña ni el almacenamiento del navegador.
