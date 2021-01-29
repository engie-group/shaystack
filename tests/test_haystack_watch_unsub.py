from unittest.mock import patch

import haystackapi
from haystackapi import Ref
from haystackapi.ops import HaystackHttpRequest
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_unsub')
def test_watch_unsub_with_zinc(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    grid = haystackapi.Grid(metadata={"close": True,
                                      "watchId": "0123456789ABCDEF"},
                            columns=['id'])
    grid.append({"id": Ref("id1")})
    grid.append({"id": Ref("id2")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_unsub(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", [Ref("id1"), Ref("id2")], True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'watch_unsub')
def test_watch_unsub_with_args(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = mime_type
    request.args["watchId"] = "0123456789ABCDEF"
    request.args["close"] = True
    ids = {"@id1", "@id2"}
    request.args["ids"] = str(ids)

    # WHEN
    response = haystackapi.watch_unsub(request, "dev")

    # THEN
    mock.assert_called_once_with("0123456789ABCDEF", {Ref("id1"), Ref("id2")}, True)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, haystackapi.MODE_ZINC) is not None
