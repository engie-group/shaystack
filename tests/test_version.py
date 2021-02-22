# -*- coding: utf-8 -*-
# Version handling/parsing tests
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import re
import sys
import warnings

from shaystack import Version


def test_malformed():
    try:
        Version('this is not a valid string')
        assert False, 'Accepted a bogus version string'
    except ValueError:
        pass


def test_str():
    assert str(Version('1.0')) == '1.0'
    assert str(Version('1.0a')) == '1.0a'


def test_str_cmp():
    assert Version('1.0') == '1.0'


def test_version_eq():
    assert Version('1') == Version('1.0')
    assert Version('1.0') == Version('1.0.0')
    assert Version('1.0a') == Version('1.0.0a')


def test_version_ne():
    assert Version('1.1') != Version('2.2')
    assert Version('1.0a') != Version('1.0')


def test_version_lt():
    assert Version('1.0') < Version('1.1')
    assert Version('1.9') < Version('1.10')
    assert Version('1.0') < Version('1.0a')
    assert Version('1.0a') < Version('1.0b')


def test_version_le():
    assert Version('1.0') <= Version('1.0')
    assert Version('1.0') <= Version('1.5')


def test_version_ge():
    assert Version('1.0') >= Version('1.0')
    assert Version('1.0') >= Version('0.9')


def test_version_gt():
    assert Version('1.0') > Version('0.9')
    assert Version('1.0a') > Version('1.0')
    assert Version('1.0b') > Version('1.0a')


_WARNING_RE = re.compile(
    r'This version of shift-4-haystack does not yet support version ([\d\\.]+), '
    r'please seek a newer version or file a bug. {2}Closest '
    r'\((older|newer)\) version supported is ([\d\\.]+).')


def _check_warning(warn):
    """
    Args:
        warn:
    """
    assert issubclass(warn.category, UserWarning)

    warning_match = _WARNING_RE.match(str(warn.message))
    assert warning_match is not None
    (detect_ver_str, older_newer, used_ver_str) = warning_match.groups()

    return (older_newer, Version(detect_ver_str),
            Version(used_ver_str))


def test_unsupported_old():
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter("always")
        assert Version.nearest("1.0") == Version("2.0")

        # Check we got a warning for that old crusty version.
        assert len(warn) == 1
        (older_newer, _, used_ver) = _check_warning(warn[-1])
        assert older_newer == 'newer'
        assert used_ver == Version('2.0')


def test_unsupported_newer():
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter("always")
        assert Version.nearest("2.5") == Version("3.0")

        # Work around Python 2.7 bug (https://tinyurl.com/y3omg4le)
        if sys.version_info[0:2] != (2, 7):
            # Check we got a warning for that oddball newer version.
            assert len(warn) == 1
            (older_newer, _, used_ver) = _check_warning(warn[-1])
            assert older_newer == 'newer'
            assert used_ver == Version('3.0')


def test_unsupported_bleedingedge():
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter("always")
        assert Version.nearest("9999.9999") == Version("3.0")

        # Check we got a warning for that bleeding edge version.
        assert len(warn) == 1
        (older_newer, _, used_ver) = _check_warning(warn[-1])
        assert older_newer == 'older'
        assert used_ver == Version('3.0')
