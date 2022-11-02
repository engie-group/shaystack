# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Functional test with different complexes scenario
# and with different providers with real database.

import copy
import datetime
import traceback
from typing import cast

import psycopg2
import pytz
import pytest
from pymongo.errors import ServerSelectionTimeoutError
from pymysql import OperationalError

from shaystack import Ref, Grid, VER_3_0, MARKER
from shaystack.providers import get_provider
from shaystack.providers.db_haystack_interface import DBHaystackInterface

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)

_db_providers = [
    # ["shaystack.providers.sql",
    #  "sqlite3:///test.db#haystack", True],
    ["shaystack.providers.sql",
     "postgresql://postgres:password@localhost:5432/postgres?connect_timeout=100#haystack", True],
    ["shaystack.providers.sql",
     "mysql://mysql:password@localhost:5432/haystackdb?connect_timeout=100#haystack", True],
    ["shaystack.providers.mongodb",
     "mongodb://localhost/haystackdb?serverSelectionTimeoutMS=100#haystack", True],
]


def _wrapper(function, provider, db, idx):
    try:
        function(provider, db)
    except ServerSelectionTimeoutError as ex:
        _db_providers[idx][2] = False
        pytest.skip("Mongo db not started")
    except psycopg2.OperationalError as ex:
        _db_providers[idx][2] = False
        pytest.skip("Postgres db not started")
    except OperationalError as ex:
        _db_providers[idx][2] = False
        pytest.skip("MySQL db not started")
    except AssertionError as ex:
        traceback.print_exc()
        raise ex
    # except Exception as ex:
    #     traceback.print_exc()
    #     _db_providers[idx][2] = False
    #     raise ex


def _for_each_provider(function):
    for idx, (provider, db, status) in enumerate(_db_providers):
        if status:
            _wrapper(function, provider, db, idx)


def _get_grids():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col", "dis", "his", "hour", "date", "datetime"])
    sample_grid.append({"id": Ref("id1"), "col": 1, "dis": "Dis 1", "his": MARKER,
                        "hour": datetime.time(20, 0),
                        "date": datetime.date(2021, 1, 1),
                        "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)})
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


def _populate_db(provider: DBHaystackInterface) -> None:
    provider.purge_db()
    for grid, version in _get_grids():
        provider.update_grid(grid, version, "", version)


# @patch.object(ping.Provider, 'point_write_read')
def _test_update_grid_in_db(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
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
        next_fake = FAKE_NOW + datetime.timedelta(minutes=1)
        provider.update_grid(right - left, version=None, customer_id="customer", now=next_fake)
        grid = provider.read_grid("customer", None)
        assert len(grid) == 1, f"with {db}"
        grid = provider.read_grid("customer", FAKE_NOW)
        assert len(grid) == 5, f"with {db}"


def test_update_grid_in_db():
    _for_each_provider(_test_update_grid_in_db)


def _test_ops(provider_name: str, db: str):
    envs = {'HAYSTACK_DB': db}
    with get_provider(provider_name, envs) as provider:
        result = provider.ops()
        assert len(result) == 5, f"with {db}"


def test_ops():
    _for_each_provider(_test_ops)


def _test_read_last_without_filter(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "last"
        assert len(result) == 2
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 5, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"
        assert result[Ref("id2")] == {"id": Ref('id2'), 'col': 6, 'dis': 'Dis 2'}, f"with {db}"


def test_read_last_without_filter():
    _for_each_provider(_test_read_last_without_filter)


def _test_read_version_without_filter(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 2
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 3, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"
        assert result[Ref("id2")] == {"id": Ref('id2'), 'col': 4, 'dis': 'Dis 2'}, f"with {db}"


def test_read_version_without_filter():
    _for_each_provider(_test_read_version_without_filter)


def _test_read_version_with_filter(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2", f"with {db}"
        assert len(result) == 1, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 3, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_version_with_filter():
    _for_each_provider(_test_read_version_with_filter)


def _test_read_with_marker_equal(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, "his==M", None)
        assert len(result) == 1, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 5, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_with_marker_equal():
    _for_each_provider(_test_read_with_marker_equal)


def _test_read_with_hour_greater(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, "hour > 18:00", None)
        assert len(result) == 1, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 5, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_with_hour_greater():
    _for_each_provider(_test_read_with_hour_greater)


def _test_read_with_date_greater(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, "date > 2020-01-01", None)
        assert len(result) == 1, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 5, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_with_date_greater():
    _for_each_provider(_test_read_with_date_greater)


def _test_read_with_datetime_greater(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, "datetime > 2020-01-01T00:00:00+00:00", None)
        assert len(result) == 1, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 5, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_with_datetime_greater():
    _for_each_provider(_test_read_with_datetime_greater)


def _test_read_with_str_greater(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, 'dis > "A"', None)
        assert len(result) == 2, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 5, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_with_str_greater():
    _for_each_provider(_test_read_with_str_greater)


def _test_read_version_with_filter_and_select(provider_name: str, db: str):
    # caplog.set_level(logging.DEBUG)
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, "id,other", None, "id==@id1", version_2)
        assert len(result) == 1, f"with {db}"
        assert len(result.column) == 2, f"with {db}"
        assert "id" in result.column, f"with {db}"
        assert "other" in result.column, f"with {db}"


def test_read_version_with_filter_and_select():
    _for_each_provider(_test_read_version_with_filter_and_select)


def _test_read_version_with_ids(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2", f"with {db}"
        assert len(result) == 1, f"with {db}"
        assert result[Ref("id1")] == {"id": Ref("id1"), "col": 3, "dis": "Dis 1", "his": MARKER,
                                      "hour": datetime.time(20, 0),
                                      "date": datetime.date(2021, 1, 1),
                                      "datetime": datetime.datetime(2021, 1, 1, 10, 0, tzinfo=pytz.UTC)}, f"with {db}"


def test_read_version_with_ids():
    _for_each_provider(_test_read_version_with_ids)


def _test_version(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        versions = provider.versions()
        assert len(versions) == 3, f"with {db}"


def test_version():
    _for_each_provider(_test_version)


def _test_values_for_tag_id(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        values = provider.values_for_tag("id")
        assert len(values) > 1, f"with {db}"


def test_values_for_tag_id():
    _for_each_provider(_test_values_for_tag_id)


def _test_values_for_tag_col(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                        )) as provider:
        _populate_db(provider)
        values = provider.values_for_tag("col")
        assert len(values) > 1, f"with {db}"


def test_values_for_tag_col():
    _for_each_provider(_test_values_for_tag_col)


def _test_values_for_tag_dis(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        values = provider.values_for_tag("dis")
        assert values == ['Dis 1', 'Dis 2'], f"with {db}"


def test_values_for_tag_dis():
    _for_each_provider(_test_values_for_tag_dis)
