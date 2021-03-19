# -*- coding: utf-8 -*-
# Zinc Grid
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
The typing for Haystack
"""
from datetime import date, time, datetime
from typing import Union, Dict, List, Any

from .datatypes import Quantity, Coordinate, Uri, Bin, XStr, _MarkerType, _NAType, _RemoveType, Ref

HaystackType = Union[str, int, float, bool,
                     date, time, datetime,
                     Ref, Quantity, Coordinate, Uri, Bin, XStr,
                     _MarkerType, _NAType, _RemoveType,
                     List[Any],
                     Dict[str, Any],
                     None]
""" All haystack compatible values (see https://project-haystack.org/doc/TagModel#tagKinds) """

Entity = Dict[str, HaystackType]
""" An entity is a collection of tag and values """
