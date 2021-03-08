# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Implementation of Haystack API
"""

from .haystack_interface import HaystackInterface, get_provider
from ..grid import Grid

__all__ = ["HaystackInterface", "get_provider"]

__pdoc__ = \
    {
        "sqldb_protocol": False,
        "db_postgres": False,
        "db_sqlite": False,
        "db_timestream": False,
        "tools": False,
    }


def purge_grid(grid: Grid) -> Grid:
    """
    Purge all entity not in columns
    """
    cols = grid.column
    new_grid = Grid(version=grid.version, metadata=grid.metadata, columns=cols)
    for row in grid:
        new_grid.append({key: val for key, val in row.items() if key in cols})
    return new_grid
