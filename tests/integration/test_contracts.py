import copy
import json
import ssl
import subprocess
import httpx
import pytest
from pydantic import ValidationError
from shared.contracts import Parameters, digest, normalize, variant
from shared.ecmp import compile_script, validate_artifact, precheck
from agent.app.router import SimulatedRouter, NativeRouter, tls_wrapper
from server.app.services.ai import Interpreter
from tests.conftest import PHP, ROOT, TOKEN, new_request

@pytest.mark.parametrize('key,value', [('tipo','ECMPr'),('tipo','PCC'),('lineas',1),('lineas',13),('lineas',True),('vel1','25M'),('vel1','0M'),('vel1',[]),('gw1','8.8.8.8'),('gw1','192.168.255.1'),('gw1','192.168.01.1'),('ip1',1),('ip1',254),('ip1','2'),('lan','172.16.255.1'),('dhcp','on'),('arbitrary_script','/system/reset-configuration')])
def test_invalid_parameters(parameters,key,value):
    parameters[key] = value
    with pytest.raises(ValidationError):
        Parameters.model_validate(parameters)

@pytest.mark.parametrize('text',['PCC','ECMPr','Hotspot','ECMP y PCC','ECMP recursivo','diagnosticar Windows','impresora'])
def test_scope(system,text):
    settings,_,tech,agent = system
    assert Interpreter(settings).classify(text) == 'OUT_OF_SCOPE'
    response = tech.post('/requests',json={'text':text,'session_id':agent.session_id,
        'target':{'router_id':'router-1','identity':'lab-router','management_interface':'ether14'}})
    assert response.json()['status'] == 'out_of_scope'
    assert not agent.step()

@pytest.mark.parametrize('version,mode',[('7.20','real'),('6.49.18','real'),('6.49.17','simulated'),('unknown','simulated'),('8.0','real'),('7.20','simulated')])
def test_no_fake_certification(version,mode):
    with pytest.raises(ValueError):
        variant(version,mode)

def php_call(file,function,parameters):
    # Fixed developer-owned harness, no shell and no user script execution.
    program = 'require $argv[1]; $p=json_decode(stream_get_contents(STDIN),true); echo '+function+'($p);'
    return subprocess.run([PHP,'-r',program,str(file)],input=json.dumps(parameters),text=True,capture_output=True,check=True).stdout

@pytest.mark.parametrize('lines',[2,3,6,12])
@pytest.mark.parametrize('dhcp',[False,True])
def test_php_manual_regression(parameters,lines,dhcp):
    parameters.update(lineas=lines,dhcp=dhcp)
    for i in range(1,lines+1):
        parameters.update({f'vel{i}':'5M',f'gw{i}':f'192.168.{i}.1',f'ip{i}':2})
    before = php_call(ROOT/'tests/fixtures/ecmp-before.php','legacy_ecmp',parameters)
    after = php_call(ROOT/'php/sistema-generador/lib/ecmp-legacy.php','legacy_ecmp',parameters)
    assert before == after

def test_php_weighted_last_gateway_fix(parameters):
    text = php_call(ROOT/'php/sistema-generador/lib/ecmp-legacy.php','ecmp_text',parameters)
    assert 'gateway=192.168.1.1,192.168.2.1,192.168.2.1 check-gateway=ping' in text
    compile_script(normalize(text))

def test_php_auth_and_invalid_input(php_server,parameters):
    assert httpx.post(php_server,json={},trust_env=False).status_code == 401
    headers = {'Authorization':'Bearer '+TOKEN}
    assert httpx.get(php_server,headers=headers,trust_env=False).status_code == 405
    for change in ({'tipo':'PCC'},{'lineas':13},{'vel1':'5M;evil'},{'ip1':'2'},{'gw2':'192.168.1.254'}):
        p = parameters | change
        assert httpx.post(php_server,headers=headers,json={'parameters':p,'routeros_family':'v6'},trust_env=False).status_code == 422
    assert httpx.post(php_server,headers=headers,json={'parameters':parameters,'routeros_family':'v7'},trust_env=False).status_code == 422

