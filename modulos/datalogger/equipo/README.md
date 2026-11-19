# Monitor T/H Zigbee

ESP32-C6 como coordinador Zigbee que recibe temperatura y humedad de sensores
UZ-5T (u otros Zigbee 3.0 con clusters estándar 0x0402/0x0405) y las muestra en
una pantalla ST7789 de 1.9" (170x320).

## Componentes

### Unidad central

| Componente | Cant. | Detalle |
|---|---|---|
| ESP32-C6 DevKit | 1 | Coordinador Zigbee. Flash de 8 MB, USB-C nativo |
| Pantalla TFT IPS 1,9" | 1 | ST7789, 170×320 px, SPI, 3,3 V. Alternativa: 2,4" ST7789V 240×320 (se elige en el Configurador) |
| Módulo lector micro SD | 1 | SPI, **3,3 V** (6 pines, pin de alimentación rotulado "3V3", sin regulador) |
| Tarjeta micro SD | 1 | 32 GB o menos, formateada en FAT32 |
| Módulo reloj RTC DS3231 | 1 | I2C (tipo ZS-042) |
| Pila CR2032 | 1 | Para el DS3231 |
| Pulsador táctil TS0719 | 1 | 12×12 mm, 4 patas; usar dos patas en diagonal |
| Buzzer activo TMB12A05 | 1 | Alarma sonora en el GPIO 22, conectado directo (sin transistor) |
| Cable USB-C de datos | 1 | Programación y configuración con el Configurador |
| Cables dupont y termorretráctil | — | En el montaje definitivo, soldar en vez de usar protoboard |

### Respaldo de energía (pendiente: faltan las celdas)

| Componente | Cant. | Detalle |
|---|---|---|
| Módulo UPS Tipo-C 15 W (variante 5 V) | 1 | Salida OUT+/OUT− a los pines 5V/GND del ESP32 |
| Celdas 18650 | Las del módulo | |
| Cargador USB-C 5 V | 1 | A la entrada del módulo UPS |
| Resistencia 20 kΩ | 1 | Divisor de detección de corte de luz (ver más abajo) |
| Resistencia 10 kΩ | 1 | Divisor de detección de corte de luz |

### Sensores

| Componente | Cant. | Detalle |
|---|---|---|
| Sensor Zigbee T/H UZ-5T | Hasta 20 por monitor | Tuya TS0201 (`_TZ3000_bgsigers`), Zigbee 3.0 |
| Pilas AAA alcalinas (LR03) | 2 por sensor | Según el manual del UZ-5T |

### Caja impresa

| Componente | Cant. | Detalle |
|---|---|---|
| Filamento PETG | — | Cuerpo, tapa y botón (detalles en [caja/LEEME.md](caja/LEEME.md)) |
| Tornillos M3×10 autorroscantes | 4 | Tapa |
| Tornillos M2×5-6 autorroscantes | 8 | Pantalla (4) y placa (4) |
| Tornillos de pared | 2 | Cabeza ≤ 8 mm |

## Configurador (firmware 2.0)

Desde el firmware 2.0 cada monitor se instala y configura sin Arduino con
`configurador/dist/Monitor TH Hospital Dr. Gustavo Fricke.exe` (aplicativo "Monitor T/H Hospital Dr. Gustavo Fricke") (ver `configurador/LEEME.md`): firmware,
código del equipo (MTH-01, MTH-02...), pantalla (1,9" o 2,4"), qué alarmas suenan, y
nombre, área, corrección de calibración y "oculto" de cada sensor. La configuración
vive en la memoria de cada placa (no en `config.h`); cada cambio queda como evento.
Las placas que existían antes de la 2.0 recuperan su configuración solas al
instalarla (`config_inicial.h`, por número de serie).

## Conexiones

