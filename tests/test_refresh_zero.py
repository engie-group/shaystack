from typing import cast
from unittest.mock import patch

from datetime import datetime

import pytz

from shaystack.dumper import dump
from shaystack.grid import Grid, VER_3_0
from shaystack.parser import MODE_ZINC
from shaystack import Ref
from shaystack.providers import get_provider
from shaystack.providers.url import Provider as URLProvider
from tests import _get_mock_s3, _get_mock_s3_updated_ontology


@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_read_last_with_refresh_zero(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """

    mock_get_url.return_value = "s3://bucket/grid.zinc"
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:

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
    with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:

        provider.cache_clear()
        provider._periodic_refresh = 15

        mock_s3.return_value = _get_mock_s3()
        result1 = provider.read(0, None, None, None, None)

        mock_s3.return_value = _get_mock_s3_updated_ontology()
        result2 = provider.read(0, None, None, None, None)

        assert len(result1._row) == 2
        assert len(result2._row) == 2
        assert len(result1._row) == len(result2._row)