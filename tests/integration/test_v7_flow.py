"""Real PHP and HTTP workflow with a memory-only RouterOS API double.

These tests cannot connect to or certify a real RouterOS instance.
"""
import copy
import json
from fastapi.testclient import TestClient
import pytest

from agent.app.router import NativeRouter, SimulatedRouter
from agent.app.runner import Agent
from server.app.core.config import Settings
from server.app.main import create_app
from shared.contracts import CERTIFIED, V7_LAB_VARIANT, V7_LAB_VERSION, digest, variant
from shared.ecmp import compile_script, precheck, validate_artifact, verify
from shared.snapshot import Snapshot
from shared.v7 import ADDRESSES
from tests.conftest import TOKEN, ROOT


class LabAPIDouble(SimulatedRouter):
    mode = 'real'  # Exercises real-mode policy; transport is exclusively in memory.
    lab_enabled = True

    def __init__(self):
        super().__init__(version=V7_LAB_VERSION, interfaces=4)
        self.writes = []
        self.fail_after = None
        self.data['tables']['/ip/address'] = [
            {'interface': interface, 'address': address, 'disabled': 'false', 'dynamic': 'false'}
            for interface, address in ADDRESSES.items()
        ]
        self.data['tables']['/ip/route'] = [
            {'dst-address': address.rsplit('.', 1)[0] + '.0/24', 'gateway': interface,
             'active': 'true', 'dynamic': 'true', 'distance': '0', 'routing-table': 'main'}
            for interface, address in ADDRESSES.items()
        ]
        self.data['tables']['/routing/table'] = [{'name': 'main', 'fib': 'true'}]
        self.data['tables']['/ip/dhcp-client'] = [{'name': 'client1', 'interface': 'ether1', 'disabled': 'true'}]

    def api(self, command, **args):
        if self.fail_after is not None and len(self.writes) >= self.fail_after:
            raise RuntimeError('Injected write failure')
        self.writes.append(command)
        table = command.rsplit('/', 1)[0]
        row = dict(args)
        if 'disabled' in row:
            row['disabled'] = 'false' if row['disabled'] == 'no' else 'true'
        if table == '/ip/route':
            row.update(active='true', dynamic='false', ecmp='true')
        if 'lease-time' in row:
            row['lease-time'] = '08:00:00'
        self.data['tables'][table].append(row)
        return iter(())

    apply = NativeRouter.apply


@pytest.fixture
def lab_system(tmp_path, php_server, parameters):
    settings = Settings(str(tmp_path/'v7.sqlite3'), 'technician-'+'t'*40, 'agent-'+'a'*40,
                        TOKEN, php_server, mode='real', v7_lab_enabled=True)
    app = create_app(settings)
    tech = TestClient(app, headers={'Authorization': 'Bearer ' + settings.technician_token})
    device = LabAPIDouble()
    agent = Agent(TestClient(app), device, 'agent-1', 'router-1', settings.agent_token)
    agent.register()
    p = parameters | {'vel2': parameters['vel1']}
    yield settings, app, tech, agent, device, p
    agent.close()
    tech.close()


def create(lab):
    _, _, tech, agent, _, p = lab
    response = tech.post('/requests', json={'text': 'Configurar ECMP', 'session_id': agent.session_id,
        'target': {'router_id': 'router-1', 'identity': 'lab-router', 'management_interface': 'ether4'},
        'parameters': p})
    assert response.status_code == 201, response.text
    return response.json()


def ready(lab):
    _, _, tech, agent, device, _ = lab
    request = create(lab)
    assert agent.step()
    request = tech.get('/requests/' + request['id']).json()
    assert request['status'] == 'await_approval', request
    assert request['variant'] == V7_LAB_VARIANT
    assert not device.writes
    return request


def approve(lab, request):
    tech = lab[2]
    response = tech.post('/requests/' + request['id'] + '/decision', json={
        'decision': 'approve', 'binding_hash': request['binding_hash']})
    assert response.status_code == 200, response.text


def test_v7_approved_flow_and_real_api_normalization(lab_system):
    _, _, tech, agent, device, _ = lab_system
    request = ready(lab_system)
    assert agent.step() is False
    assert tech.get('/health').json()['real_write_enabled'] is True
    assert tech.get('/health').json()['ecmp_certified'] is False
    approve(lab_system, request)
    assert agent.step()
    assert len(device.writes) == 7
    assert agent.step()
    result = tech.get('/requests/' + request['id']).json()
    assert result['status'] == 'configuration_with_warnings', result
    assert not any(c['status'] == 'failed' for c in result['verification']['checks'])
    assert result['final_response']['analysis']['problem_resolved'] is False
    assert result['artifact']['certified'] is False
    assert not CERTIFIED
    assert not agent.step()
    assert len(device.writes) == 7
    assert sum(e['event'] == 'approval_consumed' for e in tech.get('/requests/' + request['id'] + '/audit').json()) == 1


