from unittest.mock import patch

import haystackapi
from haystackapi.ops import HaystackHttpRequest
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'formats')
def test_formats_with_zinc(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    # apigw_event["body"] = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.formats(request, "dev")

    # THEN
    mock.assert_called_once_with()
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, mime_type) is not None
