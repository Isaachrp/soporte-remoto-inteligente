@echo off
cd /d "%~dp0.."
"agent\.venv-portable\Scripts\python.exe" -m agent.app.gui
