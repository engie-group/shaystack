import unittest
from datetime import datetime
from typing import cast
from unittest.mock import patch
from collections import OrderedDict
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
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        provider._periodic_refresh = 2
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

#THIS TEST
@patch.object(URLProvider, '_get_url')
def test_read_last_without_version_without_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        provider._periodic_refresh = 2
        result = provider.read(40, None, None, None, None)
        assert len(result) == 24


@patch.object(URLProvider, '_get_url')
def test_read_with_version_2021_without_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with get_provider("shaystack.providers.url", {}) as provider:

        version_2 = datetime(2021, 11, 2, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert len(result) == 3


@patch.object(URLProvider, '_get_url')
def test_read_with_version_2020_without_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with get_provider("shaystack.providers.url", {}) as provider:

        version_2 = datetime(2020, 11, 2, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert len(result) == 2


@patch.object(URLProvider, '_get_url')
def test_read_version_with_filter(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 11, 10, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@p_demo_r_23a44701-a89a6c66", version_2)
        assert len(result) == 1
        assert result[0]['id'] == Ref("@p_demo_r_23a44701-a89a6c66")


@patch.object(URLProvider, '_get_url')
def test_read_version_with_filter2(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2021, 11, 3, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, "id,dis", None, "id==@p_demo_r_23a44701-a89a6c66", version_2)
        # assert result.column.keys() == ["id", "dis"]
        assert list(result.keys()) == [Ref('p_demo_r_23a44701-a89a6c66', 'Carytown')]



@patch.object(URLProvider, '_get_url')
def test_read_version_with_ids(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with get_provider("shaystack.providers.url", {}) as provider:
        version_2 = datetime(2020, 11, 10, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("p_demo_r_23a44701-a89a6c66")], None, version_2)
        assert len(result) == 1
        assert result[0]['id'] == Ref("p_demo_r_23a44701-a89a6c66")


def test_unexistant_version():
    """
    Args:
    """
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
        provider.cache_clear()
        version_0 = datetime(2020, 8, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)
        url = "sample/carytown.zinc"
        result = provider._download_grid(url, version_0)
        assert len(result) == 0


@patch.object(URLProvider, '_get_url')
def test_version(mock_get_url):
    """
    Args:
        mock_get_url:
    """
    mock_get_url.return_value = "sample/carytown.hayson.json"
    with get_provider("shaystack.providers.url", {}) as provider:
        versions = provider.versions()
        assert len(versions) == 4


class ProviderTest(unittest.TestCase):
    @patch.object(URLProvider,"_refresh_versions")
    def test_given_wrong_url(self, mock_refresh_version):
        """
        Args:
            ProviderTest:
            mock_refresh_version:
        """
        mock_refresh_version.return_value = ''
        with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
            provider.cache_clear()
            provider._versions = {"wrongsheme://temp/url.zinc": \
                OrderedDict(
                    [(datetime(2021, 12, 8, 10, 55, 39, 50626), "wrongsheme://temp/url.zinc")]
                )
            }
            url = "wrongsheme://temp/url.zinc"
            with self.assertRaises(ValueError) as cm:
                provider._download_grid(url, None)
            self.assertEqual(cm.exception.args[0], "A wrong url ! (url have to be ['file','s3','']")