# Protocolo del Configurador (firmware 2.0; WiFi desde la 2.1)

Por el USB del monitor (115200 baudios; abrir el puerto con DTR y RTS en bajo para
no reiniciarlo). Cada comando es una línea que empieza con `@`. Las respuestas
también empiezan con `@`; el resto de lo que escribe el monitor (`[S1] Temp = ...`,
`[EVENTO] ...`) es diagnóstico y se ignora.

| Comando | Respuesta |
|---|---|
| `@INFO?` | `@INFO {"codigo","serie","firmware","pantalla","hora","hora_valida","unix","rtc","sd","pendientes","energia_mv","energia","sensores","wifi","emparejando"}` (`wifi` desde la 2.1: no_configurado, conectado, sin_conexion o apagado) |
| `@CFG?` | `@CFG_EQUIPO {"codigo","pantalla","buzzer_temp","buzzer_hum"}`, una línea `@CFG_SENSOR {"ieee4","nombre","perfil","corr_t","corr_h","calibrado","oculto"}` por sensor configurado, `@FIN` |
| `@SENSORES?` | Una línea `@SENSOR {"n","ieee","ieee4","nombre","perfil","configurado","t","h","bat","edad","alarma"}` por sensor emparejado, `@FIN` |
| `@EQUIPO_SET codigo\|pantalla\|buzzer_temp\|buzzer_hum` | `@OK`, o `@OK REINICIO` si cambió la pantalla (el monitor se reinicia) |
| `@SENSOR_SET ieee4\|nombre\|MED o EST\|corr_t\|corr_h\|calibrado\|oculto` | `@OK` (agrega o reemplaza) |
| `@SENSOR_DEL ieee4` | `@OK` |
| `@HORA segundos_unix_utc` | `@OK` |
| `@EMPAREJAR` | `@OK` (red abierta 180 s) |
| `@EVENTOS?` | Una línea `@EV fecha;codigo;tipo;detalle` por cada uno de los últimos 40 eventos desde el arranque, `@FIN` |
| `@CLAVE?` | `@CLAVE hex` (queda el evento CLAVE_LEIDA) |
| `@REINICIAR` | `@OK` y reinicio |
| `@WIFI?` (2.1) | `@WIFI {"configurado","red","servidor","activo","conectado","ip","rssi","envios_ok","envios_falla","memoria_libre"}` (nunca devuelve la clave) |
| `@WIFI_SET red\|clave\|servidor` (2.1) | `@OK`. Clave vacía = conservar la guardada (solo si la red no cambia). Servidor vacío = conectarse sin enviar |
| `@WIFI_BORRAR` (2.1) | `@OK` (borra red, clave y servidor; WiFi apagado) |

Errores: `@ERROR mensaje`. Cada cambio de configuración queda como evento
(`CONFIG_EQUIPO`, `CONFIG_SENSOR`, `CONFIG_SENSOR_BORRADO`, `CONFIG_WIFI`) en el registro firmado.

La configuración vive en la NVS de la placa (espacio `config`, clave `equipo`). La
primera vez que una placa arranca con la 2.0 parte de `config_inicial.h` (por número
de serie) o como `MTH-NUEVO`.

## Envío por WiFi (firmware 2.1)

Con red y servidor configurados, cada 60 s el monitor hace `POST` al servidor con
`Content-Type: application/json`:

```json
{"monitor":"MTH-03","serie":"E8F60AFFFEF7EE48","firmware":"2.1","seq":12,"unix":1795018340,
 "uptime_s":725,"rssi":-41,"heap":85224,"zb_reportes":13,"envios_ok":11,"envios_falla":0,
 "sensores":[{"n":1,"ieee":"A4C138...","nombre":"Sensor 1","temp":26.7,"hum":50,"edad_s":367,
              "bat":100,"alarma_t":0,"alarma_h":0}]}
```

`temp` ya incluye la corrección de calibración; `edad_s` = segundos desde el último
reporte del sensor; `bat` = -1 si no se conoce; `unix` = 0 si el monitor no tiene hora.
Cualquier respuesta 2xx cuenta como envío correcto. Si el WiFi o el servidor fallan no
se reintenta: el registro oficial sigue siendo el de la SD.

La red, la clave y el servidor viven en la NVS (espacio `wifi`). El WiFi no se enciende
si quedan menos de 70 KB de memoria libre, ni al arrancar si el reinicio anterior fue
por una falla (evento `WIFI_APAGADO`). Cada hora queda el evento `ZB_REPORTES_HORA`
(reportes Zigbee recibidos), para vigilar la convivencia de WiFi y Zigbee en la radio.
