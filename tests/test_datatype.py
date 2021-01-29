# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import binascii
import random
from copy import copy, deepcopy

from nose.tools import eq_

import haystackapi
from haystackapi.datatypes import XStr, Uri, Bin, MARKER, NA, REMOVE
from haystackapi.pintutil import to_haystack, to_pint


def check_singleton_deepcopy(a_singleton):
    """
    Args:
        a_singleton:
    """
    orig_dict = {'some_value': a_singleton}
    copy_dict = deepcopy(orig_dict)
    assert copy_dict['some_value'] is a_singleton


def test_marker_deepcopy():
    check_singleton_deepcopy(haystackapi.MARKER)


def test_marker_hash():
    assert hash(haystackapi.MARKER) == hash(haystackapi.MARKER.__class__)


def test_remove_deepcopy():
    check_singleton_deepcopy(haystackapi.REMOVE)


def test_remove_hash():
    assert hash(haystackapi.REMOVE) == hash(haystackapi.REMOVE.__class__)


def check_singleton_copy(a_singleton):
    """
    Args:
        a_singleton:
    """
    assert copy(a_singleton) is a_singleton


def test_marker_copy():
    check_singleton_copy(haystackapi.MARKER)


def test_remove_copy():
    check_singleton_copy(haystackapi.REMOVE)


def test_ref_not_ref_eq():
    try:
        ref_1 = haystackapi.Ref(name='a.ref')
        ref_2 = 'not.a.ref'
        ref_1 is not ref_2  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_ref_not_ref_ne():
    try:
        ref_1 = haystackapi.Ref(name='a.ref')
        ref_2 = 'not.a.ref'
        ref_1 is not ref_2  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_ref_simple_eq():
    ref_1 = haystackapi.Ref(name='a.ref')
    ref_2 = haystackapi.Ref(name='a.ref')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_simple_neq_id():
    ref_1 = haystackapi.Ref(name='a.ref')
    ref_2 = haystackapi.Ref(name='another.ref')
    assert ref_1 is not ref_2
    assert ref_1 != ref_2


def test_ref_mixed_neq():
    ref_1 = haystackapi.Ref(name='a.ref')
    ref_2 = haystackapi.Ref(name='a.ref', value='display text')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_with_dis_eq():
    ref_1 = haystackapi.Ref(name='a.ref', value='display text')
    ref_2 = haystackapi.Ref(name='a.ref', value='display text')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_with_dis_neq_id():
    ref_1 = haystackapi.Ref(name='a.ref', value='display text')
    ref_2 = haystackapi.Ref(name='another.ref', value='display text')
    assert ref_1 is not ref_2
    assert ref_1 != ref_2


def test_ref_with_dis_neq_dis():
    ref_1 = haystackapi.Ref(name='a.ref', value='display text')
    ref_2 = haystackapi.Ref(name='a.ref', value='different display text')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_hash():
    assert hash(haystackapi.Ref(name='a.ref', value='display text')) == \
           hash('a.ref')


def test_ref_std_method():
    assert str(haystackapi.Ref(name='a.ref', value='display text')) == '@a.ref \'display text\''


def test_qty_unary_ops():
    # How to run the test: check the result
    # applied to the Quantity object matches what
    # would be returned for the same operation applied
    # to the raw value.
    def _check_qty_op(_fn, *vals):
        for val in vals:
            quantity = haystackapi.Quantity(val)
            assert _fn(quantity) == a_lambda(quantity.m)

    # Try this both without, and with, pint enabled
    # These work for floats
    for a_lambda in (
            int,
            complex,
            float,
            lambda v: -v,
            lambda v: +v,
            abs):
        yield _check_qty_op, a_lambda, 123.45, -123.45

    # These work for integers
    for a_lambda in (
            oct,
            hex,
            lambda v: v.__index__(),
            int,
            complex,
            float,
            lambda v: -v,
            lambda v: +v,
            abs,
            lambda v: ~v,):
        yield _check_qty_op, a_lambda, 123, -123


def test_qty_hash():
    # Test that independent copies hash to the same value
    def _check_hash(val, unit=None):
        quantity_a = haystackapi.Quantity(val, unit=unit)
        quantity_b = haystackapi.Quantity(val, unit=unit)

        assert quantity_a is not quantity_b
        assert hash(quantity_a) == hash(quantity_b)

    _check_hash(123.45)
    _check_hash(-123.45)
    _check_hash(12345)
    _check_hash(-12345)
    _check_hash(50, 'Hz')


