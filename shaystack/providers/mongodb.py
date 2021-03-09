import logging
from datetime import datetime
from typing import Optional, List, Any, Tuple, Dict
from urllib.parse import urlparse

import pytz
from overrides import overrides
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .db_haystack_interface import DBHaystackInterface
from .url import read_grid_from_uri
from .. import Entity, traceback
from ..datatypes import Ref
from ..grid import Grid
from ..jsondumper import dump_scalar as json_dump_scalar
from ..jsonparser import parse_scalar as json_parse_scalar

log = logging.getLogger("sql.Provider")


def _conv_entity_to_row(entity: Entity) -> Dict[str, Any]:
    return {k: json_dump_scalar(v)[1:-1] for k, v in entity.items()}


def _conv_row_to_entity(row: Dict[str, Any]) -> Entity:
    return {k: json_parse_scalar(v) for k, v in row.items()}


class Provider(DBHaystackInterface):
    """
    Expose an Haystack data via the Haystack Rest API and SQL databases
    """

    def __init__(self, envs: Dict[str, str]):
        DBHaystackInterface.__init__(self, envs)
        self._connect = None
        log.info("Use %s", self._get_db())
        self._parsed_db = urlparse(self._get_db())

    def _get_db(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return self._envs["HAYSTACK_DB"]

    @property
    def name(self) -> str:
        return "MongoDB"

    @overrides
    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        pass  # FIXME

    @overrides
    def versions(self) -> List[datetime]:
        """
        Return datetime for each versions or empty array if is unknown
        """
        pass  # FIXME

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        # FIXME

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
        pass  # FIXME

    @overrides
    def his_read(
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
        pass  # FIXME

    def __exit__(self, exc_type, exc_value, exc_traceback):
        conn = self.get_connect()
        conn.close()
        self._connect = False
        # FIXME

    # -----------------------------------------
    @overrides
    def create_db(self) -> None:
        """
        Create the database and schema.
        """
        connect = self.get_connect()
        if self._table_name not in connect.list_collection_names():
            connect[self._table_name]  # Create collection

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
        try:
            # FIXME: gérer les meta-datas et les metadatas des colonnes
            grid = Grid()
            for row in self.get_collection():
                grid.append(_conv_row_to_entity(row))
        except Exception as ex:  # FIXME
            traceback.print_exc()
            raise ex

    @overrides
    def purge_db(self) -> None:
        """ Purge the current database.
        All the datas was removed.
        """
        connect = self.get_connect()
        if self._table_name in connect.list_collection_names():
            connect[self._table_name].drop()

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
        # FIXME

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
                import_time_series: True to import the time-series references via `hisURI` tag
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
            haystack_db = self.get_collection()

            target_grid = read_grid_from_uri(source_uri, envs=self._envs)

            # FIXME: calculer le delta
            # FIXME: gérer les meta-datas et les metadatas des colonnes
            # FIXME: injection du customer_id
            # FIXME: gestion des versions
            # FIXME: gérer les meta-datas de la grille et les metadata des colonnes
            if target_grid:
                records = [_conv_entity_to_row(row) for row in target_grid]
                haystack_db.insert_many(records)
        except Exception as ex:  # FIXME
            traceback.print_exc()
            raise ex  # FIXME

    @overrides
    def import_ts(self,
                  source_uri: str,
                  customer_id: str = '',
                  version: Optional[datetime] = None
                  ):
        pass  # FIXME: import des TS

    def get_connect(self) -> Database:
        if not self._connect:  # Lazy connection
            # FIXME: manage password in secret manager for MongoDB
            # password = self._parsed_db.password
            # if _BOTO3_AVAILABLE and self._parsed_db.username and \
            #         password.startswith("<") and password.endswith(">"):
            #     password = get_secret_manager_secret(password[1:-1], self._envs)
            database_name = self._parsed_db.path
            if database_name:
                database_name = database_name[1:]
            table_name = self._parsed_db.fragment
            if not table_name:
                table_name = "haystack"
            self._table_name = table_name
            client = self._connect = MongoClient(
                self._get_db(),
            )
            connect = client[database_name]
            # self._connect = LocalProxy(connect)  # Thread variable FIXME
            self._connect = connect  # FIXME: use LocalProxy
            self.create_db()
        return self._connect

    def get_collection(self) -> Collection:
        conn = self.get_connect()
        return conn[self._table_name]