"""
An Haystack API provider with a very simple implementation.
It's must be used for test.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Tuple, Any, Dict, Union, Optional

from overrides import overrides

from hszinc import Grid, VER_3_0, Ref
from .haystack_interface import HaystackInterface

log = logging.getLogger("ping.Provider")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))

PingGrid = Grid(version=VER_3_0, columns={"empty": {}}, metadata={"dis": "Ping Provider"})


class Provider(HaystackInterface):
    """ Simple provider to implement all Haystack operation """

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' ops """
        log.info("about()")
        grid = super().about(home)
        grid[0].update({  # pylint: disable=no-member
            "productVersion": "1.0",
            "moduleName": "PingProvider",
            "moduleVersion": "1.0"
        })

        return grid

    @overrides
    def read(self, limit: int, entity_ids: Optional[Grid], grid_filter: Optional[str],
             date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'read(limit={limit}, ids={entity_ids} filter="{grid_filter}", date_version={date_version})')
        return PingGrid

    @overrides
    def his_read(self, entity_id: Ref,  # pylint: disable=no-self-use, unused-argument
                 dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]],
                 date_version: Optional[datetime]) -> Grid:
        """ Return EmptyGrid """
        log.info(f'his_read(id="{entity_id}", range={dates_range}, date_version={date_version})')
        return PingGrid

    @overrides
    def his_write(self, entity_id: Ref, ts: Grid,
                  date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'his_write(id="{entity_id}, ts={ts}, date_version={date_version}")')
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
    def point_write(self, entity_id: Ref,
                    date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'point_write(id="{entity_id}, date_version={date_version}")')
        return PingGrid

    @overrides
    def invoke_action(self, entity_id: Ref, action: str, params: Dict[str, Any]) -> Grid:  # pylint: disable=no-self-use
        """ Return EmptyGrid """
        log.info(f'invoke_action(id="{entity_id}",action="{action}",params={params})')
        return PingGrid
