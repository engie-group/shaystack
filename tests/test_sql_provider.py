import copy
import datetime
import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytz
from pytest import skip

from haystackapi.providers import get_provider
from hszinc import Ref, Grid, VER_3_0

# Set HAYSTACK_DB variable, before running the tests to validate with another database
# HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
HAYSTACK_DB = os.environ.get("HAYSTACK_DB", 'sqlite3:///:memory:#haystack')

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def _get_grids():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col"])
    sample_grid.append({"id": Ref("id1"), "col": 1})
    sample_grid.append({"id": Ref("id2"), "col": 2})
    version_1 = datetime.datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
    version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
    version_3 = datetime.datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)
    g1 = copy.deepcopy(sample_grid)
    g1.metadata = {"v": "1"}
    g2 = copy.deepcopy(sample_grid)
    g2.metadata = {"v": "2"}
    g2[0]["col"] += 2
    g2[1]["col"] += 2
    g3 = copy.deepcopy(sample_grid)
    g3.metadata = {"v": "last"}
    g3[0]["col"] += 4
    g3[1]["col"] += 4

    return [
        (g1, version_1),
        (g2, version_2),
        (g3, version_3),
    ]


def _populate_db(provider):
    provider.purge_db()
    for grid, version in _get_grids():
        provider.import_diff_grid_in_db(grid, "", None, version)


def setup_function(fun):
    # Remove database
    Path("tests/test.db").unlink(missing_ok=True)


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_create_db():
    with get_provider("haystackapi.providers.sql") as provider:
        provider.create_db()


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_import_grid_in_db():
    with get_provider("haystackapi.providers.sql") as provider:
        provider.create_db()
        grid = Grid(metadata={"dis": "hello"},
                    columns=[("id", {}), ("a", {"dis": "a"}), ("b", {"dis": "b"})])
        grid.append({"id": Ref("1"), "a": "a", "b": "b"})
        grid.append({"id": Ref("2"), "a": "c", "b": "d"})
        provider.import_diff_grid_in_db(grid, "customer", None, FAKE_NOW)


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_import_diff_grid_in_db():
    with get_provider("haystackapi.providers.sql") as provider:
        provider.create_db()
        provider.purge_db()
        left = Grid(columns={"id": {}, "a": {}, "b": {}, "c": {}})
        left.append({"id": Ref("id1"), "a": 1, "b": 2})
        left.append({"id": Ref("id2"), "a": 2, "b": 2})
        left.append({"id": Ref("id3"), "a": 3, "b": 2})
        left.append({"id": Ref("id4"), "a": 4, "b": 2})
        left.append({"id": Ref("old_id"), "a": 1, "b": 2})
        right = Grid(columns={"id": {}, "a": {}, "b": {}, "c": {}})
        right.append({"id": Ref("id1"), "a": 3, "c": 5})
        provider.import_diff_grid_in_db(left, "customer", None, FAKE_NOW)
        NEXT_FAKE = FAKE_NOW + datetime.timedelta(minutes=1)
        provider.import_diff_grid_in_db(right - left, "customer", None, NEXT_FAKE)
        grid = provider.export_grid_from_db("customer", None)
        assert len(grid) == 1
        grid = provider.export_grid_from_db("customer", FAKE_NOW)
        assert len(grid) == 5


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_ops():
    with get_provider("haystackapi.providers.sql") as provider:
        result = provider.ops()
        assert len(result) == 5


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_about():
    with get_provider("haystackapi.providers.sql") as provider:
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'SQLProvider'


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_last_without_filter():
    with get_provider("haystackapi.providers.sql") as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "last"


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_without_filter():
    with get_provider("haystackapi.providers.sql") as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_with_filter():
    with get_provider("haystackapi.providers.sql") as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_with_filter(caplog):
    try:
        caplog.set_level(logging.DEBUG)
        with get_provider("haystackapi.providers.sql") as provider:
            _populate_db(provider)
            version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
            result = provider.read(0, "id,other", None, "id==@id1", version_2)
            assert "id" in result.column
            assert "other" in result.column
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_with_ids():
    with get_provider("haystackapi.providers.sql") as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_version():
    with get_provider("haystackapi.providers.sql") as provider:
        _populate_db(provider)
        versions = provider.versions()
        assert len(versions) == 3


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_values_for_tag():
    try:
        with get_provider("haystackapi.providers.sql") as provider:
            _populate_db(provider)
            values = provider.values_for_tag("id")
            assert len(values) > 1
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")
