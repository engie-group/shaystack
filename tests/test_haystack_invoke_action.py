from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, Ref
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'invoke_action')
def test_invoke_action_with_zinc(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(metadata={'id': Ref('123'), 'action': 'doIt'},
                       columns={'key': {}, 'value': {}})
    grid.append({'param': 'value'})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.invoke_action(request,"dev")

    # THEN
    mock.assert_called_once_with(Ref("123"), "doIt", {})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'invoke_action')
def test_invoke_action_without_params_with_zinc(mock):
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(metadata={'id': Ref('123'), 'action': 'doIt'},
                       columns={'key': {}, 'value': {}})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.invoke_action(request,"dev")

    # THEN
    mock.assert_called_once_with(Ref("123"), "doIt", {})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None
