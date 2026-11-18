import socket
import pytest
from server.run_central import select_port


def test_busy_explicit_port_has_actionable_error():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        sock.listen()
        with pytest.raises(ValueError, match='--port 0'):
            select_port(sock.getsockname()[1])


def test_automatic_port_is_available():
    port = select_port(0)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', port))


def test_default_falls_back_when_busy(monkeypatch):
    import server.run_central as launcher
    real_socket = socket.socket
    class BusyPreferred:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def bind(self, address):
            assert address == ('127.0.0.1', 8000)
            raise OSError('busy')
    monkeypatch.setattr(launcher.socket, 'socket', BusyPreferred)
    monkeypatch.setattr(launcher, 'free_port', lambda: 12345)
    assert launcher.select_port(None) == 12345
