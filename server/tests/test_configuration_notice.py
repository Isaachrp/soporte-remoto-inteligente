import pytest

from server.app.services.configuration_notice import configuration_notice
from server.app.services.discovery import recommend
from shared.v7 import expected_operations
from tests.integration.test_v7_flow import LabAPIDouble


@pytest.mark.parametrize('state', ['clean', 'routes', 'complete', 'disabled', 'misleading_comment'])
def test_existing_configuration_notice(state):
    device = LabAPIDouble()
    parameters = recommend(device.snapshot(), 'router-1', 'real', True)['parameters']
    for command, args in expected_operations(parameters):
        if state == 'clean' or (state == 'routes' and command != '/ip/route/add'):
            continue
        device.api(command, **args)
    if state == 'disabled':
        device.data['tables']['/ip/route'][-1]['disabled'] = 'true'
    if state == 'misleading_comment':
        device.data['tables']['/ip/route'][-1]['gateway'] = '192.168.99.1'
    snapshot = device.snapshot()
    notice = configuration_notice(snapshot, parameters)
    proposal = recommend(snapshot, 'router-1', 'real', True)
    if state == 'clean':
        assert notice is None
        assert proposal['available']
    else:
        assert not proposal['available']
        assert len(notice['actions']) == 3
        assert ('ya está hecha' in notice['title']) == (state == 'complete')
        assert ('parte' in notice['title']) == (state != 'complete')
