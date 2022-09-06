from typing import cast
from unittest.mock import patch

from shaystack.providers.url import Provider as URLProvider
from shaystack.providers import haystack_interface
from tests import _get_mock_s3, _get_mock_s3_updated_ontology


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_haystack_interface_get_singleton_provider_refresh_15(mock_s3, mock_get_url):
    haystack_interface.SINGLETON_PROVIDER = None
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    envs = {
        "HAYSTACK_PROVIDER": "shaystack.providers.url",
        "REFRESH": 15
    }
    assert haystack_interface.no_cache(envs) is False  # the caching is enabled
    with cast(haystack_interface, haystack_interface.get_singleton_provider(envs)) as provider0:
        mock_s3.return_value = _get_mock_s3()
        grid0 = provider0.read(0, None, None, None, None)

    # the provider0 is cached to be used for the next queries
    assert provider0 == haystack_interface.SINGLETON_PROVIDER
    assert haystack_interface.no_cache(envs) is False  # the caching is enabled
    assert haystack_interface.SINGLETON_PROVIDER is not None  # there is an already saved provider

    with cast(haystack_interface, haystack_interface.get_singleton_provider(envs)) as provider1:
        mock_s3.return_value = _get_mock_s3_updated_ontology()
        grid1 = provider1.read(0, None, None, None, None)

    # the provider0 is always cached inside SINGLETON_PROVIDER
    assert provider0 == provider1 == haystack_interface.SINGLETON_PROVIDER
    # assert len(grid0._row) == len(grid1._row)

@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_haystack_interface_get_singleton_provider_refresh_0(mock_s3, mock_get_url):
    haystack_interface.SINGLETON_PROVIDER = None
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    envs = {
        "HAYSTACK_PROVIDER": "shaystack.providers.url",
        "REFRESH": 0
    }
    assert haystack_interface.no_cache(envs) is True  # the caching is disabled
    assert haystack_interface.SINGLETON_PROVIDER is None  # no cached provider yet
    with cast(haystack_interface, haystack_interface.get_singleton_provider(envs)) as provider0:
        provider0.cache_clear()
        mock_s3.return_value = _get_mock_s3()
        grid0 = provider0.read(0, None, None, None, None)

    assert provider0 == haystack_interface.SINGLETON_PROVIDER
    assert haystack_interface.no_cache(envs) is True  # the caching is disabled
    assert haystack_interface.SINGLETON_PROVIDER is not None  # there is a cached provider

    with cast(haystack_interface, haystack_interface.get_singleton_provider(envs)) as provider1:
        mock_s3.return_value = _get_mock_s3_updated_ontology()
        grid1 = provider1.read(0, None, None, None, None)

    assert provider1 == haystack_interface.SINGLETON_PROVIDER
    assert provider0 != provider1
    assert len(grid0._row) == 2
    assert len(grid1._row) == 3
    assert len(grid0._row) != len(grid1._row)


def test_haystack_interface_no_cache():
    """
    test shaystack.providers.haystack_interface.no_cache when refresh = 0
    and when refresh = 15
    """
    env_0 = {
        "HAYSTACK_PROVIDER": "shaystack.providers.db",
        "REFRESH": 0
    }
    env_1 = {
        "HAYSTACK_PROVIDER": "shaystack.providers.db",
        "REFRESH": 15
    }

    assert haystack_interface.no_cache(env_0) is True
    assert haystack_interface.no_cache(env_1) is False

@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_last_with_refresh_zero(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """

    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with cast(URLProvider, haystack_interface.get_provider("shaystack.providers.url", {})) as provider:

        provider.cache_clear()
        provider._periodic_refresh = 0

        mock_s3.return_value = _get_mock_s3()
        result1 = provider.read(0, None, None, None, None)

        mock_s3.return_value = _get_mock_s3_updated_ontology()
        result2 = provider.read(0, None, None, None, None)

        assert len(result1._row) == 2
        assert len(result2._row) == 3
        assert len(result1._row) != len(result2._row)

@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_last_with_refresh__not_zero(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """

    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with cast(URLProvider, haystack_interface.get_provider("shaystack.providers.url", {})) as provider:

        provider.cache_clear()
        provider._periodic_refresh = 15

        mock_s3.return_value = _get_mock_s3()
        result1 = provider.read(0, None, None, None, None)

        mock_s3.return_value = _get_mock_s3_updated_ontology()
        result2 = provider.read(0, None, None, None, None)

        assert len(result1._row) == 2
        assert len(result2._row) == 2
        assert len(result1._row) == len(result2._row)