| ESP32-C6 | Pantalla | Micro SD | Reloj DS3231 | Pulsador | Buzzer | Módulo UPS | Divisor (corte de luz) | Color de cable |
|---|---|---|---|---|---|---|---|---|
| 5V | | | | | | OUT+ | | Rojo grueso |
| 3V3 | VCC | 3V3 | VCC | | | | | Rojo |
| GND | GND | GND | GND | Pata 2 | Pata − | OUT− | 10 kΩ (extremo inferior) | Negro |
| GPIO 6 | SCL | CLK | | | | | | Amarillo |
| GPIO 7 | SDA | MOSI | | | | | | Verde |
| GPIO 2 | | MISO | | | | | | Gris |
| GPIO 5 | | CS | | | | | | Rosado |
| GPIO 18 | CS | | | | | | | Naranjo |
| GPIO 19 | DC | | | | | | | Azul |
| GPIO 20 | RES | | | | | | | Blanco |
| GPIO 21 | BLK / BL | | | | | | | Morado |
| GPIO 10 | | | SDA | | | | | Celeste |
| GPIO 11 | | | SCL | | | | | Beige |
| GPIO 23 | | | | Pata 1 | | | | Café |
| GPIO 22 | | | | | Pata + | | | Verde claro |
| GPIO 3 | | | | | | | Unión de las dos resistencias | Naranjo claro |
| — | | | | | | IN+ (entrada 5 V) | 20 kΩ (extremo superior) | Rojo delgado |

- La pantalla y la SD comparten el bus SPI (GPIO 6 y 7); cada una tiene su propio CS.
- Pantalla, SD y reloj van a **3V3**, nunca a 5 V. Al **5V** solo va la salida del módulo UPS.
- Pantalla de 2,4" (ST7789V 240x320): mismos pines; el modelo se elige en el
  Configurador, pestaña **Configuración** → "Modelo de pantalla" (desde el firmware
  2.0; `PANTALLA_MODELO` en `config.h` solo aplica a la 1.x). Antes de conectarla,
  confirmar el orden de sus pines, el pin RES y que la luz de fondo (60 mA) tenga
  transistor en el módulo.
- No usar los GPIO 8, 9 y 15 (strapping), 12 y 13 (USB nativo) ni 16 y 17 (consola).
- El WiFi no se usa: esta placa no recibe señal y la hora viene del DS3231.
- Los pines se cambian en `config.h`.

## Arduino IDE

1. Core **esp32 de Espressif 3.x** (probado con 3.3.11).
2. Librería **GFX Library for Arduino** (de *moononournation*), desde el Gestor de Librerías.
3. Herramientas:
   - Placa: **ESP32C6 Dev Module**
   - Zigbee mode: **Zigbee ZCZR (coordinator/router)**
   - Flash Size: **4MB**, también en las placas de 8 MB (desde el firmware 2.5 hay una sola versión).
   - Partition Scheme: **Custom**. La división de la memoria está en `partitions.csv`, junto al
     `.ino`, y Arduino la usa sola: una app de 2,5 MB y la red Zigbee en `0x3EA000`. "Custom" solo
     evita que Arduino rechace el programa por tamaño (el tope real es 2,5 MB).
   - **Ojo:** grabar desde Arduino en una placa que todavía tiene la división antigua de 8 MB
     (MTH-01, MTH-02) borra en la práctica su red Zigbee sin avisar. Para esas placas usar el
     Configurador, que pide confirmación y deja la memoria en orden (ver `configurador/LEEME.md`).
   - Core Debug Level: **Info** (para ver en el monitor serie cuando se une un dispositivo)
   - Si conectas por el puerto USB nativo de la placa: USB CDC On Boot: **Enabled**
4. Monitor serie a **115200**.

## Emparejar sensores

- La red está cerrada: se abre 180 s con una **doble pulsación** del pulsador externo
  (GPIO 23) (barra inferior naranja con cuenta regresiva).
