#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc grammar specification.
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import datetime
import logging
import re
import sys

import iso8601
import pyparsing as pp
import six

# Bring in special Project Haystack types and time zones
from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, NA, REMOVE, Ref, XStr
from .grid import Grid
# Bring in our sortable dict class to preserve order
from .sortabledict import SortableDict
# Bring in version handling
from .version import Version, VER_2_0, VER_3_0
from .zoneinfo import timezone

# Logging instance for reporting debug info
LOG = logging.getLogger(__name__)

# All grids start with the version string.
VERSION_RE = re.compile(r'^ver:"(([^"\\]|\\[\\"bfnrt$])+)"')
NEWLINE_RE = re.compile(r'\r?\n')

# Character number regex; for exceptions
CHAR_NUM_RE = re.compile(' *\(at char \d+\),')


def reformat_exception(ex_msg, line_num=None):
    print(ex_msg)
    msg = CHAR_NUM_RE.sub(u'', six.text_type(ex_msg))
    print(msg)
    if line_num is not None:
        return msg.replace(u'line:1', u'line:%d' % line_num)
    else:
        return msg


# Convenience function, we want whitespace left alone.
def _leave_ws(cls, *args, **kwargs):
    return cls(*args, **kwargs).leaveWhitespace()


# Versions of the pyparsing types that leave our whitespace alone!
Empty = lambda *a, **kwa: _leave_ws(pp.Empty, *a, **kwa)
Regex = lambda *a, **kwa: _leave_ws(pp.Regex, *a, **kwa)
Literal = lambda *a, **kwa: _leave_ws(pp.Literal, *a, **kwa)
CaselessLiteral = lambda *a, **kwa: _leave_ws(pp.CaselessLiteral, *a, **kwa)
Word = lambda *a, **kwa: _leave_ws(pp.Word, *a, **kwa)
Optional = lambda *a, **kwa: _leave_ws(pp.Optional, *a, **kwa)
Suppress = lambda *a, **kwa: _leave_ws(pp.Suppress, *a, **kwa)
Combine = lambda *a, **kwa: _leave_ws(pp.Combine, *a, **kwa)
And = lambda *a, **kwa: _leave_ws(pp.And, *a, **kwa)
Or = lambda *a, **kwa: _leave_ws(pp.Or, *a, **kwa)
ZeroOrMore = lambda *a, **kwa: _leave_ws(pp.ZeroOrMore, *a, **kwa)
OneOrMore = lambda *a, **kwa: _leave_ws(pp.OneOrMore, *a, **kwa)
Group = lambda *a, **kwa: _leave_ws(pp.Group, *a, **kwa)
DelimitedList = lambda *a, **kwa: _leave_ws(pp.delimitedList, *a, **kwa)
Forward = lambda *a, **kwa: _leave_ws(pp.Forward, *a, **kwa)


class ZincParseException(ValueError):
    """
    Exception thrown when a grid cannot be parsed successfully.  If known,
    the line and column for the grid are given.
    """

    def __init__(self, message, grid_str, line, col):
        self.grid_str = grid_str
        self.line = line
        self.col = col

        try:
            # If we know the line and column, point it out in the message.
            grid_str_lines = grid_str.split('\n')
            width = max([len(l) for l in grid_str_lines])
            linefmt = u'%%-%ds' % width
            rowfmt = u'%4d%s' + linefmt + u'%s'

            formatted_lines = [
                rowfmt % (
                    num,
                    ' >' if (line == num) else '| ',
                    line_str,
                    '< ' if (line == num) else ' |'
                )
                for (num, line_str)
                in enumerate(grid_str.split('\n'), 1)
            ]
            formatted_lines.insert(line,
                                   (u'    | ' + linefmt + u' |') \
                                   % (((col - 2) * u' ') + '.^.')
                                   )

            # Border it for readability
            formatted_lines.insert(0, u'    .' + (u'-' * (2 + width)) + u'.')
            formatted_lines.append(u'    \'' + (u'-' * (2 + width)) + u'\'')

            # Append to message
            message += u'\n%s' % u'\n'.join(formatted_lines)
        except:  # pragma: no cover
            # We should not get here.
            LOG.exception('Exception encountered formatting log message')
            pass

        super(ZincParseException, self).__init__(message)


class NearestMatch(object):
    """
    This class returns the nearest matching grammar for the given version.
    """

    def __init__(self, known_grammars):
        self._known_grammars = known_grammars

    def __getitem__(self, ver):
        """
        Retrieve the grammar that closest matches the version string given.
        """
        try:
            return self._known_grammars[ver]
        except KeyError:
            pass

        nearest = Version.nearest(ver)
        g = self._known_grammars[nearest]
        self._known_grammars[ver] = g
        return g


