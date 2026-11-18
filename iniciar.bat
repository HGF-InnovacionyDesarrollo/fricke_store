@echo off
rem Uso: iniciar.bat [establecimiento] [puerto]    p. ej.: iniciar.bat marga_marga 8091
cd /d "%~dp0"
if not "%~1"=="" set ECO_ESTABLECIMIENTO=%~1
if not "%~2"=="" set ECO_PUERTO_HTTP=%~2

rem Busca un Python real. El "python" de la Microsoft Store (alias de WindowsApps) no sirve: solo ofrece instalarlo.
set "PYTHON="
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not defined PYTHON if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PYTHON=%LOCALAPPDATA%\Python\bin\python.exe"
if not defined PYTHON (
  where py >nul 2>nul && set "PYTHON=py -3"
)
if not defined PYTHON (
  for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i "WindowsApps"') do if not defined PYTHON set "PYTHON=%%P"
)
if not defined PYTHON (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ y vuelve a abrir iniciar.bat.
  pause
  exit /b 1
)
%PYTHON% backend\servidor.py
