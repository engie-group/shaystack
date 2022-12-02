# -*- coding: utf-8 -*-
# SQL Provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Manipulate Haystack ontology on SQL database.

Set the HAYSTACK_DB with sql database connection URL, similar
to [sqlalchemy](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
May be:
- postgresql://scott:tiger@localhost/mydatabase#mytable
- postgresql+psycopg2://scott:tiger@localhost/mydatabase
- sqlite3://test.db#haystack

Each entity was save in one SQL row. A column save the JSON version of entity.
"""
import importlib
import json
import logging
import re
from datetime import datetime, timedelta
from os.path import dirname
from threading import local
from types import ModuleType
from typing import Optional, Tuple, Dict, Any, List, Callable, Set, cast
from urllib.parse import urlparse, ParseResult

import pytz
from overrides import overrides

from .db_haystack_interface import DBHaystackInterface
from .sqldb_protocol import DBConnection
from .tools import get_secret_manager_secret, _BOTO3_AVAILABLE
from .url import read_grid_from_uri
from ..datatypes import Ref
from ..grid import Grid
from ..jsondumper import dump_scalar, _dump_meta, _dump_columns, _dump_row
from ..jsonparser import parse_scalar, _parse_row, _parse_metadata, _parse_cols
from ..type import Entity
from ..version import LATEST_VER

log = logging.getLogger("sql.Provider")

_default_driver = {
    "sqlite3": ("supersqlite.sqlite3", {"database"}),
    "supersqlite": ("supersqlite.sqlite3", {"database"}),
    "postgresql": ("psycopg2", {"host", "database", "user", "password"}),
    "postgres": ("psycopg2", {"host", "database", "user", "password"}),
    "mysql": ("pymysql", {"host", "database", "user", "password", "client_flag"}),  # Not implemented yet
    # "oracle": "cx_oracle",
    # "mssql": "pymssql",
}


def _validate_grid(grid: Grid):
    ids = set()
    for row in grid:
        if 'id' in row:
            id_row = row['id']
            assert id_row not in ids, f"Id {id_row} is allready in grid"
            if id_row in ids:
                return False
            ids.add(id_row)
    return True


def _import_db_driver(parsed_db: ParseResult,
                      default_driver: Dict[str, Tuple[str, Set[str]]]) \
        -> Tuple[ModuleType, str, ParseResult]:
    if not parsed_db.fragment:
        parsed_db = urlparse(parsed_db.geturl() + "#haystack")
    if parsed_db.scheme.find("+") != -1:
        dialect, driver = parsed_db.scheme.split('+')
        dialect = _fix_dialect_alias(dialect)
    else:
        dialect = _fix_dialect_alias(parsed_db.scheme)
        if dialect not in default_driver:
            raise ValueError(f"Dialect '{dialect}' not supported ({parsed_db.geturl()})")
        driver = default_driver[dialect][0]
    if driver.find('.') != -1:
        splitted = driver.split('.')
        mod = importlib.import_module(splitted[0])
        return mod.__dict__[splitted[1]], dialect, parsed_db

    return importlib.import_module(driver), dialect, parsed_db


def _fix_dialect_alias(dialect: str) -> str:
    if dialect == "postgres":
        dialect = "postgresql"
    if dialect == "sqlite":
        dialect = "sqlite3"
    return dialect


class _LocalConnect(local):
    """
    One connection by thread
    """
    __slots__ = ("_connect",)

    # noinspection PyUnresolvedReferences
    def __init__(self, module: ModuleType, **params):
        super().__init__()
        self._connect = module.connect(**params)

    def get_connect(self):
        return self._connect


class Provider(DBHaystackInterface):
    """
    Expose an Haystack data via the Haystack Rest API and SQL databases
    """
    __slots__ = "_connect", "_parsed_db", "_dialect", "_default_driver", "database", \
                "_sql", "_sql_type_to_json"

    @property
    def name(self) -> str:
        return "SQL"

    def __init__(self, envs: Dict[str, str]):
        DBHaystackInterface.__init__(self, envs)
        self._connect = None
        log.info("Use %s", self._get_db())
        self._parsed_db = urlparse(self._get_db())
        # Import DB driver compatible with DB-API2 (PEP-0249)
        self._dialect = None
        self._default_driver = _default_driver
        self.database, self._dialect, self._parsed_db = \
            _import_db_driver(self._parsed_db,
                              self._default_driver)
        self._sql = self._dialect_request(self._dialect)
        self._sql_type_to_json = self._sql["sql_type_to_json"]

    def _get_db(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return self._envs["HAYSTACK_DB"]

    @overrides
    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        customer_id = self.get_customer_id()
        distinct = self._sql.get("DISTINCT_TAG_VALUES")
        if distinct is None:
            raise NotImplementedError("Not implemented")
        conn = self.get_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(re.sub(r"\[#]", tag, distinct),
                           (customer_id,))
            result = cursor.fetchall()
            conn.commit()
            return sorted([parse_scalar(x[0]) for x in result if x[0] is not None])
        finally:
            cursor.close()

    @overrides
    def versions(self) -> List[datetime]:
        """
        Return datetime for each versions or empty array if is unknown
        """
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            customer_id = self.get_customer_id()
            cursor.execute(self._sql["DISTINCT_VERSION"], (customer_id,))
            result = cursor.fetchall()
            conn.commit()
            if result and isinstance(result[0][0], str):
                return [datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc) for x in result]
            return [x[0] for x in result]
        finally:
            cursor.close()

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        about_data = cast(Entity, grid[0])
        about_data.update(
            {  # pylint: disable=no-member
                "productVersion": "1.0",
                "moduleName": "SQLProvider",
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
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            sql_type_to_json = self._sql_type_to_json
            if date_version is None:
                date_version = datetime.now().replace(tzinfo=pytz.UTC)
            exec_sql_filter: Callable = self._sql["exec_sql_filter"]
            if entity_ids is None:
                cursor = exec_sql_filter(self._sql,
                                         cursor,
                                         self._parsed_db.fragment,
                                         grid_filter,
                                         date_version,
                                         limit,
                                         self.get_customer_id(),
                                         )
                grid = self._init_grid_from_db(date_version)
                for row in cursor:
                    grid.append(_parse_row(sql_type_to_json(row[0]), LATEST_VER))
                conn.commit()
                return grid.select(select)
            customer_id = self.get_customer_id()
            sql_ids = "('" + "','".join([entity_id.name
                                         for entity_id in entity_ids]) + "')"
            cursor.execute(self._sql["SELECT_ENTITY_WITH_ID"] + sql_ids,
                           (date_version, customer_id))

            grid = self._init_grid_from_db(date_version)
            for row in cursor:
                grid.append(_parse_row(sql_type_to_json(row[0]), LATEST_VER))
            conn.commit()
            return grid.select(select)
        finally:
            cursor.close()

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
        conn = self.get_connect()
        cursor = conn.cursor()
        customer_id = self.get_customer_id()
        history = Grid(columns=["ts", "val"])
        field_to_datetime_tz = self._sql["field_to_datetime_tz"]
        try:
            if not date_version:
                date_version = datetime.max.replace(tzinfo=pytz.UTC)
            if dates_range[1] > date_version:  # type: ignore
                dates_range = list(dates_range)  # type: ignore
                dates_range[1] = date_version  # type: ignore

            cursor.execute(self._sql["SELECT_TS"], (customer_id, entity_id.name,
                                                    dates_range[0],  # type: ignore
                                                    dates_range[1] +  # type: ignore
                                                    timedelta(microseconds=-1)))
            for row in cursor:
                history.append(
                    {
                        "ts": field_to_datetime_tz(row[0]),
                        "val": parse_scalar(row[1])
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

        finally:
            cursor.close()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        conn = self.get_connect()
        conn.close()
        self._connect = False

    def get_connect(self) -> DBConnection:  # PPR: monothread ? No with Zappa
        """ Return current connection to database. """
        if not self._connect and self._dialect:  # Lazy connection
            if self._dialect not in self._default_driver:
                raise ValueError(f"Dialect '{self._dialect}' not supported")
            try:
                port = self._parsed_db.port  # To manage sqlite in memory
            except ValueError:
                port = 0
            password = self._parsed_db.password
            if _BOTO3_AVAILABLE and self._parsed_db.username and \
                    password.startswith("<") and password.endswith(">"):  # type: ignore
                password = get_secret_manager_secret(password[1:-1], self._envs)  # type: ignore
            params = {
                "host": self._parsed_db.hostname,
                "port": port,
                "user": self._parsed_db.username,
                "passwd": password,
                "password": password,
                "db": self._parsed_db.path[1:],
                "database": self._parsed_db.path[1:],
                "dbname": self._parsed_db.path[1:],
                "client_flag": 65536,  # CLIENT.MULTI_STATEMENTS
            }
            _, keys = self._default_driver[self._dialect]
            filtered = {key: val for key, val in params.items() if key in keys}
            self._connect = _LocalConnect(self.database, **filtered)  # type: ignore
            self.create_db()
        if not self._connect:
            raise ValueError("Impossible to use the database url")
        return self._connect.get_connect()

    def _init_grid_from_db(self, version: Optional[datetime]) -> Grid:
        customer = self.get_customer_id()
        if version is None:
            version = datetime.max.replace(tzinfo=pytz.UTC, microsecond=0)
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            sql_type_to_json = self._sql_type_to_json
            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, customer))
            grid = Grid(version=LATEST_VER)
            row = cursor.fetchone()
            if row:
                meta, cols = row
                grid.metadata = _parse_metadata(sql_type_to_json(meta), LATEST_VER)
                _parse_cols(grid, sql_type_to_json(cols), LATEST_VER)
            conn.commit()
            return grid
        finally:
            cursor.close()

    def _dialect_request(self, dialect: str) -> Dict[str, Any]:
        database_name = self._parsed_db.path[1:]
        table_name = self._parsed_db.fragment
        if dialect == "sqlite3":
            # Lazy import
            from .db_sqlite import get_db_parameters as get_sqlite_parameters  # pylint: disable=import-outside-toplevel
            return get_sqlite_parameters(table_name)
        if dialect == "supersqlite":
            from .db_sqlite import get_db_parameters as get_sqlite_parameters  # pylint: disable=import-outside-toplevel
            return get_sqlite_parameters(table_name)
        if dialect == "postgresql":
            from .db_postgres import \
                get_db_parameters as get_postgres_parameters  # pylint: disable=import-outside-toplevel
            return get_postgres_parameters(table_name)
        if dialect == "mysql":
            from .db_mysql import get_db_parameters as get_mysql_parameters  # pylint: disable=import-outside-toplevel
            return get_mysql_parameters(database_name, table_name)
        raise ValueError("Dialog not implemented")

    # -----------------------------------------
    @overrides
    def create_db(self) -> None:
        """
        Create the database and schema.
        """
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            # Create table
            cursor.execute(self._sql["CREATE_HAYSTACK_TABLE"])
            # Create index
            cursor.execute(self._sql["CREATE_HAYSTACK_INDEX_1"])  # On id
            if self._sql["CREATE_HAYSTACK_INDEX_2"]:
                cursor.execute(self._sql["CREATE_HAYSTACK_INDEX_2"])  # On Json, for @> operator
            # Create table
            cursor.execute(self._sql["CREATE_METADATA_TABLE"])
            # Create ts table
            cursor.execute(self._sql["CREATE_TS_TABLE"])
            cursor.execute(self._sql["CREATE_TS_INDEX"])  # On id
            # Save (commit) the changes
            conn.commit()
        finally:
            cursor.close()

    @overrides
    def read_grid(self,
                  customer_id: str = '',
                  version: Optional[datetime] = None) -> Grid:
        """
        Read all haystack data for a specific custimer, from the database and return a Grid.
        Args:
            customer_id: The customer_id date to read
            version: version to load
        Returns:
            A grid with all data for a customer
        """
        if version is None:
            version = datetime.now().replace(tzinfo=pytz.UTC)
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            sql_type_to_json = self._sql_type_to_json

            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, customer_id))
            grid = Grid(version=LATEST_VER)
            row = cursor.fetchone()
            if row:
                meta, cols = row
                grid.metadata = _parse_metadata(sql_type_to_json(meta), LATEST_VER)
                _parse_cols(grid, sql_type_to_json(cols), LATEST_VER)

            cursor.execute(self._sql["SELECT_ENTITY"],
                           (version, customer_id))

            for row in cursor:
                grid.append(_parse_row(sql_type_to_json(row[0]), LATEST_VER))
            conn.commit()
            assert _validate_grid(grid), "Error in grid"
            return grid
        finally:
            cursor.close()

    @overrides
    def purge_db(self) -> None:
        """ Purge the current database.
        All the datas was removed.
        """
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            cursor.execute(self._sql["PURGE_TABLES_HAYSTACK"])
            cursor.execute(self._sql["PURGE_TABLES_HAYSTACK_META"])
            cursor.execute(self._sql["PURGE_TABLES_TS"])
            conn.commit()
        finally:
            cursor.close()

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
        init_grid = self.read_grid(customer_id, version)  # PPR : read partial ?
        new_grid = init_grid + diff_grid

        end_date = now - timedelta(microseconds=1)
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            # cursor.execute(self._sql["SELECT_META_DATA"],
            #                (version, customer_id))

            # Update metadata ?
            if new_grid.metadata != init_grid.metadata or new_grid.column != init_grid.column:
                cursor.execute(self._sql["CLOSE_META_DATA"],
                               (
                                   end_date,
                                   now,
                                   customer_id
                               )
                               )
                cursor.execute(self._sql["UPDATE_META_DATA"],
                               (
                                   customer_id,
                                   now,
                                   json.dumps(_dump_meta(new_grid.metadata)),
                                   json.dumps(_dump_columns(new_grid.column))
                               )
                               )
                log.debug("Update metadatas")

            for row in diff_grid:  # PPR: use a batch ?
                assert "id" in row, "Can import only entity with id"
                sql_id = row["id"].name
                cursor.execute(self._sql["CLOSE_ENTITY"],
                               (
                                   end_date,
                                   now,
                                   sql_id,
                                   customer_id
                               )
                               )
                if "remove_" not in row:
                    cursor.execute(self._sql["INSERT_ENTITY"],
                                   (
                                       sql_id,
                                       customer_id,
                                       now,
                                       json.dumps(_dump_row(new_grid, new_grid[row["id"]]))  # type: ignore
                                   )
                                   )
                    log.debug("Update record %s in DB", row['id'].name)
                else:
                    log.debug("Remove record %s in DB", row['id'].name)

            conn.commit()
        finally:
            cursor.close()

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
        try:
            if not customer_id:
                customer_id = self.get_customer_id()
            if reset:
                self.purge_db()
            self.create_db()
            original_grid = self.read_grid(customer_id, version)
            target_grid = read_grid_from_uri(source_uri, envs=self._envs)
            self.update_grid(target_grid - original_grid, version, customer_id)
            log.debug("%s imported", source_uri)

        except ModuleNotFoundError as ex:
            # noinspection PyUnresolvedReferences
            log.error("Call `pip install` "
                      "with the database driver - %s", ex.msg)  # pytype: disable=attribute-error

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
        """
        Import the Time series inside the database.

        Args:
            time_series: The time-serie grid.
            entity_id: The corresponding entity.
            customer_id: The current customer id.
            now: The pseudo 'now' datetime.
        """
        assert 'ts' in time_series.column, "TS must have a column 'ts'"
        if not customer_id:
            customer_id = ""
        conn = self.get_connect()
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
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        datetime_tz_to_field = self._sql["datetime_tz_to_field"]
        # Clean only the period
        cursor.execute(self._sql["CLEAN_TS"],
                       (
                           customer_id,
                           entity_id.name,
                           datetime_tz_to_field(begin_datetime),
                           datetime_tz_to_field(end_datetime)
                       )
                       )

        # Add add new values
        cursor.executemany(self._sql["INSERT_TS"],
                           [(entity_id.name,
                             customer_id,
                             datetime_tz_to_field(row['ts']),
                             dump_scalar(row['val'])) for row in time_series]
                           )
        cursor.close()
        conn.commit()
