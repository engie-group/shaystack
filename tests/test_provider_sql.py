# import datetime
# from typing import cast
#
# import psycopg2
# import pytz
# from nose import SkipTest
#
# from shaystack import Ref, Grid
# from shaystack.providers import get_provider
# from shaystack.providers.sql import Provider as SQLProvider
#
# # Set HAYSTACK_DB variable, before running the tests to validate with another database
# # HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
# HAYSTACK_DB = 'sqlite3:///:memory:#haystack'
#
# FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)
#
#
# def skip(msg: str) -> None:
#     raise SkipTest(msg)
#
#
# def test_create_db():
#     try:
#         envs = {'HAYSTACK_DB': HAYSTACK_DB}
#         with cast(SQLProvider, get_provider("shaystack.providers.sql", envs)) as provider:
#             provider.create_db()
#     except psycopg2.OperationalError as ex:
#         raise SkipTest("Postgres db not started") from ex
#
#
# def test_update_grid():
#     try:
#         envs = {'HAYSTACK_DB': HAYSTACK_DB}
#         with cast(SQLProvider, get_provider("shaystack.providers.sql", envs)) as provider:
#             provider.purge_db()
#             provider.create_db()
#             grid = Grid(metadata={"dis": "hello"},
#                         columns=[("id", {}), ("a", {"dis": "a"}), ("b", {"dis": "b"})])
#             grid.append({"id": Ref("1"), "a": "a", "b": "b"})
#             grid.append({"id": Ref("2"), "a": "c", "b": "d"})
#             provider.update_grid(grid, None, "customer", FAKE_NOW)
#     except psycopg2.OperationalError as ex:
#         raise SkipTest("Postgres db not started") from ex
#
#
# def test_about():
#     try:
#         with get_provider("shaystack.providers.sql",
#                           {'HAYSTACK_DB': HAYSTACK_DB},
#                           use_cache=False) as provider:
#             result = provider.about("http://localhost")
#             assert result[0]['moduleName'] == 'SQLProvider'
#     except psycopg2.OperationalError as ex:
#         raise SkipTest("Postgres db not started") from ex
