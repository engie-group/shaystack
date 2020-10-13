from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest, Ref
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_with_zinc() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, "limit": {}})
    grid.append({"filter": "id==@me", "limit": 1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response.body, hszinc.MODE_ZINC)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_with_json() -> None:
    # GIVEN
    mime_type = hszinc.MODE_JSON
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_zinc_without_content_type() -> None:
    # GIVEN
    mime_type = hszinc.MODE_CSV
    request = HaystackHttpRequest()
    grid = Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    del request.headers["Content-Type"]
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    grid: Grid = hszinc.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_json_without_content_type() -> None:
    # GIVEN
    mime_type = hszinc.MODE_JSON
    request = HaystackHttpRequest()
    grid: Grid = Grid(columns={'id': {}})
    request.headers["Accept"] = mime_type
    request.headers["Content-Type"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid: Grid = hszinc.parse(response.body, mime_type)
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_json_with_unknown_content_type() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = Grid(columns={'id': {}})
    request.headers["Accept"] = mime_type
    request.headers["Content-Type"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid: Grid = hszinc.parse(response.body, mime_type)
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_without_accept() -> None:
    # GIVEN
    mime_type = hszinc.MODE_CSV
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    del request.headers["Accept"]
    request.headers["Content-Type"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)  # Default value


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_with_invalide_accept() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = Grid(columns={'id': {}})
    request.headers["Accept"] = "text/html"
    request.headers["Content-Type"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 400
    assert response.headers["Content-Type"].startswith(mime_type)
    error_grid = hszinc.parse(response.body, mime_type)
    assert "err" in error_grid.metadata


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_with_navigator_accept() -> None:
    # GIVEN
    mime_type = hszinc.MODE_CSV
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers[
        "Accept"] = "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    request.headers["Content-Type"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response.body, mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_with_complex_accept() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers["Accept"] = "text/json;q=0.9,text/zinc;q=1"
    request.headers["Content-Type"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_negociation_with_zinc_to_json() -> None:
    # GIVEN
    mime_type = hszinc.MODE_JSON
    request = HaystackHttpRequest()
    grid = Grid(columns={'filter': {}, 'limit': {}})
    grid.append({'filter': '', 'limit': -1})
    request.headers["Accept"] = mime_type
    request.headers["Content-Type"] = hszinc.MODE_ZINC
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.read(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    hszinc.parse(response.body, mime_type)
