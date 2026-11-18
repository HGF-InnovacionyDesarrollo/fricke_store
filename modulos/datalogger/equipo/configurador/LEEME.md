# Monitor T/H Hospital Dr. Gustavo Fricke

`Monitor TH Hospital Dr. Gustavo Fricke.exe` (el aplicativo) instala el firmware y configura los monitores de
temperatura y humedad por USB, sin Arduino ni compilación. Es un solo archivo: se
copia al PC y se abre (no requiere instalar nada).

## Uso

1. Conectar el monitor al PC con un cable USB-C **de datos**. Si el monitor está
   alimentado por el módulo UPS, **desconectar antes la salida OUT+** del módulo.
2. Abrir el aplicativo, elegir el puerto (los ESP32 aparecen primero como
   "ESP32 (Espressif)") y pulsar **Conectar**.

| Pestaña | Para qué |
|---|---|
| Equipo | Ver código, serie, versión, hora, SD y respaldo de energía. Poner la hora del PC, abrir la red para emparejar sensores, reiniciar. |
| Configuración | Código del equipo (MTH-01, MTH-02...), modelo de pantalla (1,9" o 2,4") y qué alarmas suenan. |
| Sensores | Lista de sensores con sus valores. Doble clic para ponerles nombre, área (Medicamentos o Material estéril), corrección de calibración y fecha, u ocultarlos. |
| Firmware | Instalar el firmware incluido (elige solo la versión para placas de 8 MB o de 4 MB). Conserva la clave de firma, los sensores emparejados, la red y la configuración. "Equipo nuevo: borrar toda la memoria" solo para placas nuevas. |
| Registro | Últimos eventos del monitor, guardar o cargar la configuración en un archivo (respaldo o para clonar a otro equipo), exportar la clave de firma. |

Todo cambio queda registrado como evento en el registro firmado del monitor.

### Armar un monitor nuevo

1. Firmware → marcar "Equipo nuevo: borrar toda la memoria" → Instalar.
2. Configuración → código (por ejemplo MTH-03), pantalla → Guardar.
3. Equipo → Poner la hora del PC.
4. Equipo → Abrir red para emparejar → mantener el botón de cada sensor ~5 s.
5. Sensores → doble clic en cada uno → nombre, área y corrección (del Anexo 1).
6. Registro → Guardar configuración en archivo (respaldo).

## Construir el .exe (desarrollo)

Cuando cambia el firmware (`Monitor_TH.ino`):

1. Compilar con Arduino **dos veces**, cada una en su carpeta (`--build-path` en
   arduino-cli), porque hay placas ESP32-C6 con flash de 8 MB y de 4 MB:
   - 8 MB: `esp32:esp32:esp32c6:FlashSize=8M,PartitionScheme=zigbee_zczr_8MB,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc`
   - 4 MB: `esp32:esp32:esp32c6:FlashSize=4M,PartitionScheme=zigbee_zczr,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc`
2. `construir.bat <compilación 8 MB> <compilación 4 MB>`: copia los binarios a
   `firmware/8MB/` y `firmware/4MB/` y arma
   `dist\Monitor TH Hospital Dr. Gustavo Fricke.exe` con PyInstaller.

Al instalar, el aplicativo lee el tamaño de la flash de la placa y usa la compilación
que corresponde (con 16 MB usa la de 8 MB; con menos de 4 MB no instala). En la de
4 MB el programa tiene poco margen (1,25 MB por partición): si el firmware crece y
no cabe, la compilación de 4 MB falla.

Requiere Python 3 con `pip install pyserial esptool pyinstaller`.

El protocolo entre el aplicativo y el monitor está en `protocolo.md`.
