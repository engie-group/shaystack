"""
Implementation of Haystack API
"""
import re

from .haystack_interface import HaystackInterface, get_provider
from ..grid import Grid
from ..metadata import MetadataObject
from ..sortabledict import SortableDict

__all__ = ["HaystackInterface", "get_provider"]


def select_grid(grid: Grid, select: str) -> Grid:
    if select:
        select = select.strip()
        if select not in ["*", '']:
            new_grid = Grid(version=grid.version, columns=grid.column, metadata=grid.metadata)
            new_cols = SortableDict()
            for col in re.split('[, ]', select):
                new_cols[col] = MetadataObject()
            for col, meta in grid.column.items():
                if col in new_cols:
                    new_cols[col] = meta
            new_grid.column = new_cols
            for row in grid:
                new_grid.append({key: val for key, val in row.items() if key in new_cols})
            return new_grid
    return grid
