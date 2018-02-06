# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import six
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
    assert not (r1 == r2)

def test_ref_notref_ne():
    r1 = hszinc.Ref(name='a.ref')
    r2 = 'not.a.ref'
    assert r1 is not r2
    assert r1 != r2

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

def test_qty_unary_ops():
    # Try this both without, and with, pint enabled
    for pint_en in (False, True):
        hszinc.use_pint(pint_en)
        # How to run the test: check the result
        # applied to the Quantity object matches what
        # would be returned for the same operation applied
        # to the raw value.
        def _check_qty_op(fn, *vals):
            for v in vals:
                q = hszinc.Quantity(v)
                assert fn(q) == fn(q.value)

        # These work for floats
        for fn in ( lambda v : int(v),
                    lambda v : complex(v),
                    lambda v : float(v),
                    lambda v : -v,
                    lambda v : +v,
                    lambda v : abs(v)):
            yield _check_qty_op, fn, 123.45, -123.45

        # These work for integers
        for fn in ( lambda v : oct(v),
                    lambda v : hex(v),
                    lambda v : v.__index__(),
                    lambda v : int(v),
                    lambda v : complex(v),
                    lambda v : float(v),
                    lambda v : -v,
                    lambda v : +v,
                    lambda v : abs(v),
                    lambda v : ~v):
            yield _check_qty_op, fn, 123, -123

        # This only works with Python 2.
        if six.PY2:
            yield _check_qty_op, lambda v : long(v), 123.45, -123.45

def test_qty_hash():
    # Test that independent copies hash to the same value
    def _check_hash(val, unit=None):
        a = hszinc.Quantity(val, unit=unit)
        b = hszinc.Quantity(val, unit=unit)

        assert a is not b
        assert hash(a) == hash(b)

    # Try this both without, and with, pint enabled
    for pint_en in (False, True):
        hszinc.use_pint(pint_en)

        _check_hash(123.45)
        _check_hash(-123.45)
        _check_hash(12345)
        _check_hash(-12345)
        _check_hash(50, 'Hz')

def test_qty_binary_ops():
    def _check_qty_op(fn, a, b):
        qa = hszinc.Quantity(a)
        qb = hszinc.Quantity(b)

        # Reference value
        ref = fn(a, b)

        assert fn(qa, qb) == ref
        assert fn(qa, b) == ref
        assert fn(a, qb) == ref

    for pint_en in (False, True):
        hszinc.use_pint(pint_en)
        # Try some float values
        floats = (1.12, 2.23, -4.56, 141.2, -399.5)
        for a in floats:
            for b in floats:
                if a == b:
                    continue

                for fn in ( lambda a, b : a + b,
                            lambda a, b : a - b,
                            lambda a, b : a * b,
                            lambda a, b : a / b,
                            lambda a, b : a // b,
                            lambda a, b : a % b,
                            lambda a, b : divmod(a, b),
                            lambda a, b : a < b,
                            lambda a, b : a <= b,
                            lambda a, b : a == b,
                            lambda a, b : a != b,
                            lambda a, b : a >= b,
                            lambda a, b : a > b):
                    yield _check_qty_op, fn, a, b

        # Try some integer values
        ints = (1, 2, -4, 141, -399, 0x10, 0xff, 0x55)
        for a in ints:
            for b in ints:
                if a == b:
                    continue

                for fn in ( lambda a, b : a + b,
                            lambda a, b : a - b,
                            lambda a, b : a * b,
                            lambda a, b : a / b,
                            lambda a, b : a // b,
                            lambda a, b : a % b,
                            lambda a, b : divmod(a, b),
                            lambda a, b : a & b,
                            lambda a, b : a ^ b,
                            lambda a, b : a | b,
                            lambda a, b : a < b,
                            lambda a, b : a <= b,
                            lambda a, b : a == b,
                            lambda a, b : a != b,
                            lambda a, b : a >= b,
                            lambda a, b : a > b):
                    yield _check_qty_op, fn, a, b

                if b >= 0:
                    for fn in ( lambda a, b : a << b,
                                lambda a, b : a >> b):
                        yield _check_qty_op, fn, a, b

def test_qty_cmp():
    if 'cmp' not in set(locals().keys()):
        def cmp(a, b):
            return a.__cmp__(b)

    for pint_en in (False, True):
        hszinc.use_pint(pint_en)

        a = hszinc.Quantity(-3)
        b = hszinc.Quantity(432)

        assert cmp(a, b) < 0
        assert cmp(b, a) > 0
        assert cmp(a, hszinc.Quantity(-3)) == 0


class MyCoordinate(object):
    """
    A dummy class that can compare itself to a Coordinate from hszinc.
    """
    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

    def __eq__(self, other):
        if isinstance(other, hszinc.Coordinate):
            return (self.lat == other.latitude)\
                    and (self.lng == other.longitude)
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, hszinc.Coordinate):
            return (self.lat != other.latitude)\
                    and (self.lng != other.longitude)
        return NotImplemented


def test_coord_eq():
    assert hszinc.Coordinate(latitude=33.77, longitude=-77.45) \
            == hszinc.Coordinate(latitude=33.77, longitude=-77.45)

def test_coord_eq_notcoord():
    assert not (hszinc.Coordinate(latitude=33.77, longitude=-77.45) \
            == (33.77, -77.45))

def test_coord_eq_mycoord():
    hsc = hszinc.Coordinate(latitude=33.77, longitude=-77.45)
    mc = MyCoordinate(33.77, -77.45)
    assert hsc == mc
    assert mc == hsc

def test_coord_ne():
    assert hszinc.Coordinate(latitude=-33.77, longitude=77.45) \
            != hszinc.Coordinate(latitude=33.77, longitude=-77.45)

def test_coord_ne_notcoord():
    assert (hszinc.Coordinate(latitude=33.77, longitude=-77.45) \
            != (33.77, -77.45))

def test_coord_ne_mycoord():
    hsc = hszinc.Coordinate(latitude=33.77, longitude=-77.45)
    mc = MyCoordinate(-33.77, 77.45)
    assert hsc != mc
    assert mc != hsc
