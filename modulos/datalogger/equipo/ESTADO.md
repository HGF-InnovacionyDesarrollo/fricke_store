# Estado del proyecto — checkpoint 2026-09-25

Monitor de temperatura y humedad con sensores Zigbee, pensado como registrador de
datos (data logger) para un entorno clínico. Detalles de uso y conexiones en el
[README](README.md).

## Hardware en uso

- ESP32-C6 DevKit (8 MB flash) como coordinador Zigbee — **su WiFi no recibe señal**
  (0 redes en escaneo), por eso el WiFi se eliminó del firmware.
- Pantalla ST7789 1,9" 170×320, micro SD SPI 3,3 V, reloj DS3231, pulsador (GPIO 23).
- 3 sensores UZ-5T (Tuya TS0201 `_TZ3000_bgsigers`), todos emparejados.
- Montaje actual en protoboard: **las conexiones se sueltan al mover la placa**
  (causó reinicios por baja tensión y desconexiones de la SD).

### Equipos

| Código | Serie (EUI-64) | Flash | Pantalla | Firmware | Notas |
|---|---|---|---|---|---|
| MTH-01 | 98A316FFFE9BB2EC | 8 MB | 1,9" | 1.3 | Actualizar a 2.0 con el Configurador |
| MTH-02 | 98A316FFFE9BB340 | 8 MB | 2,4" | 2.0 | Sensor 00E4: confirmar nombre y área |
| MTH-03 | E8F60AFFFEF7EE48 | **4 MB** | 2,4" | 2.0 | Armado 2026-11-10: venía con firmware de fábrica; se borró la memoria y se instaló la 2.0 de 4 MB. Código y hora puestos (el DS3231 venía sin hora); SD y reloj OK, pantalla 2,4" se ve bien. Micro SD de 3,3 V (pin "3V3"). **Falta emparejar sensores**, nombrarlos y guardar el respaldo de configuración |

Hay placas ESP32-C6 con flash de 4 MB: el Configurador lee la flash e instala la
compilación que corresponde (`configurador/firmware/8MB` o `4MB`). En 4 MB el
programa ocupa el 98 % de su partición (1,25 MB).

## Funciones implementadas

