from datetime import datetime
from typing import Optional, Dict, Any


def _mongo_filter(grid_filter: Optional[str],
                  version: datetime,
                  limit: int = 0,
                  customer_id: str = '') -> Dict[str, Any]:
    return "FIXME"  # FIXME
