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
from typing import Dict, Any

import pytest

import shaystack
from shaystack.datatypes import XStr, Uri, Bin, MARKER, NA, REMOVE, Quantity


def check_singleton_deepcopy(a_singleton):
    """
    Args:
        a_singleton:
    """
    orig_dict = {'some_value': a_singleton}
    copy_dict: Dict[str, Any] = deepcopy(orig_dict)
    assert copy_dict['some_value'] is a_singleton


def test_marker_deepcopy():
    check_singleton_deepcopy(shaystack.MARKER)


def test_marker_hash():
    assert hash(shaystack.MARKER) == hash(shaystack.MARKER.__class__)


def test_remove_deepcopy():
    check_singleton_deepcopy(shaystack.REMOVE)


def test_remove_hash():
    assert hash(shaystack.REMOVE) == hash(shaystack.REMOVE.__class__)


def check_singleton_copy(a_singleton):
    """
    Args:
        a_singleton:
    """
    assert copy(a_singleton) is a_singleton


def test_marker_copy():
    check_singleton_copy(shaystack.MARKER)


def test_remove_copy():
    check_singleton_copy(shaystack.REMOVE)


def test_ref_not_ref_eq():
    try:
        ref_1 = shaystack.Ref(name='a.ref')
        ref_2 = 'not.a.ref'
        assert ref_1 is not ref_2  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_ref_not_ref_ne():
    try:
        ref_1 = shaystack.Ref(name='a.ref')
        ref_2 = 'not.a.ref'
        assert ref_1 is not ref_2  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_ref_simple_eq():
    ref_1 = shaystack.Ref(name='a.ref')
    ref_2 = shaystack.Ref(name='a.ref')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_simple_neq_id():
    ref_1 = shaystack.Ref(name='a.ref')
    ref_2 = shaystack.Ref(name='another.ref')
    assert ref_1 is not ref_2
    assert ref_1 != ref_2


def test_ref_mixed_neq():
    ref_1 = shaystack.Ref(name='a.ref')
    ref_2 = shaystack.Ref(name='a.ref', value='display text')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_with_dis_eq():
    ref_1 = shaystack.Ref(name='a.ref', value='display text')
    ref_2 = shaystack.Ref(name='a.ref', value='display text')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_with_dis_neq_id():
    ref_1 = shaystack.Ref(name='a.ref', value='display text')
    ref_2 = shaystack.Ref(name='another.ref', value='display text')
    assert ref_1 is not ref_2
    assert ref_1 != ref_2


def test_ref_with_dis_neq_dis():
    ref_1 = shaystack.Ref(name='a.ref', value='display text')
    ref_2 = shaystack.Ref(name='a.ref', value='different display text')
    assert ref_1 is not ref_2
    assert ref_1 == ref_2


def test_ref_hash():
    assert hash(shaystack.Ref(name='a.ref', value='display text')) == \
           hash('a.ref')


def test_ref_std_method():
    assert str(shaystack.Ref(name='a.ref', value='display text')) == '@a.ref \'display text\''



def _check_qty_op(_fn, *vals):
    print(_fn)
    print(*vals)
    for val in vals:
        quantity = shaystack.Quantity(val)
        assert _fn(quantity) == _fn(quantity.m)


@pytest.mark.parametrize("a_lambda", [int, complex, float, lambda v: -v, lambda v: +v, abs])
def test_qty_unary_ops_for_floats(a_lambda):
    # How to run the test: check the result
    # applied to the Quantity object matches what
    # would be returned for the same operation applied
    # to the raw value.
    # Try this both without, and with, pint enabled
    # These work for floats
    _check_qty_op(a_lambda, 123.45, -123.45)

@pytest.mark.parametrize("a_lambda", [lambda v: oct(int(v)),
                                      lambda v: hex(int(v)),
                                      lambda v: v.__index__(),
                                      int,
                                      complex,
                                      float,
                                      lambda v: -v,
                                      lambda v: +v,
                                      abs,
                                      lambda v: ~int(v), ])
