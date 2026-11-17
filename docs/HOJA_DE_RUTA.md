# Hoja de ruta

## Hecho (v0.1, nov 2026)
- Portal con portada estilo Google, menú de módulos vacío, tarjeta de cuenta, ingreso con RUT.
- Centro de privacidad (*Mi cuenta*) con derechos de la Ley 21.719.
- Bitácora encadenada, bloqueo de pantalla, cierre por inactividad.

## Hecho (v0.2, nov 2026)
- Solicitud de cuenta y de contraseña desde el login; panel de administración web con perfiles admin y DPD.

## Hecho (v0.3, nov 2026)
- Plataforma de módulos: carpeta `modulos/`, manifiesto con ficha de tratamiento, base y migraciones por módulo, permisos internos, cabecera común, exportación de datos y depuración por plazo. Directrices en `docs/MODULOS.md`.

## Hecho (v0.4, nov 2026)
- PostgreSQL como base relacional: esquema `portal` y un esquema con rol propio por módulo, migraciones numeradas, traslado desde SQLite y respaldos con `pg_dump`.

## Hecho (v0.5, nov 2026)
- Plataforma de la red: una instalación por establecimiento con el mismo código (`establecimientos/<clave>/`), partiendo por Fricke Store y Marga-Marga Store.

## Próximo
1. **Asistente de IA real**: búsqueda sobre protocolos y documentos institucionales (RAG). Preferir un modelo que corra en la red del hospital o con contrato que garantice no entrenar con los datos; evaluación de impacto antes de abrirlo. Filtro que detecte RUT o nombres de pacientes antes de enviar la pregunta.
2. **Notificaciones por correo institucional** (SMTP del hospital) cuando se aprueba una cuenta o se responde una solicitud.
3. **Registro de Actividades de Tratamiento** en PDF para el DPD, a partir de `/api/admin/modulos/registro-tratamiento`.
7. **Permisos de módulo desde el panel** (hoy se otorgan por consola con `gestionar.py permiso`).
4. **Integración con el directorio institucional** (Active Directory/LDAP) para altas y bajas automáticas.
5. **Segundo factor** (TOTP) para administradores y módulos con datos sensibles.
6. **Módulos candidatos**: SIMI (prevención de caídas), Monitor de temperatura y humedad, gestión de equipos médicos.
