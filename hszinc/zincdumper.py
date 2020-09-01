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

from . import Grid
from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, STR_SUB, XStr
from .version import LATEST_VER, VER_3_0
from .zoneinfo import timezone_name

URI_META = re.compile(r'([\\`\u0080-\uffff])')
STR_META = re.compile(r'([\\"\$\u0080-\uffff])')


def str_sub(match):
    c = match.group(0)
    o = ord(c)
    if o >= 0x0080:
        # Unicode
        return '\\u%04x' % o
    elif c in '\\"$':
        return '\\%s' % c


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
    Dump a single grid to its ZINC representation.
    """
    header = 'ver:%s' % dump_str(str(grid._version), version=grid._version)
    if bool(grid.metadata):
        header += ' ' + dump_meta(grid.metadata, version=grid._version)
    columns = dump_columns(grid.column, version=grid._version)
    rows = dump_rows(grid)
    return '\n'.join([header, columns] + rows + [''])


def dump_meta(meta, version=LATEST_VER):
    _dump = functools.partial(dump_meta_item, version=version)
    return ' '.join(map(_dump, list(meta.items())))


def dump_meta_item(item, version=LATEST_VER):
    (item_id, item_value) = item
    if item_value is MARKER:
        return dump_id(item_id, version=version)
    else:
        return '%s:%s' % (dump_id(item_id, version=version), \
                          dump_scalar(item_value, version=version))


def dump_columns(cols, version=LATEST_VER):
    _dump = functools.partial(dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    return ','.join(map(_dump, *_cols))


def dump_column(col, col_meta, version=LATEST_VER):
    if bool(col_meta):
        return '%s %s' % (dump_id(col, version=version), \
                          dump_meta(col_meta, version=version))
    else:
        return dump_id(col, version=version)


def dump_rows(grid):
    return list(map(functools.partial(dump_row, grid), grid))


def dump_row(grid, row):
    return ','.join([dump_scalar(row.get(c), version=grid.version) for \
                     c in list(grid.column.keys())])


def dump_scalar(scalar, version=LATEST_VER):
    if scalar is None:
        return 'N'
    elif scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s ' \
                             'does not support NA' \
                             % version)
        return 'NA'
    elif scalar is MARKER:
        return 'M'
    elif scalar is REMOVE:
        return 'R'
    elif isinstance(scalar, list):
        # Forbid version 2.0 and earlier.
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s ' \
                             'does not support lists' \
                             % version)
        return '[%s]' % ','.join(map(
            functools.partial(dump_scalar, version=version),
            scalar))
    elif isinstance(scalar, dict):
        # Forbid version 2.0 and earlier.
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s ' \
                             'does not support dicts' \
                             % version)
        return '{' + ' '.join([k + ':' + dump_scalar(v, version=version) for (k, v) in scalar.items()]) + '}'
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
    elif isinstance(scalar, Grid):
        return "<<" + dump_grid(scalar) + ">>"
    else:
        raise NotImplementedError('Unhandled case: %r' % scalar)


def dump_id(id_str, version=LATEST_VER):
    return id_str


def dump_str(str_value, version=LATEST_VER):
    # Replace special characters.
    str_value = STR_META.sub(str_sub, str_value)
    # Replace other escapes.
    for orig, esc in STR_SUB:
        str_value = str_value.replace(orig, esc)
    return '"%s"' % str_value


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
    return str(xstr_value)


def dump_quantity(quantity, version=LATEST_VER):
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.value, version=version)
    else:
        return '%s%s' % (dump_decimal(quantity.value),
                         quantity.unit)


def dump_decimal(decimal, version=LATEST_VER):
    return str(decimal)


def dump_bool(bool_value, version=LATEST_VER):
    return 'T' if bool(bool_value) else 'F'


def dump_coord(coordinate, version=LATEST_VER):
    return 'C(%f,%f)' % (coordinate.latitude, coordinate.longitude)


def dump_ref(ref, version=LATEST_VER):
    if ref.has_value:
        return '@%s %s' % (ref.name, dump_str(ref.value))
    else:
        return '@%s' % ref.name


def dump_date(date, version=LATEST_VER):
    return date.isoformat()


def dump_time(time, version=LATEST_VER):
    return time.isoformat()


def dump_date_time(date_time, version=LATEST_VER):
    tz_name = timezone_name(date_time, version=version)
    return '%s %s' % (date_time.isoformat(), tz_name)
