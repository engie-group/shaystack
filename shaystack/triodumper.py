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
from typing import Match, Any

from .datatypes import _STR_SUB, Uri
from .grid import Grid
from .type import Entity
from .version import LATEST_VER, Version
from .zincdumper import dump_grid as dump_zinc_grid, \
    dump_scalar as dump_zinc_scalar

_URI_META = re.compile(r'([\\`\u0080-\uffff])')
_STR_META = re.compile(r'([\\"$\u0080-\uffff])')
_EMPTY = "<empty>"


def _escape_str(str_value: str) -> str:
    # Replace special characters.
    str_value = _STR_META.sub(_str_sub, str_value)
    # Replace other escapes.
    for orig, esc in _STR_SUB:
        str_value = str_value.replace(orig, esc)
    return str_value


def _str_sub(match: Match) -> str:
    char = match.group(0)
    order = ord(char)
    if order >= 0x0080:
        # Unicode
        return '\\u%04x' % order
    if char in '\\"$':
        return '\\%s' % char
    return str(char)


def _uri_sub(match: Match) -> str:
    char = match.group(0)
    order = ord(char)
    if order >= 0x80:
        # Unicode
        return '\\u%04x' % order
    if char in '\\`':
        return '\\%s' % char
    return str(char)


def _dump_row(grid: Grid, row: Entity) -> str:
    return '\n'.join([c + ': ' + dump_scalar(row.get(c, None), version=LATEST_VER) for
                      c in grid.column.keys() if c in row])


_STR_SUB_WITHOUT_CRLF = [
    ('\\', '\\\\'),
    ('\b', '\\b'),
    ('\f', '\\f'),
    ('\t', '\\t'),
]

_REGULAR_STR = re.compile(r'[^\x00-\x7F]|[A-Za-z_-]')


def _escape(a_string: str) -> str:
    for orig, esc in _STR_SUB:
        a_string = a_string.replace(orig, esc)
    return a_string


def _dump_str(str_value: str) -> str:
    # Replace special characters.
    str_value = _escape_str(str_value)
    if '\\n' in str_value and str_value.endswith('\\n'):
        str_value = '\n  ' + str_value.replace('\\n', '\n  ')
        if str_value.endswith("\n  "):
            str_value = str_value[:-3]
        return str_value
    else:
        if '\\n' not in str_value and str_value not in ["T", "F", "NA", "R", "N", "M"] \
                and _REGULAR_STR.match(str_value[0]):
            return str_value
        else:
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
        return 'Zinc:\n' + _INDENT.sub("  ", _escape(dump_zinc_grid(scalar)[:-1]))
    return dump_zinc_scalar(scalar, version)
