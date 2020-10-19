from unittest.mock import patch

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest
from haystackapi.providers import ping
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'about')
def test_about_with_zinc(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'about')
def test_about_without_headers(mock) -> None:
    # GIVEN
    mock.return_value = Grid(columns=["a"])
    mock.return_value.append({"a": 1})
    mime_type = hszinc.MODE_CSV
    request = HaystackHttpRequest()

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'about')
def test_about_with_multivalues_headers(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = "text/zinc, application/json"

    # WHEN
    response = haystackapi.about(request, "dev")

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None