- Pulsador externo: pulsación corta = brillo alto 1 min y siguiente página; doble
  (menos de 0,7 s entre ambas) = emparejar; mantener 3 s = retirar la SD.
  BOOT: solo brillo alto.
- En el sensor: mantener su botón ~5 s hasta que parpadee, o ponerle la pila si es
  nuevo (busca red solo al encenderse).
- Se empareja una sola vez: reinicios del monitor y cambios de pila no lo requieren.
- Por serie aparece `[NUEVO] Sensor N  IEEE ...` y luego `Fabricante / Modelo`.
- Borrar la red y los sensores guardados (no la clave de firma) solo se puede por USB:
  enviar `BORRAR_RED SI` por el monitor serie. Queda registrado como evento.
- Diagnóstico: el comando serie `ESTADO` muestra cada sensor con su perfil, valores,
  antigüedad del dato y alarmas; `VECINOS`, la tabla de red del coordinador.

## Después de un corte de luz o reinicio del monitor

Los UZ-5T se desconectan de la red si el monitor deja de responder, aunque sea unos
segundos, y pueden tardar **hasta ~4 h** en volver a unirse solos (el coordinador sí
los conserva en su tabla). **Procedimiento: tras cada corte o reinicio, dar una
pulsación corta (sin mantener) al botón de cada sensor**; vuelve al instante.
Si alguno se olvida, el monitor lo marca "sin datos" a los 75 min.
Eventos para seguirlo: `RED_AL_ARRANCAR` (sensores en la tabla de red al arrancar),
`SENSOR_PRIMER_REPORTE` (minutos desde el arranque hasta su primer dato) y
`SENSOR_NUEVA_DIRECCION`.

Para ponerles nombre, copia los últimos 4 caracteres de la IEEE en la tabla
`NOMBRES` de `config.h`.

## Identificación del equipo

Cada monitor tiene un código único, `MONITOR_CODIGO` en `config.h` (este: **MTH-01**;
al armar otro, cambiarlo antes de flashear: MTH-02, MTH-03...). Aparece en:

- la columna **Monitor** de cada fila de los CSV de datos y de eventos;
- el evento `ARRANQUE` junto con el número de serie y la versión del firmware
  (`VERSION_FIRMWARE` en `Monitor_TH.ino`): `MTH-01 serie 98A316FFFE9BB2EC firmware 1.0, motivo: encendido`;
- la pantalla del logo ("Equipo MTH-01 v1.0");
- el sticker de la caja (`docs/generar_sticker.py`, variable `CODIGO`).

El **número de serie** es la dirección EUI-64 grabada de fábrica en el ESP32-C6 (16
caracteres; también es su dirección Zigbee): única y no se puede cambiar, identifica la placa física (el código es solo la etiqueta). Se lee con
el comando `EQUIPO` por USB. Si una placa arranca con un código distinto al que tenía
(configuración de otro monitor, o cambio de placa), queda el evento `CODIGO_CAMBIADO`.

## Respaldo de energía (módulo UPS 18650)

Módulo UPS Tipo-C 15 W (variante 5 V) con celdas 18650: el cargador USB-C va a la
entrada del módulo y la salida OUT+/OUT− a los pines 5V y GND del ESP32. Antes de
conectarlo, medir que la salida dé 5 V con y sin el cargador. Con el módulo
conectado **no** enchufar el USB del monitor al PC: para flashear, desconectar OUT+.

Detección del corte de luz: divisor 20 kΩ / 10 kΩ desde la entrada de 5 V del módulo
al GPIO 3 (`ENERGIA_PIN`). La detección se activa sola la primera vez que el pin
muestra el voltaje del divisor (evento `RESPALDO_ENERGIA`; queda guardada). Desde
entonces:

