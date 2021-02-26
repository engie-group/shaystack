# -*- coding: utf-8 -*-
# Zinc Grid dumper
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Tools for all parser and dumper
"""
import re
from typing import cast

_SPECIAL_CHAR = re.compile(r'([\a\b\f\n\r\t\v\"\\\u0080-\uffff])')
_MAP_CHAR = \
    {
        '\a': '\\a',
        '\b': '\\b',
        '\f': '\\f',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\v': '\\v',
        '\\': '\\\\',
        '"': '\\"',
    }


def _str_sub(match: re.Match) -> str:
    char = cast(str, match.group(0))
    order = ord(char)
    if order > 0x80:
        return '\\u%04x' % order
    if char in _MAP_CHAR:
        return _MAP_CHAR.get(char, char)
    return char


def escape_str(str_value: str) -> str:
    """
    Escape string
        Args:
            str_value: a string to escape
        Returns:
            escaped string
    """
    return _SPECIAL_CHAR.sub(_str_sub, str_value)
