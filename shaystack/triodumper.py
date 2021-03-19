# -*- coding: utf-8 -*-
# Zinc Grid dumper
# See the accompanying LICENSE file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Save a `Grid` in Zinc file, conform with the specification describe
here (https://www.project-haystack.org/doc/Zinc)
"""
from __future__ import unicode_literals

import functools
import re
from typing import Any

from .datatypes import Uri
from .grid import Grid
from .tools import escape_str
from .type import Entity
from .version import LATEST_VER, Version
from .zincdumper import dump_grid as dump_zinc_grid, \
    dump_scalar as dump_zinc_scalar


def _dump_row(grid: Grid, row: Entity) -> str:
    return '\n'.join([c + ': ' + dump_scalar(row.get(c, None), version=LATEST_VER) for
                      c in grid.column.keys() if c in row])


_REGULAR_STR = re.compile(r'^[^\x00-\x1F\t°\\]*$')


def _dump_str(str_value: str) -> str:
    # Replace special characters.
    str_value = escape_str(str_value)
    if '\\n' in str_value and str_value.endswith('\\n'):
        str_value = '\n  ' + str_value.replace('\\n', '\n  ')
        if str_value.endswith("\n  "):
            str_value = str_value[:-3]
        return str_value
    if str_value not in ["T", "F", "NA", "R", "N", "M"] \
            and _REGULAR_STR.match(str_value):
        return str_value
    return '"%s"' % str_value


def dump_grid(grid: Grid) -> str:
    """Dump a single grid to its TRIO representation.

    Args:
        grid: The grid to dump
    Returns:
        a Zinc string
    """
    str_grid = "\n---\n".join(list(map(functools.partial(_dump_row, grid), grid)))
    if str_grid:
        str_grid += '\n'
    return str_grid


_INDENT = re.compile(r"^", flags=re.MULTILINE)


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Dump a scalar to Trio
    Args:
        scalar: The scala
        version: The Haysctack version
    Returns:
        The trio string
    """
    if not isinstance(scalar, Uri) and isinstance(scalar, str):
        return _dump_str(scalar)
    if isinstance(scalar, Grid):
        return 'Zinc:\n' + _INDENT.sub("  ", dump_zinc_grid(scalar)[:-1])
    return dump_zinc_scalar(scalar, version)
