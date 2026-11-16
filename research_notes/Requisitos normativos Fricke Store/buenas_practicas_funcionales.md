# Buenas prácticas funcionales y técnicas para un portal intranet hospitalario con SSO y lanzador de aplicaciones (Fricke Store)

Convención usada en estas notas: **[E]** = esencial, **[R]** = recomendado. Las marcas E/R son juicio del investigador (están en "Inferencias") y se basan en los hallazgos citados. Estado de Fricke Store tomado del encargo: login RUT+clave con scrypt, bloqueo a los 5 fallos, cambio forzado de clave temporal, inactividad de 15 min, sesión máxima de 12 h, bloqueo de pantalla, lanzador por rol, Mi cuenta (sesiones, actividad, exportación, derechos), panel admin con registro de módulos con EIPD y auditoría con cadena hash; **sin** MFA, sin SSO/AD, sin correo, SQLite, servidor único, sin respaldos automatizados, sin monitoreo.

Advertencia general sobre las fuentes: muchas fuentes de salud sobre DR, break-glass y estaciones compartidas son blogs de proveedores o consultoras (Accountable, Censinet, nhimg, Imprivata), no normas. Se indica en cada caso.

## 1. Identidad y acceso (SSO, directorio, MFA, ciclo de vida, break-glass, PAM, estaciones compartidas, contraseñas)

### Takeaway
El portal ya cumple bien los tiempos de sesión de NIST para AAL3 (15 min de inactividad, 12 h en total). Las brechas grandes son tres. Primero, la falta de un IdP estándar (OIDC/SAML) que emita tokens a los módulos. Segundo, la falta de federación con AD/LDAP ligada a RR.HH. Tercero, la falta de MFA o de al menos una opción resistente a phishing. Además, la política de contraseñas debe revisarse contra NIST SP 800-63B rev.4: 15 caracteres mínimo sin MFA, lista de bloqueo, sin rotación periódica ni reglas de composición. Una ruta de bajo costo es Keycloak (open source), federado con AD vía LDAP.

