import inspect
import json
from unittest.mock import patch

import pytest
from botocore.client import BaseClient

import hszinc
import haystackapi
from haystackapi import HaystackHttpRequest
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_formats_with_zinc():
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    # apigw_event["body"] = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.formats(request, "dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    format_grid: Grid = hszinc.parse(response.body, hszinc.MODE_ZINC)
    assert format_grid[0]["mime"] == hszinc.MODE_ZINC
    assert format_grid[0]["receive"] == hszinc.MARKER
    assert format_grid[0]["send"] == hszinc.MARKER
    assert format_grid[1]["mime"] == "application/json"
    assert format_grid[1]["receive"] == hszinc.MARKER
    assert format_grid[1]["send"] == hszinc.MARKER
