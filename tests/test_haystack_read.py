from unittest.mock import patch

import haystackapi
from haystackapi import Grid, Ref
from haystackapi.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_filter(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    grid = haystackapi.Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    mock.assert_called_once_with(1, None, None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert not haystackapi.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_filter(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
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
    read_grid: Grid = haystackapi.parse(response.body, mime_type)
    assert not read_grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_id(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    grid = haystackapi.Grid(columns=['id'])
    grid.append({"id": Ref("me")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = haystackapi.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    ids = Grid(columns=["id"])
    ids.append({"id": Ref("me")})
    mock.assert_called_once_with(0, None, ids, '', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_id(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["id"] = Ref("me").name

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    ids = Grid(columns=["id"])
    ids.append({"id": Ref("me")})
    mock.assert_called_once_with(0, None, ids, '', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_select(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    grid = haystackapi.Grid(columns={'filter': {}, "limit": {}, "select": {}})
    grid.append({"filter": "id==@me", "limit": 1, "select": "id,site"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    mock.assert_called_once_with(1, "id,site", None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert not haystackapi.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_select(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    mock.return_value = ping._PingGrid
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
    read_grid = haystackapi.parse(response.body, mime_type)
    assert not read_grid
