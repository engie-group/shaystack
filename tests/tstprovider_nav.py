from typing import Any

from overrides import overrides

from shaystack.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def nav(self, nav_id: str) -> Any:
        return None
