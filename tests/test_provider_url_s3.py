from datetime import datetime
from typing import cast
from unittest.mock import patch

import pytz

from shaystack import MetadataObject
from shaystack import Ref
from shaystack.providers import get_provider
from shaystack.providers import haystack_interface
from shaystack.providers.url import Provider as URLProvider
from tests import _get_mock_s3_updated_ontology


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_values_for_tag(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """

    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        provider._periodic_refresh = 15
        mock_s3.return_value = _get_mock_s3_updated_ontology()
        result = provider.values_for_tag("col")
        assert result == [1.0, 2.0, 3.0]
        result = provider.values_for_tag("id")
        assert result == [Ref("id1"), Ref("id2"), Ref("id3")]


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_last_without_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        result = provider.read(0, None, None, None, None)
        print(result)
        assert result.metadata["v"] == "3"


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_version_without_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=None)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_version_with_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2"
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
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
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
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.object(URLProvider, '_s3')
def test_lru_version(mock_s3):
    """
    Args:
        mock:
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    last = None
    url = "s3://bucket/updated_grid.zinc"

    with cast(URLProvider, get_provider("shaystack.providers.url", {"REFRESH": 1})) as provider:
        result = provider._download_grid(url, last)
        assert result.metadata["v"] == "3"


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_version(mock_s3, mock_get_url):
    """
    Args:
        mock:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with get_provider("shaystack.providers.url", {}) as provider:
        versions = provider.versions()
        assert len(versions) == 3


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_his_read_with_version_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with cast(URLProvider, haystack_interface.get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        provider._periodic_refresh = 0
        version = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.his_read(entity_id=Ref("id1"),
                                   date_version=version,
                                   date_range=(
                                       datetime.min.replace(tzinfo=pytz.UTC),
                                       datetime.max.replace(tzinfo=pytz.UTC)
                                   ))
        assert (len(result._row)) == 4  # 5 out of 6 since getting all TSs < 2020-10-01T16:30:00
        assert result._row[3] == {'ts': datetime(2020, 10, 1, 0, 0, tzinfo=pytz.UTC), 'val': 20.0}


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_his_read_with_version_with_dateRangemock(mock_s3, mock_get_url):
    """
    Args:
        mock_s3
        mock_get_url
    """
    mock_s3.return_value = _get_mock_s3_updated_ontology()
    mock_get_url.return_value = "s3://bucket/updated_grid.zinc"
    with cast(URLProvider, haystack_interface.get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        provider._periodic_refresh = 0
        version = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=None)
        result = provider.his_read(entity_id=Ref("id1"),
                                   date_version=version,
                                   date_range=(
                                       datetime(2020, 8, 1, 16, 30, 0, 0, tzinfo=pytz.UTC),
                                       datetime(2020, 10, 1, 16, 30, 0, 0, tzinfo=pytz.UTC)
                                   ))
        assert (len(result._row)) == 2  # 2 out of 6 since getting all TSs < 2020-08-01T00:00:02
        #  also between 2020-09-01T16:30:00 and 2020-10-01T16:30:00
        assert result._row[1] == {'ts': datetime(2020, 10, 1, 0, 0, tzinfo=pytz.UTC), 'val': 20.0}
