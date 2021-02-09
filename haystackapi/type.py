from datetime import date, time, datetime
from typing import Union, Dict

from .datatypes import Quantity, Coordinate, Uri, Bin, XStr, _MarkerType, _NAType, _RemoveType, Ref

""" All haystack compatible values (see https://project-haystack.org/doc/TagModel#tagKinds) """
HaystackType = Union[str, int, float,
                     date, time, datetime,
                     Ref, Quantity, Coordinate, Uri, Bin, XStr,
                     _MarkerType, _NAType, _RemoveType, None]

""" An entity is a collection of tag and values """
Entity = Dict[str, HaystackType]
