"""Start only PHP + the central application. Never starts or contacts an agent."""
import argparse
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
import uuid
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def select_port(requested):
    if requested == 0:
        return free_port()
    preferred = 8000 if requested is None else requested
    try:
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', preferred))
    except OSError:
        if requested is not None:
            raise ValueError(f'El puerto {preferred} no está disponible. Use --port 0 para elegir uno libre.') from None
        selected = free_port()
        print(f'Puerto 8000 no disponible; se utilizará {selected}.', flush=True)
        return selected
    return preferred


def main():
    load_dotenv(ROOT / 'server/.env')
    parser = argparse.ArgumentParser(description='Sistema central ECMP · sin agente')
    parser.add_argument('--simulate', action='store_true', help='Entregas de simulación, sin escrituras reales')
    parser.add_argument('--ai', choices=['simulated', 'openai', 'openrouter'], default=os.getenv('ECMP_AI_MODE', 'simulated'))
    parser.add_argument('--port', type=int, default=None)
    args = parser.parse_args()
    if args.port is not None and not 0 <= args.port <= 65535:
        parser.error('Puerto inválido')
    directory = ROOT / 'runtime/central'
    directory.mkdir(parents=True, exist_ok=True)
    try:
        port = select_port(args.port)
    except ValueError as exc:
        parser.error(str(exc))
    php_port = free_port()
    while php_port == port:
        php_port = free_port()
    key = secrets.token_urlsafe(32)
    env = dict(os.environ, ECMP_TECHNICIAN_TOKEN=key, ECMP_AGENT_TOKEN=secrets.token_urlsafe(32),
               ECMP_GENERATOR_TOKEN=secrets.token_urlsafe(32), ECMP_MODE='simulated' if args.simulate else 'real',
               ECMP_AI_MODE=args.ai, ECMP_V7_LAB_ENABLED='0' if args.simulate else '1',
               ECMP_DATABASE=str(directory / ('simulated.sqlite3' if args.simulate else 'real.sqlite3')),
               ECMP_GENERATOR_URL=f'http://127.0.0.1:{php_port}/api/ecmp.php')
    php = os.environ.get('PHP_EXE', 'C:/xampp/php/php.exe')
    processes = []
    try:
        with (directory / ('start-' + uuid.uuid4().hex + '.log')).open('w', encoding='utf-8') as log:
            for cmd in ([php, '-S', f'127.0.0.1:{php_port}', '-t', str(ROOT / 'php/sistema-generador')],
                        [sys.executable, '-m', 'uvicorn', 'server.app.central:create_app', '--factory',
                         '--host', '127.0.0.1', '--port', str(port)]):
                processes.append(subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log, stderr=log,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)))
            with httpx.Client(trust_env=False, timeout=1) as client:
                for _ in range(100):
                    if any(p.poll() is not None for p in processes):
                        raise RuntimeError('No se pudo arrancar. Revise el puerto y runtime/central/*.log')
                    try:
                        ready = client.get(f'http://127.0.0.1:{port}/central/status', headers={'Authorization': 'Bearer ' + key})
                        php_ready = client.get(env['ECMP_GENERATOR_URL'])
                        if ready.status_code == 200 and php_ready.status_code == 401:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(.2)
                else:
                    raise RuntimeError('Arranque incompleto. Consulte runtime/central/*.log')
            print(f'Sistema central: http://127.0.0.1:{port}/', flush=True)
            print('Clave del técnico:', key, flush=True)
            print('Router:', env['ECMP_MODE'], '| IA:', args.ai, '| Sin agente. Ctrl+C para cerrar.', flush=True)
            while all(p.poll() is None for p in processes):
                time.sleep(.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
            p.wait(timeout=10)


if __name__ == '__main__':
    main()
