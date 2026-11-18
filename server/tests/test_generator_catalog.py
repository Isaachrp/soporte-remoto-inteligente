import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.app.router import SimulatedRouter
from server.app.core.config import Settings
from server.app.main import create_app
from server.app.generator_catalog import LABELS, V7_ONLY, fields, validate_parameters
from server.app.services.catalog_generator import generate
from server.app.services.catalog_ai import projection, Recommendations
from server.app.services.ai import Interpreter, AIError
from server.app.catalog_contract import validate
from server.app.catalog_runner import execute
from server.app.services.catalog_delivery import CatalogDelivery
from shared.contracts import digest
from tests.integration.test_v7_flow import LabAPIDouble


def parameters(procedure):
    p = {f['name']: f['default'] for f in fields(procedure)}
    for k in p:
        if k.startswith('gw'):
            p[k] = '192.168.' + k[2:] + '.1'
    if 'lan' in p:
        p['lan'] = '192.168.10.0/24' if procedure == 'Firewall' else '172.16.0.1'
    p.update({k: v for k, v in {'wan': 'ether1', 'ip_cliente': '172.16.0.10',
        'fecha_inicio': '2026-11-05', 'fecha_vencimiento': '2026-12-05', 'perfil': 'default',
        'client': 'testclient', 'password': 'examplepass', 'ip': '192.0.2.1',
        'export_pass': 'examplecert'}.items() if k in p})
    return p


@pytest.mark.parametrize('procedure', list(LABELS))
def test_original_php_generates_each_catalog_entry(procedure):
    artifact = generate(procedure, parameters(procedure))
    assert '/' in artifact['script']
    assert '<br' not in artifact['script']
    assert artifact['script_hash'] == hashlib.sha256(artifact['script'].encode()).hexdigest()
    assert bool(artifact['attachment']) == (procedure == 'OpenVPN')


@pytest.fixture
def catalog_client(tmp_path):
    settings = Settings(str(tmp_path / 'catalog.sqlite3'), 't'*40, 'a'*40, 'g'*40,
                        'http://127.0.0.1:1/api/ecmp.php', mode='real', v7_lab_enabled=True)
    app = create_app(settings, central_only=True)
    with TestClient(app, headers={'Authorization': 'Bearer ' + settings.technician_token}) as client:
        yield client


def prepared(client, procedure='Firewall'):
    snapshot = LabAPIDouble().snapshot() if procedure in V7_ONLY else SimulatedRouter().snapshot()
    record = client.post('/central/catalog/diagnostics', json=snapshot).json()
    assert len(record['options']) == 15
    assert 'recommendations' in record
    url = '/central/catalog/' + record['id']
    response = client.post(url + '/prepare', json={'procedure': procedure, 'parameters': parameters(procedure), 'confirmed': True})
    assert response.status_code == 200, response.text
    return response.json(), url


def approved(client, procedure='Firewall'):
    record, url = prepared(client, procedure)
    assert client.get(url + '/package').status_code == 409
    response = client.post(url + '/decision', json={'decision': 'approve', 'binding_hash': record['request']['binding_hash']})
    assert response.status_code == 200, response.text
    package = client.get(url + '/package').json()
    validate(package)
    return package


@pytest.mark.parametrize('procedure', list(LABELS))
def test_catalog_prepare_approve_package(catalog_client, procedure):
    package = approved(catalog_client, procedure)
    assert package['procedure'] == procedure
    assert package['schema'] == 'php-generator-offline/1'


def test_ai_receives_projected_diagnostic_and_only_catalog_choices(catalog_client, monkeypatch):
    catalog_client.app.state.service.settings.ai_mode = 'openai'
    seen = []
    def parse(self, schema, prompt, data):
        seen.append(data)
        return Recommendations(summary='Dos rutas WAN observadas.', suggestions=[{'procedure': 'PCCrV7', 'reason': 'Alternativa para distribuir conexiones entre enlaces.'}])
    monkeypatch.setattr(Interpreter, '_parse', parse)
    snapshot = LabAPIDouble().snapshot()
    snapshot['tables']['/ip/route'][0]['comment'] = 'SECRET-COMMENT'
    response = catalog_client.post('/central/catalog/diagnostics', json=snapshot)
    assert response.status_code == 201, response.text
    assert response.json()['recommendations']['suggestions'][0]['procedure'] == 'PCCrV7'
    assert 'SECRET-COMMENT' not in json.dumps(seen)
    assert 'not_collected' in seen[0]['diagnostic']
    def failed(*args):
        raise AIError('ai_timeout')
    monkeypatch.setattr(Interpreter, '_parse', failed)
    response = catalog_client.post('/central/catalog/diagnostics', json=snapshot)
    assert response.json()['analysis_error'] == 'ai_timeout'
    assert 'recommendations' not in response.json()


