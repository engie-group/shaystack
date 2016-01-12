#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid dumper
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from .grid import Grid
from .sortabledict import SortableDict
from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, MARKER, STR_SUB
from .zoneinfo import timezone_name
import datetime
import iso8601
import re

URI_META = re.compile(r'([\\`])')
STR_META = re.compile(r'([\\"$])')

def dump(grids):
    '''
    Parse the given Zinc text and return the equivalent data.
    '''
    if isinstance(grids, Grid):
        return dump_grid(grids)
    return '\n'.join(map(dump_grid, grids))

def dump_grid(grid):
    header = 'ver:%s' % dump_str(grid._version)
    if bool(grid.metadata):
        header += ' ' + dump_meta(grid.metadata)
    columns = dump_columns(grid.column)
    rows = dump_rows(grid)
    return '\n'.join([header, columns] + rows + [''])

def dump_meta(meta):
    return ' '.join(map(dump_meta_item, list(meta.items())))

def dump_meta_item(item):
    (item_id, item_value) = item
    if item_value is MARKER:
        return dump_id(item_id)
    else:
        return '%s:%s' % (dump_id(item_id), dump_scalar(item_value))

def dump_columns(cols):
    return ','.join(map(dump_column, *list(zip(*list(cols.items())))))

def dump_column(col, col_meta):
    if bool(col_meta):
        return '%s %s' % (dump_id(col), dump_meta(col_meta))
    else:
        return dump_id(col)

def dump_rows(grid):
    return [dump_row(grid, r) for r in grid]

def dump_row(grid, row):
    return ','.join([dump_scalar(row.get(c)) for c in list(grid.column.keys())])

def dump_scalar(scalar):
    if scalar is None:
        return 'N'
    elif scalar is MARKER:
        return 'M'
    elif isinstance(scalar, bool):
        return dump_bool(scalar)
    elif isinstance(scalar, Ref):
        return dump_ref(scalar)
    elif isinstance(scalar, Bin):
        return dump_bin(scalar)
    elif isinstance(scalar, Uri):
        return dump_uri(scalar)
    elif isinstance(scalar, str):
        return dump_str(scalar)
    elif isinstance(scalar, datetime.datetime):
        return dump_date_time(scalar)
    elif isinstance(scalar, datetime.time):
        return dump_time(scalar)
    elif isinstance(scalar, datetime.date):
        return dump_date(scalar)
    elif isinstance(scalar, Coordinate):
        return dump_coord(scalar)
    elif isinstance(scalar, Quantity):
        return dump_quantity(scalar)
    elif isinstance(scalar, float) or \
            isinstance(scalar, int) or \
            isinstance(scalar, int):
        return dump_decimal(scalar)
    else:
        raise NotImplementedError('Unhandled case: %r' % scalar)

def dump_id(id_str):
    return id_str

def dump_str(str_value):
    # Replace special characters.
    str_value = STR_META.sub(r'\\\1', str_value)
    # Replace other escapes.
    for orig, esc in STR_SUB:
        str_value = str_value.replace(orig, esc)
    return '"%s"' % str_value

def dump_uri(uri_value):
    # Replace special characters.
    uri_value = URI_META.sub(r'\\\1', uri_value)
    # Replace other escapes.
    for orig, esc in STR_SUB:
        uri_value = uri_value.replace(orig, esc)
    return '`%s`' % uri_value

def dump_bin(bin_value):
    return 'Bin(%s)' % bin_value

def dump_quantity(quantity):
    if quantity.unit is None:
        return dump_decimal(quantity.value)
    else:
        return '%s%s' % (dump_decimal(quantity.value), quantity.unit)

def dump_decimal(decimal):
    return str(decimal)

def dump_bool(bool_value):
    return 'T' if bool(bool_value) else 'F'

def dump_coord(coordinate):
    return 'C(%f,%f)' % (coordinate.latitude, coordinate.longitude)

def dump_ref(ref):
    if ref.has_value:
        return '@%s %s' % (ref.name, dump_str(ref.value))
    else:
        return '@%s' % ref.name

def dump_date(date):
    return date.isoformat()

def dump_time(time):
    return time.isoformat()

def dump_date_time(date_time):
    tz_name = timezone_name(date_time)
    return '%s %s' % (date_time.isoformat(), tz_name)
