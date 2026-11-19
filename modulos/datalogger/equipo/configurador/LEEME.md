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
| Configuración | Código del equipo (MTH-01, MTH-02...), modelo de pantalla (1,9" o 2,4"), qué alarmas suenan y el WiFi opcional (red, clave y servidor al que se envían las lecturas cada minuto). |
| Sensores | Lista de sensores con sus valores. Doble clic para ponerles nombre, área (Medicamentos o Material estéril), corrección de calibración y fecha, u ocultarlos. |
| Firmware | Instalar el firmware incluido (una sola versión para todas las placas). Conserva la clave de firma, los sensores emparejados, la red y la configuración (en una placa con la división antigua de 8 MB, pide confirmar y hay que volver a emparejar los sensores, una sola vez). "Equipo nuevo: borrar toda la memoria" solo para placas nuevas. |
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

1. Compilar **una sola vez** (desde el firmware 2.5 hay una sola versión para placas de 4 y
   de 8 MB). La división de la memoria está en `../partitions.csv`, en la carpeta del sketch:
   Arduino la usa sola. arduino-cli exige que la carpeta se llame como el `.ino`, así que se
   compila una copia de `equipo/` llamada `Monitor_TH`:
   ```
   arduino-cli compile --fqbn esp32:esp32:esp32c6:FlashSize=4M,PartitionScheme=custom,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc ^
       --build-property upload.maximum_size=2621440 --build-path <carpeta de compilación> <copia Monitor_TH>
   ```
   El tope de 2,5 MB (`upload.maximum_size`) es el tamaño del programa en `partitions.csv`:
   sin él Arduino no avisa si el firmware crece de más.
2. `construir.bat <carpeta de compilación>`: copia los binarios a `firmware/` (revisa que el
   programa quepa) y arma `dist\Monitor TH Hospital Dr. Gustavo Fricke.exe` con PyInstaller.

Al instalar, el aplicativo revisa la división de la memoria que tiene la placa:

- Igual a la de `partitions.csv`, en blanco, o la antigua "Zigbee ZCZR 4MB" (mismas direcciones
  de datos): instala sin borrar nada.
- La antigua de 8 MB (MTH-01, MTH-02): antes de instalar pide confirmar el cambio, que se hace
  una sola vez por equipo. Se conservan la configuración, los sensores (nombres y
  correcciones), el WiFi y la clave de firma (NVS en `0x9000`, igual en las dos). Se borran la
  red Zigbee (hay que volver a emparejar los sensores) y el respaldo interno (confirmar antes
  que la pantalla no diga "pend. SD").

Requiere Python 3 con `pip install pyserial esptool pyinstaller`.

El protocolo entre el aplicativo y el monitor está en `protocolo.md`.
