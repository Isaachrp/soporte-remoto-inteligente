import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from server.app.generator_catalog import validate_parameters

ROOT = Path(__file__).resolve().parents[3]


def generate(procedure, values):
    values = validate_parameters(procedure, values)
    directory = ROOT / 'runtime/central/php-sessions'
    directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory) as session:
        result = subprocess.run([os.environ.get('PHP_EXE', 'C:/xampp/php/php.exe'), str(ROOT / 'server/php_bridge.php')],
            input=json.dumps({'procedure': procedure, 'parameters': values, 'session_directory': session}),
            capture_output=True, text=True, encoding='utf-8', timeout=30,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    try:
        artifact = json.loads(result.stdout) if result.returncode == 0 else None
    except ValueError:
        artifact = None
    if not artifact or not artifact.get('script', '').strip() or len(artifact['script']) > 500000:
        raise ValueError('PHP no produjo un script válido para estos parámetros.')
    artifact['script_hash'] = hashlib.sha256(artifact['script'].encode()).hexdigest()
    return artifact
