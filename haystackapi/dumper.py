#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc Grid dumper
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Generic dumper of `Grid`. The mode can be `MODE_ZINC`, `MODE_JSON` or `MODE_CSV`
"""
import functools

from .csvdumper import dump_grid as dump_csv_grid, \
    dump_scalar as dump_csv_scalar
from .grid import Grid
from .jsondumper import dump_grid as dump_json_grid, \
    dump_scalar as dump_json_scalar
from .parser import MODE_ZINC, MODE_JSON, MODE_CSV
from .version import LATEST_VER
from .zincdumper import dump_grid as dump_zinc_grid, \
    dump_scalar as dump_zinc_scalar


def dump(grids, mode=MODE_ZINC):
    """
    Dump the given grids in the specified over-the-wire format.
    """
    if isinstance(grids, Grid):
        return dump_grid(grids, mode=mode)
    _dump = functools.partial(dump_grid, mode=mode)
    if mode == MODE_ZINC:
        return '\n'.join(map(_dump, grids))
    if mode == MODE_JSON:
        return '[%s]' % ','.join(map(_dump, grids))
    if mode == MODE_CSV:
        return '\n'.join(map(_dump, grids))
    raise NotImplementedError('Format not implemented: %s' % mode)


def dump_grid(grid, mode=MODE_ZINC):
    if mode == MODE_ZINC:
        return dump_zinc_grid(grid)
    if mode == MODE_JSON:
        return dump_json_grid(grid)
    if mode == MODE_CSV:
        return dump_csv_grid(grid)
    raise NotImplementedError('Format not implemented: %s' % mode)


def dump_scalar(scalar, mode=MODE_ZINC, version=LATEST_VER):
    if mode == MODE_ZINC:
        return dump_zinc_scalar(scalar, version=version)
    if mode == MODE_JSON:
        return dump_json_scalar(scalar, version=version)
    if mode == MODE_CSV:
        return dump_csv_scalar(scalar, version=version)
    raise NotImplementedError('Format not implemented: %s' % mode)
