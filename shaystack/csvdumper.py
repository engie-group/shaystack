# -*- coding: utf-8 -*-
# Grid CSV dumper
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Save a `Grid` in CSV file, conform with the specification describe
here (https://www.project-haystack.org/doc/Csv)
"""
from __future__ import unicode_literals

import datetime
import functools
from typing import AnyStr, List, Any, Match

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .sortabledict import SortableDict
from .type import Entity
from .version import LATEST_VER, VER_3_0, Version
from .zincdumper import dump_grid as zinc_dump_grid
from .zincdumper import dump_scalar as zinc_dump_scalar
from .zincparser import parse_scalar as zinc_parse_scalar, ZincParseException


def _str_csv_escape(str_value: str) -> AnyStr:
    return str_value.replace('"', '""')  # type: ignore


def _uri_sub(match: Match) -> AnyStr:
    char = match.group(0)
    order = ord(char)
    if order >= 0x80:
        # Unicode
        return '\\u%04x' % order  # type: ignore
    if char in '\\`':
        return '\\%s' % char  # type: ignore
    return char


def _dump_columns(csv_result: List[str], cols: SortableDict) -> None:
    _dump = functools.partial(_dump_column)
    csv_result.extend(map(_dump, cols.keys()))
    # Remove last comma
    if csv_result:
        csv_result[-1] = csv_result[-1][:-1]
    csv_result.append('\n')


def _dump_column(col: str) -> str:
    return _dump_id(col) + ","


def _dump_rows(csv_result: List[str], grid: Grid) -> None:
    list(map(functools.partial(_dump_row, csv_result, grid), grid))


def _dump_row(csv_result: List[str], grid: Grid, row: Entity) -> None:
    row_in_csv = [dump_scalar(row.get(c), version=grid.version) + "," for c in grid.column.keys()]
    row_in_csv[-1] = row_in_csv[-1][:-1] + '\n'
    if len(row_in_csv) == 1 and row_in_csv[0] == '\n':
        row_in_csv[0] = ",\n"
    csv_result.extend(row_in_csv)


def _dump_id(id_str: str) -> str:
    return id_str


def _dump_str(str_value: str) -> str:
    try:
        zinc_parse_scalar(str_value)  # Is it ambiguous ?
        # Yes
        return '"""' + _str_csv_escape(str_value) + '"""'
    except ZincParseException:
        # No
        return '"' + _str_csv_escape(str_value) + '"'


def _dump_uri(uri_value: Uri) -> str:
    return '"`%s`"' % _str_csv_escape(str(uri_value))


def _dump_bin(bin_value: Bin) -> str:
    return 'Bin(%s)' % bin_value


def _dump_xstr(xstr_value: XStr) -> str:
    return '"' + _str_csv_escape('%s("%s")' % (xstr_value.encoding, xstr_value.data_to_string())) + '"'


def _dump_quantity(quantity: Quantity) -> str:
    if (quantity.symbol is None) or (quantity.symbol == ''):
        return _dump_decimal(quantity.m)
    return '%s%s' % (_dump_decimal(quantity.m),
                     quantity.symbol)


def _dump_decimal(decimal: float) -> str:
    return str(decimal)


def _dump_bool(bool_value: bool) -> str:
    return 'true' if bool(bool_value) else 'false'


def _dump_coord(coordinate: Coordinate) -> str:
    return '"' + zinc_dump_scalar(coordinate) + '"'


def _dump_ref(ref: Ref) -> str:
    if ref.has_value:
        str_ref = '@%s %s' % (ref.name, ref.value)
        if '"' in str_ref or ',' in str_ref:
            str_ref = '"' + str_ref + '"'
        return str_ref
    return '@%s' % ref.name


def _dump_date(a_date: datetime.date) -> str:
    return a_date.isoformat()


def _dump_time(time: datetime.time) -> str:
    return time.isoformat()


def _dump_date_time(date_time: datetime.datetime) -> str:
    return '%s' % (date_time.isoformat())  # Note: Excel can not parse the date time with tz_name


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Dump scala to CSV.
    Args:
        scalar: The scalar value
        version: The haystack version
    """
    if scalar is None:
        return ''
    if scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s '
                             'does not support NA'
                             % version)
        return 'NA'
    if scalar is MARKER:
        return '\u2713'
    if scalar is REMOVE:
        return 'R'
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
        return _dump_date_time(scalar)
    if isinstance(scalar, datetime.time):
        return _dump_time(scalar)
    if isinstance(scalar, datetime.date):
        return _dump_date(scalar)
    if isinstance(scalar, Coordinate):
        return _dump_coord(scalar)
    if isinstance(scalar, Quantity):
        return _dump_quantity(scalar)
    if isinstance(scalar, (float, int)):
        return _dump_decimal(scalar)
    if isinstance(scalar, list):
        return '"' + _str_csv_escape(zinc_dump_scalar(scalar, version=version)) + '"'
    if isinstance(scalar, dict):
        return '"' + _str_csv_escape(zinc_dump_scalar(scalar, version=version)) + '"'
    if isinstance(scalar, Grid):
        return '"' + _str_csv_escape("<<" + zinc_dump_grid(scalar) + ">>") + '"'
    return '"' + _str_csv_escape(zinc_dump_scalar(scalar)) + '"'


def dump_grid(grid: Grid) -> AnyStr:
    """Dump a single grid to its CSV representation.

    Args:
        grid: The grid to dump
    Returns:
        a string with a CSV representation
    """

    # Use list and join
    csv_result: List[str] = []
    _dump_columns(csv_result, grid.column)
    _dump_rows(csv_result, grid)
    return ''.join(csv_result)  # type: ignore