| Área | Estado |
|---|---|
| Lectura Zigbee de temperatura, humedad y batería | Funcionando |
| Pantalla: 5 sensores por página, colores por rango, batería | Funcionando |
| Perfiles MEDICAMENTOS (APF 1.5) y MATERIAL ESTERIL (APE 1.4): rangos, colores, alarmas alta/baja, etiqueta MED/EST y columna Almacenamiento | Probado (alarmas de temperatura y humedad del Sensor 2 con perfil estéril) |
| Comando serie `ESTADO`: valores, perfil y alarmas de cada sensor | Probado |
| Firmware 2.0: configuración por equipo en la NVS (código, pantalla, buzzer, sensores) + Configurador de Windows (configurador/, .exe con el firmware incluido) | Probado 2026-11-05 en MTH-02 (migración, lectura, escritura, errores, eventos). MTH-01 sigue en 1.3: actualizarlo con el Configurador |
| Firmware 1.4: detección de corte de luz (GPIO 3, divisor 20k/10k desde la entrada del módulo UPS; se activa sola), aviso "Sin luz: bateria", brillo bajo con batería; opción `PANTALLA_MODELO` (1,9" 170x320 o 2,4" 240x320) con logo de 240 | Compilado 2026-11-04 (ambas pantallas), sin flashear; 1.3 respaldada en firmware/respaldo/v1.3 y etiqueta v1.3 |
| Código de equipo MTH-01, número de serie (EUI-64 de fábrica: 98A316FFFE9BB2EC) y versión de firmware: columna Monitor en los CSV, evento ARRANQUE, CODIGO_CAMBIADO, comando EQUIPO, pantalla del logo, sticker | Flasheado 2026-10-06 |
| Corrección de calibración por sensor (`NOMBRES` en config.h), columnas de corrección en el CSV, eventos CALIBRACION / CALIBRACION_INVALIDA | Probado 2026-10-06 (eventos y columnas en la SD); correcciones en 0 hasta la primera calibración |
| Buzzer (TMB12A05, GPIO 22) y silencio 30 min con el pulsador | Probado; conectado directo al GPIO 22 (decisión: sin transistor) |
| Alerta técnica de SD a los 10 min (vista amarilla, pitido, SD_FALLA_PROLONGADA) | Probado 2026-10-05 |
| Reloj DS3231: RTC_AUSENTE / RTC_RECUPERADO sin reiniciar | Probado 2026-09-30 |
| Caja impresa 3D (diseño en caja/, ver caja/LEEME.md) | Prototipo armado |
| Vista de alarma a pantalla completa, alarmas primero en la lista, valor destacado | Probada (temperatura, Sensor 1) |
| Reloj DS3231 como única fuente de hora; corrección de deriva cada 10 min | Implementado, prueba nocturna pendiente |
| CSV de datos y de eventos por día (formato Excel en español, carpetas `/datos` y `/eventos`) | Probado |
| Firma HMAC-SHA256 encadenada + `verificar_registro.py` | Probado (detecta filas modificadas, borradas y clave errónea) |
| Respaldo en flash interna si falta la SD, con escritura verificada | Implementado; el respaldo sin verificación ya se probó |
| Retiro seguro de la SD con el pulsador y detección automática; se reactiva sola si no se saca en 5 min | Probado |
| Cabecera con hora y fecha larga ("lunes 28 de septiembre") | Probado |
| Avisos técnicos: sin hora, sensor sin datos (75 min), batería baja | Implementado |
| Último valor de cada sensor guardado en la flash: tras un reinicio se sigue registrando sin esperar su reporte | Probado |
| Watchdog (30 s) + coredump + `herramientas/leer_coredump.py` | Probado (detectó 2 fallas reales) |
| Brillo por PWM (40 % / 15 % noche / 100 % alarma) y desplazamiento de píxeles | Implementado, verificación visual pendiente |
| Logo del hospital cada 5 min (5 s), fondo gris, "Unidad de Innovación y Desarrollo" | Probado (se ve bien en la pantalla) |
| Botones: corta = brillo/página, doble = emparejar, larga = retirar SD | Probado |
| Borrar la red solo por USB (`BORRAR_RED SI`) | Probado (pide confirmación) |

## Problemas encontrados y resueltos

1. `Serial.print` bloqueaba `loop()` si nadie leía el USB → watchdog.
   Solución: `Serial.setTxTimeoutMs(0)`.
2. La librería SD se colgaba >5 s al remontar una tarjeta con mal contacto.
   Solución: watchdog de 30 s (y arreglar el hardware).
3. Filas firmadas que no quedaron en la SD (tarjeta con mal contacto aceptaba la
   escritura). Solución: releer el tamaño del archivo antes de borrar el respaldo.
4. El reloj interno del C6 se adelantó ~7 min en 14 h. Solución: resincronizar
   con el DS3231 cada 10 min.
5. Los UZ-5T no respetan el intervalo máximo de reporte (de noche reportan cada
   40-60 min). Solución: "sin datos" a los 75 min.
6. La librería Zigbee descartaba la batería (llega al endpoint 1) y truncaba los
   decimales del umbral de reporte. Solución: `ZigbeeMonitor` propio y reportes
   configurados directamente.

## Registro histórico conocido

La cadena de firmas del 2026-09-25 tiene **5 cortes esperados** (filas perdidas
~05:50 y ~06:45 por la SD con mal contacto, y el reinicio de las 08:51). Son parte
del historial; en verificaciones futuras solo importan los cortes **nuevos**.

## Prueba de fin de semana (2026-09-25 15:50 a 2026-09-28 09:05)

Con cargador de pared: sin reinicios, sin filas faltantes, sin cortes nuevos de
firmas, sin avisos falsos de "sin datos" y sin `HORA_CORREGIDA` (deriva < 1 min
cada 10 min). Alarma de humedad real del Sensor 3 (61 %) del 26/09 15:09 al 28/09
05:02. Los UZ-5T solo reportan cambios de ~0,5 °C / ~5 % aunque se les configure
menos.

