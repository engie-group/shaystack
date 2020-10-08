from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, Ref, DEFAULT_MIME_TYPE
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_hisRead_with_zinc() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid: Grid = hszinc.parse(response.body, mime_type)
    assert not len(read_grid)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_hisRead_with_args() -> None:
    # GIVEN
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args['id'] = str(Ref("1234"))

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid: Grid = hszinc.parse(response.body, mime_type)
    assert not len(read_grid)
