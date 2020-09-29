from unittest.mock import patch

import haystackapi
from haystackapi import HaystackHttpRequest
import hszinc
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_about_with_zinc() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    about_grid: Grid = hszinc.parse(response.body, hszinc.MODE_ZINC)
    assert about_grid[0]["haystackVersion"] == '3.0'


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_about_without_headers() -> None:
    # GIVEN
    mime_type = hszinc.MODE_CSV
    request = HaystackHttpRequest()

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    about_grid: Grid = hszinc.parse(response.body, mime_type)
    assert about_grid[0]["haystackVersion"] == 3.0


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_about_with_multivalues_headers() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = hszinc.Grid()
    request.headers["Accept"] = "text/zinc, application/json"

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    about_grid: Grid = hszinc.parse(response.body, hszinc.MODE_ZINC)
    assert about_grid[0]["haystackVersion"] == '3.0'
