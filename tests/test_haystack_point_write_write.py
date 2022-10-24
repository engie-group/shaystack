from unittest.mock import patch

import shaystack
from shaystack import Quantity, Grid, VER_3_0, Ref
from shaystack.ops import HaystackHttpRequest
from shaystack.providers import ping


@patch.object(ping.Provider, 'point_write_write')
def test_point_write_write_with_zinc(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = Grid(version=VER_3_0, columns=["level", "levelDis", "val", "who"])
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', "level", "val", "who", "duration"])
    grid.append({"id": Ref("1234"),
                 "level": 1,
                 "val": 100.0,
                 "who": "PPR",
                 "duration": Quantity(1, "min")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.point_write(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("1234"), 1, 100, "PPR", Quantity(1, "min"), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None
