from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_nav_with_zinc():
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = hszinc.Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.nav(request,"dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid: Grid = hszinc.parse(response.body, hszinc.MODE_ZINC)
    assert not len(read_grid)
