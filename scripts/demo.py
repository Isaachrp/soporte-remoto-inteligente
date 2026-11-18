"""Start an isolated local demo. Only simulated AI and RouterOS are permitted."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]


def free_port(port):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', port))
        return sock.getsockname()[1]


def wait_until(check, processes, seconds=45):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(p.poll() is not None for p in processes):
            raise RuntimeError('Un proceso termino; revise los logs de esta ejecucion.')
        try:
            value = check()
            if value:
                return value
        except httpx.TransportError:
            pass
        time.sleep(.2)
    raise RuntimeError('Tiempo de espera agotado; revise los logs de esta ejecucion.')


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def self_test(client, session, processes, output):
    """Explicit automatic approval in the isolated simulation, never a real router."""
    health = client.get('/health').raise_for_status().json()
    if health['mode'] != 'simulated' or health['ai_mode'] != 'simulated' or health['real_write_enabled']:
        raise RuntimeError('La autoprueba solo permite simulacion completa.')
    devices = client.get('/devices').raise_for_status().json()
    if not any(d['id'] == session for d in devices):
        raise RuntimeError('El agente no aparece en la selección de equipos.')
    inspection = client.post('/devices/' + session + '/inspect').raise_for_status().json()
    def inspected():
        record = client.get('/inspections/' + inspection['id']).raise_for_status().json()
        if record['status'] == 'failed':
            raise RuntimeError('Falló la lectura inicial.')
        return record if record['status'] == 'completed' else None
    inspection = wait_until(inspected, processes)
    if not inspection['recommendation']['available']:
        raise RuntimeError('No se obtuvo la recomendación esperada.')
    save_json(output / 'analisis.json', inspection)
    # Verify a rejected request cannot dispatch execution.
    rejected = client.post('/inspections/' + inspection['id'] + '/prepare').raise_for_status().json()

    def await_status(request_id, expected):
        def check():
            record = client.get('/requests/' + request_id).raise_for_status().json()
            if record['status'] == expected:
                return record
            if not record['status'].startswith('await_'):
                raise RuntimeError('Estado inesperado: ' + record['status'])
            return None
        return wait_until(check, processes)

    record = await_status(rejected['id'], 'await_approval')
    client.post('/requests/' + record['id'] + '/decision', json={
        'decision': 'reject', 'binding_hash': record['binding_hash']}).raise_for_status()
    rejected_report = client.get('/requests/' + record['id'] + '/report').raise_for_status().json()
    if rejected_report['request']['status'] != 'rejected' or any(
            e['event'] == 'approval_consumed' for e in rejected_report['audit']):
        raise RuntimeError('El caso de rechazo no paso.')
    save_json(output / 'rechazo.json', rejected_report)

    record = client.post('/inspections/' + inspection['id'] + '/prepare').raise_for_status().json()
    record = await_status(record['id'], 'await_approval')
    # A changed hash must be rejected and leave the pending approval intact.
    bad = client.post('/requests/' + record['id'] + '/decision', json={
        'decision': 'approve', 'binding_hash': '0' * 64})
    if bad.status_code != 409:
        raise RuntimeError('Se acepto una aprobacion alterada.')
    client.post('/requests/' + record['id'] + '/decision', json={
        'decision': 'approve', 'binding_hash': record['binding_hash']}).raise_for_status()
    record = await_status(record['id'], 'configuration_with_warnings')
    report = client.get('/requests/' + record['id'] + '/report').raise_for_status().json()
    checks = record['verification']['checks']
    if any(c['status'] == 'failed' for c in checks) or not any(c['status'] == 'passed' for c in checks):
        raise RuntimeError('La verificacion estructural no paso.')
    if sum(e['event'] == 'approval_consumed' for e in report['audit']) != 1:
        raise RuntimeError('La aprobacion no fue consumida exactamente una vez.')
    replay = client.post('/requests/' + record['id'] + '/decision', json={
        'decision': 'approve', 'binding_hash': record['binding_hash']})
    if replay.status_code != 409:
        raise RuntimeError('Se acepto una aprobacion repetida.')
    save_json(output / 'aprobacion.json', report)
    summary = {'schema': 'ecmp-demo-acceptance/1', 'created_at': datetime.now(timezone.utc).isoformat(),
               'status': 'passed', 'ai_mode': 'simulated', 'router_mode': 'simulated',
               'php_http_real': True, 'separate_processes': True, 'real_router_tested': False,
               'checks': {'device_selection_and_analysis': True, 'rejection_without_execution': True, 'altered_approval_blocked': True,
                          'approval_consumed_once': True, 'repeated_approval_blocked': True,
                          'configuration_verified': True},
               'verification_counts': {s: sum(c['status'] == s for c in checks)
                                       for s in ('passed', 'failed', 'not_performed')}}
    save_json(output / 'resultado.json', summary)
    files = ['analisis.json', 'rechazo.json', 'aprobacion.json', 'resultado.json']
    (output / 'SHA256SUMS').write_text(''.join(
        hashlib.sha256((output / name).read_bytes()).hexdigest() + '  ' + name + '\n'
        for name in files), encoding='utf-8')
    print('AUTOPRUEBA APROBADA. Evidencias:', output, flush=True)


def main():
    parser = argparse.ArgumentParser(description='Demo local ECMP: PHP y servidor reales; IA/router simulados.')
    parser.add_argument('--self-test', action='store_true', help='Ejecutar rechazo y aprobacion simulada; guardar evidencia y cerrar')
    parser.add_argument('--port', type=int, default=8000, help='Puerto web; 0 elige uno libre')
    parser.add_argument('--php', default=os.getenv('PHP_EXE') or shutil.which('php') or 'C:/xampp/php/php.exe')
    args = parser.parse_args()
    if not Path(args.php).is_file() and not shutil.which(args.php):
        parser.error('PHP no encontrado. Use --php C:\\xampp\\php\\php.exe')
    try:
        port = free_port(args.port)
    except OSError:
        parser.error('Puerto ocupado o invalido. Use --port 8001 o --port 0; no cierre procesos ajenos.')
    php_port = free_port(0)
    while php_port == port:
        php_port = free_port(0)
    output = ROOT / 'runtime' / ('demo-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(3))
    output.mkdir(parents=True)
    technician, bootstrap, generator = (secrets.token_urlsafe(32) for _ in range(3))
    # Do not inherit external router/AI settings or persist tokens in .env files.
    base = {k: v for k, v in os.environ.items() if not k.startswith(('ECMP_', 'OPENAI_'))}
    common = base | {'ECMP_MODE': 'simulated', 'ECMP_AI_MODE': 'simulated',
                     'ECMP_AGENT_ID': 'agent-1', 'ECMP_ROUTER_ID': 'router-1',
                     'ECMP_SERVER_URL': f'http://127.0.0.1:{port}'}
    server_env = common | {'ECMP_TECHNICIAN_TOKEN': technician, 'ECMP_AGENT_TOKEN': bootstrap,
                           'ECMP_GENERATOR_TOKEN': generator, 'ECMP_TECHNICIAN_ID': 'technician-1',
                           'ECMP_GENERATOR_URL': f'http://127.0.0.1:{php_port}/api/ecmp.php',
                           'ECMP_DATABASE': str(output / 'demo.sqlite3')}
    processes = []
    with ExitStack() as stack:
        def start(command, name, env, piped=False):
            log = stack.enter_context((output / (name + '.log')).open('w', encoding='utf-8'))
            p = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log,
                                 stdin=subprocess.PIPE if piped else subprocess.DEVNULL, text=True,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            processes.append(p)
            stack.callback(stop, p)
            return p
        try:
            start([args.php, '-S', f'127.0.0.1:{php_port}', '-t', str(ROOT / 'php/sistema-generador')],
                  'php', base | {'ECMP_GENERATOR_TOKEN': generator})
            start([sys.executable, '-m', 'uvicorn', 'server.app.main:create_app', '--factory',
                   '--host', '127.0.0.1', '--port', str(port)], 'server', server_env)
            client = stack.enter_context(httpx.Client(base_url=common['ECMP_SERVER_URL'], timeout=10,
                trust_env=False, headers={'Authorization': 'Bearer ' + technician}))
            wait_until(lambda: client.get('/health').status_code == 200, processes)
            with httpx.Client(timeout=2, trust_env=False) as php_client:
                wait_until(lambda: php_client.get(server_env['ECMP_GENERATOR_URL']).status_code == 401, processes)
            agent = start([sys.executable, '-m', 'agent.app.main', '--token-stdin'], 'agent', common, piped=True)
            agent.stdin.write(bootstrap + '\n')
            agent.stdin.close()
            def find_session():
                return next((line.split()[1] for line in (output / 'agent.log').read_text().splitlines()
                             if line.startswith('Sesion:')), None)
            session = wait_until(find_session, processes)
            save_json(output / 'conexion.json', {'url': common['ECMP_SERVER_URL'], 'session_id': session,
                'router_id': 'router-1', 'identity': 'lab-router', 'management_interface': 'ether14',
                'mode': 'simulated', 'ai_mode': 'simulated'})
            print('\nDEMO LOCAL: IA y RouterOS simulados. Sin conexiones a routers reales.', flush=True)
            print('URL:', common['ECMP_SERVER_URL'], '\nSesion del agente:', session, flush=True)
            if args.self_test:
                self_test(client, session, processes, output)
                return 0
            print('Clave temporal del tecnico:', technician, flush=True)
            print('Router: router-1 | Identidad: lab-router | Administracion: ether14', flush=True)
            print('Evidencias/logs:', output, '\nMantenga esta ventana abierta. Ctrl+C cierra los tres procesos.', flush=True)
            print('Para repetir desde un router limpio, cierre y vuelva a iniciar la demo.', flush=True)
            while True:
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError('Un proceso termino; reinicie la demo y revise los logs.')
                time.sleep(.5)
        except KeyboardInterrupt:
            print('\nCerrando demo.', flush=True)
            return 0
        except Exception as exc:
            # Never dump HTTP headers or environment values on failure.
            print('Demo fallida:', type(exc).__name__, '| Revise:', output, file=sys.stderr)
            return 1


if __name__ == '__main__':
    raise SystemExit(main())
