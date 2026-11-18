@echo off
cd /d "%~dp0.."
".venv-mvp\Scripts\python.exe" "server\run_central.py" %*
pause
