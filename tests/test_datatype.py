# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import binascii
import random
from copy import copy, deepcopy

import six

import hszinc
from hszinc.datatypes import XStr, Uri, Bin, MARKER, NA, REMOVE
from hszinc.pintutil import to_haystack, to_pint
from .pint_enable import _enable_pint

from nose.tools import eq_


def check_singleton_deepcopy(S):
    orig_dict = {'some_value': S}
    copy_dict = deepcopy(orig_dict)
    assert copy_dict['some_value'] is S


def test_marker_deepcopy():
    check_singleton_deepcopy(hszinc.MARKER)


def test_marker_hash():
    assert hash(hszinc.MARKER) == hash(hszinc.MARKER.__class__)


def test_remove_deepcopy():
    check_singleton_deepcopy(hszinc.REMOVE)


def test_remove_hash():
    assert hash(hszinc.REMOVE) == hash(hszinc.REMOVE.__class__)


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


def test_ref_hash():
    assert hash(hszinc.Ref(name='a.ref', value='display text')) == \
           hash('a.ref') ^ hash('display text') ^ hash(True)


def test_ref_std_method():
    if six.PY2:
        assert str(hszinc.Ref(name='a.ref', value='display text')) == '@a.ref u\'display text\''
    else:
        assert str(hszinc.Ref(name='a.ref', value='display text')) == '@a.ref \'display text\''


def test_qty_unary_ops():
    # How to run the test: check the result
    # applied to the Quantity object matches what
    # would be returned for the same operation applied
    # to the raw value.
    def _check_qty_op(pint_en, fn, *vals):
        _enable_pint(pint_en)
        for v in vals:
            q = hszinc.Quantity(v)
            assert fn(q) == fn(q.value)

    # Try this both without, and with, pint enabled
    for pint_en in (False, True):
        # These work for floats
        for fn in (lambda v: int(v),
                   lambda v: complex(v),
                   lambda v: float(v),
                   lambda v: -v,
                   lambda v: +v,
                   lambda v: abs(v)):
            yield _check_qty_op, pint_en, fn, 123.45, -123.45

        # These work for integers
        for fn in (lambda v: oct(v),
                   lambda v: hex(v),
                   lambda v: v.__index__(),
                   lambda v: int(v),
                   lambda v: complex(v),
                   lambda v: float(v),
                   lambda v: -v,
                   lambda v: +v,
                   lambda v: abs(v),
                   lambda v: ~v):
            yield _check_qty_op, pint_en, fn, 123, -123

        # This only works with Python 2.
        if six.PY2:  # pragma: no cover
            yield _check_qty_op, pint_en, lambda v: long(v), 123.45, -123.45


def test_qty_hash():
    def _check_qty_hash(pint_en):
        # Test that independent copies hash to the same value
        def _check_hash(val, unit=None):
            a = hszinc.Quantity(val, unit=unit)
            b = hszinc.Quantity(val, unit=unit)

            assert a is not b
            assert hash(a) == hash(b)

        _enable_pint(pint_en)

        _check_hash(123.45)
        _check_hash(-123.45)
        _check_hash(12345)
        _check_hash(-12345)
        _check_hash(50, 'Hz')

    for pint_en in (False, True):
        yield _check_qty_hash, pint_en


def test_qty_binary_ops():
    def _check_qty_op(pint_en, fn, a, b):
        _enable_pint(pint_en)
        qa = hszinc.Quantity(a)
        qb = hszinc.Quantity(b)

        # Reference value
        ref = fn(a, b)

        assert fn(qa, qb) == ref
        assert fn(qa, b) == ref
        assert fn(a, qb) == ref

    for pint_en in (False, True):
        # Try some float values
        floats = (1.12, 2.23, -4.56, 141.2, -399.5)
        for a in floats:
            for b in floats:
                if a == b:
                    continue

                for fn in (lambda a, b: a + b,
                           lambda a, b: a - b,
                           lambda a, b: a * b,
                           lambda a, b: a / b,
                           lambda a, b: a // b,
                           lambda a, b: a % b,
                           lambda a, b: divmod(a, b),
                           lambda a, b: a < b,
                           lambda a, b: a <= b,
                           lambda a, b: a == b,
                           lambda a, b: a != b,
                           lambda a, b: a >= b,
                           lambda a, b: a > b):
                    yield _check_qty_op, pint_en, fn, a, b

        # Exponentiation, we can't use all the values above
        # as some go out of dates_range.
        small_floats = tuple(filter(lambda f: abs(f) < 10, floats))
        for a in small_floats:
            for b in small_floats:
                if a == b:
                    continue

                # Python2 won't allow raising negative numbers
                # to a fractional power
                if a < 0:
                    continue

                yield _check_qty_op, pint_en, lambda a, b: a ** b, a, b

        # Try some integer values
        ints = (1, 2, -4, 141, -399, 0x10, 0xff, 0x55)
        for a in ints:
            for b in ints:
                if a == b:
                    continue

                for fn in (lambda a, b: a + b,
                           lambda a, b: a - b,
                           lambda a, b: a * b,
                           lambda a, b: a / b,
                           lambda a, b: a // b,
                           lambda a, b: a % b,
                           lambda a, b: divmod(a, b),
                           lambda a, b: a & b,
                           lambda a, b: a ^ b,
                           lambda a, b: a | b,
                           lambda a, b: a < b,
                           lambda a, b: a <= b,
                           lambda a, b: a == b,
                           lambda a, b: a != b,
                           lambda a, b: a >= b,
                           lambda a, b: a > b):
                    yield _check_qty_op, pint_en, fn, a, b

                if b >= 0:
                    for fn in (lambda a, b: a << b,
                               lambda a, b: a >> b):
                        yield _check_qty_op, pint_en, fn, a, b

        # Exponentiation, we can't use all the values above
        # as some go out of dates_range.
        small_ints = tuple(filter(lambda f: abs(f) < 10, ints))
        for a in small_ints:
            for b in small_ints:
                if a == b:
                    continue

                yield _check_qty_op, pint_en, lambda a, b: a ** b, a, b


