"""
Manipulate Haystack ontology on SQL database.

Set the HAYSTACK_DB with sql database connection URL, similar
to [sqlalchemy](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
May be:
- postgresql://scott:tiger@localhost/mydatabase#mytable
- postgresql+psycopg2://scott:tiger@localhost/mydatabase
- sqlite3://test.db#haystack
"""
import importlib
import json
import logging
import os
import re
from datetime import datetime
from types import ModuleType
from typing import Optional, Union, Tuple, Dict, Any, Set, List
from urllib.parse import urlparse

import iso8601
import pytz
from overrides import overrides

from hszinc import Grid, Ref, jsondumper, jsonparser, VER_3_0, MetadataObject
from . import select_grid
from .haystack_interface import HaystackInterface

log = logging.getLogger("sql.Provider")

BATCH_SIZE = 25

_default_driver = {
    "postgresql": ("psycopg2", {"host", "database", "user", "password"}),
    "postgre": ("psycopg2", {"host", "database", "user", "password"}),
    # "mysql": "mysqldb",  # Not implemented yet
    # "oracle": "cx_oracle",
    # "mssql": "pymssql",
    "sqlite3": ("sqlite3", {"database"}),
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


def _import_db_driver(parsed_db) -> Tuple[ModuleType, str]:
    if not parsed_db.fragment:
        parsed_db.fragment = "haystack"
    if parsed_db.scheme.find("+") != -1:
        dialect, driver = parsed_db.scheme.split('+')
        dialect = _fix_dialect_alias(dialect)
    else:
        dialect = _fix_dialect_alias(parsed_db.scheme)
        driver = _default_driver[dialect][0]
    return (importlib.import_module(driver), dialect)


def _fix_dialect_alias(dialect):
    if dialect == "postgres":
        dialect = "postgresql"
    if dialect == "sqlite":
        dialect == "sqlite3"
    return dialect


class Provider(HaystackInterface):
    """
    Expose an Haystack file via the Haystactk Rest API.
    """

    def __init__(self):
        self._connect = None
        log.info("Use %s", self._get_db())
        self._parsed_db = urlparse(self._get_db())
        # Import DB driver compatible with DB-API2 (PEP-0249)
        self.db, dialect = _import_db_driver(self._parsed_db)
        self._sql = self._dialect_request(dialect)
        self._sql_type_to_json = self._sql["sql_type_to_json"]

    def _get_db(self):  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return os.environ["HAYSTACK_DB"]

    def create_db(self):
        conn = self._get_connect()
        cursor = conn.cursor()
        table_name = self._parsed_db.fragment
        # Create table
        cursor.execute(self._sql["CREATE_HAYSTACK_TABLE"])
        # Create index
        cursor.execute(self._sql["CREATE_HAYSTACK_INDEX_1"])  # On id
        cursor.execute(self._sql["CREATE_HAYSTACK_INDEX_2"])  # On Json, for @> operator
        # Create table
        cursor.execute(self._sql["CREATE_METADATA_TABLE"])
        # Save (commit) the changes
        conn.commit()

    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> Set[Any]:
        distinct = self._sql.get("DISTINCT_TAG_VALUES")
        if distinct is None:
            raise NotImplementedError("Not implemented")
        conn = self._get_connect()
        cursor = conn.cursor()
        cursor.execute(re.sub(r"\[#]", tag, self._sql["DISTINCT_TAG_VALUES"]),
                       (tag,))
        result = cursor.fetchall()
        conn.commit()
        return [jsonparser.parse_scalar(x[0]) for x in result]

    def versions(self) -> List[datetime]:
        """
        Return datetime for each versions or empty array if is unknown
        """
        conn = self._get_connect()
        cursor = conn.cursor()
        cursor.execute(self._sql["DISTINCT_VERSION"])
        result = cursor.fetchall()
        conn.commit()
        if result and isinstance(result[0], str):
            return [iso8601.parse_date(x[0], default_timezone=pytz.UTC) for x in result]
        return result

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        about_data: Dict[str, Any] = grid[0]
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
            entity_ids: Optional[Grid] = None,
            grid_filter: Optional[str] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:  # pylint: disable=unused-argument
        """ Implement Haystack 'read' """
        log.debug(
            "----> Call read(limit=%s, select='%s', ids=%s grid_filter='%s' date_version=%s)",
            limit,
            select,
            entity_ids,
            grid_filter,
            date_version,
        )
        conn = self._get_connect()
        cursor = conn.cursor()
        sql_type_to_json = self._sql_type_to_json
        if date_version is None:
            date_version = datetime(9999, 12, 31)
        exec_sql_filter = self._sql["exec_sql_filter"]
        if entity_ids is None:
            exec_sql_filter(self._sql,
                            cursor,
                            self._parsed_db.fragment,
                            grid_filter,
                            date_version,
                            limit,
                            self.get_customer(),
                            )
            grid = self._init_grid_from_db(date_version)
            for row in cursor:
                grid.append(jsonparser.parse_row(sql_type_to_json(row[0]), VER_3_0))
            conn.commit()
            return select_grid(grid, select)
        else:
            customer = self.get_customer()
            sql_ids = "('" + "',".join([jsondumper.dump_scalar(id) for id in entity_ids]) + "')"
            if customer:
                cursor.execute(self._sql["SELECT_ENTITY_WITH_ID_AND_CUSTOMER"] + sql_ids,
                               (date_version, date_version, customer))
            else:
                cursor.execute(self._sql["SELECT_ENTITY_WITH_ID"] + sql_ids,
                               (date_version, date_version))

            grid = self._init_grid_from_db(date_version)
            for row in cursor:
                grid.append(jsonparser.parse_row(sql_type_to_json(row[0]), VER_3_0))
            conn.commit()
            return select_grid(grid, select)

        raise NotImplementedError()

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]],
            date_version: Optional[datetime],
    ) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(
            "----> Call his_read(id=%s , range=%s, " "date_version=%s)",
            entity_id,
            dates_range,
            date_version,
        )

        raise NotImplementedError()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._get_connect().close()
        self._connect = False

    def __del__(self):
        self.__exit__(None, None, None)

    def _get_connect(self):  # PPR: monothread ? No with Zappa
        if not self._connect:  # Lazy connection
            params = {
                "host": self._parsed_db.hostname,
                "port": self._parsed_db.port,
                "user": self._parsed_db.username,
                "passwd": self._parsed_db.password,
                "password": self._parsed_db.password,
                "db": self._parsed_db.path[1:],
                "database": self._parsed_db.path[1:],
                "dbname": self._parsed_db.path[1:],
            }
            _, keys = _default_driver[self._parsed_db.scheme]
            filtered = {key: val for key, val in params.items() if key in keys}
            self._connect = self.db.connect(**filtered)
            self.create_db()
        return self._connect

    def _init_grid_from_db(self, version: Optional[datetime]) -> Grid:
        customer = self.get_customer()
        if version is None:
            version = datetime(9999, 12, 31)
        conn = self._get_connect()
        cursor = conn.cursor()
        sql_type_to_json = self._sql_type_to_json
        if customer:
            cursor.execute(self._sql["SELECT_META_DATA_WITH_CUSTOMER"],
                           (version, version, customer))
        else:
            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, version))
        grid = Grid(version=VER_3_0)
        row = cursor.fetchone()
        if row:
            meta, cols = row
            grid.metadata = MetadataObject(jsonparser.parse_metadata(sql_type_to_json(meta), VER_3_0))
            jsonparser.parse_cols(grid, sql_type_to_json(cols), VER_3_0)
        conn.commit()
        return grid

    def export_grid_from_db(self,
                            customer: Optional[str],
                            version: Optional[datetime]) -> Grid:
        """ Read haystack data from database and return a Grid"""
        if version is None:
            version = datetime(9999, 12, 31)
        conn = self._get_connect()
        cursor = conn.cursor()
        sql_type_to_json = self._sql_type_to_json

        if customer:
            cursor.execute(self._sql["SELECT_META_DATA_WITH_CUSTOMER"],
                           (version, version, customer))
        else:
            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, version))
        grid = Grid(version=VER_3_0)
        row = cursor.fetchone()
        if row:
            meta, cols = row
            grid.metadata = jsonparser.parse_metadata(sql_type_to_json(meta), VER_3_0)
            jsonparser.parse_cols(grid, sql_type_to_json(cols), VER_3_0)

        if customer:
            cursor.execute(self._sql["SELECT_ENTITY_WITH_CUSTOMER"],
                           (version, version, customer))
        else:
            cursor.execute(self._sql["SELECT_ENTITY"],
                           (version, version))

        for row in cursor:
            grid.append(jsonparser.parse_row(sql_type_to_json(row[0]), VER_3_0))
        conn.commit()
        assert _validate_grid(grid), "Error in grid"
        return grid

    def purge_db(self):
        conn = self._get_connect()
        cursor = conn.cursor()
        cursor.execute(self._sql["PURGE_TABLES_HAYSTACK"])
        cursor.execute(self._sql["PURGE_TABLES_HAYSTACK_META"])
        conn.commit()

    def import_diff_grid_in_db(self,
                               diff_grid: Grid,
                               customer: Optional[str],
                               version: Optional[datetime],
                               now: Optional[datetime] = None):

        init_grid = self._init_grid_from_db(version)
        new_grid = init_grid + diff_grid

        if now is None:
            now = datetime.now(tz=pytz.UTC)

        if version is None:
            version = datetime(9999, 12, 31)
        conn = self._get_connect()
        cursor = conn.cursor()
        sql_type_to_json = self._sql_type_to_json
        cursor.execute(self._sql["SELECT_META_DATA"],
                       (version, version))

        # Update metadata ?
        if new_grid.metadata != init_grid.metadata or new_grid.column != init_grid.column:
            cursor.execute(self._sql["CLOSE_META_DATA"],
                           (
                               now,
                           )
                           )
            cursor.execute(self._sql["UDPATE_META_DATA"],
                           (
                               customer,
                               now,
                               json.dumps(jsondumper.dump_meta(new_grid.metadata)),
                               json.dumps(jsondumper.dump_columns(new_grid.column))
                           )
                           )
            log.debug("Update metadatas")

        for row in diff_grid:
            assert "id" in row, "Can import only entity with id"
            json_id = jsondumper.dump_scalar(row["id"])
            cursor.execute(self._sql["CLOSE_ENTITY"],
                           (
                               now,
                               json_id,
                           )
                           )
            if "remove_" not in row:
                cursor.execute(self._sql["INSERT_ENTITY"],
                               (
                                   json_id,
                                   customer,
                                   now,
                                   json.dumps(jsondumper.dump_row(new_grid, new_grid[row["id"]]))
                               )
                               )
                log.debug("Update %s", row['id'].name)
            else:
                log.debug("Remove %s", row['id'].name)

        conn.commit()

    def get_customer(self) -> Optional[str]:
        """ Override this for multi-tenant"""
        return None

    def _dialect_request(self, dialect: str) -> Dict[str, str]:
        table_name = self._parsed_db.fragment
        if dialect == "sqlite3":
            # Lazy import
            from .db_sqlite import get_db_parameters as get_sqlite_parameters
            return get_sqlite_parameters(table_name)
        if dialect == "postgresql":
            from .db_postgres import get_db_parameters as get_postgres_parameters
            return get_postgres_parameters(table_name)
        raise ValueError("Dialog not implemented")
