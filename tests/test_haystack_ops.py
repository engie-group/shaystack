from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_ops_with_zinc() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = hszinc.Grid()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    # apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.ops(request,"dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    ops_grid: Grid = hszinc.parse(response.body, hszinc.MODE_ZINC)
    assert ops_grid[0]["name"] == "about"
    assert ops_grid[1]["name"] == "ops"
