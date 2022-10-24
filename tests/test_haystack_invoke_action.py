from unittest.mock import patch

import shaystack
from shaystack import Ref
from shaystack.ops import HaystackHttpRequest
from shaystack.providers import ping


@patch.object(ping.Provider, 'invoke_action')
def test_invoke_action_with_zinc(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(metadata={'id': Ref('123'), 'action': 'doIt'},
                          columns={'key': {}, 'value': {}})
    grid.append({'param': 'value'})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.invoke_action(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("123"), "doIt", {})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None


@patch.object(ping.Provider, 'invoke_action')
def test_invoke_action_without_params_with_zinc(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(metadata={'id': Ref('123'), 'action': 'doIt'},
                          columns={'key': {}, 'value': {}})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.invoke_action(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("123"), "doIt", {})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None
