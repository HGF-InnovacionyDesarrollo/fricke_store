@echo off
rem Arma "Monitor TH Hospital Dr. Gustavo Fricke.exe" con el firmware compilado incluido.
rem
rem Uso:  construir.bat <carpeta de compilacion>
rem   Es la carpeta que se paso a arduino-cli con --build-path. Una sola compilacion para
rem   todas las placas (4 y 8 MB), con ../partitions.csv (ver LEEME.md):
rem   FQBN esp32:esp32:esp32c6:FlashSize=4M,PartitionScheme=custom,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc
rem   y --build-property upload.maximum_size=2621440.
rem   Debe tener Monitor_TH.ino.bin, Monitor_TH.ino.bootloader.bin,
rem   Monitor_TH.ino.partitions.bin y boot_app0.bin.
rem
rem Requiere Python con pyserial, esptool y pyinstaller:
rem   pip install pyserial esptool pyinstaller

setlocal
cd /d "%~dp0"
if "%~1"=="" ( echo Uso: construir.bat ^<carpeta de compilacion^> & exit /b 1 )

python preparar_firmware.py "%~1" || exit /b 1

python -m PyInstaller --noconfirm --onefile --windowed --name "Monitor TH Hospital Dr. Gustavo Fricke" ^
  --version-file version_info.txt ^
  --icon icono.ico ^
  --add-data "firmware;firmware" --add-data "icono.ico;." --add-data "logo_app.png;." --add-data "logo_app_2x.png;." ^
  --collect-data esptool --hidden-import esptool ^
  configurador.py || exit /b 1

echo.
echo Listo: %~dp0dist\Monitor TH Hospital Dr. Gustavo Fricke.exe
