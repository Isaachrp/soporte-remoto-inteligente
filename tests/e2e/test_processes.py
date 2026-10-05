"""Real HTTP across separate PHP, Uvicorn, and agent processes. No router/OpenAI."""
import json
import os
from pathlib import Path
import socket
import shutil
import hashlib
import subprocess
import sys
import time
import httpx
import pytest
from tests.conftest import ROOT, TOKEN

def wait_for(fn, seconds=30):
    until = time.monotonic()+seconds
    while time.monotonic() < until:
        try:
            value = fn()
            if value:
                return value
        except (httpx.HTTPError, OSError, IndexError):
            pass
        time.sleep(.1)
    raise AssertionError('Timeout esperando proceso; no se usa fallback simulado')

@pytest.mark.parametrize('portable',[False,True])
def test_full_http_processes(tmp_path,php_server,parameters,portable):
    exe = ROOT/'dist/ecmp-agent/ecmp-agent.exe'
    if portable and not exe.exists():
        pytest.skip('Construya el paquete antes de validar portabilidad')
    if portable:
        relocated = tmp_path/'portable'
        shutil.copytree(exe.parent,relocated)
        exe = relocated/exe.name
        for line in (relocated/'SHA256SUMS').read_text().splitlines():
            expected,relative = line.split('  ',1)
            assert hashlib.sha256((relocated/relative).read_bytes()).hexdigest() == expected
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env.update(ECMP_MODE='simulated',ECMP_AI_MODE='simulated',ECMP_DATABASE=str(tmp_path/'e2e.sqlite3'),
               ECMP_GENERATOR_URL=php_server,ECMP_GENERATOR_TOKEN=TOKEN,
               ECMP_TECHNICIAN_TOKEN='t'*48,ECMP_AGENT_TOKEN='a'*48,ECMP_AGENT_ID='agent-1',ECMP_ROUTER_ID='router-1',
               ECMP_SERVER_URL=f'http://127.0.0.1:{port}')
    flags = getattr(subprocess,'CREATE_NO_WINDOW',0)
    log = tmp_path/'agent.log'
    with (tmp_path/'server.log').open('w') as server_log, log.open('w') as agent_log:
        server = subprocess.Popen([sys.executable,'-m','uvicorn','server.app.main:create_app','--factory','--host','127.0.0.1','--port',str(port)],
                                  cwd=ROOT,env=env,stdout=server_log,stderr=server_log,creationflags=flags)
        agent = None
        try:
            with httpx.Client(base_url=env['ECMP_SERVER_URL'],headers={'Authorization':'Bearer '+env['ECMP_TECHNICIAN_TOKEN']},trust_env=False) as client:
                wait_for(lambda: client.get('/health').status_code == 200)
                command = [str(exe)] if portable else [sys.executable,'-m','agent.app.main']
                # Deliberately remove backend and generator credentials from agent environment.
                agent_env = {k:v for k,v in env.items() if k not in ('ECMP_TECHNICIAN_TOKEN','ECMP_AGENT_TOKEN','ECMP_GENERATOR_TOKEN','OPENAI_API_KEY')}
                if portable:
                    agent_env.pop('PYTHONPATH',None)
                    agent_env.pop('PYTHONHOME',None)
                agent = subprocess.Popen(command+['--token-stdin','--max-tasks','3'],cwd=exe.parent if portable else ROOT,env=agent_env,
                    stdin=subprocess.PIPE,stdout=agent_log,stderr=agent_log,text=True,creationflags=flags)
                agent.stdin.write('a'*48+'\n')
                agent.stdin.close()
                session = wait_for(lambda: next((line.split()[1] for line in log.read_text().splitlines() if line.startswith('Sesion:')),None))
                response = client.post('/requests',json={'text':'Configurar ECMP','session_id':session,
                    'target':{'router_id':'router-1','identity':'lab-router','management_interface':'ether14'},'parameters':parameters})
                assert response.status_code == 201,response.text
                id = response.json()['id']
                def awaiting():
                    r = client.get('/requests/'+id).json()
                    return r if r['status'] == 'await_approval' else None
                r = wait_for(awaiting)
                assert client.post('/requests/'+id+'/decision',json={'decision':'approve','binding_hash':r['binding_hash']}).status_code == 200
                wait_for(lambda: client.get('/requests/'+id).json()['status'] == 'configuration_with_warnings')
                assert agent.wait(timeout=10) == 0,log.read_text()
                assert 'a'*48 not in log.read_text()
                if portable:
                    assert not list(exe.parent.rglob('.env'))
                audit = client.get('/requests/'+id+'/audit').json()
                assert any(row['event']=='approval_consumed' for row in audit)
        finally:
            if agent is not None and agent.poll() is None:
                agent.terminate()
                agent.wait(timeout=10)
            server.terminate()
            server.wait(timeout=10)
