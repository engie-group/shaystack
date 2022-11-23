# -*- coding: utf-8 -*-
# Filter parser
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Parse the filter syntax to produce a FilterAST.
See https://project-haystack.org/doc/docHaystack/Filters
"""
from datetime import datetime, date, time, timedelta, tzinfo
from functools import lru_cache
from typing import Any, List, Callable, Tuple

from pyparsing import ZeroOrMore, Literal, Forward, Suppress

from . import Grid
from .datatypes import Ref, XStr, MARKER, NA, REMOVE
from .filter_ast import FilterPath, FilterBinary, FilterUnary, FilterAST, FilterNode
from .type import Entity
from .zincparser import hs_scalar_3_0, hs_id, hs_all_date, hs_date, \
    hs_time, pyparser_lock

# Necessary for generated code
_ = XStr
_ = MARKER  # type: ignore
_ = NA  # type: ignore
_ = REMOVE  # type: ignore


def _merge_and_or(key: str, toks: List[FilterBinary]) -> FilterBinary:
    if len(toks) == 1:
        return toks[0]
    return FilterBinary(key, _merge_and_or(key, toks[:-2]), toks[-1])


hs_filter = Forward()
hs_bool = (Literal("true") | "false").setParseAction(
    lambda toks: toks[0] == "true"
)  # Extension to accept T or F
hs_val = hs_scalar_3_0 ^ hs_bool

hs_path = (hs_id + ZeroOrMore(Suppress("->") + hs_id)).setParseAction(
    lambda toks: FilterPath(list(toks))
)
hs_cmpOp = Literal("==") | "!=" | "<=" | ">=" | "<" | ">"
hs_cmp = (hs_path + hs_cmpOp + hs_val).setParseAction(
    lambda toks: FilterBinary(toks[1], toks[0], toks[2])
)
hs_missing = (Suppress("not") + hs_path).setParseAction(
    lambda toks: FilterUnary("not", toks[0])
)
hs_has = hs_path.copy().setParseAction(
    lambda toks: FilterUnary("has", FilterPath(list(toks)))
)

hs_parens = (Suppress("(") + hs_filter + Suppress(")")).setParseAction(
    lambda toks: toks[0]
)
hs_term = hs_parens | hs_missing | hs_cmp | hs_has

hs_condAnd = (hs_term + ZeroOrMore("and" + hs_term)).setParseAction(
    lambda toks: _merge_and_or("and", toks)
)
hs_condOr = (hs_condAnd + ZeroOrMore("or" + hs_condAnd)).setParseAction(
    lambda toks: _merge_and_or("or", toks)
)
hs_filter <<= hs_condOr


def parse_filter(grid_filter: str) -> FilterAST:
    """Return an AST tree of filter. Can be used to generate other language
    (Python, SQL, etc.)

    Args:
        grid_filter: A filter request
    Returns:
        A `FilterAST`
    """
    with pyparser_lock:
        return FilterAST(hs_filter.parseString(grid_filter, parseAll=True)[0])


# --- Generate python to apply filter
# Maximum number of generated python function
_FILTER_CACHE_LRU_SIZE = 500
# Id of next generated function
_ID_FUNCTION = 0  # pylint: disable=C0103


class _NotFoundValue:
    """ Hack to easely manage the 'not found' value.
    All operators return `False`.
    """

    def __repr__(self):
        return 'NOT_FOUND'

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return False

    def __ne__(self, other: Any) -> bool:
        return False

    def __lt__(self, other: Any) -> bool:
        return False

    def __le__(self, other: Any) -> bool:
        return False

    def __gt__(self, other: Any) -> bool:
        return False

    def __ge__(self, other: Any) -> bool:
        return False


NOT_FOUND = _NotFoundValue()


def _get_path(grid: Grid, obj: Any, paths: List[str]) -> Any:
    """
    Return the value at a specific path.

    Args:
        grid: The root grid to use.
        obj: The current object
        paths: The path to apply
    Returns:
        The value of the tag at this `path`
    """
    try:
        for i, path in enumerate(paths):
            obj = obj[path]
            if i != len(paths) - 1 and isinstance(obj, Ref):
                obj = grid[obj]  # Follow the reference
        if obj is None:      #not obj and obj != 0:
            return NOT_FOUND
        return obj  # It's a value at this time
    except TypeError:
        return NOT_FOUND
    except KeyError:
        return NOT_FOUND


def _generate_filter_in_python(node: FilterNode, def_filter: List[str]) -> List[str]:
    """
    Generate a partial python code to represent the current node.
    Args:
        node: Node to convert to python
        def_filter: Current generated code.
    Returns:
        The extends generated code.
    """
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
    """
    A wrapper to manage the lifecycle of generated python methods.
    Can be used with @lru to remove the generated method if this wrapper is deleted.
    Args:
        fun_name: The function name to manage.
        function_template: The body of the function.
    """
    __slots__ = ("fun_name",)

    def __init__(self, fun_name: str, function_template: str):
        self.fun_name = fun_name
        # Import the function inside Python engine
        exec(function_template, globals(), globals())  # pylint: disable=W0122

    def __del__(self) -> None:  # pragma: no cover
        # Remove the corresponding python function from Python engine
        del globals()[self.fun_name]  # Remove generated function if the LRU ask that

    def get(self) -> Callable[[Grid, Entity], bool]:
        # Gest the python function.
        return globals()[self.fun_name]


def _filter_to_python(grid_filter: str) -> Tuple[str, str]:
    global _ID_FUNCTION  # pylint: disable=global-statement
    def_filter = _generate_filter_in_python(
        parse_filter(grid_filter).head, [])   # type: ignore
    func_name = "_gen_hsfilter_" + str(_ID_FUNCTION)
    function_template = "def %s(_grid, _entity):\n  return " % func_name + "".join(def_filter)
    _ID_FUNCTION += 1
    return func_name, function_template


@lru_cache(maxsize=_FILTER_CACHE_LRU_SIZE)
def _filter_function(grid_filter: str) -> _FnWrapper:
    """
    Generate and manage the life cycle of generation python function.
    Args:
        grid_filter: The filter request
    Returns:
        A wrapper to manage the life cycle of generated function
    """
    func_name, function_template = _filter_to_python(grid_filter)
    return _FnWrapper(func_name, function_template)


def filter_set_lru_size(lru_size: int) -> None:
    """Change the lru size for the compiled filter functions.

    Args:
        lru_size: The new LRU size
    """
    # noinspection PyGlobalUndefined
    global _filter_function  # pylint: disable=W0601, C0103
    # noinspection PyUnresolvedReferences
    original_function = _filter_function.__wrapped__  # pylint: disable=E1101
    _filter_function = lru_cache(lru_size, original_function)  # type: ignore


def filter_function(grid_filter: str) -> Callable[[Grid, Entity], bool]:
    """
    Convert the request filter to a python function.

    Args:
        grid_filter: The request filter.
    Returns:
        The corresponding python function to apply to the grid
    """
    return _filter_function(grid_filter).get()


def parse_hs_datetime_format(datetime_str: str, timezone: tzinfo) -> datetime:
    """
    Parse the haystack date time (for filter).
    Args:
        datetime_str: The string to parse
        timezone: Time zone info
    Returns:
        the corresponding `datetime`
    Raises:
        `pyparsing.ParseException` if the string does not conform
    """
    if datetime_str == "today":
        return datetime.combine(date.today(), datetime.min.time()) \
            .replace(tzinfo=timezone)
    if datetime_str == "yesterday":
        return datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
            .replace(tzinfo=timezone)

    return hs_all_date.parseString(datetime_str, parseAll=True)[0]


def parse_hs_date_format(date_str) -> date:
    """
    Parse the haystack date (for filter).
    Args:
        date_str: The string to parse
    Returns:
        the corresponding `date`
    Raises:
        `pyparsing.ParseException` if the string does not conform
    """
    return hs_date.parseString(date_str, parseAll=True)[0]


def parse_hs_time_format(time_str) -> time:
    """
    Parse the haystack date (for filter).
    Args:
        time_str: The string to parse
    Returns:
        the corresponding `time`
    Raises:
        `pyparsing.ParseException` if the string does not conform
    """
    return hs_time.parseString(time_str, parseAll=True)[0]
