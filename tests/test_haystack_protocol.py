from unittest.mock import patch

import shaystack
from shaystack import Grid, Ref
from shaystack.ops import HaystackHttpRequest
from shaystack.providers.haystack_interface import HttpError


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
@patch('shaystack.providers.haystack_interface.no_cache')
def test_negociation_with_zinc(no_cache) -> None:
    # GIVEN
    """
    Args:
        no_cache:
    """
    no_cache.return_value = True
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    shaystack.parse(response.body, shaystack.MODE_ZINC)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
@patch('shaystack.providers.haystack_interface.no_cache')
def test_negociation_with_json(no_cache) -> None:
    # GIVEN
    """
    Args:
        no_cache:
    """
    no_cache.return_value = True
    mime_type = shaystack.MODE_JSON
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    shaystack.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_zinc_without_content_type() -> None:
    # GIVEN
    mime_type = shaystack.MODE_CSV
    request = HaystackHttpRequest()
    grid = Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    del request.headers["Content-Type"]
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    shaystack.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_json_without_content_type() -> None:
    # GIVEN
    mime_type = shaystack.MODE_JSON
    request = HaystackHttpRequest()
    grid: Grid = Grid(columns={'id': {}})
    request.headers["Accept"] = mime_type
    del request.headers["Content-Type"]
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    shaystack.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_json_with_unknown_content_type() -> None:
    # GIVEN
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = Grid(columns={'id': {}})
    request.headers["Accept"] = mime_type
    request.headers["Content-Type"] = "text/html"
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 406
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid: Grid = shaystack.parse(response.body, mime_type)
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_without_accept() -> None:
    # GIVEN
    mime_type = shaystack.MODE_CSV
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    del request.headers["Accept"]
    request.headers["Content-Type"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    try:
        shaystack.read(request, "dev")
        assert False, "Must generate exception"
    except HttpError as ex:
        assert ex.error == 406


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_with_invalide_accept() -> None:
    # GIVEN
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = Grid(columns={'id': {}})
    request.headers["Accept"] = "text/html"
    request.headers["Content-Type"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 406
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid = shaystack.parse(response.body, mime_type)
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_with_navigator_accept() -> None:
    # GIVEN
    mime_type = shaystack.MODE_CSV
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers[
        "Accept"] = "Accept:text/html,application/xhtml+xml," \
                    "application/xml;q=0.9," \
                    "image/webp,image/apng," \
                    "*/*;q=0.8," \
                    "application/signed-exchange;v=b3;q=0.9"
    request.headers["Content-Type"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    shaystack.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_with_complex_accept() -> None:
    # GIVEN
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers["Accept"] = "text/json;q=0.9,text/zinc;q=1"
    request.headers["Content-Type"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'})
def test_negociation_with_zinc_to_json() -> None:
    # GIVEN
    mime_type = shaystack.MODE_JSON
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers["Accept"] = mime_type
    request.headers["Content-Type"] = shaystack.MODE_ZINC
    request.body = shaystack.dump(grid, mode=shaystack.MODE_ZINC)

    # WHEN
    response = shaystack.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    shaystack.parse(response.body, mime_type)
