import pytest

from server.app.offline_runner import ClientRouter


def test_ecmp_delivery_uses_api_without_certificate(monkeypatch):
    import librouteros
    calls = []
    connection = object()
    def connect(**kwargs):
        calls.append(kwargs)
        return connection
    monkeypatch.setattr(librouteros, 'connect', connect)
    router = ClientRouter('10.255.255.1', 'technician', 'test-password')
    assert router.api is connection
    assert router.lab_enabled and router.mode == 'real'
    assert calls == [dict(host='10.255.255.1', username='technician', password='test-password', port=8728, timeout=5)]
    with pytest.raises(ValueError):
        ClientRouter('192.168.88.1', 'technician', 'test-password')
    assert len(calls) == 1
