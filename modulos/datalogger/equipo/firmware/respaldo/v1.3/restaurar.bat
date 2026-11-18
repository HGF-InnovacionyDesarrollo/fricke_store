@echo off
rem Restaura el firmware 1.3 del Monitor T/H (MTH-01) sin borrar la clave de firma,
rem los sensores emparejados ni la red Zigbee: escribe solo arranque, particiones y
rem programa, igual que un flasheo normal desde Arduino.
rem Uso:  restaurar.bat COM10     (desconectar antes la salida OUT+ del modulo UPS)
if "%1"=="" ( echo Uso: restaurar.bat COMx & exit /b 1 )
set ESPTOOL=%LOCALAPPDATA%\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe
cd /d "%~dp0"
"%ESPTOOL%" --chip esp32c6 --port %1 --baud 921600 --before default-reset --after hard-reset write-flash -z --flash-mode keep --flash-freq keep --flash-size keep 0x0 bootloader.bin 0x8000 partitions.bin 0xe000 boot_app0.bin 0x10000 Monitor_TH_v1.3.bin
