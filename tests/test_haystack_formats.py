from unittest.mock import patch

import shaystack
from shaystack.ops import HaystackHttpRequest
from shaystack.providers import ping


@patch.object(ping.Provider, 'formats')
def test_formats_with_zinc(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    # apigw_event["body"] = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.formats(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with()
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None
