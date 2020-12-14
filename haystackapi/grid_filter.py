#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
from datetime import datetime
from functools import lru_cache

from iso8601 import iso8601
from pyparsing import Word, ZeroOrMore, Literal, Forward, Combine, Optional, Regex, OneOrMore, \
    CaselessLiteral, Suppress, Group

from .datatypes import REMOVE, MARKER, Coordinate, NA, Bin, Ref, XStr, Uri, Quantity
from .filter_ast import FilterPath, FilterBinary, FilterUnary, FilterAST
from .zincparser import DelimitedList, to_dict
from .zoneinfo import timezone

hs_filter = Forward()
hs_strChar = Regex(r"([^\x00-\x1f\\\"]|\\[bfnrt\\\"$]|\\[uU][0-9a-fA-F]{4})")
hs_str = Combine(Suppress(Literal('"')) + ZeroOrMore(hs_strChar) + Suppress(Literal('"')))
hs_uriChar = Regex(r"([^\x00-\x1f\\`]|\\[bfnrt\\:/?"
                   + r"#\[\]@&=;`]|\\[uU][0-9a-fA-F]{4})")
hs_uri = Combine(Suppress(Literal('`')) + ZeroOrMore(hs_uriChar) + Suppress(Literal('`'))).setParseAction(
    lambda toks: Uri(toks[0])
)
hs_digits = Regex(r'[0-9_]+')
hs_alpha = Regex(r'[a-zA-Z]')
hs_valueSep = Regex(r' *, *')
hs_plusMinus = Literal('+') | Literal('-')
hs_exp = Combine(CaselessLiteral('e') + Optional(hs_plusMinus) + hs_digits)
hs_decimal = Combine(
    Optional(Literal('-')) + hs_digits + Optional(Literal('.') + hs_digits) + Optional(hs_exp)).setParseAction(
    lambda toks: float(toks[0])
)
hs_unitChar = hs_alpha | Word(u'%_/$' + u''.join([
    chr(c) for c in range(0x0080, 0xffff)
]), exact=1)
hs_unit = Combine(OneOrMore(hs_unitChar))
hs_digit = Regex(r'\d')
hs_digits = Regex(r'[0-9_]+')
hs_quantity = (hs_decimal + hs_unit).leaveWhitespace().setParseAction(
    lambda toks: Quantity(toks[0], toks[1])
)
hs_number = hs_quantity | hs_decimal | Literal('INF') | Literal("-INF") | Literal("Nan")
hs_bool = (Literal("true") | Literal("false")).setParseAction(
    lambda toks: toks[0] == "true"
)  # Extension to accept T or F
hs_id = Regex(r'[a-z][a-zA-Z0-9_]*')
hs_name = hs_id

hs_coordDeg = Combine(
    Optional(Literal('-')) +
    Optional(Regex(r'[0-9]+')) +
    Optional(Literal('.') + Regex(r'[0-9]+'))).setParseAction(
    lambda toks: [float(toks[0])]
)

hs_coord = (Suppress(Literal('C(')) +
            hs_coordDeg +
            Suppress(hs_valueSep) +
            hs_coordDeg +
            Suppress(Literal(')'))).setParseAction(
    lambda toks: Coordinate(toks[0], toks[1])
)

# Singleton values
hs_remove = Literal('R').setParseAction(
    lambda toks: [REMOVE]).setName('remove')
hs_marker = Literal('M').setParseAction(
    lambda toks: [MARKER]).setName('marker')
hs_null = Literal('N').setParseAction(
    lambda toks: [None]).setName('null')
hs_na = Literal('NA').setParseAction(
    lambda toks: [NA]).setName('na')

hs_binChar = Regex(r"[\x20-\x27\x2a-\x7f]")
hs_bin = Combine(
    Suppress(Literal('Bin(')) +
    Combine(ZeroOrMore(hs_binChar)) +
    Suppress(Literal(')'))
).setParseAction(
    lambda toks: [Bin(toks[0])]
)

hs_xstr = (Regex(r"[a-zA-Z0-9_]+") +
           Suppress(Literal('(')) +
           hs_str +
           Suppress(Literal(')'))).setParseAction(
    lambda toks: [XStr(toks[0], toks[1])]
)

hs_dateSep = CaselessLiteral('T')
hs_date_str = Combine(
    hs_digit + hs_digit + hs_digit + hs_digit +
    Literal('-') +
    hs_digit + hs_digit +
    Literal('-') +
    hs_digit + hs_digit)
