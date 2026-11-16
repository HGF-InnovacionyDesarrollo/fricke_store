# Hoja de ruta

## Hecho (v0.1, nov 2026)
- Portal con portada estilo Google, menú de módulos vacío, tarjeta de cuenta, ingreso con RUT.
- Centro de privacidad (*Mi cuenta*) con derechos de la Ley 21.719.
- Bitácora encadenada, bloqueo de pantalla, cierre por inactividad.

## Próximo
1. **Asistente de IA real**: búsqueda sobre protocolos y documentos institucionales (RAG). Preferir un modelo que corra en la red del hospital o con contrato que garantice no entrenar con los datos; evaluación de impacto antes de abrirlo. Filtro que detecte RUT o nombres de pacientes antes de enviar la pregunta.
2. **Panel de administración** como primer módulo (solo rol `admin`): usuarios, módulos con su ficha de tratamiento, solicitudes de derechos, verificación de la bitácora.
3. **Registro de Actividades de Tratamiento** generado desde las fichas de los módulos (PDF para el DPD).
4. **Integración con el directorio institucional** (Active Directory/LDAP) para altas y bajas automáticas.
5. **Segundo factor** (TOTP) para administradores y módulos con datos sensibles.
6. **Módulos candidatos**: SIMI (prevención de caídas), Monitor de temperatura y humedad, gestión de equipos médicos.
