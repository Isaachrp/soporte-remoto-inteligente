"""Offline delivery integration with real PHP; no physical-router access."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import time

from fastapi.testclient import TestClient
import pytest
from agent.app.router import SimulatedRouter
from server.app.core.config import Settings
from server.app.main import create_app
from server.app.offline_contract import validate_package
from server.app.offline_runner import execute
from server.app.services.central_delivery import CentralDelivery
from shared.contracts import digest
from tests.conftest import php_server, TOKEN, ROOT
from tests.integration.test_v7_flow import LabAPIDouble


@pytest.fixture(params=['simulated', 'real'])
def central(request, tmp_path, php_server):
    real = request.param == 'real'
    settings = Settings(str(tmp_path / 'central.sqlite3'), 't'*40, 'a'*40, TOKEN,
                        php_server, mode=request.param, v7_lab_enabled=real)
    app = create_app(settings, central_only=True)
    client = TestClient(app, headers={'Authorization': 'Bearer ' + settings.technician_token})
    device = LabAPIDouble() if real else SimulatedRouter()
    yield app, client, device
    client.close()


def prepare(central):
    app, client, device = central
    response = client.post('/central/diagnostics', json={'snapshot': device.snapshot()})
    assert response.status_code == 201, response.text
    record = response.json()
    assert record['recommendation']['available'], record
    response = client.post('/central/deliveries/' + record['id'] + '/prepare', json={'confirmed': True})
    assert response.status_code == 200, response.text
    record = response.json()
    assert record['status'] == 'await_approval', record
    return record


def approve(central):
    record = prepare(central)
    response = central[1].post('/central/deliveries/' + record['id'] + '/decision',
        json={'decision': 'approve', 'binding_hash': record['request']['binding_hash']})
    assert response.status_code == 200, response.text
    return response.json()['package']


def test_delivery_without_agent_and_execution(central, tmp_path):
    app, client, device = central
    package = approve(central)
    with app.state.service.store.transaction() as db:
        assert not app.state.service.store.all(db, 'session')
        assert not app.state.service.store.all(db, 'task')
    response = client.get('/central/deliveries/' + package['id'] + '/package')
    assert response.json() == package
    validate_package(package)
    result = execute(package, device, tmp_path, lambda _: True)
    assert result['status'] == 'configuration_with_warnings', result
    assert result['completed'] == len(package['executable']['operations'])
    saved = json.loads((tmp_path / ('resultado-' + package['id'] + '.json')).read_text(encoding='utf-8'))
    assert saved == result
    with pytest.raises(ValueError):
        execute(package, device, tmp_path, lambda _: True)
    # Even a restored base cannot reuse a delivery in the same output directory.
    device.data = copy.deepcopy(package['snapshot'])
    with pytest.raises(FileExistsError):
        execute(package, device, tmp_path, lambda _: True)


def test_reject_authentication_and_approval_binding(central):
    app, client, device = central
    assert TestClient(app).get('/central/deliveries').status_code == 401
    assert client.post('/agent/sessions', json={}).status_code == 404
    record = prepare(central)
    base = '/central/deliveries/' + record['id']
    assert client.get(base + '/package').status_code == 409
    assert client.post(base + '/decision', json={'decision': 'approve', 'binding_hash': 'wrong'}).status_code == 409
    assert client.post(base + '/decision', json={'decision': 'reject', 'binding_hash': record['request']['binding_hash']}).status_code == 200
    assert client.get(base + '/package').status_code == 409
    assert client.get(base + '/executable').status_code == 409


def test_invalid_diagnostic_and_confirmation(central):
    _, client, device = central
    assert client.post('/central/diagnostics', json={'schema': 'ecmp-lab-readonly/1'}).status_code == 422
    bad = device.snapshot()
    bad['tables']['/system/password'] = [{'password': 'SECRET'}]
    response = client.post('/central/diagnostics', json=bad)
    assert response.status_code == 422 and 'SECRET' not in response.text
    record = client.post('/central/diagnostics', json=device.snapshot()).json()
    assert client.post('/central/deliveries/' + record['id'] + '/prepare', json={'confirmed': False}).status_code == 422
    device.data['version'] = '7.99'
    incompatible = client.post('/central/diagnostics', json=device.snapshot())
    if incompatible.status_code == 201:
        assert not incompatible.json()['recommendation']['available']
        assert client.post('/central/deliveries/' + incompatible.json()['id'] + '/prepare', json={'confirmed': True}).status_code == 409
    else:
        assert incompatible.status_code == 422


def test_expiry_tampering_and_drift(central, tmp_path):
    app, client, device = central
    package = approve(central)
    with pytest.raises(ValueError):
        validate_package(package, package['expires_at'])
    changed = copy.deepcopy(package)
    changed['executable']['operations'][0]['command'] = '/system/reset-configuration'
    changed['package_hash'] = digest({k: v for k, v in changed.items() if k != 'package_hash'})
    with pytest.raises(ValueError):
        validate_package(changed)
    # A change while the confirmation is on screen must block all writes.
    def confirm(_):
        device.data['identity'] = 'other-router'
        return True
    with pytest.raises(ValueError):
        execute(package, device, tmp_path, confirm)
    assert not list(tmp_path.glob('resultado-*'))
    device.data = copy.deepcopy(package['snapshot'])
    assert execute(package, device, tmp_path, lambda _: False)['status'] == 'cancelled'
    app.state.service.clock = lambda: package['expires_at'] + 1
    assert client.get('/central/deliveries/' + package['id'] + '/package').status_code == 409


def test_partial_write_is_journaled_and_not_retried(central, tmp_path):
    _, _, device = central
    package = approve(central)
    def partial(operations):
        raise TimeoutError('Secret exception must not be recorded')
    device.apply = partial
    result = execute(package, device, tmp_path, lambda _: True)
    assert result['status'] == 'intervention_required'
    assert result['completed'] is None
    assert 'Secret' not in json.dumps(result)
    with pytest.raises(FileExistsError):
        execute(package, device, tmp_path, lambda _: True)


def test_restart_retains_approved_delivery(central):
    app, client, device = central
    package = approve(central)
    restarted = create_app(app.state.service.settings, central_only=True)
    client2 = TestClient(restarted, headers=client.headers)
    assert client2.get('/central/deliveries/' + package['id'] + '/package').json() == package
    assert client2.get('/central/deliveries').json()[0]['status'] == 'approved'


def test_windows_file_lock_retries_only_evidence(central, tmp_path, monkeypatch):
    import server.app.offline_runner as runner
    _, _, device = central
    package = approve(central)
    original_replace = runner.os.replace
    original_apply = device.apply
    calls = {'save': 0, 'apply': 0}
    def locked_once(source, target):
        calls['save'] += 1
        if calls['save'] == 1:
            raise PermissionError('Temporary scanner lock')
        return original_replace(source, target)
    def apply_once(operations):
        calls['apply'] += 1
        return original_apply(operations)
    monkeypatch.setattr(runner.os, 'replace', locked_once)
    monkeypatch.setattr(device, 'apply', apply_once)
    result = execute(package, device, tmp_path, lambda _: True)
    assert result['status'] == 'configuration_with_warnings'
    assert calls['apply'] == 1 and calls['save'] >= 2


def test_captured_snapshot_is_supported(central):
    app, client, device = central
    if device.mode != 'real':
        return
    fixture = json.loads((ROOT / 'tests/fixtures/v7-precheck-main-fib-flag.json').read_text(encoding='utf-8'))
    response = client.post('/central/diagnostics', json=fixture)
    assert response.status_code == 201, response.text
    assert response.json()['recommendation']['available']


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows executable')
def test_build_actual_executable(central, tmp_path):
    app, client, device = central
    package = approve(central)
    path = CentralDelivery(app.state.service).executable(package['id'])
    assert path.read_bytes()[:2] == b'MZ'
    result = subprocess.run([str(path), '--validate-only'], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Paquete integrado' in result.stdout
    assert CentralDelivery(app.state.service).executable(package['id']) == path
    if device.mode == 'simulated':
        result = subprocess.run([str(path)], input='APLICAR lab-router\n\n', capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads((path.parent / ('resultado-' + package['id'] + '.json')).read_text(encoding='utf-8'))
        assert report['status'] == 'configuration_with_warnings'
    (tmp_path / 'built-path.txt').write_text(str(path), encoding='utf-8')
