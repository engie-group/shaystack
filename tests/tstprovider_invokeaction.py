from datetime import datetime
from typing import Dict, Any, Optional

from overrides import overrides

from haystackapi.providers import HaystackInterface
from hszinc import Grid
from hszinc import Ref


class Provider(HaystackInterface):
    @overrides
    def invoke_action(self, entity_id: Ref, action: str,
                      params: Dict[str, Any],
                      date_version: Optional[datetime]) -> Grid:
        pass
