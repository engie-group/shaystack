"""
An Haystack API provider with a very simple implementation.
It's may be used to test.
"""
import logging
import os
from datetime import datetime
from typing import Tuple, Any, Dict, Union

from overrides import overrides

from hszinc import Grid, Uri, VER_3_0
from .haystack_interface import HaystackInterface, EmptyGrid, get_default_about

log = logging.getLogger("ping.Provider")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))

PingGrid = Grid(version=VER_3_0, columns={"empty": {}}, metadata={"dis":"Ping Provider"})

class Provider(HaystackInterface):
    """ Simple provider to implement all Haystack operation """

    @overrides
    def about(self) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' ops """
        log.info("about()")
        grid = get_default_about()
        grid[0].update({  # pylint: disable=no-member
            "productUri": Uri("http://localhost:80"),  # FIXME indiquer le port et trouver l'URL ?
            "productVersion": "1.0",  # FIXME: set the product version
            "moduleName": "PingProvider",
            "moduleVersion": "1.0"  # FIXME: set the module version
        })

        return grid

    @overrides
    def read(self, grid_filter: str, limit: int) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'read(filter="{grid_filter}",limit={limit})')
        return PingGrid

    @overrides
    def his_read(self, entity_id: str,  # pylint: disable=no-self-use, unused-argument
                 dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]]) -> Grid:
        """ Return EmptyGrid """
        log.info(f'his_read(id="{id}",range={dates_range})')
        return PingGrid

    @overrides
    def his_write(self, entity_id: str) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'his_write(id="{entity_id}")')
        return PingGrid

    @overrides
    def nav(self, nav_id: Grid) -> Any:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'nav(id="{nav_id}")')
        return PingGrid

    @overrides
    def watch_sub(self, watch_id: Grid) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'watch_sub(watchId="{watch_id}")')
        return PingGrid

    @overrides
    def watch_unsub(self, watch_id: Grid) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'watch_unsub(watchId="{watch_id}")')
        return PingGrid

    @overrides
    def watch_poll(self, watch_id: Grid) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'watch_poll(watchId="{watch_id}")')
        return PingGrid

    @overrides
    def point_write(self, entity_id: str) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'point_write(id="{entity_id}")')
        return PingGrid

    @overrides
    def invoke_action(self, entity_id: str, action: str, params: Dict[str, Any]) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'invoke_action(id="{entity_id}",action="{action}",params={params})')
        return PingGrid