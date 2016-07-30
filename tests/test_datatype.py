# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

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

def test_ref_notref_eq():
    r1 = hszinc.Ref(name='a.ref')
    r2 = 'not.a.ref'
    assert r1 is not r2
    try:
        if r1 != r2:
            assert False, 'Somehow compared ref to string'
    except TypeError:
        pass

def test_ref_simple_eq():
    r1 = hszinc.Ref(name='a.ref')
    r2 = hszinc.Ref(name='a.ref')
    assert r1 is not r2
    assert r1 == r2

def test_ref_simple_neq_id():
    r1 = hszinc.Ref(name='a.ref')
    r2 = hszinc.Ref(name='another.ref')
    assert r1 is not r2
    assert r1 != r2

def test_ref_mixed_neq():
    r1 = hszinc.Ref(name='a.ref')
    r2 = hszinc.Ref(name='a.ref', value='display text')
    assert r1 is not r2
    assert r1 != r2

def test_ref_withdis_eq():
    r1 = hszinc.Ref(name='a.ref', value='display text')
    r2 = hszinc.Ref(name='a.ref', value='display text')
    assert r1 is not r2
    assert r1 == r2

def test_ref_withdis_neq_id():
    r1 = hszinc.Ref(name='a.ref', value='display text')
    r2 = hszinc.Ref(name='another.ref', value='display text')
    assert r1 is not r2
    assert r1 != r2

def test_ref_withdis_neq_dis():
    r1 = hszinc.Ref(name='a.ref', value='display text')
    r2 = hszinc.Ref(name='a.ref', value='different display text')
    assert r1 is not r2
    assert r1 != r2