def test_qty_unary_ops_for_integers(a_lambda):
    # How to run the test: check the result
    # applied to the Quantity object matches what
    # would be returned for the same operation applied
    # to the raw value.
    # Try this both without, and with, pint enabled
    # These work for integers
    _check_qty_op(a_lambda, 123, -123)


def test_qty_hash():
    # Test that independent copies hash to the same value
    def _check_hash(val, unit=None):
        quantity_a = shaystack.Quantity(val, unit)
        quantity_b = shaystack.Quantity(val, unit)

        assert quantity_a is not quantity_b
        assert hash(quantity_a) == hash(quantity_b)

    _check_hash(123.45)
    _check_hash(-123.45)
    _check_hash(12345)
    _check_hash(-12345)
    _check_hash(50, 'Hz')


class MyCoordinate:
    """A dummy class that can compare itself to a Coordinate from
    shift-4-haystack.
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
        if isinstance(other, shaystack.Coordinate):
            return (self.lat == other.latitude) and (self.lng == other.longitude)
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, shaystack.Coordinate):
            return (self.lat != other.latitude) and (self.lng != other.longitude)
        return NotImplemented


def test_coord_eq():
    assert shaystack.Coordinate(latitude=33.77, longitude=-77.45) \
           == shaystack.Coordinate(latitude=33.77, longitude=-77.45)


def test_coord_eq_not_coord():
    try:
        assert shaystack.Coordinate(latitude=33.77, longitude=-77.45) == (33.77, -77.45)  # pylint: disable=W0106
        assert False
    except AssertionError:
        pass


def test_coord_eq_my_coord():
    try:
        hsc = shaystack.Coordinate(latitude=33.77, longitude=-77.45)
        my_coordinate = MyCoordinate(33.77, -77.45)
        assert my_coordinate == hsc
        assert hsc == my_coordinate  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_coord_ne():
    assert shaystack.Coordinate(latitude=-33.77, longitude=77.45) \
           != shaystack.Coordinate(latitude=33.77, longitude=-77.45)


def test_coord_ne_not_coord():
    try:
        assert (shaystack.Coordinate(latitude=33.77,
                                     longitude=-77.45) != (33.77, -77.45))  # pylint: disable=W0106

        assert False
    except AssertionError:
        pass


def test_coord_ne_my_coord():
    try:
        hsc = shaystack.Coordinate(latitude=33.77, longitude=-77.45)
        my_coordinate = MyCoordinate(-33.77, 77.45)
        assert my_coordinate != hsc
        assert hsc != my_coordinate  # pylint: disable=pointless-statement
        assert False
    except AssertionError:
        pass


def test_coord_hash():
    assert hash(shaystack.Coordinate(latitude=33.77, longitude=-77.45)) == \
           hash(33.77) ^ hash(-77.45)


def test_coord_default_method():
    coord = shaystack.Coordinate(latitude=33.77, longitude=-77.45)
    ref_str = '33.770000° lat -77.450000° long'

    assert repr(coord) == 'Coordinate(33.77, -77.45)'
    assert str(coord) == ref_str


def test_xstr_hex():
    assert XStr("hex", "deadbeef").data == b'\xde\xad\xbe\xef'
    b_array = bytearray(random.getrandbits(8) for _ in range(10))
    assert b_array == shaystack.XStr("hex", binascii.hexlify(b_array).decode("ascii")).data


def test_xstr_other():
    assert XStr("other", "hello word").data == "hello word".encode('ascii')


def test_xstr_b64():
    assert XStr("b64", '3q2+7w==').data == b'\xde\xad\xbe\xef'
    b_array = bytearray(random.getrandbits(8) for _ in range(10))
    assert b_array == shaystack.XStr("b64", binascii.b2a_base64(b_array).decode("utf-8")).data


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


def test_new_quantity():
    Quantity(1, '$')
