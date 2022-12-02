# -*- coding: utf-8 -*-
# SQL Provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
# pylint: disable=line-too-long
"""
Manipulate Haystack ontology on MongoDB database.

Set the HAYSTACK_DB with mongo database connection URL
May be:
- mongodb+srv://localhost/?w=majority&wtimeoutMS=2500#haystack

Each entity was save in one Mongo document. A column save the JSON version of entity.
"""
import logging
from datetime import datetime, timedelta
from os.path import dirname
from typing import Optional, List, Any, Tuple, Dict, cast
from urllib.parse import urlparse, urlunparse

import pytz
from overrides import overrides
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from .db_haystack_interface import DBHaystackInterface
from .db_mongo import _mongo_filter as mongo_filter
from .tools import _BOTO3_AVAILABLE, get_secret_manager_secret
from .url import read_grid_from_uri
from .. import Entity, LATEST_VER, re
from ..datatypes import Ref
from ..grid import Grid
from ..jsondumper import dump_scalar as json_dump_scalar, _dump_meta, _dump_columns
from ..jsonparser import parse_scalar as json_parse_scalar, _parse_metadata, _parse_cols

log = logging.getLogger("sql.Provider")

_END_OF_WORLD = datetime.max.replace(tzinfo=pytz.UTC)


def _conv_entity_to_row(entity: Entity) -> Dict[str, Any]:
    return {k: json_dump_scalar(v)[1:-1] for k, v in entity.items()}


def _conv_row_to_entity(row: Dict[str, Any]) -> Entity:
    return {k: json_parse_scalar(v) for k, v in row.items()}


