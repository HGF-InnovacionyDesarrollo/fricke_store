# Cumplimiento normativo del portal

Mapa de qué hace el ecosistema para cumplir la **Ley 21.719** (protección de datos personales, plena vigencia el 1 de diciembre de 2026) y normas relacionadas. Es un documento técnico de apoyo: **debe validarlo el Delegado de Protección de Datos (DPD) y la asesoría jurídica**.

## Ley 21.719: principios

| Principio | Cómo se implementa |
|---|---|
| **Licitud y lealtad** | Base de licitud: funciones legales del órgano público y obligaciones legales. Por eso al primer ingreso se pide *leer* el aviso (deber de información), no "aceptar" un consentimiento que no corresponde en una relación laboral. Queda registro de versión y fecha de lectura (`aceptaciones_aviso`). |
| **Finalidad** | El portal solo usa datos para autenticar, autorizar y auditar. Cada módulo futuro declara su finalidad en la tabla `modulos` (`finalidad`, `categorias_datos`). |
| **Proporcionalidad / minimización** | Solo RUT, nombre, cargo, unidad y correo. El asistente IA no guarda el texto de las preguntas, solo su largo. Los intentos con RUT inexistente se registran enmascarados (`12.***.**8-5`). La pantalla bloqueada muestra solo el nombre. |
| **Calidad** | La persona ve sus datos en *Mi cuenta › Información personal* y puede pedir rectificación con un clic. |
| **Responsabilidad (accountability)** | Bitácora encadenada con SHA-256: cada registro incluye el hash del anterior; `gestionar.py verificar-auditoria` detecta cualquier edición o borrado. |
| **Seguridad** | scrypt con sal, bloqueo tras 5 intentos, cookie `HttpOnly` + `SameSite=Strict`, token guardado como hash, cierre por inactividad (15 min) y por fin de turno (12 h), bloqueo de pantalla para equipos compartidos, cabeceras CSP/anti-iframe, protección CSRF. |
| **Transparencia e información** | Aviso de privacidad en lenguaje simple (resumen de 4 puntos al ingresar + texto completo en `/privacidad`), versionado. |
| **Confidencialidad** | Mínimo privilegio: el menú de módulos solo muestra los habilitados para el rol o la persona. Sin cookies de terceros ni analítica externa; sin recursos cargados desde Internet. |

## Ley 21.719: derechos del titular

| Derecho | Dónde |
|---|---|
| Acceso | *Mi cuenta › Información personal* y *Descargar mis datos* (JSON con todo lo almacenado, incluida su bitácora). |
| Rectificación, supresión, oposición, bloqueo | *Mi cuenta › Datos y privacidad › Nueva solicitud*. Se calcula el vencimiento (30 días corridos) y el DPD las ve con `gestionar.py solicitudes`. |
| Portabilidad | Mismo archivo JSON, formato estructurado y de uso común. |
| Información sobre su actividad | *Mi cuenta › Seguridad*: sesiones abiertas (con cierre remoto) y últimos 50 eventos, con los intentos fallidos destacados. |

## Privacidad por diseño para los módulos futuros

Ningún módulo puede aparecer en el menú de puntos si:
- no tiene **finalidad** y **categorías de datos** declaradas (columnas obligatorias), o
- trata **datos sensibles** (salud) y no tiene la **evaluación de impacto aprobada** (`eipd_aprobada = 1`).

Con esos campos se puede generar automáticamente el **Registro de Actividades de Tratamiento** del hospital.

## Otras normas consideradas

- **Ley 20.584** (derechos y deberes de los pacientes): la ficha clínica es reservada; la trazabilidad de accesos de este portal es la base para auditar quién entra a los módulos con datos de pacientes.
- **Ley 21.663** (Marco de Ciberseguridad): los prestadores de salud pueden ser calificados como operadores de importancia vital. La bitácora íntegra y el registro de intentos fallidos sirven para detectar y reportar incidentes en plazo.
- **Ley 21.180** (Transformación Digital del Estado) y sus normas técnicas: autenticación, registro y seguridad de la información.
- **Accesibilidad**: navegación por teclado, foco visible, etiquetas en todos los controles, modo oscuro automático, diseño usable en celular.

## Pendientes antes de producción

1. Revisión del aviso de privacidad por el DPD y jurídica; completar correo del DPD y plazos de conservación (`config.py`).
2. Servir por **HTTPS** (`ECO_COOKIE_SEGURA=1`) detrás del proxy institucional.
3. Política de respaldo y retención de la bitácora; copia periódica del último hash fuera del servidor (sello de integridad).
4. Procedimiento de reporte de vulneraciones a la Agencia de Protección de Datos y a la ANCI.
5. Integrar el alta/baja de usuarios con el registro de personal (hoy es por consola).
6. Segundo factor (TOTP) para administradores.
