# -*- coding: utf-8 -*-
# Zinc data types
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Implementation of all haystack types.
See https://www.project-haystack.org/doc/TagModel#tagKinds
"""
import base64
import binascii
import re
from abc import ABCMeta
from numbers import Number
from typing import Optional, Tuple, Union

import six

from .pintutil import to_pint, unit_reg

_STR_SUB = [
    ('\b', '\\b'),
    ('\f', '\\f'),
    ('\n', '\\n'),
    ('\r', '\\r'),
    ('\t', '\\t'),
]


# Will keep in memory the way we want Quantity being created

class Quantity(six.with_metaclass(ABCMeta, object)):  # pylint: disable=too-few-public-methods
    """A float value with with pint unit.
        Args:
            m:The quantity
            unit: An optional unit (must be compatible with pint)
    """

    def __new__(cls, m: float, unit: Optional[str] = None):
        return _PintQuantity(m, to_pint(unit))

    # Fake ctr to help audit tools
    def __init__(self, m: float, unit: Optional[str] = None):
        self.m = m  # pylint: disable=invalid-name
        self.unit = unit


class Qty:
    """A quantity is a scalar value (floating point) with a unit.
        Args:
            m:The quantity
            unit: An optional unit (must be compatible with pint)
    """

    def __init__(self, value: float, unit: Optional[str]):
        self.value = value
        self.unit = unit

    def __repr__(self) -> str:
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.value, self.unit
        )

    def __str__(self) -> str:
        return '%s %s' % (
            self.value, self.unit
        )

    def __index__(self) -> float:
        return self.value.__index__()

    def __oct__(self) -> str:  # pragma: no cover
        return oct(int(self.value))

    def __hex__(self) -> str:  # pragma: no cover
        return hex(int(self.value))

    def __int__(self) -> int:  # pragma: no cover
        return int(self.value)

    def __complex__(self) -> complex:
        return complex(self.value)

    def __float__(self) -> float:
        return float(self.value)

    def __neg__(self) -> 'Qty':
        return Qty(-self.value, self.unit)

    def __pos__(self) -> 'Qty':
        return self

    def __abs__(self) -> 'Qty':
        return Qty(abs(self.value), self.unit)

    def __invert__(self) -> 'Qty':
        return Qty(~self.value, self.unit)

    def __add__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value + other, self.unit)

    def __sub__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value - other, self.unit)

    def __mul__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value * other, self.unit)

    def __div__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value / other, self.unit)

    def __truediv__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value / other, self.unit)

    def __floordiv__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value // other, self.unit)

    def __mod__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value % other, self.unit)

    def __divmod__(self, other: Union[Number, 'Qty']) -> Tuple[float, float]:
        if isinstance(other, Qty):
            other = other.value

        return divmod(self.value, other)

    def __pow__(self, other: Union[Number, 'Qty'], modulo: Optional[int] = None) -> complex:
        if isinstance(other, Qty):
            other = other.value
        return pow(self.value, other, modulo)

    def __lshift__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value << other, self.unit)

    def __rshift__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value >> other, self.unit)

    def __and__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value & other, self.unit)

    def __xor__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value ^ other, self.unit)

    def __or__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):
            other = other.value
        return Qty(self.value | other, self.unit)

    def __radd__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):  # pragma: no cover
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return Qty(other + self.value, self.unit)

    def __rsub__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):  # pragma: no cover
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return Qty(other - self.value, self.unit)

    def __rmul__(self, other: Union[Number, 'Qty']) -> 'Qty':
        if isinstance(other, Qty):  # pragma: no cover
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return Qty(other * self.value, self.unit)

    def __rdiv__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        if isinstance(other, Qty):
            # Unlikely due to Qty supporting these ops directly
            other = other.value
        return Qty(other / self.value, self.unit)

    def __rtruediv__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other / self.value, self.unit)

    def __rfloordiv__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other // self.value, self.unit)

    def __rmod__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other % self.value, self.unit)

    def __rdivmod__(self, other: Union[Number, 'Qty']) -> Tuple[float, float]:  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return divmod(other, self.value)

    def __rpow__(self, other: Union[Number, 'Qty']) -> complex:  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return pow(other, self.value)

    def __rlshift__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other << self.value, self.unit)

    def __rrshift__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other >> self.value, self.unit)

    def __rand__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other & self.value, self.unit)

    def __rxor__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other ^ self.value, self.unit)

    def __ror__(self, other: Union[Number, 'Qty']) -> 'Qty':  # pragma: no cover
        # Unlikely due to Qty supporting these ops directly
        if isinstance(other, Qty):
            other = other.value
        return Qty(other | self.value, self.unit)

    def _cmp_op(self, other: Union[Number, 'Qty'], operator) -> bool:  # PPR: type
        if isinstance(other, Qty):
            if other.unit != self.unit:
                raise TypeError('Quantity units differ: %s vs %s' % (self.unit, other.unit))
            return operator(self.value, other.value)
        return operator(self.value, other)

    def __lt__(self, other: Union[Number, 'Qty']) -> bool:
        return self._cmp_op(other, lambda x, y: x < y)

    def __le__(self, other: Union[Number, 'Qty']) -> bool:
        return self._cmp_op(other, lambda x, y: x <= y)

    def __eq__(self, other: Union[Number, 'Qty']) -> bool:
        return self._cmp_op(other, lambda x, y: x == y)

    def __ge__(self, other: Union[Number, 'Qty']) -> bool:
        return self._cmp_op(other, lambda x, y: x >= y)

    def __gt__(self, other: Union[Number, 'Qty']) -> bool:
        return self._cmp_op(other, lambda x, y: x > y)

    def __ne__(self, other: Union[Number, 'Qty']) -> bool:
        return self._cmp_op(other, lambda x, y: x != y)

    def __cmp__(self, other: Union[Number, 'Qty']) -> int:
        if self == other:
            return 0
        if self < other:
            return -1
        return 1

    def __hash__(self) -> int:
        return hash((self.value, self.unit))


class _PintQuantity(Qty, unit_reg.Quantity):
    """A quantity is a scalar value (floating point) with a unit. This object
    uses Pint feature allowing conversion between units for example :

        a = haystackapi.Q_(19, 'degC') a.to('degF')

    See https://pint.readthedocs.io for details
    """


Quantity.register(_PintQuantity)  # noqa: E303


# PPR Quantity = unit_reg.Quantity


class Coordinate:
    """A 2D co-ordinate in degrees latitude and longitude.
        Args:
            latitude: the latitude
            longitude: the longitude
    """

    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self) -> str:
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.latitude, self.longitude
        )

    def __str__(self) -> str:
        return ('%f\N{DEGREE SIGN} lat %f\N{DEGREE SIGN} long' % (
            round(self.latitude, ndigits=6), round(self.longitude, ndigits=6)
        ))

    def __eq__(self, other: 'Coordinate') -> bool:
        if not isinstance(other, Coordinate):
            return False
        return (self.latitude == other.latitude) and \
               (self.longitude == other.longitude)

    def __ne__(self, other: 'Coordinate') -> bool:
        if not isinstance(other, Coordinate):
            return True
        return not self == other

    def __hash__(self) -> int:
        return hash(self.latitude) ^ hash(self.longitude)


class Uri(str):
    """A convenience class to allow identification of a URI from other string
    types.
    Args:
        uri: The uri
    """

    def __repr__(self) -> str:
        return '%s(%s)' % (self.__class__.__name__,
                           super().__repr__())

    def __eq__(self, other: 'Uri') -> bool:
        assert isinstance(other, Uri)
        return super().__eq__(other)


class Bin(str):
    """A convenience class to allow identification of a Bin from other string
    types.
    Args:
        data: the datas
    """

    def __repr__(self) -> str:
        return '%s(%s)' % (self.__class__.__name__,
                           super().__repr__())

    def __eq__(self, other: 'Bin') -> bool:
        assert isinstance(other, Bin)
        return super().__eq__(other)


class XStr:
    """A convenience class to allow identification of a XStr.

        Args:
            encoding: encoding format (accept `hex` and `b64`)
            data: The data
    """

    def __init__(self, encoding: str, data: str):
        self.encoding = encoding
        if encoding == "hex":
            self.data = bytearray.fromhex(data)
        elif encoding == "b64":
            self.data = base64.b64decode(data)
        else:
            self.data = data.encode('ascii')  # Not decoded

    def data_to_string(self) -> str:
        """
        Dump the binary data to string with the corresponding encoding.
        Returns:
            A string
        """
        if self.encoding == "hex":
            return binascii.b2a_hex(self.data).decode("ascii")
        if self.encoding == "b64":
            return binascii.b2a_base64(self.data, newline=False).decode("ascii")
        raise ValueError("Ignore encoding")

    def __repr__(self) -> str:
        return 'XStr("%s","%s")' % (self.encoding, self.data_to_string())

    def __eq__(self, other: 'XStr') -> bool:
        if not isinstance(other, XStr):
            return False
        return self.data == other.data  # Check only binary data

    def __ne__(self, other: 'XStr') -> bool:
        if not isinstance(other, XStr):
            return True
        return not self.data == other.data  # Check only binary data


class _Singleton:
    def __copy__(self) -> '_Singleton':
        return self

    def __deepcopy__(self, memo: '_Singleton') -> '_Singleton':
        # A singleton return himself
        return self

    def __hash__(self) -> int:
        return hash(self.__class__)


class _MarkerType(_Singleton):
    """A singleton class representing a Marker."""

    def __repr__(self) -> str:
        return 'MARKER'


MARKER = _MarkerType()


class _NAType(_Singleton):
    """A singleton class representing a NA."""

    def __repr__(self) -> str:
        return 'NA'


NA = _NAType()


class _RemoveType(_Singleton):
    """A singleton class representing a Remove."""

    def __repr__(self) -> str:
        return 'REMOVE'


REMOVE = _RemoveType()


class Ref:
    """A reference to an object in Project Haystack.
        Args:
            name: the uniq id
            value: the comment to describe the reference
    """

    def __init__(self, name: str, value: Optional[str] = None):
        assert isinstance(name, str) and re.match("^[a-zA-Z0-9_:\\-.~]+$", name)
        self.name = name
        self.value = value

    @property
    def has_value(self):
        return self.value is not None

    def __repr__(self) -> str:
        return '%s(%r, %r)' % (
            self.__class__.__name__, self.name, self.value
        )

    def __str__(self) -> str:
        if self.has_value:
            return '@%s %r' % (
                self.name, self.value
            )
        return '@%s' % self.name

    def __eq__(self, other: 'Ref') -> bool:
        if not isinstance(other, Ref):
            return False
        return self.name == other.name

    def __ne__(self, other: 'Ref'):
        if not isinstance(other, Ref):
            return True
        return not self == other

    def __lt__(self, other: 'Ref') -> bool:
        return self.name.__lt__(other.name)

    def __le__(self, other: 'Ref') -> bool:
        return self.name.__le__(other.name)

    def __gt__(self, other: 'Ref') -> bool:
        return self.name.__gt__(other.name)

    def __ge__(self, other: 'Ref') -> bool:
        return self.name.__ge__(other.name)

    def __hash__(self) -> int:
        return hash(self.name)
