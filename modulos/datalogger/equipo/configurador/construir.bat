@echo off
rem Arma "Monitor TH Hospital Dr. Gustavo Fricke.exe" con el firmware compilado incluido.
rem
rem Uso:  construir.bat <compilacion 8 MB> <compilacion 4 MB>
rem   Son las carpetas que se pasaron a arduino-cli con --build-path, una por placa:
rem   8 MB: FlashSize=8M,PartitionScheme=zigbee_zczr_8MB
rem   4 MB: FlashSize=4M,PartitionScheme=zigbee_zczr
rem   (el resto del FQBN igual: ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc).
rem   Cada una debe tener Monitor_TH.ino.bin, Monitor_TH.ino.bootloader.bin,
rem   Monitor_TH.ino.partitions.bin y boot_app0.bin.
rem
rem Requiere Python con pyserial, esptool y pyinstaller:
rem   pip install pyserial esptool pyinstaller

setlocal
cd /d "%~dp0"
if "%~2"=="" ( echo Uso: construir.bat ^<compilacion 8 MB^> ^<compilacion 4 MB^> & exit /b 1 )

python preparar_firmware.py "%~1" "%~2" || exit /b 1

python -m PyInstaller --noconfirm --onefile --windowed --name "Monitor TH Hospital Dr. Gustavo Fricke" ^
  --version-file version_info.txt ^
  --icon icono.ico ^
  --add-data "firmware;firmware" --add-data "icono.ico;." --add-data "logo_app.png;." --add-data "logo_app_2x.png;." ^
  --collect-data esptool --hidden-import esptool ^
  configurador.py || exit /b 1

echo.
echo Listo: %~dp0dist\Monitor TH Hospital Dr. Gustavo Fricke.exe
