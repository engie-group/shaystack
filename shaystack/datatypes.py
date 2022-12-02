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
from typing import Optional, NewType

from .pintutil import unit_reg, _to_pint_unit

MODE = NewType('Mode', str)  # type: ignore
"""
Compatible haystack file format
"""
MODE_ZINC: MODE = MODE('text/zinc')
MODE_TRIO: MODE = MODE('text/trio')
MODE_JSON: MODE = MODE('application/json')
MODE_HAYSON: MODE = MODE('application/hayson')
MODE_CSV: MODE = MODE('text/csv')


# Update the unit when create a pint.Quantity
class Quantity(unit_reg.Quantity):
    """
    A quantity with unit.
    The quantity use the pint framework and can be converted.
    See [here](https://pint.readthedocs.io/en/stable/tutorial.html#defining-a-quantity)

    Properties:
        value: The magnitude
        units: Pint unit
        symbol: The original symbol
    """

    def __new__(cls, value, units=None):
        new_quantity = unit_reg.Quantity.__new__(Quantity, value,
                                                 _to_pint_unit(units) if units else None)
        new_quantity.symbol = units
        return new_quantity


class Coordinate:
    """A 2D co-ordinate in degrees latitude and longitude.
        Args:
            latitude: the latitude
            longitude: the longitude
    """
    __slots__ = "latitude", "longitude"

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

    def __eq__(self, other: 'Coordinate') -> bool:  # type: ignore
        if not isinstance(other, Coordinate):
            return False
        return (self.latitude == other.latitude) and \
               (self.longitude == other.longitude)

    def __ne__(self, other: 'Coordinate') -> bool:  # type: ignore
        if not isinstance(other, Coordinate):
            return True
        return not self == other

    def __hash__(self) -> int:
        return hash(self.latitude) ^ hash(self.longitude)


class Uri(str):
    """A convenience class to allow identification of a URI from other string
    types.
    """

    def __repr__(self) -> str:
        return '%s(%s)' % (self.__class__.__name__,
                           super().__repr__())

    def __eq__(self, other: 'Uri') -> bool:  # type: ignore
        if not isinstance(other, Uri):
            return False
        return super().__eq__(other)


class Bin(str):
    """A convenience class to allow identification of a Bin from other string
    types.
    """

    def __repr__(self) -> str:
        return '%s(%s)' % (self.__class__.__name__,
                           super().__repr__())

    def __eq__(self, other: 'Bin') -> bool:  # type: ignore
        assert isinstance(other, Bin)
        return super().__eq__(other)


class XStr:
    """A convenience class to allow identification of a XStr.

        Args:
            encoding: encoding format (accept `hex` and `b64`)
            data: The data
    """
    __slots__ = "encoding", "data"

    def __init__(self, encoding: str, data: str):
        self.encoding = encoding
        if encoding == "hex":
            self.data = bytearray.fromhex(data)
        elif encoding == "b64":
            self.data = base64.b64decode(data)  # type: ignore
        else:
            self.data = data.encode('ascii')  # type: ignore # Not decoded

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

    def __eq__(self, other: 'XStr') -> bool:  # type: ignore
        if not isinstance(other, XStr):
            return False
        return self.data == other.data  # Check only binary data

    def __ne__(self, other: 'XStr') -> bool:  # type: ignore
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

    __slots__ = "name", "value"

    def __init__(self, name: str, value: Optional[str] = None):
        if name.startswith("@"):
            name = name[1:]
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

    def __eq__(self, other: 'Ref') -> bool:  # type: ignore
        if not isinstance(other, Ref):
            return False
        return self.name == other.name

    def __ne__(self, other: 'Ref'):  # type: ignore
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
