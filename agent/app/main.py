import argparse
import getpass
import os
import sys
import time
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv
from agent.app.router import NativeRouter, SimulatedRouter
from agent.app.runner import Agent
from shared.contracts import VERSION

def main():
    parser = argparse.ArgumentParser(description='Agente ECMP portatil; inicio manual')
    parser.add_argument('--version',action='version',version=VERSION)
    parser.add_argument('--once',action='store_true',help='Registrar, consultar una vez y cerrar')
    parser.add_argument('--token-stdin',action='store_true',help='Leer token de un pipe confiable; no argumentos ni archivo')
    parser.add_argument('--max-tasks',type=int,default=0,help='Cerrar tras N tareas (0: hasta Ctrl+C o caducidad)')
    parser.add_argument('--diagnose', action='store_true', help='Prueba real de solo lectura, sin servidor ni token')
    parser.add_argument('--lab-v7', action='store_true', help='Permitir ensayo supervisado exclusivo CHR-LAB 7.24.5; no certificacion')
    parser.add_argument('--host', help='IP/nombre del router, coincidente con SAN del certificado')
    parser.add_argument('--ca', help='Archivo PEM de la CA del laboratorio')
    parser.add_argument('--identity', help='Identidad esperada exacta del router')
    parser.add_argument('--routeros-version', help='Version esperada exacta, incluido sufijo si existe')
    parser.add_argument('--management', help='Nombre actual del puerto administrativo')
    parser.add_argument('--report', help='Archivo JSON nuevo para el informe de laboratorio')
    args = parser.parse_args()
    if args.diagnose:
        required = ('host', 'ca', 'identity', 'routeros_version', 'management', 'report')
        if any(not getattr(args, key) for key in required):
            parser.error('--diagnose requiere --host, --ca, --identity, --routeros-version, --management y --report')
        if args.once or args.token_stdin or args.max_tasks or args.lab_v7:
            parser.error('--diagnose no admite opciones de sesiones/tareas')
        from agent.app.diagnostic import run_diagnostic
        raise SystemExit(run_diagnostic(args))
    load_dotenv('agent/.env')
    mode = os.getenv('ECMP_MODE','real')
    if args.lab_v7 and mode != 'real':
        parser.error('--lab-v7 requiere ECMP_MODE=real')
    url = os.environ['ECMP_SERVER_URL']
    parsed = urlparse(url)
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1','localhost')):
        raise ValueError('HTTPS requerido')
    if parsed.username or parsed.password:
        raise ValueError('No se permiten credenciales en URL')
    token = sys.stdin.readline().strip() if args.token_stdin else getpass.getpass('Token temporal de registro del agente: ')
    if mode == 'simulated':
        router = SimulatedRouter()
    elif mode == 'real':
        username = input('Usuario RouterOS: ')
        password = getpass.getpass('Password RouterOS (solo memoria): ')
        try:
            router = NativeRouter(os.environ['ECMP_ROUTER_HOST'],username,password,os.environ['ECMP_ROUTER_CA'], lab_enabled=args.lab_v7)
        finally:
            password = None
    else:
        raise ValueError('Modo invalido')
    client = httpx.Client(base_url=url,timeout=20,follow_redirects=False,trust_env=False)
    agent = Agent(client,router,os.getenv('ECMP_AGENT_ID','agent-1'),os.getenv('ECMP_ROUTER_ID','router-1'),token)
    token = None
    try:
        print('Sesion:',agent.register(), '| modo:',mode, '| version:',VERSION, flush=True)
        completed = 0
        while True:
            completed += int(agent.step())
            if args.once or (args.max_tasks and completed >= args.max_tasks):
                break
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        agent.close()

if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Agente detenido: error de configuracion, conexion o autorizacion. Revise auditoria; no reintente escrituras.',file=sys.stderr)
        sys.exit(1)
