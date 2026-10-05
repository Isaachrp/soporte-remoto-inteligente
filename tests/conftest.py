import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import httpx
import pytest
from fastapi.testclient import TestClient
from server.app.core.config import Settings
from server.app.main import create_app
from agent.app.router import SimulatedRouter
from agent.app.runner import Agent

ROOT = Path(__file__).resolve().parents[1]
PHP = os.getenv('PHP_EXE') or shutil.which('php') or 'C:/xampp/php/php.exe'
TOKEN = 'generator-' + 'g'*40

@pytest.fixture(scope='session')
def php_server():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env['ECMP_GENERATOR_TOKEN'] = TOKEN
    process = subprocess.Popen([PHP,'-S',f'127.0.0.1:{port}','-t',str(ROOT/'php/sistema-generador')],
        env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    url = f'http://127.0.0.1:{port}/api/ecmp.php'
    try:
        for _ in range(100):
            try:
                if httpx.get(url,timeout=0.2,trust_env=False).status_code == 401:
                    break
            except httpx.HTTPError:
                time.sleep(0.05)
        else:
            pytest.fail('PHP no inicio; no se sustituye por mock')
        yield url
    finally:
        process.terminate()
        process.wait(timeout=10)

@pytest.fixture
def parameters():
    return {'tipo':'ECMP','lineas':2,'vel1':'5M','gw1':'192.168.1.1','ip1':2,
            'vel2':'10M','gw2':'192.168.2.1','ip2':2,'lan':'172.16.0.1','dhcp':True}

@pytest.fixture
def system(tmp_path,php_server):
    settings = Settings(str(tmp_path/'db.sqlite3'),'technician-'+'t'*40,'agent-'+'a'*40,TOKEN,php_server,mode='simulated')
    app = create_app(settings)
    client = TestClient(app)
    technician = TestClient(app,headers={'Authorization':'Bearer '+settings.technician_token})
    router = SimulatedRouter()
    agent = Agent(client,router,'agent-1','router-1',settings.agent_token)
    agent.register()
    yield settings,app,technician,agent
    agent.close()
    technician.close()

def new_request(technician,agent,parameters):
    response = technician.post('/requests',json={'text':'Configurar ECMP','session_id':agent.session_id,
        'target':{'router_id':'router-1','identity':'lab-router','management_interface':'ether14'},'parameters':parameters})
    assert response.status_code == 201, response.text
    return response.json()