- `CORTE_ENERGIA` / `ENERGIA_RESTABLECIDA` en los eventos (con la duración del corte).
- Aviso "! Sin luz: bateria N min" en la barra y brillo bajo (`BRILLO_BATERIA`).
- Desde el firmware 2.4, además, alerta "SIN LUZ" a pantalla completa (alterna con la
  lista, como la de la SD, y tiene prioridad sobre ella; las alarmas de sensores van
  primero) y el buzzer suena como una alarma. Se silencia con el pulsador por
  `SILENCIO_MIN` (30 min), igual que las otras alarmas, y deja de sonar sola al
  volver la luz. Sin el divisor instalado no hay detección, ni alerta ni sonido.
- El comando `EQUIPO` muestra el voltaje en el pin y el estado.
- Si se saca el divisor o el módulo UPS (por ejemplo, un equipo de escritorio conectado solo
  al PC), la detección sigue activa y el pin en 0 V se lee como corte de luz: el comando
  serie `ENERGIA OFF` (firmware 2.5) la apaga y borra la marca guardada (evento
  `RESPALDO_ENERGIA`). Se vuelve a activar sola cuando el pin muestra otra vez el divisor.
- Desde el firmware 2.5 la dirección del servidor se escribe sin la clave del equipo
  (`http://****@host/...`) por el puerto serie y en el evento `WIFI_ENCENDIDO`.

## Micro SD y hora

- Módulo SD SPI de 3,3 V: CLK→GPIO 6 y MOSI→GPIO 7 (compartidos con la pantalla),
  MISO→GPIO 2, CS→GPIO 5. Tarjeta de 32 GB o menos en FAT32.
- Reloj RTC DS3231: SDA→GPIO 10, SCL→GPIO 11, VCC→3V3. Es la única fuente de hora
  (no se usa WiFi). Para ponerlo en hora desde el PC, enviar por el monitor serie
  `HORA <segundos unix UTC>`. Sin hora válida no se graba en la SD.
- Si el DS3231 deja de responder (cable suelto) se registra `RTC_AUSENTE`, la barra
  inferior muestra "! Reloj no responde" y se sigue con el reloj interno; se busca
  cada minuto (reiniciando el bus I2C) y al volver se registra `RTC_RECUPERADO`. Si
  el monitor arrancó sin reloj, al conectarlo toma la hora y retoma el registro.
  Comando serie `RTC`: diagnóstico del reloj.
- El reloj interno del C6 se adelanta varios minutos por día: se corrige con el DS3231
  cada 10 min (evento `HORA_CORREGIDA` si la diferencia supera 1 min).
- El último valor de cada sensor se guarda en la flash cada 5 min: tras un reinicio se
  sigue registrando con él (con su hora de lectura original) hasta que el sensor vuelva
  a reportar, si no tiene más de `SIN_DATOS_MIN`.
- Cada escritura en la SD se verifica (se relee el tamaño del archivo); si no cuadra,
  las filas quedan en la flash y se reintenta.
- Cada 5 min se agrega una fila por sensor a `/datos/AAAA-MM-DD.csv`. Formato del Excel
  en español: columnas separadas por `;`, decimales con coma y marca UTF-8 (se abre con
  doble clic, cada dato en su columna). **No guardar el CSV desde Excel**: lo reescribe
  y las firmas dejan de coincidir; para trabajar, copiarlo o "Guardar como" .xlsx.
  La columna "Hora de la lectura" indica cuándo envió el sensor ese dato (los UZ-5T
  reportan solo cuando el valor cambia o cada 40-60 min, así que el dato de una fila
  puede ser anterior a su "Fecha y hora"). Las columnas "Corrección T" y "Corrección HR"
  son la calibración ya aplicada a ese valor (ver Calibración). Si el encabezado cambia con una nueva versión,
  ese día sigue en `AAAA-MM-DD_2.csv` para no mezclar formatos.
  Los archivos anteriores al 2026-09-25 13:47 están en la raíz (`datos-AAAA-MM-DD.csv`,
  separados por `,`); el verificador lee ambos formatos.
