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
