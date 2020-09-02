#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc data types
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import base64
import binascii
import sys
from abc import ABCMeta

import six

from . import PINT_AVAILABLE

if PINT_AVAILABLE:
    from . import ureg
    from .pintutil import to_pint

STR_SUB = [
    ('\b', '\\b'),
    ('\f', '\\f'),
    ('\n', '\\n'),
    ('\r', '\\r'),
    ('\t', '\\t'),
]

# Will keep in memory the way we want Quantity being created
MODE_PINT = False


def use_pint(val=True):
    global MODE_PINT
    if val:
        # print('Switching to Pint')
        if PINT_AVAILABLE:
            MODE_PINT = True
        else:  # pragma: no cover
            # Really difficult to test this case in CI
            raise ImportError(
                'Pint not installed. Use pip install pint if needed')
    else:  # pragma: no cover
        # print('Back to default Quantity')
        MODE_PINT = False


class Quantity(six.with_metaclass(ABCMeta, object)):
    def __new__(self, value, unit=None):
        if MODE_PINT:
            return PintQuantity(value, to_pint(unit))
        else:
            return BasicQuantity(value, unit)


class Qty(object):
    """
    A quantity is a scalar value (floating point) with a unit.
    """

    def __init__(self, value, unit):
        self.value = value
        self.unit = unit

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.value, self.unit
        )

    def __str__(self):
        return '%s %s' % (
            self.value, self.unit
        )

    def __index__(self):
        return self.value.__index__()

    def __oct__(self):  # pragma: no cover
        return oct(self.value)

    def __hex__(self):  # pragma: no cover
        return hex(self.value)

    def __int__(self):  # pragma: no cover
        return int(self.value)

    if six.PY2:  # pragma: no cover
        # Python 3 doesn't have 'long'
        def __long__(self):
            return long(self.value)

    def __complex__(self):
        return complex(self.value)

    def __float__(self):
        return float(self.value)

    def __neg__(self):
        return -self.value

    def __pos__(self):
        return +self.value

    def __abs__(self):
        return abs(self.value)

    def __invert__(self):
        return ~self.value

    def __add__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value + other

    def __sub__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value - other

    def __mul__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value * other

    def __div__(self, other):  # pragma: no cover
        if isinstance(other, Qty):
            other = other.value
        return self.value / other

    def __truediv__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value / other

    def __floordiv__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value // other

    def __mod__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value % other

    def __divmod__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return divmod(self.value, other)

    def __pow__(self, other, modulo=None):
        if isinstance(other, Qty):
            other = other.value
        return pow(self.value, other, modulo)

    def __lshift__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value << other

    def __rshift__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value >> other

    def __and__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value & other

    def __xor__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value ^ other

    def __or__(self, other):
        if isinstance(other, Qty):
            other = other.value
        return self.value | other

    def __radd__(self, other):
        if isinstance(other, Qty):  # pragma: no cover
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return other + self.value

    def __rsub__(self, other):
        if isinstance(other, Qty):  # pragma: no cover
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return other - self.value

    def __rmul__(self, other):
        if isinstance(other, Qty):  # pragma: no cover
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return other * self.value

    def __rdiv__(self, other):  # pragma: no cover
        if isinstance(other, Qty):
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return other / self.value

    def __rtruediv__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other / self.value

    def __rfloordiv__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other // self.value

    def __rmod__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other % self.value

    def __rdivmod__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return divmod(other, self.value)

    def __rpow__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return pow(other, self.value)

    def __rlshift__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other << self.value

    def __rrshift__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other >> self.value

    def __rand__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other & self.value

    def __rxor__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other ^ self.value

    def __ror__(self, other):  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return other | self.value

    def _cmp_op(self, other, op):
        if isinstance(other, Qty):
            if other.unit != self.unit:
                raise TypeError('Quantity units differ: %s vs %s' \
                                % (self.unit, other.unit))
            return op(self.value, other.value)
        return op(self.value, other)

    def __lt__(self, other):
        return self._cmp_op(other, lambda x, y: x < y)

    def __le__(self, other):
        return self._cmp_op(other, lambda x, y: x <= y)

    def __eq__(self, other):
        return self._cmp_op(other, lambda x, y: x == y)

    def __ge__(self, other):
        return self._cmp_op(other, lambda x, y: x >= y)

    def __gt__(self, other):
        return self._cmp_op(other, lambda x, y: x > y)

    def __ne__(self, other):
        return self._cmp_op(other, lambda x, y: x != y)

    def __cmp__(self, other):
        if self == other:
            return 0
        elif self < other:
            return -1
        else:
            return 1

    def __hash__(self):
        return hash((self.value, self.unit))


class BasicQuantity(Qty):
    """
    Default class to be used to define Quantity.
    """
    pass


Quantity.register(BasicQuantity)

