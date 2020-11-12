from datetime import datetime, date
from typing import Union, Tuple, Optional

from overrides import overrides

from haystackapi.providers import HaystackInterface
from hszinc import Grid, Ref


class Provider(HaystackInterface):
    @overrides
    def read(self, limit: int,
             select: Optional[str] = None,
             entity_ids: Optional[Grid] = None,
             grid_filter: Optional[str] = None,
             date_version: Optional[datetime] = None) -> Grid:
        pass

    @overrides
    def his_read(self, entity_id: Ref,
                 dates_range: Optional[Union[Union[datetime, str],
                                             Tuple[datetime, Optional[datetime]],
                                             Tuple[date, Optional[date]]]],
                 date_version: Optional[datetime]) -> Grid:
        pass
