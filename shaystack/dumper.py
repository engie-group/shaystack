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
from typing import Any, Optional

from .csvdumper import dump_grid as dump_csv_grid, \
    dump_scalar as dump_csv_scalar
from .datatypes import MODE_TRIO
from .grid import Grid
from .haysondumper import dump_grid as dump_hayson_grid, \
    dump_scalar as dump_hayson_scalar
from .jsondumper import dump_grid as dump_json_grid, \
    dump_scalar as dump_json_scalar
from .parser import MODE_ZINC, MODE_HAYSON, MODE_JSON, MODE_CSV, MODE
from .triodumper import dump_grid as dump_trio_grid, \
    dump_scalar as dump_trio_scalar
from .version import LATEST_VER, Version
from .zincdumper import dump_grid as dump_zinc_grid, \
    dump_scalar as dump_zinc_scalar


def dump(grid: Grid, mode: MODE = MODE_ZINC) -> str:
    """
    Dump a single grid in the specified over-the-wire format.
    Args:
        grid: The grid to dump.
        mode: The format. Must be MODE_ZINC, MODE_CSV or MODE_JSON
    """
    if mode == MODE_ZINC:
        return dump_zinc_grid(grid)
    if mode == MODE_TRIO:
        return dump_trio_grid(grid)
    if mode == MODE_JSON:
        return dump_json_grid(grid)
    if mode == MODE_HAYSON:
        return dump_hayson_grid(grid)
    if mode == MODE_CSV:
        return dump_csv_grid(grid)
    raise NotImplementedError('Format not implemented: %s' % mode)


def dump_scalar(scalar: Any, mode: MODE = MODE_ZINC, version: Version = LATEST_VER) -> Optional[str]:
    """
    Dump a scalar value in the specified over-the-wire format and version.
    Args:
        scalar: The value to dump
        mode: The format. Must be MODE_ZINC, MODE_CSV or MODE_JSON
        version: The Haystack version to apply
    """
    if mode == MODE_ZINC:
        return dump_zinc_scalar(scalar, version=version)
    if mode == MODE_TRIO:
        return dump_trio_scalar(scalar, version=version)
    if mode == MODE_JSON:
        return dump_json_scalar(scalar, version=version)
    if mode == MODE_HAYSON:
        return dump_hayson_scalar(scalar, version=version)
    if mode == MODE_CSV:
        return dump_csv_scalar(scalar, version=version)
    raise NotImplementedError('Format not implemented: %s' % mode)
