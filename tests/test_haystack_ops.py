from unittest.mock import patch

import haystackapi
from haystackapi.ops import HaystackHttpRequest
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'ops')
def test_ops_with_zinc(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    # apigw_event["body"] = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.ops(request, "dev")

    # THEN
    mock.assert_called_once_with()
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None
