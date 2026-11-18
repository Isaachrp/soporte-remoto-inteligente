"""Start the explicit, supervised CHR v7 lab. Never approves a request."""
import argparse
from contextlib import ExitStack
from datetime import datetime
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

import httpx

from demo import free_port, stop, wait_until

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--ca', type=Path, default=ROOT / 'lab-local/router-ca.crt')
    parser.add_argument('--php', default=os.getenv('PHP_EXE') or shutil.which('php') or 'C:/xampp/php/php.exe')
    args = parser.parse_args()
    ca = args.ca.resolve(strict=True)
    if not ca.is_file():
        raise ValueError('Se requiere el certificado publico de la CA')
    port, php_port = free_port(args.port), free_port(0)
    technician, bootstrap, generator = (secrets.token_urlsafe(32) for _ in range(3))
    output = ROOT / 'runtime' / ('lab-v7-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(3))
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(ECMP_MODE='real', ECMP_AI_MODE='simulated', ECMP_V7_LAB_ENABLED='1',
               ECMP_DATABASE=str(output / 'lab.sqlite3'), ECMP_TECHNICIAN_TOKEN=technician,
               ECMP_AGENT_TOKEN=bootstrap, ECMP_GENERATOR_TOKEN=generator,
               ECMP_GENERATOR_URL=f'http://127.0.0.1:{php_port}/api/ecmp.php',
               ECMP_SERVER_URL=f'http://127.0.0.1:{port}', ECMP_TECHNICIAN_ID='technician-1',
               ECMP_AGENT_ID='agent-1', ECMP_ROUTER_ID='router-1',
               ECMP_ROUTER_HOST='10.255.255.1', ECMP_ROUTER_CA=str(ca))
    env.pop('OPENAI_API_KEY', None)
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    with ExitStack() as stack:
        processes = []
        try:
            commands = [
                ('php', [args.php, '-S', f'127.0.0.1:{php_port}', '-t', str(ROOT / 'php/sistema-generador')]),
                ('server', [sys.executable, '-m', 'uvicorn', 'server.app.main:create_app', '--factory',
                            '--host', '127.0.0.1', '--port', str(port)]),
            ]
            for name, command in commands:
                log = stack.enter_context((output / (name + '.log')).open('w', encoding='utf-8'))
                process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=flags)
                processes.append(process)
            with httpx.Client(base_url=env['ECMP_SERVER_URL'], trust_env=False, timeout=2) as client:
                def healthy():
                    response = client.get('/health')
                    if response.status_code != 200:
                        return False
                    body = response.json()
                    return (body['mode'] == 'real' and body['ai_mode'] == 'simulated'
                            and body['v7_lab_enabled'] and body['real_write_enabled'])
                wait_until(healthy, processes)
                wait_until(lambda: httpx.get(env['ECMP_GENERATOR_URL'], trust_env=False, timeout=2).status_code == 401, processes)
            print('\nENSAYO REAL CHR 7.24.5: cambios solo tras aprobacion en la interfaz.', flush=True)
            print('Destino fijo: 10.255.255.1. Restaurar y preparar la base antes de solicitar ECMP.', flush=True)
            print('Interfaz:', env['ECMP_SERVER_URL'], flush=True)
            print('Clave temporal del tecnico:', technician, flush=True)
            print('Token temporal del agente (copiar en el siguiente prompt):', bootstrap, flush=True)
            print('El agente pedira ademas el usuario y password RouterOS con permisos read,write,api.', flush=True)
            print('Logs sin claves:', output, '| Ctrl+C termina los procesos de este ensayo.\n', flush=True)
            agent_env = {k: v for k, v in env.items() if k not in
                         ('ECMP_TECHNICIAN_TOKEN', 'ECMP_AGENT_TOKEN', 'ECMP_GENERATOR_TOKEN', 'OPENAI_API_KEY')}
            # Inherit the console for interactive secrets; never save or pipe router credentials.
            agent = subprocess.Popen([sys.executable, '-m', 'agent.app.main', '--lab-v7'], cwd=ROOT, env=agent_env)
            processes.append(agent)
            while all(p.poll() is None for p in processes):
                time.sleep(.5)
            code = agent.poll()
            if code not in (None, 0):
                raise RuntimeError('Agente termino con error; conservar evidencia y revisar')
            if code is None:
                raise RuntimeError('Servidor o PHP termino; conservar evidencia y revisar')
        except KeyboardInterrupt:
            print('\nCerrando el ensayo; no se restaura ni repite configuracion.', flush=True)
        finally:
            for process in reversed(processes):
                stop(process)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('No se pudo continuar el laboratorio:', type(exc).__name__, '| Revise CA, puertos y logs.', file=sys.stderr)
        sys.exit(1)
