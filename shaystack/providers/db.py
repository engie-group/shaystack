# -*- coding: utf-8 -*-
# SQL Provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
# pylint: disable=line-too-long
"""
An generic Haystack Read-Only API provider to expose an Haystack data via the Haystack API.

The data must be referenced with the environment variable HAYSTACK_DB and may be the form:

    - sample/carytown.zinc
    - file:///var/ontology/ontology.json
    - http://localhost:3000/ontology.json
    - http://.../ontology.zinc.gz
    - ftp://<user>:<passwd>@.../ontology.json
    - s3://.../ontology.zinc (the lambda functions must have the privilege to read this file)
    - file://etc/ontology/my_ontology.zinc
    - postgresql://scott:tiger@localhost/mydatabase#mytable
    - postgresql+psycopg2://scott:tiger@localhost/mydatabase
    - sqlite3://test.db#haystack
    - mongodb+srv://localhost/?w=majority&wtimeoutMS=2500#haystack

The URL is in form:

`&lt;dialect[+driver]&gt;://[&lt;user&gt;[:&lt;password&gt;]@][&lt;host&gt;][&lt;path&gt;][#database][?&lt;param&gt;=&lt;value&gt;]*`
"""
import logging
import sys
from datetime import datetime
from typing import Optional, Tuple, Any, List, cast, Dict
from urllib.parse import urlparse

from overrides import overrides

from .db_haystack_interface import DBHaystackInterface
from .haystack_interface import get_provider
from ..datatypes import Ref
from ..grid import Grid

log = logging.getLogger("sql.Provider")

# Associate a scheme with a provider
_scheme_to_providers = {
    '': "url",
    "file": "url",
    "ftp": "url",
    "ftps": "url",
    "http": "url",
    "https": "url",
    "s3": "url",
    "sqlite3": "sql",
    "sqlite": "sql",
    "supersqlite": "sql",
    "postgresql": "sql",
    "postgres": "sql",
    "mysql": "sql",
    "mongodb": "mongodb",
}


class Provider(DBHaystackInterface):
    """
    Expose an Haystack data via the Haystack Rest API and SQL databases.

    It's a generic provider, capable to delegate the request to `sql` or `url` providers.
    """
    __slots__ = ("_delegate",)

    def __init__(self, envs: Dict[str, str]):
        super().__init__(envs)
        if "HAYSTACK_DB" not in envs:
            print("Set 'HAYSTACK_DB' to use database", file=sys.stderr)
            sys.exit(-1)
        parsed_db = urlparse(envs["HAYSTACK_DB"])
        dialect = parsed_db.scheme
        if '+' in dialect:
            dialect = dialect.split('+')[0]
        if dialect not in _scheme_to_providers:
            print(f"Dialect {dialect} not supported", file=sys.stderr)
            sys.exit(-1)

        provider_name = __name__[0:__name__.rindex('.') + 1] + _scheme_to_providers[dialect]
        self._delegate = cast(DBHaystackInterface, get_provider(provider_name, self._envs))

    @property
    def name(self) -> str:
        # noinspection PyCallingNonCallable
        return self._delegate.name()  # type: ignore

    @overrides
    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        return self._delegate.values_for_tag(tag, date_version)

    @overrides
    def versions(self) -> List[datetime]:
        """
        Return datetime for each versions or empty array if is unknown
        """
        return self._delegate.versions()

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        return self._delegate.about(home)

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
        return self._delegate.read(limit, select, entity_ids, grid_filter, date_version)

    @overrides
    def his_read(  # type: ignore
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        """ Implement Haystack 'hisRead' """
        return self._delegate.his_read(entity_id, dates_range, date_version)  # type: ignore

    @overrides
    def create_db(self) -> None:
        """
        Create the database and schema.
        """
        self._delegate.create_db()

    def purge_db(self) -> None:
        """ Purge the current database. """
        return self._delegate.purge_db()

    @overrides
    def import_data(self,
                    source_uri: str,
                    customer_id: str = '',
                    reset: bool = False,
                    version: Optional[datetime] = None
                    ) -> None:
        return self._delegate.import_data(source_uri,
                                          customer_id,
                                          reset,
                                          version)

    @overrides
    def import_ts(self,
                  source_uri: str,
                  customer_id: str = '',
                  version: Optional[datetime] = None
                  ):
        return self._delegate.import_ts(source_uri, customer_id, version)

    @overrides
    def update_grid(self,
                    diff_grid: Grid,
                    version: Optional[datetime],
                    customer_id: Optional[str],
                    now: Optional[datetime] = None) -> None:
        return self._delegate.update_grid(diff_grid, version, customer_id, now)

    @overrides
    def read_grid(self,
                  customer_id: str = '',
                  version: Optional[datetime] = None) -> Grid:
        return self._delegate.read_grid(customer_id, version)
