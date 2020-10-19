from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, Ref
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_unsub')
def test_watch_unsub_with_zinc(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(metadata={"close": True,
                                 "watchId": "0123456789ABCDEF"},
                       columns=['id'])
    grid.append({"id": Ref("id1")})
    grid.append({"id": Ref("id2")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_unsub(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", [Ref("id1"), Ref("id2")], True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_unsub')
def test_watch_unsub_with_args(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = mime_type
    request.args["watchId"] = "0123456789ABCDEF"
    request.args["close"] = True
    ids = set(["@id1", "@id2"])
    request.args["ids"] = str(ids)

    # WHEN
    response = haystackapi.watch_unsub(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", set([Ref("id1"), Ref("id2")]), True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, hszinc.MODE_ZINC) is not None
