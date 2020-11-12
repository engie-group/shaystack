from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi.ops import HaystackHttpRequest
from haystackapi.providers import ping
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'nav')
def test_nav_with_zinc(mock):
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = hszinc.Grid(columns=['navId'])
    grid.append({"navId": "01235456789ABCDEF", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.nav(request, "dev")

    # THEN
    mock.assert_called_once_with("01235456789ABCDEF")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None
