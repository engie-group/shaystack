from datetime import datetime
from typing import Optional

from overrides import overrides

from haystackapi import HaystackInterface, Ref
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def point_write(self, id: Ref) -> Grid:
        pass

    @overrides
    def his_write(self, id: Ref, ts: Grid, date_version: Optional[datetime]) -> Grid:
        pass
