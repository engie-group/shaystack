# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Implementation of Haystack API
"""
import re

from .haystack_interface import HaystackInterface, get_provider
from ..grid import Grid
from ..metadata import MetadataObject
from ..sortabledict import SortableDict

__all__ = ["HaystackInterface", "get_provider"]

__pdoc__ = \
    {
        "sqldb_protocol": False
    }


def select_grid(grid: Grid, select: str) -> Grid:
    """
    Args:
        grid (Grid):
        select (str):
    """
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
