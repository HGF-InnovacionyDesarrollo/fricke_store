# Respaldo del firmware 1.3 (MTH-01)

Firmware que estaba funcionando antes de la versión 1.4 (respaldado el 2026-11-04).
Código fuente: etiqueta git `v1.3` (`git checkout v1.3`).

Configuración de esta versión: prueba funcional en Esterilización, sensor FFFF como
"Bodega Esteril" (perfil MATERIAL ESTERIL, corrección +0,2 °C), sensores D314 y 00E4
ocultos, buzzer sin alarmas de temperatura ni de humedad (solo alerta de SD),
pantalla 1,9" 170×320.

Para volver a esta versión: conectar el monitor por USB (con la salida OUT+ del módulo
UPS desconectada) y ejecutar `restaurar.bat COM10`. Escribe los mismos sectores que un
flasheo normal: **no borra** la clave de firma, los sensores emparejados ni la red.

| Archivo | Dirección |
|---|---|
| bootloader.bin | 0x0 |
| partitions.bin | 0x8000 |
| boot_app0.bin | 0xe000 |
| Monitor_TH_v1.3.bin | 0x10000 |

`SHA256SUMS.txt` permite verificar que los archivos no cambiaron.
