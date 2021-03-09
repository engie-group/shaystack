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


def unescape_str(a_string: str, uri: bool = False) -> str:
    """Iterative parser for string escapes.
    """
    out = ''
    while len(a_string) > 0:
        char = a_string[0]
        if char == '\\':
            # Backslash escape
            esc_c = a_string[1]

            if esc_c in ('u', 'U'):
                # Unicode escape
                out += chr(int(a_string[2:6], base=16))
                a_string = a_string[6:]
                continue
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
            elif esc_c == 'v':
                out += '\v'
            elif esc_c == '\\':
                out += '\\'
            else:
                if uri and (esc_c == '#'):
                    # \# is passed through with backslash.
                    out += '\\'
                # Pass through
                out += esc_c
            a_string = a_string[2:]
            continue
        out += char
        a_string = a_string[1:]
    return out
