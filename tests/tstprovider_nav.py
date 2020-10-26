from overrides import overrides

from haystackapi import Any
from haystackapi.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def nav(self, nav_id: str) -> Any:
        pass
