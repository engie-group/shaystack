import copy
import datetime
import os
from typing import cast
from unittest.mock import patch

import pytz
from nose import SkipTest

from shaystack import Ref, Grid, VER_3_0
from shaystack.providers import get_provider
from shaystack.providers.db import Provider as DBProvider

# Set HAYSTACK_DB variable, before running the tests to validate with another database
# HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
HAYSTACK_DB = os.environ.get("HAYSTACK_DB", 'sqlite3:///:memory:#haystack')

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def skip(msg: str) -> None:
    raise SkipTest(msg)


def _get_grids():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col", "dis"])
    sample_grid.append({"id": Ref("id1"), "col": 1, "dis": "Dis 1"})
    sample_grid.append({"id": Ref("id2"), "col": 2, "dis": "Dis 2"})
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


def _populate_db(provider: DBProvider) -> None:
    provider.purge_db()
    for grid, version in _get_grids():
        provider.update_grid_in_db(grid, None, "", version)


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_create_db():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        provider.create_db()


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_import_grid_in_db():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        provider.create_db()
        grid = Grid(metadata={"dis": "hello"},
                    columns=[("id", {}), ("a", {"dis": "a"}), ("b", {"dis": "b"})])
        grid.append({"id": Ref("1"), "a": "a", "b": "b"})
        grid.append({"id": Ref("2"), "a": "c", "b": "d"})
        provider.update_grid_in_db(grid, None, "customer", FAKE_NOW)


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_update_grid_in_db():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        provider.purge_db()
        provider.create_db()
        left = Grid(columns={"id": {}, "a": {}, "b": {}, "c": {}})
        left.append({"id": Ref("id1"), "a": 1, "b": 2})
        left.append({"id": Ref("id2"), "a": 2, "b": 2})
        left.append({"id": Ref("id3"), "a": 3, "b": 2})
        left.append({"id": Ref("id4"), "a": 4, "b": 2})
        left.append({"id": Ref("old_id"), "a": 1, "b": 2})
        right = Grid(columns={"id": {}, "a": {}, "b": {}, "c": {}})
        right.append({"id": Ref("id1"), "a": 3, "c": 5})
        provider.update_grid_in_db(left, version=None, customer_id="customer", now=FAKE_NOW)
        NEXT_FAKE = FAKE_NOW + datetime.timedelta(minutes=1)
        provider.update_grid_in_db(right - left, version=None, customer_id="customer", now=NEXT_FAKE)
        grid = provider.read_grid_from_db("customer", None)
        assert len(grid) == 1
        grid = provider.read_grid_from_db("customer", FAKE_NOW)
        assert len(grid) == 5


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_ops():
    with get_provider("shaystack.providers.db") as provider:
        result = provider.ops()
        assert len(result) == 5


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_about():
    with get_provider("shaystack.providers.db") as provider:
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'SQLProvider'


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_last_without_filter():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "last"


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_without_filter():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_with_filter():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_with_filter2():
    try:
        # caplog.set_level(logging.DEBUG)
        with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
            _populate_db(provider)
            version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
            result = provider.read(0, "id,other", None, "id==@id1", version_2)
            assert "id" in result.column
            assert "other" in result.column
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_read_version_with_ids():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_version():
    with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
        _populate_db(provider)
        versions = provider.versions()
        assert len(versions) == 3


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_values_for_tag_id():
    try:
        with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
            _populate_db(provider)
            values = provider.values_for_tag("id")
            assert len(values) > 1
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_values_for_tag_col():
    try:
        with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
            _populate_db(provider)
            values = provider.values_for_tag("col")
            assert len(values) > 1
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
def test_values_for_tag_dis():
    try:
        with cast(DBProvider, get_provider("shaystack.providers.db")) as provider:
            _populate_db(provider)
            values = provider.values_for_tag("dis")
            assert values == ['Dis 1', 'Dis 2']
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")
