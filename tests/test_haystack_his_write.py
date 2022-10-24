from datetime import datetime
from unittest.mock import patch

import pytz

import shaystack
from shaystack import Ref, parse_hs_datetime_format, Grid, VER_3_0
from shaystack.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
from shaystack.providers import ping


@patch.object(ping.Provider, 'his_write')
def test_his_write_with_zinc(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_write(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(None, grid, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_write')
def test_his_write_with_args(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    time_serie = [
        (datetime(2020, 1, 1, tzinfo=pytz.utc).isoformat() + " UTC", 100),
        (datetime(2020, 1, 2, tzinfo=pytz.utc).isoformat() + " UTC", 200)]
    mock.return_value = ping._PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args['id'] = str(Ref("1234"))
    request.args['ts'] = str(time_serie)

    # WHEN
    response = shaystack.his_write(envs, request, "dev", ping.Provider(envs))

    # THEN
    result_ts = Grid(version=VER_3_0, columns=["date", "val"])
    result_ts.extend([{"date": parse_hs_datetime_format(d, pytz.UTC), "val": v} for d, v in time_serie])
    mock.assert_called_once_with(Ref("1234"), result_ts, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None
