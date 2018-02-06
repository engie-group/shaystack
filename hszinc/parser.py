#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from .zincparser import parse_grid as parse_zinc_grid, \
                        parse_scalar as parse_zinc_scalar
from .jsonparser import parse_grid as parse_json_grid, \
                        parse_scalar as parse_json_scalar
import re
import six
import functools
import json

# Bring in version handling
from .version import Version, LATEST_VER

GRID_SEP = re.compile(r'\n\n+')

MODE_ZINC = 'zinc'
MODE_JSON = 'json'

def parse(grid_str, mode=MODE_ZINC, charset='utf-8'):
    '''
    Parse the given Zinc text and return the equivalent data.
    '''
    # Decode incoming text (or python3 will whine!)
    if isinstance(grid_str, six.binary_type):
        grid_str = grid_str.decode(encoding=charset)

    # Split the separate grids up, the grammar definition has trouble splitting
    # them up normally.  This will truncate the newline off the end of the last
    # row.
    _parse = functools.partial(parse_grid, mode=mode,
            charset=charset)
    if mode == MODE_JSON:
        if isinstance(grid_str, six.string_types):
            grid_data = json.loads(grid_str)
        else:
            grid_data = grid_str
        if isinstance(grid_data, dict):
            return _parse(grid_data)
        else:
            return list(map(_parse, grid_data))
    else:
        return list(map(_parse, GRID_SEP.split(grid_str.rstrip())))

def parse_grid(grid_str, mode=MODE_ZINC, charset='utf-8'):
    # Decode incoming text
    if isinstance(grid_str, six.binary_type): # pragma: no cover
        # No coverage here, because it *should* be handled above unless the user
        # is pre-empting us by calling `parse_grid` directly.
        grid_str = grid_str.decode(encoding=charset)

    if mode == MODE_ZINC:
        return parse_zinc_grid(grid_str)
    elif mode == MODE_JSON:
        return parse_json_grid(grid_str)
    else: # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)

def parse_scalar(scalar, mode=MODE_ZINC, version=LATEST_VER, charset='utf-8'):
    # Decode version string
    if not isinstance(version, Version):
        version = Version(version)

    # Decode incoming text
    if isinstance(scalar, six.binary_type):
        scalar = scalar.decode(encoding=charset)

    if mode == MODE_ZINC:
        return parse_zinc_scalar(scalar, version=version)
    elif mode == MODE_JSON:
        return parse_json_scalar(scalar, version=version)
    else: # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)
