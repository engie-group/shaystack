#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc grammar specification.
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si: 

import pyparsing as pp
import iso8601
import datetime
import string
import warnings
import six
import logging

import re

# Bring in special Project Haystack types and time zones
from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, REMOVE, Ref
from .grid import Grid
from .zoneinfo import timezone

# Bring in our sortable dict class to preserve order
from .sortabledict import SortableDict

# Bring in version handling
from .version import Version, LATEST_VER, VER_2_0, VER_3_0

# Logging instance for reporting debug info
LOG = logging.getLogger(__name__)

# All grids start with the version string.
VERSION_RE = re.compile(r'^ver:"(([^"\\]|\\[\\"bfnrt$])+)"')
NEWLINE_RE = re.compile(r'\r?\n')

# Convenience function, we want whitespace left alone.
def _leave_ws(cls, *args, **kwargs):
    return cls(*args, **kwargs).leaveWhitespace()

# Versions of the pyparsing types that leave our whitespace alone!
Empty           = lambda *a, **kwa : _leave_ws(pp.Empty, *a, **kwa)
Regex           = lambda *a, **kwa : _leave_ws(pp.Regex, *a, **kwa)
Literal         = lambda *a, **kwa : _leave_ws(pp.Literal, *a, **kwa)
CaselessLiteral = lambda *a, **kwa : _leave_ws(pp.CaselessLiteral, *a, **kwa)
Word            = lambda *a, **kwa : _leave_ws(pp.Word, *a, **kwa)
Optional        = lambda *a, **kwa : _leave_ws(pp.Optional, *a, **kwa)
Suppress        = lambda *a, **kwa : _leave_ws(pp.Suppress, *a, **kwa)
Combine         = lambda *a, **kwa : _leave_ws(pp.Combine, *a, **kwa)
And             = lambda *a, **kwa : _leave_ws(pp.And, *a, **kwa)
Or              = lambda *a, **kwa : _leave_ws(pp.Or, *a, **kwa)
ZeroOrMore      = lambda *a, **kwa : _leave_ws(pp.ZeroOrMore, *a, **kwa)
OneOrMore       = lambda *a, **kwa : _leave_ws(pp.OneOrMore, *a, **kwa)
Group           = lambda *a, **kwa : _leave_ws(pp.Group, *a, **kwa)
DelimitedList   = lambda *a, **kwa : _leave_ws(pp.delimitedList, *a, **kwa)
Forward         = lambda *a, **kwa : _leave_ws(pp.Forward, *a, **kwa)


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

        def use(v):
            g = self._known_grammars[v]
            self._known_grammars[ver] = g
            return g

        # We might not have an exact match for that.
        # See if we have one that's newer than the grid we're looking at.
        versions = list(self._known_grammars.keys())
        versions.sort(reverse=True)
        best = None
        for candidate in versions:
            # Due to ambiguities, we might have an exact match and not know it.
            # '2.0' will not hash to the same value as '2.0.0', but both are
            # equivalent.
            if candidate == ver:
                # We can't beat this, make a note of the match for later
                return use(candidate)

            # If we have not seen a better candidate, and this is older
            # then we may have to settle for that.
            if (best is None) and (candidate < ver):
                warnings.warn('This version of hszinc does not yet '\
                            'support version %s, please seek a newer version '\
                            'or file a bug.  Closest (older) version supported is %s.'\
                            % (ver, candidate))
                return use(candidate)

            # Probably the best so far, but see if we can go closer
            if candidate > ver:
                best = candidate

        # Unhappy path, no best option?  This should not happen.
        assert best is not None
        warnings.warn('This version of hszinc does not yet '\
                    'support version %s, please seek a newer version '\
                    'or file a bug.  Closest (newer) version supported is %s.'\
                    % (ver, best))
        return use(best)


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
hs_digit        = Regex(r'\d')
hs_digits       = Regex(r'[0-9_]+').setParseAction(
        lambda toks : [''.join([t.replace('_','') for t in toks[0]])])
hs_alphaLo      = Regex(r'[a-z]')
hs_alphaHi      = Regex(r'[A-Z]')
hs_alpha        = Regex(r'[a-zA-Z]')
hs_valueSep     = Regex(r' *, *').setName('valueSep')
hs_plusMinus    = Or([Literal('+'), Literal('-')])

