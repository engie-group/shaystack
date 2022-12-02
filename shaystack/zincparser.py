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

import datetime
import logging
import re
import sys
from threading import RLock
from typing import Dict, Any, Callable, List, Tuple
from typing import Optional as Typing_Optional

import iso8601
from pint import UndefinedUnitError
from pyparsing import Regex, Forward, Combine, Suppress, CaselessLiteral, Literal, Optional, ParseException, \
    Word, Group, Empty, delimitedList, ParserElement

from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, NA, REMOVE, Ref, XStr
from .grid import Grid
# Bring in our sortable dict class to preserve order
from .sortabledict import SortableDict
# Bring in version handling
from .tools import unescape_str
from .version import Version, VER_2_0, VER_3_0, LATEST_VER
from .zoneinfo import timezone

# Logging instance for reporting debug info
LOG = logging.getLogger(__name__)

# All grids start with the version string.
_VERSION_RE = re.compile(r'^ver:"(([^"\\]|\\[\\"bfnrt$])+)"')
_NEWLINE_RE = re.compile(r'\r?\n')

# Character number regex; for exceptions
_CHAR_NUM_RE = re.compile(r' *\(at char \d+\),')


def _reformat_exception(ex_msg: ParseException, line_num: Typing_Optional[int] = None) -> str:
    msg = _CHAR_NUM_RE.sub('', str(ex_msg))
    if line_num is not None:
        return msg.replace('line:1', 'line:%d' % line_num)
    return msg


def _parse_time(toks: List[str]) -> List[datetime.time]:
    time_str = toks[0]
    time_fmt = '%H:%M'
    if time_str.count(':') == 2:
        time_fmt += ':%S'
    if '.' in time_str:
        time_fmt += '.%f'
    return [datetime.datetime.strptime(time_str, time_fmt).time()]


def _parse_datetime(toks: Tuple[datetime.datetime, Typing_Optional[str]]) -> List[datetime.datetime]:
    # Made up of parts: ISO8601 Date/Time, time zone label
    """
    Args:
        toks:
    """
    isodt = toks[0]
    if len(toks) > 1:
        tzname = toks[1]
    else:
        tzname = None

    assert not ((isodt.tzinfo is None) and bool(tzname))  # pragma: no cover
    if tzname:
        return [isodt.astimezone(timezone(tzname))]
    if isodt.tzname():
        return [isodt]
    return [isodt.astimezone(timezone("UTC"))]


def _assign_ver(toks: List[SortableDict]) -> SortableDict:
    """
    Args:
        toks:
    """
    ver = toks[0]
    if len(toks) > 1:
        grid_meta = toks[1]
    else:
        grid_meta = SortableDict()

    # Put 'ver' at the start
    grid_meta.add_item('ver', ver, index=0)
    return grid_meta


def _gen_grid(toks: List[Any]) -> Grid:
    """
    Args:
        toks:
    """
    (grid_meta, col_meta, rows) = toks
    if len(rows) == 1 and rows[0] is None:
        rows = []
    grid = Grid(version=grid_meta.pop('ver'),
                metadata=grid_meta,
                columns=list(col_meta.items()))
    for row in rows:
        grid.append({k: row[p] for p, k in enumerate(col_meta.keys()) if row[p] is not None})
    return grid


def toks_to_dict(toks: List[Any]) -> Dict[str, Any]:
    """
    Args:
        toks:
    """
    result = {}
    iterator = enumerate(toks)
    for i, tok in iterator:
        if i < len(toks) - 2 and toks[i + 1] == ':':
            result[toks[i]] = toks[i + 2]
            next(iterator)
            next(iterator)
        else:
            if isinstance(tok, str):
                result[tok] = MARKER
            elif isinstance(tok, tuple):
                if len(tok) > 1 and tok[1] is not None:
                    result[tok[0]] = tok[1]
            else:
                result[tok] = MARKER

    return result


