"""Build a source distribution without Windows binaries, credentials or caches."""
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'dist/agente-diagnostico-linux.tar.gz'
    output.parent.mkdir(exist_ok=True)
    files = [ROOT / p for p in ('agent/__init__.py', 'agent/app/__init__.py',
        'agent/app/gui.py', 'agent/app/router.py', 'agent/requirements.txt',
        'agent/iniciar-diagnostico.sh', 'agent/preparar-linux.sh', 'agent/LINUX.md')]
    files += sorted((ROOT / 'shared').glob('*.py'))
    with tarfile.open(output, 'w:gz') as archive:
        for path in files:
            info = archive.gettarinfo(str(path), arcname='agente-linux/' + path.relative_to(ROOT).as_posix())
            info.mode = 0o755 if path.suffix == '.sh' else 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            with path.open('rb') as stream:
                archive.addfile(info, stream)
    print(output)


if __name__ == '__main__':
    main()