# Forward declaration of data types.
hs_scalar_2_0   = Forward()
hs_scalar_3_0   = Forward()
hs_scalar = NearestMatch({
        VER_2_0: hs_scalar_2_0,
        VER_3_0: hs_scalar_3_0
})

# Co-ordinates
hs_coordDeg     = Combine(And([
        Optional(Literal('-')),
        Optional(hs_digits),
        Optional(And([Literal('.'), hs_digits]))
])).setParseAction(lambda toks : [float(toks[0] or '0')])
hs_coord        = And([Suppress(Literal('C(')),
                hs_coordDeg,
                Suppress(hs_valueSep),
                hs_coordDeg,
                Suppress(Literal(')'))]).setParseAction(
                        lambda toks : [Coordinate(toks[0], toks[1])])

# Dates and times
hs_tzHHMMOffset = Combine(Or([
        CaselessLiteral('z'),
        And([hs_plusMinus, Regex(r'\d\d:\d\d')])]
))
hs_tzName       = Regex(r'[A-Z][a-zA-Z0-9_\-]*')
hs_tzUTCGMT     = Or([Literal('UTC'), Literal('GMT')])
hs_tzUTCOffset  = Combine(And([
    hs_tzUTCGMT, Optional(
        Or([Literal('0'),
            And([hs_plusMinus, OneOrMore(hs_digit)]
        )]
    ))]))
hs_timeZoneName = Or([hs_tzUTCOffset, hs_tzName])
hs_dateSep      = CaselessLiteral('T')
hs_date_str     = Combine(And([
    hs_digit, hs_digit, hs_digit, hs_digit,
    Literal('-'),
    hs_digit, hs_digit,
    Literal('-'),
    hs_digit, hs_digit]))
hs_date         = hs_date_str.copy().setParseAction(
        lambda toks : [datetime.datetime.strptime(toks[0], '%Y-%m-%d').date()])

