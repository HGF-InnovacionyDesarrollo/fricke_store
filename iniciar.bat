@echo off
rem Uso: iniciar.bat [establecimiento] [puerto]    p. ej.: iniciar.bat marga_marga 8091
cd /d "%~dp0"
if not "%~1"=="" set ECO_ESTABLECIMIENTO=%~1
if not "%~2"=="" set ECO_PUERTO_HTTP=%~2
python backend\servidor.py
