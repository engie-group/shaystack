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

GRID_SEP = re.compile(r'(?<=\n)\n+')

MODE_ZINC = 'text/zinc'
MODE_JSON = 'application/json'

def _parse_mode(mode):
    """
    Sanitise the mode given.  Whilst code _should_ use the MODE_ZINC and
    MODE_JSON constants above, we have some code internally that plays fast
    and loose with this.
    """
    if mode in (MODE_ZINC, MODE_JSON):
        return mode

    # Danger zone: user has given us something different.  They better know
    # what it is they are doing!
    mode = str(mode).lower()
    if mode == 'zinc':
        return MODE_ZINC
    elif mode == 'json':
        return MODE_JSON
    else:
        # Clearly that was a wrong assumption.  Let 'em have it!
        raise ValueError('Unrecognised mode, should be MODE_ZINC or MODE_JSON')


def parse(grid_str, mode=MODE_ZINC, charset='utf-8', single=True):
    """
    Parse the given Zinc text and return the equivalent data.
    """
    # Sanitise mode
    mode = _parse_mode(mode)

    # Decode incoming text (or python3 will whine!)
    if isinstance(grid_str, six.binary_type):
        grid_str = grid_str.decode(encoding=charset)

    # Split the separate grids up, the grammar definition has trouble splitting
    # them up normally.  This will truncate the newline off the end of the last
    # row.
    _parse = functools.partial(parse_grid, mode=mode, charset=charset)
    if mode == MODE_JSON:
        if isinstance(grid_str, six.string_types):
            grid_data = json.loads(grid_str)
        else:
            grid_data = grid_str

        # Normally JSON only permits a single grid, but we'll support an
        # extension where a JSON array of grid objects represents multiple.
        # To simplify programming, we'll "normalise" to array-of-grids here.
        if isinstance(grid_data, dict):
            grid_data = [grid_data]
    else:
        grid_data = GRID_SEP.split(grid_str)

    grids = list(map(_parse, grid_data))
    if single:
        # Most of the time, we will only want one grid.
        if grids:
            return grids[0]
        else:
            return None
    else:
        return grids


def parse_grid(grid_str, mode=MODE_ZINC, charset='utf-8'):
    # Sanitise mode
    mode = _parse_mode(mode)

    # Decode incoming text
    if isinstance(grid_str, six.binary_type):  # pragma: no cover
        # No coverage here, because it *should* be handled above unless the user
        # is pre-empting us by calling `parse_grid` directly.
        grid_str = grid_str.decode(encoding=charset)

    if mode == MODE_ZINC:
        return parse_zinc_grid(grid_str)
    elif mode == MODE_JSON:
        return parse_json_grid(grid_str)
    else:  # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)


def parse_scalar(scalar, mode=MODE_ZINC, version=LATEST_VER, charset='utf-8'):
    # Sanitise mode
    mode = _parse_mode(mode)

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
    else:  # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)
