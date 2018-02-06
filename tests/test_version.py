# -*- coding: utf-8 -*-
# Version handling/parsing tests
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

from hszinc import Version

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
