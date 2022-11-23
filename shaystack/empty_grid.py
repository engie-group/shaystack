# -*- coding: utf-8 -*-
# Zinc Grid dumper
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
Read-only Empty grid
"""

from typing import Union, List, Optional, Iterable

from .datatypes import Ref
from .grid import Grid
from .type import Entity
from .version import VER_3_0


class _ImmuableGrid(Grid):
    def __add__(self, other: 'Grid') -> 'Grid':
        raise NotImplementedError("Read only grid")

    def __setitem__(self, index: Union[int, Ref, slice],  # type: ignore
                    value: Union[Entity, List[Entity]]) -> 'Grid':
        raise NotImplementedError("Read only grid")

    def __delitem__(self, key: Union[int, Ref]) -> Optional[Entity]:  # type: ignore
        raise NotImplementedError("Read only grid")

    def clear(self):
        raise NotImplementedError("Read only grid")

    def pop(self, *index: Union[int, Ref]) -> Optional[Entity]:
        raise NotImplementedError("Read only grid")

    def insert(self, index: int, value: Entity) -> 'Grid':  # type: ignore
        raise NotImplementedError("Read only grid")

    def reindex(self) -> 'Grid':
        raise NotImplementedError("Read only grid")

    def pack_columns(self) -> 'Grid':
        raise NotImplementedError("Read only grid")

    def extends_columns(self) -> 'Grid':
        raise NotImplementedError("Read only grid")

    def extend(self, values: Iterable[Entity]) -> 'Grid':  # type: ignore
        raise NotImplementedError("Read only grid")

    def sort(self, tag: str) -> 'Grid':
        raise NotImplementedError("Read only grid")

    def purge(self) -> 'Grid':
        raise NotImplementedError("Read only grid")

    def copy(self) -> 'Grid':
        return Grid()


EmptyGrid = _ImmuableGrid(version=VER_3_0, columns={"empty": {}})
