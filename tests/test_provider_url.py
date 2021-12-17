from datetime import datetime
from typing import cast
from unittest.mock import patch

import pytz

from shaystack import MetadataObject
from shaystack import Ref
from shaystack.providers import get_provider
from shaystack.providers.url import Provider as URLProvider
from tests import _get_mock_s3


@patch.object(URLProvider, '_get_url')
def test_values_for_tag(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:

        result = provider.values_for_tag("id")
        assert len(result) == 24


def test_ops():
    provider = get_provider("shaystack.providers.url", {})
    result = provider.ops()
    assert len(result) == 5


@patch.object(URLProvider, '_get_url')
def test_about(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'URLProvider'


@patch.object(URLProvider, '_get_url')
def test_read_last_without_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.zinc"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        result = provider.read(40, None, None, None, None)
        assert len(result) == 24


@patch.object(URLProvider, '_get_url')
def test_read_version_without_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert len(result) == 5


@patch.object(URLProvider, '_get_url')
def test_read_version_with_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@p_demo_r_23a44701-a89a6c66", version_2)
        assert len(result) == 1
        assert result[0]['id'] == Ref("@p_demo_r_23a44701-a89a6c66")


@patch.object(URLProvider, '_get_url')
def test_read_version_with_filter2(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, "id,dis", None, "id==@p_demo_r_23a44701-a89a6c66", version_2)
        # assert result.column.keys() == ["id", "dis"]
        assert list(result.keys()) == [Ref('p_demo_r_23a44701-a89a6c66', 'Carytown')]



@patch.object(URLProvider, '_get_url')

def test_read_version_with_ids(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("p_demo_r_23a44701-a89a6c66")], None, version_2)
        assert len(result) == 1
        assert result[0]['id'] == Ref("p_demo_r_23a44701-a89a6c66")


@patch.object(URLProvider, '_s3')
def test_lru_version(mock):
    """
    Args:
        mock:
    """
    mock.return_value = _get_mock_s3()
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        version_3 = datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        version_1 = datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
        version_0 = datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)

        last = None
        url = "s3://bucket/grid.zinc"
        assert provider._download_grid(url, last).metadata["v"] == "3"
        assert provider._download_grid(url, version_3).metadata["v"] == "3"
        assert provider._download_grid(url, version_2).metadata["v"] == "2"
        assert provider._download_grid(url, version_1).metadata["v"] == "1"
        result = provider._download_grid(url, version_0)
        assert len(result) == 0


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_version(mock, mock_get_url):
    """
    Args:
        mock:
        mock_get_url:
    """
    mock.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        versions = provider.versions()
        assert len(versions) == 3