hs_date = hs_date_str.copy().setParseAction(
    lambda toks: [datetime.strptime(toks[0], '%Y-%m-%d').date()])

hs_time_str = Combine(
    hs_digit + hs_digit +
    Literal(':') +
    hs_digit + hs_digit +
    Literal(':') +
    hs_digit + hs_digit +
    Optional(
        Literal('.') +
        OneOrMore(hs_digit)))


def _parse_time(toks):
    time_str = toks[0]
    time_fmt = '%H:%M:%S'
    if '.' in time_str:
        time_fmt += '.%f'
    return [datetime.strptime(time_str, time_fmt).time()]


hs_time = hs_time_str.copy().setParseAction(_parse_time)

hs_tzHHMMOffset = Combine(
    CaselessLiteral('z') |
    (hs_plusMinus + Regex(r'\d\d:\d\d')))

hs_isoDateTime = Combine(
    hs_date_str +
    hs_dateSep +
    hs_time_str +
    Optional(hs_tzHHMMOffset)).setParseAction(
    lambda toks: [iso8601.parse_date(toks[0].upper())]
)

hs_tzName = Regex(r'[A-Z][a-zA-Z0-9_\-]*')
hs_tzUTCGMT = Literal('UTC') | Literal('GMT')
hs_tzUTCOffset = Combine(
    hs_tzUTCGMT + Optional(
        Literal('0') | (hs_plusMinus + OneOrMore(hs_digit))))
hs_timeZoneName = hs_tzUTCOffset | hs_tzName


def _parse_datetime(toks):
    # Made up of parts: ISO8601 Date/Time, time zone label
    isodt = toks[0]
    if len(toks) > 1:
        tzname = toks[1]
    else:
        tzname = None

    if (isodt.tzinfo is None) and bool(tzname):  # pragma: no cover
        # This technically shouldn't happen according to Zinc specs
        return [timezone(tzname).localize(isodt)]
    if bool(tzname):
        try:
            return [isodt.astimezone(timezone(tzname))]
        except:  # noqa: E722 pragma: no cover
            # Unlikely to occur, might do though if Project Haystack changes
            # its timezone list or if a system doesn't recognise a particular
            # timezone.
            return [isodt]  # Failed, leave alone
    else:
        return [isodt]


hs_dateTime = (hs_isoDateTime +
               Optional(
                   hs_timeZoneName
               )).setParseAction(_parse_datetime)

hs_val = Forward()
hs_list = Group(
    Suppress(Regex(r'[ *]')) |
    (Suppress(Regex(r'\[ *')) +
     Optional(DelimitedList(
         hs_val,
         delim=hs_valueSep)) +
     Suppress(Regex(r' *\]'))
     )
).setParseAction(lambda toks: toks.asList())

hs_tagmarker = hs_id
hs_tagpair = hs_id + Literal(':') + hs_val
hs_tag = hs_tagpair | hs_tagmarker

hs_tags = ZeroOrMore(hs_tag)

hs_dict = (Suppress(Literal('{')) +
           hs_tags +
           Suppress(Literal('}'))).setParseAction(to_dict)

hs_refChar = hs_alpha | hs_digit | Word('_:-.~', exact=1)
hs_ref = (Suppress(Literal('@')) + Combine(ZeroOrMore(hs_refChar)) + Optional(
    hs_str)).setParseAction(
    lambda toks: [Ref(toks[0], toks[1] if len(toks) > 1 else None)])

hs_all_date = hs_dateTime | hs_date | hs_time
hs_val <<= hs_list | hs_dict | \
           hs_ref | hs_bin | hs_xstr | \
           hs_all_date | \
           hs_coord | \
           hs_number | hs_na | hs_null | hs_marker | hs_bool | \
           hs_str | hs_uri

# -------------------------------------
hs_path = (hs_name + ZeroOrMore(Suppress(Literal("->")) + hs_name)).setParseAction(
    lambda toks: FilterPath(list(toks))
)
hs_cmpOp = Literal("==") | Literal("!=") | Literal("<=") | Literal(">=") | Literal("<") | Literal(">")
hs_cmp = (hs_path + hs_cmpOp + hs_val).setParseAction(
    lambda toks: FilterBinary(toks[1], toks[0], toks[2])
)
hs_missing = (Suppress(Literal("not")) + hs_path).setParseAction(
    lambda toks: FilterUnary("not", toks[0])
)
hs_has = hs_path.copy().setParseAction(
    lambda toks: FilterUnary("has", FilterPath(list(toks)))
)

