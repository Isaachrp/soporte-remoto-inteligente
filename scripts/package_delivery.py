"""Build a source delivery using an allowlist; never package local credentials."""
from datetime import datetime
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = {ROOT / name for name in (
        'README.md', 'pytest.ini', 'iniciar-demo.cmd', 'iniciar-lab-v7.cmd', '.gitignore',
        'server/__init__.py', 'agent/__init__.py',
        'server/requirements.txt', 'server/requirements.lock',
        'agent/requirements.txt', 'agent/requirements.lock',
        'agent/build-requirements.txt', 'agent/build.lock',
        'agent/build_portable.py', 'agent/verify_package.py', 'agent/portable_entry.py',
        'server/.env.example', 'agent/.env.example',
        'tests/requirements.txt', 'tests/requirements.lock',
        'tests/fixtures/ecmp-before.php',
        'tests/fixtures/v7-precheck-main-fib-flag.json',
        'php/sistema-generador/api/ecmp.php',
        'php/sistema-generador/lib/ecmp-contract.php',
        'php/sistema-generador/lib/ecmp-legacy.php',
        'php/sistema-generador/lib/ecmp-v7-lab.php',
        'php/sistema-generador/logo_b.png', 'php/sistema-generador/modem.gif',
        'php/sistema-generador/mikrotik.jpg', 'php/sistema-generador/clientes.jpg',
        'server/app/ui.html')}
    for folder in ('server/app', 'agent/app', 'shared', 'tests', 'scripts'):
        paths.update((ROOT / folder).rglob('*.py'))
    for path in (ROOT / 'docs').rglob('*'):
        if path.is_file() and (path.suffix in ('.md', '.json', '.jpg', '.png') or path.name == 'SHA256SUMS'):
            paths.add(path)
    # Never descend into a virtual environment or include hidden local directories.
    paths = {p for p in paths if not any(part.startswith('.') or part == '__pycache__'
             for part in p.relative_to(ROOT).parts[:-1])}
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.is_file()]
    if missing:
        raise RuntimeError('Faltan archivos de entrega: ' + ', '.join(missing))
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    name = 'segundo-avance-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip'
    target = output / name
    manifest = []
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            archive.writestr(relative, data)
            manifest.append(hashlib.sha256(data).hexdigest() + '  ' + relative)
        archive.writestr('MANIFEST-SHA256.txt', '\n'.join(manifest) + '\n')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('El ZIP no paso la verificacion CRC.')
    print('Entrega:', target)
    print('Archivos:', len(paths), '| SHA256:', hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
