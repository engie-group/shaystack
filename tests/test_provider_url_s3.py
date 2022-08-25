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
@patch.object(URLProvider, '_s3')
def test_values_for_tag(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """

    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        provider._periodic_refresh = 15
        mock_s3.return_value = _get_mock_s3()
        result1 = provider.read(0, None, None, None, None)
        print(result1)
        result = provider.values_for_tag("col")
        assert result == [1.0, 2.0]
        result = provider.values_for_tag("id")
        assert result == [Ref("id1"), Ref("id2")]


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_last_without_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "3"

@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_version_without_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.read(0, None, None, None, date_version=version_2)
        print(result.metadata)
        assert result.metadata["v"] == "3"


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_version_with_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "3"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_version_with_filter2(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.read(0, "id,other", None, "id==@id1", version_2)
        assert result.column == {"id": MetadataObject(), "other": MetadataObject()}


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_version_with_ids(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "3"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.object(URLProvider, '_s3')
def test_lru_version(mock):
    """
    Args:
        mock:
    """
    mock.return_value = _get_mock_s3()
    last = None
    url = "s3://bucket/grid.zinc"

    with cast(URLProvider, get_provider("shaystack.providers.url", {"REFRESH": 1})) as provider:
        assert provider._download_grid(url, last).metadata["v"] == "3"



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
        print(versions)
        assert len(versions) == 3