class ZincParseException(ValueError):
    """Exception thrown when a grid cannot be parsed successfully. If known, the
    line and column for the grid are given.
    """
    __slots__ = "grid_str", "line", "col"

    def __init__(self, message: str, grid_str: Typing_Optional[str],
                 line: Typing_Optional[int], col: Typing_Optional[int]):
        if grid_str:
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
                formatted_lines.insert(line,  # type: ignore
                                       ('    | ' + line_fmt + ' |')
                                       % (((col - 2) * ' ') + '.^.')  # type: ignore
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


class _NearestMatch:  # pylint: disable=global-statement
    """This class returns the nearest matching grammar for the given version."""

    __slots__ = ("_known_grammars",)

    def __init__(self, known_grammars: Dict[Version, Any]):
        self._known_grammars = known_grammars

    def __getitem__(self, ver: Version) -> Any:
        """Retrieve the grammar that closest matches the version string given.
        """
        try:
            return self._known_grammars[ver]
        except KeyError:
            pass

        nearest = Version.nearest(ver)
        a_generator = self._known_grammars[nearest]
        self._known_grammars[ver] = a_generator
        return a_generator


class _GenerateMatch:
    """This class tries to generate a matching grammar based on the version
    input given.
    """

    __slots__ = "_generator_fn", "_known_grammars"

    def __init__(self, generator_fn: Callable[[Version], Any]):
        """
        Args:
            generator_fn:
        """
        self._generator_fn = generator_fn
        self._known_grammars = {}  # type: ignore

    def __getitem__(self, ver: Version) -> Any:
        try:
            return self._known_grammars[ver]
        except KeyError:
            a_generator = self._generator_fn(ver)
            self._known_grammars[ver] = a_generator
            return a_generator


# Grammar according to
#   latest: http://project-haystack.org/doc/Zinc
#   "2.0":  https://web.archive.org/web/20141012013653/http://project-haystack.org:80/doc/Zinc
#   "3.0":  https://web.archive.org/web/20160805064015/http://project-haystack.org:80/doc/Zinc

ParserElement.setDefaultWhitespaceChars(' \t')
# Rudimentary elements
hs_digit = Regex(r'\d')
hs_digits = Regex(r'[0-9_]+').setParseAction(
    lambda toks: [''.join([t.replace('_', '') for t in toks[0]])])
hs_alpha = Regex(r'[a-zA-Z]')
hs_plusMinus = Literal('+') ^ '-'

# Forward declaration of data types.
hs_scalar_2_0 = Forward()
hs_scalar_3_0 = Forward()
hs_scalar = _NearestMatch({
    VER_2_0: hs_scalar_2_0,
    VER_3_0: hs_scalar_3_0
})

hs_grid_2_0 = Forward()
hs_grid_3_0 = Forward()
hs_grid = _NearestMatch({
    VER_2_0: hs_grid_2_0,
    VER_3_0: hs_grid_3_0
})

# Co-ordinates
hs_coordDeg = Combine(
    Optional('-') +
    Optional(hs_digits) +
    Optional('.' + hs_digits)
).setParseAction(lambda toks: [float(toks[0] or '0')])
hs_coord = (Suppress('C(') +
            hs_coordDeg +
            Suppress(',') +
            hs_coordDeg +
            Suppress(')')).setParseAction(
    lambda toks: [Coordinate(toks[0], toks[1])])

# Dates and times
hs_tzHHMMOffset = Combine(
    CaselessLiteral('z') ^
    hs_plusMinus + Regex(r'\d\d:\d\d')
)
hs_tzName = Regex(r'[A-Z][a-zA-Z0-9_\-]*')
hs_tz_UTC_GMT = Literal('UTC') ^ 'GMT'
hs_tzUTCOffset = Combine(
    hs_tz_UTC_GMT + Optional(
        hs_plusMinus + hs_digit[1, ...] ^
        '0'
    ))
hs_timeZoneName = hs_tzUTCOffset ^ hs_tzName
hs_dateSep = CaselessLiteral('T')
hs_date_str = Combine(
    hs_digit + hs_digit + hs_digit + hs_digit +
    '-' +
    hs_digit + hs_digit +
    '-' +
    hs_digit + hs_digit)
hs_date = hs_date_str.copy().setParseAction(
    lambda toks: [datetime.datetime.strptime(toks[0], '%Y-%m-%d').date()])

hs_time_str = Combine(
    hs_digit + hs_digit +
    ':' +
    hs_digit + hs_digit +
    Optional(
        ':' +
        hs_digit + hs_digit +
        Optional(
            '.' +
            hs_digit[1, ...])
    )
)

hs_time = hs_time_str.copy().setParseAction(_parse_time)
hs_isoDateTime = Combine(
    hs_date_str +
    hs_dateSep +
    hs_time_str +
    Optional(hs_tzHHMMOffset)
).setParseAction(lambda toks: [iso8601.parse_date(toks[0].upper())])

hs_dateTime = (
        hs_isoDateTime +
        Optional(hs_timeZoneName)
).setParseAction(_parse_datetime)

hs_all_date = hs_dateTime | hs_date | hs_time

# Quantities and raw numeric values
hs_unitChar = hs_alpha ^ Word('%_/$' + ''.join([
    chr(c)
    for c in range(0x0080, 0xffff)
]), exact=1)

hs_unit = Combine(hs_unitChar[1, ...])
hs_exp = Combine(
    CaselessLiteral('e') +
    Optional(hs_plusMinus) +
    hs_digits
)
hs_decimal = Combine(
    Optional('-') +
    hs_digits +
    Optional(
        '.' +
        hs_digits
    ) +
    Optional(hs_exp)
).setParseAction(lambda toks: [float(toks[0])])


def _quantity(toks):
    try:
        return [Quantity(*toks)]
    except UndefinedUnitError as ex:
        raise ZincParseException("Invalide unit", None, 0, 0) from ex


hs_quantity = (hs_decimal + hs_unit).leaveWhitespace() \
    .setParseAction(_quantity)
hs_number = hs_quantity ^ hs_decimal ^ (
        Literal('INF') ^
        '-INF' ^
        'NaN'
).setParseAction(lambda toks: [float(toks[0])])

# URIs
hs_uriChar = Regex(r"([^\x00-\x1f\\`]|\\[bfnrt\\:/?"
                   + r"#\[\]@&=;`]|\\[uU][0-9a-fA-F]{4})")
hs_uri = Combine(
    Suppress('`') +
    hs_uriChar[...] +
    Suppress('`')
).setParseAction(lambda toks: [Uri(unescape_str(toks[0], uri=True))])

# Strings
hs_strChar = Regex(r"([^\x00-\x1f\\\"]|\\[bfnrt\\\"$]|\\[uU][0-9a-fA-F]{4})")
hs_str = Combine(
    Suppress('"') +
    hs_strChar[...] +
    Suppress('"')
).setParseAction(lambda toks: [unescape_str(toks[0], uri=False)])

# References
hs_refChar = hs_alpha ^ hs_digit ^ Word('_:-.~', exact=1)
hs_ref = (
        Suppress('@') +
        Combine(hs_refChar[...]) +
        Optional(hs_str)
).setParseAction(lambda toks: [
    Ref(toks[0], toks[1] if len(toks) > 1 else None)
])

# Bins
hs_binChar = Regex(r"[\x20-\x27\x2a-\x7f]")
hs_bin = Combine(
    Suppress('Bin(') +
    Combine(hs_binChar[...]) +
    Suppress(')')
).setParseAction(lambda toks: [Bin(toks[0])])

# Haystack 3.0 XStr(...)
hs_xstr = (
        Regex(r"[a-zA-Z0-9_]+") +
        Suppress('(') +
        hs_str +
        Suppress(')')
).setParseAction(lambda toks: [XStr(toks[0], toks[1])])

# Booleans
hs_bool = Word('TF', min=1, max=1, exact=1).setParseAction(
    lambda toks: [toks[0] == 'T'])

# Singleton values
hs_remove = Literal('R').setParseAction(
    lambda toks: [REMOVE]).setName('remove')
hs_marker = Literal('M').setParseAction(
    lambda toks: [MARKER]).setName('marker')
hs_null = Literal('N').setParseAction(
    lambda toks: [None]).setName('null')
hs_na = Literal('NA').setParseAction(
    lambda toks: [NA]).setName('na')
# Lists, these will probably be in Haystack 4.0, so let's not
# assume a version.  There are three cases:
# - Empty list: [ {optional whitespace} ]
# - List *with* trailing comma: [ 1, 2, 3, ]
# - List without trailing comma: [ 1, 2, 3 ]
#
# We need to handle this trailing separator case.  That for now means
# that a NULL within a list *MUST* be explicitly given using the 'N'
# literal: we cannot support implicit NULLs as they are ambiguous.
hs_list = _GenerateMatch(
    lambda ver: Group(
        Suppress('[') +
        Optional(delimitedList(
            hs_scalar[ver],
            delim=',')) +
        Suppress(Optional(',')) +
        Suppress(']')
    ).setParseAction(lambda toks: toks.asList()))
# Tag IDs
hs_id = Regex(r'[a-z_][a-zA-Z0-9_]*').setName('id')

# Grid building blocks
hs_cell = _GenerateMatch(
    lambda ver: (Empty().copy().setParseAction(lambda toks: [None]) ^
                 hs_scalar[ver]).setName('cell'))

# Dict
# There are three cases:
# - Empty dict: { {optional whitespace} }
# - map with marker: { m }
# - dics: { k:1  ]
#
hs_tagmarker = hs_id

hs_tagpair = _GenerateMatch(
    lambda ver: (hs_id +
                 Suppress(':') +
                 hs_scalar[ver]
                 ).setParseAction(lambda toks: tuple(toks[:2])).setName('tagPair'))

hs_tag = _GenerateMatch(
    lambda ver: (hs_tagmarker ^ hs_tagpair[ver]).setName('tag'))

hs_tags = _GenerateMatch(
    lambda ver: hs_tag[ver][...].setName('tags'))

hs_dict = _GenerateMatch(
    lambda ver:
    (Suppress('{') +
     hs_tags[ver] +
     Suppress('}')
     ).setName("dict").setParseAction(toks_to_dict)
)

hs_inner_grid = _GenerateMatch(
    lambda ver:
    Suppress('<<') +
    hs_grid[ver] +
    Suppress('>>')
)

# All possible scalar values, by Haystack version
hs_scalar_2_0 <<= (hs_ref ^ hs_bin ^ hs_str ^ hs_uri ^ hs_all_date ^
                   hs_coord ^ hs_number ^ hs_null ^ hs_marker ^
                   hs_remove ^ hs_bool).setName('scalar')
hs_scalar_3_0 <<= (hs_ref ^ hs_xstr ^ hs_str ^ hs_uri ^ hs_all_date ^
                   hs_coord ^ hs_number ^ hs_na ^ hs_null ^ hs_marker ^
                   hs_remove ^ hs_bool ^ hs_list[VER_3_0] ^ hs_dict[VER_3_0] ^
                   hs_inner_grid[VER_3_0]).setName('scalar')

hs_nl = Combine(Optional('\r') + '\n')

hs_row = _GenerateMatch(
    lambda ver: Group(delimitedList(hs_cell[ver], delim=',') +
                      Suppress(hs_nl)
                      ).setName('row'))

hs_rows = _GenerateMatch(
    lambda ver: Group(hs_row[ver][...]).setName("rows"))

hs_metaPair = _GenerateMatch(
    lambda ver: (
            hs_id +
            Suppress(':') +
            hs_scalar[ver]
    ).setParseAction(lambda toks: [tuple(toks[:2])]).setName('metaPair'))
hs_metaMarker = hs_id.copy().setParseAction(
    lambda toks: [(toks[0], MARKER)]).setName('metaMarker')
hs_metaItem = _GenerateMatch(
    lambda ver: (
            hs_metaMarker ^
            hs_metaPair[ver]
    ).setName('metaItem'))
hs_meta = _GenerateMatch(
    lambda ver: hs_metaItem[ver][1, ...].setParseAction(
        lambda toks: [SortableDict(toks.asList())]
    ).setName('meta'))

hs_col = _GenerateMatch(
    lambda ver: (
            hs_id +
            Optional(hs_meta[ver]).setName('colMeta')
    ).setParseAction(lambda toks: [
        (toks[0], toks[1] if len(toks) > 1 else {})]))

hs_cols = _GenerateMatch(
    lambda ver:
    delimitedList(
        hs_col[ver], delim=',')
        .setParseAction(lambda toks: [SortableDict(toks.asList())]) +
    Suppress(hs_nl)
)

hs_gridVer = Combine(Suppress('ver:') + hs_str)

hs_gridMeta = _GenerateMatch(
    lambda ver: (
            hs_gridVer +
            Optional(hs_meta[ver]).setName('gridMeta') +
            Suppress(hs_nl)
    ).setParseAction(_assign_ver))

hs_grid_2_0 <<= (
        hs_gridMeta[VER_2_0] +
        hs_cols[VER_2_0] +
        hs_rows[VER_2_0]
).setParseAction(_gen_grid)

hs_grid_3_0 <<= (
        hs_gridMeta[VER_3_0] +
        hs_cols[VER_3_0] +
        hs_rows[VER_3_0]
).setParseAction(_gen_grid)

pyparser_lock = RLock()


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
            # First element is the grid metadata
            ver_match = _VERSION_RE.match(grid_data)
            if ver_match is None:
                raise ZincParseException(
                    'Could not determine version from %r' % _NEWLINE_RE.split(grid_data)[0],
                    grid_data, 1, 1)
            version = Version(ver_match.group(1))

            # Now parse the grid of the grid accordingly
            return hs_grid[version].parseString(grid_data, parseAll=parse_all)[0]
    except ParseException as parse_exception:
        LOG.debug('Failing grid: %r', grid_data)
        raise ZincParseException(
            'Failed to parse: %s' % _reformat_exception(parse_exception, parse_exception.lineno),
            grid_data, parse_exception.lineno, parse_exception.col) from parse_exception

    except ValueError as ex:
        LOG.debug('Failing grid: %r', grid_data)
        raise ZincParseException(
            'Failed to parse: %s' % sys.exc_info()[0], grid_data, 0, 0) from ex


def parse_scalar(scalar_data: str, version: Version = LATEST_VER) -> Any:
    """Parse a Project Haystack scalar in ZINC format.

    Args:
        scalar_data: The zinc string scalar
        version: The Haystack version
    Returns:
        The scala value
    """
    if not isinstance(scalar_data, str) or scalar_data != scalar_data.strip():
        raise ZincParseException('Failed to parse scalar: %s' % scalar_data, None, None, None)
    try:
        return hs_scalar[version].parseString(scalar_data, parseAll=True)[0]
    except ParseException as parse_exception:
        # Raise a new exception with the appropriate line number.
        raise ZincParseException(
            'Failed to parse scalar: %s' % _reformat_exception(parse_exception),
            scalar_data, 1, parse_exception.col) from parse_exception
