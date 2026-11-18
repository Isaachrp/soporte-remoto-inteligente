@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-mvp\Scripts\python.exe" (
    echo Falta el entorno. Consulte docs\18-primer-avance.md para instalarlo.
    exit /b 1
)
".venv-mvp\Scripts\python.exe" scripts\demo.py %*
exit /b %errorlevel%
