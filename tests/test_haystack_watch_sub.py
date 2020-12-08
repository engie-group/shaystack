from unittest.mock import patch

import haystackapi
from haystackapi import Grid
from haystackapi.ops import HaystackHttpRequest, Ref, VER_3_0
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_sub')
def test_watch_sub_with_zinc(mock):
    # GIVEN
    mock.return_value = Grid(version=VER_3_0,
                             metadata={"watchId": "0123456789ABCDEF", "lease": 1},
                             columns=["empty"])
    mock.return_value.append({})
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    grid = haystackapi.Grid(
        metadata={"watchDis": "myWatch", "watchId": "myid", "lease": 1},
        columns=['id'])
    grid.append({"id": Ref("id1")})
    grid.append({"id": Ref("id2")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_sub(request, "dev")

    # THEN
    mock.assert_called_once_with("myWatch", "myid", [Ref("id1"), Ref("id2")], 1)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_sub')
def test_watch_sub_with_args(mock):
    # GIVEN
    mock.return_value = Grid(version=VER_3_0,
                             metadata={"watchId": "0123456789ABCDEF", "lease": 1},
                             columns=["empty"])
    mock.return_value.append({})
    mime_type = haystackapi.MODE_ZINC
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
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None
