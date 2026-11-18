"""Fixed execution harness embedded by the central server; no server connection."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sys
import time

from agent.app.router import NativeRouter, SimulatedRouter
from shared.ecmp import precheck, verify, validate_artifact
from server.app.offline_contract import canonical_snapshot, validate_package
from server.app.existing_ecmp import check_existing, verification_operations


class ClientRouter(NativeRouter):
    """Plain RouterOS API for the approved lab delivery; no CA prompt."""
    def __init__(self, host, username, password):
        if host != '10.255.255.1':
            raise ValueError('Esta entrega ECMP está limitada al router de laboratorio 10.255.255.1.')
        from librouteros import connect
        self.lab_enabled = True
        self.api = connect(host=host, username=username, password=password, port=8728, timeout=5)


def snapshot_hash(snapshot, package):
    if package.get('execution_policy') == 'preserve_existing':
        return check_existing(snapshot, package['target'], package['parameters'], package['mode'], package['mode'] == 'real')
    return precheck(snapshot, package['target'], package['parameters'], package['mode'] == 'real')


def execute(package, router, directory, confirm):
    validate_package(package)
    if router.mode != package['mode']:
        raise ValueError('Modo del router distinto al del paquete.')
    current = canonical_snapshot(router.snapshot())
    if snapshot_hash(current, package) != package['snapshot_hash']:
        raise ValueError('La configuración cambió desde el diagnóstico. No se ejecutó nada.')
    if not confirm(package):
        return {'status': 'cancelled', 'completed': 0}
    # Read again after the operator's confirmation, which can take arbitrary time.
    validate_package(package)
    current = canonical_snapshot(router.snapshot())
    if snapshot_hash(current, package) != package['snapshot_hash']:
        raise ValueError('El router cambió durante la confirmación.')
    directory = Path(directory)
    result_path = directory / ('resultado-' + package['id'] + '.json')
    record = {'schema': 'ecmp-offline-result/1', 'package_id': package['id'],
              'package_hash': package['package_hash'], 'mode': package['mode'],
              'started_at': time.time(), 'status': 'intervention_required',
              'completed': None, 'message': 'Ejecución iniciada; no repetir sin revisar.',
              'wan_lan_tested': False}
    # Exclusive, durable journal BEFORE writing: interruption never silently retries.
    with result_path.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        continuing = package.get('execution_policy') == 'preserve_existing'
        operations = package['executable']['operations']
        if continuing:
            # Package validation binds this exact subset to the trusted PHP artifact.
            # Keep the legacy agent's full-template apply contract unchanged.
            record['completed'] = 0
            started = time.monotonic()
            for op in operations:
                if time.monotonic() - started > 110:
                    raise TimeoutError('Tiempo de ejecución agotado')
                list(router.api(op['command'], **op['args']))
                record['completed'] += 1
            record['preserved'] = len(validate_artifact(package['artifact'], package['parameters'])['operations']) - len(operations)
        else:
            record['completed'] = router.apply(operations)
        if record['completed'] != len(package['executable']['operations']):
            raise ValueError('Aplicación parcial')
        after = canonical_snapshot(router.snapshot())
        if after['identity'] != current['identity'] or after['version'] != current['version']:
            raise ValueError('Identidad o versión alterada')
        full = validate_artifact(package['artifact'], package['parameters'])
        record['verification'] = verify(after, verification_operations(full) if continuing else operations)
        record['status'] = record['verification']['outcome']
        record['message'] = 'Configuración comprobada. Consulte las comprobaciones; tráfico WAN/LAN pendiente.'
    except Exception:
        record['message'] = 'Ejecución parcial o incierta. No repita: revise el router y conserve este resultado.'
    record['finished_at'] = time.time()
    temporary = result_path.with_suffix('.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    # Windows scanners can briefly hold a newly-created file. Only retry saving
    # evidence, never router.apply. The original journal remains on final failure.
    for attempt in range(6):
        try:
            os.replace(temporary, result_path)
            break
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.1 * (attempt + 1))
    return record


def main():
    parser = argparse.ArgumentParser(description='ECMP autorizado · ejecutor independiente del servidor')
    parser.add_argument('--validate-only', action='store_true', help='Validar el paquete integrado sin conectar al router')
    args = parser.parse_args()
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    package = validate_package(json.loads((root / 'delivery.json').read_text(encoding='utf-8')))
    print('Paquete:', package['id'], '| Router:', package['target']['identity'])
    print('Modo:', package['mode'], '| IA de preparación:', package['ai_mode'])
    print('Operaciones:', len(package['executable']['operations']), '| Sin conexión al servidor central.')
    if args.validate_only:
        print('Paquete integrado válido. No se conectó al MikroTik.')
        return 0
    router = None
    try:
        if package['mode'] == 'simulated':
            router = SimulatedRouter()
            router.data = package['snapshot']
            print('SIMULACIÓN: este ejecutable no modifica un router real.')
        else:
            print('Ensayo ECMP CHR 7.24.5 · API 8728 sin cifrado · usar LAN o VPN.')
            host = input('IP del router [10.255.255.1]: ').strip() or '10.255.255.1'
            username = input('Usuario RouterOS: ').strip()
            password = getpass.getpass('Contraseña RouterOS (solo memoria): ')
            try:
                router = ClientRouter(host, username, password)
            finally:
                password = None
        def confirm(value):
            if value.get('execution_policy') == 'preserve_existing':
                print('Se conserva lo coincidente. Solo se agregan estas operaciones:')
                print(json.dumps(value['executable']['operations'], ensure_ascii=False, indent=2))
                if not value['executable']['operations']:
                    print('Configuración completa: solo verificación, sin escrituras.')
            else:
                print(value['artifact']['script'])
            print('Se comprobará nuevamente el estado antes de escribir. No se reintenta una ejecución parcial.')
            return input('Escriba APLICAR ' + value['target']['identity'] + ' para continuar: ').strip() == 'APLICAR ' + value['target']['identity']
        directory = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
        result = execute(package, router, directory, confirm)
        print(result.get('message', 'Operación cancelada.'), '| Estado:', result['status'])
        print('Carpeta de resultados:', directory)
        return 0 if result['status'] in ('cancelled', 'configuration_with_warnings', 'configuration_successful') else 1
    finally:
        if router is not None:
            router.close()


if __name__ == '__main__':
    code = 1
    try:
        code = main()
    except Exception:
        print('No se pudo completar la operación. Revise vigencia, IP, credenciales, API 8728 y resultado previo. No repita escrituras a ciegas.', file=sys.stderr)
    if '--validate-only' not in sys.argv and '--help' not in sys.argv:
        try:
            input('Pulse Enter para cerrar…')
        except EOFError:
            pass
    raise SystemExit(code)
