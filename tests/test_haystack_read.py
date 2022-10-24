from unittest.mock import patch

import shaystack
from shaystack import Grid, Ref
from shaystack.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
from shaystack.providers import ping


@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_filter(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(1, None, None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert not shaystack.parse(response.body, mime_type)


@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_filter(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["filter"] = "id==@me"
    request.args["limit"] = "1"

    # WHEN
    response = shaystack.read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(1, None, None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid: Grid = shaystack.parse(response.body, mime_type)
    assert not read_grid


@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_id(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id'])
    grid.append({"id": Ref("me")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(envs, request, "dev", ping.Provider(envs))

    # THEN
    ids = [Ref("me")]
    mock.assert_called_once_with(0, None, ids, '', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_id(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["id"] = Ref("me").name

    # WHEN
    response = shaystack.read(envs, request, "dev", ping.Provider(envs))

    # THEN
    ids = [Ref("me")]
    mock.assert_called_once_with(0, None, ids, '', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'read')
def test_read_with_zinc_and_select(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns={'filter': {}, "limit": {}, "select": {}})
    grid.append({"filter": "id==@me", "limit": 1, "select": "id,site"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(1, "id,site", None, 'id==@me', None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert not shaystack.parse(response.body, mime_type)


@patch.object(ping.Provider, 'read')
def test_read_with_arg_and_select(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args["filter"] = "id==@me"
    request.args["limit"] = "1"
    request.args["select"] = "id,site"

    # WHEN
    response = shaystack.read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(1, "id,site", None, "id==@me", None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    read_grid = shaystack.parse(response.body, mime_type)
    assert not read_grid