if PINT_AVAILABLE:
    class PintQuantity(Qty, ureg.Quantity):
        """
        A quantity is a scalar value (floating point) with a unit.
        This object uses Pint feature allowing conversion between units
        for example :
            a = hszinc.Q_(19, 'degC')
            a.to('degF')
        See https://pint.readthedocs.io for details
        """

        def __init__(self, value, unit):
            super(PintQuantity, self).__init__(value, unit)


    Quantity.register(PintQuantity)
else:  # pragma: no cover
    # If things turn really bad...just in case.
    PintQuantity = BasicQuantity
    to_pint = lambda unit: unit


class Coordinate(object):
    """
    A 2D co-ordinate in degrees latitude and longitude.
    """

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.latitude, self.longitude
        )

    def __str__(self):
        fmt = u'%f\N{DEGREE SIGN} lat %f\N{DEGREE SIGN} long'

        if six.PY2:  # pragma: no cover
            fmt = fmt.encode('utf-8')

        return fmt % (
            round(self.latitude, ndigits=6), round(self.longitude, ndigits=6)
        )

    def __eq__(self, other):
        if not isinstance(other, Coordinate):
            return NotImplemented
        return (self.latitude == other.latitude) and \
               (self.longitude == other.longitude)

    def __ne__(self, other):
        if not isinstance(other, Coordinate):
            return NotImplemented
        return not (self == other)

    def __hash__(self):
        return hash(self.latitude) ^ hash(self.longitude)


class Uri(six.text_type):
    """
    A convenience class to allow identification of a URI from other string
    types.
    """

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           super(Uri, self).__repr__())

    def __eq__(self, other):
        if not isinstance(other, Uri):
            return NotImplemented
        return super(Uri, self).__eq__(other)


class Bin(six.text_type):
    """
    A convenience class to allow identification of a Bin from other string
    types.
    """

    # TODO: This seems to be the MIME type, no idea where the data lives.
    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           super(Bin, self).__repr__())

    def __eq__(self, other):
        if not isinstance(other, Bin):
            return NotImplemented
        return super(Bin, self).__eq__(other)


class XStr(object):
    """
    A convenience class to allow identification of a Xstr
    """

    def __init__(self, encoding, data):
        self.encoding = encoding
        if "hex" == encoding:
            if six.PY2:  # pragma: no cover
                self.data = binascii.a2b_hex(data)
            else:
                self.data = bytearray.fromhex(data)
        elif "b64" == encoding:
            if six.PY2:  # pragma: no cover
                self.data = data.decode('base64')
            else:
                self.data = base64.b64decode(data)
        else:
            self.data = data  # Not decoded

    def data_to_string(self):
        if "hex" == self.encoding:
            return binascii.b2a_hex(self.data).decode("ascii")
        elif "b64" == self.encoding:
            if six.PY2:  # pragma: no cover
                return binascii.b2a_base64(self.data)[:-1]
            elif sys.version_info[0:2] <= (3, 6):
                return binascii.b2a_base64(self.data).decode("ascii").replace('\n', '')
            else:
                return binascii.b2a_base64(self.data, newline=False).decode("ascii")
        else:
            return self.data

    def __repr__(self):
        return '%s("%s")' % (self.encoding, self.data_to_string())

    def __eq__(self, other):
        if not isinstance(other, XStr):
            return NotImplemented
        return self.data == other.data  # Check only binary datas


class Singleton(object):
    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __hash__(self):
        return hash(self.__class__)


class MarkerType(Singleton):
    """
    A singleton class representing a Marker.
    """

    def __repr__(self):
        return 'MARKER'


MARKER = MarkerType()


class NAType(Singleton):
    """
    A singleton class representing a NA.
    """

    def __repr__(self):
        return 'NA'


NA = NAType()


class RemoveType(Singleton):
    """
    A singleton class representing a Remove.
    """

    def __repr__(self):
        return 'REMOVE'


REMOVE = RemoveType()


class Ref(object):
    """
    A reference to an object in Project Haystack.
    """

    # TODO: The grammar specifies that it can have a string following a space,
    # but the documentation does not specify what this string encodes.  This is
    # distinct from the reference name itself immediately following the @
    # symbol.  I'm guessing it's some kind of value.
    def __init__(self, name, value=None, has_value=False):
        self.name = name
        self.value = value
        self.has_value = has_value or (value is not None)

    def __repr__(self):
        return '%s(%r, %r, %r)' % (
            self.__class__.__name__, self.name, self.value, self.has_value
        )

    def __str__(self):
        if self.has_value:
            return '@%s %r' % (
                self.name, self.value
            )
        else:
            return '@%s' % self.name

    def __eq__(self, other):
        if not isinstance(other, Ref):
            return NotImplemented
        return (self.name == other.name) and \
               (self.has_value == other.has_value) and \
               (self.value == other.value)

    def __ne__(self, other):
        if not isinstance(other, Ref):
            return NotImplemented
        return not (self == other)

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^ hash(self.has_value)
