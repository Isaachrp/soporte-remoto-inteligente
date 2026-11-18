@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-mvp\Scripts\python.exe" (
    echo Falta el entorno .venv-mvp. Consulte la instalacion del proyecto.
    exit /b 1
)
".venv-mvp\Scripts\python.exe" scripts\lab_v7.py %*
exit /b %errorlevel%
