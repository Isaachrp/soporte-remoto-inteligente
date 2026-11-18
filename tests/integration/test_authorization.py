import copy
import time
from shared.contracts import digest
from tests.integration.test_flow import ready, approve

def test_claim_single_use(system,parameters):
    _,_,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    task = agent.client.get(agent.base+'/tasks').json()
    url = agent.base+'/tasks/'+task['id']+'/claim'
    assert agent.client.post(url,json=agent.router.snapshot()).status_code == 200
    assert agent.client.post(url,json=agent.router.snapshot()).status_code == 409

def test_mutated_representation_never_executes(system,parameters):
    _,_,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    task = agent.client.get(agent.base+'/tasks').json()
    task['payload']['executable']['operations'][0]['args']['name'] = 'CHANGED'
    assert agent.execute(task)['status'] == 'failed'
    assert agent.router.calls == 0

def test_changed_persisted_parameters_invalidates_approval(system,parameters):
    _,app,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    task = agent.client.get(agent.base+'/tasks').json()
    store = app.state.service.store
    with store.transaction() as db:
        row = store.get(db,'request',r['id'])
        row['target']['identity'] = 'changed'
        store.put(db,'request',r['id'],row)
    assert agent.client.post(agent.base+'/tasks/'+task['id']+'/claim',json=agent.router.snapshot()).status_code == 409

def test_rehashed_altered_script_cannot_use_original_approval(system,parameters):
    from shared.ecmp import validate_artifact
    _,_,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    task = agent.client.get(agent.base+'/tasks').json()
    artifact = task['payload']['artifact']
    artifact['script'] = artifact['script'].replace('servers=8.8.8.8,8.8.4.4','servers=1.1.1.1')
    artifact['script_hash'] = digest(artifact['script'])
    task['payload']['executable'] = validate_artifact(artifact,parameters)
    assert agent.execute(task)['status'] == 'failed'
    assert agent.router.calls == 0

def test_cross_session_result_forbidden(system,parameters):
    settings,_,tech,agent = system
    from tests.conftest import new_request
    new_request(tech,agent,parameters)
    task = agent.client.get(agent.base+'/tasks').json()
    other = tech.post('/agent/sessions',headers={'Authorization':'Bearer '+settings.agent_token},json={
        'agent_id':'agent-1','router_id':'router-1','version':'0.1.0','mode':'simulated'}).json()
    url = '/agent/sessions/'+other['session_id']+'/tasks/'+task['id']+'/result'
    assert tech.post(url,headers={'Authorization':'Bearer '+other['session_token']},json={'status':'ok','snapshot':agent.router.snapshot()}).status_code == 403

def test_reconciliation_is_read_only(system,parameters):
    _,app,tech,agent = system
    r = ready(system,parameters)
    approve(tech,r)
    task = agent.client.get(agent.base+'/tasks').json()
    store = app.state.service.store
    with store.transaction() as db:
        task['deadline'] = 0
        store.put(db,'task',task['id'],task)
    app.state.service.sweep()
    response = tech.post('/requests/'+r['id']+'/reconcile',json={'session_id':agent.session_id})
    assert response.status_code == 200
    assert response.json()['write_authorized'] is False
    agent.step()
    assert agent.router.calls == 0
    r = tech.get('/requests/'+r['id']).json()
    assert r['status'] == 'intervention_required'
    assert r['reason'] == 'reconciliation_observed_manual_review_required'
    assert 'verification' in r
