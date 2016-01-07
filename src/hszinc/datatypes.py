#!/usr/bin/python
# -*- coding: utf-8 -*-
# Zinc data types
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si: 

class Quantity(object):
    '''
    A quantity is a scalar value (floating point) with a unit.
    '''
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


class Coordinate(object):
    '''
    A 2D co-ordinate in degrees latitude and longitude.
    '''
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return '%s(%r, %r)' % (
                self.__class__.__name__, self.latitude, self.longitude
        )

    def __str__(self):
        return '%f° lat %f° long' % (
                self.latitude, self.longitude
        )


class Uri(str):
    '''
    A convenience class to allow identification of a URI from other string
    types.
    '''
    pass


class Bin(str):
    '''
    A convenience class to allow identification of a Bin from other string
    types.
    '''
    # TODO: This seems to be the MIME type, no idea where the data lives.
    pass

class MarkerType(object):
    '''
    A singleton class representing a Marker.
    '''
    pass

marker = MarkerType()


class Ref(object):
    '''
    A reference to an object in Project Haystack.
    '''
    # TODO: The grammar specifies that it can have a string following a space,
    # but the documentation does not specify what this string encodes.  This is
    # distinct from the reference name itself immediately following the @
    # symbol.  I'm guessing it's some kind of value.
    def __init__(self, name, value):
        self.name   = name
        self.value  = value

    def __repr__(self):
        return '%s(%r, %r)' % (
                self.__class__.__name__, self.name, self.value
        )

    def __str__(self):
        return '@%s %r' % (
                self.name, self.value
        )
