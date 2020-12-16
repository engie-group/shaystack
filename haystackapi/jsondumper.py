#!/usr/bin/python
# -*- coding: utf-8 -*-
# JSON Grid dumper
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Save a `Grid` in JSON file, conform with the specification describe
here (https://www.project-haystack.org/doc/Json)
"""
from __future__ import unicode_literals

import datetime
import functools
import json

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .jsonparser import MARKER_STR, NA_STR, REMOVE2_STR, REMOVE3_STR
from .version import LATEST_VER, VER_3_0
from .zoneinfo import timezone_name


def dump_grid(grid):
    return json.dumps(_dump_grid_to_json(grid))


def _dump_grid_to_json(grid):
    return {
        'meta': dump_meta(grid.metadata, version=grid.version, grid=True),
        'cols': dump_columns(grid.column, version=grid.version),
        'rows': dump_rows(grid),
    }


def dump_meta(meta, version=LATEST_VER, grid=False):
    _dump = functools.partial(dump_meta_item, version=version)
    _meta = dict(map(_dump, list(meta.items())))
    if grid:
        _meta['ver'] = str(version)
    return _meta


def dump_meta_item(item, version=LATEST_VER):
    (item_id, item_value) = item
    return (dump_id(item_id),
            dump_scalar(item_value, version=version))


def dump_columns(cols, version=LATEST_VER):
    _dump = functools.partial(dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    return list(map(_dump, *_cols))


def dump_column(col, col_meta, version=LATEST_VER):
    if bool(col_meta):
        _meta = dump_meta(col_meta, version=version)
    else:
        _meta = {}
    _meta['name'] = col
    return _meta


def dump_rows(grid):
    return list(map(functools.partial(dump_row, grid), grid))


def dump_row(grid, row):
    return {
        c: dump_scalar(row.get(c), version=grid.version)
        for c in list(grid.column.keys()) if c in row}


def dump_scalar(scalar, version=LATEST_VER):
    if scalar is None:
        return None
    if scalar is MARKER:
        return MARKER_STR
    if scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack %s '
                             'does not support NA' % version)
        return NA_STR
    if scalar is REMOVE:
        if version < VER_3_0:
            return REMOVE2_STR
        return REMOVE3_STR
    if isinstance(scalar, list):
        return dump_list(scalar, version=version)
    if isinstance(scalar, dict):
        return dump_dict(scalar, version=version)
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
        return dump_date_time(scalar)
    if isinstance(scalar, datetime.time):
        return dump_time(scalar)
    if isinstance(scalar, datetime.date):
        return dump_date(scalar)
    if isinstance(scalar, Coordinate):
        return dump_coord(scalar)
    if isinstance(scalar, Quantity):
        return dump_quantity(scalar)
    if isinstance(scalar, (float, int)):
        return dump_decimal(scalar)
    if isinstance(scalar, Grid):
        return _dump_grid_to_json(scalar)
    raise NotImplementedError('Unhandled case: %r' % scalar)


def dump_id(id_str):
    return id_str


def dump_str(str_value):
    return u's:%s' % str_value


def dump_uri(uri_value):
    return u'u:%s' % uri_value


def dump_bin(bin_value):
    return u'b:%s' % bin_value


def dump_xstr(xstr_value):
    return u'x:%s:%s' % (xstr_value.encoding, xstr_value.data_to_string())


def dump_quantity(quantity):
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.value)
    return 'n:%f %s' % (quantity.value, quantity.unit)


def dump_decimal(decimal):
    return 'n:%f' % decimal


def dump_bool(bool_value):
    return bool_value


def dump_coord(coordinate):
    return 'c:%f,%f' % (coordinate.latitude, coordinate.longitude)


def dump_ref(ref):
    if ref.has_value:
        return u'r:%s %s' % (ref.name, ref.value)
    return u'r:%s' % ref.name


def dump_date(date):
    return 'd:%s' % date.isoformat()


def dump_time(time):
    return 'h:%s' % time.isoformat()


def dump_date_time(date_time):
    tz_name = timezone_name(date_time)
    return 't:%s %s' % (date_time.isoformat(), tz_name)


def dump_list(lst, version=LATEST_VER):
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support lists' % version)
    return list(map(functools.partial(dump_scalar, version=version), lst))


def dump_dict(dic, version=LATEST_VER):
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support dict' % version)
    return {k: dump_scalar(v, version=version) for (k, v) in dic.items()}