def test_qty_binary_ops():  # pylint: disable=too-many-branches
    def _check_qty_op(_fn, _a, _b):
        quantity_a = haystackapi.Quantity(_a)
        quantity_b = haystackapi.Quantity(_b)

        # Reference value
        ref = _fn(_a, _b)

        assert _fn(quantity_a, quantity_b) == ref
        assert _fn(quantity_a, _b) == ref
        assert _fn(_a, quantity_b) == ref

    # Try some float values
    floats = (1.12, 2.23, -4.56, 141.2, -399.5)
    for small_int_left in floats:
        for small_int_right in floats:
            if small_int_left == small_int_right:
                continue

            for a_lambda in (lambda a, b: a + b,
                             lambda a, b: a - b,
                             lambda a, b: a * b,
                             lambda a, b: a / b,
                             lambda a, b: a // b,
                             lambda a, b: a % b,
                             divmod,
                             lambda a, b: a < b,
                             lambda a, b: a <= b,
                             lambda a, b: a == b,
                             lambda a, b: a != b,
                             lambda a, b: a >= b,
                             lambda a, b: a > b):
                yield _check_qty_op, a_lambda, small_int_left, small_int_right

    # Exponentiation, we can't use all the values above
    # as some go out of dates_range.
    small_floats = tuple(filter(lambda f: abs(f) < 10, floats))
    for small_int_left in small_floats:
        for small_int_right in small_floats:
            if small_int_left == small_int_right:
                continue

            # Python2 won't allow raising negative numbers
            # to a fractional power
            if small_int_left < 0:
                continue

            yield _check_qty_op, lambda a, b: a ** b, small_int_left, small_int_right

    # Try some integer values
    ints = (1, 2, -4, 141, -399, 0x10, 0xff, 0x55)
    for small_int_left in ints:
        for small_int_right in ints:
            if small_int_left == small_int_right:
                continue

            for a_lambda in (lambda a, b: a + b,
                             lambda a, b: a - b,
                             lambda a, b: a * b,
                             lambda a, b: a / b,
                             lambda a, b: a // b,
                             lambda a, b: a % b,
                             divmod,
                             lambda a, b: a & b,
                             lambda a, b: a ^ b,
                             lambda a, b: a | b,
                             lambda a, b: a < b,
                             lambda a, b: a <= b,
                             lambda a, b: a == b,
                             lambda a, b: a != b,
                             lambda a, b: a >= b,
                             lambda a, b: a > b):
                yield _check_qty_op, a_lambda, small_int_left, small_int_right

            if small_int_right >= 0:
                for a_lambda in (lambda a, b: a << b,
                                 lambda a, b: a >> b):
                    yield _check_qty_op, a_lambda, small_int_left, small_int_right

    # Exponentiation, we can't use all the values above
    # as some go out of dates_range.
    small_ints = tuple(filter(lambda f: abs(f) < 10, ints))
    for small_int_left in small_ints:
        for small_int_right in small_ints:
            if small_int_left == small_int_right:
                continue

            yield _check_qty_op, lambda a, b: a ** b, small_int_left, small_int_right


def test_qty_cmp():
    if 'cmp' not in set(locals().keys()):
        def cmp(_a, _b):
            return _a.__cmp__(_b)
    else:
        cmd = locals()['cmp']  # pylint: disable=W0612

    quantity_1 = haystackapi.Quantity(-3)
    quantity_2 = haystackapi.Quantity(432)
    quantity_3 = haystackapi.Quantity(4, unit='A')
    quantity_4 = haystackapi.Quantity(10, unit='A')
    quantity_5 = haystackapi.Quantity(12, unit='V')

    assert cmp(quantity_1, quantity_2) < 0
    assert cmp(quantity_2, quantity_1) > 0
    assert cmp(quantity_1, haystackapi.Quantity(-3)) == 0
    assert cmp(quantity_3, quantity_4) < 0
    assert cmp(quantity_4, quantity_3) > 0
    assert cmp(quantity_3, haystackapi.Quantity(4, unit='A')) == 0

    try:
        cmp(quantity_3, quantity_5)
    except TypeError as ex:
        assert str(ex) == 'Quantity units differ: A vs V'


