"""Standalone, read-only laboratory check. Never creates a server session."""
import getpass
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path

from agent.app.router import NativeRouter


def inspect_router(router, identity, version, management):
    snapshot = router.snapshot()
    tables = snapshot['tables']
    interfaces = tables['/interface/ethernet']
    checks = [
        {'name': 'identity', 'passed': snapshot['identity'] == identity},
        {'name': 'version', 'passed': snapshot['version'] == version},
        {'name': 'management_interface', 'passed': any(
            row.get('name') == management for row in interfaces)},
        {'name': 'management_address', 'passed': any(
            row.get('interface') == management for row in tables['/ip/address'])},
    ]
    return {
        'schema': 'ecmp-lab-readonly/1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'real', 'read_only': True,
        'status': 'passed' if all(c['passed'] for c in checks) else 'failed',
        'identity': snapshot['identity'], 'routeros_version': snapshot['version'],
        'interfaces': [{'name': row.get('name'), 'default_name': row.get('default-name')}
                       for row in interfaces],
        'table_counts': {table: len(rows) for table, rows in tables.items()},
        'checks': checks, 'ecmp_certified': False, 'real_writes_enabled': False,
        'next_step': 'Revisar version y topologia antes de adaptar y validar ECMP real.',
    }


def run_diagnostic(args):
    # Validate everything before prompting for secrets or connecting.
    ca = Path(args.ca).resolve(strict=True)
    output = Path(args.report).resolve()
    if not ca.is_file() or not output.parent.is_dir():
        raise ValueError('CA o directorio de informe invalido')
    # Exclusive creation prevents overwriting previous evidence (or the CA).
    with output.open('x', encoding='utf-8') as report_file:
        router = None
        report = {'schema': 'ecmp-lab-readonly/1', 'mode': 'real', 'read_only': True,
                  'status': 'failed', 'ecmp_certified': False, 'real_writes_enabled': False}
        try:
            username = input('Usuario RouterOS de solo lectura: ').strip()
            password = getpass.getpass('Password RouterOS (solo memoria): ')
            try:
                router = NativeRouter(args.host, username, password, str(ca))
            finally:
                password = None
            report = inspect_router(router, args.identity, args.routeros_version, args.management)
        except ssl.SSLError:
            report['error'] = 'tls: revise CA, SAN, vigencia, reloj y certificado de api-ssl'
        except TimeoutError:
            report['error'] = 'timeout: revise cable, IP, firewall y TCP 8729'
        except Exception:
            # Library exception text can contain credentials or router data.
            report['error'] = 'connection_or_read: revise acceso, usuario, permisos y compatibilidad API'
        finally:
            if router is not None:
                try:
                    router.close()
                except Exception:
                    report['status'] = 'failed'
                    report['error'] = 'connection_close'
            json.dump(report, report_file, indent=2, ensure_ascii=False)
            report_file.write('\n')
    print('Diagnostico:', report['status'], '| Informe:', output)
    print('Esta prueba no aplica ni certifica ECMP.')
    return 0 if report['status'] == 'passed' else 1
