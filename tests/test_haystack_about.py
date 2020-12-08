from unittest.mock import patch

import haystackapi
from haystackapi import Grid
from haystackapi.ops import HaystackHttpRequest
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch('haystackapi.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'about')
def test_about_with_zinc(mock, no_cache) -> None:
    # GIVEN
    no_cache.return_value = True
    mock.return_value = ping.PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch('haystackapi.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'about')
def test_about_without_headers(mock, no_cache) -> None:
    # GIVEN
    no_cache.return_value = True
    mock.return_value = Grid(columns=["a"])
    mock.return_value.append({"a": 1})
    mime_type = haystackapi.MODE_CSV
    request = HaystackHttpRequest()

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch('haystackapi.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'about')
def test_about_with_multivalues_headers(mock, no_cache) -> None:
    # GIVEN
    no_cache.return_value = True
    mock.return_value = ping.PingGrid
    mime_type = haystackapi.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = "text/zinc, application/json"

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert haystackapi.parse(response.body, mime_type) is not None