- En la cabecera: hora arriba a la izquierda, "SD" verde si está grabando, amarillo
  si falta la tarjeta (las filas se guardan en la flash interna y se pasan a la SD
  cuando vuelve), rojo si no se puede guardar en ninguna parte.
- Si la SD lleva más de 10 min sin grabar (`SD_ALERTA_MIN`: tarjeta colgada, con falla
  o retirada y no devuelta) aparece una alerta técnica: vista amarilla a pantalla
  completa ("FALLA SD" o "SD RETIRADA", qué hacer, filas pendientes y desde cuándo),
  un pitido corto cada 10 s (se silencia con una pulsación corta) y el evento
  `SD_FALLA_PROLONGADA`. Las alarmas de sensores tienen prioridad. Una tarjeta
  colgada vuelve a funcionar al sacarla y ponerla (se le corta la alimentación).
- Los eventos ocurridos sin hora válida (arranque sin reloj) esperan en memoria y se
  fechan hacia atrás cuando aparece la hora, con "(hora estimada)".
- Para sacar la tarjeta: mantener el pulsador externo 3 s hasta ver "Puede retirar
  la SD". Al volver a ponerla se detecta sola. Si no se saca en 5 min
  (`SD_REACTIVAR_MIN`), se vuelve a usar sola (evento `SD_INSERTADA`); también se
  reactiva manteniendo otra vez el pulsador 3 s. Mientras la SD no se usa, la barra
  inferior lo avisa en amarillo. Si se saca sin avisar, se detecta en
  unos segundos y no se pierden filas.
- Cabecera: el ícono de F+data siempre visible a la derecha (24 px, el mínimo de las
  directrices de Fricke Store, con 6 px libres alrededor; firmware 2.3). La hora, la
  fecha, la alarma y los avisos se acortan para no pasar bajo el ícono: en la alarma
  se acorta el nombre del sensor, nunca el valor. El ícono se genera desde
  `logo_f-data.png` con `python herramientas/generar_marca.py logo_marca.h`.
- Barra inferior: cuenta regresiva del emparejamiento; si no, avisos técnicos en
  amarillo ("! Reloj sin hora", "! Sensor N sin datos", "! Sensor N bateria baja");
  si no hay, cantidad de sensores y filas pendientes de pasar a la SD.

## Registro de eventos, firmas y watchdog

- `/eventos/AAAA-MM-DD.csv`: arranques (con motivo: encendido, watchdog, falla...),
  filas programadas que no se grabaron (`SIN_REGISTRO`, con cuántas y de qué hora a qué hora), alarmas y su fin, sensor sin datos
  (más de `SIN_DATOS_MIN` = 75 min; de noche los UZ-5T reportan solo cada 40-60 min) o recuperado, batería baja u OK, SD retirada,
  insertada o desmontada, ajustes de hora, emparejamientos, sensores nuevos.
- Cada fila de datos y de eventos termina en una firma HMAC-SHA256 encadenada con la
  anterior, con una clave secreta de la placa. Para revisar que nada se editó,
  borró o insertó:
  1. Enviar `CLAVE` por el monitor serie para obtener la clave (queda registrado).
  2. `python verificar_registro.py --clave <clave> <carpeta de la SD>`
  Quien tenga acceso al USB de la placa puede leer la clave.
- Watchdog: si el programa se cuelga más de 30 s (`WATCHDOG_S`), la placa se reinicia y el siguiente
  `ARRANQUE` lo indica. El detalle del error queda en la partición `coredump`.
- Batería en pantalla: verde desde 40 % (`BATERIA_ATENCION`), amarillo de 20 a 39 %,
  rojo bajo 20 % (`BATERIA_BAJA`, con aviso y evento). Gris si el % aún no se
  confirma desde el arranque; pila vacía sin % si el sensor no está reportando.

## Cuidado de la pantalla (uso 24/7)