@pytest.mark.parametrize('gate', ['server', 'agent'])
def test_v7_requires_both_opt_ins(lab_system, gate):
    settings, _, tech, agent, device, _ = lab_system
    request = ready(lab_system)
    approve(lab_system, request)
    if gate == 'server':
        settings.v7_lab_enabled = False
    else:
        device.lab_enabled = False
    assert agent.step()
    assert not device.writes
    assert tech.get('/requests/' + request['id']).json()['status'] == 'intervention_required'
    assert not any(e['event'] == 'approval_consumed' for e in tech.get('/requests/' + request['id'] + '/audit').json())


def test_v7_disabled_server_never_generates(lab_system):
    settings, app, tech, agent, device, _ = lab_system
    # Rebuild the graph to emulate starting with the opt-in disabled.
    settings.v7_lab_enabled = False
    from server.app.workflow import build_workflow
    from server.app.services.ai import Interpreter
    from server.app.services.generator import Generator
    app.state.service.graph = build_workflow(Interpreter(settings), Generator(settings))
    request = create(lab_system)
    agent.step()
    result = tech.get('/requests/' + request['id']).json()
    assert result['status'] == 'intervention_required'
    assert not result.get('artifact')
    assert not device.writes


def test_v7_partial_application_is_never_retried(lab_system):
    _, _, tech, agent, device, _ = lab_system
    request = ready(lab_system)
    approve(lab_system, request)
    device.fail_after = 2
    agent.step()
    result = tech.get('/requests/' + request['id']).json()
    assert result['status'] == 'intervention_required'
    assert result['execution_result']['status'] == 'uncertain'
    assert len(device.writes) == 2
    assert agent.step() is False


def test_v7_reject_does_not_write(lab_system):
    request = ready(lab_system)
    tech, agent, device = lab_system[2:5]
    assert tech.post('/requests/' + request['id'] + '/decision', json={
        'decision': 'reject', 'binding_hash': request['binding_hash']}).status_code == 200
    assert agent.step() is False
    assert not device.writes


def test_v7_drift_before_claim_rejects_approval(lab_system):
    request = ready(lab_system)
    approve(lab_system, request)
    _, _, tech, agent, device, _ = lab_system
    device.data['tables']['/ip/dhcp-client'][0]['disabled'] = 'false'
    agent.step()
    assert not device.writes
    assert not any(e['event'] == 'approval_consumed' for e in tech.get('/requests/' + request['id'] + '/audit').json())


@pytest.mark.parametrize('version,mode,flag', [
    (V7_LAB_VERSION, 'real', False), ('7.24.4 (stable)', 'real', True),
    (V7_LAB_VERSION, 'simulated', True), ('6.49.18', 'real', True),
])
def test_exact_lab_version_gate(version, mode, flag):
    with pytest.raises(ValueError):
        variant(version, mode, flag)


@pytest.mark.parametrize('table,row', [
    ('/ip/firewall/nat', {'chain': 'srcnat'}),
    ('/ip/firewall/filter', {'chain': 'forward', 'action': 'drop'}),
    ('/ip/firewall/mangle', {'chain': 'output'}),
    ('/ip/pool', {'name': 'collision'}),
    ('/ip/dhcp-server/network', {'address': '172.16.0.0/24'}),
    ('/ip/dhcp-server', {'name': 'collision'}),
    ('/interface/bridge/port', {'interface': 'ether3', 'bridge': 'bridge1'}),
    ('/routing/rule', {'action': 'lookup', 'table': 'other'}),
    ('/ip/route', {'dst-address': '0.0.0.0/0', 'gateway': '192.168.1.1'}),
    ('/ip/dhcp-client', {'interface': 'ether2', 'disabled': 'false'}),
])
def test_v7_precheck_rejects_conflicts(lab_system, table, row):
    device, p = lab_system[4:]
    baseline = device.snapshot()
    target = {'identity': 'lab-router', 'management_interface': 'ether4'}
    assert precheck(baseline, target, p, True) == digest(baseline)
    baseline['tables'][table].append(row)
    with pytest.raises(ValueError):
        precheck(baseline, target, p, True)