### Cited Findings
**Contraseñas y sesión (NIST SP 800-63B-4)**
- Las contraseñas de factor único SHALL tener mínimo 15 caracteres. Las que se usan solo dentro de MFA, mínimo 8 — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- Se SHOULD permitir un máximo de al menos 64 caracteres, y se SHOULD aceptar ASCII imprimible, espacio y Unicode — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- No SHALL imponerse reglas de composición (mezcla de tipos de caracteres). No SHALL exigirse cambio periódico. Sí SHALL forzarse el cambio ante evidencia de compromiso — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- Las claves nuevas o cambiadas SHALL compararse contra una lista de bloqueo de claves comunes, esperadas o comprometidas, y se SHALL informar al usuario el motivo del rechazo — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- Limitación de intentos: no más de 100 fallos consecutivos antes de deshabilitar el autenticador; se MAY fijar límites menores — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- Timeouts de sesión. AAL2: total ≤24 h e inactividad ≤1 h (SHOULD). AAL3: total ≤12 h (SHALL) e inactividad ≤15 min (SHOULD) — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- Las contraseñas no son resistentes a phishing. En AAL2 el verificador SHALL ofrecer al menos una opción resistente a phishing. AAL3 exige autenticador resistente a phishing con clave no exportable — [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html)
- OWASP: el timeout de sesión debe aplicarse en el servidor, no solo en el cliente — [OWASP WSTG Testing Session Timeout](https://pentest.y-security.de/Web%20Security%20Testing%20Guide/2022/06-Session_Management_Testing/07-Testing_Session_Timeout); [OWASP ASVS 4.0.3 V3](https://github.com/OWASP/ASVS/blob/v4.0.3/4.0/en/0x12-V3-Session-management.md)
- ASVS v4 anotado: L2 con 12 h o 30 min de inactividad; L3 con 12 h o 15 min y 2FA. No se pudo verificar el texto de ASVS 5.0 — [OWASP AASVS 3.3](https://owasp-aasvs4.readthedocs.io/en/latest/V3.3.html)

**MFA en salud (NHS como referencia)**
- La política MFA de NHS England, incorporada al DSPT, exige MFA en todo acceso remoto y en el acceso privilegiado a sistemas alojados externamente. Recomienda MFA para el acceso privilegiado a otros sistemas. La autenticación federada con un sistema capaz de MFA cuenta como cumplimiento, y las excepciones deben quedar en un registro de excepciones MFA — [NHS England MFA policy](https://nhsd-proxy.openprescribing.net/cyber-and-data-security/guidance-and-resources/multi-factor-authentication-mfa-policy/nhs-england-multi-factor-authentication-policy)
- NHS CIS2 (Care Identity Service 2) acepta smartcards, Windows Hello, passkeys, llaves de seguridad (YubiKey) e iPads. Algunas APIs nacionales exigen un autenticador AAL3 (Windows Hello o smartcard) — [NHS CIS2 authenticators](https://nhsd-proxy.openprescribing.net/services/care-identity-service/applications-and-services/cis2-authentication/authenticators); [CPE CIS2](https://cpe.org.uk/digital-and-technology/data-security/care-identity-service-2-cis2/)
- NHS ofrece "virtual smartcards" con passcode opcional — [NHS virtual smartcards](https://nhsd-proxy.openprescribing.net/services/care-identity-service/registration-authority-users/registration-authority-help/virtual-smartcards)

**Tap-and-go / SSO clínico (casos de proveedor, cifras autorreportadas)**
- Harrogate NHS FT: las enfermeras reportan ahorrar 15–30 min por turno de 12 h con Imprivata (tap-and-go) — [Imprivata Harrogate](https://imprivata.com/sites/imprivata/files/2024-12/Harrogate%20and%20District%20NHS%20Foundation%20Trust%20%20improves%20clinical%20workflow%20efficiencies%20with%20%20Imprivata%2C%20benefiting%20both%20staff%20and%20patients.pdf)
- CHRISTUS Health: 49.057 horas clínicas liberadas y USD 3,2 M de ahorro anual — [casestudies.com CHRISTUS](https://www.casestudies.com/company/imprivata/case-study/proving-the-impact-of-time-savings-and-reducing-physician-burnout-with-single-sign-on); [Becker's](https://www.beckershospitalreview.com/healthcare-information-technology/how-single-sign-on-within-ehrs-can-save-clinicians-time-reduce-hospital-costs-improve-patient-care)
- Tallaght University Hospital (Irlanda): cerca de 1 h más de contacto con pacientes por turno, según el titular del caso — [Imprivata Tallaght 2026](https://www.imprivata.com/sites/imprivata/files/2026-04/EAM%20with%20MFA%20-%20Tallaght%20University%20Hospital%20Case%20Study%20-%20Mar2026%20%28UK%29.pdf)
- Royal United Hospitals Bath: proyecto "tap-and-go" orientado a reducir el largo login inicial al comienzo del turno — [Imprivata RUH Bath](https://www.imprivata.com/sites/imprivata/files/2021-04/OS-CSS-bath-royal-UK-0720.pdf)

**Estaciones compartidas**
- Separar la sesión del dispositivo (gestionada por TI, siempre encendida) de la sesión de identidad del usuario, que se renueva por persona — [nhimg FAQ shared workstations](https://nhimg.org/faq/why-do-shared-clinical-workstations-create-identity-governance-risk/)
- Reautenticación rápida (badge, smartcard, biometría), bloqueo automático por inactividad, cierre forzado al cambio de turno y no depender solo del logout manual — [SecureW2 shared workstation guide](https://securew2.com/blog/hipaa-shared-workstation-authentication-guide); [CapMinds](https://www.capminds.com/blog/how-to-secure-windows-clinical-workstations-without-disrupting-nursing-workflows/)
- El cambio rápido de usuario debe limpiar el contexto previo (formularios en caché, aprobaciones abiertas). Un modelo de política recomienda deshabilitar el "fast user switching" de Windows salvo justificación clínica — [nhimg](https://nhimg.org/faq/what-controls-matter-most-for-shared-device-access-governance-in-healthcare/); [Accountable workstation policy](https://www.accountablehq.com/post/workstation-security-policy-for-shared-exam-room-computers-template-requirements-and-best-practices)
- Step-up de autenticación para acciones sensibles (prescribir, liberar registros) — [nhimg](https://nhimg.org/faq/what-controls-matter-most-for-shared-device-access-governance-in-healthcare/)
- Sin bloqueo rápido y cambio limpio de usuario, la auditoría deja de reflejar al actor real — [nhimg](https://nhimg.org/faq/why-do-shared-workstations-create-so-much-access-friction-in-healthcare/)

**Break-glass y acceso privilegiado (fuentes de consultoría, no normativas)**
- Break-glass solo cuando hay riesgo para el paciente. Debe pedir un motivo obligatorio, alertar en tiempo real a seguridad o cumplimiento, y revisar a posteriori cada evento — [Accountable EHR access controls](https://www.accountablehq.com/post/ehr-access-controls-what-they-are-how-to-implement-them-and-hipaa-best-practices)
- Elevación just-in-time con expiración automática y cuentas de emergencia dedicadas, separadas de las de administración habitual — [Accountable PAM](https://www.accountablehq.com/post/healthcare-privileged-access-management-best-practices-practical-steps-to-protect-ehrs-and-meet-hipaa-compliance); [Avatier](https://www.avatier.com/blog/emergency-access-passwords/)
- Riesgo principal: que el break-glass se normalice y se vuelva rutina. Hay que conciliar los eventos contra la necesidad clínica y ensayarlo antes de un incidente. No existe un estándar universal de duración — [nhimg break-glass](https://nhimg.org/faq/what-should-teams-get-right-about-break-glass-access-for-patient-data/); [nhimg hospitals](https://nhimg.org/faq/how-should-hospitals-balance-strong-identity-controls-with-emergency-access-need/)

**SSO/IdP de bajo costo**
- Keycloak federa usuarios desde LDAP y Active Directory y soporta OIDC, OAuth2 y SAML — [Keycloak Server Admin](https://www.keycloak.org/docs/25.0.0/server_admin/); [OneUptime Keycloak AD](https://oneuptime.com/blog/post/2026-01-25-keycloak-identity-management/markdown)
- Caso CNCF: Keycloak da SSO a más de 200.000 usuarios de una plataforma de salud en Japón (web, escritorio y nativas), integrada con el sistema nacional de receta electrónica — [CNCF case study](https://www.cncf.io/case-studies/infosys-ltd-client-5/)
- Caso CNCF: IFTM (instituto público brasileño) moderniza su autenticación con Keycloak e integración Gov.br, un referente latinoamericano de federación con identidad estatal — [CNCF IFTM](https://www.cncf.io/case-studies/iftm/)
- Microsoft My Apps: aunque no todas las apps estén migradas, se puede usar "Linked SSO" (un tile que solo enlaza) y migrar gradualmente a SSO real — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)

**Ciclo de vida y revisiones (CIS Controls)**
- CIS v8: retener los logs de auditoría al menos 90 días (Safeguard 8.10, aparentemente IG2). Deshabilitar las cuentas sin uso por 90 días o más (5.3, numeración de fuente secundaria) — [Tripwire CIS](https://www.tripwire.com/node/25254); [Bastion CIS v8 list](https://bastion.tech/learn/cis-controls/cis-controls-v8-list)

### Inferences
- **[E] IdP estándar OIDC (y SAML si hace falta) que emita tokens a los módulos**, para que no reautentiquen ni reciban la clave. Ruta realista: Keycloak autoalojado como IdP, con el portal como cliente OIDC; los módulos validan el token JWT o usan el flujo Authorization Code + PKCE. Mientras tanto, los "tiles enlazados" (Linked SSO) son aceptables como transición.
- **[E] Federación con Active Directory del hospital** (Keycloak, proveedor LDAP en solo lectura), para que el alta y la baja vengan del directorio y no de un CRUD paralelo. Si el Servicio de Salud usa Entra ID/M365, se puede federar OIDC contra Entra.
- **[E] Joiner-mover-leaver ligado a RR.HH. (SIRH/planilla)**: baja automática al término del contrato, cambio de rol al trasladarse y desactivación por inactividad de 90 días. Hoy depende de la acción manual del admin.
- **[E] Ajustar la política de contraseñas a NIST 800-63B-4**: mínimo 15 caracteres mientras no haya MFA (u 8 con MFA), máximo de 64 o más, lista de bloqueo (claves filtradas como HIBP k-anonymity offline, más una lista local como "Fricke2026" o el RUT), sin composición forzada y sin rotación periódica. El bloqueo a los 5 fallos es más estricto que NIST (100); es aceptable, pero conviene un bloqueo temporal progresivo para evitar DoS contra cuentas y llamadas a la mesa de ayuda.
- **[E] MFA al menos para administradores, DPD y acceso remoto o desde fuera de la red**, en línea con la política del NHS. TOTP es lo más barato; WebAuthn/passkeys o FIDO2 es la opción resistente a phishing (llaves de ~USD 25–50 para admins). En estaciones clínicas, más que MFA en cada login, conviene un login rápido con tarjeta de proximidad, que ya suele existir como credencial de funcionario.
- **[R] Tap-and-go con tarjeta de proximidad** en las estaciones de urgencia y pabellón. El costo de Imprivata puede ser alto; una alternativa son lectores RFID con un plugin de IdP, PIN más badge. Los ahorros de 15–60 min por turno son cifras de proveedor.
- **[E] Break-glass formal** si algún módulo expone datos clínicos: motivo obligatorio, duración limitada, alerta al DPD o a seguridad, y revisión mensual. El registro con cadena hash existente es una buena base.
- **[R] Revisión periódica de accesos** (trimestral para roles privilegiados, semestral para el resto) con atestación del jefe de servicio, más registro de excepciones MFA.
- **[R] PAM liviano**: cuentas de admin separadas de las personales, step-up para acciones administrativas y sin cuentas compartidas.
- **[E] Estaciones compartidas**: el bloqueo con Ctrl+Alt+L y el timeout de 15 min están alineados. Falta un "cambiar de usuario" que limpie todo el estado del cliente (localStorage, caché) y forzar el timeout en el servidor (verificarlo).

### Gaps
- No se obtuvo el texto oficial de OWASP ASVS 5.0 (V6/V7, autenticación y sesión); solo v4.
- No se verificó qué Safeguards de CIS v8.1 en IG1 exigen MFA.
- No se encontraron casos documentados de hospitales públicos chilenos con SSO/Keycloak ni tap-and-go. Se desconoce qué IdP usa el Servicio de Salud Viña del Mar–Quillota o MINSAL.
- No se encontró una guía primaria (HIPAA o NIST) específica de break-glass; las fuentes son de consultoría.

## 2. Lanzador y patrón de ecosistema de apps

### Takeaway
Los lanzadores maduros (Microsoft My Apps) combinan cuatro cosas: visibilidad por asignación (rol o grupo), colecciones personalizables, búsqueda y solicitud de acceso con flujo de aprobación. Fricke Store ya tiene visibilidad por rol y un registro de módulos con ficha de privacidad, una ventaja frente a My Apps. Le faltan búsqueda, favoritos y colecciones, solicitud de acceso a módulos, notificaciones y emisión de tokens a los módulos.

### Cited Findings
- My Apps muestra una app solo si es "visible" **y** está asignada al usuario o grupo. Las propiedades de la app son nombre, URL de inicio, logo, "habilitada para login" y "visible" — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)
- Los usuarios pueden buscar, cambiar entre vista lista y cuadrícula, crear colecciones propias y ocultar o reordenar colecciones. Los admins crean colecciones por rol, tarea o proyecto — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)
- Hay autoservicio de acceso: el usuario solicita, la solicitud va a un grupo, el dueño del grupo aprueba y los aprobadores reciben la notificación en el portal — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)
- Los admins configuran experiencias de consentimiento, incluidos términos de servicio, y branding — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)
- El usuario puede revisar y revocar los permisos que consintió a cada app ("Manage your application") — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)
- Se recomienda habilitar SSO para todas las apps del portal cuando sea posible, migrando gradualmente desde Linked SSO — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)

### Inferences
- **[E] Contrato de onboarding de módulos**: ficha (dueño funcional y técnico, finalidad, categorías de datos, EIPD, roles), registro como cliente OIDC en el IdP con redirect URIs y scopes, y checklist de seguridad mínima antes de publicar. Fricke Store ya tiene la ficha de privacidad y el gate EIPD; falta la parte técnica (client_id/secret, scopes, URL de health).
- **[E] Emisión de tokens a los módulos (OIDC/JWT)** con claims de rol y unidad, en lugar de compartir la sesión del portal.
- **[R] Página de estado de módulos** (health check periódico a /health de cada módulo, con banner en el tile cuando el módulo está caído o en mantención).
- **[R] Búsqueda global, favoritos y recientes, y colecciones por servicio clínico** (Urgencia, Pabellón, Administrativo). Es lo estándar en My Apps y en el lanzador de Google Workspace.
- **[R] Solicitud de acceso a un módulo con aprobación del jefe directo o del dueño del módulo**, reutilizando el flujo de solicitudes existente.
- **[R] Centro de notificaciones y anuncios** (avisos institucionales, mantenciones, resultado de solicitudes), más correo vía SMTP institucional para reseteos y aprobaciones. Hoy no hay correo.
- **[R] Integración con mesa de ayuda** (botón "Reportar problema" que crea un ticket con el contexto del módulo) y feedback por módulo.
- **[R] Chat IA**: hoy es un mock. Antes de conectarlo a un LLM real se necesita EIPD, una regla de no ingresar datos de pacientes y un registro de uso.

### Gaps
- No se obtuvo documentación primaria del lanzador de Google Workspace ni de Epic Hyperspace/Haiku launchers (búsqueda no realizada por límite de llamadas).
- No se encontraron fuentes con métricas de adopción de páginas de estado o de centros de notificación en intranets hospitalarias.

## 3. Operaciones (respaldos, DR, HA, base de datos, monitoreo, logs, entornos, CI/CD, escaneo, pentest)

### Takeaway
Para un portal que pasa a ser la puerta de entrada (SSO), la identidad se vuelve un sistema crítico de nivel 1: las referencias de consultoría sugieren un RTO de alrededor de 1 h para identidad/SSO. Los mínimos realistas son seis: migrar de SQLite a PostgreSQL, respaldos automáticos cifrados con una copia inmutable o fuera de línea, restauración probada, monitoreo y alertas, logs centralizados con retención de 90 días o más, y separación dev/staging/prod con CI.

### Cited Findings
- Las metas de RTO y RPO en salud varían según la fuente (todas son de consultoría, no normas). Un ejemplo de niveles: clínico crítico RPO <1 min / RTO <15 min, administrativo RPO <15 min / RTO <2 h, archivo 24 h — [Censinet RTO/RPO](https://censinet.com/perspectives/ransomware-recovery-setting-rto-rpo)
- Otra fuente: EHR con RTO 2 h / RPO 15 min, **identidad/SSO con RTO 1 h**, y sistemas administrativos no críticos con RTO de 24–72 h — [Accountable EHR DR](https://www.accountablehq.com/post/ehr-disaster-recovery-best-practices-rto-rpo-and-hipaa-compliance)
- Las metas deben salir de un análisis de impacto (BIA) y de procedimientos de contingencia probados. Ejemplo: el ataque a Scripps Health (2021) mantuvo el EHR caído cerca de 4 semanas — [Censinet](https://censinet.com/perspectives/ransomware-recovery-setting-rto-rpo); [Accountable DR guide](https://www.accountablehq.com/post/healthcare-disaster-recovery-guide-best-practices-templates-and-checklist)
- Se recomiendan copias inmutables, fuera de línea o air-gapped contra ransomware — [Censinet backup automation](https://censinet.com/perspectives/ultimate-backup-automation-guide-healthcare); [Accountable backups](https://www.accountablehq.com/post/data-backup-best-practices-for-hospitals-hipaa-compliant-strategies-for-ehr-protection-and-continuity)
- NHS CAF-aligned DSPT: proteger los respaldos del acceso no autorizado y la manipulación, definir retención y ubicación, mantener copias segregadas o fuera de línea, probar respaldos y restauraciones a intervalos planificados y tras cambios mayores, y registrar y remediar las fallas de restauración — [NHS CAF-aligned DSPT](https://nhsd-proxy.openprescribing.net/cyber-and-data-security/guidance-and-resources/caf-aligned-dspt-guidance/overview/introduction); [NHS England board assurance](https://www.england.nhs.uk/long-read/board-and-executive-assurance-cyber-security-risk/)
- SQLite (proyecto oficial): si los datos están separados de la aplicación por una red, conviene una base cliente/servidor. SQLite admite un solo escritor a la vez por archivo — [sqlite.org use over net](https://sqlite.org/useovernet.html); [SQLite appropriate uses](https://hci-sqlite-page.pages.dev/whentouse.html)
- Escalar réplicas de la aplicación no convierte un SQLite compartido en una base distribuida — [dbpro SQLite vs PostgreSQL](https://www.dbpro.app/learn/sqlite/guides/sqlite-vs-postgresql)
- CIS v8: retención de logs de auditoría de 90 días como mínimo (8.10) — [Tripwire CIS](https://www.tripwire.com/node/25254)
- HHS 405(d) HICP: 10 prácticas con subprácticas por tamaño (Vol. 1 para organizaciones pequeñas, Vol. 2 para medianas y grandes), alineables con NIST CSF — [Industrial Cyber HICP](https://industrialcyber.co/medical/hhs-hicp-document-improves-cybersecurity-posture-focuses-on-zero-trust-defense-in-depth-strategies/); [Clearwater HICP 2023](https://clearwatersecurity.com/blog/evolving-healthcare-cybersecurity-practices-the-2023-updates-to-405d-hicp/)
- Chile, Ley 21.663 (Marco de Ciberseguridad): la ANCI opera desde el 1-ene-2025. Desde el 1-mar-2025 rigen la calificación de OIV, la obligación de notificar incidentes al CSIRT Nacional (reglamento DS 295/2024) y las sanciones. Los OIV deben tener un sistema de gestión de seguridad continuo y planes de continuidad — [BCN Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434); [AZ reglamento reporte](https://www.az.cl/ley-marco-de-ciberseguridad-claves-del-reglamento-de-reporte-de-incidentes/); [Garrigues](https://www.garrigues.com/node/15320)
- Calificación OIV: hubo una lista preliminar en sep-2025 y una segunda etapa por Res. Exenta N°187 del 24-jul-2026 — [Cariola sep-2025](https://www.cariola.cl/app/uploads/2025/09/Alerta-legal-17Sept-1.pdf); [Guerrero OIV 2026](https://guerrero.cl/wp-content/uploads/2026/07/DOC_Nuevos_OIV-1.pdf)
- Ley 21.719 (datos personales): vigencia prevista el 1-dic-2026. Hay un proyecto de postergación (a dic-2027 o 15-oct-2027 según la fuente) aún en trámite; mientras no se publique, rige la fecha original — [Diario Constitucional](https://www.diarioconstitucional.cl/2026/06/12/la-ley-21-719-entra-en-vigor-el-1-de-diciembre-y-expone-vacios-en-regulacion-de-pequenas-empresas/); [IAPP](https://iapp.org/news/a/protecci-n-de-datos-personales-puntos-pendientes-antes-de-la-entrada-en-vigor-de-la-reforma-en-chile); [Guía digital.gob.cl](https://wikiguias.digital.gob.cl/datos-personales/guia-practica-implementacion-nueva-ley-datos-personales)

### Inferences
- **[E] Migrar a PostgreSQL** antes de la producción con 2.000 usuarios y varios módulos escribiendo (sesiones, auditoría, solicitudes). Keycloak también requiere PostgreSQL en producción.
- **[E] Respaldos automatizados** con la regla 3-2-1: pg_dump diario y WAL archiving con RPO ≤15 min, cifrados, con una copia fuera del servidor y otra inmutable o offline. **Prueba de restauración trimestral documentada.**
- **[E] Metas propuestas**: portal/IdP con RTO ≤1 h y RPO ≤15 min (el portal se vuelve la puerta de entrada); módulos administrativos con RTO ≤24 h. Validar con un BIA del hospital.
- **[E] Procedimiento de contingencia** si el portal cae: acceso directo a los módulos críticos con credenciales locales de emergencia (break-glass técnico) documentado y probado.
- **[R] Alta disponibilidad**: dos nodos de aplicación detrás de un proxy, PostgreSQL con réplica en standby y Keycloak en clúster. Como mínimo, una VM con snapshot y un plan de reconstrucción automatizado (infraestructura como código).
- **[E] Monitoreo y alertas**: uptime externo (Uptime Kuma), métricas (Prometheus/Grafana o Zabbix, que suele estar ya en hospitales), alertas de logins fallidos masivos, certificados por vencer y disco.
- **[E] Logs centralizados** (Graylog, Wazuh o Loki) con retención de 90 días en caliente y retención más larga para la auditoría de accesos. La cadena hash existente se mantiene, con exportación periódica del hash raíz a un medio externo. Wazuh es SIEM open source.
- **[E] Entornos separados dev/staging/prod**, sin datos reales en dev (usar datos sintéticos).
- **[E] CI/CD** con pruebas, SAST (Semgrep/Bandit), escaneo de dependencias (pip-audit, Dependabot/OSV), escaneo de imágenes (Trivy) y despliegue reproducible.
- **[R] Pentest externo antes de la puesta en producción y luego anual**, o tras cambios mayores; se puede apoyar en el CSIRT de Gobierno o en la ANCI cuando corresponda.
- **[E] Procedimiento de notificación de incidentes** alineado con la Ley 21.663 (si el hospital o su Servicio de Salud es calificado como servicio esencial u OIV) y con la Ley 21.719 (brechas de datos).

### Gaps
- No se verificó si el Hospital Dr. Gustavo Fricke o su Servicio de Salud figura en la lista OIV de la ANCI (Res. Ex. 187/2026); hay que revisarlo directamente.
- No se encontró una norma técnica chilena (MINSAL o ANCI) con RTO/RPO obligatorios para sistemas hospitalarios; las cifras son de consultoría de EE.UU.
- No se obtuvieron los textos primarios del HHS 405(d) HICP Technical Volumes (subprácticas de backup y acceso).

## 4. UX y accesibilidad para personal clínico

### Takeaway
El estándar de referencia es WCAG 2.2 AA, obligatorio en el sector público del NHS para servicios a pacientes **y a personal**. Los criterios nuevos más relevantes para un portal con login son 3.3.8 (Autenticación accesible), 2.5.8 (Tamaño de objetivo de 24×24 px) y 2.4.11 (Foco no oculto). Las prácticas de estación compartida (login rápido, limpieza de contexto) son también un tema de UX.

### Cited Findings
- NHS: como organismo público, existe el deber legal de cumplir WCAG nivel AA en todos los servicios para pacientes y para personal. WCAG 2.2 agrega 9 criterios, 6 de ellos de nivel A/AA — [NHS Service Manual WCAG 2.2](https://service-manual.nhs.uk/accessibility/new-criteria-in-wcag-2-2); [NHS what all services need to do](https://service-manual.nhs.uk/accessibility/what-all-nhs-services-need-to-do)
- El estándar NHS para soluciones web (incluidas intranets/extranets) exige WCAG 2.2 AA o superior — [NHS standards WCAG 2.2](https://standards.nhs.uk/published-standards/web-content-accessibility-guidelines-22); [NHSE DSIC](https://nhse-dsic.atlassian.net/wiki/spaces/DCSDCS/pages/15040184321/Accessibility+Standard+Web+Based)
- 3.3.8 Accessible Authentication (Minimum, AA): no exigir pruebas cognitivas como memorizar o transcribir sin alternativa. Permitir pegar o usar gestores de contraseñas es la vía usual. 2.5.8: objetivos ≥24×24 CSS px. 2.4.11: el elemento con foco no debe quedar oculto — [Deque WCAG 2.2](https://dequeuniversity.com/resources/wcag-2.2); [BOIA](https://www.boia.org/blog/whats-new-in-wcag-2.2-new-success-criteria-for-digital-accessibility); [AbilityNet](https://abilitynet.org.uk/node/2849)
- Algunas fuentes secundarias confunden la numeración (3.3.7 es Redundant Entry, no Autenticación accesible) — [Deque WCAG 2.2](https://dequeuniversity.com/resources/wcag-2.2)
- El login lento al inicio del turno es un problema reconocido en hospitales; motivó proyectos "tap-and-go" — [Imprivata RUH Bath](https://www.imprivata.com/sites/imprivata/files/2021-04/OS-CSS-bath-royal-UK-0720.pdf)

### Inferences
- **[E] WCAG 2.2 AA** como meta declarada, con una declaración de accesibilidad publicada en el portal. En el login: permitir pegar en el campo de clave, `autocomplete="username"/"current-password"`, mostrar y ocultar la clave, y no usar CAPTCHA cognitivo.
- **[E] Diseño responsive móvil-primero** (celular personal en pasillo o turnos), tiles ≥24 px (idealmente ≥44 px para tacto) y alto contraste para pantallas en salas iluminadas.
- **[E] Velocidad**: el lanzador debe cargar en menos de ~2 s en las estaciones antiguas del hospital (presupuesto de JS pequeño, sin frameworks pesados). Medir con Lighthouse en un equipo real del hospital.
- **[R] Tolerancia offline**: cachear la shell del lanzador (service worker) y mostrar un mensaje claro de "módulo no disponible" con el procedimiento de contingencia, sin cachear datos personales en las estaciones compartidas.
- **[E] Lenguaje claro en español chileno**: mensajes de error accionables ("Su clave debe tener al menos 15 caracteres", no "Error 400") y glosario de términos de privacidad (EIPD, ARCO).
- **[R] Onboarding**: un tour breve en el primer ingreso, videos de menos de 2 min por módulo, "campeones digitales" por servicio clínico y material de capacitación en la inducción de funcionarios nuevos.

### Gaps
- No se encontró una norma chilena explícita que obligue WCAG 2.2 AA en intranets públicas. Existe la Ley 20.422 y guías de Gobierno Digital, pero no se verificaron en esta investigación.
- No se encontraron estudios de usabilidad de lanzadores en hospitales latinoamericanos.

## 5. Gobernanza (cambios, comité de aprobación de módulos, documentación, soporte)

### Takeaway
Las referencias maduras (NHS DSPT/CAF, HICP, Ley 21.663) piden un responsable de seguridad, gestión de riesgos, planes de continuidad, registro de excepciones y aseguramiento a nivel de dirección. Para un ecosistema de módulos, esto se traduce en cuatro piezas: un comité de aprobación de módulos que use el gate EIPD existente, gestión de cambios con ventanas de mantención anunciadas, un modelo de soporte en niveles y documentación viva.

### Cited Findings
- NHS England pide aseguramiento del riesgo cibernético a nivel de directorio y ejecutivo — [NHS England board assurance](https://www.england.nhs.uk/long-read/board-and-executive-assurance-cyber-security-risk/)
- El DSPT alineado al CAF se evalúa por resultados (outcomes) con auditoría independiente — [NHS CAF-aligned DSPT audit guide](https://nhsd-proxy.openprescribing.net/cyber-and-data-security/guidance-and-resources/caf-aligned-dspt-guidance/audit-guides/strengthening-assurance-independent-assessment-and-audit-guide/executive-summary)
- La política MFA del NHS exige un registro de excepciones — [NHS England MFA policy](https://nhsd-proxy.openprescribing.net/cyber-and-data-security/guidance-and-resources/multi-factor-authentication-mfa-policy/nhs-england-multi-factor-authentication-policy)
- Los OIV (Ley 21.663) deben implementar un sistema de gestión de seguridad de la información continuo y planes de continuidad — [BCN Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)
- Las metas de RTO/RPO deben reflejarse en contratos con proveedores, procedimientos de contingencia y ventanas de mantención — [Censinet](https://censinet.com/perspectives/ransomware-recovery-setting-rto-rpo)
- HICP es reconocido por la OCR (EE.UU.) como "práctica de seguridad reconocida" si lleva 12 meses implementado; sirve como marco de referencia por tamaño de organización — [CASRAI healthcare cybersecurity](https://casrai.org/guides/healthcare-cybersecurity)

### Inferences
- **[E] Comité de aprobación de módulos** (Innovación, TI, DPD, Seguridad y un representante clínico) que revise cinco cosas antes de publicar: finalidad y datos (ficha existente), EIPD, checklist de seguridad (OIDC, logs, respaldos), dueño funcional y plan de soporte. También retira los módulos sin dueño.
- **[E] Gestión de cambios**: cambios normales con aprobación y ventana anunciada en el portal, cambios de emergencia con revisión posterior y registro de versiones (changelog visible).
- **[E] Modelo de soporte**: N1 mesa de ayuda (reseteos, que ya existen), N2 Innovación/TI y N3 desarrollador o proveedor del módulo, con horario y escalamiento para urgencias 24/7, dado que el portal será puerta de entrada.
- **[R] SLA interno publicado** (p. ej. 99,5% de disponibilidad mensual en horario hábil, e incidentes P1 atendidos en menos de 1 h).
- **[E] Documentación**: arquitectura, runbooks (restaurar respaldo, rotar secretos, alta de módulo), registro de actividades de tratamiento (Ley 21.719), política de contraseñas y MFA, y procedimiento de break-glass.
- **[R] Autoevaluación anual** contra NIST CSF 2.0 o CIS IG1/IG2, más un pentest. Usar HICP Vol. 2 como lista de chequeo de prácticas para organizaciones medianas y grandes.

### Gaps
- No se encontraron directrices MINSAL específicas sobre gobierno de portales o intranets.
- No se revisaron documentos HIMSS (EMRAM/INFRAM) por límite de llamadas. INFRAM sería relevante para infraestructura, HA y DR.

## 6. Referencias de portales y lanzadores existentes

### Takeaway
Los referentes útiles son tres: Microsoft My Apps (patrón funcional del lanzador), NHS CIS2 con su abanico de autenticadores (modelo de identidad nacional en salud con smartcard, Windows Hello y passkeys) e Imprivata (SSO clínico y tap-and-go, costoso). Keycloak aparece como opción open source con casos en salud (Japón) y en el sector público latinoamericano (Brasil, Gov.br).

### Cited Findings
- Microsoft My Apps: visibilidad por asignación, colecciones, búsqueda, solicitudes de acceso con aprobación, Linked SSO como transición y límite de 950 apps por usuario — [Microsoft Learn My Apps](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/myapps-overview)
- NHS CIS2: identidad única para el personal sanitario con múltiples autenticadores (smartcard, Windows Hello, passkeys, llaves de seguridad) — [NHS CIS2 authenticators](https://nhsd-proxy.openprescribing.net/services/care-identity-service/applications-and-services/cis2-authentication/authenticators); [NHS England CIS2](https://www.england.nhs.uk/nhs-care/)
- Imprivata OneSign / Enterprise Access Management: SSO clínico y tap-and-go con casos NHS (Harrogate, RUH Bath), en Irlanda (Tallaght) y en EE.UU. (CHRISTUS) — [Imprivata Harrogate](https://imprivata.com/sites/imprivata/files/2024-12/Harrogate%20and%20District%20NHS%20Foundation%20Trust%20%20improves%20clinical%20workflow%20efficiencies%20with%20%20Imprivata%2C%20benefiting%20both%20staff%20and%20patients.pdf); [Imprivata RUH 2026](https://www.imprivata.com/sites/imprivata/files/2026-04/3768-2026_EAM-CS-royal-united-hospitals.pdf)
- Imprivata soporta el flujo de virtual smartcards del NHS Spine — [Imprivata docs Spine virtual smartcards](https://docs.imprivata.com/onesign/content/topics/onesign/authentication_management/spinevirtualsmartcards.html)
- Keycloak: SSO para más de 200.000 usuarios de salud en Japón; IFTM (Brasil) con Gov.br — [CNCF Japan](https://www.cncf.io/case-studies/infosys-ltd-client-5/); [CNCF IFTM](https://www.cncf.io/case-studies/iftm/)

### Inferences
- Fricke Store puede posicionarse como un "My Apps hospitalario" con capa de privacidad: el registro de módulos con EIPD y la auditoría con cadena hash son diferenciadores que My Apps no trae nativamente.
- Para Chile, el análogo de la federación Gov.br sería ClaveÚnica, pero para funcionarios lo pertinente es el AD institucional. ClaveÚnica solo aplicaría a portales para pacientes (no verificado).

### Gaps
- No se recopilaron fuentes primarias sobre Epic Hyperspace/Haiku launchers, el lanzador de Google Workspace ni portales de hospitales públicos latinoamericanos (p. ej. Hospital Digital de MINSAL o Hospital Italiano de Buenos Aires); quedan pendientes.
