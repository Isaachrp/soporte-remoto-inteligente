"""Runs only the PHP script embedded in a technician-approved executable."""
import argparse
import getpass
import json
import os
from pathlib import Path
import sys
import time

from agent.app.router import NativeRouter
from server.app.catalog_contract import validate
from server.app.offline_contract import canonical_snapshot
from shared.contracts import digest


class Router:
    snapshot = NativeRouter.snapshot
    close = NativeRouter.close

    def __init__(self, host, user, password):
        from librouteros import connect
        self.api = connect(host=host, username=user, password=password, port=8728, timeout=120)


def failure_detail(exc):
    """Classify errors without retaining router source, credentials or raw messages."""
    from librouteros.exceptions import TrapError, MultiTrapError, ConnectionClosed
    if isinstance(exc, (TrapError, MultiTrapError)):
        message = str(exc).lower()
        if 'permission' in message or 'not allowed' in message:
            return 'permissions', 'RouterOS rechazó la operación por permisos insuficientes.'
        if 'syntax' in message or 'expected end' in message or 'bad command' in message:
            return 'script_syntax', 'RouterOS rechazó la sintaxis del script original de PHP.'
        if 'already' in message or 'duplicate' in message:
            return 'existing_configuration', 'RouterOS encontró un elemento que ya existe.'
        return 'router_error', 'RouterOS rechazó la operación. Revisa el registro del router.'
    if isinstance(exc, (TimeoutError, ConnectionError, ConnectionClosed, OSError)):
        return 'connection', 'Se perdió la conexión o se agotó el tiempo de espera.'
    return 'execution_error', 'No se pudo completar la operación.'


def execute(package, router, directory, confirm):
    validate(package)
    if package['mode'] != 'real':
        return {'status': 'not_executed', 'message': 'Paquete de prueba: no ejecuta cambios.'}
    def check():
        validate(package)
        if digest(canonical_snapshot(router.snapshot())) != package['snapshot_hash']:
            raise ValueError('El router cambió desde el diagnóstico. Genera una entrega nueva.')
    check()
    if not confirm(package):
        return {'status': 'cancelled', 'message': 'Cancelado.'}
    check()
    directory = Path(directory)
    journal = directory / ('resultado-' + package['id'] + '.json')
    record = {'package_id': package['id'], 'status': 'intervention_required', 'started_at': time.time(),
              'message': 'Ejecución iniciada. No repetir sin revisar.', 'functionality_verified': False}
    with journal.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False)
        stream.flush()
        os.fsync(stream.fileno())
    script_name = 'central-' + package['id']
    stage = 'check_previous_delivery'
    run_requested = False
    run_completed = False
    try:
        # A marker on the router blocks replay even when the executable is copied.
        rows = list(router.api('/system/script/print', **{'.proplist': '.id,name,comment'}))
        if any(row.get('name') == script_name for row in rows):
            record['error_code'] = 'previous_delivery'
            raise ValueError('Entrega ya iniciada en este router.')
        stage = 'create_script'
        list(router.api('/system/script/add', name=script_name, source=package['artifact']['script'],
                        policy='read,write,test,policy,password,sensitive,ftp',
                        **{'dont-require-permissions': 'no', 'comment': 'central:started'}))
        stage = 'locate_script'
        rows = list(router.api('/system/script/print', **{'.proplist': '.id,name'}))
        matches = [r for r in rows if r.get('name') == script_name]
        if len(matches) != 1 or not matches[0].get('.id'):
            raise ValueError('No se pudo identificar la entrega.')
        script_id = matches[0]['.id']
        stage = 'run_script'
        run_requested = True
        list(router.api('/system/script/run', **{'.id': script_id}))
        run_completed = True
        stage = 'clear_script_source'
        # Preserve the replay marker, remove source (may contain generated credentials).
        list(router.api('/system/script/set', **{'.id': script_id, 'source': '', 'comment': 'central:completed'}))
        record.update(status='script_executed', message='Script ejecutado. El técnico debe comprobar el servicio y la conectividad.')
    except Exception as exc:
        code, detail = failure_detail(exc)
        if record.get('error_code') == 'previous_delivery':
            code, detail = 'previous_delivery', 'Esta entrega ya tiene un registro en el router. No se volvió a ejecutar.'
        record.update(error_code=code, failed_stage=stage)
        if run_completed:
            detail += ' El script terminó, pero falló la limpieza de su código.'
        elif run_requested:
            detail += ' La ejecución puede ser parcial; revisa el router antes de repetir.'
        else:
            detail += ' En este intento no se envió la orden de ejecutar el script.'
        record['message'] = detail
    record.update(script_run_requested=run_requested, script_run_completed=run_completed)
    record['finished_at'] = time.time()
    temporary = journal.with_suffix('.tmp')
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    for attempt in range(6):
        try:
            os.replace(temporary, journal)
            break
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.1 * (attempt + 1))
    return record


def main():
    parser = argparse.ArgumentParser(description='Configuración MikroTik · Sistema central')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    package = validate(json.loads((root / 'delivery.json').read_text(encoding='utf-8')))
    print(package['procedure'], '| Router:', package['snapshot']['identity'], '| Modo:', package['mode'])
    if args.validate_only:
        print('Paquete integrado válido. Sin conexión al router.')
        return 0
    if package['mode'] != 'real':
        print('Paquete de prueba: no ejecuta cambios.')
        return 0
    print('API RouterOS 8728 · conexión por LAN o VPN.')
    host = input('IP del router: ').strip()
    user = input('Usuario: ').strip()
    password = getpass.getpass('Contraseña: ')
    router = Router(host, user, password)
    password = None
    directory = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path.cwd()
    try:
        def confirm(value):
            print(value['artifact']['script'])
            print('Se ejecutará el script original de PHP; puede modificar o reemplazar configuración existente.')
            return input('Escribe APLICAR ' + value['snapshot']['identity'] + ': ').strip() == 'APLICAR ' + value['snapshot']['identity']
        result = execute(package, router, directory, confirm)
        print(result['message'])
        return 0 if result['status'] in ('cancelled', 'script_executed') else 1
    finally:
        router.close()


if __name__ == '__main__':
    code = 1
    try:
        code = main()
    except Exception:
        print('No se completó la entrega. Revisa vigencia, diagnóstico, conexión y registro de resultados.')
    if '--validate-only' not in sys.argv and '--help' not in sys.argv:
        try:
            input('Enter para cerrar…')
        except EOFError:
            pass
    raise SystemExit(code)
