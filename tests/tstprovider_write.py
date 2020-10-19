from datetime import datetime
from typing import Optional, Any

from overrides import overrides

from haystackapi import HaystackInterface, Ref
from hszinc import Grid, Quantity


class Provider(HaystackInterface):
    @overrides
    def point_write_read(self,
                         entity_id: Ref,
                         date_version: Optional[datetime]) -> Grid:
        pass

    @overrides
    def point_write_write(self,
                          entity_id: Ref,
                          level: int,
                          val: Optional[Any],
                          duration: Quantity,
                          who: Optional[str],
                          date_version: Optional[datetime]) -> None:
        pass

    @overrides
    def his_write(self,
                  entity_id: Ref,
                  time_serie: Grid,
                  date_version: Optional[datetime]) -> Grid:
        pass
