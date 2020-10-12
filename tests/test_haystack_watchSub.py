from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, Ref, VER_3_0
from haystackapi.providers import ping
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_sub')
def test_watchSub_with_zinc(mock):
    # GIVEN
    mock.return_value = Grid(version=VER_3_0,
                             metadata={"watchId": "0123456789ABCDEF", "lease": 1},
                             columns=["empty"])
    mock.return_value.append({})
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(
        metadata={"watchDis": "myWatch", "watchId": "myid", "lease": 1},
        columns=['id'])
    grid.append({"id": Ref("id1")})
    grid.append({"id": Ref("id2")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_sub(request, "dev")

    # THEN
    mock.assert_called_once_with("myWatch", "myid", [Ref("id1"), Ref("id2")], 1)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_sub')
def test_watchSub_with_args(mock):
    # GIVEN
    mock.return_value = Grid(version=VER_3_0,
                             metadata={"watchId": "0123456789ABCDEF", "lease": 1},
                             columns=["empty"])
    mock.return_value.append({})
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = mime_type
    request.args["watchDis"] = "myWatch"
    request.args["watchId"] = "myid"
    request.args["lease"] = 1
    ids = ["@id1", "@id2"]
    request.args["ids"] = str(ids)

    # WHEN
    response = haystackapi.watch_sub(request, "dev")

    # THEN
    mock.assert_called_once_with("myWatch", "myid", [Ref("id1"), Ref("id2")], 1)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None