def test_normalization_and_integrity(php_server,parameters):
    artifact = httpx.post(php_server,headers={'Authorization':'Bearer '+TOKEN},json={'parameters':parameters,'routeros_family':'v6'},trust_env=False).json()
    assert '<br>' not in artifact['script']
    assert artifact['script_hash'] == digest(normalize(artifact['script']))
    assert normalize('x  \r\n\r\ny\r\n') == 'x\n\ny\n'
    validate_artifact(artifact,parameters)
    artifact['script'] += 'bad\n'
    with pytest.raises(ValueError):
        validate_artifact(artifact,parameters)

@pytest.mark.parametrize('script',['/system/reset-configuration\n', '/ip/route\nremove [find]\n', '/ip/route\nadd gateway=$evil\n','/ip/route\nadd gateway=1.2.3.4;quit\n','/ip/dns\nset unknown=yes\n'])
def test_adapter_rejects_unknown_syntax(script):
    with pytest.raises(ValueError):
        compile_script(script)

def test_management_and_interfaces(parameters):
    router = SimulatedRouter()
    target = {'identity':'lab-router','management_interface':'ether1'}
    with pytest.raises(ValueError):
        precheck(router.snapshot(),target,parameters)
    target['management_interface'] = 'ether14'
    precheck(router.snapshot(),target,parameters)
    router.data['tables']['/interface/bridge/port'] = [{'interface':'ether1','bridge':'bridge'}]
    with pytest.raises(ValueError):
        precheck(router.snapshot(),target,parameters)

def test_native_tls_arguments_and_failure(monkeypatch):
    import librouteros
    observed = {}
    def reject(**kwargs):
        observed.update(kwargs)
        raise ssl.SSLCertVerificationError('certificate')
    monkeypatch.setattr(librouteros,'connect',reject)
    with pytest.raises(ssl.SSLCertVerificationError):
        NativeRouter('router.example','user','temporary',None)
    assert observed['port'] == 8729
    wrapper = observed['ssl_wrapper']
    assert wrapper.keywords['server_hostname'] == 'router.example'
    assert wrapper.func.__self__.verify_mode == ssl.CERT_REQUIRED
    assert wrapper.func.__self__.check_hostname is True

@pytest.mark.parametrize('exception,code',[(ssl.SSLCertVerificationError(),'tls'),(TimeoutError(),'timeout'),(ConnectionError(),'connection')])
def test_agent_read_errors(system,parameters,monkeypatch,exception,code):
    _,_,tech,agent = system
    r = new_request(tech,agent,parameters)
    task = agent.client.get(agent.base+'/tasks').json()
    def broken():
        raise exception
    monkeypatch.setattr(agent.router,'snapshot',broken)
    assert agent.execute(task) == {'status':'failed','error':code}

def test_action_allowlist(system):
    _,_,_,agent = system
    result = agent.execute({'action':'run_powershell','session_id':agent.session_id})
    assert result == {'status':'failed','error':'validation'}

def test_secrets_not_echoed(system):
    _,_,tech,_ = system
    result = tech.post('/requests',json={'password':'do-not-echo-me'})
    assert result.status_code == 422
    assert 'do-not-echo-me' not in result.text

def test_native_executor_gate_and_api_representation(monkeypatch):
    router = NativeRouter.__new__(NativeRouter)
    calls = []
    def fake_api(command,**args):
        calls.append((command,args))
        return [{'.id':'*A','default-name':'ether1'}] if command.endswith('/print') else []
    router.api = fake_api
    monkeypatch.setattr(router,'snapshot',lambda:{'version':'6.49.18'})
    operations = compile_script('/interface ethernet\nset [ find default-name=ether1 ] comment="Puerto 1" name=WAN1\n')
    with pytest.raises(ValueError):
        router.apply(operations)
    assert calls == []
    # Exercise conversion with a fake API only; this does not certify firmware.
    monkeypatch.setattr('agent.app.router.variant',lambda *_:'test-only')
    assert router.apply(operations) == 1
    assert calls[-1] == ('/interface/ethernet/set',{'comment':'Puerto 1','name':'WAN1','.id':'*A'})