def test_qty_std_method():
    quantity_repr = repr(haystackapi.Quantity(4, unit='A'))
    assert quantity_repr in ("_BasicQuantity(4, \'A\')", "_PintQuantity(4, \'A\')")
    assert str(haystackapi.Quantity(4, unit='A')) == '4 A'


class MyCoordinate:
    """A dummy class that can compare itself to a Coordinate from
    haystackapi.
    """

    def __init__(self, lat, lng):
        """
        Args:
            lat:
            lng:
        """
        self.lat = lat
        self.lng = lng

    def __eq__(self, other):
        if isinstance(other, haystackapi.Coordinate):
            return (self.lat == other.latitude) and (self.lng == other.longitude)
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, haystackapi.Coordinate):
            return (self.lat != other.latitude) and (self.lng != other.longitude)
        return NotImplemented


def test_coord_eq():
    assert haystackapi.Coordinate(latitude=33.77, longitude=-77.45) \
           == haystackapi.Coordinate(latitude=33.77, longitude=-77.45)


def test_coord_eq_not_coord():
    try:
        haystackapi.Coordinate(latitude=33.77, longitude=-77.45) == (33.77, -77.45)  # pylint: disable=W0106
        assert False
    except AssertionError:
        pass


def test_coord_eq_my_coord():
    try:
        hsc = haystackapi.Coordinate(latitude=33.77, longitude=-77.45)
        my_coordinate = MyCoordinate(33.77, -77.45)
        assert my_coordinate == hsc
        hsc == my_coordinate  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_coord_ne():
    assert haystackapi.Coordinate(latitude=-33.77, longitude=77.45) \
           != haystackapi.Coordinate(latitude=33.77, longitude=-77.45)


def test_coord_ne_not_coord():
    try:
        (haystackapi.Coordinate(latitude=33.77, longitude=-77.45)  # pylint: disable=W0106
         != (33.77, -77.45))
        assert False
    except AssertionError:
        pass


def test_coord_ne_my_coord():
    try:
        hsc = haystackapi.Coordinate(latitude=33.77, longitude=-77.45)
        my_coordinate = MyCoordinate(-33.77, 77.45)
        assert my_coordinate != hsc
        hsc != my_coordinate  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_coord_hash():
    assert hash(haystackapi.Coordinate(latitude=33.77, longitude=-77.45)) == \
           hash(33.77) ^ hash(-77.45)


def test_coord_default_method():
    coord = haystackapi.Coordinate(latitude=33.77, longitude=-77.45)
    ref_str = '33.770000° lat -77.450000° long'

    eq_(repr(coord), 'Coordinate(33.77, -77.45)')
    eq_(str(coord), ref_str)


def test_xstr_hex():
    assert XStr("hex", "deadbeef").data == b'\xde\xad\xbe\xef'
    b_array = bytearray(random.getrandbits(8) for _ in range(10))
    assert b_array == haystackapi.XStr("hex", binascii.hexlify(b_array).decode("ascii")).data


def test_xstr_other():
    assert XStr("other", "hello word").data == "hello word".encode('ascii')


def test_xstr_b64():
    assert XStr("b64", '3q2+7w==').data == b'\xde\xad\xbe\xef'
    b_array = bytearray(random.getrandbits(8) for _ in range(10))
    assert b_array == haystackapi.XStr("b64", binascii.b2a_base64(b_array).decode("utf-8")).data


def test_xstr_equal():
    assert XStr("hex", "deadbeef") == XStr("b64", '3q2+7w==')


def test_uri():
    uri = Uri("abc")
    assert uri == Uri("abc")
    assert repr(uri) == 'Uri(\'abc\')'
    assert str(uri) == 'abc'


def test_bin():
    hs_bin = Bin("text/plain")
    assert repr(hs_bin) == 'Bin(\'text/plain\')'
    assert str(hs_bin) == 'text/plain'


def test_marker():
    assert repr(MARKER) == 'MARKER'


def test_na():
    assert repr(NA) == 'NA'


def test_remove():
    assert repr(REMOVE) == 'REMOVE'


def test_to_haystack():
    assert to_haystack('/h') == ''
    assert to_haystack('foot ** 3') == 'cubic_foot'
    assert to_haystack('deg') == '\N{DEGREE SIGN}'


def test_to_pint():
    assert to_pint('\N{DEGREE SIGN}') == 'deg'
    assert to_pint('cubic_foot') == 'cubic foot'
