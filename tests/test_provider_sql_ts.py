# import datetime
# import logging
# import os
# from typing import cast
# from unittest.mock import patch
#
# import pytz
# from nose.plugins.attrib import attr
#
# # noinspection PyProtectedMember
# from shaystack import Ref, Grid, Quantity, MARKER, REMOVE, Coordinate, NA, parse_date_range, XStr
# from shaystack.providers import get_provider
# from shaystack.providers.sql import Provider as SQLProvider
# from shaystack.providers.timestream import Provider as DBTSProvider
#
# # Set HAYSTACK_DB variable, before running the tests to validate with another database
# # HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
# HAYSTACK_DB = os.environ.get("_HAYSTACK_DB", 'sqlite3:///:memory:#haystack')
# HAYSTACK_TS = os.environ.get("_HAYSTACK_TS", 'timestream://HaystackDemo/?mem_ttl=8766&mag_ttl=400#haystack')
#
# FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)
#
# log = logging.getLogger("sql_ts.Provider")
#
#
# @attr('aws')
# def test_create_db():
#     envs = {'HAYSTACK_DB': HAYSTACK_DB,
#             'HAYSTACK_TS': HAYSTACK_TS,
#             'AWS_PROFILE': os.environ['AWS_PROFILE'],
#             'AWS_REGION': os.environ['AWS_REGION']
#             }
#     with cast(DBTSProvider, get_provider("shaystack.providers.timestream", envs)) as provider:
#         provider.create_db()
#
#
# @attr('aws')
# @patch.object(SQLProvider, 'get_customer_id')
# @patch.object(DBTSProvider, 'get_customer_id')
# def test_import_ts_grid_in_db_and_his_read(mock1, mock2):
#     mock1.return_value = "customer"
#     mock2.return_value = "customer"
#     envs = {'HAYSTACK_DB': HAYSTACK_DB,
#             'HAYSTACK_TS': HAYSTACK_TS,
#             'AWS_PROFILE': os.environ['AWS_PROFILE'],
#             'AWS_REGION': os.environ['AWS_REGION']
#             }
#     with cast(DBTSProvider, get_provider("shaystack.providers.timestream", envs)) as provider:
#         values = [
#             (XStr("hex", "deadbeef"), "Str"),
#             ("100", "Str"),
#             (100.0, "Number"), (Quantity(1, "m"), "Number"), (100, "Number"),
#             (True, "Bool"), (False, "Bool"),
#             (MARKER, "Marker"), (None, "Marker"),
#             (REMOVE, "Remove"), (None, "Remove"),
#             (NA, "NA"), (None, "NA"),
#             (Ref("abc"), "Ref"),
#             (datetime.datetime.utcnow().replace(microsecond=0), "DateTime"),
#             (datetime.date.today(), "Date"),
#             (datetime.datetime.utcnow().time(), "Time"),
#             (datetime.time(16, 58, 57, 994), "Time"),
#             (Coordinate(100.0, 200.0), "Coord"),
#         ]
#
#         # Check TS with all types
#         entity_id = Ref("abc")
#
#         for val, kind in values:
#             # Clean DB for the specific kind
#             provider.purge_db()
#             provider.create_db()
#
#             # Insert an entity for the TS, with an attribut "kind"
#             grid = Grid(columns=["id", "kind"])
#             grid.append({"id": entity_id, "kind": kind})  # Without "kind", the default is "Number" or "float"
#             version = datetime.datetime.now(tz=pytz.UTC)
#             provider.update_grid(diff_grid=grid, version=version, customer_id="customer")
#
#             # WARNING: timestream accept only datetime in the memory retention period.
#             # Not before and not after.
#
#             log.debug("Test %s", type(val))
#             grid = Grid(columns=["ts", "val"])
#
#             # You must use utcnow() and a retention
#             grid.append({"ts": datetime.datetime.utcnow(), "val": val})
#
#             provider._import_ts_in_db(grid, entity_id, "customer", FAKE_NOW)
#             grid_ts = provider.his_read(entity_id, parse_date_range("today", provider.get_tz()), None)
#             assert grid_ts[0]['val'] == val, f"with kind={kind} and val={val}"
#
#
# @attr('aws')
# @patch.object(SQLProvider, 'get_customer_id')
# @patch.object(DBTSProvider, 'get_customer_id')
# def test_import_ts_grid_in_db_with_a_lot_of_records(mock1, mock2):
#     mock1.return_value = "customer"
#     mock2.return_value = "customer"
#     envs = {'HAYSTACK_DB': HAYSTACK_DB,
#             'HAYSTACK_TS': HAYSTACK_TS,
#             'AWS_PROFILE': os.environ['AWS_PROFILE'],
#             'AWS_REGION': os.environ['AWS_REGION']
#             }
#     with cast(DBTSProvider, get_provider("shaystack.providers.timestream", envs)) as provider:
#         # Check TS with all types
#         entity_id = Ref("abc")
#
#         # Insert an antity for the TS, with an attribut "kind"
#         provider.purge_db()
#         grid = Grid(columns=["id", "kind"])
#         grid.append({"id": entity_id, "kind": "Number"})  # Without "kind", the default is "Number" or "float"
#         version = datetime.datetime.now(tz=pytz.UTC)
#         provider.update_grid(diff_grid=grid, version=version, customer_id="customer")
#
#         # WARNING: timestream accept only datetime in the memory retention period.
#         # Not before and not after.
#         # It's not possible to extend the memory retention temporary to inject an old value
#
#         provider.purge_ts()
#         provider.create_db()
#         grid = Grid(columns=["ts", "val"])
#
#         # You must use utcnow() and a retention
#         for i in range(0, 200):
#             grid.append({"ts": datetime.datetime.utcnow().replace(microsecond=i * 1000), "val": i})
#         provider._import_ts_in_db(grid, entity_id, "customer", FAKE_NOW)
#
#
# @attr('aws')
# def test_about():
#     envs = {'HAYSTACK_DB': HAYSTACK_DB,
#             'HAYSTACK_TS': HAYSTACK_TS,
#             'AWS_PROFILE': os.environ['AWS_PROFILE'],
#             'AWS_REGION': os.environ['AWS_REGION']
#             }
#     with get_provider("shaystack.providers.timestream", envs) as provider:
#         result = provider.about("http://localhost")
#         assert result[0]['moduleName'] == 'SQLProvider'
