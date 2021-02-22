from datetime import datetime
from typing import Dict, Any, Optional

from overrides import overrides

from shaystack import Grid
from shaystack import Ref
from shaystack.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def invoke_action(
            self,
            entity_id: Ref,
            action: str,
            params: Dict[str, Any],
            date_version: Optional[datetime] = None
    ) -> Grid:
        raise NotImplementedError()
