# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Generic parser from file to `Grid`. The mode can be `MODE_ZINC`, `MODE_JSON` or `MODE_CSV`
"""
import logging
from typing import Optional, Any, Union, AnyStr, cast

from .csvparser import parse_grid as parse_csv_grid
from .csvparser import parse_scalar as parse_csv_scalar
from .datatypes import MODE_ZINC, MODE_JSON, MODE_CSV, MODE
from .grid import Grid
from .jsonparser import parse_grid as parse_json_grid, \
    parse_scalar as parse_json_scalar
# Bring in version handling
from .version import Version, LATEST_VER, VER_3_0
from .zincparser import parse_grid as parse_zinc_grid, \
    parse_scalar as parse_zinc_scalar

EmptyGrid = Grid(version=VER_3_0, columns={"empty": {}})

LOG = logging.getLogger(__name__)

_suffix_to_mode = {".zinc": MODE_ZINC,
                   ".json": MODE_JSON,
                   ".csv": MODE_CSV
                   }

_mode_to_suffix = {MODE_ZINC: ".zinc",
                   MODE_JSON: ".json",
                   MODE_CSV: ".csv"
                   }


def suffix_to_mode(ext: str) -> Optional[MODE]:
    """Convert a file suffix to Haystack mode

    Args:
        ext: The file suffix (`.zinc`, `.json`, `.csv`)
    Returns:
        The corresponding haystack mode (`MODE_...`)
    """
    return cast(Optional[MODE], _suffix_to_mode.get(ext, None))


def mode_to_suffix(mode: MODE) -> Optional[str]:
    """Convert haystack mode to file suffix

    Args:
        mode: The haystack mode (`MODE_...`)
    Returns:
        The file suffix (`.zinc`, `.json`, `.csv`)
    """
    return _mode_to_suffix.get(mode, None)


def parse(grid_str: AnyStr, mode: MODE = MODE_ZINC) -> Grid:
    # Decode incoming text
    """
    Parse a grid.
    Args:
        grid_str: The string to parse
        mode: The format (`MODE_...`)
    Returns:
        a grid
    """
    if isinstance(grid_str, bytes):  # pragma: no cover
        # No coverage here, because it *should* be handled above unless the user
        # is preempting us by calling `parse_grid` directly.
        if grid_str[:2] == b'\xef\xbb':
            grid_str = grid_str.decode(encoding="utf-8-sig")
        else:
            grid_str = grid_str.decode(encoding="utf-8")

    if mode == MODE_ZINC:
        return parse_zinc_grid(grid_str)
    if mode == MODE_JSON:
        return parse_json_grid(grid_str)
    if mode == MODE_CSV:
        return parse_csv_grid(grid_str)
    raise NotImplementedError('Format not implemented: %s' % mode)


def parse_scalar(scalar: Union[bytes, str], mode: MODE = MODE_ZINC,
                 version: Union[Version, str] = LATEST_VER) -> Any:
    # Decode version string
    """
    Parse a scalar value
    Args:
        scalar: The scalar data to parse
        mode: The haystack mode
        version: The haystack version
    Returns:
        a value
    """
    charset = 'utf-8'
    if not isinstance(version, Version):
        version = Version(version)

    # Decode incoming text
    if isinstance(scalar, bytes):
        scalar = scalar.decode(encoding=charset)

    if mode == MODE_ZINC:
        return parse_zinc_scalar(scalar, version=version)
    if mode == MODE_JSON:
        return parse_json_scalar(scalar, version=version)
    if mode == MODE_CSV:
        return parse_csv_scalar(scalar, version=version)
    raise NotImplementedError('Format not implemented: %s' % mode)
