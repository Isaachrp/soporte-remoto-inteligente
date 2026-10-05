"""Run in an isolated Python 3.12 Windows build environment. No credentials.
Output includes runtime and deps. Publish SHA256SUMS via a trusted channel.
"""
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    if sys.platform != 'win32' or sys.version_info[:2] != (3,12):
        raise SystemExit('Build requires Windows and Python 3.12')
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir',
        '--name','ecmp-agent','--paths',str(ROOT),'--distpath',str(ROOT/'dist'),
        '--workpath',str(ROOT/'build/agent'),'--specpath',str(ROOT/'build'),
        str(ROOT/'agent/portable_entry.py')],cwd=ROOT,check=True)
    folder = ROOT/'dist/ecmp-agent'
    (folder/'VERSION').write_text('0.1.0\n',encoding='utf-8')
    lines = []
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name != 'SHA256SUMS':
            lines.append(hashlib.sha256(path.read_bytes()).hexdigest()+'  '+path.relative_to(folder).as_posix())
    (folder/'SHA256SUMS').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(folder)

if __name__ == '__main__':
    main()
