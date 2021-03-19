# -*- coding: utf-8 -*-
# Zinc grammar specification.
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Parse Zinc file conform with the specification describe here (https://www.project-haystack.org/doc/Zinc)
and produce a `Grid` instance.
"""

import logging
import sys
import textwrap
from typing import Any, Iterable

from pyparsing import Suppress, ParseException, Literal, StringEnd, \
    LineStart, ZeroOrMore, Regex, LineEnd, Optional

from .grid import Grid
from .tools import unescape_str
from .type import Entity
from .version import Version, LATEST_VER
from .zincparser import hs_nl, pyparser_lock, _reformat_exception, \
    parse_grid as parse_zinc_grid, \
    hs_id, toks_to_dict, hs_scalar

# Logging instance for reporting debug info
LOG = logging.getLogger(__name__)


class TrioParseException(ValueError):
    """Exception thrown when a grid cannot be parsed successfully. If known, the
    line and column for the grid are given.
    """
    __slots__ = "grid_str", "line", "col"

    def __init__(self, message: str, grid_str: str, line: int, col: int):
        self.grid_str = grid_str
        self.line = line
        self.col = col

        try:
            # If we know the line and column, point it out in the message.
            grid_str_lines = grid_str.split('\n')
            width = max([len(line) for line in grid_str_lines])
            line_fmt = '%%-%ds' % width
            row_fmt = '%4d%s' + line_fmt + '%s'

            formatted_lines = [
                row_fmt % (
                    num,
                    ' >' if (line == num) else '| ',
                    line_str,
                    '< ' if (line == num) else ' |'
                )
                for (num, line_str)
                in enumerate(grid_str.split('\n'), 1)
            ]
            formatted_lines.insert(line,
                                   ('    | ' + line_fmt + ' |')
                                   % (((col - 2) * ' ') + '.^.')
                                   )

            # Border it for readability
            formatted_lines.insert(0, '    .' + ('-' * (2 + width)) + '.')
            formatted_lines.append('    \'' + ('-' * (2 + width)) + '\'')

            # Append to message
            message += '\n%s' % '\n'.join(formatted_lines)
        except ValueError:  # pragma: no cover
            # We should not get here.
            LOG.exception('Exception encountered formatting log message')

        super().__init__(message)


trio_multiline_string = Suppress(hs_nl) + Regex(
    r'([ \t]+.*[\n\r]+)*[ \t]+.*(?=[\n\r]+)').leaveWhitespace().setParseAction(
    lambda toks: unescape_str(textwrap.dedent(toks[0])) + "\n"
)

trio_zinc_nested = Suppress(Literal("Zinc:") + hs_nl) + Regex(
    r'([ \t]+.*[\n\r]+)*[ \t]+.*(?=[\n\r]+)').leaveWhitespace().setParseAction(
    lambda toks: parse_zinc_grid(textwrap.dedent(toks[0]) + '\n')
)

trio_safe_string = Regex('[^\x00-\x7F]|[A-Za-z_-].*(?=[\n\r]+)').setParseAction(
    lambda toks: unescape_str(toks[0])
)

hs_trio_scalar = (trio_multiline_string ^ trio_zinc_nested ^
                  hs_scalar[LATEST_VER] ^
                  trio_safe_string ^
                  Suppress(LineEnd()))

hs_trio_tagpair = (hs_id +
                   Suppress(':') +
                   (hs_trio_scalar + Suppress(hs_nl) ^ Suppress(hs_nl))
                   ).setParseAction(lambda toks: tuple(toks[:2])).setName('tagPair')

hs_trio_tag = ((Optional(hs_id) + Suppress(hs_nl)) ^ hs_trio_tagpair).setName('tag')

hs_row = hs_trio_tag | Suppress(Regex("//.*[\n\r]+").leaveWhitespace())

hs_record = (hs_row[...] + Suppress((LineStart() + Literal('-')[1, ...] + hs_nl) |
                                    StringEnd())).setParseAction(
    toks_to_dict)


def _gen_grid(toks: Iterable[Entity]):
    grid = Grid(LATEST_VER)
    grid.extend(toks)
    grid.extends_columns()
    return grid


hs_trio = ZeroOrMore(hs_record, stopOn=StringEnd()).setParseAction(_gen_grid)


def parse_grid(grid_data: str, parse_all: bool = True) -> Grid:
    """Parse the incoming grid.

    Args:
        grid_data: The Zinc string
        parse_all: Parse all the string ?
    Returns:
        The grid
    """
    try:
        with pyparser_lock:

            # Now parse the grid of the grid accordingly
            grid = hs_trio.parseString(grid_data, parseAll=parse_all)[0]
            return grid
    except ParseException as parse_exception:
        raise TrioParseException(
            'Failed to parse: %s' % _reformat_exception(parse_exception, parse_exception.lineno),
            grid_data, parse_exception.lineno, parse_exception.col) from parse_exception

    except ValueError as ex:
        raise TrioParseException(
            'Failed to parse: %s' % sys.exc_info()[0], grid_data, 0, 0) from ex


def parse_scalar(scalar_data: str, version: Version = LATEST_VER) -> Any:
    """Parse a Project Haystack scalar in ZINC format.

    Args:
        scalar_data: The zinc string scalar
        version: The Haystack version
    Returns:
        The scala value
    """
    try:
        assert version == LATEST_VER
        return hs_trio_scalar.parseString(scalar_data, parseAll=True)[0]
    except ParseException as parse_exception:
        # Raise a new exception with the appropriate line number.
        raise TrioParseException(
            'Failed to parse scalar: %s' % _reformat_exception(parse_exception),
            scalar_data, 1, parse_exception.col) from parse_exception
