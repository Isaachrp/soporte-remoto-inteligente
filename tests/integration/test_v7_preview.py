"""Offline draft checks with actual PHP; never certify or connect to firmware."""
import json
import subprocess
import sys

import pytest

from scripts.preview_v7 import generate_preview
from shared.contracts import digest, normalize, variant
from shared.ecmp import validate_artifact
from tests.conftest import PHP, ROOT


def test_preview_preserves_lab_and_keeps_dhcp_disabled():
    artifact = generate_preview(PHP)
    script = artifact['script']
    assert artifact['target_version'] == '7.24.5 (stable)'
    assert artifact['preflight_performed'] is False
    assert artifact['required_addresses']['ether4'] == '10.255.255.1/24'
    assert artifact['load_distribution'] == 'equal_cost'
    assert artifact['speed_values_used_for_weighting'] is False
    assert normalize(script) == script
    assert digest(script) == artifact['script_hash']
    commands = [line for line in script.splitlines() if line.startswith('add ')]
    assert len(commands) == 7
    routes = [line for line in commands if 'dst-address=0.0.0.0/0' in line]
    assert len(routes) == 2
    assert all('routing-table=main distance=1 check-gateway=ping' in line for line in routes)
    assert 'gateway=192.168.1.1 ' in routes[0]
    assert 'gateway=192.168.2.1 ' in routes[1]
    nat = [line for line in commands if 'chain=srcnat' in line]
    assert len(nat) == 2
    assert all('src-address=172.16.0.0/24' in line and 'action=masquerade' in line for line in nat)
    assert 'out-interface=ether1 ' in nat[0] and 'out-interface=ether2 ' in nat[1]
    assert 'ranges=172.16.0.50-172.16.0.250' in script
    assert 'interface=ether3 address-pool=ecmp7_lab_pool lease-time=8h disabled=yes' in script
    assert 'dns-server=1.1.1.1,8.8.8.8' in script
    for forbidden in ('/interface ethernet', '/ip address', '/ip dns', '/ip firewall mangle',
                      '/certificate', '/user', 'routing-mark=', 'broadcast=', 'remove ', 'set '):
        assert forbidden not in script
    with pytest.raises(ValueError):
        validate_artifact(artifact, artifact['parameters'])
    with pytest.raises(ValueError):
        variant('7.24.5 (stable)', 'real')


@pytest.mark.parametrize('change', [
    {'vel2': '10M'}, {'lineas': 3}, {'lan': '172.16.1.1'},
    {'gw1': '192.168.3.1'}, {'ip2': 3}, {'vel1': '5M;reset'},
])
def test_php_preview_rejects_other_topologies_and_weights(change):
    parameters = generate_preview(PHP)['parameters'] | change
    program = ('require $argv[1]; '
               'echo json_encode(ecmp_v7_lab_artifact(json_decode(stream_get_contents(STDIN),true)));')
    result = subprocess.run(
        [PHP, '-r', program, str(ROOT / 'php/sistema-generador/lib/ecmp-v7-lab.php')],
        input=json.dumps(parameters), text=True, capture_output=True, timeout=15,
    )
    assert result.returncode != 0


def test_php_preview_optional_dhcp():
    parameters = generate_preview(PHP)['parameters'] | {'dhcp': False}
    program = ('require $argv[1]; '
               'echo json_encode(ecmp_v7_lab_artifact(json_decode(stream_get_contents(STDIN),true)));')
    result = subprocess.run(
        [PHP, '-r', program, str(ROOT / 'php/sistema-generador/lib/ecmp-v7-lab.php')],
        input=json.dumps(parameters), text=True, capture_output=True, check=True, timeout=15,
    )
    artifact = json.loads(result.stdout)
    assert '/ip pool' not in artifact['script']
    assert '/ip dhcp-server' not in artifact['script']


def test_preview_cli_preserves_previous_evidence(tmp_path):
    output = tmp_path / 'preview'
    command = [sys.executable, str(ROOT / 'scripts/preview_v7.py'), '--php', PHP, '--output', str(output)]
    first = subprocess.run(command, text=True, capture_output=True, timeout=20)
    assert first.returncode == 0, first.stderr
    saved = (output / 'ecmp-v7-lab.rsc').read_bytes()
    artifact = json.loads((output / 'artefacto.json').read_text(encoding='utf-8'))
    assert saved == artifact['script'].encode('utf-8')
    assert (output / 'SHA256SUMS').read_text().startswith(digest(artifact['script']))
    second = subprocess.run(command, text=True, capture_output=True, timeout=20)
    assert second.returncode != 0
    assert (output / 'ecmp-v7-lab.rsc').read_bytes() == saved
