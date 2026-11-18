import copy
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from server.app.core.config import Settings
from server.app.main import create_app
from server.app.offline_contract import validate_package
from server.app.offline_runner import execute
from shared.contracts import digest
from shared.v7 import expected_operations
from server.app.services.discovery import recommend
from server.app.services.central_delivery import CentralDelivery
from tests.conftest import php_server, TOKEN
from tests.integration.test_v7_flow import LabAPIDouble


@pytest.fixture
def central_existing(tmp_path, php_server):
    settings = Settings(str(tmp_path / 'central.sqlite3'), 't'*40, 'a'*40, TOKEN,
                        php_server, mode='real', v7_lab_enabled=True)
    app = create_app(settings, central_only=True)
    with TestClient(app, headers={'Authorization': 'Bearer ' + settings.technician_token}) as client:
        yield client, LabAPIDouble()


def populate(device, complete):
    parameters = recommend(device.snapshot(), 'router-1', 'real', True)['parameters']
    for command, args in expected_operations(parameters):
        if complete or command == '/ip/route/add':
            device.api(command, **args)
    device.writes.clear()


def package_for(client, device):
    record = client.post('/central/diagnostics', json=device.snapshot()).json()
    assert record['recommendation']['can_continue_existing']
    assert not record['recommendation']['available']
    url = '/central/deliveries/' + record['id']
    assert client.post(url + '/prepare', json={'confirmed': True}).status_code == 409
    assert client.post(url + '/prepare', json={'confirmed': False, 'continue_existing': True}).status_code == 422
    response = client.post(url + '/prepare', json={'confirmed': True, 'continue_existing': True})
    assert response.status_code == 200, response.text
    record = response.json()
    assert record['status'] == 'await_approval', record
    assert client.get(url + '/package').status_code == 409
    response = client.post(url + '/decision', json={'decision': 'approve', 'binding_hash': record['request']['binding_hash']})
    assert response.status_code == 200, response.text
    package = client.get(url + '/package').json()
    validate_package(package)
    return package


@pytest.mark.parametrize('complete', [False, True])
def test_continue_preserves_and_only_adds_missing(central_existing, tmp_path, complete):
    client, device = central_existing
    populate(device, complete)
    # Comments do not change the meaning of an existing rule.
    device.data['tables']['/ip/route'][-1]['comment'] = 'Mi WAN'
    before = copy.deepcopy(device.data)
    package = package_for(client, device)
    assert package['schema'] == 'ecmp-offline/2'
    assert len(package['executable']['operations']) == (0 if complete else 5)
    result = execute(package, device, tmp_path, lambda _: True)
    assert result['status'] == 'configuration_with_warnings', result
    assert result['completed'] == (0 if complete else 5)
    assert result['preserved'] == (7 if complete else 2)
    assert len(device.writes) == result['completed']
    for table, rows in before['tables'].items():
        assert all(row in device.data['tables'][table] for row in rows)


@pytest.mark.parametrize('conflict', ['gateway', 'duplicate', 'firewall', 'identity'])
def test_continue_rejects_conflicting_configuration(central_existing, conflict):
    client, device = central_existing
    populate(device, False)
    if conflict == 'gateway':
        device.data['tables']['/ip/route'][-1]['gateway'] = '192.168.99.1'
    elif conflict == 'duplicate':
        device.data['tables']['/ip/route'].append(copy.deepcopy(device.data['tables']['/ip/route'][-1]))
    elif conflict == 'firewall':
        device.data['tables']['/ip/firewall/filter'].append({'chain': 'forward', 'action': 'drop'})
    else:
        device.data['identity'] = 'another-router'
    record = client.post('/central/diagnostics', json=device.snapshot()).json()
    assert not record['recommendation']['can_continue_existing']
    assert client.post('/central/deliveries/' + record['id'] + '/prepare',
                       json={'confirmed': True, 'continue_existing': True}).status_code == 409
    assert not device.writes


def test_continue_tampering_drift_and_partial_failure(central_existing, tmp_path):
    client, device = central_existing
    populate(device, False)
    package = package_for(client, device)
    altered = copy.deepcopy(package)
    altered['executable']['operations'].pop()
    altered['executable']['operations_hash'] = digest(altered['executable']['operations'])
    altered['package_hash'] = digest({k: v for k, v in altered.items() if k != 'package_hash'})
    with pytest.raises(ValueError):
        validate_package(altered)
    def confirm(_):
        device.data['tables']['/ip/route'][-1]['comment'] = 'changed'
        return True
    with pytest.raises(ValueError):
        execute(package, device, tmp_path, confirm)
    assert not device.writes
    device.data = copy.deepcopy(package['snapshot'])
    device.fail_after = 1
    result = execute(package, device, tmp_path, lambda _: True)
    assert result['status'] == 'intervention_required'
    assert result['completed'] == 1
    assert len(device.writes) == 1


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows executable')
def test_build_continuation_executable(central_existing):
    client, device = central_existing
    populate(device, True)
    package = package_for(client, device)
    path = CentralDelivery(client.app.state.service).executable(package['id'])
    result = subprocess.run([str(path), '--validate-only'], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Operaciones: 0' in result.stdout
