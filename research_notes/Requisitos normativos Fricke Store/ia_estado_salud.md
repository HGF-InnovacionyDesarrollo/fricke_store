# IA generativa (asistente LLM con RAG) en un hospital público chileno: obligaciones, orientaciones y buenas prácticas

Contexto: asistente de chat en la portada de "Fricke Store" (Hospital Dr. Gustavo Fricke, red pública) que responde dudas del personal sobre protocolos y documentos institucionales (RAG) y que más adelante podría resumir documentos. Modelo local o API en la nube (proveedores de EE. UU.). Notas actualizadas al 16-nov-2026.

Advertencia general: varias fechas de 2026 provienen de fuentes secundarias (prensa, columnas, consultoras). Antes de decidir conviene confirmarlas en senado.cl, camara.cl y bcn.cl.

## 1. Política Nacional de IA (actualizada en 2024) y su plan de acción: qué aplica a los órganos públicos

### Takeaway
La Política Nacional de IA (2021, actualizada en mayo de 2024) y su plan de acción no imponen obligaciones legales directas a un hospital. Su bajada práctica al Estado es el **Oficio Circular N° 711 (11-dic-2023)** de SEGPRES y MinCiencia, con lineamientos no obligatorios pero aplicables a todo órgano de la Administración que use IA. El plan también incluye herramientas de GobLab UAI, como la ficha de transparencia algorítmica y la medición de sesgos.

