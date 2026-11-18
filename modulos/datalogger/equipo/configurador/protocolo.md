# Protocolo del Configurador (firmware 2.0)

Por el USB del monitor (115200 baudios; abrir el puerto con DTR y RTS en bajo para
no reiniciarlo). Cada comando es una línea que empieza con `@`. Las respuestas
también empiezan con `@`; el resto de lo que escribe el monitor (`[S1] Temp = ...`,
`[EVENTO] ...`) es diagnóstico y se ignora.

| Comando | Respuesta |
|---|---|
| `@INFO?` | `@INFO {"codigo","serie","firmware","pantalla","hora","hora_valida","unix","rtc","sd","pendientes","energia_mv","energia","sensores","emparejando"}` |
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

Errores: `@ERROR mensaje`. Cada cambio de configuración queda como evento
(`CONFIG_EQUIPO`, `CONFIG_SENSOR`, `CONFIG_SENSOR_BORRADO`) en el registro firmado.

La configuración vive en la NVS de la placa (espacio `config`, clave `equipo`). La
primera vez que una placa arranca con la 2.0 parte de `config_inicial.h` (por número
de serie) o como `MTH-NUEVO`.
