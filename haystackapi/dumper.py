# -*- coding: utf-8 -*-
# Zinc Grid dumper
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Generic dumper of `Grid`. The mode can be `MODE_ZINC`, `MODE_JSON` or `MODE_CSV`
"""
import functools
from typing import Union, List, Any, Optional

from .csvdumper import dump_grid as dump_csv_grid, \
    dump_scalar as dump_csv_scalar
from .grid import Grid
from .jsondumper import dump_grid as dump_json_grid, \
    dump_scalar as dump_json_scalar
from .parser import MODE_ZINC, MODE_JSON, MODE_CSV
from .version import LATEST_VER, Version
from .zincdumper import dump_grid as dump_zinc_grid, \
    dump_scalar as dump_zinc_scalar


def dump(grids: Union[Grid, List[Grid]], mode: str = MODE_ZINC) -> str:
    """Dump the given grids in the specified over-the-wire format.

    Args:
        grids:
        mode (str):
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


def dump_grid(grid: Grid, mode: str = MODE_ZINC) -> str:
    """
    Args:
        grid (Grid):
        mode (str):
    """
    if mode == MODE_ZINC:
        return dump_zinc_grid(grid)
    if mode == MODE_JSON:
        return dump_json_grid(grid)
    if mode == MODE_CSV:
        return dump_csv_grid(grid)
    raise NotImplementedError('Format not implemented: %s' % mode)


def dump_scalar(scalar: Any, mode: str = MODE_ZINC, version: Version = LATEST_VER) -> Optional[str]:
    """
    Args:
        scalar (Any):
        mode (str):
        version (Version):
    """
    if mode == MODE_ZINC:
        return dump_zinc_scalar(scalar, version=version)
    if mode == MODE_JSON:
        return dump_json_scalar(scalar, version=version)
    if mode == MODE_CSV:
        return dump_csv_scalar(scalar, version=version)
    raise NotImplementedError('Format not implemented: %s' % mode)
