from unittest.mock import patch

import shaystack
from shaystack import Grid
from shaystack.ops import HaystackHttpRequest, Ref, VER_3_0
from shaystack.providers import ping


@patch.object(ping.Provider, 'watch_sub')
def test_watch_sub_with_zinc(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = Grid(version=VER_3_0,
                             metadata={"watchId": "0123456789ABCDEF", "lease": 1},
                             columns=["empty"])
    mock.return_value.append({})
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(
        metadata={"watchDis": "myWatch", "watchId": "myid", "lease": 1},
        columns=['id'])
    grid.append({"id": Ref("id1")})
    grid.append({"id": Ref("id2")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.watch_sub(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("myWatch", "myid", [Ref("id1"), Ref("id2")], 1)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None


@patch.object(ping.Provider, 'watch_sub')
def test_watch_sub_with_args(mock):
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = Grid(version=VER_3_0,
                             metadata={"watchId": "0123456789ABCDEF", "lease": 1},
                             columns=["empty"])
    mock.return_value.append({})
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = mime_type
    request.args["watchDis"] = "myWatch"
    request.args["watchId"] = "myid"
    request.args["lease"] = "1"
    ids = ["@id1", "@id2"]
    request.args["ids"] = str(ids)

    # WHEN
    response = shaystack.watch_sub(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("myWatch", "myid", [Ref("id1"), Ref("id2")], 1)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, shaystack.MODE_ZINC) is not None
