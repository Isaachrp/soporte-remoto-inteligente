"""Verify an extracted package against its trusted SHA256SUMS manifest."""
import hashlib
from pathlib import Path
import sys

folder = Path(sys.argv[1]).resolve()
manifest = folder/'SHA256SUMS'
expected_files = set()
for line in manifest.read_text(encoding='utf-8').splitlines():
    expected, relative = line.split('  ',1)
    path = (folder/relative).resolve()
    if not path.is_relative_to(folder) or not path.is_file():
        raise SystemExit('Ruta invalida en manifiesto')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit('Integridad incorrecta: '+relative)
    expected_files.add(relative)
actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p != manifest}
if actual != expected_files:
    raise SystemExit('Archivos adicionales o faltantes')
print('Paquete integro:',len(expected_files),'archivos. La autenticidad depende del canal de distribucion del manifiesto.')
