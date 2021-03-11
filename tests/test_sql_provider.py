import datetime
from typing import cast

import pytz
from nose import SkipTest

from shaystack import Ref, Grid
from shaystack.providers import get_provider
from shaystack.providers.sql import Provider as SQLProvider

# Set HAYSTACK_DB variable, before running the tests to validate with another database
# HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
HAYSTACK_DB = 'sqlite3:///:memory:#haystack'

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def skip(msg: str) -> None:
    raise SkipTest(msg)



def test_create_db():
    envs = {'HAYSTACK_DB': HAYSTACK_DB}
    with cast(SQLProvider, get_provider("shaystack.providers.sql", envs)) as provider:
        provider.create_db()


def test_update_grid():
    envs = {'HAYSTACK_DB': HAYSTACK_DB}
    with cast(SQLProvider, get_provider("shaystack.providers.sql", envs)) as provider:
        provider.purge_db()
        provider.create_db()
        grid = Grid(metadata={"dis": "hello"},
                    columns=[("id", {}), ("a", {"dis": "a"}), ("b", {"dis": "b"})])
        grid.append({"id": Ref("1"), "a": "a", "b": "b"})
        grid.append({"id": Ref("2"), "a": "c", "b": "d"})
        provider.update_grid(grid, None, "customer", FAKE_NOW)


def test_update_grid_in_db():
    with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                        {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
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
        provider.update_grid(left, version=None, customer_id="customer", now=FAKE_NOW)
        NEXT_FAKE = FAKE_NOW + datetime.timedelta(minutes=1)
        provider.update_grid(right - left, version=None, customer_id="customer", now=NEXT_FAKE)
        grid = provider.read_grid("customer", None)
        assert len(grid) == 1
        grid = provider.read_grid("customer", FAKE_NOW)
        assert len(grid) == 5


def test_ops():
    envs = {'HAYSTACK_DB': HAYSTACK_DB}
    with get_provider("shaystack.providers.sql", envs) as provider:
        result = provider.ops()
        assert len(result) == 5


def test_about():
    with get_provider("shaystack.providers.sql",
                      {'HAYSTACK_DB': HAYSTACK_DB}) as provider:
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'SQLProvider'


def test_read_last_without_filter():
    with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                        {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "last"
        assert len(result) == 2
        assert result[0] == {"id": Ref('id1'), 'col': 5, 'dis': 'Dis 1'}
        assert result[1] == {"id": Ref('id2'), 'col': 6, 'dis': 'Dis 2'}


def test_read_version_without_filter():
    with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                        {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 2
        assert result[0] == {"id": Ref('id1'), 'col': 3, 'dis': 'Dis 1'}
        assert result[1] == {"id": Ref('id2'), 'col': 4, 'dis': 'Dis 2'}


def test_read_version_with_filter():
    with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                        {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0] == {"id": Ref('id1'), 'col': 3, 'dis': 'Dis 1'}


def test_read_version_with_filter_and_select():
    try:
        # caplog.set_level(logging.DEBUG)
        with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                            {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
            _populate_db(provider)
            version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
            result = provider.read(0, "id,other", None, "id==@id1", version_2)
            assert len(result) == 1
            assert len(result.column) == 2
            assert "id" in result.column
            assert "other" in result.column
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


def test_read_version_with_ids():
    with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                        {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0] == {"id": Ref('id1'), 'col': 3, 'dis': 'Dis 1'}


def test_version():
    with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                        {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
        _populate_db(provider)
        versions = provider.versions()
        assert len(versions) == 3


def test_values_for_tag_id():
    try:
        with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                            {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
            _populate_db(provider)
            values = provider.values_for_tag("id")
            assert len(values) > 1
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


def test_values_for_tag_col():
    try:
        with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                            {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
            _populate_db(provider)
            values = provider.values_for_tag("col")
            assert len(values) > 1
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")


def test_values_for_tag_dis():
    try:
        with cast(SQLProvider, get_provider("shaystack.providers.sql",
                                            {'HAYSTACK_DB': HAYSTACK_DB})) as provider:
            _populate_db(provider)
            values = provider.values_for_tag("dis")
            assert values == ['Dis 1', 'Dis 2']
    except NotImplementedError:
        skip("Unsupported with standard sqlite. Use supersqlite")