def test_qty_cmp():
    def _check_qty_cmp(pint_en):
        if 'cmp' not in set(locals().keys()):
            def cmp(a, b):
                return a.__cmp__(b)

        _enable_pint(pint_en)

        a = hszinc.Quantity(-3)
        b = hszinc.Quantity(432)
        c = hszinc.Quantity(4, unit='A')
        d = hszinc.Quantity(10, unit='A')
        e = hszinc.Quantity(12, unit='V')

        assert cmp(a, b) < 0
        assert cmp(b, a) > 0
        assert cmp(a, hszinc.Quantity(-3)) == 0
        assert cmp(c, d) < 0
        assert cmp(d, c) > 0
        assert cmp(c, hszinc.Quantity(4, unit='A')) == 0

        try:
            cmp(c, e)
        except TypeError as ex:
            assert str(ex) == 'Quantity units differ: A vs V'

    for pint_en in (False, True):
        yield _check_qty_cmp, pint_en


def test_qty_std_method():
    def _check_qty_cmp(pint_en):
        r = repr(hszinc.Quantity(4, unit='A'))
        if six.PY2:
            assert (r == 'BasicQuantity(4, u\'A\')') or (r == 'PintQuantity(4, u\'A\')')
        else:
            assert (r == 'BasicQuantity(4, \'A\')') or (r == 'PintQuantity(4, \'A\')')
        assert str(hszinc.Quantity(4, unit='A')) == '4 A'

    yield _check_qty_cmp, True
    yield _check_qty_cmp, False


class MyCoordinate(object):
    """
    A dummy class that can compare itself to a Coordinate from hszinc.
    """

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng

    def __eq__(self, other):
        if isinstance(other, hszinc.Coordinate):
            return (self.lat == other.latitude) \
                   and (self.lng == other.longitude)
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, hszinc.Coordinate):
            return (self.lat != other.latitude) \
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


def test_coord_hash():
    assert hash(hszinc.Coordinate(latitude=33.77, longitude=-77.45)) == \
           hash(33.77) ^ hash(-77.45)


def test_coord_default_method():
    coord = hszinc.Coordinate(latitude=33.77, longitude=-77.45)
    ref_str = u'33.770000° lat -77.450000° long'
    if six.PY2:
        ref_str = ref_str.encode('utf-8')

    eq_(repr(coord), 'Coordinate(33.77, -77.45)')
    eq_(str(coord), ref_str)


def test_xstr_hex():
    assert XStr("hex", "deadbeef").data == b'\xde\xad\xbe\xef'
    barray = bytearray(random.getrandbits(8) for _ in range(10))
    assert barray == hszinc.XStr("hex", binascii.hexlify(barray).decode("ascii")).data


def test_xstr_other():
    assert (XStr("other", "hello word").data == "hello word")
    barray = bytearray(random.getrandbits(8) for _ in range(10))
    assert barray == hszinc.XStr("other", barray).data


def test_xstr_b64():
    assert XStr("b64", '3q2+7w==').data == b'\xde\xad\xbe\xef'
    barray = bytearray(random.getrandbits(8) for _ in range(10))
    assert barray == hszinc.XStr("b64", binascii.b2a_base64(barray)).data


def test_xstr_equal():
    assert XStr("hex", "deadbeef") == XStr("b64", '3q2+7w==')


def test_uri():
    uri = Uri("abc")
    assert uri == Uri("abc")
    if six.PY2:
        assert repr(uri) == 'Uri(u\'abc\')'
    else:
        assert repr(uri) == 'Uri(\'abc\')'
    assert str(uri) == 'abc'


def test_bin():
    bin = Bin("text/plain")
    if six.PY2:
        assert repr(bin) == 'Bin(u\'text/plain\')'
    else:
        assert repr(bin) == 'Bin(\'text/plain\')'
    assert str(bin) == 'text/plain'


def test_marker():
    assert repr(MARKER) == 'MARKER'


def test_na():
    assert repr(NA) == 'NA'


def test_remove():
    assert repr(REMOVE) == 'REMOVE'


def test_to_haystack():
    assert to_haystack('/h') == u''
    assert to_haystack(u'foot ** 3') == u'cubic_foot'
    assert to_haystack(u'deg') == u'\N{DEGREE SIGN}'

def test_to_pint():
    assert to_pint(u'\N{DEGREE SIGN}') == 'deg'
    assert to_pint('cubic_foot') == u'cubic foot'
