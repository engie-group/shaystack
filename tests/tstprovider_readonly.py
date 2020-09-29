from datetime import datetime
from typing import Union, Tuple, Optional

from overrides import overrides

from haystackapi import HaystackInterface
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def read(self, grid_filter: str, limit: int, date_version: Optional[datetime]) -> Grid:
        pass

    @overrides
    def his_read(self, id: str,
                 range: Union[Union[datetime, str], Tuple[Union[datetime, str], Union[datetime, str]]],
                 date_version: Optional[datetime]) -> Grid:
        pass
