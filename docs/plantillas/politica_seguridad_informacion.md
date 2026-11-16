# Política de Seguridad de la Información — Hospital Dr. Gustavo Fricke

Versión 0.1 (borrador) · Aprobada por Resolución Exenta N° [____] de [fecha] · Revisión cada 2 años

> Plantilla de Innova Fricke basada en el DS 7/2023 (arts. 4 y 5), la política general del MINSAL PS-NC-005 v5 (NCh-ISO 27001:2022) y la Ley 21.663. **Antes de usarla, verifica si el Servicio de Salud Viña del Mar-Quillota o el hospital ya tienen una política vigente.** Si existe, este documento sirve como anexo para Fricke Store.

## 1. Objetivo

Proteger la confidencialidad, integridad, disponibilidad y resiliencia de la información del hospital, especialmente la información clínica y los datos personales, frente a amenazas internas y externas.

## 2. Alcance

Todos los sistemas, equipos, redes y personas (funcionarios, honorarios y proveedores) que traten información del hospital, incluido el ecosistema Fricke Store y sus módulos.

## 3. Responsables (DS 7/2023 art. 5; no externalizables)

- **Director(a):** aprueba esta política y asigna los recursos.
- **Encargado(a) de Seguridad de la Información:** [nombre].
- **Responsable de los activos de información:** [nombre por cada sistema crítico].
- **Delegado(a) de Ciberseguridad** (Ley 21.663): [nombre].
- **Delegado(a) de Protección de Datos** (Ley 21.719): [nombre].
- **Comité de Seguridad de la Información:** Director o subdirector administrativo, Encargado de SI, TI, DPD, Delegado de Ciberseguridad, Calidad y Jurídica. Sesiona [trimestralmente].

## 4. Principios y lineamientos

1. **Identificar:** se mantiene un inventario de activos y un catálogo de plataformas (DS 11/2023), con clasificación de la información y análisis de riesgos anual.
2. **Proteger:**
   - **Acceso:** por perfil y mínimo privilegio; cuentas personales e intransferibles; alta y baja ligadas a Recursos Humanos; revisión trimestral de las cuentas privilegiadas.
   - **Autenticación:** contraseñas de al menos 15 caracteres y lista de prohibidas; segundo factor obligatorio para cuentas privilegiadas, acceso remoto y sistemas con datos sensibles.
   - **Protección de datos y equipos:** cifrado en tránsito (TLS 1.2+) y en respaldos; equipos clínicos y de IoT en redes segmentadas.
   - **Desarrollo seguro:** OWASP ASVS, revisión de dependencias y separación de ambientes.
3. **Detectar:** monitoreo continuo, registro de eventos en UTC sincronizado con el SHOA y conservado al menos 5 años, y alertas de seguridad.
4. **Responder:** Procedimiento de gestión y reporte de incidentes (ANCI en 3 h; Agencia sin dilaciones indebidas).
5. **Recuperar:**
   - respaldos diarios cifrados con copia externa y pruebas de restauración al menos trimestrales;
   - plan de continuidad revisado cada 2 años y certificado, si corresponde, como OIV.

## 5. Capacitación y concientización

- Inducción en seguridad y protección de datos para todo funcionario nuevo.
- Campaña anual.
- Simulacro anual de incidente.

## 6. Cumplimiento

El incumplimiento de esta política puede dar lugar a responsabilidad administrativa. La Ley 21.719 considera falta grave a la probidad las infracciones gravísimas a la protección de datos (arts. 45 y 46).

## 7. Políticas específicas (anexos)

Autenticación · Control de acceso · Respaldo · Criptografía · Uso aceptable · Gestión de incidentes · Proveedores · Desarrollo seguro.
Usar como base las políticas específicas del MINSAL: PS-NC-003, PS-NC-004, PS-NC-008, PS-NC-015 y otras.
