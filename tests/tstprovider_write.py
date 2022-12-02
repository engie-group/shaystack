from datetime import datetime
from typing import Optional, Any

from overrides import overrides

from shaystack import Grid, Quantity, Ref
from shaystack.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def point_write_read(self,  # type: ignore
                         entity_id: Ref,
                         date_version: Optional[datetime]) -> Grid:
        raise NotImplementedError()

    @overrides
    def point_write_write(self,
                          entity_id: Ref,
                          level: int,
                          val: Optional[Any],
                          duration: Quantity,
                          who: Optional[str],
                          date_version: Optional[datetime] = None) -> None:
        raise NotImplementedError()

    @overrides
    def his_write(self,
                  entity_id: Ref,
                  time_series: Grid,
                  date_version: Optional[datetime] = None) -> Grid:
        raise NotImplementedError()
