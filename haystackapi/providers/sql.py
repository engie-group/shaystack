"""
Manipulate Haystack ontology on SQL database.

Set the HAYSTACK_DB with sql database connection URL, similar
to [sqlalchemy](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
May be:
- postgresql://scott:tiger@localhost/mydatabase#mytable
- postgresql+psycopg2://scott:tiger@localhost/mydatabase
- sqlite3://test.db#haystack
"""
import base64
import importlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from types import ModuleType
from typing import Optional, Tuple, Dict, Any, List, Callable, Set, cast
from urllib.parse import urlparse, ParseResult

import pytz
from overrides import overrides

from . import select_grid
from .haystack_interface import HaystackInterface
from .sqldb import DBConnection
from ..datatypes import Ref
from ..grid import Grid
from ..jsondumper import dump_scalar, dump_meta, dump_columns, dump_row
from ..jsonparser import parse_scalar, parse_row, parse_metadata, parse_cols
from ..metadata import MetadataObject
from ..version import VER_3_0

try:
    from botocore.exceptions import ClientError
except ImportError:
    @dataclass
    class ClientError(Exception):
        response: List[Any]

log = logging.getLogger("sql.Provider")

BOTO3_AVAILABLE = False
try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    pass

_default_driver = {
    "sqlite3": ("supersqlite.sqlite3", {"database"}),
    "supersqlite": ("supersqlite.sqlite3", {"database"}),
    "postgresql": ("psycopg2", {"host", "database", "user", "password"}),
    "postgre": ("psycopg2", {"host", "database", "user", "password"}),
    # "mysql": "mysqldb",  # Not implemented yet
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
        driver = default_driver[dialect][0]
    if driver.find('.') != -1:
        s = driver.split('.')
        mod = importlib.import_module(s[0])
        return mod.__dict__[s[1]], dialect, parsed_db

    return importlib.import_module(driver), dialect, parsed_db


def _fix_dialect_alias(dialect: str) -> str:
    if dialect == "postgres":
        dialect = "postgresql"
    if dialect == "sqlite":
        dialect = "sqlite3"
    return dialect


class Provider(HaystackInterface):
    """
    Expose an Haystack file via the Haystactk Rest API.
    """

    @property
    def name(self) -> str:
        return "SQL"

    def __init__(self):
        self._connect = None
        log.info("Use %s", self._get_db())
        self._parsed_db = urlparse(self._get_db())
        # Import DB driver compatible with DB-API2 (PEP-0249)
        self._dialect = None
        self._default_driver = _default_driver
        self.db, self._dialect, self._parsed_db = \
            _import_db_driver(self._parsed_db,
                              self._default_driver)
        self._sql = self._dialect_request(self._dialect)
        self._sql_type_to_json = self._sql["sql_type_to_json"]

    def _get_db(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return os.environ["HAYSTACK_DB"]

    def create_db(self) -> None:
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            # Create table
            cursor.execute(self._sql["CREATE_HAYSTACK_TABLE"])
            # Create index
            cursor.execute(self._sql["CREATE_HAYSTACK_INDEX_1"])  # On id
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
        about_data = cast(Dict[str, Any], grid[0])
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
    ) -> Grid:
        """ Implement Haystack 'read' """
        log.debug(
            "----> Call read(limit=%s, select='%s', ids=%s grid_filter='%s' date_version=%s)",
            limit,
            select,
            entity_ids,
            grid_filter,
            date_version,
        )
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            sql_type_to_json = self._sql_type_to_json
            if date_version is None:
                date_version = datetime.max.replace(tzinfo=pytz.UTC)
            exec_sql_filter: Callable = self._sql["exec_sql_filter"]
            if entity_ids is None:
                exec_sql_filter(self._sql,
                                cursor,
                                self._parsed_db.fragment,
                                grid_filter,
                                date_version,
                                limit,
                                self.get_customer_id(),
                                )
                grid = self._init_grid_from_db(date_version)
                for row in cursor:
                    grid.append(parse_row(sql_type_to_json(row[0]), VER_3_0))  # FIXME: sql_type ?
                conn.commit()
                return select_grid(grid, select)
            customer_id = self.get_customer_id()
            sql_ids = "('" + "','".join([dump_scalar(entity_id)
                                         for entity_id in entity_ids]) + "')"
            cursor.execute(self._sql["SELECT_ENTITY_WITH_ID"] + sql_ids,
                           (date_version, customer_id))

            grid = self._init_grid_from_db(date_version)
            for row in cursor:
                grid.append(parse_row(sql_type_to_json(row[0]), VER_3_0))
            conn.commit()
            return select_grid(grid, select)
        finally:
            cursor.close()

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]],
            date_version: Optional[datetime],
    ) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(
            "----> Call his_read(id=%s , range=%s, " "date_version=%s)",
            entity_id,
            dates_range,
            date_version,
        )
        conn = self.get_connect()
        cursor = conn.cursor()
        customer_id = self.get_customer_id()
        history = Grid(columns=["ts", "val"])
        field_to_datetime_tz = self._sql["field_to_datetime_tz"]
        try:
            if not date_version:
                date_version = datetime.max.replace(tzinfo=pytz.UTC)
            if dates_range[1] > date_version:
                dates_range = list(dates_range)
                dates_range[1] = date_version

            cursor.execute(self._sql["SELECT_TS"], (customer_id, entity_id.name,
                                                    dates_range[0], dates_range[1]))
            for row in cursor:
                history.append(
                    {
                        "ts": field_to_datetime_tz(row[0]),
                        "val": parse_scalar(row[1])
                    }
                )
            min_date = datetime.max.replace(tzinfo=pytz.UTC)
            max_date = datetime.min.replace(tzinfo=pytz.UTC)

            for time_serie in history:
                min_date = min(min_date, time_serie["ts"])
                max_date = max(max_date, time_serie["ts"])

            history.metadata = {
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
        if not self._connect and self._dialect:  # Lazy connection
            try:
                port = self._parsed_db.port  # To manage sqlite in memory
            except ValueError:
                port = 0
            password = self._parsed_db.password
            if self._parsed_db.username and password is None or password == "":
                password = self._get_secret_manager_secret()
            params = {
                "host": self._parsed_db.hostname,
                "port": port,
                "user": self._parsed_db.username,
                "passwd": password,
                "password": password,
                "db": self._parsed_db.path[1:],
                "database": self._parsed_db.path[1:],
                "dbname": self._parsed_db.path[1:],
            }
            _, keys = self._default_driver[self._dialect]
            filtered = {key: val for key, val in params.items() if key in keys}
            connect: DBConnection = self.db.connect(**filtered)
            self._connect = connect
            self.create_db()
        if not self._connect:
            raise ValueError("Inconnect database url")
        return self._connect

    def _get_secret_manager_secret(self) -> str:  # pylint: disable=no-self-use
        if not BOTO3_AVAILABLE:
            return "secretManager"

        secret_name = os.environ['HAYSTACK_DB_SECRET']
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=os.environ["AWS_REGION"]
        )

        try:
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            # Decrypts secret using the associated KMS CMK.
            # Depending on whether the secret is a string or binary,
            # one of these fields will be populated.
            if 'SecretString' in get_secret_value_response:
                secret = get_secret_value_response['SecretString']
                j = json.loads(secret)
                return j['password']
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary']).decode("UTF8")
            return decoded_binary_secret
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise ex
            if ex.response['Error']['Code'] == 'InternalServiceErrorException':
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise ex
            if ex.response['Error']['Code'] == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise ex
            if ex.response['Error']['Code'] == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise ex
            if ex.response['Error']['Code'] == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise ex
            raise ex

    def _init_grid_from_db(self, version: Optional[datetime]) -> Grid:
        customer = self.get_customer_id()
        if version is None:
            version = datetime.max.replace(tzinfo=pytz.UTC)
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            sql_type_to_json = self._sql_type_to_json
            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, customer))
            grid = Grid(version=VER_3_0)
            row = cursor.fetchone()
            if row:
                meta, cols = row
                grid.metadata = MetadataObject(parse_metadata(sql_type_to_json(meta), VER_3_0))
                parse_cols(grid, sql_type_to_json(cols), VER_3_0)
            conn.commit()
            return grid
        finally:
            cursor.close()

    def export_grid_from_db(self,
                            customer: Optional[str],
                            version: Optional[datetime]) -> Grid:
        """ Read haystack data from database and return a Grid"""
        if version is None:
            version = datetime.max.replace(tzinfo=pytz.UTC)
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            sql_type_to_json = self._sql_type_to_json

            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, customer))
            grid = Grid(version=VER_3_0)
            row = cursor.fetchone()
            if row:
                meta, cols = row
                grid.metadata = parse_metadata(sql_type_to_json(meta), VER_3_0)
                parse_cols(grid, sql_type_to_json(cols), VER_3_0)

            cursor.execute(self._sql["SELECT_ENTITY"],
                           (version, customer))

            for row in cursor:
                grid.append(parse_row(sql_type_to_json(row[0]), VER_3_0))
            conn.commit()
            assert _validate_grid(grid), "Error in grid"
            return grid
        finally:
            cursor.close()

    def purge_db(self) -> None:
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            cursor.execute(self._sql["PURGE_TABLES_HAYSTACK"])
            cursor.execute(self._sql["PURGE_TABLES_HAYSTACK_META"])
            conn.commit()
        finally:
            cursor.close()

    def import_diff_grid_in_db(self,
                               diff_grid: Grid,
                               customer_id: Optional[str],
                               version: Optional[datetime],
                               now: Optional[datetime] = None) -> None:

        init_grid = self._init_grid_from_db(version)
        new_grid = init_grid + diff_grid

        if now is None:
            now = datetime.now(tz=pytz.UTC)
        end_date = now - timedelta(milliseconds=1)
        if version is None:
            version = datetime.max.replace(tzinfo=pytz.UTC)
        conn = self.get_connect()
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        try:
            cursor.execute(self._sql["SELECT_META_DATA"],
                           (version, customer_id))

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
                                   json.dumps(dump_meta(new_grid.metadata)),
                                   json.dumps(dump_columns(new_grid.column))
                               )
                               )
                log.debug("Update metadatas")

            for row in diff_grid:
                assert "id" in row, "Can import only entity with id"
                json_id = dump_scalar(row["id"])
                cursor.execute(self._sql["CLOSE_ENTITY"],
                               (
                                   end_date,
                                   now,
                                   json_id,
                                   customer_id
                               )
                               )
                if "remove_" not in row:
                    cursor.execute(self._sql["INSERT_ENTITY"],
                                   (
                                       json_id,
                                       customer_id,
                                       now,
                                       json.dumps(dump_row(new_grid, new_grid[row["id"]]))
                                   )
                                   )
                    log.debug("Update %s", row['id'].name)
                else:
                    log.debug("Remove %s", row['id'].name)

            conn.commit()
        finally:
            cursor.close()

    def import_ts_in_db(self, time_series: Grid, entity_id: Ref, customer_id: str) -> None:
        assert 'ts' in time_series.column, "TS must have a column 'ts'"
        conn = self.get_connect()
        begin_datetime = time_series.metadata.get("hisStart")
        end_datetime = time_series.metadata.get("hisStart")
        if time_series and not begin_datetime:
            begin_datetime = time_series[0]['ts']
        if time_series and not end_datetime:
            end_datetime = time_series[-1]['ts']
        if not begin_datetime:
            begin_datetime = datetime.min
        if not end_datetime:
            end_datetime = datetime.max
        # with conn.cursor() as cursor:
        cursor = conn.cursor()
        datetime_tz_to_field = self._sql["datetime_tz_to_field"]
        try:
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
                                 json.dumps(dump_scalar(row['val']))) for row in time_series]
                               )
            cursor.close()
            conn.commit()
        finally:
            pass

    def _dialect_request(self, dialect: str) -> Dict[str, Any]:
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
        raise ValueError("Dialog not implemented")