def test_v7_snapshot_requires_all_preflight_tables(lab_system):
    snapshot = lab_system[4].snapshot()
    del snapshot['tables']['/ip/firewall/filter']
    with pytest.raises(ValueError):
        Snapshot.model_validate(snapshot)


def test_v7_forged_commands_rejected_even_with_new_hash(lab_system):
    artifact = ready(lab_system)['artifact']
    artifact['script'] = artifact['script'].replace('gateway=192.168.1.1', 'gateway=192.168.9.1')
    artifact['script_hash'] = digest(artifact['script'])
    with pytest.raises(ValueError):
        validate_artifact(artifact, lab_system[5])


def test_v6_compiler_does_not_gain_v7_permissions():
    with pytest.raises(ValueError):
        compile_script('/ip route\nadd dst-address=0.0.0.0/0 gateway=192.168.1.1 routing-table=main\n')


def test_v7_existing_configuration_cannot_be_applied_twice(lab_system):
    request = ready(lab_system)
    approve(lab_system, request)
    _, _, tech, agent, device, p = lab_system
    agent.step()
    agent.step()
    request2 = create(lab_system)
    agent.step()
    result = tech.get('/requests/' + request2['id']).json()
    assert result['status'] == 'intervention_required'
    assert not result.get('artifact')
    assert len(device.writes) == 7
    operations = request['executable']['operations']
    snapshot = device.snapshot()
    snapshot['tables']['/ip/dhcp-server'][0]['disabled'] = 'true'
    assert verify(snapshot, operations)['outcome'] == 'configuration_failed'


def test_v7_native_api_limits_host_before_connecting():
    with pytest.raises(ValueError):
        NativeRouter('192.168.1.1', 'user', 'unused', None, lab_enabled=True)


def test_v7_native_snapshot_queries_preflight_and_normalizes_order():
    baseline = LabAPIDouble().snapshot()
    native = NativeRouter.__new__(NativeRouter)
    reads = []
    reverse = False
    def api(command, **args):
        reads.append(command)
        assert '.proplist' in args
        if command == '/system/identity/print':
            return [{'name': 'lab-router'}]
        if command == '/system/resource/print':
            return [{'version': V7_LAB_VERSION}]
        rows = baseline['tables'][command.removesuffix('/print')]
        # Mimic native API booleans rather than simulator strings.
        result = [{k: True if v == 'true' else False if v == 'false' else v for k, v in row.items()} for row in rows]
        return list(reversed(result)) if reverse else result
    native.api = api
    first = native.snapshot()
    reverse = True
    assert digest(native.snapshot()) == digest(first)
    assert '/routing/table/print' in reads
    assert '/ip/firewall/filter/print' in reads
    assert '/ip/dhcp-client/print' in reads
    assert first['tables']['/ip/dhcp-client'][0]['disabled'] == 'true'


def test_lab_launcher_help_does_not_connect_or_prompt():
    import subprocess
    import sys
    from tests.conftest import ROOT
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/lab_v7.py'), '--help'],
                            text=True, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert '--ca' in result.stdout
    assert 'Token temporal' not in result.stdout


def test_captured_routeros_precheck_reaches_approval_without_writes(lab_system):
    capture = json.loads((ROOT / 'tests/fixtures/v7-precheck-main-fib-flag.json').read_text(encoding='utf-8'))
    device = lab_system[4]
    device.data = copy.deepcopy(capture['snapshot'])
    assert device.data['tables']['/routing/table'] == [{'fib': '', 'name': 'main'}]
    assert precheck(device.snapshot(), capture['target'], capture['parameters'], True) == digest(device.snapshot())
    request = ready(lab_system)
    assert request['artifact']['schema'] == 'ecmp-v7-lab-execution/1'
    assert len(request['executable']['operations']) == 7
    assert not device.writes


@pytest.mark.parametrize('row', [
    {'name': 'main'}, {'name': 'main', 'fib': 'false'},
    {'name': 'main', 'fib': 'no'}, {'name': 'other', 'fib': ''},
])
def test_fib_switch_fix_still_rejects_missing_false_or_other_table(lab_system, row):
    device, p = lab_system[4:]
    snapshot = device.snapshot()
    snapshot['tables']['/routing/table'] = [row]
    with pytest.raises(ValueError):
        precheck(snapshot, {'identity': 'lab-router', 'management_interface': 'ether4'}, p, True)
