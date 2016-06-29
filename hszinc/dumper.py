#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid dumper
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from .grid import Grid
from .sortabledict import SortableDict
from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
        MARKER, REMOVE, STR_SUB
from .zoneinfo import timezone_name
from .parser import MODE_ZINC, MODE_JSON, MARKER_STR

import datetime
import iso8601
import re
import functools
import json
import six

URI_META = re.compile(six.u(r'([\\`\u0080-\uffff])'))
STR_META = re.compile(six.u(r'([\\"\$\u0080-\uffff])'))

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

def dump(grids, mode=MODE_ZINC):
    '''
    Parse the given Zinc text and return the equivalent data.
    '''
    if isinstance(grids, Grid):
        return dump_grid(grids, mode=mode)
    _dump = functools.partial(dump_grid, mode=mode)
    if mode == MODE_ZINC:
        return '\n'.join(map(_dump, grids))
    elif mode == MODE_JSON:
        return '[%s]' % ','.join(map(_dump, grids))
    else: # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)

def dump_grid(grid, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        header = 'ver:%s' % dump_str(grid._version)
        if bool(grid.metadata):
            header += ' ' + dump_meta(grid.metadata)
        columns = dump_columns(grid.column)
        rows = dump_rows(grid)
        return '\n'.join([header, columns] + rows + [''])
    elif mode == MODE_JSON:
        return json.dumps({
            'meta': dump_meta(grid.metadata, version=grid._version,
                mode=mode),
            'cols': dump_columns(grid.column, mode=mode),
            'rows': dump_rows(grid, mode=mode),
        })
    else: # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)

def dump_meta(meta, version=None, mode=MODE_ZINC):
    _dump = functools.partial(dump_meta_item, mode=mode)
    if mode == MODE_ZINC:
        return ' '.join(map(_dump, list(meta.items())))
    else:
        _meta = dict(map(_dump, list(meta.items())))
        if version is not None:
            _meta['ver'] = version
        return _meta

def dump_meta_item(item, mode=MODE_ZINC):
    (item_id, item_value) = item
    if mode == MODE_ZINC:
        if item_value is MARKER:
            return dump_id(item_id, mode=mode)
        else:
            return '%s:%s' % (dump_id(item_id, mode=mode), \
                    dump_scalar(item_value, mode=mode))
    elif mode == MODE_JSON:
        return (dump_id(item_id, mode=mode), \
                dump_scalar(item_value, mode=mode))

def dump_columns(cols, mode=MODE_ZINC):
    _dump = functools.partial(dump_column, mode=mode)
    _cols = list(zip(*list(cols.items())))
    if mode == MODE_ZINC:
        return ','.join(map(_dump, *_cols))
    elif mode == MODE_JSON:
        return list(map(_dump, *_cols))

def dump_column(col, col_meta, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        if bool(col_meta):
            return '%s %s' % (dump_id(col, mode=mode), \
                    dump_meta(col_meta, mode=mode))
        else:
            return dump_id(col, mode=mode)
    elif mode == MODE_JSON:
        if bool(col_meta):
            _meta = dump_meta(col_meta, mode=mode)
        else:
            _meta = {}
        _meta['name'] = col
        return _meta

def dump_rows(grid, mode=MODE_ZINC):
    return [dump_row(grid, r, mode=mode) for r in grid]

def dump_row(grid, row, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        return ','.join([dump_scalar(row.get(c), mode=mode) for \
                c in list(grid.column.keys())])
    elif mode == MODE_JSON:
        return dict([
            (c, dump_scalar(row.get(c), mode=mode))
            for c in list(grid.column.keys())])

def dump_scalar(scalar, mode=MODE_ZINC):
    if scalar is None:
        if mode == MODE_ZINC:
            return 'N'
        elif mode == MODE_JSON:
            return None
        else: # pragma: no cover
            raise NotImplementedError('Unhandled case: %r' % scalar)
    elif scalar is MARKER:
        if mode == MODE_ZINC:
            return 'M'
        elif mode == MODE_JSON:
            return MARKER_STR
        else: # pragma: no cover
            raise NotImplementedError('Unhandled case: %r' % scalar)
    elif scalar is REMOVE:
        if mode == MODE_ZINC:
            return 'R'
        else: # pragma: no cover
            raise NotImplementedError('Unhandled case: %r' % scalar)
    elif isinstance(scalar, bool):
        return dump_bool(scalar, mode=mode)
    elif isinstance(scalar, Ref):
        return dump_ref(scalar, mode=mode)
    elif isinstance(scalar, Bin):
        return dump_bin(scalar, mode=mode)
    elif isinstance(scalar, Uri):
        return dump_uri(scalar, mode=mode)
    elif isinstance(scalar, six.string_types):
        return dump_str(scalar, mode=mode)
    elif isinstance(scalar, datetime.datetime):
        return dump_date_time(scalar, mode=mode)
    elif isinstance(scalar, datetime.time):
        return dump_time(scalar, mode=mode)
    elif isinstance(scalar, datetime.date):
        return dump_date(scalar, mode=mode)
    elif isinstance(scalar, Coordinate):
        return dump_coord(scalar, mode=mode)
    elif isinstance(scalar, Quantity):
        return dump_quantity(scalar, mode=mode)
    elif isinstance(scalar, float) or \
            isinstance(scalar, int) or \
            isinstance(scalar, int):
        return dump_decimal(scalar, mode=mode)
    else: # pragma: no cover
        raise NotImplementedError('Unhandled case: %r' % scalar)

def dump_id(id_str, mode=MODE_ZINC):
    return id_str

def dump_str(str_value, mode=MODE_ZINC):
    if mode == MODE_JSON:
        return u's:%s' % str_value
    elif mode == MODE_ZINC:
        # Replace special characters.
        str_value = STR_META.sub(str_sub, str_value)
        # Replace other escapes.
        for orig, esc in STR_SUB:
            str_value = str_value.replace(orig, esc)
        return '"%s"' % str_value

def dump_uri(uri_value, mode=MODE_ZINC):
    if mode == MODE_JSON:
        return u'u:%s' % uri_value
    elif mode == MODE_ZINC:
        # Replace special characters.
        uri_value = URI_META.sub(uri_sub, uri_value)
        # Replace other escapes.
        for orig, esc in STR_SUB:
            uri_value = uri_value.replace(orig, esc)
        return '`%s`' % uri_value

def dump_bin(bin_value, mode=MODE_ZINC):
    if mode == MODE_JSON:
        return u'b:%s' % bin_value
    elif mode == MODE_ZINC:
        return 'Bin(%s)' % bin_value

def dump_quantity(quantity, mode=MODE_ZINC):
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.value, mode=mode)
    elif mode == MODE_ZINC:
        return '%s%s' % (dump_decimal(quantity.value), quantity.unit)
    elif mode == MODE_JSON:
        return 'n:%f %s' % (quantity.value, quantity.unit)

def dump_decimal(decimal, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        return str(decimal)
    elif mode == MODE_JSON:
        return 'n:%f' % decimal

def dump_bool(bool_value, mode=MODE_ZINC):
    if mode == MODE_JSON:
        return bool_value
    elif mode == MODE_ZINC:
        return 'T' if bool(bool_value) else 'F'

def dump_coord(coordinate, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        return 'C(%f,%f)' % (coordinate.latitude, coordinate.longitude)
    elif mode == MODE_JSON:
        return 'c:%f,%f' % (coordinate.latitude, coordinate.longitude)

def dump_ref(ref, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        if ref.has_value:
            return '@%s %s' % (ref.name, dump_str(ref.value))
        else:
            return '@%s' % ref.name
    elif mode == MODE_JSON:
        if ref.has_value:
            return u'r:%s %s' % (ref.name, ref.value)
        else:
            return u'r:%s' % ref.name

def dump_date(date, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        return date.isoformat()
    elif mode == MODE_JSON:
        return 'd:%s' % date.isoformat()

def dump_time(time, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        return time.isoformat()
    elif mode == MODE_JSON:
        return 'h:%s' % time.isoformat()

def dump_date_time(date_time, mode=MODE_ZINC):
    tz_name = timezone_name(date_time)
    if mode == MODE_ZINC:
        return '%s %s' % (date_time.isoformat(), tz_name)
    elif mode == MODE_JSON:
        return 't:%s %s' % (date_time.isoformat(), tz_name)
