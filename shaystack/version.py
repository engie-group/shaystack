# -*- coding: utf-8 -*-
# Project Haystack version definitions.
# See the accompanying LICENSE file.
# (C) 2018 VRT Systems
# (C) 2021 Engie Digital
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
The arbitrary text is compared lexicographically.

So, in this implementation:

        2.0 < 3.0
        2.0 == 2.0.0 == 2.0.0.0
        2.0 < 2.0a
        2.0a < 2.0b
"""

import re
import warnings
from typing import Union

_VERSION_RE = re.compile(r'^(\d[\d.]*)([^\d].*)*$')


class Version:
    """A Project Haystack version number.
    Args:
        ver_str: The version str
    """
    __slots__ = "version_nums", "version_extra"

    def __init__(self, ver_str: Union[str, 'Version']):
        if isinstance(ver_str, Version):
            # Clone constructor
            self.version_nums = ver_str.version_nums  # type: ignore
            self.version_extra = ver_str.version_extra  # type: ignore
        else:
            match = _VERSION_RE.match(ver_str)
            if match is None:
                raise ValueError('Not a valid version string: %r' % ver_str)

            # We should have a nice friendly dotted decimal, followed
            # by anything else not recognised.  Parse out the first bit.
            (version_nums, version_extra) = match.groups()
            if not version_nums:
                raise ValueError('Not a valid version string: %r' % ver_str)
            self.version_nums = tuple([int(p or 0)  # pylint: disable=consider-using-generator
                                       for p in version_nums.split('.')])
            self.version_extra = version_extra

    def __str__(self) -> str:
        base = '.'.join([str(p) for p in self.version_nums])
        if self.version_extra:
            base += self.version_extra
        return base

    def _cmp(self, other: Union['Version', str]) -> int:
        """Compare two Project Haystack version strings

        Args:
            other: Other version
        Returns
             -1 if self < other, 0 if self == other or 1 if self > other.
        """
        if isinstance(other, str):
            other = Version(other)

        num1 = self.version_nums
        num2 = other.version_nums

        # Pad both to be the same length
        ver_len = max(len(num1), len(num2))
        num1 += tuple([0 for _ in range(len(num1), ver_len)])  # pylint: disable=consider-using-generator
        num2 += tuple([0 for _ in range(len(num2), ver_len)])  # pylint: disable=consider-using-generator

        # Compare the versions
        for (pair_1, pair_2) in zip(num1, num2):
            if pair_1 < pair_2:
                return -1
            if pair_1 > pair_2:
                return 1

        # All the same, compare the extra strings.
        # If a version misses the extra part; we consider that as coming *before*.
        if self.version_extra is None:
            if other.version_extra is None:
                return 0
            return -1
        if other.version_extra is None:
            return 1
        if self.version_extra == other.version_extra:
            return 0
        if self.version_extra < other.version_extra:
            return -1
        return 1

    def __hash__(self) -> int:
        return hash(str(self))

    # Comparison operators

    def __lt__(self, other) -> bool:
        return self._cmp(other) < 0

    def __le__(self, other) -> bool:
        return self._cmp(other) < 1

    def __eq__(self, other) -> bool:
        return self._cmp(other) == 0

    def __ne__(self, other) -> bool:
        return self._cmp(other) != 0

    def __ge__(self, other) -> bool:
        return self._cmp(other) > -1

    def __gt__(self, other) -> bool:
        return self._cmp(other) > 0

    @classmethod
    def nearest(cls, ver: Union[str, 'Version']) -> 'Version':
        """Retrieve the official version nearest the one given.

        Args:
            ver: The version to analyse
        Returns:
            The version nearest the one given
        """
        if isinstance(ver, str):
            ver = Version(ver)

        if ver in OFFICIAL_VERSIONS:
            return ver

        # We might not have an exact match for that.
        # See if we have one that's newer than the grid we're looking at.
        versions = list(OFFICIAL_VERSIONS)
        versions.sort(reverse=True)
        best = None
        for candidate in versions:
            # Due to ambiguities, we might have an exact match and not know it.
            # '2.0' will not hash to the same value as '2.0.0', but both are
            # equivalent.
            if candidate == ver:
                # We can't beat this, make a note of the match for later
                return candidate

            # If we have not seen a better candidate, and this is older
            # then we may have to settle for that.
            if (best is None) and (candidate < ver):
                warnings.warn('This version of shift-4-haystack does not yet '
                              'support version %s, please seek a newer version '
                              'or file a bug.  Closest (older) version supported is %s.'
                              % (ver, candidate))
                return candidate

            # Probably the best so far, but see if we can go closer
            if candidate > ver:
                best = candidate

        # Unhappy path, no best option?  This should not happen.
        assert best is not None
        warnings.warn('This version of shift-4-haystack does not yet '
                      'support version %s, please seek a newer version '
                      'or file a bug.  Closest (newer) version supported is %s.'
                      % (ver, best))
        return best


# Standard Project Haystack versions
VER_2_0 = Version('2.0')
VER_3_0 = Version('3.0')
LATEST_VER = VER_3_0

OFFICIAL_VERSIONS = {
    VER_2_0, VER_3_0
}
