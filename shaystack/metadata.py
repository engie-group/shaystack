# -*- coding: utf-8 -*-
# Zinc Grid Metadata
# See the accompanying LICENSE file.
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
    """An object that contains some metadata fields.

    Used as a convenience base-class for grids and columns, both of which have metadata.
    """

    def append(self, key: str, value: Any = MARKER, replace: bool = True) -> 'MetadataObject':
        """Append the item to the metadata.

        Args:
            key: The tag name
            value: The value
            replace: Flag to replace or not the value
        Returns
            `self`
        """
        self.add_item(key, value, replace=replace)
        return self

    def extend(self, items: Iterable[Any], replace: bool = True) -> 'MetadataObject':
        """Append the items to the metadata.

        Args:
            items: A list of items
            replace: Flag to replace or not the value
        Returns
            `self`
        """
        if isinstance(items, (dict, SortableDict)):
            items = list(items.items())

        for (key, value) in items:
            self.append(key, value, replace=replace)
        return self

    def copy(self) -> 'MetadataObject':
        """
        Deep copy of metadata
        Returns:
            A new metadata object
        """
        return copy.deepcopy(self)
