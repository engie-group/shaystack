from unittest.mock import patch

import shaystack
from shaystack import Grid
from shaystack.ops import HaystackHttpRequest
from shaystack.providers import ping


@patch('shaystack.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'about')
def test_about_with_zinc(mock, no_cache) -> None:
    # GIVEN
    """
    Args:
        mock:
        no_cache:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    no_cache.return_value = True
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type

    # WHEN
    response = shaystack.about(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch('shaystack.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'about')
def test_about_without_headers(mock, no_cache) -> None:
    # GIVEN
    """
    Args:
        mock:
        no_cache:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    no_cache.return_value = True
    mock.return_value = Grid(columns=["a"])
    mock.return_value.append({"a": 1})
    mime_type = shaystack.MODE_CSV
    request = HaystackHttpRequest()

    # WHEN
    response = shaystack.about(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch('shaystack.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'about')
def test_about_with_multivalues_headers(mock, no_cache) -> None:
    # GIVEN
    """
    Args:
        mock:
        no_cache:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    no_cache.return_value = True
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Accept"] = "text/zinc, application/json"

    # WHEN
    response = shaystack.about(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with("https://localhost/dev")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None
