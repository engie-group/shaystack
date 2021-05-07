from typing import List, Optional

from overrides import overrides

from shaystack import Grid, Ref
from shaystack.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def watch_sub(self, watch_dis: str, watch_id: Optional[str],
                  ids: List[Ref], lease: Optional[int]) -> Grid:
        raise NotImplementedError()

    @overrides
    def watch_poll(self, watch_id: str, refresh: bool) -> Grid:
        raise NotImplementedError()

    @overrides
    def watch_unsub(self, watch_id: str, ids: List[Ref], close: bool) -> Grid:
        raise NotImplementedError()
