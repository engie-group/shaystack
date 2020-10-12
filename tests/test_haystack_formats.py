from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'formats')
def test_formats_with_zinc(mock):
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    # apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.formats(request, "dev")

    # THEN
    mock.assert_called_once_with()
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None
