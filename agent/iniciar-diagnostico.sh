#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="$ROOT/agent/.venv-linux/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  printf '%s\n' 'Primero ejecuta: bash agent/preparar-linux.sh'
  exit 1
fi
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  printf '%s\n' 'Abre este programa desde una sesión de escritorio Linux.'
  exit 1
fi
exec "$PYTHON" -m agent.app.gui
