# -*- coding: utf-8 -*-
# Zinc Grid dumper
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Save a `Grid` in Zinc file, conform with the specification describe
here (https://www.project-haystack.org/doc/Zinc)
"""
from __future__ import unicode_literals

import datetime
import functools
import re
from typing import Match, Tuple, Any, List, Dict

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, STR_SUB, XStr
from .grid import Grid
from .metadata import MetadataObject
from .sortabledict import SortableDict
from .version import LATEST_VER, VER_3_0, Version
from .zoneinfo import timezone_name

URI_META = re.compile(r'([\\`\u0080-\uffff])')
STR_META = re.compile(r'([\\"$\u0080-\uffff])')


def str_sub(match: Match) -> str:
    char = match.group(0)
    order = ord(char)
    if order >= 0x0080:
        # Unicode
        return '\\u%04x' % order
    if char in '\\"$':
        return '\\%s' % char
    return str(char)


def uri_sub(match: Match) -> str:
    char = match.group(0)
    order = ord(char)
    if order >= 0x80:
        # Unicode
        return '\\u%04x' % order
    if char in '\\`':
        return '\\%s' % char
    return str(char)


def dump_grid(grid: Grid) -> str:
    """
    Dump a single grid to its ZINC representation.
    """
    header = 'ver:%s' % dump_str(str(grid.version))
    if bool(grid.metadata):
        header += ' ' + dump_meta(grid.metadata, version=grid.version)
    columns = dump_columns(grid.column, version=grid.version)
    rows = dump_rows(grid)
    return '\n'.join([header, columns] + rows + [''])


def dump_meta(meta: MetadataObject, version: Version = LATEST_VER) -> str:
    _dump = functools.partial(dump_meta_item, version=version)
    return ' '.join(map(_dump, list(meta.items())))


def dump_meta_item(item: Tuple[str, Any], version: Version = LATEST_VER) -> str:
    (item_id, item_value) = item
    if item_value is MARKER:
        return dump_id(item_id)
    return '%s:%s' % (dump_id(item_id),
                      dump_scalar(item_value, version=version))


def dump_columns(cols: SortableDict, version: Version = LATEST_VER) -> str:
    if not cols:
        return ''
    _dump = functools.partial(dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    return ','.join(map(_dump, *_cols))


def dump_column(col: str, col_meta: MetadataObject, version: Version = LATEST_VER) -> str:
    if bool(col_meta):
        return '%s %s' % (dump_id(col),
                          dump_meta(col_meta, version=version))
    return dump_id(col)


def dump_rows(grid: Grid) -> List[str]:
    return list(map(functools.partial(dump_row, grid), grid))


_EMPTY = "<empty>"


def dump_row(grid: Grid, row: Dict[str, Any]) -> str:
    if len(grid.column.keys()) > 1:
        return ','.join([dump_scalar(row.get(c, _EMPTY), version=grid.version) for
                         c in grid.column.keys()])
    return ','.join([dump_scalar(row.get(c, None), version=grid.version) for
                     c in grid.column.keys()])


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    if scalar is _EMPTY:
        return ""
    if scalar is None:
        return 'N'
    if scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s '
                             'does not support NA'
                             % version)
        return 'NA'
    if scalar is MARKER:
        return 'M'
    if scalar is REMOVE:
        return 'R'
    if isinstance(scalar, list):
        # Forbid version 2.0 and earlier.
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s '
                             'does not support lists'
                             % version)
        return '[%s]' % ','.join(map(
            functools.partial(dump_scalar, version=version),
            scalar))
    if isinstance(scalar, dict):
        # Forbid version 2.0 and earlier.
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s '
                             'does not support dicts'
                             % version)
        return '{' + ' '.join([k + ':' + dump_scalar(v, version=version) for (k, v) in scalar.items()]) + '}'
    if isinstance(scalar, bool):
        return dump_bool(scalar)
    if isinstance(scalar, Ref):
        return dump_ref(scalar)
    if isinstance(scalar, Bin):
        return dump_bin(scalar)
    if isinstance(scalar, XStr):
        return dump_xstr(scalar)
    if isinstance(scalar, Uri):
        return dump_uri(scalar)
    if isinstance(scalar, str):
        return dump_str(scalar)
    if isinstance(scalar, datetime.datetime):
        return dump_hs_date_time(scalar)
    if isinstance(scalar, datetime.time):
        return dump_hs_time(scalar)
    if isinstance(scalar, datetime.date):
        return dump_hs_date(scalar)
    if isinstance(scalar, Coordinate):
        return dump_coord(scalar)
    if isinstance(scalar, Quantity):
        return dump_quantity(scalar)
    if isinstance(scalar, (float, int)):
        return dump_decimal(scalar)
    if isinstance(scalar, Grid):
        return "<<" + dump_grid(scalar) + ">>"
    raise NotImplementedError('Unhandled case: %r' % scalar)


def dump_id(id_str: str) -> str:
    return id_str


def dump_str(str_value: str) -> str:
    # Replace special characters.
    str_value = STR_META.sub(str_sub, str_value)
    # Replace other escapes.
    for orig, esc in STR_SUB:
        str_value = str_value.replace(orig, esc)
    return '"%s"' % str_value


def dump_uri(uri: Uri) -> str:
    # Replace special characters.
    uri_value = str(uri)
    uri_value = URI_META.sub(uri_sub, uri_value)
    # Replace other escapes.
    for orig, esc in STR_SUB:
        uri_value = uri_value.replace(orig, esc)
    return '`%s`' % uri_value


def dump_bin(bin_value: Bin) -> str:
    return 'Bin(%s)' % bin_value


def dump_xstr(xstr_value: XStr) -> str:
    return '%s("%s")' % (xstr_value.encoding, xstr_value.data_to_string())


def dump_quantity(quantity: Quantity) -> str:
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.m)
    return '%s%s' % (dump_decimal(quantity.m),
                     quantity.unit)


def dump_decimal(decimal: float) -> str:
    return str(decimal)


def dump_bool(bool_value: bool) -> str:
    return 'T' if bool(bool_value) else 'F'


def dump_coord(coordinate: Coordinate) -> str:
    return 'C(%f,%f)' % (coordinate.latitude, coordinate.longitude)


def dump_ref(ref: Ref) -> str:
    if ref.has_value:
        return '@%s %s' % (ref.name, dump_str(ref.value))
    return '@%s' % ref.name


def dump_hs_date(date: datetime.date) -> str:
    return date.isoformat()


def dump_hs_time(time: datetime.time) -> str:
    return time.isoformat()


def dump_hs_date_time(date_time: datetime.datetime) -> str:
    tz_name = timezone_name(date_time)
    return '%s %s' % (date_time.isoformat(), tz_name)
