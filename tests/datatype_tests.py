# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import hszinc
from copy import copy, deepcopy

def check_singleton_deepcopy(S):
    orig_dict = {'some_value': S}
    copy_dict = deepcopy(orig_dict)
    assert copy_dict['some_value'] is S

def test_marker_deepcopy():
    check_singleton_deepcopy(hszinc.MARKER)

def test_remove_deepcopy():
    check_singleton_deepcopy(hszinc.REMOVE)

def check_singleton_copy(S):
    assert copy(S) is S

def test_marker_copy():
    check_singleton_copy(hszinc.MARKER)

def test_remove_copy():
    check_singleton_copy(hszinc.REMOVE)
