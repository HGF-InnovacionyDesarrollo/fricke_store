# Gobierno digital, transparencia, firma electrónica, accesibilidad y compras públicas aplicables a "Fricke Store" (Hospital Dr. Gustavo Fricke, SS Viña del Mar-Quillota)

> Notas de investigación al 16-nov-2026. Fuentes primarias leídas en texto completo: DS 7, 9 y 11 de 2023 (Segpres, Diario Oficial 17-08-2023) e Instructivo Presidencial de Transformación Digital del 24-01-2019. LeyChile/BCN no cargó (requiere JavaScript), así que la Ley 21.180, el DFL 1/2020, la Ley 19.799, la Ley 20.285, la Ley 20.422, la Ley 21.634 y el DS 1/2015 **no se leyeron en texto oficial en esta sesión**. Lo que se afirma sobre ellos sin cita va en "Inferencias" o "Brechas".

## 1. Ley 21.180 y normas técnicas de 2023: ¿qué aplica a un portal interno frente a un servicio ciudadano? ¿ClaveÚnica? ¿Calendario?

### Conclusión
Las seis normas técnicas (DS 7 a 12 de 2023, Segpres) definen "usuarios" de forma que **incluyen a los funcionarios que acceden a plataformas que soportan procedimientos administrativos "o procesos relacionados con estos"**. Por eso un portal interno de SSO que da acceso a sistemas de gestión documental, expedientes o comunicaciones oficiales queda dentro de su alcance, aunque no sea un trámite ciudadano. ClaveÚnica es el mecanismo oficial obligatorio para **interesados personas naturales** (por ejemplo, pacientes en el futuro). La norma no exige ClaveÚnica a los funcionarios ni crea una "ClaveÚnica Funcionaria". Aun así, sí impone requisitos técnicos y de trazabilidad a toda autenticación de la plataforma.