class GenerateMatch(object):
    """
    This class tries to generate a matching grammar based on the version input given.
    """

    def __init__(self, generator_fn):
        self._generator_fn = generator_fn
        self._known_grammars = {}

    def __getitem__(self, ver):
        try:
            return self._known_grammars[ver]
        except KeyError:
            g = self._generator_fn(ver)
            self._known_grammars[ver] = g
            return g


def _unescape(s, uri=False):
    """
    Iterative parser for string escapes.
    """
    out = ''
    while len(s) > 0:
        c = s[0]
        if c == '\\':
            # Backslash escape
            esc_c = s[1]

            if esc_c in ('u', 'U'):
                # Unicode escape
                out += six.unichr(int(s[2:6], base=16))
                s = s[6:]
                continue
            else:
                if esc_c == 'b':
                    out += '\b'
                elif esc_c == 'f':
                    out += '\f'
                elif esc_c == 'n':
                    out += '\n'
                elif esc_c == 'r':
                    out += '\r'
                elif esc_c == 't':
                    out += '\t'
                else:
                    if uri and (esc_c == '#'):
                        # \# is passed through with backslash.
                        out += '\\'
                    # Pass through
                    out += esc_c
                s = s[2:]
                continue
        else:
            out += c
            s = s[1:]
    return out


# Grammar according to
#   latest: http://project-haystack.org/doc/Zinc
#   "2.0":  https://web.archive.org/web/20141012013653/http://project-haystack.org:80/doc/Zinc
#   "3.0":  https://web.archive.org/web/20160805064015/http://project-haystack.org:80/doc/Zinc

# Rudimentary elements
hs_digit = Regex(r'\d')
hs_digits = Regex(r'[0-9_]+').setParseAction(
    lambda toks: [''.join([t.replace('_', '') for t in toks[0]])])
hs_alphaLo = Regex(r'[a-z]')
hs_alphaHi = Regex(r'[A-Z]')
hs_alpha = Regex(r'[a-zA-Z]')
hs_valueSep = Regex(r' *, *').setName('valueSep')
hs_rowSep = Regex(r' *\n *').setName('rowSep')
hs_plusMinus = Or([Literal('+'), Literal('-')])

# Forward declaration of data types.
hs_scalar_2_0 = Forward()
hs_scalar_3_0 = Forward()
hs_scalar = NearestMatch({
    VER_2_0: hs_scalar_2_0,
    VER_3_0: hs_scalar_3_0
})

hs_grid_2_0 = Forward()
hs_grid_3_0 = Forward()
hs_grid = NearestMatch({
    VER_2_0: hs_grid_2_0,
    VER_3_0: hs_grid_3_0
})

# Co-ordinates
hs_coordDeg = Combine(And([
    Optional(Literal('-')),
    Optional(hs_digits),
    Optional(And([Literal('.'), hs_digits]))
])).setParseAction(lambda toks: [float(toks[0] or '0')])
hs_coord = And([Suppress(Literal('C(')),
                hs_coordDeg,
                Suppress(hs_valueSep),
                hs_coordDeg,
                Suppress(Literal(')'))]).setParseAction(
    lambda toks: [Coordinate(toks[0], toks[1])])

# Dates and times
hs_tzHHMMOffset = Combine(Or([
    CaselessLiteral('z'),
    And([hs_plusMinus, Regex(r'\d\d:\d\d')])]
))
hs_tzName = Regex(r'[A-Z][a-zA-Z0-9_\-]*')
hs_tzUTCGMT = Or([Literal('UTC'), Literal('GMT')])
hs_tzUTCOffset = Combine(And([
    hs_tzUTCGMT, Optional(
        Or([Literal('0'),
            And([hs_plusMinus, OneOrMore(hs_digit)]
                )]
           ))]))
hs_timeZoneName = Or([hs_tzUTCOffset, hs_tzName])
hs_dateSep = CaselessLiteral('T')
hs_date_str = Combine(And([
    hs_digit, hs_digit, hs_digit, hs_digit,
    Literal('-'),
    hs_digit, hs_digit,
    Literal('-'),
    hs_digit, hs_digit]))
hs_date = hs_date_str.copy().setParseAction(
    lambda toks: [datetime.datetime.strptime(toks[0], '%Y-%m-%d').date()])

hs_time_str = Combine(And([
    hs_digit, hs_digit,
    Literal(':'),
    hs_digit, hs_digit,
    Literal(':'),
    hs_digit, hs_digit,
    Optional(And([
        Literal('.'),
        OneOrMore(hs_digit)]))
]))


