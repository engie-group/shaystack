from unittest.mock import patch

import shaystack
from shaystack import Grid, MARKER
from shaystack.ops import HaystackHttpRequest
from shaystack.providers import ping


@patch.object(ping.Provider, 'watch_poll')
def test_watch_poll_with_zinc(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = shaystack.Grid(
        metadata={'watchId': "0123456789ABCDEF",
                  'refresh': MARKER
                  },
        columns=["empty"])
    grid.append({})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.watch_poll(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None


@patch.object(ping.Provider, 'watch_poll')
def test_watch_poll_with_args(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = mime_type
    request.args["watchId"] = "0123456789ABCDEF"
    request.args["refresh"] = "true"

    # WHEN
    response = shaystack.watch_poll(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None
