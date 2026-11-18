import pytest
from agent.app.gui import collect
from agent.app.router import SimulatedRouter
from server.app.offline_contract import extract_snapshot


def test_complete_server_format_without_writes_or_secrets():
    router = SimulatedRouter()
    closed = []
    router.close = lambda: closed.append(True)
    report = collect('host', 'private-user', 'private-password', factory=lambda *args: router)
    assert extract_snapshot(report) == extract_snapshot(router.snapshot())
    assert router.calls == 0 and closed == [True]
    assert 'private-user' not in str(report) and 'private-password' not in str(report)


def test_failed_read_closes_connection():
    router = SimulatedRouter()
    closed = []
    router.close = lambda: closed.append(True)
    def fail():
        raise TimeoutError()
    router.snapshot = fail
    with pytest.raises(TimeoutError):
        collect('host', 'user', 'password', factory=lambda *args: router)
    assert closed == [True]


def test_plain_api_readonly_transport(monkeypatch):
    import librouteros
    from agent.app.gui import DiagnosticRouter
    calls = []
    monkeypatch.setattr(librouteros, 'connect', lambda **kwargs: calls.append(kwargs))
    router = DiagnosticRouter('192.168.88.1', 'reader', 'secret')
    assert calls == [dict(host='192.168.88.1', username='reader', password='secret', port=8728, timeout=5)]
    assert not hasattr(router, 'apply')
