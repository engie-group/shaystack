from datetime import datetime
from typing import Union, Tuple, Optional, List

from overrides import overrides

from haystackapi import Grid, Ref
from haystackapi.providers import HaystackInterface


class Provider(HaystackInterface):
    @overrides
    def read(self, limit: int,
             select: Optional[str] = None,
             entity_ids: Optional[List[Ref]] = None,
             grid_filter: Optional[str] = None,
             date_version: Optional[datetime] = None) -> Grid:
        """
        Args:
            limit (int):
            select:
            entity_ids:
            grid_filter:
            date_version:
        """
        raise NotImplementedError()

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]],
            date_version: Optional[datetime] = None,
    ) -> Grid:
        """
        Args:
            entity_id (Ref):
            dates_range:
            date_version:
        """
        raise NotImplementedError()
