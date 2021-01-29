from unittest.mock import patch

import haystackapi
from haystackapi import Grid, MARKER
from haystackapi.ops import HaystackHttpRequest
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_poll')
def test_watch_poll_with_zinc(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = haystackapi.Grid(
        metadata={'watchId': "0123456789ABCDEF",
                  'refresh': MARKER
                  },
        columns=["empty"])
    grid.append({})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_poll(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_poll')
def test_watch_poll_with_args(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
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
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None
