"""Opt-in real TLS read. Passing does NOT certify a writable ECMP variant."""
import os
import pytest
from agent.app.router import NativeRouter

@pytest.mark.lab
@pytest.mark.skipif(os.getenv('ECMP_LAB_AUTHORIZED') != '1',reason='Requiere laboratorio autorizado explicitamente')
def test_real_api_ssl_readonly():
    router = NativeRouter(os.environ['ECMP_ROUTER_HOST'],os.environ['ECMP_LAB_USER'],
                          os.environ['ECMP_LAB_PASSWORD'],os.environ['ECMP_ROUTER_CA'])
    try:
        snapshot = router.snapshot()
        assert snapshot['identity'] == os.environ['ECMP_LAB_IDENTITY']
        assert snapshot['version'] == os.environ['ECMP_LAB_VERSION']
    finally:
        router.close()
