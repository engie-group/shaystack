from datetime import datetime, date
from typing import Union, Tuple, Optional

from overrides import overrides

from haystackapi import HaystackInterface, Ref
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def read(self, limit: int, entity_ids: Optional[Grid] = None, grid_filter: Optional[str] = None,
             date_version: Optional[datetime] = None) -> Grid:
        pass

    @overrides
    def his_read(self, entity_id: Ref,
                 dates_range: Optional[Union[Union[datetime, str],
                                             Tuple[datetime, Optional[datetime]],
                                             Tuple[date, Optional[date]]]],
                 date_version: Optional[datetime]) -> Grid:
        pass
