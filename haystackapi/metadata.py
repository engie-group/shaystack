# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
A support of metadata of a grid or column.
"""
import copy
from typing import Any, Iterable

from .datatypes import MARKER
from .sortabledict import SortableDict


class MetadataObject(SortableDict):  # pylint: disable=too-many-ancestors
    """An object that contains some metadata fields. Used as a convenience
    base-class for grids and columns, both of which have metadata.
    """

    def append(self, key: str, value: Any = MARKER, replace: bool = True) -> 'MetadataObject':
        """Append the item to the metadata.

        Args:
            key (str):
            value (Any):
            replace (bool):
        """
        self.add_item(key, value, replace=replace)
        return self

    def extend(self, items: Iterable[Any], replace: bool = True) -> None:
        """Append the items to the metadata.

        Args:
            items:
            replace (bool):
        """
        if isinstance(items, (dict, SortableDict)):
            items = list(items.items())

        for (key, value) in items:
            self.append(key, value, replace=replace)

    def copy(self) -> 'MetadataObject':
        return copy.deepcopy(self)
