import pytest
from server.app.services.discovery import recommend
from tests.integration.test_v7_flow import lab_system


def inspect(tech, agent):
    response = tech.post('/devices/' + agent.session_id + '/inspect')
    assert response.status_code == 201
    record = response.json()
    assert tech.post('/inspections/' + record['id'] + '/prepare').status_code == 409
    assert agent.step()
    return tech.get('/inspections/' + record['id']).json()


def test_guided_flow_without_manual_ids(system):
    settings, app, tech, agent = system
    devices = tech.get('/devices').json()
    assert devices[0]['id'] == agent.session_id
    assert 'token_hash' not in str(devices)
    assert agent.client.get('/devices').status_code == 401
    record = inspect(tech, agent)
    assert record['recommendation']['available']
    assert record['recommendation']['target']['management_interface'] == 'ether14'
    assert agent.router.calls == 0
    request = tech.post('/inspections/' + record['id'] + '/prepare').json()
    assert request['status'] == 'await_precheck'
    assert request['inspection_id'] == record['id']
    agent.step()
    request = tech.get('/requests/' + request['id']).json()
    assert request['status'] == 'await_approval'
    assert agent.router.calls == 0
    tech.post('/requests/' + request['id'] + '/decision', json={'decision': 'approve', 'binding_hash': request['binding_hash']}).raise_for_status()
    agent.step()
    agent.step()
    report = tech.get('/requests/' + request['id'] + '/report').json()
    assert report['inspection']['id'] == record['id']
    assert report['request']['status'] == 'configuration_with_warnings'
    assert tech.get('/history').json()[0]['id'] == request['id']


def test_guided_v7_and_existing_configuration(lab_system):
    _, _, tech, agent, device, _ = lab_system
    record = inspect(tech, agent)
    assert record['recommendation']['available']
    assert record['recommendation']['parameters']['ip1'] == 2
    request = tech.post('/inspections/' + record['id'] + '/prepare').json()
    agent.step()
    request = tech.get('/requests/' + request['id']).json()
    assert request['artifact']['routeros_family'] == 'v7'
    assert not device.writes
    tech.post('/requests/' + request['id'] + '/decision', json={'decision': 'reject', 'binding_hash': request['binding_hash']}).raise_for_status()
    device.data['tables']['/ip/firewall/nat'].append({'chain': 'srcnat'})
    blocked = inspect(tech, agent)
    assert not blocked['recommendation']['available']
    assert blocked['recommendation']['blockers']
    assert tech.post('/inspections/' + blocked['id'] + '/prepare').status_code == 409
    assert not device.writes


def test_analysis_expiry_and_session_privacy(system):
    _, app, tech, agent = system
    record = inspect(tech, agent)
    service = app.state.service
    service.clock = lambda: record['observed_at'] + 301
    assert tech.post('/inspections/' + record['id'] + '/prepare').status_code == 409
    assert tech.get('/devices').json() == []
    assert agent.client.get('/history').status_code == 401
    assert agent.client.get('/inspections/' + record['id']).status_code == 401


def test_failed_inspection_and_duplicate_pending(system):
    _, app, tech, agent = system
    first = tech.post('/devices/' + agent.session_id + '/inspect').json()
    second = tech.post('/devices/' + agent.session_id + '/inspect').json()
    assert first['id'] == second['id']
    app.state.service.clock = lambda: first['created'] + 301
    assert tech.get('/inspections/' + first['id']).json()['status'] == 'failed'
    assert agent.router.calls == 0


def test_discovery_does_not_expand_version_or_topology(lab_system):
    settings, _, _, _, device, _ = lab_system
    snapshot = device.snapshot()
    assert not recommend(snapshot, 'router-1', 'real', False)['available']
    snapshot['tables']['/ip/address'][0]['address'] = '192.168.1.3/24'
    proposal = recommend(snapshot, 'router-1', 'real', True)
    assert proposal['parameters']['ip1'] == 3
    assert not proposal['available']


def test_drift_after_discovery_still_blocks_generation(system):
    _, _, tech, agent = system
    record = inspect(tech, agent)
    agent.router.data['tables']['/ip/firewall/nat'].append({'chain': 'srcnat'})
    request = tech.post('/inspections/' + record['id'] + '/prepare').json()
    agent.step()
    request = tech.get('/requests/' + request['id']).json()
    assert request['status'] == 'intervention_required'
    assert not request.get('artifact')
    assert agent.router.calls == 0
