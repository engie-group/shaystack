from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, DEFAULT_MIME_TYPE
from haystackapi.providers import ping
from hszinc import Grid, Ref


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_filter(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    mock.assert_called_once_with(1, None, None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert not hszinc.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_filter(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["filter"] = "id==@me"
    request.args["limit"] = "1"

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    mock.assert_called_once_with(1, None, None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid: Grid = hszinc.parse(response.body, mime_type)
    assert not read_grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_id(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id'])
    grid.append({"id": Ref("me")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    ids = Grid(columns=["id"])
    ids.append({"id": Ref("me")})
    mock.assert_called_once_with(0, None, ids, None, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_id(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["id"] = Ref("me").name

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    ids = Grid(columns=["id"])
    ids.append({"id": Ref("me")})
    mock.assert_called_once_with(0, None, ids, None, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_select(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns={'filter': {}, "limit": {}, "select": {}})
    grid.append({"filter": "id==@me", "limit": 1, "select": "id,site"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    mock.assert_called_once_with(1, "id,site", None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert not hszinc.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_select(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["filter"] = "id==@me"
    request.args["limit"] = "1"
    request.args["select"] = "id,site"

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    mock.assert_called_once_with(1, "id,site", None, "id==@me", None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid = hszinc.parse(response.body, mime_type)
    assert not read_grid
