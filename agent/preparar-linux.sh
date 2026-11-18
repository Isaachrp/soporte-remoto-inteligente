#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if ! python3 -c 'import tkinter, venv' >/dev/null 2>&1; then
  printf '%s\n' 'Instala Python 3, Tk y venv con el gestor de tu distribución.' 'En Ubuntu/Debian: sudo apt install python3 python3-tk python3-venv'
  exit 1
fi
python3 -m venv agent/.venv-linux
agent/.venv-linux/bin/python -m pip install -r agent/requirements.txt
printf '%s\n' 'Preparación completa. Ejecuta: bash agent/iniciar-diagnostico.sh'
