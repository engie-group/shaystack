from datetime import datetime
from typing import Union, Tuple

from overrides import overrides

from haystackapi import HaystackInterface
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def read(self, grid_filter: str, limit: int) -> Grid:
        pass

    @overrides
    def his_read(self, id: str,
                 range: Union[Union[datetime, str], Tuple[Union[datetime, str], Union[datetime, str]]]) -> Grid:
        pass
