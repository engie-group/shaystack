#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid dumper
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from __future__ import unicode_literals

import datetime
import functools
import re

import six

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, STR_SUB, XStr
from .grid import Grid
from .version import LATEST_VER, VER_3_0
from .zincdumper import dump_grid as zinc_dump_grid
from .zincdumper import dump_scalar as zinc_dump_scalar
from .zoneinfo import timezone_name

URI_META = re.compile(r'([\\`\u0080-\uffff])')
STR_META = re.compile(r'([\\"\$\u0080-\uffff])')

CSV_SUB = [
    (u'\\"', u'""'),
    (u'\\\\', u'\\'),
    (u'\\u2713', u'\u2713'),
]


def str_sub(match):
    c = match.group(0)
    o = ord(c)
    if o >= 0x0080:
        # Unicode
        return '\\u%04x' % o
    elif c in '\\"$':
        return '\\%s' % c


def str_csv_escape(str_value):
    str_value = STR_META.sub(str_sub, str_value)
    for orig, esc in CSV_SUB:
        str_value = str_value.replace(orig, esc)
    return str_value


def uri_sub(match):
    c = match.group(0)
    o = ord(c)
    if o >= 0x80:
        # Unicode
        return '\\u%04x' % o
    elif c in '\\`':
        return '\\%s' % c


def dump_grid(grid):
    """
    Dump a single grid to its CSV representation.
    """

    # Use list and join
    csv_result = []
    dump_columns(csv_result, grid.column, version=grid._version)
    dump_rows(csv_result, grid)
    return ''.join(csv_result)


def dump_columns(csv_result, cols, version=LATEST_VER):
    _dump = functools.partial(dump_column, version=version)
    csv_result.extend(map(_dump, cols.keys()))
    # Remove last comma
    if len(csv_result):
        csv_result[-1] = csv_result[-1][:-1]
    csv_result.append('\n')


def dump_column(col, version):
    return dump_id(col, version=version) + ","


def dump_rows(csv_result, grid):
    list(map(functools.partial(dump_row, csv_result, grid), grid))


def dump_row(csv_result, grid, row):
    rc = [dump_scalar(row.get(c), version=grid.version) + "," for \
          c in grid.column.keys()]
    rc[-1] = rc[-1][:-1] + '\n'
    if len(rc) == 1 and rc[0] == '\n':
        rc[0] = ",\n"
    csv_result.extend(rc)


def dump_id(id_str, version=LATEST_VER):
    return id_str


def dump_str(str_value, version=LATEST_VER):
    return '"' + str_csv_escape(str_value) + '"'


def dump_uri(uri_value, version=LATEST_VER):
    # Replace special characters.
    uri_value = URI_META.sub(uri_sub, uri_value)
    # Replace other escapes.
    for orig, esc in STR_SUB:
        uri_value = uri_value.replace(orig, esc)
    return '`%s`' % uri_value


def dump_bin(bin_value, version=LATEST_VER):
    return 'Bin(%s)' % bin_value


def dump_xstr(xstr_value, version=LATEST_VER):
    return '"' + str_csv_escape(str(xstr_value)) + '"'


def dump_quantity(quantity, version=LATEST_VER):
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.value, version=version)
    else:
        return '%s%s' % (dump_decimal(quantity.value),
                         quantity.unit)


def dump_decimal(decimal, version=LATEST_VER):
    return str(decimal)


def dump_bool(bool_value, version=LATEST_VER):
    return 'true' if bool(bool_value) else 'false'


def dump_coord(coordinate, version=LATEST_VER):
    return '"'+zinc_dump_scalar(coordinate)+'"'



def dump_ref(ref, version=LATEST_VER):
    if ref.has_value:
        s = '@%s %s' % (ref.name, ref.value)
        if '"' in s or ',' in s:
            s = '"' + s + '"'
        return s
    else:
        return '@%s' % ref.name


def dump_date(date, version=LATEST_VER):
    return date.isoformat()


def dump_time(time, version=LATEST_VER):
    return time.isoformat()


def dump_date_time(date_time, version=LATEST_VER):
    tz_name = timezone_name(date_time, version=version)
    return '%s %s' % (date_time.isoformat(), tz_name)


def dump_scalar(scalar, version=LATEST_VER):
    if scalar is None:
        return ''
    elif scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s ' \
                             'does not support NA' \
                             % version)
        return 'NA'
    elif scalar is MARKER:
        return '\u2713'
    elif scalar is REMOVE:
        return 'R'
    elif isinstance(scalar, bool):
        return dump_bool(scalar, version=version)
    elif isinstance(scalar, Ref):
        return dump_ref(scalar, version=version)
    elif isinstance(scalar, Bin):
        return dump_bin(scalar, version=version)
    elif isinstance(scalar, XStr):
        return dump_xstr(scalar, version=version)
    elif isinstance(scalar, Uri):
        return dump_uri(scalar, version=version)
    elif isinstance(scalar, six.string_types):
        return dump_str(scalar, version=version)
    elif isinstance(scalar, datetime.datetime):
        return dump_date_time(scalar, version=version)
    elif isinstance(scalar, datetime.time):
        return dump_time(scalar, version=version)
    elif isinstance(scalar, datetime.date):
        return dump_date(scalar, version=version)
    elif isinstance(scalar, Coordinate):
        return dump_coord(scalar, version=version)
    elif isinstance(scalar, Quantity):
        return dump_quantity(scalar, version=version)
    elif isinstance(scalar, float) or \
            isinstance(scalar, int) or \
            isinstance(scalar, int):
        return dump_decimal(scalar, version=version)
    # FIXME
    # elif isinstance(scalar, list):
    #     return '"' + str_csv_escape(zinc_dump_scalar(scalar, version=version)) + '"'
    # elif isinstance(scalar, dict):
    #     return '"' + str_csv_escape(zinc_dump_scalar(scalar, version=version)) + '"'
    elif isinstance(scalar, Grid):
        return '"' + str_csv_escape("<<" + zinc_dump_grid(scalar) + ">>") + '"'
    else:
        return '"' + str_csv_escape(zinc_dump_scalar(scalar)) + '"'
        # raise NotImplementedError('Unhandled case: %r' % scalar)
