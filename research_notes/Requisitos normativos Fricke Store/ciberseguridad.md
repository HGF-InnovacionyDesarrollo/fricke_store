# Obligaciones de ciberseguridad aplicables a Fricke Store (Hospital Dr. Gustavo Fricke, Chile) — estado a noviembre 2026

> Nota metodológica: las fuentes primarias consultadas directamente fueron el texto de la Ley 21.663 en BCN (vía XML de LeyChile), el DS 7/2023 en el Diario Oficial (texto íntegro extraído del PDF), la presentación oficial de ANCI sobre SE/OIV y la página de seguridad de la información del MINSAL. La pertenencia del HGF a la nómina OIV proviene de un sitio de terceros que reproduce la Res. Ex. 87/2025; debe verificarse en el Diario Oficial (17-12-2025). Los controles ISO/NIST/OWASP se citan desde su fuente canónica, pero su numeración proviene de conocimiento previo, no de una lectura en esta sesión.

## 1. Ley 21.663: servicios esenciales, OIV y si alcanza a hospitales públicos

### Takeaway
La Ley 21.663 (publicada el 08-04-2024) considera la "prestación institucional de salud (hospitales, clínicas, consultorios y centros médicos)" como servicio esencial. Además, todos los órganos de la Administración del Estado son servicios esenciales por definición. Según la nómina definitiva de OIV de la primera etapa (Res. Ex. N° 87, publicada el 17-12-2025), tanto el **Hospital Doctor Gustavo Fricke (RUT 61.606.602-1)** como el **Servicio de Salud Viña del Mar Quillota (RUT 61.606.600-5)** son **Operadores de Importancia Vital**. Por eso Fricke Store queda bajo los deberes reforzados de los OIV.

