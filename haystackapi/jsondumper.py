# -*- coding: utf-8 -*-
# JSON Grid dumper
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
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
from typing import Dict, Optional, Tuple, List, Any, Union

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .jsonparser import MARKER_STR, NA_STR, REMOVE2_STR, REMOVE3_STR
from .metadata import MetadataObject
from .sortabledict import SortableDict
from .version import LATEST_VER, VER_3_0, Version
from .zoneinfo import timezone_name


def dump_grid(grid: Grid) -> str:
    """
    Args:
        grid (Grid):
    """
    return json.dumps(_dump_grid_to_json(grid))


def _dump_grid_to_json(grid: Grid) -> Dict[str, Union[List[str], Dict[str, str]]]:
    """
    Args:
        grid (Grid):
    """
    return {
        'meta': dump_meta(grid.metadata, version=grid.version, for_grid=True),
        'cols': dump_columns(grid.column, version=grid.version),
        'rows': dump_rows(grid),
    }


def dump_meta(meta: MetadataObject,
              version: Version = LATEST_VER,
              for_grid: Optional[bool] = False) -> Dict[str, str]:
    """
    Args:
        meta (MetadataObject):
        version (Version):
        for_grid:
    """
    _dump = functools.partial(dump_meta_item, version=version)
    _meta = dict(map(_dump, list(meta.items())))
    if for_grid:
        _meta['ver'] = str(version)
    return _meta


def dump_meta_item(item: str, version: Version = LATEST_VER) \
        -> Tuple[str, Union[None, bool, str, List[str], Dict[str, Any]]]:
    """
    Args:
        item (str):
        version (Version):
    """
    (item_id, item_value) = item
    return (dump_id(item_id),
            _dump_scalar(item_value, version=version))


def dump_columns(cols: SortableDict, version: Version = LATEST_VER) -> List[str]:
    """
    Args:
        cols (SortableDict):
        version (Version):
    """
    _dump = functools.partial(dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    return list(map(_dump, *_cols))


def dump_column(col: str, col_meta: MetadataObject, version: Version = LATEST_VER) -> Dict[str, str]:
    """
    Args:
        col (str):
        col_meta (MetadataObject):
        version (Version):
    """
    if bool(col_meta):
        _meta = dump_meta(col_meta, version=version)
    else:
        _meta = {}
    _meta['name'] = col
    return _meta


def dump_rows(grid: Grid) -> List[str]:
    """
    Args:
        grid (Grid):
    """
    return list(map(functools.partial(dump_row, grid), grid))


def dump_row(grid: Grid, row: Dict[str, Any]) -> Dict[str, str]:
    """
    Args:
        grid (Grid):
        row:
    """
    return {
        c: _dump_scalar(row.get(c), version=grid.version)
        for c in list(grid.column.keys()) if c in row
    }


def _dump_scalar(scalar: Any, version: Version = LATEST_VER) \
        -> Union[None, str, bool, List[str], Dict[str, Any]]:
    """
    Args:
        scalar (Any):
        version (Version):
    """
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


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Args:
        scalar (Any):
        version (Version):
    """
    return json.dumps(_dump_scalar(scalar, version))


def dump_id(id_str: str) -> str:
    """
    Args:
        id_str (str):
    """
    return id_str


def dump_str(str_value: str) -> str:
    """
    Args:
        str_value (str):
    """
    return 's:%s' % str_value


def dump_uri(uri_value: Uri) -> str:
    """
    Args:
        uri_value (Uri):
    """
    return 'u:%s' % uri_value


def dump_bin(bin_value: Bin) -> str:
    """
    Args:
        bin_value (Bin):
    """
    return 'b:%s' % bin_value


def dump_xstr(xstr_value: XStr) -> str:
    """
    Args:
        xstr_value (XStr):
    """
    return 'x:%s:%s' % (xstr_value.encoding, xstr_value.data_to_string())


def dump_quantity(quantity: Quantity) -> str:
    """
    Args:
        quantity (Quantity):
    """
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.m)
    return 'n:%f %s' % (quantity.m, quantity.unit)


def dump_decimal(decimal: float) -> str:
    """
    Args:
        decimal (float):
    """
    return 'n:%f' % decimal


def dump_bool(bool_value: bool) -> bool:
    """
    Args:
        bool_value (bool):
    """
    return bool_value


def dump_coord(coordinate: Coordinate) -> str:
    """
    Args:
        coordinate (Coordinate):
    """
    return 'c:%f,%f' % (coordinate.latitude, coordinate.longitude)


def dump_ref(ref: Ref) -> str:
    """
    Args:
        ref (Ref):
    """
    if ref.has_value:
        return 'r:%s %s' % (ref.name, ref.value)
    return 'r:%s' % ref.name


def dump_date(date: datetime.date) -> str:
    """
    Args:
        date (datetime.date):
    """
    return 'd:%s' % date.isoformat()


def dump_time(time: datetime.time) -> str:
    """
    Args:
        time (datetime.time):
    """
    return 'h:%s' % time.isoformat()


def dump_date_time(date_time: datetime.datetime) -> str:
    """
    Args:
        date_time (datetime.datetime):
    """
    tz_name = timezone_name(date_time)
    return 't:%s %s' % (date_time.isoformat(), tz_name)


def dump_list(lst: List[Any], version: Version = LATEST_VER) -> List[str]:
    """
    Args:
        lst:
        version (Version):
    """
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support lists' % version)
    return list(map(functools.partial(_dump_scalar, version=version), lst))


def dump_dict(dic: Dict[str, Any], version: Version = LATEST_VER) -> Dict[str, str]:
    """
    Args:
        dic:
        version (Version):
    """
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support dict' % version)
    return {k: _dump_scalar(v, version=version) for (k, v) in dic.items()}
