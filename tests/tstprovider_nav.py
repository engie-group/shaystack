from overrides import overrides

from haystackapi import HaystackInterface, Any
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def nav(self, nav_id: Grid) -> Any:
        pass
