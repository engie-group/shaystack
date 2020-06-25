import threading
from abc import abstractmethod
from datetime import datetime
from typing import Any, Tuple, Dict, Optional

from werkzeug.routing import Map

import hszinc
from HaystackInterface import HaystackInterface, EmptyGrid
from haystackapi_lambda import get_lambda_context, _tcontext
from hszinc import Grid, Uri
from lambda_types import LambdaContext


class S3Provider(HaystackInterface):
    def about(self) -> Grid:
        grid = hszinc.Grid(columns={
            "haystackVersion": {},  # Str version of REST implementation
            "tz": {},  # Str of server's default timezone
            "serverName": {},  # Str name of the server or project database
            "serverTime": {},  # TODO: type current DateTime of server's clock
            "serverBootTime": {},  # TODO: type DateTime when server was booted up
            "productName": {},  # Str name of the server software product
            "productUri": {},  # TODO: type Uri of the product's web site
            "productVersion": {},  # TODO: from git label. version of the server software product
            # "moduleName": {},  # module which implements Haystack server protocol if its a plug-in to the product
            # "moduleVersion": {}  # Str version of moduleName
        })
        grid.append(
            {
                "haystackVersion": "3.0",
                "tz": None,  # FIXME: set the tz
                "serverName": "localhost",  # FIXME: set the server name
                "serverTime": None,  # FIXME: set the serverTime
                "serverBootTime": None,  # FIXME: set the serverBootTime
                "productName": "carbonapi",
                "productUri": Uri("http://localhost:1234"),  # FIXME indiquer le port et trouver l'URL ?
                "productVersion": None,  # FIXME: set the product version
                "moduleName": "carbonapi",
                "moduleVersion": None  # FIXME: set the module version
            })
        return grid

    def ops(self) -> Grid:
        grid = hszinc.Grid(columns={
            "name": {},
            "summary": {},
        })
        grid.extend([
            {"name": "about", "summary": "Summary information for server"},
            {"name": "ops", "summary": "Operations supported by this server"},
            {"name": "formats", "summary": "Grid data formats supported by this server"},
            {"name": "read", "summary": "read grid with filter and limit"},
        ])
        return grid

    def read(self, filter: str, limit: int) -> Grid:
        context = get_lambda_context()  # FIXME: trouver comment faire
        return Grid(columns={"id":{}}) # FIXME: implement read

    def nav(self, navId) -> Any:  # FIXME Voir comment implementer
        return Grid(columns={"id":{}}) # FIXME: implement read

    def watchSub(self, watchId: Grid) -> Grid:
        return Grid(columns={"id":{}}) # FIXME: implement read

    def watchUnsub(self, watchId: Grid) -> EmptyGrid:
        return Grid(columns={"id":{}}) # FIXME: implement read

    def watchPoll(self, watchId: Grid) -> Grid:
        return Grid(columns={"id":{}}) # FIXME: implement read

    def pointWrite(self, id: str) -> Grid:
        return Grid(columns={"id":{}}) # FIXME: implement read

    def hisRead(self, id: str, range: Tuple[datetime, datetime]) -> Grid:
        return Grid(columns={"id":{}}) # FIXME: implement read

    def hisWrite(self, id: str) -> EmptyGrid:
        return Grid(columns={"id":{}}) # FIXME: implement read

    def invokeAction(self, id: str, action: str, params: Dict[str, Any]) -> Grid:
        return Grid(columns={"id":{}}) # FIXME: implement read