### Cited Findings
- La Política Nacional de IA se lanzó el 28-oct-2021 con tres ejes (factores habilitantes, desarrollo y adopción, gobernanza y ética) y un plan de acción con un horizonte de 10 años — [MinCiencia, Plan de Acción IA v2](https://minciencia.gob.cl/uploads/filer_public/4a/ce/4acec1c3-9219-46bb-b78f-74f851c3403d/plan_de_accion_ia_v2.pdf); [Bloomberg Línea, 28-oct-2021](https://www.bloomberglinea.com/2021/10/28/chile-presenta-su-primera-politica-nacional-de-inteligencia-artificial/)
- En mayo de 2024 se presentó la actualización de la Política y de su plan de acción, con énfasis en una IA centrada en las personas y en los derechos fundamentales. El mismo proceso incluyó la circular sobre uso responsable de IA en el sector público — [Carey, nota sobre la política](https://www.carey.cl/api/archivo/chile-presenta-su-primera-politica-nacional-de-inteligencia-artificial?lang=es) (síntesis del buscador; no se obtuvo el texto íntegro de la actualización 2024)
- **Oficio Circular N° 711**, del 11-dic-2023, firmado por el Ministro SEGPRES y la Ministra de Ciencia: "Lineamientos para el uso de herramientas de IA en el sector público". Rige desde el 1-ene-2024, no es obligatorio y se dirige a todo órgano de la Administración del Estado que desarrolle, implemente o use IA — [DOE Actualidad Jurídica, 20-dic-2023](https://actualidadjuridica.doe.cl/lineamientos-para-el-uso-de-herramientas-de-inteligencia-artificial-en-el-sector-publico/); [DF, lineamientos](https://www.df.cl/df-lab/transformacion-digital/gobierno-publica-lineamientos-para-el-uso-responsable-de-inteligencia)
- Contenido del Oficio 711 (cuatro lineamientos):
  - **Personas al centro:** evaluar si la IA es la solución adecuada, evitar discriminación arbitraria y seguir la "Guía de Formulación Ética de Proyectos de Ciencia de Datos" de Gobierno Digital.
  - **Transparencia y explicabilidad:** informar a la ciudadanía sobre las herramientas de IA en uso y **comunicar por medios idóneos el uso de chatbots** en la relación con las personas.
  - **Privacidad:** tratar los datos personales, sobre todo los sensibles, conforme a la Ley 19.628. **No ingresar información personal, en especial sensible, en herramientas de IA generativa que no hayan sido contratadas o desarrolladas por o para el órgano.** Cumplir el DS 7/2023 (seguridad de la información y ciberseguridad) y el DS 11/2023 (plataformas electrónicas).
  - **Capacitación:** formar a los funcionarios.
  - Seguimiento: la División de Gobierno Digital puede pedir información a los Coordinadores de Transformación Digital.
  - Fuente: [DOE](https://actualidadjuridica.doe.cl/lineamientos-para-el-uso-de-herramientas-de-inteligencia-artificial-en-el-sector-publico/)
- El Oficio 711 no contiene una recomendación explícita de supervisión humana — [DOE](https://actualidadjuridica.doe.cl/lineamientos-para-el-uso-de-herramientas-de-inteligencia-artificial-en-el-sector-publico/)
- El 26-jun-2024, MinCiencia, Hacienda, la Secretaría de Gobierno Digital y GobLab UAI presentaron, como parte del Plan de Acción de la Política, las herramientas "Ficha de transparencia algorítmica" y "Medición de sesgos y equidad estadística" — [Hacienda, nota](https://www.hacienda.cl/noticias-y-eventos/noticias/ministerios-de-ciencia-y-hacienda-lanzan-herramientas-para-un-desarrollo)
- Existe la iniciativa "Salud a la VanguardIA" (MinCiencia, MINSAL, CENIA y Laboratorio de Gobierno) para identificar problemas de gestión hospitalaria y diseñar soluciones con IA — [DPL News](https://dplnews.com/chile-salud-a-la-vanguardia-inteligencia-artificial-para-mejorar-la-gestion-en-la-salud-publica/)

### Inferences
- Para el hospital, el Oficio 711 es el estándar mínimo de referencia. Un asistente de protocolos debería: (a) anunciar que es IA, (b) usar solo un modelo contratado o desarrollado por o para el hospital o el Servicio de Salud (no ChatGPT u otros servicios de consumo con cuentas personales), (c) cumplir el DS 7/2023 y (d) acompañarse de capacitación.
- La regla de "no ingresar datos personales en IA generativa no contratada" refuerza la necesidad de un filtro de PII/RUT y de un contrato formal con el proveedor de nube.

### Gaps
- No se obtuvo el texto íntegro de la Política actualizada 2024 ni de su plan de acción 2024, por lo que no se pudo listar las acciones específicas para el Estado o la salud.
- No se verificó si existe una versión posterior del Oficio 711 (2025-2026) ni una guía específica de Gobierno Digital sobre IA generativa.

## 2. Proyecto de ley de IA (boletines 16.821-19 y 15.869-19, refundidos): estado a noviembre de 2026, categorías de riesgo y transparencia

### Takeaway
Al 16-nov-2026 **Chile no tiene una ley de IA**. El proyecto está en segundo trámite en el Senado: la Comisión de Desafíos del Futuro lo aprobó en general el 26-oct-2026, el Ejecutivo anunció una indicación sustitutiva y el plazo de indicaciones propuesto es el 4-dic-2026. El texto de la Cámara tiene cuatro niveles de riesgo y exige informar que se interactúa con IA. Un chatbot interno de protocolos se ubicaría probablemente en "riesgo limitado" (deber de transparencia), no en "alto riesgo". La propuesta del Gobierno de 2026 podría cambiar ese esquema.

### Cited Findings
- Tramitación:
  - 7-may-2024: ingresa el mensaje del Ejecutivo (boletín 16.821-19), refundido con la moción 15.869-19 de abril de 2023.
  - 4-ago-2025: la Cámara lo aprueba en general.
  - 13-oct-2025: oficio al Senado.
  - 14-oct-2025: pasa a la Comisión de Desafíos del Futuro.
  - 6-ene-2026 y 20-ene-2026: urgencia suma.
  - Fuentes: [Neuronet, 3-feb-2026](https://neuronet.cl/ley-inteligencia-artificial-chile/); [Fundación Progresa, datos al 30-oct-2026](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/); [Senado, noticia de ingreso a la comisión](https://www.senado.cl/comunicaciones/noticias/proyecto-que-regula-sistemas-de-inteligencia-artificial-sera-estudiado-por)
- 26-may-2026: la ministra de Ciencia presenta al Senado un enfoque alternativo de "ley marco" con seis pilares — [Senado, "Senadores conocen propuesta del Ejecutivo para ley marco de IA"](https://www.senado.cl/comunicaciones/noticias/senadores-conocen-propuesta-del-ejecutivo-para-ley-marco-de-ia); [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/)
- 1-sep-2026: el Ejecutivo baja la urgencia a "simple". 26-oct-2026: la Comisión de Desafíos del Futuro aprueba en general por unanimidad. El Ejecutivo presentará una indicación sustitutiva antes del 4-dic-2026, plazo de indicaciones que aún requiere ratificación de la Sala — [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/); [El Dínamo, opinión, 3-nov-2026](https://www.eldinamo.cl/opinion/2026/11/03/ley-de-ia-en-chile-el-riesgo-de-llegar-tarde-a-regular-el-futuro/); [BioBioChile, 28-oct-2026](https://www.biobiochile.cl/noticias/opinion/columnas-bbcl/2026/10/28/la-inteligencia-artificial-no-espera-a-chile.shtml); [BioBioChile, 5-nov-2026](https://www.biobiochile.cl/noticias/nacional/chile/2026/11/05/rojo-edwards-dice-que-se-debe-reformular-y-redisenar-el-segundo-piso-de-la-moneda.shtml)
- Texto aprobado por la Cámara:
  - **Cuatro categorías de riesgo** (art. 6): inaceptable, alto, limitado y sin riesgo evidente. No hay anexo que liste los sistemas de cada categoría.
  - **Siete usos prohibidos** (art. 7), entre ellos el reconocimiento de emociones en el trabajo y en la educación, el reconocimiento facial en tiempo real en espacios públicos (con excepciones) y el puntaje social discriminatorio.
  - **Obligaciones para alto riesgo** (arts. 8 a 10, modelo UE): gestión de riesgos, gobernanza de datos, documentación técnica, registros, **supervisión humana**, precisión, robustez y ciberseguridad.
  - Fuentes: [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/); [IAPP, aprobación en primer trámite](https://iapp.org/news/a/se-aprueba-en-primer-tr-mite-constitucional-el-proyecto-que-regula-los-sistemas-de-ia-en-chile)
- Transparencia en el texto de la Cámara: **las personas deben ser informadas de que interactúan con un sistema de IA**, y el contenido sintético (texto, audio, imagen o video) debe identificarse como generado o manipulado artificialmente. Un análisis indica que un chatbot de atención probablemente queda en "riesgo limitado", cuyo foco es la transparencia — [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/); [IAPP](https://iapp.org/news/a/se-aprueba-en-primer-tr-mite-constitucional-el-proyecto-que-regula-los-sistemas-de-ia-en-chile). La numeración del artículo de transparencia difiere entre versiones (se cita un art. 5), por lo que no fue posible confirmarla.
- Fiscalización y sanciones:
  - Texto de la Cámara: multas de hasta 20.000 UTM, a cargo de la Agencia de Protección de Datos Personales, pero sin procedimiento sancionatorio propio.
  - Propuesta del Gobierno (2026): **sin sanciones específicas de IA**. Cada infracción se sancionaría con la ley sectorial que corresponda (datos personales, ciberseguridad, consumidor, propiedad intelectual). Tendrían rol la ANCI, la APDP y ChileCompra, coordinadas por MinCiencia, con sandboxes regulatorios de dos años. Además, reemplazaría las categorías fijas por una regulación proporcional al contexto y al impacto.
  - Fuente: [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/)
- El mensaje original del Ejecutivo (2024) está disponible en [Diario Constitucional (PDF boletín 16821-19)](https://diarioconstitucional.cl/wp-content/uploads/2024/08/16821-19.pdf) y en [Cámara, documento de la iniciativa](https://www.camara.cl/verDoc.aspx?prmID=17048&prmTIPO=INICIATIVA).
- Hay una moción paralela de senadores para regular el uso ético de la IA en la investigación biomédica (dic-2025) — [Diario Constitucional, 20-dic-2025](https://www.diarioconstitucional.cl/2025/12/20/senadores-proponen-regular-uso-etico-de-ia-en-investigacion-biomedica/)

### Inferences
- Un asistente que responde preguntas del personal sobre protocolos, sin decidir sobre derechos de pacientes ni de funcionarios, no encaja en los ejemplos de alto riesgo citados (contratación, prestaciones, inspecciones). Sí le aplicaría el deber de informar que se trata de IA. Si en el futuro el asistente apoya decisiones clínicas (triaje, diagnóstico) o de personal, su clasificación podría subir.
- La ley no estará vigente en el corto plazo: al menos queda el segundo trámite completo, posiblemente una comisión mixta, y la vigencia diferida. Conviene diseñar ya según el texto de la Cámara y el AI Act como "estándar anticipado" sin depender de esas fechas.

### Gaps
- No se obtuvo de senado.cl el acta oficial de la votación del 26-oct-2026 ni el texto de la indicación sustitutiva (pendiente al 4-dic-2026).
- No se confirmó si el texto de la Cámara menciona expresamente la salud o el sector público como alto riesgo. Ninguna fuente consultada lo afirma.

## 3. Guía gubernamental sobre IA en el Estado: Gobierno Digital, CPLT (transparencia algorítmica), Contraloría y ChileCompra

### Takeaway
Hay tres instrumentos no vinculantes pero directamente pertinentes. (1) El Oficio Circular 711/2023 (ver sección 1). (2) Las **Recomendaciones del CPLT sobre Transparencia Algorítmica (Res. Exenta N° 372/2024)**, con su guía de adopción de junio-julio de 2025: proponen una sección "Transparencia Algorítmica" en el portal de transparencia activa, enfocada en sistemas de decisión automatizada o semiautomatizada. (3) La **Directiva de Contratación Pública N° 44/2026 de ChileCompra** (12-mar-2026) y las Bases Tipo de IA (Res. N° 60/2022) para comprar IA.

### Cited Findings
- El CPLT aprobó "Recomendaciones del Consejo para la Transparencia sobre Transparencia Algorítmica" (Resolución Exenta N° 372 de 2024) en lugar de la Instrucción General que se proyectaba para 2023. Su objeto es promover buenas prácticas de transparencia en los sistemas de decisión automatizada y semiautomatizada del Estado. Sugieren una sección "Transparencia Algorítmica" en los portales de transparencia activa, con información periódica sobre los sistemas — [Minuta CPLT, SEGPRES nov-2025](https://www.minsegpres.gob.cl/wp-content/uploads/2025/11/MINUTA-CPLT.pdf); [Uniandes, resumen de las recomendaciones](https://algoritmos.uniandes.edu.co/recommendations-of-the-transparency-council-on-algorithmic-transparency-recomendaciones-del-consejo-para-la-transparencia-sobre-transparencia-algoritmica/); [Diario Constitucional, 10-sep-2024](https://www.diarioconstitucional.cl/2024/09/10/luces-y-sombras-de-la-transparencia-algoritmica-en-las-recomendaciones-del-consejo-para-la-transparencia-cplt-por-lorayne-finol-romero/)
- En julio de 2025 el CPLT publicó una "Guía de Transparencia Algorítmica" (fechada en junio de 2025) para que los órganos adopten las recomendaciones con información clara, accesible y periódica — [CPLT, Guía PDF jun-2025](https://www.consejotransparencia.cl/wp-content/uploads/page/2024/05/GUIA-Transparencia-Algoritmica-junio-2025.pdf); [Diario Constitucional, 17-jul-2025](https://www.diarioconstitucional.cl/2025/07/17/consejo-para-la-transparencia-lanza-guia-pionera-sobre-transparencia-algoritmica-en-decisiones-automatizadas-del-estado/). No se pudo leer el PDF por su tamaño.
- Antecedente: el estudio UAI-CPLT "Transparencia Algorítmica en el Sector Público" (2021) catastró 219 sistemas y evaluó 12 — [Estudio GobLab-CPLT](https://staticcl1.fidelizador.com/cptcomunica/ESTUDIO%20TRANSPARENCIA%20ALGORITMICA%20EN%20EL%20SECTOR%20PUBLICO%20GOBLAB%20CPLT%20final...-1.pdf)
- ChileCompra:
  - **Directiva N° 44/2026** (publicada el 12-mar-2026), que actualiza la de 2023 creada en el proyecto Algoritmos Éticos de la UAI, con recomendaciones para contratar proyectos de ciencia de datos e IA. Recomienda planificación rigurosa, equipos multidisciplinarios y evaluar aspectos éticos, legales y técnicos antes de licitar.
  - Las **Bases Tipo para "Proyectos de Ciencia de Datos e IA"** (Res. N° 60, dic-2022) incluyen requisitos éticos.
  - Fuentes: [ChileCompra, 12-mar-2026](https://www.chilecompra.cl/2026/03/chilecompra-actualiza-directiva-para-la-contratacion-de-proyectos-de-ciencia-de-datos-e-inteligencia-artificial/); [ChileCompra, bases tipo ene-2023](https://www.chilecompra.cl/2023/01/ya-se-encuentra-disponible-bases-tipo-para-licitar-proyectos-de-algoritmos-e-inteligencia-artificial-con-requisitos-eticos/); [OECD.AI, Directiva 44/2026](https://oecd.ai/en/dashboards/policy-initiatives/public-procurement-directive-no-442026-for-data-science-and-artificial-intelligence-projects)
- En la propuesta del Gobierno de 2026 para la ley de IA, ChileCompra tendría un rol, que podría ejercerse mediante bases de licitación — [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/)

### Inferences
- El CPLT apunta a sistemas que deciden o apoyan decisiones sobre personas. Un asistente de consulta de protocolos queda en el borde de ese alcance. Aun así, publicar una "ficha de transparencia algorítmica" (finalidad, modelo y proveedor, datos usados, responsable, limitaciones) en el portal o en transparencia activa es una buena práctica de bajo costo y coherente con el Oficio 711 y la herramienta GobLab de 2024.
- Si se contrata una API de nube, la compra debería pasar por la Directiva 44/2026 o las Bases Tipo: cláusulas de no entrenamiento con datos del hospital, ubicación y retención de datos, auditoría, salida y portabilidad, y seguridad conforme al DS 7/2023.

### Gaps
- **Contraloría (CGR):** no se encontró un dictamen o guía específica sobre IA generativa en la Administración. No se buscó a fondo; queda pendiente.
- No se verificó si la Secretaría de Gobierno Digital publicó en 2025-2026 una guía específica de IA generativa para funcionarios (más allá del Oficio 711 y de su wiki de datos personales).

## 4. MINSAL, Superintendencia de Salud, OMS/OPS y AI Act de la UE

### Takeaway
No se encontró una norma ni una orientación formal del MINSAL o de la Superintendencia de Salud específica sobre IA generativa o LLM (al 16-nov-2026). Como referencia internacional, sirven: la **guía de la OMS sobre modelos multimodales grandes (LMM), de enero de 2024**, con más de 40 recomendaciones y deberes para quienes despliegan; la **guía de la OPS de octubre de 2025** sobre diseño de instrucciones de IA en salud pública, que enfatiza la supervisión humana; y el **AI Act de la UE**, cuyo art. 50 (informar que se interactúa con IA) aplica desde el 2-ago-2026, mientras que los sistemas de alto riesgo del Anexo III se postergaron al 2-dic-2027 (Digital Omnibus).

### Cited Findings
- MINSAL: en la búsqueda solo aparecen iniciativas, como "Salud a la VanguardIA", el anuncio de un Departamento de Salud Digital y la Estrategia de Digitalización e Interoperabilidad, pero no orientaciones normativas sobre IA generativa — [DPL News](https://dplnews.com/chile-salud-a-la-vanguardia-inteligencia-artificial-para-mejorar-la-gestion-en-la-salud-publica/); [MINSAL/CEPAL, estrategia de digitalización](https://www.cepal.org/sites/default/files/news/files/estrategia-de-digitalizacion-e-interoperabilidad-en-salud-en-chile-minsal.pdf)
- La Superintendencia de Salud emitió la Circular IF/N° 514 (oct-2025) sobre telemedicina, que menciona iniciativas de IA en atenciones. No es una regulación de LLM — [SuperSalud, Circular IF 514-2025](https://www.superdesalud.gob.cl/app/uploads/2025/10/circular-if-n-514-2025.pdf)
- Una columna del exministro Jaime Manalich (7-nov-2026) plantea que Chile necesita un marco público de evaluación de IA clínica (validación local y monitoreo) articulado entre MINSAL, ISP y APDP. Es una opinión — [The Clinic](https://www.theclinic.cl/2026/11/07/columna-de-jaime-manalich-la-ia-ya-entro-a-la-clinica/)
- **OMS, "Ethics and governance of AI for health: Guidance on large multi-modal models" (18-ene-2024):**
  - Cubre cinco usos, entre ellos tareas administrativas y educación médica.
  - Advierte sobre respuestas falsas, inexactas, sesgadas o incompletas y sobre riesgos de ciberseguridad.
  - Para quienes despliegan: evitar entornos inadecuados, comunicar riesgos previsibles y errores que hayan causado daño, y suspender o retirar el uso si hay daño.
  - Para gobiernos: auditorías posteriores e independientes y evaluaciones de impacto (protección de datos y derechos humanos) en despliegues a gran escala.
  - Fuentes: [OMS, nota de prensa](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models); [UN Innovation Network, ficha](https://www.uninnovation.network/innovation-library/ethics-and-governance-of-artificial-intelligence-for-health-guidance-on-large-multi-modal-models)
- **OPS (20-oct-2025):** guía "Diseño de instrucciones de IA para la salud pública" (Programa de Alfabetización Digital), sobre cómo redactar prompts para obtener contenido fiable y culturalmente adecuado. Advierte de los riesgos de la IA generativa en salud pública y enfatiza la supervisión humana — [OPS, noticia](https://www.paho.org/es/noticias/20-10-2025-ops-publica-guia-para-disenar-instrucciones-inteligencia-artificial-salud). La OPS y el BID tienen además un kit de evaluación de preparación para la IA en salud pública (fecha no confirmada) — [ConsultorSalud](https://consultorsalud.com/ops-bid-herramienta-ia-sistemas-salud-publica/)
- **AI Act (Reglamento UE 2024/1689):**
  - El art. 50.1 exige a los proveedores diseñar los sistemas que interactúan con personas de modo que estas sepan que interactúan con IA. Aplica desde el 2-ago-2026 y no fue aplazado por el Digital Omnibus.
  - Los sistemas de alto riesgo del Anexo III pasan al 2-dic-2027, y los del Anexo I (productos regulados, como los dispositivos médicos) al 2-ago-2028.
  - Las fuentes discrepan sobre la fecha del marcado legible por máquina (art. 50.2) y sobre si el Omnibus ya se publicó en el DOUE.
  - Fuentes: [Jones Walker](https://www.joneswalker.com/en/insights/blogs/ai-law-blog/yes-august-2-still-matters-the-eu-approved-a-high-risk-ai-delay-but-most-trans.html); [Holistic AI](https://www.holisticai.com/blog/eu-ai-acts-deadline-moved-2027); [EUR-Lex, Reglamento 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
- Según el texto del AI Act, el Anexo III punto 5 incluye como alto riesgo los sistemas que usan autoridades públicas para evaluar el derecho a prestaciones esenciales, incluida la atención de salud, y los de triaje de pacientes en emergencias. El software con finalidad médica cae en el Anexo I, vía el Reglamento de Dispositivos Médicos (MDR) — [EUR-Lex, Reglamento 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj). Este punto proviene del conocimiento previo del texto y no se releyó en esta sesión.

### Inferences
- Como referencia de la UE, un asistente de protocolos para el personal no sería de alto riesgo, pero sí le aplicaría el art. 50.1. Resumir documentos clínicos de pacientes o recomendar conductas clínicas podría acercarlo a un dispositivo médico (Anexo I y MDR) o a un sistema de triaje (Anexo III).
- En ausencia de una norma del MINSAL, lo razonable es adoptar la guía de la OMS 2024 como marco ético y documentarlo en una política interna del hospital o del Servicio de Salud Viña del Mar-Quillota.

### Gaps
- No se encontró una actualización 2025 de la guía de la OMS sobre LMM ni otra guía de la OMS de 2025 específica para LLM. Tampoco orientaciones del ISP sobre software como dispositivo médico con IA.
- No se revisó si la Superintendencia de Salud tiene criterios de acreditación (calidad y seguridad del paciente) que alcancen herramientas de IA.

## 5. Ley 21.719 (protección de datos) y el asistente: decisiones automatizadas, transferencia internacional a EE. UU. y EIPD

### Takeaway
La Ley 21.719 (DO 13-dic-2024) entra en vigencia el **1-dic-2026**. El Senado aprobó el 28-oct-2026 postergarla al **15-oct-2027**, pero ese proyecto sigue en la Cámara: mientras no se publique, rige la fecha original. Para el asistente importan cinco puntos:
- **Datos de salud** (art. 16 bis): solo pueden tratarse para los fines de las leyes sanitarias.
- **Transferencia internacional** (arts. 27-28): no hay adecuación de EE. UU. Se necesitan cláusulas contractuales o garantías adecuadas, y las excepciones solo cubren transferencias específicas y no habituales.
- **EIPD obligatoria** (art. 15 ter) si hay tratamiento masivo, de datos sensibles o decisiones automatizadas con efectos significativos.
- **Notificación de brechas** (art. 14 sexies).
- **Art. 8° bis**: solo se activa si el asistente toma decisiones con efectos significativos sobre personas.

### Cited Findings
- Publicada en el Diario Oficial el 13-dic-2024. La vigencia legal es el 1-dic-2026 (artículo primero transitorio) — [Diario Constitucional, 12-jun-2026](https://www.diarioconstitucional.cl/2026/06/12/la-ley-21-719-entra-en-vigor-el-1-de-diciembre-y-expone-vacios-en-regulacion-de-pequenas-empresas/); [Diario Oficial, texto de la ley](https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf)
- Postergación:
  - 1-sep-2026: el Gobierno ingresa el boletín 18.623-07.
  - 28-oct-2026: el Senado lo aprueba 33-6, con nueva fecha 15-oct-2027 y un Consejo de la APDP ampliado de 3 a 5 integrantes. Pasa a la Cámara.
  - Mientras no se publique, la fecha legal sigue siendo el 1-dic-2026.
  - Fuentes: [Garrigues](https://www.garrigues.com/es_ES/noticia/senado-chileno-aprueba-proyecto-ley-busca-postergar-15-octubre-2027-entrada-vigencia-nueva); [La Tercera](https://www.latercera.com/nacional/noticia/senado-aprueba-postergacion-de-entrada-en-vigencia-de-ley-de-proteccion-de-datos-personales-iniciativa-pasa-a-la-camara/); [Diario Constitucional](https://www.diarioconstitucional.cl/legislativo/la-ley-que-espera-a-su-guardian-la-postergacion-de-la-ley-n-21719-y-lo-que-el-proyecto-deja-sin)
- **Art. 8° bis (decisiones individuales automatizadas):**
  - El titular tiene derecho a oponerse y a no ser objeto de decisiones basadas en tratamiento automatizado, incluida la elaboración de perfiles, que produzcan efectos jurídicos o le afecten significativamente.
  - Excepciones: contrato, consentimiento expreso o ley con salvaguardas.
  - En todos los casos el responsable debe asegurar información y transparencia, el **derecho a obtener una explicación, la intervención humana** y el derecho a expresar su punto de vista.
  - Fuente: [Diario Oficial, Ley 21.719](https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf)
- **Art. 15 ter (EIPD):**
  - Obligatoria, antes de iniciar el tratamiento, cuando sea probable un alto riesgo "por su naturaleza, alcance, contexto, tecnología utilizada o fines".
  - Siempre en estos casos: a) evaluación sistemática o decisiones automatizadas con efectos jurídicos significativos; b) tratamiento masivo o a gran escala; c) monitoreo sistemático de zonas públicas; d) datos sensibles en las hipótesis de excepción al consentimiento.
  - La APDP publicará una lista orientativa y orientaciones mínimas.
  - Fuente: [Diario Oficial, Ley 21.719](https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf)
- **Art. 16 bis (salud):** los datos relativos a la salud y al perfil biológico solo pueden tratarse para los fines de las leyes especiales en materia sanitaria. Sin consentimiento, solo en los casos tasados del artículo — [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf)
- **Art. 14 sexies (brechas):**
  - Reportar a la Agencia sin dilaciones indebidas las vulneraciones de seguridad con riesgo razonable para los titulares, y llevar un registro de ellas.
  - Si afectan **datos sensibles**, comunicar también a cada titular en lenguaje claro.
  - Fuente: [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf)
- **Arts. 27-28 (transferencia internacional):**
  - La transferencia es lícita si: a) va a un país adecuado (lo declara la APDP); b) hay cláusulas contractuales, normas corporativas vinculantes u otros instrumentos con garantías adecuadas; o c) hay un modelo de cumplimiento o certificación.
  - Sin adecuación ni garantías, solo se permite una transferencia "específica y que no sea habitual" (por ejemplo, con consentimiento expreso).
  - Según el art. 28, las garantías adecuadas deben otorgar derechos exigibles y acciones efectivas a los titulares.
  - Fuente: [Diario Oficial](https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf)
- No existe un listado chileno de países adecuados. Un análisis sostiene que declarar adecuado a EE. UU. en su conjunto sería improcedente porque carece de una autoridad nacional de protección de datos. Agrega que el uso de nube implica habitualmente transferencia internacional y que las excepciones del art. 27 no sirven para flujos habituales — [DOE, entrevista a Oliver Ortiz](https://actualidadjuridica.doe.cl/oliver-ortiz-sobre-transferencias-internacionales-de-datos-la-adecuacion-de-una-jurisdiccion-requiere-un-pronunciamiento-de-la-autoridad/)
- Se aprobaron cláusulas contractuales modelo para transferencias internacionales, basadas en la guía de la Red Iberoamericana, publicadas en el Diario Oficial un 19 de diciembre (probablemente 2025) y vigentes de forma transitoria hasta que regule la Agencia. Debe confirmarse quién las aprobó y su alcance — [BCN LeyChile, norma 1219636](https://www.bcn.cl/leychile/navegar?idNorma=1219636); [Guerrero Olivos, ene-2026](https://guerrero.cl/wp-content/uploads/2026/01/DOC_Aprobacion-Clausulas-Contractuales-Tipo.pdf)
- La Secretaría de Gobierno Digital publica una "Guía Práctica para la implementación de la nueva Ley de Protección de Datos Personales en la Administración". No se pudo leer su contenido — [Wiki Guías Gobierno Digital](https://wikiguias.digital.gob.cl/datos-personales/guia-practica-implementacion-nueva-ley-datos-personales)
- Recomendaciones de abogados (AZ, 5-ago-2026) para IA bajo la Ley 21.719:
  - Mapear los datos e inventariar los sistemas de IA y sus fines.
  - Cifrar en tránsito y en reposo, y controlar accesos.
  - Actualizar los contratos con proveedores.
  - Formar comités multidisciplinarios y medir métricas de desempeño de la IA.
  - Fuente: [AZ Abogados](https://www.az.cl/ley-de-proteccion-de-datos-e-inteligencia-artificial-el-doble-desafio-que-enfrentan-las-empresas-en-chile/)
- La seguridad de la información del Estado se rige además por el DS 7/2023, y las brechas también por la Ley Marco de Ciberseguridad 21.663 — [DOE, Oficio 711](https://actualidadjuridica.doe.cl/lineamientos-para-el-uso-de-herramientas-de-inteligencia-artificial-en-el-sector-publico/); [AZ](https://www.az.cl/ley-de-proteccion-de-datos-e-inteligencia-artificial-el-doble-desafio-que-enfrentan-las-empresas-en-chile/)

### Inferences
- **Decisiones automatizadas:** un asistente que solo informa protocolos al personal no adopta decisiones sobre titulares, así que el art. 8° bis en principio no se activa. Sí se activaría si se usara para priorizar pacientes, evaluar funcionarios o asignar prestaciones.
- **Transferencia internacional:**
  - Si los prompts pueden contener datos personales (aunque esté prohibido), enviarlos a una API en EE. UU. es una transferencia internacional habitual. Requiere un contrato con cláusulas modelo o garantías equivalentes (art. 27 b) y, para datos de salud, cumplir además el art. 16 bis.
  - Un filtro de PII y RUT, más una política de "cero datos de pacientes", reduce el riesgo, pero no elimina la necesidad de base contractual si existe la posibilidad real de que se filtren datos.
  - El alojamiento local o en una región dentro de Chile evita el problema.
- **EIPD:** si el documento fuente incluye datos de pacientes (por ejemplo, la función futura de resumir documentos) o si el uso es masivo, se dispara el art. 15 ter, letras b) y d). Conviene hacer una EIPD voluntaria desde ya, porque es buena práctica y deja trazabilidad.
- Los logs de prompts son tratamiento de datos personales de funcionarios (usuario, RUT de login) y, potencialmente, de pacientes. Requieren finalidad declarada, plazo de retención, control de acceso y cifrado, y quedan sujetos al deber de reporte de brechas.

### Gaps
- No se verificó si la APDP (cuyos consejeros asumirían en oct-2026) ya publicó la lista orientativa de EIPD o una regulación sobre transferencias.
- No se obtuvo el texto del Título IV (tratamiento por órganos públicos) ni el régimen sancionatorio aplicable a órganos públicos.

## 6. Buenas prácticas: filtro de PII y RUT, logs y retención, supervisión humana, avisos, evaluación, alucinaciones y citas

### Takeaway
Ninguna norma chilena fija controles técnicos específicos para LLM. Las buenas prácticas se derivan del Oficio 711 (aviso de chatbot, no ingresar datos personales en IA no contratada), de la Ley 21.719 (seguridad, EIPD, brechas, transferencias), de la OMS 2024 (comunicar riesgos y errores, suspender si hay daño, auditoría y evaluación de impacto), de la OPS 2025 (supervisión humana, diseño de prompts) y del AI Act (art. 50 y, como referencia, los requisitos de alto riesgo del art. 14 sobre supervisión humana y del art. 12 sobre registros).

### Cited Findings
- **Aviso de IA:** el Oficio 711 pide comunicar por medios idóneos el uso de chatbots. El proyecto de ley exige informar la interacción con IA. El AI Act art. 50.1 aplica desde el 2-ago-2026 — [DOE](https://actualidadjuridica.doe.cl/lineamientos-para-el-uso-de-herramientas-de-inteligencia-artificial-en-el-sector-publico/); [Fundación Progresa](https://fundacionprogresa.cl/ley-inteligencia-artificial-chile/); [Jones Walker](https://www.joneswalker.com/en/insights/blogs/ai-law-blog/yes-august-2-still-matters-the-eu-approved-a-high-risk-ai-delay-but-most-trans.html)
- **No ingresar datos personales en IA no contratada:** [DOE, Oficio 711](https://actualidadjuridica.doe.cl/lineamientos-para-el-uso-de-herramientas-de-inteligencia-artificial-en-el-sector-publico/)
- **Riesgo de respuestas falsas, inexactas o incompletas** en salud. El que despliega debe comunicar riesgos y errores y poder suspender el uso — [OMS, 18-ene-2024](https://www.who.int/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models)
- **Supervisión humana y prompts bien diseñados** (OPS 2025) — [OPS](https://www.paho.org/es/noticias/20-10-2025-ops-publica-guia-para-disenar-instrucciones-inteligencia-artificial-salud)
- **Evaluación y medición de sesgos:** herramienta "Medición de sesgos y equidad estadística" y "Ficha de transparencia algorítmica" (GobLab UAI, 2024) — [Hacienda](https://www.hacienda.cl/noticias-y-eventos/noticias/ministerios-de-ciencia-y-hacienda-lanzan-herramientas-para-un-desarrollo)
- **Gobernanza:** inventario de sistemas de IA, comités multidisciplinarios, métricas de desempeño por caso de uso y cifrado — [AZ Abogados](https://www.az.cl/ley-de-proteccion-de-datos-e-inteligencia-artificial-el-doble-desafio-que-enfrentan-las-empresas-en-chile/)
- **Columna crítica sobre automatizar sin supervisión** en salud — [Portal Innova](https://portalinnova.cl/?p=255288)

### Inferences (propuestas de diseño para Fricke Store, no exigidas literalmente por norma)
1. **Filtro previo al envío al modelo (obligatorio si hay API externa):**
   - Detectar RUT con regex (`\b\d{1,2}\.?\d{3}\.?\d{3}-[\dkK]\b`) y validar el dígito verificador con módulo 11 para reducir falsos positivos.
   - Detectar también nombres junto a palabras clínicas, números de ficha clínica o episodio, fechas de nacimiento, teléfonos, correos y direcciones.
   - Ante una detección: bloquear el envío y mostrar un mensaje ("no ingrese datos de pacientes") o seudonimizar. Registrar solo el evento, no el dato.
   - Aplicar el mismo filtro a los documentos indexados para RAG.
2. **Aviso visible y permanente:** "Está conversando con un asistente de IA. Puede equivocarse. Verifique en el documento oficial citado. No ingrese datos de pacientes. No reemplaza el juicio clínico ni las instrucciones de su jefatura". Agregar el enlace a la ficha de transparencia algorítmica.
3. **Respuestas fundadas y con cita:**
   - Contestar solo a partir de los documentos recuperados, citando el título, la versión o vigencia y la sección, con enlace.
   - Si no hay evidencia suficiente, responder "no encontré esto en los protocolos vigentes".
   - Indexar solo documentos aprobados y vigentes, con control de versiones y retiro de los obsoletos.
   - Usar temperatura baja.
4. **Logs y retención:**
   - Registrar fecha, usuario (seudonimizado si es posible), pregunta filtrada, documentos citados, versión del modelo y del índice, y retroalimentación.
   - Fijar un plazo de retención breve y declarado (por ejemplo, de 90 a 180 días para análisis de calidad) en la política de privacidad del portal.
   - Restringir el acceso y cifrar.
   - En la nube, contratar la opción de cero retención o no entrenamiento del proveedor.
5. **Supervisión humana:**
   - Designar un responsable clínico y uno de TI como dueños del asistente.
   - Revisar periódicamente una muestra de respuestas.
   - Botón para reportar errores.
   - Procedimiento para suspender el servicio (OMS).
   - Excluir usos clínicos directos (dosis, triaje, diagnóstico) o derivarlos explícitamente al protocolo y al profesional.
6. **Evaluación antes y durante la operación:**
   - Antes de salir a producción, un conjunto de preguntas de referencia por servicio, con medición de exactitud, fidelidad a la fuente (groundedness), tasa de "no sé" y tasa de citas correctas.
   - Pruebas de inyección de prompts mediante documentos.
   - Volver a evaluar en cada cambio de modelo o de índice.
7. **Documentación de cumplimiento:**
   - EIPD (Ley 21.719, art. 15 ter, voluntaria u obligatoria).
   - Ficha de transparencia algorítmica (CPLT y GobLab).
   - Contrato con el proveedor conforme a la Directiva ChileCompra 44/2026 y las cláusulas modelo de transferencia internacional.
   - Registro en el inventario de activos según el DS 7/2023.
   - Capacitación del personal (Oficio 711).
8. **Preferir el alojamiento local o en Chile** si se prevé resumir documentos con datos de pacientes. Eso evita la transferencia internacional y facilita cumplir el art. 16 bis.

### Gaps
- No se encontraron guías chilenas oficiales con estándares técnicos para LLM (detección de PII, retención de prompts, métricas de alucinación). Las propuestas 1 a 8 son inferencias basadas en principios.
- No se verificaron plazos de retención exigidos por normas chilenas de archivo o de registros de auditoría (por ejemplo, el DS 7/2023 o las normas del Archivo Nacional) aplicables a logs de sistemas.
