from unittest.mock import patch

import shaystack
from shaystack import Grid
from shaystack.ops import HaystackHttpRequest
from shaystack.providers import ping


@patch.object(ping.Provider, 'nav')
def test_nav_with_zinc(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = shaystack.Grid(columns=['navId'])
    grid.append({"navId": "01235456789ABCDEF", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.nav(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(nav_id='01235456789ABCDEF')
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None
