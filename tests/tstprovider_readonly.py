from datetime import datetime, date
from typing import Union, Tuple, Optional

from overrides import overrides

from haystackapi import HaystackInterface
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def read(self, limit: int, entity_ids: Optional[Grid], grid_filter: Optional[str],
             date_version: Optional[datetime]) -> Grid:
        pass

    @overrides
    def his_read(self, id: str,
                 range: Optional[Union[Union[datetime, str],
                                       Tuple[datetime, Optional[datetime]],
                                       Tuple[date, Optional[date]]]],
                 date_version: Optional[datetime]) -> Grid:
        pass