### Hallazgos con cita
**Identificación de las normas técnicas.** Las seis son del Ministerio Secretaría General de la Presidencia, todas dictadas en Santiago el 19-05-2023 y publicadas en el Diario Oficial N.º 43.629 del 17-08-2023:
- DS N.º 7: Seguridad de la Información y Ciberseguridad — [DO CVE 2361371](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- DS N.º 8: Notificaciones — [DO CVE 2361372](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361372.pdf)
- DS N.º 9: Autenticación — [DO CVE 2361373](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf); [BCN](https://www.bcn.cl/leychile/navegar?i=1195122)
- DS N.º 10: Documentos y Expedientes Electrónicos — [DO CVE 2361374](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361374.pdf); [BCN](https://www.bcn.cl/leychile/navegar?idNorma=1195123)
- DS N.º 11: Calidad y Funcionamiento de las plataformas electrónicas — [DO CVE 2361375](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- DS N.º 12: Interoperabilidad — [DO CVE 2361376](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361376.pdf); [BCN](https://www.bcn.cl/leychile/navegar?idNorma=1195125)

**Marco general**
- Las normas técnicas tienen su fuente en el Reglamento DS N.º 4/2020 Segpres, que ordenó dictar seis normas técnicas. La gradualidad la fija el DFL N.º 1/2020 Segpres (considerandos 2 a 4 del DS 9) — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Definición de "Usuarios" (art. 2 N.º 7 DS 9; idéntica en el art. 2 N.º 9 DS 11 y en el DS 7):** comprende a los interesados de un procedimiento administrativo y también a "los(as) funcionarios(as) que acceden a las plataformas electrónicas que soportan procedimientos administrativos o procesos relacionados con estos". "Plataforma electrónica" se define como "software o conjunto de software, datos e infraestructura tecnológica que sustenta procesos o procedimientos" — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf); [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- El DS 11 rige no solo para las plataformas que sustentan procedimientos, sino también para "aquellas plataformas o sistemas informáticos que se interconecten, integren, interoperen o permitan el acceso" a las plataformas de gestión de expedientes electrónicos y a la plataforma de comunicaciones oficiales — [DS 11, encabezado del decreto](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)

**DS 9 (Autenticación)**
- **Art. 3:** los órganos deben usar mecanismos oficiales de autenticación para el acceso de **los interesados** a sus plataformas. Si la normativa no permite usar uno, pueden usar otro mecanismo, pero con autorización expresa previa de Segpres — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 4:** ClaveÚnica es "de uso exclusivo para personas naturales", se basa en OpenID Connect y está vinculada al RUN. La administra la División de Gobierno Digital (DGD) y el enrolamiento lo hace el Registro Civil. El jefe superior del servicio debe aceptar los términos y condiciones — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf). Los términos de uso vigentes son la Res. Ex. N.º 733/2025 — [wikiguias](https://wikiguias.digital.gob.cl/documentos/rex._733_e6606_2025_aprueba_t%C3%A9rminos_de_uso_de_clave%C3%BAnica.pdf); [BCN](https://www.bcn.cl/leychile/navegar?idNorma=1218250)
- **Art. 5:** Clave Tributaria es solo para personas jurídicas. Ningún órgano distinto del SII puede usarla para autenticar personas naturales — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 6 (estándares técnicos):** OpenID Connect y OAuth 2.0 o superiores; credenciales almacenadas con Bcrypt, PBKDF2, SHA-3 o Argon2 o superiores; transmisión con TLS 1.2 o superior; registros trazables. Estos estándares se dirigen a los "mecanismos oficiales", pero son la referencia técnica estatal — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 7:** CAPTCHA u otro mecanismo de prevención, límite de intentos fallidos con bloqueo y un procedimiento de desbloqueo (exigido a quien administra un mecanismo oficial) — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 8:** buenas prácticas de experiencia de usuario y accesibilidad web en el proceso de autenticación. Si se integra ClaveÚnica, hay que respetar la marca y los lineamientos gráficos del administrador — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 10:** se deben usar mecanismos oficiales "en sus plataformas electrónicas que requieran autenticación". La integración tiene tres etapas: solicitud, entrega de credenciales e integración, y certificación y habilitación — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 12:** ante sospecha de riesgos o amenazas, hay que informar de inmediato al CSIRT (hoy en la ANCI; ver brechas) y al administrador del mecanismo — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 13:** registro de accesos para trazabilidad con, al menos, el identificador del usuario y la fecha y hora en **UTC+00:00**, sincronizada con el Servicio Hidrográfico y Oceanográfico de la Armada (SHOA) — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 14:** protección de datos personales y derechos de acceso, rectificación, cancelación y oposición conforme a la Ley 19.628 — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 15:** se pueden agregar factores de autenticación adicionales (MFA), "especialmente en plataformas electrónicas que permitan el acceso a información personal de carácter sensible" — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Arts. 16 a 18:** un órgano puede pedir a Segpres que reconozca un **nuevo mecanismo oficial** (previa consulta al Registro Civil). Debe cumplir los estándares y contar con enrolamiento seguro, gestión de credenciales y soporte — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- **Art. 20:** la gradualidad sigue el DFL 1/2020. **Art. 21:** la norma se revisa al menos cada dos años — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)

**DS 11 (Calidad y funcionamiento)**
- **Art. 3:** catálogo de plataformas electrónicas con línea de base, obligatorio antes del Ciclo de Gestión de la Calidad — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- **Arts. 4 a 11:** Plan de Mejora Continua en cinco etapas (plan, formulación presupuestaria, implementación, evaluación, ajustes). Incluye un mínimo de cuatro subcaracterísticas de calidad con métricas y umbrales, y una estimación de la vida útil según el principio de actualización del art. 16 bis de la Ley 19.880. El plan debe considerar la "Guía de Lineamientos para el Desarrollo de Software" de la DGD — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- **Arts. 12 a 14:** los proyectos TIC que requieran presupuesto pasan por **EvalTIC** (Dipres con DGD, Secretaría de Modernización y ChileCompra), cuya evaluación es **vinculante** para la formulación presupuestaria — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- **Arts. 15 y 16:** cada jefe superior de servicio designa un **Coordinador(a) de Transformación Digital**, que reporta al jefe de servicio y a la DGD — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- El DS 11 **no contiene requisitos de accesibilidad ni de WCAG**. Su contenido es obsolescencia, continuidad, niveles de servicio, soporte y términos de uso (art. 1) — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)

**DS 7 (Seguridad y ciberseguridad)**
- Exige un diagnóstico inicial (art. 4) y una Política de Seguridad de la Información y Ciberseguridad (arts. 3 y 5). Organiza el trabajo en funciones; la de identificación incluye la categoría "contratación y gestión de la relación con proveedores de servicios en la nube" (art. 7), y la de protección incluye gestión de servidores, redes, autenticación y control de acceso (art. 8). Se revisa cada dos años — [DS 7](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)

**Instructivo Presidencial del 24-01-2019**
- El Servicio de Salud Viña del Mar-Quillota figura en la distribución. Ordena que los servicios, "en sus plataformas digitales de trámites o servicios", usen solo ClaveÚnica para personas naturales, reemplazando los sistemas propios. Esto incluye la verificación de identidad para ejercer derechos de la Ley 19.628 (punto 1.b). Fijaba la implementación total a más tardar en 2020 (1.c) — [Instructivo](https://www.alejandrobarros.com/wp-content/uploads/2019/02/Instructivo-Transformacion-Digital.pdf)

**Calendario**
- La implementación se divide en grupos A, B y C. El grupo A incluye ministerios, servicios públicos no comprendidos en B o C, la Contraloría y las FF.AA. y de orden; B y C corresponden a gobiernos regionales y municipios — [Alejandro Barros, 15-04-2026](https://www.alejandrobarros.com/ley-21-180-cumpliremos-el-2027/); [G&A Abogados](https://www.ga-abogados.cl/principales-aspectos-del-dfl-1-que-establece-normas-de-aplicacion-del-articulo-1-de-la-ley-21-180-de-transformacion-digital-del-estado/)
- Fechas de término según un análisis secundario de abril de 2026: la aplicación completa es en 2026 para el grupo A y en 2027 para B y C. La adopción del notificador (Domicilio Digital Único) es en diciembre de 2026 para el grupo A y diciembre de 2027 para B y C. Las fases 2, 3 y 6 requieren ClaveÚnica activa — [Alejandro Barros](https://www.alejandrobarros.com/ley-21-180-cumpliremos-el-2027/)
- Otra fuente sitúa la implementación completa al 31-12-2027 tras la reforma de la Ley 21.464 (2022) — [búsqueda: Carey](https://www.carey.cl/publican-reglamento-de-ley-21-180-sobre-transformacion-digital-del-estado); [ACHM 2026](https://www.achm.cl/uploads/docs/2025/12/Ley-N%C2%B021.180.pdf). **Hay conflicto entre fuentes**: 2026 para el grupo A frente a 2027 como fecha general.
- La misma fuente pone a los "servicios de salud regionales" en la categoría "en riesgo" de cumplimiento del tablero de la DGD — [Alejandro Barros](https://www.alejandrobarros.com/ley-21-180-cumpliremos-el-2027/)

### Inferencias
- Los Servicios de Salud son servicios públicos descentralizados de la Administración Central, así que muy probablemente están en el **Grupo A**. Con eso, el plazo final más probable es el **31-12-2026**, que vence en semanas respecto de esta fecha de corte. Hay que confirmarlo con el texto vigente del DFL 1/2020.
- Para los funcionarios, el DS 9 no impone ClaveÚnica. Su art. 3 habla de "interesados", y la ClaveÚnica es para personas naturales que actúan como tales. El login RUT+contraseña propio es defendible para el personal si cumple los estándares de los arts. 6, 7, 13 y 15 como buena práctica: hash Argon2/bcrypt, TLS 1.2 o superior, bloqueo por intentos, bitácora en UTC y MFA para datos sensibles. Lo recomendable es OIDC/OAuth 2.0 internamente, idealmente federado con el directorio institucional (AD/Entra ID).
- Si el portal se abre a **pacientes**, tanto el DS 9 (art. 3) como el Instructivo de 2019 obligan a usar **ClaveÚnica** para personas naturales. Mantener una contraseña propia requeriría autorización expresa de Segpres.
- Como el portal es un SSO hacia otras plataformas, debe incluirse en el **catálogo de plataformas** del DS 11 (art. 3) y en el diagnóstico del DS 7, coordinado con el Coordinador de Transformación Digital del Servicio o del hospital.
- Si el desarrollo requiere presupuesto específico, aplica **EvalTIC**.

### Brechas
- No se encontró ninguna fuente oficial sobre una "ClaveÚnica Funcionaria" ni sobre un mecanismo oficial de identidad para funcionarios. No hay evidencia de que exista como norma.
- No se pudo leer el DFL 1/2020 en su versión vigente (BCN no carga), ni confirmar la tabla oficial de fases y años por grupo, ni si hubo nuevas prórrogas en 2025-2026.
- No se leyeron en esta sesión el DS 8 (Notificaciones), el DS 10 (Documentos y expedientes, incluida la firma) ni el DS 12 (Interoperabilidad: PISEE/Red de Interoperabilidad).
- Tampoco se verificó el traspaso del CSIRT de Gobierno a la ANCI bajo la Ley 21.663 Marco de Ciberseguridad, ni si los Servicios de Salud o el hospital fueron calificados como Operador de Importancia Vital. Esto debe investigarse por separado.

## 2. Ley 19.799 (firma electrónica): ¿cuándo se requiere FEA o FES? ¿Qué entrega FirmaGob?

### Conclusión
Los órganos del Estado certifican la **firma electrónica avanzada (FEA) de sus autoridades y funcionarios** mediante el modelo FirmaGob. Funciona con ministros de fe y un operador designados por cada institución (art. 9 de la Ley 19.799 y art. 40 de su reglamento). Los módulos del portal que emitan actos administrativos o documentos con valor de instrumento público necesitarán FEA. Los registros internos de trabajo pueden usar firma simple.

### Hallazgos con cita
- El art. 9 de la Ley 19.799 regula la certificación de las firmas de autoridades y funcionarios. Cada institución designa un **ministro de fe** y un **operador** que mantiene el registro de los funcionarios autorizados para solicitar certificados FEA (art. 40 del Reglamento de la Ley 19.799) — [Manual operador FirmaGob](https://wikiguias.digital.gob.cl/Manuales/manual-operador-firma); [Habilitación autoridad certificadora](https://wikiguias.digital.gob.cl/Manuales/habilitacion-autoridad-certificadora)
- En octubre de 2025 se publicó en el Diario Oficial un convenio para la FEA de autoridades y funcionarios en el marco de la Ley 19.799 — [DO 13-10-2025](https://www.diariooficial.interior.gob.cl/publicaciones/2025/10/13/44273/01/2708500.pdf) (contenido no leído)
- El Instructivo 2019 impuso la Política de Cero Papel, que exige que el 100 % de las comunicaciones oficiales entre órganos sea digital y pase por la plataforma compartida (DocDigital) o interopere con ella al 31-12-2019 (punto 3.d-e) — [Instructivo](https://www.alejandrobarros.com/wp-content/uploads/2019/02/Instructivo-Transformacion-Digital.pdf)

### Inferencias
- Regla general de la Ley 19.799, conocida pero no releída en esta sesión: la firma electrónica simple tiene el mismo valor que la manuscrita (art. 3). Los instrumentos públicos y los actos administrativos que exigen solemnidad requieren FEA (arts. 4 y 7).
- Ejemplos para Fricke Store: resoluciones, certificados, oficios, actas con efecto jurídico y documentos de expedientes del DS 10 deberían usar FEA (FirmaGob). Para registros de turnos, solicitudes internas o acuse de lectura de políticas basta con FES (autenticación + trazabilidad).
- La ficha clínica la rige otra normativa sanitaria (Ley 20.584 y DS 41/2012 Minsal) y está fuera de este alcance.
- Lo recomendable es integrar la **API de FirmaGob** para firmar desde el portal en lugar de un proveedor privado. FirmaGob tiene modalidades "desatendida" (sello de órgano) y "atendida" (con segundo factor/OTP); esto debe verificarse en las guías de la DGD.

### Brechas
- No se verificaron en fuente primaria el costo de FirmaGob (se dice que es gratuito para los órganos, sin fuente confirmada), sus modalidades y API, ni el contenido del DS 10/2023 sobre documentos electrónicos y firma.

## 3. Ley 20.285 (transparencia) y relación entre el CPLT y la Ley 21.719

### Conclusión
El portal no genera por sí mismo deberes nuevos de transparencia activa. Pero los **datos y documentos que gestione son "información pública"** sujeta a solicitudes de acceso, salvo causales de reserva, como los datos sensibles de salud. La Ley 21.719 de datos personales estaba programada para entrar en vigor el **01-12-2026**, pero hay un **proyecto de postergación en trámite** a noviembre de 2026.

### Hallazgos con cita
- La Ley 21.719 se publicó en diciembre de 2024 con entrada en vigor el 01-12-2026. El Ejecutivo ingresó en septiembre de 2026 un proyecto para postergarla al 01-12-2027. La Comisión de Constitución de la Cámara lo aprobó en general con fecha **15-10-2027**, según una nota de noviembre de 2026. La agencia fiscalizadora no estaba constituida y el plazo para designar a sus consejeros venció en junio de 2026 — [Diario Constitucional 12-06-2026](https://www.diarioconstitucional.cl/2026/06/12/la-ley-21-719-entra-en-vigor-el-1-de-diciembre-y-expone-vacios-en-regulacion-de-pequenas-empresas/); [Cámara](https://www.camara.cl/cms/?p=100841); [Carey](https://www.carey.cl/api/archivo/gobierno-ingresa-proyecto-de-ley-que-posterga-en-un-ano-entrada-en-vigor-de-la-ley-sobre-proteccion-de-datos-personales?lang=es); [Garrigues](https://www.garrigues.com/es_ES/noticia/chile-ejecutivo-presenta-proyecto-postergar-entrada-vigor-nueva-ley-proteccion-datos.md); [Cariola, sep-2026](https://www.cariola.cl/app/uploads/2026/09/Alerta-legal_-2septiembre.pdf)
- El DS 9 (art. 14) ya obliga a respetar la Ley 19.628 y los derechos ARCO en las plataformas con autenticación — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- El CPLT participó en la mesa técnica que elaboró la norma de autenticación (considerando 6 del DS 9) — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)

### Inferencias
- Por el art. 7 de la Ley 20.285 (no releído), la transparencia activa abarca estructura, personal y remuneraciones, compras, actos con efectos sobre terceros, trámites y requisitos, entre otros. Si Fricke Store publica nóminas, turnos o licitaciones, debe ser coherente con lo informado en el Portal de Transparencia del SS Viña del Mar-Quillota, pero no reemplaza ese portal.
- Las bitácoras de acceso, los registros del panel de administración y los correos internos pueden ser objeto de solicitudes de acceso a información (art. 10 y ss.). Hay que diseñar con capacidad de exportar y de tachar datos personales (principio de divisibilidad, art. 11 letra e).
- Bajo la Ley 21.719, según el diseño conocido de la ley y no verificado en esta sesión: los órganos públicos quedan bajo la fiscalización de la nueva Agencia de Protección de Datos Personales, y el CPLT conserva la competencia en transparencia. Los datos de salud son **datos sensibles**, lo que exige bases de licitud, registro de actividades, medidas de seguridad, notificación de brechas y, posiblemente, un delegado de protección de datos. Esto debe confirmarse con el texto legal y con lo que resulte del proyecto de postergación.

### Brechas
- No se encontraron fuentes primarias sobre la división de competencias entre el CPLT y la Agencia de Datos respecto de los órganos públicos. Tampoco se pudo leer el boletín 18.623-07 ni su estado final. La Cámara devolvió error 403.
- No se verificó el texto de la Ley 20.285 en esta sesión.

## 4. Accesibilidad: Ley 20.422, norma técnica web del Estado y Ley 21.180

### Conclusión
La norma vinculante identificada para sitios del Estado sigue siendo el **DS N.º 1/2015 Segpres** (norma técnica sobre sistemas y sitios web de los órganos del Estado), con nivel **AA de la W3C sobre WCAG 2.0**. La guía actual de SENADIS y del Kit Digital ya usa **WCAG 2.1 (y 2.2 en borrador)**. Las normas técnicas de 2023 no contienen un estándar WCAG explícito; el DS 9 solo exige buenas prácticas de accesibilidad en la autenticación.

### Hallazgos con cita
- SENADIS indica que en 2015 Segpres dictó el Decreto N.º 1, que aprueba la norma técnica sobre sistemas y sitios web de los órganos del Estado, con conformidad W3C de nivel AA o AAA — [SENADIS](https://senadis.gob.cl/descarga/i/7571/documento); [SENADIS 2](https://senadis.gob.cl/descarga/i/7772)
- La guía técnica de accesibilidad web de SENADIS, publicada en el Kit Digital, sigue WCAG 2.1 e incorpora el borrador de 2.2. Es una guía de implementación, no un decreto — [Kit Digital: Manual Accesibilidad Web](https://kitdigital.gob.cl/archivos/insumos/nuevos/Manual%20Accesibilidad%20Web.pdf); [SENADIS guía](https://www.senadis.gob.cl/descarga/i/3676/documento); [Guía SENADIS 2022](https://transparencia.defensacivil.cl/wp-content/uploads/2025/01/Guia-Para-la-Implementacion-de-Sitios-Web-Accesibles-SENADIS-2022-1_compressed-1.pdf)
- La guía metodológica de la DGD busca reforzar el cumplimiento de la Norma Técnica de sitios web de 2015 — [wikiguias guía metodológica](https://wikiguias.digital.gob.cl/guias/guia-metodologica-std)
- **DS 9, art. 8:** buenas prácticas de experiencia de usuario y accesibilidad web en el proceso de autenticación — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)
- El **DS 11/2023 no menciona accesibilidad ni WCAG** — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)
- Un estudio privado de 2025 evalúa los sitios estatales con WCAG 2.1 AA como referencia de facto — [Árbol Digital 2025](https://arboldigital.cl/assets/blog/ad_informe_accesibilidad_web_chile_2025-vf.pdf)

### Inferencias
- Recomendación práctica: diseñar Fricke Store con **WCAG 2.1 AA, idealmente 2.2 AA**. Así se cumple el piso legal del DS 1/2015 (2.0 AA) y se anticipa cualquier actualización.
- La Ley 20.422 (igualdad de oportunidades e inclusión de personas con discapacidad; no releída) obliga al Estado a asegurar la accesibilidad. Respecto del **personal**, también fundamenta el deber de ajustes razonables para funcionarios con discapacidad, lo que refuerza que una herramienta interna también debe ser accesible.
- Puntos concretos para el portal: contraste (la paleta azul y menta debe validarse a 4.5:1), navegación por teclado del lanzador de aplicaciones, foco visible, etiquetas ARIA en los íconos, `lang="es"` y mensajes de error accesibles en el login.

### Brechas
- No se pudo verificar en texto oficial si el DS 1/2015 fue reemplazado o actualizado entre 2023 y 2026 (por ejemplo, una nueva norma de accesibilidad digital que adopte WCAG 2.1 o 2.2). No se encontró evidencia de ello.
- Tampoco se pudo verificar en BCN el artículo exacto del DS 1/2015 que fija el nivel AA.

## 5. Kit Digital / Sistema de Diseño del Gobierno de Chile: ¿obligatorio?

### Conclusión
El Instructivo Presidencial de 2019 ordenó a los servicios adecuarse a los "nuevos estándares de diseño de sitios web" y a una plantilla universal de la DGD **antes del 31-12-2020**. Por eso, para **sitios web institucionales y plataformas de trámites ciudadanos** su uso se presenta como instruido, no como opcional. No se encontró ninguna norma que lo extienda a herramientas internas para funcionarios.

### Hallazgos con cita
- Instructivo 2019, punto 2.A.c: la DGD "definirá políticas relacionadas con el diseño y accesibilidad de los sitios web de las instituciones públicas", con estándares web a los que "tendrán que adecuarse las plataformas existentes y los nuevos desarrollos" — [Instructivo](https://www.alejandrobarros.com/wp-content/uploads/2019/02/Instructivo-Transformacion-Digital.pdf)
- Punto 2.A.h: la DGD debía publicar en 60 días los nuevos estándares de diseño y una plantilla universal, y los servicios debían adecuarse antes del 31-12-2020 — [Instructivo](https://www.alejandrobarros.com/wp-content/uploads/2019/02/Instructivo-Transformacion-Digital.pdf)
- El Kit Digital (kitdigital.gob.cl) aloja insumos como el Manual de Accesibilidad Web — [Kit Digital](https://kitdigital.gob.cl/archivos/insumos/nuevos/Manual%20Accesibilidad%20Web.pdf)
- Si se integra ClaveÚnica, el DS 9 art. 8 obliga a respetar "las definiciones de marca y lineamientos gráficos" del administrador, es decir, el botón y el flujo oficiales — [DS 9](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361373.pdf)

### Inferencias
- Para un portal **interno** de funcionarios, el diseño propio estilo Google es defendible. El instructivo se refiere a "sitios web de las instituciones públicas" y a la "digitalización de trámites", no a intranets.
- Si en el futuro hay una cara pública para pacientes, conviene adoptar el Kit Digital (o al menos su barra gob.cl, su tipografía y componentes accesibles) y el botón oficial de ClaveÚnica.
- Riesgo de la estética "estilo Google": evitar parecerse a marcas de terceros, por ejemplo con logos o íconos protegidos.

### Brechas
- No se verificó si el instructivo de 2019 sigue vigente o fue derogado o reemplazado por instructivos posteriores (2022-2026), ni si existe una resolución o circular de la DGD que haga obligatorio el Sistema de Diseño.

## 6. Compras públicas y licencias: Ley 19.886 / Ley 21.634, desarrollo propio, código abierto, nube y SaaS de IA

### Conclusión
El desarrollo **in-house** con personal propio no es una compra y no gatilla la Ley 19.886. Sí la gatillan la contratación de servicios de desarrollo, licencias, nube o SaaS (incluida la IA), que deben hacerse por convenio marco o licitación en Mercado Público. ChileCompra tiene convenios marco de nube (desde 2014) y de desarrollo y mantención de software (renovado en agosto de 2024). Si el proyecto requiere presupuesto, pasa por **EvalTIC**. No se encontró una "Política de uso de nube" oficial vigente con reglas de residencia de datos.

### Hallazgos con cita
- Desde 2014 el Estado puede contratar servicios en la nube (IaaS, nube pública y privada) por convenio marco de ChileCompra — [ChileCompra 2014](https://www.chilecompra.cl/2014/01/chile-se-convierte-en-el-primer-pais-de-latinoamerica-donde-el-estado-podra-contratar-servicios-en-la-nube-cloud-store-y-de-data-center/)
- El nuevo convenio marco de Desarrollo y Mantención de Software, Servicios Profesionales TI e Infraestructura como Servicio está habilitado en la tienda desde el 09-08-2024 — [ChileCompra 2024](https://www.chilecompra.cl/2024/08/ya-se-encuentra-habilitado-en-la-tienda-electronica-el-nuevo-convenio-marco-de-desarrollo-y-mantencion-de-software/); [licitación](https://www.chilecompra.cl/2024/01/participa-de-la-licitacion-publica-de-convenio-marco-de-servicios-de-desarrollo-y-mantencion-de-software-servicios-profesionales-ti-e-infraestructura/)
- En julio de 2025 ChileCompra realizó un seminario sobre la nube en el sector público — [ChileCompra 2025](https://www.chilecompra.cl/2025/07/seminario-reune-a-actores-del-sector-publico-privado-y-academia-para-discutir-sobre-los-avances-desafios-y-oportunidades-de-la-tecnologia-cloud/)
- El Plan Nacional de Data Centers 2024-2030 (Ministerio de Ciencia, diciembre de 2024) impulsa un servicio compartido de multinube estatal — [Carey](https://www.carey.cl/api/archivo/lanzamiento-del-plan-nacional-de-data-centers-2024-2030?lang=es)
- La Política Nacional de Ciberseguridad 2023-2028 incluye lineamientos sobre datos, inversiones tecnológicas y compras en la nube — [Hacienda MO17](https://media.hacienda.cl/publico/Modernizacion/MO17.pdf); [Carey](https://www.carey.cl/api/archivo/publican-politica-nacional-de-ciberseguridad-2023-2028?lang=es)
- La Política Nacional de IA fue actualizada por decreto — [BCN](https://www.bcn.cl/leychile/navegar?idNorma=1210664)
- **DS 7/2023 art. 7:** la gestión de proveedores de nube es una categoría obligatoria de la función de identificación — [DS 7](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- **DS 11/2023 arts. 6, 12 a 14:** la Guía de Lineamientos para el Desarrollo de Software de la DGD es referencia obligada en los Planes de Mejora, y la evaluación EvalTIC es vinculante para el presupuesto — [DS 11](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361375.pdf)

### Inferencias
- La Ley 21.634 (moderniza la Ley 19.886, publicada en diciembre de 2023 y con nuevo reglamento en 2024-2025; no verificada en esta sesión) amplió la probidad, los conflictos de interés, la compra ágil y los procedimientos especiales. Lo relevante para el portal: cualquier contratación de nube, licencias, servicios de IA o desarrollo externo debe pasar por Mercado Público. La declaración de intereses de quienes participan en la evaluación es obligatoria.
- Recomendación sobre código abierto: publicar el código en un repositorio institucional y licenciarlo como software libre. Esto facilita la reutilización entre Servicios de Salud y se alinea con la Guía de Lineamientos para el Desarrollo de Software de la DGD (no leída en detalle).
- Datos de salud en la nube o con IA en modalidad SaaS: hay que evaluar la transferencia internacional bajo la Ley 21.719 (datos sensibles), las cláusulas contractuales de seguridad y confidencialidad, y la gestión de proveedores (DS 7, art. 7).

### Brechas
- No se encontró ninguna "Política de uso de nube" ni circular oficial con reglas de **residencia de datos** para el Estado chileno. No se pudo confirmar si existe.
- No se verificaron los artículos específicos de la Ley 21.634 ni de su reglamento (número, fecha y vigencia), ni orientaciones de ChileCompra para comprar IA (por ejemplo, una directiva de contratación de IA).

## 7. Instructivos presidenciales aplicables (2019-2026)

### Conclusión
El instructivo base identificado es el **Instructivo Presidencial sobre Transformación Digital del 24-01-2019**. Su distribución incluye expresamente al Director del Servicio de Salud Viña del Mar-Quillota. Sus obligaciones sobre ClaveÚnica, estándares web, Cero Papel y Coordinador de Transformación Digital luego se recogieron en la Ley 21.180 y los DS de 2023.

### Hallazgos con cita
Todas estas disposiciones provienen del [Instructivo de 2019](https://www.alejandrobarros.com/wp-content/uploads/2019/02/Instructivo-Transformacion-Digital.pdf):
- Fecha: 24-01-2019, firmado por el Presidente Piñera. Destinatarios: todos los ministerios, incluida la Subsecretaría de Redes Asistenciales, y los 29 Servicios de Salud, incluido el **SS Viña del Mar-Quillota (N.º 230 de la distribución)**.
- Metas: ClaveÚnica como identidad digital única para personas naturales (1.b); digitalizar el 80 % de los trámites al 31-12-2021 y el 100 % al 31-12-2023 (2.A.b); estándares de diseño web y plantilla universal antes del 31-12-2020 (2.A.h).
- Cero Papel: plataforma obligatoria de comunicaciones oficiales al 31-12-2019 (3.d-e). Las plataformas transversales de compras, gestión documental y RR.HH. son opcionales si se cumplen los estándares (3.c).
- Coordinador Institucional de Transformación Digital que reporta al jefe de servicio (4.a).

### Inferencias
- Para Fricke Store: el punto 3.c permite usar plataformas propias para procesos internos "siempre que cumplan con los estándares que serán definidos". Es el respaldo para un desarrollo in-house, condicionado a la interoperabilidad (DS 12) y a la integración con DocDigital para las comunicaciones oficiales.

### Brechas
- No se identificaron ni verificaron instructivos o circulares presidenciales posteriores (2020-2026) sobre transformación digital, software o IA en el Estado. Por ejemplo, posibles instructivos sobre ciberseguridad o sobre el uso de IA generativa en la Administración. Deben buscarse en la web de Segpres/DGD y en el Diario Oficial.