def _parse_time(toks):
    time_str = toks[0]
    time_fmt = '%H:%M:%S'
    if '.' in time_str:
        time_fmt += '.%f'
    return [datetime.datetime.strptime(time_str, time_fmt).time()]


hs_time = hs_time_str.copy().setParseAction(_parse_time)
hs_isoDateTime = Combine(And([
    hs_date_str,
    hs_dateSep,
    hs_time_str,
    Optional(hs_tzHHMMOffset)
])).setParseAction(lambda toks: [iso8601.parse_date(toks[0].upper())])


def _parse_datetime(toks):
    # Made up of parts: ISO8601 Date/Time, time zone label
    isodt = toks[0]
    if len(toks) > 1:
        tzname = toks[1]
    else:
        tzname = None

    if (isodt.tzinfo is None) and bool(tzname):  # pragma: no cover
        # This technically shouldn't happen according to Zinc specs
        return [timezone(tzname).localise(isodt)]
    elif bool(tzname):
        try:
            tz = timezone(tzname)
            return [isodt.astimezone(tz)]
        except:  # pragma: no cover
            # Unlikely to occur, might do though if Project Haystack changes
            # its timezone list or if a system doesn't recognise a particular
            # timezone.
            return [isodt]  # Failed, leave alone
    else:
        return [isodt]


hs_dateTime = And([
    hs_isoDateTime,
    Optional(And([
        Suppress(Literal(' ')),
        hs_timeZoneName
    ]))
]).setParseAction(_parse_datetime)

# Quantities and raw numeric values
hs_unitChar = Or([
    hs_alpha,
    Word(u'%_/$' + u''.join([
        six.unichr(c)
        for c in range(0x0080, 0xffff)
    ]), exact=1)
])
hs_unit = Combine(OneOrMore(hs_unitChar))
hs_exp = Combine(And([
    CaselessLiteral('e'),
    Optional(hs_plusMinus),
    hs_digits
]))
hs_decimal = Combine(And([
    Optional(Literal('-')),
    hs_digits,
    Optional(And([
        Literal('.'),
        hs_digits
    ])),
    Optional(hs_exp)
])).setParseAction(lambda toks: [float(toks[0])])

hs_quantity = And([hs_decimal, hs_unit]).setParseAction(
    lambda toks: [Quantity(toks[0], unit=toks[1])])
hs_number = Or([
    hs_quantity,
    hs_decimal,
    Or([
        Literal('INF'),
        Literal('-INF'),
        Literal('NaN')
    ]).setParseAction(lambda toks: [float(toks[0])])
])

# URIs
hs_uriChar = Regex(r"([^\x00-\x1f\\`]|\\[bfnrt\\:/?" \
                   + r"#\[\]@&=;`]|\\[uU][0-9a-fA-F]{4})")
hs_uri = Combine(And([
    Suppress(Literal('`')),
    ZeroOrMore(hs_uriChar),
    Suppress(Literal('`'))
])).setParseAction(lambda toks: [Uri(_unescape(toks[0], uri=True))])

# Strings
hs_strChar = Regex(r"([^\x00-\x1f\\\"]|\\[bfnrt\\\"$]|\\[uU][0-9a-fA-F]{4})")
hs_str = Combine(And([
    Suppress(Literal('"')),
    ZeroOrMore(hs_strChar),
    Suppress(Literal('"'))
])).setParseAction(lambda toks: [_unescape(toks[0], uri=False)])

# References
hs_refChar = Or([hs_alpha, hs_digit, Word('_:-.~', exact=1)])
hs_ref = And([
    Suppress(Literal('@')),
    Combine(ZeroOrMore(hs_refChar)),
    Optional(And([
        Suppress(Literal(' ')),
        hs_str
    ]))
]).setParseAction(lambda toks: [ \
    Ref(toks[0], toks[1] if len(toks) > 1 else None) \
    ])

# Bins
hs_binChar = Regex(r"[\x20-\x27\x2a-\x7f]")
hs_bin = Combine(And([
    Suppress(Literal('Bin(')),
    Combine(ZeroOrMore(hs_binChar)),
    Suppress(Literal(')'))
])).setParseAction(lambda toks: [Bin(toks[0])])

# Haystack 3.0 XStr(...)
hs_xstr = And([
    Regex(r"[a-zA-Z0-9_]+"),
    Suppress(Literal('(')),
    hs_str,
    Suppress(Literal(')'))
]).setParseAction(lambda toks: [XStr(toks[0], toks[1])])