- Brillo de la luz de fondo por PWM: 40 % normal, 15 % de 22:00 a 07:00, 100 % con
  alguna alarma o durante 1 min tras apretar el pulsador o BOOT (sin emparejar) (`BRILLO_*` en `config.h`).
- Cada hora la imagen se desplaza 1 px (9 posiciones) para evitar retención de imagen.
- Cada 5 min se muestra 5 s el logo del hospital (`LOGO_CADA_MIN`, `LOGO_SEGUNDOS`),
  salvo con alarma, aviso, emparejamiento o si alguien acaba de apretar un botón.
  El comando serie `LOGO` lo muestra de inmediato. La imagen (`logo_hgf.h`) se genera
  desde `LOGO HGF.png` con `python herramientas/generar_logo.py "LOGO HGF.png" logo_hgf.h`.

## Sensores ocultos (fuera de servicio)

Con `oculto = true` en la tabla `NOMBRES` de `config.h`, el monitor ignora ese sensor:
no lo muestra, no lo registra, no da alarmas ni avisos de "sin datos", y no lo borra
de la red Zigbee (con `false` vuelve a aparecer en su próximo reporte). Cada arranque
deja un evento `SENSOR_OCULTO` por cada uno. Desde el 2026-10-13 (prueba funcional en
Esterilización) solo el sensor FFFF está activo, como "Bodega Esteril"
con perfil MATERIAL ESTERIL; D314 y 00E4 están ocultos.

## Perfiles: rangos, colores y alarmas

Cada sensor usa un perfil definido en `config.h` según los protocolos del HGF. Se
asigna en la tabla `NOMBRES` junto con su nombre; los que no están en la tabla usan
`PERFIL_POR_DEFECTO` (medicamentos).

| | MEDICAMENTOS (APF 1.5) | MATERIAL ESTERIL (APE 1.4) |
|---|---|---|
| Verde (temperatura) | 16 a 24 °C | 19 a 23 °C |
| Amarillo (temperatura) | sobre 24 °C hasta 30 °C (tolerancia "hasta 30 °C por periodos breves") y de 15 °C a menos de 16 °C | sobre 23 °C hasta 24 °C y de 18 °C a menos de 19 °C |
| Alarma (temperatura) | sobre 30 °C o bajo 15 °C | sobre 24 °C o bajo 18 °C |
| Verde (humedad) | hasta 55 % | 33 a 47 % |
| Amarillo (humedad) | sobre 55 % hasta 60 % | sobre 47 % hasta 50 % y de 30 % a menos de 33 % |
| Alarma (humedad) | sobre 60 % | sobre 50 % o bajo 30 % |

- En pantalla, junto al nombre va una etiqueta de color con el tipo: **MED** (morado)
  o **EST** (verde azulado); la vista de alarma muestra el tipo bajo el nombre. En el
  CSV de datos, la columna **Almacenamiento** dice "Medicamentos" o "Material estéril".
- Al arrancar, la alarma se evalúa con los últimos valores recuperados, así que un
  cambio de perfil se aplica sin esperar el próximo reporte del sensor.
- La alarma se apaga al volver al rango con un margen de 0,5 °C o 2 %
  (`ALARMA_HISTERESIS`, `ALARMA_HUM_HISTERESIS`), para que no parpadee en el límite.
- El evento indica el perfil y el rango excedido, p. ej.
  `Medicamentos 1: 30.4 C (MEDICAMENTOS rango 15.0-30.0 C)`.

## Calibración (corrección por sensor)

El procedimiento está en `docs/Instructivo_calibracion_sensores_Monitor_TH.docx`
(procedimiento 7.4). La corrección de cada sensor se carga en la tabla `NOMBRES` de
`config.h` y se flashea:

```c
//  IEEE    nombre            perfil                corrT  corrHR  calibrado
{"FFFF", "Medicamentos 1", &PERFIL_MEDICAMENTOS, -0.4,  3,     "2026-10-20"},
```

