#!/usr/bin/python
# -*- coding: utf-8 -*-
# JSON Grid Parser
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import copy
import datetime
import functools
import json
import re
import sys

import iso8601
import six

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, XStr
from .grid import Grid
from .version import LATEST_VER, Version, VER_3_0
from .zoneinfo import timezone

URI_META = re.compile(r'\\([:/\?#\[\]@\\&=;"$`])')
GRID_SEP = re.compile(r'\n\n+')

# Type regular expressions
MARKER_STR = 'm:'
NA_STR = 'z:'
REMOVE2_STR = 'x:'
REMOVE3_STR = '-:'
NUMBER_RE = re.compile(r'^n:(-?\d+(:?\.\d+)?(:?[eE][+\-]?\d+)?)(:? (.*))?$',
                       flags=re.MULTILINE)
REF_RE = re.compile(r'^r:([a-zA-Z0-9_:\-.~]+)(:? (.*))?$',
                    flags=re.MULTILINE)
DATE_RE = re.compile(r'^d:(\d{4})-(\d{2})-(\d{2})$', flags=re.MULTILINE)
TIME_RE = re.compile(r'^h:(\d{2}):(\d{2})(:?:(\d{2}(:?\.\d+)?))?$',
                     flags=re.MULTILINE)
DATETIME_RE = re.compile(r'^t:(\d{4}-\d{2}-\d{2}T' \
                         r'\d{2}:\d{2}(:?:\d{2}(:?\.\d+)?)' \
                         r'(:?[zZ]|[+\-]\d+:?\d*))(:? ([A-Za-z\-+_0-9]+))?$',
                         flags=re.MULTILINE)
URI_RE = re.compile(r'u:(.+)$', flags=re.MULTILINE)
BIN_RE = re.compile(r'b:(.+)$', flags=re.MULTILINE)
COORD_RE = re.compile(r'c:(-?\d*\.?\d*),(-?\d*\.?\d*)$',
                      flags=re.MULTILINE)

STR_ESC_RE = re.compile(r'\\([bfnrt"\\$]|u[0-9a-fA-F]{4})')


def parse_grid(grid_str):
    # Grab the metadata
    if isinstance(grid_str, six.string_types):
        parsed = json.loads(grid_str)
    else:
        parsed = copy.deepcopy(grid_str)
    meta = parsed.pop('meta')
    # Decode version
    version = Version(meta.pop('ver'))

    # Parse the remaining elements
    metadata = {}
    for name, value in meta.items():
        metadata[name] = parse_embedded_scalar(value, version=version)

    grid = Grid(version=version, metadata=metadata)

    # Grab the columns in the order given
    for col in parsed.pop('cols'):
        name = col.pop('name')
        meta = {}
        for key, value in col.items():
            meta[key] = parse_embedded_scalar(value, version=version)
        grid.column[name] = meta

    # Parse the rows
    for row in (parsed.pop('rows', []) or []):
        parsed_row = {}
        for col, value in row.items():
            parsed_row[col] = parse_embedded_scalar(value, version=version)
        grid.append(parsed_row)

    return grid


def parse_embedded_scalar(scalar, version=LATEST_VER):
    # Simple cases
    if scalar is None:
        return None
    elif isinstance(scalar, list):
        # We support this only in version 3.0 and up.
        if version < VER_3_0:
            raise ValueError('Lists are not supported in Haystack version %s' \
                             % version)
        return list(map(functools.partial(parse_scalar, version=version),
                        scalar))
    elif isinstance(scalar, dict):
        # We support this only in version 3.0 and up.
        if version < VER_3_0:
            raise ValueError('Dicts are not supported in Haystack version %s' \
                             % version)
        if sys.version_info[0] < 3 and {"meta", "cols", "rows"} <= scalar.viewkeys() \
                or {"meta", "cols", "rows"} <= scalar.keys():  # Check if grid in grid
            return parse_grid(scalar)
        else:
            return {k: parse_scalar(v, version=version) for (k, v) in scalar.items()}
    elif scalar == MARKER_STR:
        return MARKER
    elif scalar == NA_STR:
        return NA
    elif (scalar == REMOVE2_STR) or (scalar == REMOVE3_STR):
        # Strictly speaking: x: is a HS 2.0 Remove, and -: is a 3.0 Remove
        # but we'll treat both the same.
        return REMOVE
    elif isinstance(scalar, bool):
        return scalar
    elif scalar == 'n:INF':
        return float('INF')
    elif scalar == 'n:-INF':
        return -float('INF')
    elif scalar == 'n:NaN':
        return float('nan')
    # Conversion to dict of float value turn them into float 
    # so regex won't work... better just return them
    elif isinstance(scalar, float) or isinstance(scalar, six.integer_types):
        return scalar

    # Is it a number?
    match = NUMBER_RE.match(scalar)
    if match:
        # We'll get a value and a unit, amongst other tokens.
        matched = match.groups()
        value = float(matched[0])
        if matched[-1] is not None:
            # It's a quantity
            return Quantity(value, matched[-1])
        else:
            # It's a raw value
            return value

    # Is it a string?
    if scalar.startswith('s:'):
        return scalar[2:]

    # Is it a xstr?
    if scalar.startswith('x:'):
        return XStr(*scalar[2:].split(':'))

    # Is it a reference?
    match = REF_RE.match(scalar)
    if match:
        matched = match.groups()
        if matched[-1] is not None:
            return Ref(matched[0], matched[-1], has_value=True)
        else:
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
        isodate = iso8601.parse_date(matches[0])
        # Parse timezone
        tzname = matches[-1]
        if tzname is None:
            return isodate  # No timezone given
        else:
            try:
                tz = timezone(tzname)
                return isodate.astimezone(tz)
            except:  # pragma: no cover
                # Unlikely code path.
                return isodate

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


def parse_scalar(scalar, version=LATEST_VER):
    # If we're given a string, decode the JSON data.
    if isinstance(scalar, six.text_type) and \
            (len(scalar) >= 2) and \
            (scalar[0] in ('"','[','{')) and \
            (scalar[-1] in ('"',']','}')):
        scalar = json.loads(scalar)

    return parse_embedded_scalar(scalar, version=version)
