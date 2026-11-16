@echo off
cd /d "%~dp0"
echo Ecosistema en http://localhost:8090
python -m uvicorn app:app --app-dir backend --host 0.0.0.0 --port 8090
