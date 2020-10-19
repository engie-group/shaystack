from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest
from haystackapi.providers import ping
from hszinc import Grid, MARKER


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_poll')
def test_watch_poll_with_zinc(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = hszinc.Grid(
        metadata={'watchId': "0123456789ABCDEF",
                  'refresh': MARKER
                  },
        columns=["empty"])
    grid.append({})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_poll(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_poll')
def test_watch_poll_with_args(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = mime_type
    request.args["watchId"] = "0123456789ABCDEF"
    request.args["refresh"] = True

    # WHEN
    response = haystackapi.watch_poll(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None