## Pendientes

- **Reconexión tras reinicios (2026-09-29):** cada reinicio del monitor deja
  sensores sin reportar hasta ~4 h (se desconectan solos; el timeout que piden es
  15 360 s). Probado: al pulsar el botón del sensor se vuelve a unir al instante.
  Mitigación actual: procedimiento de pulsar los sensores tras un corte (README).
  Etapa 2: respaldo de energía y, al elegir sensores, verificar que se reconecten
  solos tras reiniciar el coordinador.
- **Hardware:** soldar las conexiones (placa perforada) y usar un gabinete cerrado
  que deje accesible solo el pulsador.
- Calibración de temperatura hecha (2026-10-06 a 08, referencia T&D RTR502B cert.
  LT/9097; docs/Anexo1_calibracion_MTH-01_2026-10.docx): correcciones +0,2 / 0,0 /
  +0,1 °C cargadas y flasheadas en firmware 1.1 (2026-10-08). Verificación posterior
  cumplida (09-10 y 13-10: diferencias +0,2 a +0,4 °C, todas los sensores leen algo
  bajo a 21-22 °C; revisar en la próxima calibración anual, antes del 08-09-2027).
  Pendiente: firmas del Anexo 1, calibración de humedad (falta referencia de HR) y
  aprobación del instructivo por Farmacia, Esterilización y Calidad.
- Opcional: aviso de calibración vencida (12 meses, APF 1.5) y modo calibración
  (reportes cada 5 min durante el ensayo; solo algunos sensores lo respetan).
- Etapa 2: probar Sonoff SNZB-02P / SNZB-02D (salas) y SNZB-02LD (sonda para
  refrigeradores) junto a un UZ-5T antes de comprar en cantidad.
- Poner a los sensores el nombre de su ubicación real (hoy: Medicamentos 1, Medicamentos 3, Medicamentos 2).
- Nombres para los sensores (identificarlos soplando uno a la vez).
- Etapa 2 (hardware): sensores calibrados con certificado, placa con WiFi
  funcional, respaldo de energía.
- Etapa 3: enviar lecturas y alarmas a la Central SIMI, reconocimiento de alarmas,
  informes.
- Proyecto posterior (evaluado 2026-10-06): avisos remotos (Telegram) por LoRaWAN.
  Cada monitor con un módulo RAK3172 (placa RAK3272S, variante **9XX MHz**) por UART
  con comandos AT, sin tocar el Zigbee; un gateway RAK7268V2 para todo el hospital,
  variante **Type4 = AU915** (Option1 sin 4G ~$143.500; Option7 con 4G EC25-AU
  ~$226.000; letra A = 12 V, revisar enchufe), ambos en la tienda oficial RAK de
  AliExpress; un PC o Raspberry Pi con Internet envía los Telegram. La alarma local
  (pantalla y buzzer) sigue siendo la principal. Alternativa sin LoRa: ESP32 con WiFi
  junto al monitor (requiere red y acceso a api.telegram.org).
- Etapa 4: validación (IQ/OQ/PQ) y procedimientos con el área de calidad.
- Seguridad: proteger los comandos USB (hoy cualquiera con acceso físico puede
  leer la clave o borrar la red).

## Cómo compilar y flashear

Arduino IDE o arduino-cli con el core esp32 3.3.11 y "GFX Library for Arduino" 1.6.7:

```
arduino-cli compile --fqbn "esp32:esp32:esp32c6:FlashSize=8M,PartitionScheme=zigbee_zczr_8MB,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc" Monitor_TH
arduino-cli upload -p COM10 --fqbn "<mismo fqbn>" Monitor_TH
```

No cambiar el esquema de particiones: la red Zigbee está guardada en `0x7EA000`.

Placas de 4 MB (MTH-03): `FlashSize=4M,PartitionScheme=zigbee_zczr` (resto del FQBN
igual; red Zigbee en `0x3EA000`). Desde el firmware 2.0 lo normal es instalar con el
Configurador, que elige la compilación solo.
