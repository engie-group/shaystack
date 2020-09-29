from typing import Dict, Any

from overrides import overrides

from haystackapi import HaystackInterface
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def invoke_action(self, id: str, action: str, params: Dict[str, Any]) -> Grid:
        pass
