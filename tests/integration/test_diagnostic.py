import argparse
import json
import ssl

import pytest

from agent.app import diagnostic
from agent.app.router import SimulatedRouter


def test_report_is_readonly_and_does_not_certify():
    router = SimulatedRouter(interfaces=4)
    result = diagnostic.inspect_router(router, 'lab-router', '6.49.18', 'ether4')
    assert result['status'] == 'passed'
    assert result['ecmp_certified'] is False
    assert result['real_writes_enabled'] is False
    assert router.calls == 0
    assert '10.255.255.1' not in json.dumps(result)
    assert diagnostic.inspect_router(router, 'wrong-router', '6.49.18', 'ether4')['status'] == 'failed'
    assert diagnostic.inspect_router(router, 'lab-router', '7.1', 'ether4')['status'] == 'failed'
    assert diagnostic.inspect_router(router, 'lab-router', '6.49.18', 'ether3')['status'] == 'failed'


@pytest.mark.parametrize('failure', [None, ssl.SSLCertVerificationError('secret-value'), RuntimeError('secret-value')])
def test_diagnostic_credentials_cleanup_and_report(tmp_path, monkeypatch, failure):
    ca = tmp_path / 'ca.pem'
    ca.write_text('test')
    output = tmp_path / 'report.json'
    args = argparse.Namespace(host='router', ca=str(ca), report=str(output),
                              identity='lab-router', routeros_version='6.49.18', management='ether4')
    router = SimulatedRouter(interfaces=4)
    closed = []
    monkeypatch.setattr(router, 'close', lambda: closed.append(True))
    monkeypatch.setattr('builtins.input', lambda _: 'reader')
    monkeypatch.setattr(diagnostic.getpass, 'getpass', lambda _: 'secret-value')
    def connect(*values):
        assert values == ('router', 'reader', 'secret-value', str(ca))
        if failure:
            raise failure
        return router
    monkeypatch.setattr(diagnostic, 'NativeRouter', connect)
    assert diagnostic.run_diagnostic(args) == (1 if failure else 0)
    assert 'secret-value' not in output.read_text()
    assert closed == ([] if failure else [True])
    assert router.calls == 0
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        diagnostic.run_diagnostic(args)
    assert output.read_bytes() == before