- `corrT` (°C, un decimal) y `corrHR` (%, entero) se **suman** a lo que envía el
  sensor: corrección = promedio de (referencia − sensor).
- Pantalla, alarmas y CSV usan el valor corregido. El CSV de datos trae las columnas
  **Corrección T (°C)** y **Corrección HR (%)**: el valor que midió el sensor es el
  registrado menos la corrección. Las firmas cubren también esas columnas.
- Cada arranque registra un evento `CALIBRACION` por sensor de la tabla, con su
  corrección y fecha (o "sin calibracion registrada").
- Una corrección mayor a ±3 °C o ±15 % HR (`CORRECCION_MAX_*`) se toma como error
  de tipeo: no se aplica y queda el evento `CALIBRACION_INVALIDA`.
- `ESTADO` por USB muestra la corrección de cada sensor (`corr=+0.0/+0`).

## Alarmas

- Vista de alarma a pantalla completa (fondo rojo parpadeante): sensor, variable,
  valor en grande, límite y desde cuándo. Alterna 5 s con 3 s de la lista
  (`ALARMA_PANTALLA_S`, `ALARMA_LISTA_S`); si hay varias alarmas se muestran por turno
  ("1 de 2"). Tras apretar el pulsador o BOOT se muestra solo la lista durante 1 min.
- En la lista, los sensores en alarma van primero y el valor fuera de rango se
  destaca en blanco sobre rojo; la cabecera muestra "ALARMA" con el sensor y el valor.
- Buzzer activo (TMB12A05) conectado directo: pata + al GPIO 22 y pata − a GND (nunca
  la pata + a 5V con la − al GPIO: el C6 no tolera 5 V). A 3,3 V suena algo más bajo
  que a 5 V; como pita en forma intermitente, el pin lo soporta. Pitido de 200 ms cada
  2 s mientras haya alarma.
- Las alarmas de humedad no suenan (`BUZZER_HUMEDAD false` en `config.h`, decisión
  del 2026-10-06) y, durante la prueba en Esterilización, tampoco las de temperatura
  (`BUZZER_TEMPERATURA false`, 2026-10-13): se ven en pantalla y quedan en los
  eventos, pero sin buzzer. La alerta técnica de la SD sigue sonando.
- Silenciar: con el buzzer sonando, una pulsación corta del pulsador lo calla
  `SILENCIO_MIN` (30 min); la alarma sigue en pantalla, la barra inferior muestra
  "Silenciado N min" y queda el evento `ALARMA_SILENCIADA`. Una alarma nueva vuelve a
  sonar aunque esté silenciado. Sin nada sonando, la pulsación corta cambia de página.
- Los sensores reportan cada cambio de ~0,5 °C o ~5 % (como máximo uno cada 5 min)
  y, sin cambios, al menos cada 30 min (`REPORTE_MAX_S`); la alarma puede tardar
  hasta 5 min en activarse.
- Una alarma sigue activa hasta que llega una lectura dentro del rango. Si el sensor
  deja de reportar más de `SIN_DATOS_MIN` (75 min; también tras un reinicio), la alarma
  se cierra en silencio con su evento de fin ("sin datos hace mas de 75 min, alarma
  cerrada") y el sensor queda como "! Sensor N sin datos" en la barra inferior, sin
  sonido. Si vuelve a reportar fuera de rango, la alarma se abre de nuevo (firmware 2.3;
  antes la alarma sonaba sin fin).
- Cada alarma queda en el registro de eventos (`ALARMA_TEMP`, `ALARMA_TEMP_FIN`,
  `ALARMA_HUM`, `ALARMA_HUM_FIN`).

## Si un sensor se une pero nunca muestra lecturas

Con Core Debug Level en Info verás `New device commissioned` pero no `[NUEVO]`.
Eso indica que el sensor usa el cluster propietario de Tuya (0xEF00) en vez de
los estándar, y hay que agregar su decodificación.
