# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# Use license Apache V2.0
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Generic parser from file to `Grid`. The mode can be `MODE_ZINC`, `MODE_JSON` or `MODE_CSV`
"""
import functools
import json
import logging
import re
from typing import Optional, Any, AnyStr, Union, List

from .csvparser import parse_grid as parse_csv_grid
from .csvparser import parse_scalar as parse_csv_scalar
from .grid import Grid
from .jsonparser import parse_grid as parse_json_grid, \
    parse_scalar as parse_json_scalar
# Bring in version handling
from .version import Version, LATEST_VER, VER_3_0
from .zincparser import parse_grid as parse_zinc_grid, \
    parse_scalar as parse_zinc_scalar

EmptyGrid = Grid(version=VER_3_0, columns={"empty": {}})

LOG = logging.getLogger(__name__)

# Trailing newline sanitation
TRAILING_NL_RE = re.compile(r'\n+$')

GRID_SEP = re.compile(r'(?<=\n)\n+')  # It's may be not enough if a string has an empty line

MODE_ZINC = 'text/zinc'
MODE_JSON = 'application/json'
MODE_CSV = 'text/csv'

_suffix_to_mode = {".zinc": MODE_ZINC,
                   ".json": MODE_JSON,
                   ".csv": MODE_CSV
                   }

_mode_to_suffix = {MODE_ZINC: ".zinc",
                   MODE_JSON: ".json",
                   MODE_CSV: ".csv"
                   }


def suffix_to_mode(ext: str) -> Optional[str]:
    """ Convert a file suffix to Haystack mode"""
    return _suffix_to_mode.get(ext, None)


def mode_to_suffix(mode: str) -> Optional[str]:
    """ Convert haystackapi mode to file suffix"""
    return _mode_to_suffix.get(mode, None)


def parse(grid_str: Union[AnyStr, List[str]],
          mode: str = MODE_ZINC,
          charset: str = 'utf-8',
          single: bool = True) -> Union[Grid, List[Grid]]:
    """
    Parse the given Zinc text and return the equivalent data.
    """

    # Decode incoming text (or python3 will whine!)
    if isinstance(grid_str, bytes):
        grid_str = grid_str.decode(encoding=charset)

    # Split the separate grids up, the grammar definition has trouble splitting
    # them up normally.  This will truncate the newline off the end of the last
    # row.
    _parse = functools.partial(parse_grid, mode=mode,
                               charset=charset)
    if mode == MODE_JSON:
        if isinstance(grid_str, str):
            grid_data = json.loads(grid_str)
        else:
            grid_data = grid_str

        # Normally JSON only permits a single grid, but we'll support an
        # extension where a JSON array of grid objects represents multiple.
        # To simplify programming, we'll "normalise" to array-of-grids here.
        if isinstance(grid_data, dict):
            grid_data = [grid_data]
    else:
        if not single:
            grid_data = GRID_SEP.split(TRAILING_NL_RE.sub('\n', grid_str))
        else:
            grid_data = [grid_str]

    grids = list(map(_parse, grid_data))
    if single:
        # Most of the time, we will only want one grid.
        if grids:
            return grids[0]
        return EmptyGrid
    return grids


def parse_grid(grid_str: str, mode: str = MODE_ZINC, charset: str = 'utf-8') -> Grid:
    # Decode incoming text
    if isinstance(grid_str, bytes):  # pragma: no cover
        # No coverage here, because it *should* be handled above unless the user
        # is preempting us by calling `parse_grid` directly.
        grid_str = grid_str.decode(encoding=charset)

    if mode == MODE_ZINC:
        return parse_zinc_grid(grid_str)
    if mode == MODE_JSON:
        return parse_json_grid(grid_str)
    if mode == MODE_CSV:
        return parse_csv_grid(grid_str)
    raise NotImplementedError('Format not implemented: %s' % mode)


def parse_scalar(scalar: Union[bytes, str], mode: str = MODE_ZINC,
                 version: Union[Version, str] = LATEST_VER,
                 charset: str = 'utf-8') -> Any:
    # Decode version string
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