hs_time_str     = Combine(And([
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
hs_time         = hs_time_str.copy().setParseAction(_parse_time)
hs_isoDateTime  = Combine(And([
    hs_date_str,
    hs_dateSep,
    hs_time_str,
    Optional(hs_tzHHMMOffset)
])).setParseAction(lambda toks : [iso8601.parse_date(toks[0].upper())])

def _parse_datetime(toks):
    # Made up of parts: ISO8601 Date/Time, time zone label
    isodt = toks[0]
    if len(toks) > 1:
        tzname = toks[1]
    else:
        tzname = None

    if (isodt.tzinfo is None) and bool(tzname): # pragma: no cover
        # This technically shouldn't happen according to Zinc specs
        return [timezone(tzname).localise(isodt)]
    elif bool(tzname):
        try:
            tz = timezone(tzname)
            return [isodt.astimezone(tz)]
        except: # pragma: no cover
            # Unlikely to occur, might do though if Project Haystack changes
            # its timezone list or if a system doesn't recognise a particular
            # timezone.
            return [isodt]  # Failed, leave alone
    else:
        return [isodt]
hs_dateTime     = And([
    hs_isoDateTime,
    Optional(And([
        Suppress(Literal(' ')),
        hs_timeZoneName
        ]))
    ]).setParseAction(_parse_datetime)

# Quantities and raw numeric values
hs_unitChar     = Or([
    hs_alpha,
    Word(u'%_/$' + u''.join([
        six.unichr(c)
        for c in range(0x0080, 0xffff)
    ]), exact=1)
])
hs_unit         = Combine(OneOrMore(hs_unitChar))
hs_exp          = Combine(And([
    CaselessLiteral('e'),
    Optional(hs_plusMinus),
    hs_digits
]))
hs_decimal      = Combine(And([
    Optional(Literal('-')),
    hs_digits,
    Optional(And([
        Literal('.'),
        hs_digits
    ])),
    Optional(hs_exp)
])).setParseAction(lambda toks : [float(toks[0])])

hs_quantity     = And([hs_decimal, hs_unit]).setParseAction(
        lambda toks : [Quantity(toks[0], unit=toks[1])])
hs_number       = Or([
    hs_quantity,
    hs_decimal,
    Or([
        Literal('INF'),
        Literal('-INF'),
        Literal('NaN')
    ]).setParseAction(lambda toks : [float(toks[0])])
])

# URIs
hs_uriChar      = Regex(r"([^\x00-\x1f\\`]|\\[bfnrt\\:/?" \
                        + r"#\[\]@&=;`]|\\[uU][0-9a-fA-F]{4})")
hs_uri          = Combine(And([
    Suppress(Literal('`')),
    ZeroOrMore(hs_uriChar),
    Suppress(Literal('`'))
])).setParseAction(lambda toks : [Uri(_unescape(toks[0], uri=True))])

# Strings
hs_strChar      = Regex(r"([^\x00-\x1f\\\"]|\\[bfnrt\\\"$]|\\[uU][0-9a-fA-F]{4})")
hs_str          = Combine(And([
    Suppress(Literal('"')),
    ZeroOrMore(hs_strChar),
    Suppress(Literal('"'))
])).setParseAction(lambda toks : [_unescape(toks[0], uri=False)])

# References
hs_refChar      = Or([hs_alpha, hs_digit, Word('_:-.~', exact=1)])
hs_ref          = And([
    Suppress(Literal('@')),
    Combine(ZeroOrMore(hs_refChar)),
    Optional(And([
        Suppress(Literal(' ')),
        hs_str
    ]))
]).setParseAction(lambda toks : [\
        Ref(toks[0], toks[1] if len(toks) > 1 else None)\
])

# Bins
hs_binChar      = Regex(r"[\x20-\x27\x2a-\x7f]")
hs_bin          = Combine(And([
    Suppress(Literal('Bin(')),
    Combine(ZeroOrMore(hs_binChar)),
    Suppress(Literal(')'))
])).setParseAction(lambda toks : [Bin(toks[0])])

# Booleans
hs_bool         = Word('TF', min=1, max=1, exact=1).setParseAction(\
        lambda toks : [toks[0] == 'T'])

# Singleton values
hs_remove       = Literal('R').setParseAction(\
        lambda toks : [REMOVE]).setName('remove')
hs_marker       = Literal('M').setParseAction(\
        lambda toks : [MARKER]).setName('marker')
hs_null         = Literal('N').setParseAction(\
        lambda toks : [None]).setName('null')

# Lists, these will probably be in Haystack 4.0, so let's not
# assume a version.  There are three cases:
# - Empty list: [ {optional whitespace} ]
# - List *with* trailing comma: [ 1, 2, 3, ]
# - List without trailing comma: [ 1, 2, 3 ]
#
# We need to handle this trailing separator case.  That for now means
# that a NULL within a list *MUST* be explicitly given using the 'N'
# literal: we cannot support implicit NULLs as they are ambiguous.
hs_list         = GenerateMatch(                            \
        lambda ver : Group(Or([                             \
            Suppress(Regex(r'[ *]')),                       \
            And([                                           \
                Suppress(Regex(r'\[ *')),                   \
                Optional(DelimitedList(                     \
                        hs_scalar[ver],                     \
                        delim=hs_valueSep)),                \
                Suppress(Optional(hs_valueSep)),            \
                Suppress(Regex(r' *\]'))                    \
            ])                                              \
        ])).setParseAction(lambda toks : toks.asList()))

# All possible scalar values, by Haystack version
hs_scalar_2_0 <<= Or([hs_ref, hs_bin, hs_str, hs_uri, hs_dateTime,
            hs_date, hs_time, hs_coord, hs_number, hs_null, hs_marker,
            hs_remove, hs_bool]).setName('scalar')
hs_scalar_3_0 <<= Or([hs_ref, hs_bin, hs_str, hs_uri, hs_dateTime,
            hs_date, hs_time, hs_coord, hs_number, hs_null, hs_marker,
            hs_remove, hs_bool, hs_list[VER_3_0]]).setName('scalar')

# Tag IDs
hs_id           = Regex(r'[a-z][a-zA-Z0-9_]*').setName('id')

# Grid building blocks
hs_cell         = GenerateMatch(                                                \
        lambda ver : Or([Empty().copy().setParseAction(lambda toks : [None]),   \
                        hs_scalar[ver]]).setName('cell'))
hs_nl           = Combine(And([Optional(Literal('\r')), Literal('\n')]))

hs_row          = GenerateMatch(\
        lambda ver : Group(DelimitedList(hs_cell[ver], delim=hs_valueSep)))
hs_metaPair     = GenerateMatch(\
        lambda ver : And([ \
            hs_id, \
            Suppress(And([ \
                ZeroOrMore(Literal(' ')), \
                Literal(':'), \
                ZeroOrMore(Literal(' ')) \
            ])), \
            hs_scalar[ver] \
        ]).setParseAction(lambda toks : [tuple(toks[:2])]).setName('metaPair'))
hs_metaMarker   = hs_id.copy().setParseAction(\
        lambda toks : [(toks[0], MARKER)]).setName('metaMarker')
hs_metaItem     = GenerateMatch(\
        lambda ver : Or([\
                hs_metaMarker, \
                hs_metaPair[ver]\
            ]).setName('metaItem'))
hs_meta         = GenerateMatch(\
        lambda ver : DelimitedList(hs_metaItem[ver], \
                delim=' ').setParseAction(\
                    lambda toks : [SortableDict(toks.asList())] \
            ).setName('meta'))

hs_col          = GenerateMatch(\
        lambda ver : And([ \
            hs_id, \
            Optional(And([ \
                Suppress(Literal(' ')), \
                hs_meta[ver]
            ])).setName('colMeta') \
        ]).setParseAction(lambda toks : [\
            (toks[0], toks[1] if len(toks) > 1 else {})]))

hs_cols         = GenerateMatch(\
        lambda ver : DelimitedList(
            hs_col[ver], delim=hs_valueSep).setParseAction( # + hs_nl
                lambda toks : [SortableDict(toks.asList())]))

hs_gridVer      = Combine(And([Suppress(Literal('ver:')) + hs_str]))

def _assign_ver(toks):
    ver = toks[0]
    if len(toks) > 1:
        grid_meta = toks[1]
    else:
        grid_meta = SortableDict()

    # Put 'ver' at the start
    grid_meta.add_item('ver', ver, index=0)
    return grid_meta
hs_gridMeta     = GenerateMatch(\
        lambda ver : And([ \
            hs_gridVer, \
            Optional(And([ \
                Suppress(Literal(' ')), \
                hs_meta[ver] \
            ])).setName('gridMeta')
        ]).setParseAction(_assign_ver)) # + hs_nl


def parse_grid(grid_data):
    """
    Parse the incoming grid.
    """
    # Split the grid up.
    grid_parts = NEWLINE_RE.split(grid_data)
    if len(grid_parts) < 2:
        raise ValueError('Malformed grid received')

    # Grid and column metadata are the first two lines.
    grid_meta_str = grid_parts.pop(0)
    col_meta_str = grid_parts.pop(0)

    # First element is the grid metadata
    ver_match = VERSION_RE.match(grid_meta_str)
    if ver_match is None:
        raise ValueError('Could not determine version from %r' % grid_meta_str)
    version = Version(ver_match.group(1))

    # Now parse the rest of the grid accordingly
    try:
        grid_meta = hs_gridMeta[version].parseString(grid_meta_str, parseAll=True)[0]
    except: # pragma: no cover
        # Report an error to the log if we fail to parse something.
        LOG.debug('Failed to parse grid meta: %r', grid_meta_str)
        raise

    try:
        col_meta = hs_cols[version].parseString(col_meta_str, parseAll=True)[0]
    except: # pragma: no cover
        # Report an error to the log if we fail to parse something.
        LOG.debug('Failed to parse column meta: %r', col_meta_str)
        raise

    row_grammar = hs_row[version]
    def _parse_row(row):
        try:
            return dict(zip(col_meta.keys(),
                row_grammar.parseString(row, parseAll=True)[0].asList()))
        except: # pragma: no cover
            # Report an error to the log if we fail to parse something.
            LOG.debug('Failed to parse row: %r', row)
            raise

    g = Grid(version=grid_meta.pop('ver'),
            metadata=grid_meta,
            columns=list(col_meta.items()))
    g.extend(map(_parse_row, filter(lambda gp : bool(gp), grid_parts)))
    return g


def parse_scalar(scalar_data, version):
    """
    Parse a Project Haystack scalar in ZINC format.
    """
    return hs_scalar[version].parseString(scalar_data, parseAll=True)[0]