def test_unknown_parameters_injection_and_wrong_version(catalog_client):
    p = parameters('Firewall')
    p['wan'] = 'WAN; /system reset-configuration'
    with pytest.raises(ValueError):
        validate_parameters('Firewall', p)
    snapshot = LabAPIDouble().snapshot()
    record = catalog_client.post('/central/catalog/diagnostics', json=snapshot).json()
    url = '/central/catalog/' + record['id'] + '/prepare'
    assert catalog_client.post(url, json={'procedure': 'PCC', 'parameters': parameters('PCC'), 'confirmed': True}).status_code == 409
    assert catalog_client.post(url, json={'procedure': 'unknown', 'parameters': {}, 'confirmed': True}).status_code == 422
    assert catalog_client.post(url, json={'procedure': 'Firewall', 'parameters': parameters('Firewall'), 'confirmed': False}).status_code == 422
    assert TestClient(catalog_client.app).post('/central/catalog/diagnostics', json=snapshot).status_code == 401


class ScriptRouter:
    def __init__(self, snapshot):
        self.data = copy.deepcopy(snapshot)
        self.scripts = []
        self.calls = []
        self.fail = False

    def snapshot(self):
        return copy.deepcopy(self.data)

    def api(self, command, **args):
        self.calls.append((command, args))
        if command == '/system/script/print':
            return iter(copy.deepcopy(self.scripts))
        if command == '/system/script/add':
            self.scripts.append({'.id': '*1', **args})
        if command == '/system/script/run' and self.fail:
            raise TimeoutError('Sensitive exception')
        if command == '/system/script/set':
            self.scripts[0].update(args)
        return iter(())


def test_runner_confirmation_drift_marker_and_partial_failure(catalog_client, tmp_path):
    package = approved(catalog_client)
    router = ScriptRouter(package['snapshot'])
    assert execute(package, router, tmp_path, lambda _: False)['status'] == 'cancelled'
    assert not router.calls
    def changed(_):
        router.data['identity'] = 'changed'
        return True
    with pytest.raises(ValueError):
        execute(package, router, tmp_path, changed)
    assert not router.calls
    router.data = copy.deepcopy(package['snapshot'])
    result = execute(package, router, tmp_path, lambda _: True)
    assert result['status'] == 'script_executed'
    assert not result['functionality_verified']
    source = next(args['source'] for cmd, args in router.calls if cmd.endswith('/add'))
    assert source == package['artifact']['script']
    assert router.scripts[0]['source'] == ''
    other = tmp_path / 'copy'
    other.mkdir()
    assert execute(package, router, other, lambda _: True)['status'] == 'intervention_required'
    assert sum(cmd == '/system/script/run' for cmd, _ in router.calls) == 1
    failed = ScriptRouter(package['snapshot'])
    failed.fail = True
    other = tmp_path / 'failed'
    other.mkdir()
    assert execute(package, failed, other, lambda _: True)['status'] == 'intervention_required'
    assert 'Sensitive' not in next(other.glob('*.json')).read_text()


def test_package_tamper_expiry_and_reject(catalog_client):
    package = approved(catalog_client)
    altered = copy.deepcopy(package)
    altered['artifact']['script'] += '\n/system reboot'
    with pytest.raises(ValueError):
        validate(altered)
    with pytest.raises(ValueError):
        validate(package, package['expires_at'])
    record, url = prepared(catalog_client)
    assert catalog_client.post(url + '/decision', json={'decision': 'approve', 'binding_hash': '0'*64}).status_code == 409
    assert catalog_client.post(url + '/decision', json={'decision': 'reject', 'binding_hash': record['request']['binding_hash']}).status_code == 200
    assert catalog_client.get(url + '/package').status_code == 409


@pytest.mark.parametrize('stage,code,message', [
    ('create_script', 'permissions', 'not enough permissions (9) SECRET'),
    ('run_script', 'script_syntax', 'expected end of command SECRET'),
    ('clear_script_source', 'permissions', 'not enough permissions SECRET'),
])
def test_runner_reports_failure_stage_without_secrets(catalog_client, tmp_path, stage, code, message):
    from librouteros.exceptions import TrapError
    package = approved(catalog_client)
    router = ScriptRouter(package['snapshot'])
    original = router.api
    command = {'create_script': '/system/script/add', 'run_script': '/system/script/run',
               'clear_script_source': '/system/script/set'}[stage]
    def failing(path, **args):
        if path == command:
            raise TrapError(message)
        return original(path, **args)
    router.api = failing
    result = execute(package, router, tmp_path, lambda _: True)
    assert result['failed_stage'] == stage
    assert result['error_code'] == code
    assert result['script_run_requested'] == (stage != 'create_script')
    assert result['script_run_completed'] == (stage == 'clear_script_source')
    assert 'SECRET' not in json.dumps(result)


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows executable')
def test_build_catalog_executable(catalog_client):
    package = approved(catalog_client, 'PCC-DYNAMIC')
    path = CatalogDelivery(catalog_client.app.state.service).executable(package['id'])
    result = subprocess.run([str(path), '--validate-only'], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Paquete integrado' in result.stdout
