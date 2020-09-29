import base64
import gzip
import inspect
import json
from unittest.mock import patch

import pytest
from botocore.client import BaseClient

import haystackapi
import hszinc
from haystackapi import HaystackHttpRequest
from hszinc import Grid


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
def test_watchUnsub_with_zinc() -> None:
    # GIVEN
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid: Grid = hszinc.Grid(columns={'id': {}})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=hszinc.MODE_ZINC)

    # WHEN
    response = haystackapi.watch_unsub(request,"dev")

    # THEN
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    watchUnsub_grid = hszinc.parse(response.body, hszinc.MODE_ZINC)
    assert not len(watchUnsub_grid)