### Cited Findings
- La Ley 21.663, Ley Marco de Ciberseguridad, se promulgó el 26-03-2024 y se publicó el 08-04-2024 — [BCN LeyChile, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)
- Arts. 4 y 5: la ley se aplica a quienes prestan servicios esenciales, entre ellos la "prestación institucional de salud (hospitales, clínicas, consultorios y centros médicos)" — [BCN LeyChile, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)
- La presentación oficial de ANCI incluye como servicios esenciales a los ministerios, municipalidades, "órganos y servicios públicos creados para el cumplimiento de la función administrativa" y la "Prestación institucional de salud: Hospitales, clínicas, consultorios y centros médicos" — [ANCI, PPT Presentación SE y OIV](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf)
- Según ANCI, los criterios para calificar un OIV son que el servicio dependa de redes y sistemas informáticos y que su afectación, interceptación, interrupción o destrucción tenga un impacto significativo en la seguridad y el orden público, en la provisión continua de servicios esenciales o en las funciones del Estado — [ANCI, PPT](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf)
- Art. 6: ANCI califica a los OIV y debe revisar la calificación al menos cada 3 años. En el caso de instituciones públicas lo hace con un informe del Ministerio de Hacienda — [BCN, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)
- Nómina preliminar: Res. Ex. N° 50 (16-09-2025). La consulta pública cerró el 16-10-2025 — [Resolución 50 exenta (copia)](https://alog.cl/wp-content/uploads/2025/12/Resolucion-50-EXENTA_16-SEP-2025-4.pdf); [DF](https://www.df.cl/df-lab/tech-negocios/anci-explica-los-cambios-en-la-lista-de-operadores-de-importancia-vital-se)
- Nómina definitiva de la primera etapa: Res. Ex. N° 87/2025, publicada el 17-12-2025. El total de OIV bajó de 1.712 a 915 y en salud pasó de 326 a 114 entidades. Se excluyó a los centros de diálisis porque no dependen de una ficha clínica electrónica — [DF](https://www.df.cl/df-lab/tech-negocios/anci-explica-los-cambios-en-la-lista-de-operadores-de-importancia-vital-se); [Trendtic](https://www.trendtic.cl/2025/12/anci-disminuye-de-1712-a-915-los-operadores-de-importancia-vital-oiv/)
- En la Res. 87/2025 figuran "Hospital Doctor Gustavo Fricke" (RUT 61606602-1, sector Salud) y "Servicio de Salud de Viña del Mar Quillota" (RUT 61606600-5, sector Público), junto con los 29 Servicios de Salud y unos 61 hospitales e institutos públicos — [ley21663.info, listado OIV (sitio de terceros)](https://ley21663.info/operadores-de-importancia-vital/listado/)
- Segunda etapa: Res. Ex. N° 187/2026 (julio de 2026), con 239 instituciones de combustibles, agua, transporte, concesiones, seguridad social y producción farmacéutica, más 84 entidades adicionales de sectores de la primera etapa — [Carey, julio 2026](https://www.carey.cl/api/archivo/anci-aprueba-la-nomina-definitiva-de-operadores-de-importancia-vital-de-la-segunda-etapa-del-primer-procedimiento-de-calificacion?lang=es); [BCN idNorma 1226358](https://www.bcn.cl/leychile/navegar?idNorma=1226358); [Diario Oficial 24-07-2026](https://www.diariooficial.interior.gob.cl/publicaciones/2026/07/24/44507/01/2842835.pdf)
- Las entidades de salud de la segunda etapa son clínicas privadas, como Clínica Alemana, UC Christus y Red Interclínica, y no hospitales públicos — [ley21663.info](https://ley21663.info/operadores-de-importancia-vital/listado/)
- Contra la calificación procede recurso de reposición ante ANCI (5 días hábiles) y recurso de ilegalidad ante la Corte de Apelaciones (15 días) — [DF](https://www.df.cl/df-lab/tech-negocios/anci-explica-los-cambios-en-la-lista-de-operadores-de-importancia-vital-se)

### Inferences
- El HGF tiene una doble condición: es servicio esencial como órgano del Estado y como prestador institucional de salud, y además es OIV de forma individual. Fricke Store, como portal SSO que da acceso a sistemas clínicos, entra en el alcance del SGSI y del plan de continuidad que el HGF debe tener como OIV.
- Los módulos futuros con ficha clínica electrónica, IoT y cámaras refuerzan el criterio que ANCI usó para mantener a los prestadores de salud en la nómina: la dependencia de la ficha clínica electrónica.

### Gaps
- No se leyó directamente el PDF de la Res. Ex. 87/2025 en el Diario Oficial. La pertenencia del HGF se confirmó solo por el sitio de terceros ley21663.info, que tiene anomalías de datos conocidas (RUT duplicados). **Hay que verificarla en el Diario Oficial del 17-12-2025.**
- No se encontró un plazo legal, contado desde la calificación, para que un OIV tenga implementado el SGSI y certificados sus planes de continuidad. Hay que revisar las instrucciones de ANCI y el reglamento de calificación.

## 2. Deberes concretos, plazos de reporte y sanciones (Ley 21.663)

### Takeaway
Todo servicio esencial debe prevenir, reportar y resolver incidentes (art. 7) y reportar al CSIRT Nacional los incidentes con efectos significativos. El esquema es alerta temprana en **3 horas**, actualización en **72 horas** (**24 horas** si un OIV ve afectado su servicio esencial), informe final en **15 días corridos** y plan de acción del OIV en **7 días corridos** (art. 9). Como OIV, el HGF además debe tener un SGSI, planes de continuidad certificados y revisados al menos cada 2 años, simulacros, capacitación y un delegado de ciberseguridad (art. 8). Las multas llegan a 40.000 UTM para un OIV, aunque a los órganos del Estado se les aplica un régimen distinto (art. 47).

### Cited Findings
- Art. 7, deberes generales: aplicar de forma permanente medidas para prevenir, reportar y resolver incidentes, siguiendo los protocolos y estándares de ANCI o los sectoriales — [BCN, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434); [ANCI PPT](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf)
- Art. 8, deberes específicos de los OIV: implementar un SGSI continuo; mantener un registro de las acciones del SGSI; elaborar e implementar planes de continuidad operacional y ciberseguridad (certificados y revisados al menos cada 2 años); hacer ejercicios y simulacros; adoptar oportunamente medidas para reducir el impacto y la propagación de incidentes; contar con programas de capacitación continua; informar a los potenciales afectados; y designar un delegado de ciberseguridad como contraparte de ANCI — [BCN, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434); [ANCI PPT](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf)
- Art. 9, reporte: alerta temprana dentro de 3 horas desde que se conoce el incidente; actualización en 72 horas, o 24 horas si un OIV ve afectada la prestación de su servicio esencial; informe final a los 15 días corridos desde la alerta; plan de acción del OIV en un máximo de 7 días corridos — [BCN, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)
- ANCI precisa que la actualización a las 72 horas debe incluir "evaluación inicial, gravedad, impacto e IoC". Los contratos con proveedores no pueden restringir que el prestador comunique información sobre amenazas. La plataforma de reporte es https://portal.anci.gob.cl — [ANCI PPT](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf)
- Según ANCI, un incidente tiene "efecto significativo" si interrumpe la continuidad de un servicio esencial, afecta la integridad física o la salud de las personas, afecta sistemas con datos personales, afecta la integridad o confidencialidad de activos o la disponibilidad de redes, o implica un ingreso no autorizado — [ANCI PPT](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf)
- La obligación de reportar rige desde el 01-03-2025, con la publicación del Reglamento de Reporte de Incidentes (DS N° 295/2024) — [Cariola, alerta 04-03-2025](https://www.cariola.cl/app/uploads/2025/03/Alerta-Legal_04.03.2025.pdf); [AZ](https://www.az.cl/ley-marco-de-ciberseguridad-claves-del-reglamento-de-reporte-de-incidentes/)
- Arts. 39 y 40, infracciones y multas: leves hasta 5.000 UTM (10.000 si es OIV); graves hasta 10.000 UTM (20.000 si es OIV); gravísimas hasta 20.000 UTM (40.000 si es OIV). No designar delegado es leve. No adoptar a tiempo medidas para reducir el impacto de un incidente es grave, y gravísima si el incidente tiene impacto significativo. Las infracciones prescriben a los 3 años — [BCN, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)
- Cariola clasifica la omisión de reportar como grave (hasta 10.000 UTM). AZ habla de hasta 20.000 UTM para gravísimas y 40.000 UTM para OIV. Ambas cifras son compatibles con la escala del art. 40 — [Cariola](https://www.cariola.cl/app/uploads/2025/03/Alerta-Legal_04.03.2025.pdf); [AZ](https://www.az.cl/?p=258468)
- Art. 47, órganos de la Administración del Estado: el jefe superior del servicio debe velar por que se apliquen medidas idóneas para prevenir, reportar y resolver incidentes, y el organismo debe adoptar las medidas que ANCI indique. En el texto leído no hay una multa específica al órgano ni al jefe de servicio — [BCN, Ley 21.663](https://www.bcn.cl/leychile/navegar?idNorma=1202434)

### Inferences
- El sistema de Fricke Store debe permitir cumplir la alerta de 3 horas. Eso exige detectar a tiempo: alertas sobre la bitácora encadenada, bloqueos masivos de cuentas y accesos anómalos. También exige poder extraer IoC (IP, usuario, hora, hash) dentro de 72 o 24 horas.
- Como el HGF es un órgano público, la responsabilidad recae en el director o directora del hospital (art. 47), y en la práctica puede derivar en responsabilidad administrativa mediante sumario. Esto es una inferencia: no se leyó una norma que lo establezca de forma expresa.

### Gaps
- El texto obtenido de BCN se leyó con resúmenes automáticos y hubo inconsistencias de numeración entre las fuentes (arts. 38 o 39 para la clasificación). Conviene revisar los arts. 38 a 47 en el texto oficial.
- No se pudo confirmar si las multas del Título VII se aplican a órganos públicos que son OIV, o si a ellos solo les rige el art. 47.

## 3. Instrucciones, protocolos y taxonomía de ANCI, y el CSIRT

### Takeaway
A noviembre de 2026, ANCI había dictado al menos: la Instrucción General N° 1 (registro de servicios esenciales, 2025); la taxonomía de incidentes (Res. Ex. N° 7/2025); y las Instrucciones Generales N° 2 (plataforma de inscripción y reporte), N° 3 (designación del delegado de ciberseguridad) y N° 4 (respuesta técnica inmediata y contención), publicadas el 26-12-2025. No se encontró un CSIRT sectorial de salud. El reporte se dirige al CSIRT Nacional a través de portal.anci.gob.cl.

### Cited Findings
- Instrucción General N° 1 de ANCI — [BCN idNorma 1213936](https://www.bcn.cl/leychile/navegar?idNorma=1213936); [regulations.ai, registro de servicios esenciales N°1/2025](https://regulations.ai/regulations/RAI-CL-NA-IGNANXX-2025)
- La Res. Ex. N° 7/2025 aprueba la Taxonomía de Incidentes de Ciberseguridad, que contempla 4 áreas de impacto y 11 efectos observables — [Cariola](https://www.cariola.cl/app/uploads/2025/03/Alerta-Legal_04.03.2025.pdf)
- Diario Oficial del 26-12-2025: IG N° 2 (plataforma de inscripción y reporte, con autenticación por Clave Única y una alternativa excepcional), IG N° 3 (delegado de ciberseguridad con un perfil mínimo, **independiente de las áreas de TI**, designación formal acreditada ante ANCI y aviso de cambios en plazos breves) e IG N° 4 (contención inmediata). Todas desarrollan los arts. 6, 8, 9 y 11 de la ley y el DS 295/2024 — [Actualidad Jurídica DOE](https://actualidadjuridica.doe.cl/anci-fija-estandares-obligatorios-para-operadores-vitales-delegado-de-ciberseguridad-reporte-de-incidentes-y-contencion-inmediata/)
- La IG N° 4 exige: restringir accesos y aislar los sistemas comprometidos; cambiar las credenciales administrativas; deshabilitar el acceso remoto expuesto; suspender temporalmente servicios en riesgo; usar herramientas de detección y contención; configurar firewalls con política *default-deny*; segmentar redes para evitar el movimiento lateral; y registrar las acciones — [Actualidad Jurídica DOE](https://actualidadjuridica.doe.cl/anci-fija-estandares-obligatorios-para-operadores-vitales-delegado-de-ciberseguridad-reporte-de-incidentes-y-contencion-inmediata/)
- Gobernanza de la ley: ANCI, CSIRT Nacional, CSIRT Nacional de Defensa, Consejo Multisectorial y Comité Interministerial (arts. 48-52) — [ANCI PPT](https://anci.gob.cl/documents/4692/PPT_Presentacion_SE_y_OIV_VF.pdf); [BCN](https://www.bcn.cl/leychile/navegar?idNorma=1202434)

### Inferences
- Fricke Store debe incorporar los "botones de pánico" que exige la IG 4: revocar todas las sesiones, forzar el cambio de credenciales de administradores, deshabilitar cuentas o módulos y aislar integraciones. Debe además registrar cada acción en la bitácora encadenada.
- El delegado de ciberseguridad del HGF no puede ser el desarrollador ni el jefe de TI (IG 3). Conviene que el portal tenga un rol de auditoría de solo lectura para él.

### Gaps
- No se leyó el texto íntegro de las IG 2, 3 y 4 ni de la taxonomía. Faltan plazos exactos, formularios y campos obligatorios.
- No se encontró un CSIRT de salud ni un CSIRT de la Red Asistencial. El sitio del MINSAL tampoco lo menciona.
- No se encontraron protocolos o estándares técnicos de ANCI del art. 7 aprobados para el sector salud. Están pendientes o no se hallaron.

## 4. Ley 21.180 y DS 7/2023 (Norma Técnica de Seguridad de la Información y Ciberseguridad)

### Takeaway
El DS N° 7 de 2023 de SEGPRES ("Establece Norma Técnica de Seguridad de la Información y Ciberseguridad conforme la Ley N° 21.180"), del 19-05-2023 y publicado en el Diario Oficial el 17-08-2023, obliga a los órganos de la Administración del Estado a hacer un diagnóstico inicial, aprobar una Política de SI y Ciberseguridad mediante acto administrativo del jefe de servicio, designar un responsable institucional de SI y ciberseguridad y un responsable de activos de información (sin poder externalizarlos), y organizar el trabajo según 5 funciones (identificar, proteger, detectar, responder y recuperar). Los controles concretos están en la guía técnica GU-CIBER-001 de Gobierno Digital.

### Cited Findings
- Art. 1: la norma define estándares y directrices para resguardar la confidencialidad, integridad y disponibilidad de "las plataformas electrónicas que sustentan sus procedimientos administrativos" — [Diario Oficial 17-08-2023, CVE 2361371](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Art. 4: diagnóstico inicial del estado de ciberseguridad de las plataformas, que debe incluirse en el Catálogo de Plataformas de la Norma Técnica de Calidad y Funcionamiento — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Art. 5: Política aprobada por el jefe superior del servicio, que incorpore "la privacidad como parte del diseño inicial". Debe definir un responsable institucional de SI y ciberseguridad y un responsable de los activos de información (identificación, clasificación y riesgo). "El desempeño de estas funciones no podrá ser externalizado bajo ninguna forma". Si el órgano ya tiene un encargado de ciberseguridad según el Instructivo Presidencial N° 8/2018, el requisito se da por cumplido — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Art. 7, identificación: contexto, gobernanza, gestión de activos, gestión de riesgos y relación con proveedores de nube — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Art. 8, protección: "gestión de servidores, redes, autenticación y control de acceso", concienciación, seguridad de los datos y "registro de eventos" — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Art. 9, detección: análisis de eventos, monitoreo continuo y protección contra código malicioso en servidores y plataformas — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Arts. 10 y 11, respuesta (planificación, comunicación, análisis, mitigación y mejora) y recuperación (planes de recuperación, mejora y comunicación del estado) — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- Arts. 12-14: Gobierno Digital dicta guías técnicas; la gradualidad sigue el DFL N° 1/2020 de SEGPRES; la norma se revisa al menos cada 2 años — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- La guía técnica GU-CIBER-001 entrega los lineamientos operativos (art. 12) y se basa en NCh-ISO 27000, en NIST y en el DS 83/2004 — [Wikiguías Gobierno Digital, GU-CIBER-001](https://wikiguias.digital.gob.cl/guias/GU-CIBER-001)
- Existe una Norma Técnica de Autenticación separada, también bajo la Ley 21.180 — [BCN idNorma 1195122](https://www.bcn.cl/leychile/navegar?i=1195122)
- El DS 7/2023 seguía citado como vigente en el Diario Oficial del 31-12-2025 — [Diario Oficial 31-12-2025](https://www.diariooficial.interior.gob.cl/publicaciones/2025/12/31/44337/01/2748664.pdf)

### Inferences
- Fricke Store es una "plataforma electrónica" en el sentido del art. 2 n° 10 del DS 7. Debe figurar en el catálogo de plataformas con su diagnóstico y quedar cubierta por la Política del HGF o del Servicio de Salud.
- El DS 7 no fija parámetros numéricos (largo de contraseña, retención de logs). Esos parámetros quedan en la guía técnica y en las políticas internas, y se recomienda alinearlos con NIST SP 800-63B (ver sección 6).

### Gaps
- No se pudo leer el contenido de GU-CIBER-001 (la página no se renderizó). Faltan los controles numéricos de autenticación, logs y respaldos.
- No se verificó el contenido de la Norma Técnica de Autenticación (si exige Clave Única o segundo factor para funcionarios).
- Gradualidad: no se confirmó en qué etapa del DFL 1/2020 están los Servicios de Salud y hospitales autogestionados.

## 5. Políticas del MINSAL y de los Servicios de Salud

### Takeaway
El MINSAL tiene una Política General de Seguridad de la Información y Ciberseguridad (PS-NC-005 v5, Res. Ex. N° 854 del 23-07-2025), un conjunto de políticas específicas basadas en NCh-ISO 27001:2022 e instructivos dirigidos al "sector salud". También aprobó un plan de ciberseguridad para el sector salud 2026-2029 (Res. Ex. N° 1333). No se encontró un CSIRT sectorial de salud. Hay reportes de que el MINSAL implementa un SOC.

### Cited Findings
- PS-NC-005 v5, Res. Ex. N° 854 (23-07-2025). El marco de referencia es NCh-ISO 27001:2022 (SGSI) y la Ley 21.663 — [MINSAL, Seguridad de la Información y Ciberseguridad](https://www.minsal.cl/seguridad_de_la_informacion/)
- Las políticas específicas incluyen: identificación y autenticación de usuarios (PS-NC-003), respaldo de información y software (PS-NC-004 v5, 24-06-2025), control de acceso lógico (PS-NC-008), seguridad de red (PS-NC-009), seguridad física (PS-NC-010), protección de datos personales (PS-NC-011), criptografía (PS-NC-015), clasificación de la información (PS-NC-016), teletrabajo (PS-NC-018), proveedores (PS-NC-020), gestión de riesgos (PS-NC-021), nube pública (PS-NC-022) y uso de IA (PS-NC-024). Hay además un procedimiento de gestión de identidad y derechos de acceso (PROS-NC-004) — [MINSAL](https://www.minsal.cl/seguridad_de_la_informacion/)
- Instructivos dirigidos al sector salud: ITS-NC-007 (Res. 853) e ITS-NC-006 (Res. 850). Plan de ciberseguridad y SI del sector salud 2026-2029: Res. Ex. N° 1333 — [MINSAL](https://www.minsal.cl/seguridad_de_la_informacion/). Un resultado de búsqueda menciona en cambio una Res. N° 969 (julio de 2025) para el plan sectorial — [MINSAL ?p=136907](https://www.minsal.cl/?p=136907). **Las fuentes no coinciden.**
- Según el encargado de seguridad del MINSAL, hay diferencias de infraestructura y capacidades entre los establecimientos de la red asistencial — [Diario Estrategia](https://www.diarioestrategia.cl/texto-diario/mostrar/6063765/expertos-advierten-nuevas-exigencias-sector-salud-requieren-cambios-alla-tecnologia)

### Inferences
- Lo razonable es que Fricke Store se alinee con PS-NC-003, PS-NC-008, PS-NC-004 y PS-NC-015 del MINSAL y con la política propia del SSVQ/HGF, si existe. No se confirmó que sean obligatorias para los Servicios de Salud, pero los instructivos "sector salud" lo sugieren.

### Gaps
- No se leyó el contenido de las políticas PS-NC (parámetros de contraseña, retención de respaldos).
- No se encontró la política de SI del Servicio de Salud Viña del Mar-Quillota ni la del HGF.
- No se encontró un CSIRT de salud ni de la Red Asistencial. El SOC del MINSAL solo aparece en prensa.

## 6. Controles técnicos mapeados a Fricke Store (ISO 27001/27002:2022, ISO 27799, NIST CSF 2.0, SP 800-63B, OWASP ASVS)

### Takeaway
El MINSAL y la guía del DS 7 toman como base la familia NCh-ISO 27000 y el marco NIST, así que estos controles son la forma natural de mostrar cumplimiento. Para un portal SSO, lo crítico es: MFA para cuentas privilegiadas y para acceso a datos clínicos; política de contraseñas de NIST 800-63B rev. 4 (largo antes que complejidad, verificación contra listas de contraseñas comprometidas, sin rotación periódica forzada); logs centralizados, íntegros y con hora sincronizada; respaldos probados; gestión de vulnerabilidades; TLS en todo el tráfico; segmentación de IoT y cámaras; y desarrollo según OWASP ASVS.

### Cited Findings
- La guía técnica del DS 7 se basa en NCh-ISO 27000 y en NIST — [GU-CIBER-001](https://wikiguias.digital.gob.cl/guias/GU-CIBER-001). El MINSAL basa su SGSI en NCh-ISO 27001:2022 — [MINSAL](https://www.minsal.cl/seguridad_de_la_informacion/)
- NIST CSF 2.0 (feb. 2024) agrega la función GOVERN (GV) a Identify, Protect, Detect, Respond y Recover. Las 5 funciones del DS 7 coinciden con las de CSF 1.1 — [NIST CSF 2.0](https://www.nist.gov/cyberframework); [Diario Oficial DS 7](https://www.diariooficial.interior.gob.cl/publicaciones/2023/08/17/43629/01/2361371.pdf)
- NIST SP 800-63B (rev. 4, versión final de 2025): con contraseña como único factor, mínimo 15 caracteres; si forma parte de MFA, mínimo 8. Admite al menos 64 caracteres. No impone reglas de composición ni rotación periódica (solo ante evidencia de compromiso). Verifica contra listas de contraseñas comprometidas o comunes. Limita los intentos fallidos (*rate limiting*). En AAL2 exige MFA y en AAL3, autenticador resistente a phishing — [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
- OWASP ASVS (v5.0, 2025) define requisitos verificables de autenticación, sesión, control de acceso, logging, criptografía y configuración en 3 niveles. El nivel 2 o 3 aplica a aplicaciones con datos sensibles — [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)

Mapa de controles (numeración ISO/IEC 27002:2022 tomada de conocimiento previo; [ISO/IEC 27001:2022](https://www.iso.org/standard/27001), [ISO 27799:2016](https://www.iso.org/standard/62777.html)):

| Ámbito | ISO 27002:2022 | NIST CSF 2.0 | Aplicación en Fricke Store | Estado actual (según el brief) |
|---|---|---|---|---|
| Gobierno, roles, delegado | 5.1, 5.2, 5.3 | GV.RR, GV.PO | Política aprobada por el director; responsable SI (DS 7 art. 5); delegado ANCI (art. 8, IG 3) | Organizacional, pendiente |
| Inventario y clasificación | 5.9, 5.12 | ID.AM | Fricke Store en el catálogo de plataformas (DS 7 art. 4); clasificar datos clínicos como sensibles | Pendiente |
| Control de acceso / RBAC | 5.15, 5.18, 8.2, 8.3 | PR.AA | Mínimo privilegio, revisión periódica de accesos, alta y baja ligada a RR.HH. | RBAC existe; falta recertificación periódica |
| Autenticación / MFA | 5.17, 8.5 | PR.AA | MFA (TOTP/WebAuthn) obligatorio para admin y módulos clínicos (AAL2); contraseñas según 800-63B (≥15 sin MFA, lista de contraseñas comprometidas, sin rotación forzada) | Hash scrypt y bloqueo OK; **falta MFA** |
| Sesión | 8.5 | PR.AA | Timeout por inactividad, bloqueo de pantalla, revocación global de sesiones (IG 4) | Timeout y bloqueo OK; falta revocación masiva |
| Registro y monitoreo | 8.15, 8.16, 8.17 | DE.CM, DE.AE | Logs con sello de tiempo NTP, protegidos contra alteración, enviados a SIEM/SOC, con alertas que permitan cumplir las 3 h | Bitácora encadenada OK; falta envío externo y alertas |
| Respaldos | 8.13 | PR.DS, RC.RP | Respaldo cifrado de SQLite, copia fuera de línea o inmutable, pruebas de restauración (PS-NC-004 del MINSAL) | No indicado |
| Vulnerabilidades y parches | 8.8, 8.19 | ID.RA, PR.PS | Escaneo de dependencias (pip-audit), parches del SO y de FastAPI/uvicorn, pentest | No indicado |
| Criptografía / TLS | 8.24 | PR.DS | TLS 1.2+ (preferente 1.3) incluso en la red interna; HSTS; cifrado en reposo de la BD con datos clínicos (PS-NC-015) | Verificar |
| Segmentación de red (IoT y cámaras) | 8.20, 8.21, 8.22 | PR.IR | VLAN o zonas separadas para IoT y CCTV, firewall *default-deny* (IG 4), sin acceso directo desde la red de usuarios al portal de administración | Futuro |
| Desarrollo seguro | 8.25, 8.26, 8.28, 8.29 | PR.PS | OWASP ASVS nivel 2 (3 para módulos clínicos), revisión de código, SAST y pruebas de seguridad | Parcial |
| Proveedores | 5.19-5.22 | GV.SC | Cláusulas que no restrinjan la comunicación de amenazas (Ley 21.663, según ANCI) | Pendiente |
| Incidentes | 5.24-5.28 | RS.MA, RS.CO | Procedimiento con alerta de 3 h, 72/24 h y 15 días; preservación de evidencia | Pendiente |
| Continuidad | 5.29, 5.30 | RC.RP | Plan de continuidad certificado y revisado cada 2 años, con simulacros (OIV, art. 8) | Pendiente |
| Salud (ISO 27799) | Guía sectorial de 27002 | — | Registro de todo acceso a datos de pacientes, identificación única de usuarios, acceso de emergencia (*break-glass*) auditado | Futuro |

### Inferences
- La brecha regulatoria más visible en el estado actual es la **falta de MFA**: un OIV que procesa ficha clínica difícilmente justificará solo contraseña ante ANCI, y NIST exige MFA desde AAL2.
- Si se mantiene el login con un solo factor, la política de contraseñas debería exigir al menos 15 caracteres según 800-63B rev. 4.
- SQLite on-premise plantea retos de cifrado en reposo, alta disponibilidad y concurrencia para los módulos clínicos. Conviene evaluarlo en el plan de continuidad.

### Gaps
- No se leyeron en esta sesión los textos de ISO 27002/27799 (son de pago); la numeración es de conocimiento previo.
- No se verificó en esta sesión el estado exacto de la versión final de SP 800-63B rev. 4 ni de ASVS 5.0 (se citan desde conocimiento previo, con enlaces canónicos).
- No se encontró una exigencia chilena explícita de retención de logs en número de días u horas.

## 7. IoT y dispositivos médicos (ISP)

### Takeaway
No se encontró una guía ni una obligación del ISP específica sobre ciberseguridad de dispositivos médicos o IoT. Lo que existe del ISP trata sobre buenas prácticas de fabricación (NCh ISO 13485) y la tecnovigilancia (reporte de eventos adversos). Para sensores y cámaras, las exigencias concretas vienen de la Ley 21.663 (IG 4: segmentación y *default-deny*) y de las buenas prácticas internacionales.

### Cited Findings
- El ISP aprobó en enero de 2023 una guía de buenas prácticas de fabricación de dispositivos médicos basada en NCh ISO 13485:2017 — [Carey](https://www.carey.cl/instituto-de-salud-publica-aprueba-guia-de-buenas-practicas-de-fabricacion-de-dispositivos-medicos-y-dispositivos-medicos-de-diagnosticos-in-vitro)
- El ISP sometió a consulta pública la 5ª edición de la Guía del Sistema Nacional de Tecnovigilancia, que se aplica a dispositivos médicos usados en el país. Los incidentes y eventos adversos se notifican a ese sistema — [AZ](https://www.az.cl/isp-somete-a-consulta-publica-la-quinta-edicion-de-la-guia-del-sistema-nacional-de-tecnovigilancia/); [Carey](https://www.carey.cl/isp-somete-a-consulta-publica-guia-del-sistema-nacional-de-tecnovigilancia)
- La IG 4 de ANCI exige segmentar redes para evitar el movimiento lateral y usar firewalls *default-deny* — [Actualidad Jurídica DOE](https://actualidadjuridica.doe.cl/anci-fija-estandares-obligatorios-para-operadores-vitales-delegado-de-ciberseguridad-reporte-de-incidentes-y-contencion-inmediata/)

### Inferences
- Si un sensor conectado a Fricke Store es un dispositivo médico, un incidente de ciberseguridad que lo afecte podría tener que reportarse a ANCI (por afectar la salud de las personas) y también a tecnovigilancia del ISP. Esta inferencia no está confirmada por las fuentes.
- Como referencia técnica para IoT y cámaras (sin fuerza obligatoria en Chile) se pueden usar NISTIR 8259A, IEC 62443 y la guía FDA de ciberseguridad premarket; no se verificaron en esta sesión.

### Gaps
- No se encontró ninguna norma chilena sobre la seguridad de cámaras o CCTV en hospitales, más allá de la protección de datos (Ley 21.719, cubierta por otra línea de investigación).
- Plazos pendientes no confirmados: protocolos sectoriales de ANCI para salud, reglamento de calificación de OIV con plazos de implementación y la próxima revisión del DS 7 (debía hacerse cada 2 años desde su entrada en vigencia, es decir, alrededor de 2025).
