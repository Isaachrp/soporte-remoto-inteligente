import json

from tests.conftest import new_request


def test_report_authenticated_and_complete(system, parameters):
    settings, app, tech, agent = system
    record = new_request(tech, agent, parameters)
    agent.step()
    record = tech.get('/requests/' + record['id']).json()
    tech.post('/requests/' + record['id'] + '/decision', json={
        'decision': 'approve', 'binding_hash': record['binding_hash']}).raise_for_status()
    agent.step()
    agent.step()
    path = '/requests/' + record['id'] + '/report'
    assert agent.client.get(path).status_code == 401
    response = tech.get(path)
    assert response.status_code == 200
    report = response.json()
    assert report['schema'] == 'ecmp-delivery/1'
    assert report['request']['status'] == 'configuration_with_warnings'
    assert report['mode'] == report['ai_mode'] == 'simulated'
    assert report['real_write_enabled'] is False
    assert report['request']['artifact']['script']
    assert sum(row['event'] == 'approval_consumed' for row in report['audit']) == 1
    serialized = json.dumps(report)
    for token in (settings.technician_token, settings.agent_token, settings.generator_token,
                  agent.client.headers['Authorization'].removeprefix('Bearer ')):
        assert token not in serialized
    assert tech.get('/requests/missing/report').status_code == 404