hs_parens = (Suppress(Literal("(")) + hs_filter + Suppress(Literal(")"))).setParseAction(
    lambda toks: toks[0]
)
hs_term = hs_parens | hs_missing | hs_cmp | hs_has


def _merge_and_or(key, toks):
    if len(toks) == 1:
        return toks[0]
    return FilterBinary(key, _merge_and_or(key, toks[:-2]), toks[-1])


hs_condAnd = (hs_term + ZeroOrMore(Literal("and") + hs_term)).setParseAction(
    lambda toks: _merge_and_or("and", toks)
)
hs_condOr = (hs_condAnd + ZeroOrMore(Literal("or") + hs_condAnd)).setParseAction(
    lambda toks: _merge_and_or("or", toks)
)
hs_filter <<= hs_condOr


def parse_filter(grid_filter):
    """
    Return an AST tree of filter.
    Can be used to generate other language (SQL, etc.)
    """
    return FilterAST(hs_filter.parseString(grid_filter, parseAll=True)[0])


# --- Generate python to apply filter
FILTER_CACHE_LRU_SIZE = 500
_id_function = 0  # pylint: disable=C0103


class _NotFoundValue:
    def __repr__(self):
        return 'NOT_FOUND'

    def __bool__(self):
        return False

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return False

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False


NOT_FOUND = _NotFoundValue()


def _get_path(grid, obj, paths):
    try:
        for i, path in enumerate(paths):
            obj = obj[path]
            if i != len(paths) - 1 and isinstance(obj, Ref):
                obj = grid[obj]  # Follow the reference
        if not obj:
            return NOT_FOUND
        return obj  # It's a value at this time
    except KeyError:
        return NOT_FOUND


def _generate_filter_in_python(node, def_filter):
    if isinstance(node, FilterPath):
        def_filter.append("_get_path(_grid, _entity, %s)" % node.paths)
    elif isinstance(node, FilterBinary):
        def_filter.append("(")
        _generate_filter_in_python(node.left, def_filter)
        def_filter.append(" " + node.operator + " ")
        _generate_filter_in_python(node.right, def_filter)
        def_filter.append(")")
    elif isinstance(node, FilterUnary):
        if node.operator == "has":
            def_filter.append('(id(')
            _generate_filter_in_python(node.right, def_filter)
            def_filter.append(') !=  id(NOT_FOUND))')
        elif node.operator == "not":
            def_filter.append('(id(')
            _generate_filter_in_python(node.right, def_filter)
            def_filter.append(") == id(NOT_FOUND))")
        else:  # pragma: no cover
            assert 0
    else:
        def_filter.append(repr(node))
    return def_filter


class _FnWrapper:
    def __init__(self, fun_name, function_template):
        self.fun_name = fun_name
        exec(function_template, globals(), globals())  # pylint: disable=W0122

    def __del__(self):  # pragma: no cover
        del globals()[self.fun_name]  # Remove generated function if the LRU ask that

    def get(self):
        return globals()[self.fun_name]


@lru_cache(maxsize=FILTER_CACHE_LRU_SIZE)
def _filter_function(grid_filter):
    global _id_function  # pylint: disable=C0103
    def_filter = _generate_filter_in_python(parse_filter(grid_filter)._head, [])
    fun_name = "_gen_hsfilter_" + str(_id_function)
    function_template = "def %s(_grid, _entity):\n  return " % fun_name + "".join(def_filter)
    # print("\nGenerate:\n# " + grid_filter + "\n" + function_template)  # For debug
    _id_function += 1
    return _FnWrapper(fun_name, function_template)


def filter_set_lru_size(lru_size):
    """ Change the lru size for the compiled filter functions """
    global _filter_function  # pylint: disable=W0601, C0103
    original_function = _filter_function.__wrapped__  # pylint: disable=E1101
    _filter_function = lru_cache(lru_size, original_function)  # type: ignore


def filter_function(grid_filter):
    return _filter_function(grid_filter).get()


# FIXME: avec graphql, les dates sont au format "YYYY-MM-DD HH:MM" avec espace. Pb de conv.
def parse_hs_date_format(date_str) -> datetime:
    return hs_all_date.parseString(date_str, parseAll=True)[0]
