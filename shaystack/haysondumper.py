# -*- coding: utf-8 -*-
# JSON Grid dumper
# See the accompanying LICENSE file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Save a `Grid` in Hayson file, conform with the specification describe
here (https://project-haystack.org/forum/topic/792)
"""
from __future__ import unicode_literals

import datetime
import functools
import json
from typing import Dict, Optional, Tuple, List, Any, Union

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .haysonparser import MARKER_STR, REMOVE_STR
from .metadata import MetadataObject
from .sortabledict import SortableDict
from .type import Entity
from .version import LATEST_VER, VER_3_0, Version
from .zoneinfo import timezone_name


def dump_grid(grid: Grid) -> str:
    """
    Dump a grid to JSON
    Args:
        grid: The grid.
    Returns:
        A json string
    """
    return json.dumps(_dump_grid_to_hayson(grid))


def _dump_grid_to_hayson(grid: Grid) -> Dict[str, Union[List[str], Dict[str, str]]]:
    """
    Convert a grid to JSON object
    Args:
        grid: The grid to dump
    Returns:
        A json object.
    """

    return {
        'meta': _dump_meta(grid.metadata, version=grid.version, for_grid=True),
        'cols': _dump_columns(grid.column, version=grid.version),
        'rows': _dump_rows(grid),
    }


def _dump_meta(meta: MetadataObject,
               version: Version = LATEST_VER,
               for_grid: Optional[bool] = False) -> Dict[str, str]:
    _dump = functools.partial(_dump_meta_item, version=version)
    _meta = dict(map(_dump, list(meta.items())))
    if for_grid:
        _meta['ver'] = str(version)
    return _meta  # type: ignore


def _dump_meta_item(item: str, version: Version = LATEST_VER) \
        -> Tuple[str, Union[None, bool, str, float, List[str], Entity]]:
    (item_id, item_value) = item  # type: ignore
    return (_dump_id(item_id),  # type: ignore
            _dump_scalar(item_value, version=version))  # type: ignore


def _dump_columns(cols: SortableDict, version: Version = LATEST_VER) -> List[str]:
    _dump = functools.partial(_dump_column, version=version)
    _cols = list(zip(*list(cols.items())))
    if not _cols:
        raise ValueError("Empty columns is not valide. Use `grid.extends_columns()`")
    return list(map(_dump, *_cols))  # type: ignore


def _dump_column(col: str, col_meta: MetadataObject, version: Version = LATEST_VER) -> Dict[str, str]:
    if bool(col_meta):
        _meta = _dump_meta(col_meta, version=version)
    else:
        _meta = {}
    _meta['name'] = col
    return _meta


def _dump_rows(grid: Grid) -> List[str]:
    return list(map(functools.partial(_dump_row, grid), grid))  # type: ignore


def _dump_row(grid: Grid, row: Entity) -> Dict[str, str]:
    return {
        c: _dump_scalar(row.get(c), version=grid.version)  # type: ignore
        for c in list(grid.column.keys()) if c in row
    }


def _dump_scalar(scalar: Any, version: Version = LATEST_VER) \
        -> Union[None, str, bool, float, List[str], Entity]:
    if scalar is None:
        return None
    if scalar is MARKER:
        return _dump_marker()
    if scalar is REMOVE:
        return _dump_remove()
    if scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack %s '
                             'does not support NA' % version)
        return _dump_na()
    if isinstance(scalar, list):
        return _dump_list(scalar, version=version)
    if isinstance(scalar, dict):
        return _dump_dict(scalar, version=version)  # type: ignore
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
    if isinstance(scalar, Grid):
        return _dump_grid_to_hayson(scalar)  # type: ignore
    raise NotImplementedError('Unhandled case: %r' % scalar)


def _dump_id(id_str: str) -> str:
    return id_str


def _dump_na() -> Dict:
    return {'_kind': 'NA'}


def _dump_marker() -> Dict:
    return {'_kind': MARKER_STR}


def _dump_str(str_value: str) -> str:
    return str_value


def _dump_uri(uri_value: Uri) -> Dict:
    return {
        "_kind": "Uri",
        "val": uri_value
    }

# TO CHALLENGE
def _dump_bin(bin_value: Bin) -> Dict:
    return {
        "_kind": "Bin",
        "val": bin_value
    }


def _dump_remove() -> Dict:
    return {"_kind": REMOVE_STR}


def _dump_xstr(xstr_value: XStr) -> Dict:
    return {
        "_kind": "XStr",
        "type": xstr_value.encoding,
        "val": xstr_value.data_to_string()
    }


def _dump_quantity(quantity: Quantity) -> Union[Dict, float]:
    if (quantity.units is None) or (quantity.units == ''):
        return _dump_decimal(quantity.m)
    return {
        "_kind": "Num",
        "val": quantity.m,
        "unit": str(quantity.symbol)
    }


def _dump_decimal(decimal: float) -> float:
    return decimal


def _dump_bool(bool_value: bool) -> bool:
    return bool_value


def _dump_coord(coordinate: Coordinate) -> Dict:
    return {
        "_kind": "Coord",
        "lat": coordinate.latitude,
        "lng": coordinate.longitude
    }


def _dump_ref(ref: Ref) -> Dict:
    if ref.has_value:
        return {
            "_kind": "Ref",
            "val": ref.name,
            "dis": ref.value
        }
    return {
        "_kind": "Ref",
        "val": ref.name
    }


def _dump_date(date: datetime.date) -> Dict:
    return {
        "_kind": "Date",
        "val": date.isoformat()
    }

def _dump_time(time: datetime.time) -> Dict:
    return {
        "_kind": "Time",
        "val": time.isoformat()
    }


def _dump_date_time(date_time: datetime.datetime) -> Dict:
    tz_name = timezone_name(date_time)
    return {
        "_kind": "DateTime",
        "val": date_time.isoformat(),
        "tz": tz_name
    }


def _dump_list(lst: List[Any], version: Version = LATEST_VER) -> List[str]:
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support lists' % version)
    return list(map(functools.partial(_dump_scalar, version=version), lst))  # type: ignore


def _dump_dict(dic: Dict[str, Any], version: Version = LATEST_VER) -> Dict[str, str]:
    if version < VER_3_0:
        raise ValueError('Project Haystack %s '
                         'does not support dict' % version)
    return {k: _dump_scalar(v, version=version) for (k, v) in dic.items()}  # type: ignore


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Dump a scalar to JSON
    Args:
        scalar: The scalar value
        version: The Haystack version
    Returns:
        The JSON string
    """
    return json.dumps(_dump_scalar(scalar, version))
