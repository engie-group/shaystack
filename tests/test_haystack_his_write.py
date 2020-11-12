from datetime import datetime
from unittest.mock import patch

import pytz

import haystackapi
import hszinc
from haystackapi.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
from haystackapi.providers import ping
from hszinc import Ref, parse_date_format, Grid, VER_3_0


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_write')
def test_his_write_with_zinc(mock):
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_write(request, "dev")

    # THEN
    mock.assert_called_once_with(None, grid, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_write')
def test_his_write_with_args(mock):
    # GIVEN
    time_serie = [
        (datetime(2020, 1, 1, tzinfo=pytz.utc).isoformat() + " UTC", 100),
        (datetime(2020, 1, 2, tzinfo=pytz.utc).isoformat() + " UTC", 200)]
    mock.return_value = ping.PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args['id'] = str(Ref("1234"))
    request.args['ts'] = str(time_serie)

    # WHEN
    response = haystackapi.his_write(request, "dev")

    # THEN
    result_ts = Grid(version=VER_3_0, columns=["date", "val"])
    result_ts.extend([{"date": parse_date_format(d), "val": v} for d, v in time_serie])
    mock.assert_called_once_with(Ref("1234"), result_ts, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None