# Booleans
hs_bool = Word('TF', min=1, max=1, exact=1).setParseAction( \
    lambda toks: [toks[0] == 'T'])

# Singleton values
hs_remove = Literal('R').setParseAction( \
    lambda toks: [REMOVE]).setName('remove')
hs_marker = Literal('M').setParseAction( \
    lambda toks: [MARKER]).setName('marker')
hs_null = Literal('N').setParseAction( \
    lambda toks: [None]).setName('null')
hs_na = Literal('NA').setParseAction( \
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
hs_list = GenerateMatch( \
    lambda ver: Group(Or([ \
        Suppress(Regex(r'[ *]')), \
        And([ \
            Suppress(Regex(r'\[ *')), \
            Optional(DelimitedList( \
                hs_scalar[ver], \
                delim=hs_valueSep)), \
            Suppress(Optional(hs_valueSep)), \
            Suppress(Regex(r' *\]')) \
            ]) \
        ])).setParseAction(lambda toks: toks.asList()))
# Tag IDs
hs_id = Regex(r'[a-z][a-zA-Z0-9_]*').setName('id')

# Grid building blocks
hs_cell = GenerateMatch( \
    lambda ver: Or([Empty().copy().setParseAction(lambda toks: [None]), \
                    hs_scalar[ver]]).setName('cell'))

# Dict
# There are three cases:
# - Empty dict: { {optional whitespace} }
# - map with marker: { m }
# - dics: { k:1  ]
#
hs_tagmarker = hs_id

hs_tagpair = GenerateMatch(
    lambda ver: And([hs_id,
                     Suppress(Regex(r': *')),
                     hs_scalar[ver]
                     ])
        .setParseAction(lambda toks: tuple(toks[:2]))
        .setName('tagPair'))

hs_tag = GenerateMatch(
    lambda ver: Or([hs_tagmarker, hs_tagpair[ver]])
        .setName('tag'))

hs_tags = GenerateMatch(
    lambda ver: ZeroOrMore(Or([hs_tag[ver], \
                               Suppress(Regex(r'[ *]'))])) \
        .setName('tags'))


def to_dict(tokenlist):
    result = {}
    i = 0
    it = enumerate(tokenlist)
    for i, tok in it:
        if i < len(tokenlist) - 2 and tokenlist[i + 1] == ':':
            result[tokenlist[i]] = tokenlist[i + 2]
            next(it)
            next(it)
        else:
            if isinstance(tok, six.string_types):
                result[tok] = MARKER
            elif isinstance(tok, tuple):
                result[tok[0]] = tok[1]
            else:
                result[tok] = MARKER

    return result

# def to_dict(tokenlist):
#     result = {}
#     for i, tok in enumerate(tokenlist):
#         if isinstance(tok, six.string_types):
#             result[tok] = MARKER
#         else:
#             result[tok[0]] = tok[1]
#     return result


hs_dict = GenerateMatch(
    lambda ver: Or([
        Suppress(Regex(r'[ *]')),
        And([
            Suppress(Regex(r'{ *')),
            hs_tags[ver],
            Suppress(Regex(r' *}'))
        ])
    ])
        .setName("dict")
        .setParseAction(to_dict)
)

hs_inner_grid = GenerateMatch( \
    lambda ver: And([
        Suppress(Regex(r'<< *')),
        hs_grid[ver],
        Suppress(Regex(r' *>>')),
    ]))

# All possible scalar values, by Haystack version
hs_scalar_2_0 <<= Or([hs_ref, hs_bin, hs_str, hs_uri, hs_dateTime,
                      hs_date, hs_time, hs_coord, hs_number, hs_null, hs_marker,
                      hs_remove, hs_bool]).setName('scalar')
hs_scalar_3_0 <<= Or([hs_ref, hs_xstr, hs_str, hs_uri, hs_dateTime,
                      hs_date, hs_time, hs_coord, hs_number, hs_na, hs_null, hs_marker,
                      hs_remove, hs_bool, hs_list[VER_3_0], hs_dict[VER_3_0], hs_inner_grid[VER_3_0]]).setName('scalar')

hs_nl = Combine(And([Optional(Literal('\r')), Literal('\n')]))

hs_row = GenerateMatch( \
    lambda ver: Group(And([DelimitedList(hs_cell[ver], delim=hs_valueSep),
                           Suppress(Regex(r' *')),
                           Suppress(hs_nl)
                           ])).setName('row'))

hs_rows = GenerateMatch( \
    lambda ver: Group(ZeroOrMore(hs_row[ver])).setName("rows"))

hs_metaPair = GenerateMatch( \
    lambda ver: And([ \
        hs_id, \
        Suppress(And([ \
            ZeroOrMore(Literal(' ')), \
            Literal(':'), \
            ZeroOrMore(Literal(' ')) \
            ])), \
        hs_scalar[ver] \
        ]).setParseAction(lambda toks: [tuple(toks[:2])]).setName('metaPair'))
hs_metaMarker = hs_id.copy().setParseAction( \
    lambda toks: [(toks[0], MARKER)]).setName('metaMarker')
hs_metaItem = GenerateMatch( \
    lambda ver: Or([ \
        hs_metaMarker, \
        hs_metaPair[ver] \
        ]).setName('metaItem'))
hs_meta = GenerateMatch( \
    lambda ver: DelimitedList(hs_metaItem[ver], \
                              delim=' ').setParseAction( \
        lambda toks: [SortableDict(toks.asList())] \
        ).setName('meta'))

hs_col = GenerateMatch( \
    lambda ver: And([ \
        hs_id, \
        Optional(And([ \
            Suppress(Literal(' ')), \
            hs_meta[ver]
        ])).setName('colMeta') \
        ]).setParseAction(lambda toks: [ \
        (toks[0], toks[1] if len(toks) > 1 else {})]))

hs_cols = GenerateMatch( \
    lambda ver: And([
        DelimitedList(
            hs_col[ver], delim=hs_valueSep).setParseAction(  # + hs_nl
            lambda toks: [SortableDict(toks.asList())]),
        Suppress(Regex(r' *')),
        Suppress(hs_nl)
    ])
)

hs_gridVer = Combine(And([Suppress(Literal('ver:')) + hs_str]))


def _assign_ver(toks):
    ver = toks[0]
    if len(toks) > 1:
        grid_meta = toks[1]
    else:
        grid_meta = SortableDict()

    # Put 'ver' at the start
    grid_meta.add_item('ver', ver, index=0)
    return grid_meta


hs_gridMeta = GenerateMatch( \
    lambda ver: And([ \
        hs_gridVer, \
        Optional(And([ \
            Suppress(Literal(' ')), \
            hs_meta[ver] \
            ])).setName('gridMeta'),
        Suppress(Regex(r' *')),
        Suppress(hs_nl)
    ]).setParseAction(_assign_ver))  # + hs_nl


def _gen_grid(toks):
    (grid_meta, col_meta, rows) = toks
    if len(rows) == 1 and rows[0] == None:
        rows = []
    g = Grid(version=grid_meta.pop('ver'),
             metadata=grid_meta,
             columns=list(col_meta.items()))
    g.extend(map(lambda row: dict(zip(col_meta.keys(), row)), rows))
    return g


hs_grid_2_0 <<= And([ \
    hs_gridMeta[VER_2_0],
    hs_cols[VER_2_0],
    hs_rows[VER_2_0],
]).setParseAction(_gen_grid)

hs_grid_3_0 <<= And([ \
    hs_gridMeta[VER_3_0],
    hs_cols[VER_3_0],
    hs_rows[VER_3_0],
]).setParseAction(_gen_grid)


def parse_grid(grid_data, parseAll=True):
    """
    Parse the incoming grid.
    """
    try:
        # First element is the grid metadata
        ver_match = VERSION_RE.match(grid_data)
        if ver_match is None:
            raise ZincParseException(
                'Could not determine version from %r' % NEWLINE_RE.split(grid_data)[0],
                grid_data, 1, 1)
        version = Version(ver_match.group(1))

        # Now parse the grid of the grid accordingly
        g = hs_grid[version].parseString(grid_data, parseAll=parseAll)[0]
        return g
    except pp.ParseException as pe:
        LOG.debug('Failing grid: %r', grid_data)
        raise ZincParseException(
            'Failed to parse: %s' % reformat_exception(pe, pe.lineno),
            grid_data, pe.lineno, pe.col)
    except:
        LOG.debug('Failing grid: %r', grid_data)
        raise ZincParseException(
            'Failed to parse: %s' % sys.exc_info()[0], grid_data, 0, 0)


def parse_scalar(scalar_data, version):
    """
    Parse a Project Haystack scalar in ZINC format.
    """
    try:
        return hs_scalar[version].parseString(scalar_data, parseAll=True)[0]
    except pp.ParseException as pe:
        # Raise a new exception with the appropriate line number.
        raise ZincParseException(
            'Failed to parse scalar: %s' % reformat_exception(pe),
            scalar_data, 1, pe.col)
    except:
        LOG.debug('Failing scalar data: %r (version %r)',
                  scalar_data, version)
        raise
