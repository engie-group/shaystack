#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid dumper
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import functools

from .grid import Grid
from .jsondumper import dump_grid as dump_json_grid, \
    dump_scalar as dump_json_scalar
from .parser import MODE_ZINC, MODE_JSON, _parse_mode
from .version import LATEST_VER
from .zincdumper import dump_grid as dump_zinc_grid, \
    dump_scalar as dump_zinc_scalar


def dump(grids, mode=MODE_ZINC):
    """
    Dump the given grids in the specified over-the-wire format.
    """
    # Sanitise mode
    mode = _parse_mode(mode)

    if isinstance(grids, Grid):
        return dump_grid(grids, mode=mode)
    _dump = functools.partial(dump_grid, mode=mode)
    if mode == MODE_ZINC:
        return '\n'.join(map(_dump, grids))
    elif mode == MODE_JSON:
        return '[%s]' % ','.join(map(_dump, grids))
    else:  # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)


def dump_grid(grid, mode=MODE_ZINC):
    # Sanitise mode
    mode = _parse_mode(mode)

    if mode == MODE_ZINC:
        return dump_zinc_grid(grid)
    elif mode == MODE_JSON:
        return dump_json_grid(grid)
    else:  # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)


def dump_scalar(scalar, mode=MODE_ZINC, version=LATEST_VER):
    # Sanitise mode
    mode = _parse_mode(mode)

    if mode == MODE_ZINC:
        return dump_zinc_scalar(scalar, version=version)
    elif mode == MODE_JSON:
        return dump_json_scalar(scalar, version=version)
    else:  # pragma: no cover
        raise NotImplementedError('Format not implemented: %s' % mode)
