from overrides import overrides

from haystackapi import HaystackInterface, Any


class Provider(HaystackInterface):
    @overrides
    def nav(self, nav_id: str) -> Any:
        pass
