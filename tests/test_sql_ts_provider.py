import datetime
import logging
import os
from typing import cast
from unittest.mock import patch

import pytz
from nose import SkipTest

from haystackapi import Ref, Grid
from haystackapi.providers import get_provider
from haystackapi.providers.sql_ts import Provider as SQLTSProvider

# Set HAYSTACK_DB variable, before running the tests to validate with another database
# HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
HAYSTACK_DB = os.environ.get("HAYSTACK_DB", 'sqlite3:///:memory:#haystack')
HAYSTACK_TS = os.environ.get("HAYSTACK_TS", 'timeseries://HaystackAPIDemo/?mem_ttl=1&mag_ttl=73000#haystack')

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)

log = logging.getLogger("sql_ts.Provider")


def skip(msg: str) -> None:
    raise SkipTest(msg)


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
@patch.dict('os.environ', {'HAYSTACK_TS': HAYSTACK_TS})
def test_create_db():
    with cast(SQLTSProvider, get_provider("haystackapi.providers.sql_ts")) as provider:
        provider.create_db()


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
@patch.dict('os.environ', {'HAYSTACK_TS': HAYSTACK_TS})
@patch.object(SQLTSProvider, 'get_customer_id')
def test_import_ts_grid_in_db_and_his_read(mock):
    mock.return_value = "customer"
    with cast(SQLTSProvider, get_provider("haystackapi.providers.sql_ts")) as provider:
        # FIXME (NA, "NA"),
        values = [
            # ("100", "Str"),
            # (100.0, "Number"), (Quantity(1, "m"), "Number"), (100, "Number"),
            (True, "Bool"), (False, "Bool"),
            # (MARKER, "Marker"), (None, "Marker"),
            # (REMOVE, "Remove"), (None, "Remove"),
            # (Ref("abc"), "Ref"),
            # (datetime.datetime.utcnow().replace(microsecond=0), "DateTime"),
            # (datetime.date.today(), "Date"),
            # (datetime.datetime.utcnow().time(), "Time"),
            # (datetime.time(16, 58, 57, 994), "Time"),
            # (Coordinate(100.0, 200.0), "Coord"),
        ]

        # Check TS with all types
        entity_id = Ref("abc")

        for val, kind in values:
            # Insert an antity for the TS, with an attribut "kind"
            provider.purge_db()  # FIXME: purger ts ?
            grid = Grid(columns=["id", "kind"])
            grid.append({"id": entity_id, "kind": kind})  # Without "kind", the default is "Number" or "float"
            version = datetime.datetime.now(tz=pytz.UTC)
            provider.import_diff_grid_in_db(diff_grid=grid, version=version, customer_id="customer")

            # WARNING: timestream accept only datetime in the memory retention period.
            # Not before and not after.
            # It's not possible to extend the memory retention temporary to inject an old value

            provider.delete_ts()
            provider.create_db()
            log.debug(f"Test {type(val)}")
            grid = Grid(columns=["ts", "val"])

            # You must use utcnow() and a retention
            grid.append({"ts": datetime.datetime.utcnow(), "val": val})
            provider.import_ts_in_db(grid, FAKE_NOW, Ref("abc"), "customer", FAKE_NOW)
            grid_ts = provider.his_read(entity_id, None, None)
            assert grid_ts[0]['val'] == val, f"with {kind=} and {val=}"


@patch.dict('os.environ', {'HAYSTACK_DB': HAYSTACK_DB})
@patch.dict('os.environ', {'HAYSTACK_TS': HAYSTACK_TS})
def test_about():
    with get_provider("haystackapi.providers.sql_ts") as provider:
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'SQLProvider'
