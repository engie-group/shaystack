from overrides import overrides

from haystackapi import HaystackInterface
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def point_write(self, id: str) -> Grid:
        pass

    @overrides
    def his_write(self, id: str) -> Grid:
        pass

