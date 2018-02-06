#!/usr/bin/python
# -*- coding: utf-8 -*-
# Project Haystack version definitions.
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Project Haystack Version comparison.

Project Haystack does not use a standard versioning scheme like Semantic
Versioning, rather, they have a Major.Minor scheme.  This tries to mimic
the Debian-style versioning handling:

The version number itself consists of digits grouped by decimal points;
followed by some arbitrary text.

Each group of digits is compared directly.
The arbitrary text is compared lexographically.

So, in this implementation:

        2.0 < 3.0
        2.0 == 2.0.0 == 2.0.0.0
        2.0 < 2.0a
        2.0a < 2.0b
"""

import re

VERSION_RE = re.compile(r'^(\d[\d\.]*)([^\d].*)*$')

class Version(object):
    """
    A Project Haystack version number
    """
    def __init__(self, ver_str):
        if isinstance(ver_str, Version):
            # Clone constructor
            self.version_nums = ver_str.version_nums
            self.version_extra = ver_str.version_extra
        else:
            match = VERSION_RE.match(ver_str)
            if match is None:
                raise ValueError('Not a valid version string: %r' % ver_str)

            # We should have a nice friendly dotted decimal, followed
            # by anything else not recognised.  Parse out the first bit.
            (version_nums, version_extra) = match.groups()
            self.version_nums = tuple([int(p or 0) \
                    for p in version_nums.split('.')])
            self.version_extra = version_extra

    def __str__(self):
        base = '.'.join([str(p) for p in self.version_nums])
        if self.version_extra:
            base += self.version_extra
        return base

    def _cmp(self, other):
        """
        Compare two Project Haystack version strings, then return
            -1 if self < other,
            0 if self == other
            or 1 if self > other.
        """
        if not isinstance(other, Version):
            other = Version(other)

        num1 = self.version_nums
        num2 = other.version_nums

        # Pad both to be the same length
        ver_len = max(len(num1), len(num2))
        num1 += tuple([0 for n in range(len(num1), ver_len)])
        num2 += tuple([0 for n in range(len(num2), ver_len)])

        # Compare the versions
        for (p1, p2) in zip(num1, num2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1

        # All the same, compare the extra strings.
        # If a version misses the extra part; we consider that as coming *before*.
        if self.version_extra is None:
            if other.version_extra is None:
                return 0
            else:
                return -1
        elif other.version_extra is None:
            return 1
        elif self.version_extra == other.version_extra:
            return 0
        elif self.version_extra < other.version_extra:
            return -1
        else:
            return 1

    def __hash__(self):
        return hash(str(self))

    # Comparison operators

    def __lt__(self, other):
        return self._cmp(other) < 0
    
    def __le__(self, other):
        return self._cmp(other) < 1

    def __eq__(self, other):
        return self._cmp(other) == 0

    def __ne__(self, other):
        return self._cmp(other) != 0

    def __ge__(self, other):
        return self._cmp(other) > -1

    def __gt__(self, other):
        return self._cmp(other) > 0


# Standard Project Haystack versions
VER_2_0 = Version('2.0')
VER_3_0 = Version('3.0')
LATEST_VER = VER_3_0
