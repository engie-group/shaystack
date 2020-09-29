from overrides import overrides

from haystackapi import HaystackInterface
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def watch_poll(self, watchId: Grid) -> Grid:
        pass

    @overrides
    def watch_sub(self, watchId: Grid) -> Grid:
        pass

    @overrides
    def watch_unsub(self, watchId: Grid) -> Grid:
        pass

