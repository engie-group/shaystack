import datetime
from typing import cast

import pytz
import pytest
from pymongo.errors import ServerSelectionTimeoutError

from shaystack import Ref, Grid
from shaystack.providers import get_provider
# noinspection PyProtectedMember
from shaystack.providers.mongodb import Provider as MongoProvider, _conv_row_to_entity

# Set HAYSTACK_DB variable, before running the tests to validate with another database
# HAYSTACK_DB = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
HAYSTACK_DB = 'mongodb://localhost/haystackdb?serverSelectionTimeoutMS=100#haystack'

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def skip(msg: str) -> None:
    pytest.skip(msg)


def test_create_db():
    envs = {'HAYSTACK_DB': HAYSTACK_DB}
    try:

        with cast(MongoProvider, get_provider("shaystack.providers.mongodb", envs)) as provider:
            provider.create_db()

            assert "haystack" in provider.get_db().list_collection_names()
            assert "haystack_ts" in provider.get_db().list_collection_names()
            assert "haystack_meta_datas" in provider.get_db().list_collection_names()
    except ServerSelectionTimeoutError as ex:
        pytest.skip(f"Mongo db not started: {ex}")



def test_update_grid():
    try:
        envs = {'HAYSTACK_DB': HAYSTACK_DB}
        with cast(MongoProvider, get_provider("shaystack.providers.mongodb", envs)) as provider:
            provider.purge_db()
            provider.create_db()
            grid = Grid(metadata={"dis": "hello"},
                        columns=[("id", {}), ("a", {"dis": "a"}), ("b", {"dis": "b"})])
            grid.append({"id": Ref("1"), "a": "a", "b": "b"})
            grid.append({"id": Ref("2"), "a": "c", "b": "d"})
            provider.update_grid(grid, None, "customer", FAKE_NOW)

            in_table = [_conv_row_to_entity(row['entity']) for row in provider.get_collection().find()]
            assert len(in_table) == len(grid)
            assert in_table[0] == grid[0]
            assert in_table[1] == grid[1]
    except ServerSelectionTimeoutError as ex:
        pytest.skip(f"Mongo db not started: {ex}")

def test_about():
    with get_provider("shaystack.providers.mongodb",
                      {'HAYSTACK_DB': HAYSTACK_DB}) as provider:
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'MongoProvider'
