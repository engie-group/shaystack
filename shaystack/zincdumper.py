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

import datetime
import functools
from typing import Tuple, Any, List

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .metadata import MetadataObject
from .sortabledict import SortableDict
from .tools import escape_str
from .type import Entity
from .version import LATEST_VER, VER_3_0, Version
from .zoneinfo import timezone_name

_EMPTY = "<empty>"


def _dump_meta(meta: MetadataObject, version: Version = LATEST_VER) -> str:
    _dump = functools.partial(_dump_meta_item, version=version)
    return ' '.join(map(_dump, list(meta.items())))


def _dump_meta_item(item: Tuple[str, Any], version: Version = LATEST_VER) -> str:
    (item_id, item_value) = item
    if item_value is MARKER:
        return _dump_id(item_id)
    return '%s:%s' % (_dump_id(item_id),
                      dump_scalar(item_value, version=version))


def _dump_columns(cols: SortableDict, version: Version = LATEST_VER) -> str:
    if not cols:
        return ''
    _dump = functools.partial(_dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    return ','.join(map(_dump, *_cols))


def _dump_column(col: str, col_meta: MetadataObject, version: Version = LATEST_VER) -> str:
    if bool(col_meta):
        return '%s %s' % (_dump_id(col),
                          _dump_meta(col_meta, version=version))
    return _dump_id(col)


def _dump_rows(grid: Grid) -> List[str]:
    return list(map(functools.partial(_dump_row, grid), grid))


def _dump_row(grid: Grid, row: Entity) -> str:
    if len(grid.column.keys()) > 1:
        return ','.join([dump_scalar(row.get(c, _EMPTY), version=grid.version) for
                         c in grid.column.keys()])
    return ','.join([dump_scalar(row.get(c, None), version=grid.version) for
                     c in grid.column.keys()])


def _dump_id(id_str: str) -> str:
    return id_str


def _dump_str(str_value: str) -> str:
    # Replace special characters.
    return f'"{escape_str(str_value)}"'


def _dump_uri(uri: Uri) -> str:
    # Replace special characters.
    uri_value = escape_str(str(uri))
    return '`%s`' % uri_value


def _dump_bin(bin_value: Bin) -> str:
    return 'Bin(%s)' % bin_value


def _dump_xstr(xstr_value: XStr) -> str:
    return '%s("%s")' % (xstr_value.encoding, xstr_value.data_to_string())


def _dump_quantity(quantity: Quantity) -> str:
    if (quantity.units is None) or (quantity.units == ''):
        return _dump_decimal(quantity.m)
    return '%s%s' % (_dump_decimal(quantity.m),
                     quantity.symbol)


def _dump_decimal(decimal: float) -> str:
    return str(decimal)


def _dump_bool(bool_value: bool) -> str:
    return 'T' if bool(bool_value) else 'F'


def _dump_coord(coordinate: Coordinate) -> str:
    return 'C(%f,%f)' % (coordinate.latitude, coordinate.longitude)


def _dump_ref(ref: Ref) -> str:
    if ref.has_value:
        return '@%s %s' % (ref.name, _dump_str(ref.value))  # type: ignore
    return '@%s' % ref.name


def _dump_hs_date(date: datetime.date) -> str:
    return date.isoformat()


def _dump_hs_time(time: datetime.time) -> str:
    return time.isoformat()


def _dump_hs_date_time(date_time: datetime.datetime) -> str:
    tz_name = timezone_name(date_time)
    return '%s %s' % (date_time.isoformat(), tz_name)


def dump_grid(grid: Grid) -> str:
    """Dump a single grid to its ZINC representation.

    Args:
        grid: The grid to dump
    Returns:
        a Zinc string
    """
    header = 'ver:%s' % _dump_str(str(grid.version))
    if bool(grid.metadata):
        header += ' ' + _dump_meta(grid.metadata, version=grid.version)
    columns = _dump_columns(grid.column, version=grid.version)
    rows = _dump_rows(grid)
    return '\n'.join([header, columns] + rows + [''])


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Dump a scalar to Zinc
    Args:
        scalar: The scala
        version: The Haysctack version
    Returns:
        The zinc string
    """
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
        return _dump_bool(scalar)
    if isinstance(scalar, Ref):
        return _dump_ref(scalar)
    if isinstance(scalar, Bin):
        return _dump_bin(scalar)
    if isinstance(scalar, XStr):
        return _dump_xstr(scalar)
    if isinstance(scalar, Uri):
        return _dump_uri(scalar)
    if isinstance(scalar, str):
        return _dump_str(scalar)
    if isinstance(scalar, datetime.datetime):
        return _dump_hs_date_time(scalar)
    if isinstance(scalar, datetime.time):
        return _dump_hs_time(scalar)
    if isinstance(scalar, datetime.date):
        return _dump_hs_date(scalar)
    if isinstance(scalar, Coordinate):
        return _dump_coord(scalar)
    if isinstance(scalar, Quantity):
        return _dump_quantity(scalar)
    if isinstance(scalar, (float, int)):
        return _dump_decimal(scalar)
    if isinstance(scalar, Grid):
        return "<<" + dump_grid(scalar) + ">>"
    raise NotImplementedError('Unhandled case: %r' % scalar)
