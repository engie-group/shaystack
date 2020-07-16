"""
An Haystack API provider with a very simple implementation.
It's may be used to test.
"""
import logging
import os
from datetime import datetime
from typing import Tuple, Any, Dict

from tzlocal import get_localzone

import hszinc
from hszinc import Grid, Uri, VER_3_0
from providers.HaystackInterface import HaystackInterface, EmptyGrid

log = logging.getLogger("PingProvider")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))


# FIXME: a déplacer dans un autre package ? CookieCutter ?
class PingProvider(HaystackInterface):
    def about(self) -> Grid:
        log.info("about()")
        grid = hszinc.Grid(version=VER_3_0,
                           columns={
                               "haystackVersion": {},  # Str version of REST implementation
                               "tz": {},  # Str of server's default timezone
                               "serverName": {},  # Str name of the server or project database
                               "serverTime": {},
                               "serverBootTime": {},
                               "productName": {},  # Str name of the server software product
                               "productUri": {},
                               "productVersion": {},
                               # "moduleName": {},  # module which implements Haystack server protocol if its a plug-in to the product
                               # "moduleVersion": {}  # Str version of moduleName
                           })
        grid.append(
            {
                "haystackVersion": str(VER_3_0),
                "tz": str(get_localzone()),
                "serverName": "haystack_" + os.environ["AWS_REGION"],  # FIXME: set the server name
                "serverTime": datetime.now(tz=get_localzone()).replace(microsecond=0),
                "serverBootTime": datetime.now(tz=get_localzone()).replace(microsecond=0),
                "productName": "AWS Lamda Haystack Provider",
                "productUri": Uri("http://localhost:80"),  # FIXME indiquer le port et trouver l'URL ?
                "productVersion": None,  # FIXME: set the product version
                "moduleName": "PingProvider",
                "moduleVersion": None  # FIXME: set the module version
            })
        return grid

    def read(self, filter: str, limit: int) -> Grid:
        log.info(f'read(filter="{filter}",limit={limit})')
        return EmptyGrid

    def hisRead(self, id: str, range: Tuple[datetime, datetime]) -> Grid:
        log.info(f'hisRead(id="{id}",range={range})')
        return EmptyGrid  # FIXME

    def hisWrite(self, id: str) -> EmptyGrid:
        log.info(f'hisWrite(id="{id}")')
        return EmptyGrid

    def nav(self, navId: Grid) -> Any:
        log.info(f'nav(id="{navId}")')
        return EmptyGrid

    def watchSub(self, watchId: Grid) -> Grid:
        log.info(f'watchSub(watchId="{watchId}")')
        return EmptyGrid

    def watchUnsub(self, watchId: Grid) -> EmptyGrid:
        log.info(f'watchUnsub(watchId="{watchId}")')
        return EmptyGrid

    def watchPoll(self, watchId: Grid) -> Grid:
        log.info(f'watchPoll(watchId="{watchId}")')
        return EmptyGrid

    def pointWrite(self, id: str) -> Grid:
        log.info(f'pointWrite(id="{id}")')
        return EmptyGrid

    def invokeAction(self, id: str, action: str, params: Dict[str, Any]) -> Grid:
        log.info(f'invokeAction(id="{id}",action="{action}",params={params})')
        return EmptyGrid