# noinspection PyPep8,PyPep8,PyPep8,PyPep8
class Provider(DBHaystackInterface):
    """
    Expose an Haystack data via the Haystack Rest API and SQL databases
    """
    __slots__ = '_connect', '_client', '_parsed_db', '_table_name', '_envs', '_db_url'

    def __init__(self, envs: Dict[str, str]):
        DBHaystackInterface.__init__(self, envs)
        self._connect = None
        self._client = None
        self._table_name = None
        self._db_url = self._envs["HAYSTACK_DB"]
        log.info("Use %s", self._get_db())
        self._parsed_db = urlparse(self._get_db())

        table_name = self._parsed_db.fragment
        if not table_name:
            table_name = "haystack"
        else:
            parts = list(self._parsed_db)
            self._db_url = urlunparse(parts[:-1] + [''])  # Remove fragment
            self._parsed_db = urlparse(self._db_url)
        self._table_name = table_name

        password = self._parsed_db.password
        if _BOTO3_AVAILABLE and self._parsed_db.username and \
                password.startswith("<") and password.endswith(">"):  # type: ignore
            password = get_secret_manager_secret(password[1:-1], self._envs)  # type: ignore
            parts = list(self._parsed_db)
            user, _, host = re.split('[:|@]', parts[1])
            parts[1] = f"{user}:{password}@{host}"
            self._db_url = urlunparse(parts)
            self._parsed_db = urlparse(urlunparse(parts))

    def _get_db(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return self._db_url

    @property
    def name(self) -> str:
        return "MongoDB"

    @overrides
    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        return sorted([
            json_parse_scalar(val)
            for val in self.get_collection().distinct(
                f"entity.{tag}",
                {
                    "customer_id": self.get_customer_id()
                }
            )])

    @overrides
    def versions(self) -> List[datetime]:
        """
        Return datetime for each versions or empty array if is unknown
        """
        return sorted(self.get_collection().distinct(
            "start_datetime",
            {
                "customer_id": self.get_customer_id()
            }
        ))

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        about_data = cast(Entity, grid[0])
        about_data.update(
            {  # pylint: disable=no-member
                "productVersion": "1.0",
                "moduleName": "MongoProvider",
                "moduleVersion": "1.0",
            }
        )
        return grid

    @overrides
    def read(
            self,
            limit: int,
            select: Optional[str],
            entity_ids: Optional[List[Ref]] = None,
            grid_filter: Optional[str] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        """ Implement Haystack 'read' """
        log.debug(
            "----> Call read(limit=%s, select='%s', ids=%s grid_filter='%s' date_version=%s)",
            repr(limit),
            repr(select),
            repr(entity_ids),
            repr(grid_filter),
            repr(date_version),
        )
        if date_version is None:
            date_version = datetime.now().replace(tzinfo=pytz.UTC)

        if entity_ids is None:
            cursor = self.get_collection().aggregate(
                mongo_filter(grid_filter, date_version, limit, self.get_customer_id())  # type: ignore
            )

            grid = self._init_grid_from_db(date_version)
            for row in cursor:
                grid.append(_conv_row_to_entity(row))
            return grid.select(select)

        customer_id = self.get_customer_id()
        cursor = self.get_collection().aggregate(
            [
                {'$match': {'customer_id': customer_id,
                            'start_datetime': {'$lte': date_version},
                            'end_datetime': {'$gt': date_version}}},
                {'$replaceRoot': {'newRoot': '$entity'}},
                {
                    '$match': {
                        '$expr': {
                            '$in': [
                                {
                                    '$let': {
                                        'vars': {'id_regex_':
                                            {
                                                '$regexFind': {
                                                    'input': '$id',
                                                    'regex': 'r:([:.~a-zA-Z0-9_-]+)'
                                                }
                                            }
                                        },
                                        'in': {'$arrayElemAt': ['$$id_regex_.captures', 0]}
                                    }
                                },
                                [ref.name for ref in entity_ids]
                            ]
                        }
                    }
                },
            ]
        )

        grid = self._init_grid_from_db(date_version)
        for row in cursor:
            grid.append(_conv_row_to_entity(row))
        return grid.select(select)

    @overrides
    def his_read(  # type: ignore
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(
            "----> Call his_read(id=%s , range=%s, " "date_version=%s)",
            repr(entity_id),
            repr(dates_range),
            repr(date_version),
        )
        customer_id = self.get_customer_id()
        history = Grid(columns=["ts", "val"])
        if not date_version:
            date_version = datetime.max.replace(tzinfo=pytz.UTC)
        if dates_range[1] > date_version:  # type: ignore
            dates_range = list(dates_range)  # type: ignore
            dates_range[1] = date_version  # type: ignore

        ts_collection = self._get_ts_collection()

        cursor = ts_collection.find(
            {
                "customer_id": customer_id,
                "id": entity_id.name,
                "ts":
                    {
                        "$gte": dates_range[0],  # type: ignore
                        "$lt": dates_range[1]  # type: ignore
                    }
            }).sort("ts")
        for row in cursor:
            history.append(
                {
                    "ts": row['ts'].replace(tzinfo=pytz.UTC),
                    "val": json_parse_scalar(row['val'])
                }
            )

        if history:
            min_date = datetime.max.replace(tzinfo=pytz.UTC)
            max_date = datetime.min.replace(tzinfo=pytz.UTC)

            for time_serie in history:
                min_date = min(min_date, time_serie["ts"])
                max_date = max(max_date, time_serie["ts"])
        else:
            min_date = date_version
            max_date = date_version

        history.metadata = {  # type: ignore
            "id": entity_id,
            "hisStart": min_date,
            "hisEnd": max_date,
        }
        return history

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self._client:
            self._client.close()
            self._connect = False

    # -----------------------------------------
    @overrides
    def create_db(self) -> None:
        """
        Create the database and schema.
        """
        connect = self.get_db()
        if self._table_name not in connect.list_collection_names():
            collection = connect.create_collection(self._table_name)  # type: ignore
            collection.create_index(
                [("customer_id", ASCENDING),
                 ("start_datetime", ASCENDING),
                 ("end_datetime", ASCENDING),
                 ])
        metadata_name = self._table_name + "_meta_datas"  # type: ignore
        if metadata_name not in connect.list_collection_names():
            collection = connect.create_collection(metadata_name)
            collection.create_index(
                [
                    ("customer_id", ASCENDING),
                    ("start_datetime", ASCENDING),
                    ("end_datetime", ASCENDING),
                ])
        ts_name = self._table_name + "_ts"  # type: ignore
        if ts_name not in connect.list_collection_names():
            collection = connect.create_collection(ts_name)
            collection.create_index(
                [
                    ("customer_id", ASCENDING),
                    ("id", ASCENDING),
                    ("ts", ASCENDING),
                ])

    @overrides
    def purge_db(self) -> None:
        """ Purge the current database.
        All the datas was removed.
        """
        connect = self.get_db()
        if self._table_name in connect.list_collection_names():
            connect[self._table_name].drop()
        metadata_name = self._table_name + "_meta_datas"  # type: ignore
        if metadata_name in connect.list_collection_names():
            connect[metadata_name].drop()
        ts_name = self._table_name + "_ts"  # type: ignore
        if ts_name in connect.list_collection_names():
            connect[ts_name].drop()

    @overrides
    def read_grid(self,
                  customer_id: str = '',
                  version: Optional[datetime] = None) -> Grid:
        """
        Read all haystack data for a specific customer, from the database and return a Grid.
        Args:
            customer_id: The customer_id date to read
            version: version to load
        Returns:
            A grid with all data for a customer
        """
        if version is None:
            version = datetime.now().replace(tzinfo=pytz.UTC)
        grid = self._init_grid_from_db(version)
        for row in self.get_collection().find(
                {
                    'customer_id': customer_id,
                    'start_datetime': {'$lte': version},
                    'end_datetime': {'$gt': version},
                },
                {"entity": True}):
            grid.append(_conv_row_to_entity(row["entity"]))
        return grid

    def _read_partial_grid(self,
                           ids: List[Ref],
                           customer_id: str,
                           version: datetime) -> Grid:
        """
        Read all haystack data for a specific customer, from the database and return a Grid.
        Args:
            customer_id: The customer_id date to read
            version: version to load
        Returns:
            A grid with all data for a customer
        """
        grid = self._init_grid_from_db(version)
        for row in self.get_collection().find(
                {
                    'customer_id': customer_id,
                    'start_datetime': {'$lte': version},
                    'end_datetime': {'$gt': version},
                    'entity.id': {
                        "$in": [json_dump_scalar(id_entity)[1:-1] for id_entity in ids]
                    }
                },
                {"entity": True}):
            grid.append(_conv_row_to_entity(row["entity"]))
        return grid

    # noinspection PyPep8
    def _init_grid_from_db(self, version: Optional[datetime]) -> Grid:
        customer_id = self.get_customer_id()
        if version is None:
            version = datetime.now().replace(tzinfo=pytz.UTC)
        meta_collection = self._get_meta_collection()

        grid = Grid(version=LATEST_VER)
        # noinspection PyPep8
        meta_record = list(meta_collection.aggregate(
            [
                # noinspection PyPep8
                {'$match':
                    {
                        'customer_id': customer_id,
                        'start_datetime': {'$lte': version},
                        'end_datetime': {'$gt': version},
                    }
                },
                {"$project": {"metadata": True, "cols": True}}
            ]))
        if meta_record:
            grid.metadata = _parse_metadata(_conv_row_to_entity(meta_record[0]['metadata']), LATEST_VER)
            _parse_cols(grid, meta_record[0]['cols'], LATEST_VER)
        return grid

    @overrides
    def update_grid(self,
                    diff_grid: Grid,
                    version: Optional[datetime],
                    customer_id: Optional[str],
                    now: Optional[datetime] = None) -> None:
        """Import the diff_grid inside the database.
        Args:
            diff_grid: The difference to apply in database.
            version: The version to save.
            customer_id: The customer id to insert in each row.
            now: The pseudo 'now' datetime.
        """
        if not customer_id:
            customer_id = ""
        if now is None:
            now = datetime.now(tz=pytz.UTC)
        if version is None:
            version = datetime.now().replace(tzinfo=pytz.UTC)
        end_date = now - timedelta(microseconds=1)

        # Read only modified rows
        init_grid = self._read_partial_grid(
            [row['id'] for row in diff_grid],
            customer_id, version
        )
        # Updated rows
        new_grid = init_grid + diff_grid

        # Update metadata ?
        if new_grid.metadata != init_grid.metadata or new_grid.column != init_grid.column:
            haystack_meta_db = self._get_meta_collection()
            haystack_meta_db.update_one(
                {
                    "customer_id": customer_id,
                    "end_datetime": _END_OF_WORLD
                },
                {"$set": {"end_datetime": end_date}}
            )
            haystack_meta_db.insert_one(
                {
                    'customer_id': customer_id,
                    "start_datetime": version,
                    "end_datetime": _END_OF_WORLD,
                    "metadata": _dump_meta(new_grid.metadata),
                    "cols": _dump_columns(new_grid.column)
                })
            log.debug("Update metadatas")
        # Close all entities
        haystack_db = self.get_collection()
        closed_id = [json_dump_scalar(row["id"])[1:-1] for row in diff_grid]
        if closed_id:
            result = haystack_db.update_many(
                {
                    "entity.id": {"$in": closed_id},
                    "end_datetime": _END_OF_WORLD
                },
                {"$set": {"end_datetime": end_date}}
            )
            log.debug("Close %s record(s)", result.modified_count)
            # Insert and update entities
            records = [
                {
                    "customer_id": customer_id,
                    "start_datetime": now,
                    "end_datetime": _END_OF_WORLD,
                    "entity": _conv_entity_to_row(new_grid[updated_entity["id"]])  # type: ignore
                }
                for updated_entity in diff_grid
                if updated_entity["id"] in new_grid
            ]
            result = haystack_db.insert_many(records)
            log.debug("Import %s record(s)", len(result.inserted_ids))

    def import_data(self,  # pylint: disable=too-many-arguments
                    source_uri: str,
                    customer_id: str = '',
                    reset: bool = False,
                    version: Optional[datetime] = None
                    ) -> None:
        """
        Import source URI to database.
        Args:
                source_uri: The source URI.
                customer_id: The customer id.
                reset: Remove all the current data before import the grid.
                version: The associated version time.
        """
        if not version:
            version = datetime.now(tz=pytz.UTC)
        if not customer_id:
            customer_id = self.get_customer_id()
        if reset:
            self.purge_db()
        self.create_db()

        original_grid = self.read_grid(customer_id, version)
        target_grid = read_grid_from_uri(source_uri, envs=self._envs)
        self.update_grid(target_grid - original_grid, version, customer_id)

    # PPR: add transaction ?
    @overrides
    def import_ts(self,
                  source_uri: str,
                  customer_id: str = '',
                  version: Optional[datetime] = None
                  ):
        target_grid = read_grid_from_uri(source_uri, envs=self._envs)
        dir_name = dirname(source_uri)
        for row in target_grid:
            if "hisURI" in row:
                assert "id" in row, "TS must have an id"
                uri = dir_name + '/' + row['hisURI']
                ts_grid = read_grid_from_uri(uri, envs=self._envs)
                self._import_ts_in_db(ts_grid, row["id"], customer_id)
                log.debug("%s imported", uri)
            elif "history" in row:
                ts_grid = row["history"]
                self._import_ts_in_db(ts_grid, row["id"], customer_id)
                log.debug("%s imported", uri)

    # noinspection PyUnusedLocal
    def _import_ts_in_db(self,
                         time_series: Grid,
                         entity_id: Ref,
                         customer_id: Optional[str],
                         now: Optional[datetime] = None
                         ) -> None:
        assert 'ts' in time_series.column, "TS must have a column 'ts'"
        if not customer_id:
            customer_id = ""
        ts_collection = self._get_ts_collection()
        begin_datetime = time_series.metadata.get("hisStart")
        end_datetime = time_series.metadata.get("hisStart")
        if time_series and not begin_datetime:
            begin_datetime = time_series[0]['ts']  # type: ignore
        if time_series and not end_datetime:
            end_datetime = time_series[-1]['ts']  # type: ignore
        if not begin_datetime:
            begin_datetime = datetime.min
        if not end_datetime:
            end_datetime = datetime.max

        #                 id TEXT NOT NULL,
        #                 customer_id TEXT NOT NULL,
        #                 date_time TIMESTAMP WITH TIME ZONE NOT NULL,
        #                 val JSONB NOT NULL
        # Clean only the period
        ts_collection.delete_many(
            {
                "customer_id": customer_id,
                "id": entity_id.name,
                "ts":
                    {
                        "$gte": begin_datetime,
                        "$lt": end_datetime
                    }
            })

        # Add add new values
        ts_collection.insert_many(
            [
                {
                    "customer_id": customer_id,
                    "id": entity_id.name,
                    "ts": row['ts'],
                    "val": json_dump_scalar(row['val'])
                }
                for row in time_series
            ]
        )

    def get_db(self) -> Database:
        if not self._connect:  # Lazy connection
            database_name = self._parsed_db.path
            if database_name:
                database_name = database_name[1:]
            self._parsed_db.geturl()
            self._client = self._connect = MongoClient(  # type: ignore
                self._get_db(),
            )
            connect = self._client[database_name]  # type: ignore
            self._connect = connect
            self.create_db()
        return self._connect  # type: ignore

    def get_collection(self) -> Collection:
        mongodb = self.get_db()
        return mongodb[self._table_name]  # type: ignore

    def _get_meta_collection(self) -> Collection:
        mongodb = self.get_db()
        return mongodb[self._table_name + "_meta_datas"]  # type: ignore

    def _get_ts_collection(self) -> Collection:
        mongodb = self.get_db()
        return mongodb[self._table_name + "_ts"]  # type: ignore
