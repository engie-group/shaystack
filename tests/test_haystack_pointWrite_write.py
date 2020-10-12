from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, Ref, Grid, VER_3_0
from haystackapi.providers import ping
from hszinc import Quantity


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'point_write_write')
def test_pointWrite_write_with_zinc(mock) -> None:
    # GIVEN
    mock.return_value = Grid(version=VER_3_0, columns=["level", "levelDis", "val", "who"])
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', "level", "val", "who", "duration"])
    grid.append({"id": Ref("1234"),
                 "level": 1,
                 "val": 100.0,
                 "who": "PPR",
                 "duration": Quantity(1, "min")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.point_write(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), 1, 100, "PPR", Quantity(1, "min"), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None
