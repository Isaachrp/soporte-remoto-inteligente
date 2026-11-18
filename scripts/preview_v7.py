"""Generate a PHP-owned lab draft locally; no router or server connection."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def generate_preview(php):
    parameters = {
        'tipo': 'ECMP', 'lineas': 2, 'lan': '172.16.0.1', 'dhcp': True,
        'vel1': '5M', 'gw1': '192.168.1.1', 'ip1': 2,
        'vel2': '5M', 'gw2': '192.168.2.1', 'ip2': 2,
    }
    # Fixed harness: PHP generates the script; Python only saves its output.
    program = ('require $argv[1]; $p=json_decode(stream_get_contents(STDIN),true,32,JSON_THROW_ON_ERROR); '
               'echo json_encode(ecmp_v7_lab_artifact($p),JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES);')
    result = subprocess.run(
        [php, '-r', program, str(ROOT / 'php/sistema-generador/lib/ecmp-v7-lab.php')],
        input=json.dumps(parameters), text=True, capture_output=True, check=True, timeout=15,
    )
    artifact = json.loads(result.stdout)
    script = artifact['script']
    if (artifact['schema'] != 'ecmp-v7-lab-preview/1' or artifact['preview_only'] is not True
            or artifact['certified'] is not False or artifact['agent_execution_supported'] is not False
            or hashlib.sha256(script.encode('utf-8')).hexdigest() != artifact['script_hash']):
        raise ValueError('Vista previa invalida')
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--php', default=os.getenv('PHP_EXE') or shutil.which('php') or 'C:/xampp/php/php.exe')
    parser.add_argument('--output', type=Path, help='Carpeta nueva; nunca sobrescribe una revision anterior')
    args = parser.parse_args()
    artifact = generate_preview(args.php)
    output = args.output or ROOT / 'lab-local' / ('preview-v7-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    output.mkdir(parents=True, exist_ok=False)
    script_path = output / 'ecmp-v7-lab.rsc'
    script_path.write_bytes(artifact['script'].encode('utf-8'))
    (output / 'artefacto.json').write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (output / 'SHA256SUMS').write_text(artifact['script_hash'] + '  ecmp-v7-lab.rsc\n', encoding='ascii')
    print('BORRADOR generado; no se conecto ni se aplico al router.')
    print('Script:', script_path.resolve())
    print('SHA256:', artifact['script_hash'])
    print('DHCP preparado deshabilitado. Revisar condiciones en artefacto.json.')


if __name__ == '__main__':
    main()
