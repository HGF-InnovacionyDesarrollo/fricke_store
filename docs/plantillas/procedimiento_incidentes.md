# Procedimiento de gestión y reporte de incidentes de ciberseguridad y vulneraciones de datos personales

**Hospital Dr. Gustavo Fricke** · Versión 0.1 (borrador) · Aprobado por Resolución Exenta N° [____] de [fecha]

> Plantilla preparada por Innova Fricke. Antes de aprobarla, deben revisarla el Delegado de Ciberseguridad, el Delegado de Protección de Datos, Asesoría Jurídica y el Encargado de Seguridad de la Información. Los corchetes indican datos por completar.

## 1. Objetivo y alcance

Asegurar que todo incidente de ciberseguridad o vulneración de datos personales que afecte a los sistemas del hospital, incluido el ecosistema Fricke Store y sus módulos, se detecte, contenga, reporte y resuelva dentro de los plazos legales.

**Marco normativo:**
- Ley 21.663, arts. 7, 8 y 9. El hospital figura como Operador de Importancia Vital, según la Res. Ex. ANCI 87/2025 [verificar en el Diario Oficial].
- Instrucciones Generales de ANCI N° 2, 3 y 4.
- Ley 21.719, art. 14 sexies.
- DS 7/2023, art. 10.

## 2. Roles

| Rol | Responsable | Función |
|---|---|---|
| Director | [nombre] | Jefe superior del servicio; responde ante ANCI y la Agencia |
| Delegado de Ciberseguridad | [nombre] | Coordina el incidente y envía los reportes a ANCI |
| Delegado de Protección de Datos | [nombre] | Evalúa la vulneración de datos y notifica a la Agencia y a los titulares |
| Encargado de Seguridad de la Información | [nombre] | Dirige el análisis técnico y la contención |
| Jefatura TI / Innova Fricke | [nombre] | Ejecuta la contención y la recuperación |
| Comunicaciones | [nombre] | Prepara los mensajes internos y externos |

Turno de contacto 24/7: [teléfono o celular de guardia].

## 3. Plazos legales (desde que se toma conocimiento)

| Paso | Plazo | Destino | Norma |
|---|---|---|---|
| Alerta temprana | **3 horas** | CSIRT Nacional, portal.anci.gob.cl | Ley 21.663 art. 9 a) |
| Actualización (gravedad, impacto, indicadores de compromiso) | **72 horas**; **24 horas** si se afecta un servicio esencial | ANCI | art. 9 b) |
| Plan de acción (OIV) | **7 días corridos** | ANCI | art. 9 |
| Informe final | **15 días corridos** | ANCI | art. 9 c) |
| Aviso de vulneración de datos | **Sin dilaciones indebidas** (meta interna: 72 horas) | Agencia de Protección de Datos | Ley 21.719 art. 14 sexies |
| Aviso a las personas afectadas | Sin dilaciones indebidas, si hay datos sensibles | Titulares | art. 14 sexies |

Fricke Store calcula estos plazos al registrar el incidente en **Administración › Incidentes**, los muestra con cuenta regresiva y alerta cuando alguno vence.

## 4. Etapas

1. **Detección y registro**
   - Toda persona que detecte algo anómalo avisa a la Mesa de ayuda ([anexo]) o al turno de guardia.
   - El delegado registra el incidente en Fricke Store con la hora real de detección.
2. **Evaluación inicial (primera hora)**
   - Determinar qué se afecta: la atención (servicio esencial), datos personales o datos sensibles.
   - Asignar la severidad.
3. **Contención**
   - Aplicar las medidas de la IG N° 4:
     - aislar los equipos afectados;
     - cambiar las credenciales de administradores;
     - cerrar el acceso remoto expuesto;
     - bloquear por defecto en el firewall.
   - En Fricke Store, usar **Seguridad y respaldos › Contención**: cerrar sesiones, forzar el cambio de claves privilegiadas, suspender módulos y pausar los formularios.
4. **Reporte**
   - Enviar la alerta temprana a ANCI y marcarla en Fricke Store con el número de ticket.
   - Cumplir los plazos de la tabla anterior.
5. **Erradicación y recuperación**
   - Restaurar desde un respaldo verificado (`python backend/respaldo.py probar` antes de restaurar).
6. **Cierre y lecciones aprendidas**
   - Preparar el informe final y el plan de acción.
   - Actualizar este procedimiento si corresponde.
   - Cerrar el incidente en Fricke Store con su justificación.

## 5. Registro y evidencia

- La bitácora encadenada de Fricke Store y el registro de incidentes son el **registro de vulneraciones** del art. 14 sexies.
- Conservar los comprobantes de envío a ANCI y a la Agencia por al menos 5 años.

## 6. Simulacros

- Al menos **un simulacro al año** (Ley 21.663 art. 8 para OIV).
- Registrarlo en Fricke Store como incidente de severidad "baja" con título "SIMULACRO".
