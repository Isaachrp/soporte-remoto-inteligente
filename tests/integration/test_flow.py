import copy
import time
from fastapi.testclient import TestClient
from server.app.main import create_app
from tests.conftest import new_request

def ready(system,parameters):
    settings,app,tech,agent = system
    request = new_request(tech,agent,parameters)
    assert request['status'] == 'await_precheck'
    assert agent.step()
    request = tech.get('/requests/'+request['id']).json()
    assert request['status'] == 'await_approval', request
    return request

def approve(tech,r):
    return tech.post('/requests/'+r['id']+'/decision',json={'decision':'approve','binding_hash':r['binding_hash']})

def test_complete_real_php_simulated_router(system,parameters):
    settings,app,tech,agent = system
    r = ready(system,parameters)
    assert agent.step() is False  # genuine human pause
    assert approve(tech,r).status_code == 200
    assert agent.step()
    assert tech.get('/requests/'+r['id']).json()['status'] == 'await_verification'
    assert agent.step()
    final = tech.get('/requests/'+r['id']).json()
    assert final['status'] == 'configuration_with_warnings'
    assert all(c['status'] != 'failed' for c in final['verification']['checks'])
    assert final['verification']['checks'][-1]['status'] == 'not_performed'
    audit = tech.get('/requests/'+r['id']+'/audit').text
    assert 'approval_consumed' in audit
    assert settings.agent_token not in audit and settings.generator_token not in audit
    assert approve(tech,r).status_code == 409

def test_restart_at_approval(system,parameters):
    settings,app,tech,agent = system
    r = ready(system,parameters)
    restarted = create_app(settings)
    tech2 = TestClient(restarted,headers=tech.headers)
    agent.client = TestClient(restarted,headers=agent.client.headers)
    assert tech2.get('/requests/'+r['id']).json()['binding_hash'] == r['binding_hash']
    assert approve(tech2,r).status_code == 200
    agent.step()
    agent.step()
    assert tech2.get('/requests/'+r['id']).json()['status'] == 'configuration_with_warnings'

def test_auth_roles_and_binding(system,parameters):
    settings,app,tech,agent = system
    r = ready(system,parameters)
    assert agent.client.post('/requests',json={}).status_code == 401
    assert tech.get(agent.base+'/tasks').status_code == 401
    assert tech.post('/requests/'+r['id']+'/decision',json={'decision':'approve','binding_hash':'changed'}).status_code == 409
    assert tech.put('/requests/'+r['id']+'/parameters',json=parameters).status_code == 409
    assert tech.post('/requests/'+r['id']+'/decision',json={'approved':True}).status_code == 422

def test_reject(system,parameters):
    _,_,tech,agent = system
    r = ready(system,parameters)
    assert tech.post('/requests/'+r['id']+'/decision',json={'decision':'reject','binding_hash':r['binding_hash']}).json()['status'] == 'rejected'
    assert not agent.step()

def test_changed_router_blocks_write(system,parameters):
    _,_,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    agent.router.data['identity'] = 'different'
    agent.step()
    assert agent.router.calls == 0
    assert tech.get('/requests/'+r['id']).json()['status'] == 'intervention_required'

def test_lost_delivery_never_reissued(system,parameters):
    _,app,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    delivered = agent.client.get(agent.base+'/tasks').json()
    assert delivered['action'] == 'apply_approved_ecmp'
    assert agent.client.get(agent.base+'/tasks').json() is None
    app.state.service.clock = lambda: time.time()+200
    app.state.service.sweep()
    r = tech.get('/requests/'+r['id']).json()
    assert r['reason'] == 'execution_uncertain'
    assert agent.router.calls == 0

def test_approval_expiry(system,parameters):
    _,app,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    with app.state.service.store.transaction() as db:
        current = app.state.service.store.get(db,'request',r['id'])
        a = app.state.service.store.get(db,'approval',current['approval_id'])
        a['expires'] = 0
        app.state.service.store.put(db,'approval',a['id'],a)
    assert agent.client.get(agent.base+'/tasks').json() is None

def test_duplicate_result_and_conflict(system,parameters):
    _,_,tech,agent = system
    new_request(tech,agent,parameters)
    task = agent.client.get(agent.base+'/tasks').json()
    url = agent.base+'/tasks/'+task['id']+'/result'
    result = {'status':'ok','snapshot':agent.router.snapshot()}
    assert agent.client.post(url,json=result).json() == {'duplicate':False}
    assert agent.client.post(url,json=result).json() == {'duplicate':True}
    result['snapshot']['identity'] = 'changed'
    assert agent.client.post(url,json=result).status_code == 409

def test_missing_parameters_and_out_of_scope(system,parameters):
    _,_,tech,agent = system
    r = new_request(tech,agent,None)
    assert r['status'] == 'await_parameters'
    assert tech.put('/requests/'+r['id']+'/parameters',json=parameters).json()['status'] == 'await_precheck'

def test_uncertain_partial_write(system,parameters,monkeypatch):
    _,_,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    def partial(ops):
        agent.router.data['tables']['/ip/dns'] = [{'servers':'8.8.8.8'}]
        raise TimeoutError()
    monkeypatch.setattr(agent.router,'apply',partial)
    agent.step()
    r = tech.get('/requests/'+r['id']).json()
    assert r['status'] == 'intervention_required'
    assert r['execution_result']['status'] == 'uncertain'
    assert not agent.step()

def test_verification_failure(system,parameters):
    _,_,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    agent.step()
    agent.router.data['tables']['/ip/firewall/nat'].clear()
    agent.step()
    assert tech.get('/requests/'+r['id']).json()['status'] == 'configuration_failed'
