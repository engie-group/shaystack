from typing import Dict, Any

from overrides import overrides

from haystackapi import HaystackInterface, Ref
from hszinc import Grid


class Provider(HaystackInterface):
    @overrides
    def invoke_action(self, entity_id: Ref, action: str, params: Dict[str, Any]) -> Grid:
        pass
