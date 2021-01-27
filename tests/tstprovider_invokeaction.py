from datetime import datetime
from typing import Dict, Any, Optional

from overrides import overrides

from haystackapi import Grid
from haystackapi import Ref
from haystackapi.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def invoke_action(
            self,
            entity_id: Ref,
            action: str,
            params: Dict[str, Any],
            date_version: Optional[datetime] = None
    ) -> Grid:
        """
        Args:
            entity_id (Ref):
            action (str):
            params:
            date_version:
        """
        raise NotImplementedError()
