# -*- coding: utf-8 -*-
# JSON Grid Parser
# See the accompanying LICENSE file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Parse Json file conform with the specification describe
here (https://www.project-haystack.org/doc/Json)
and produce a `Grid` instance.
"""

import copy
import datetime
import functools
import json
import re
import sys
from typing import Any, List, Dict, Union

import iso8601

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .metadata import MetadataObject
from .tools import unescape_str
from .type import Entity
from .version import LATEST_VER, Version, VER_3_0
from .zoneinfo import timezone

URI_META = 'Uri'
GRID_SEP = re.compile(r'\n\n+')

# Type regular expressions
MARKER_STR = 'Marker'
NA_STR = 'na'
REMOVE_STR = 'Remove'
NUMBER_STR = 'Num'
REF_RE = 'Ref'
DATE_RE = 'Date'
TIME_RE = 'Time'
DATETIME_RE = 'DateTime'
URI_RE = 'Uri'
BIN_RE = 'Bin'
COORD_RE = 'Coord'


def _parse_metadata(meta: Entity, version: Version) -> MetadataObject:
    metadata = MetadataObject()
    for name, value in meta.items():
        metadata[name] = _parse_embedded_scalar(value, version=version)
    return metadata


def _parse_cols(grid: Grid, parsed: List[Entity], version: Version) -> None:
    for col in parsed:
        name = col.pop('name')
        meta = {}
        for key, value in col.items():
            value = _parse_embedded_scalar(value, version=version)
            if value is not None:
                meta[key] = value
        grid.column[name] = meta


def _parse_row(row: Dict[str, Any], version: Version) -> Entity:
    parsed_row = {}
    for col, value in row.items():
        value = _parse_embedded_scalar(value, version=version)
        if value is not None:
            parsed_row[col] = value
    return parsed_row


def _parse_embedded_scalar(scalar: Union[None, List, Dict, str],
                           version: Version = LATEST_VER) -> Any:  # pylint: disable=too-many-locals
    if isinstance(scalar, dict):
        if isinstance(scalar, list):
            # We support this only in version 3.0 and up.
            if version < VER_3_0:
                raise ValueError('Lists are not supported in Haystack version %s'
                                 % version)
            return list(map(functools.partial(parse_scalar, version=version),
                            scalar))
        if isinstance(scalar, dict):
            # We support this only in version 3.0 and up.
            if version < VER_3_0:
                raise ValueError('Dicts are not supported in Haystack version %s'
                                 % version)
            if sys.version_info[0] < 3 and {"meta", "cols", "rows"} <= scalar.viewkeys() \
                    or {"meta", "cols", "rows"} <= scalar.keys():  # Check if grid in grid
                return parse_grid(scalar)
            return {k: parse_scalar(v, version=version) for (k, v) in scalar.items()}
        kind = scalar.get('_kind')
        if kind:

            if kind == MARKER_STR:
                return MARKER
            if kind == NA_STR:
                return NA
            if kind == REMOVE_STR:
                return REMOVE
            if kind == NUMBER_STR:
                value = scalar.get('val')
                if value == 'INF':
                    return float('INF')
                if value == '-INF':
                    return -float('INF')
                if value == 'NaN':
                    return float('nan')
                else:
                    if scalar.get('unit'):
                        return Quantity(value, scalar.get('unit'))
            # Conversion to dict of float value turn them into float
            # so regex won't work... better just return them
            if isinstance(scalar, (float, int)):
                return scalar


            # Is it a xstr?
            if kind == 'xstr':
                return XStr(*scalar[2:].split(':'))

            # Is it a reference?
            match = REF_RE.match(scalar)
            if match:
                matched = match.groups()
                if matched[-1] is not None:
                    return Ref(matched[0], matched[-1])
                return Ref(matched[0])

            # Is it a date?
            match = DATE_RE.match(scalar)
            if match:
                (year, month, day) = match.groups()
                return datetime.date(year=int(year), month=int(month), day=int(day))

            # Is it a time?
            match = TIME_RE.match(scalar)
            if match:
                (hour, minute, _, second, _) = match.groups()
                # Convert second to seconds and microseconds
                if second is None:
                    sec = 0
                    usec = 0
                elif '.' in second:
                    (whole_sec, frac_sec) = second.split('.', 1)
                    sec = int(whole_sec)
                    usec = int(frac_sec[:6].ljust(6, '0'))
                else:
                    sec = int(second)
                    usec = 0
                return datetime.time(hour=int(hour), minute=int(minute),
                                     second=sec, microsecond=usec)

            # Is it a date/time?
            match = DATETIME_RE.match(scalar)
            if match:
                matches = match.groups()
                # Parse ISO8601 component
                iso_date = iso8601.parse_date(matches[0])
                # Parse timezone
                tzname = matches[-1]
                if tzname is None:
                    return iso_date  # No timezone given
                try:
                    time_zone = timezone(tzname)
                    return iso_date.astimezone(time_zone)
                except TypeError:  # noqa: E722 pragma: no cover
                    # Unlikely code path.
                    return iso_date

            # Is it a URI?
            match = URI_RE.match(scalar)
            if match:
                return Uri(match.group(1))

            # Is it a Bin?
            match = BIN_RE.match(scalar)
            if match:
                return Bin(match.group(1))

            # Is it a co-ordinate?
            match = COORD_RE.match(scalar)
            if match:
                (lat, lng) = match.groups()
                return Coordinate(float(lat), float(lng))
            return scalar
    return scalar

def parse_scalar(scalar: Union[str, bool, float, int, list, dict], version: Version = LATEST_VER) -> Any:
    """
    Parse a scalar.
    Args:
        scalar: The string with the scalar value.
        version: The Haysack version
    Returns:
        The scalar value.
    """
    if scalar is None:
        return None
    if isinstance(scalar, (bool, float, int)):
        return scalar
    if isinstance(scalar, str):
        scalar = unescape_str(scalar)
    if isinstance(scalar, str) and \
            (len(scalar) >= 2) and \
            (scalar[0] in ('"', '[', '{')) and \
            (scalar[-1] in ('"', ']', '}')):
        scalar = json.loads(scalar)

    return _parse_embedded_scalar(scalar, version=version)


def parse_grid(grid_str: Union[str, Dict[str, Any]]) -> Grid:
    """
    Parse a grid from json string.
    Args:
        grid_str: The json string
    Returns:
        The corresponding grid.
    """
    if isinstance(grid_str, str):
        parsed = json.loads(grid_str)
    else:
        parsed = copy.deepcopy(grid_str)
    meta = parsed.pop('meta')
    # Decode version
    version = Version(meta.pop('ver'))

    # Parse the remaining elements
    metadata = _parse_metadata(meta, version)

    grid = Grid(version=version, metadata=metadata)

    # Grab the columns in the order given
    _parse_cols(grid, parsed.pop('cols'), version)

    # Parse the rows
    for row in (parsed.pop('rows', []) or []):
        parsed_row = _parse_row(row, version)
        grid.append(parsed_row)

    return grid
