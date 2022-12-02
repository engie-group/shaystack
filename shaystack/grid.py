# -*- coding: utf-8 -*-
# Zinc Grid
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

"""
An entire ontology in memory.
It's like a list of dict.
"""

import copy
import datetime
import logging
import numbers
import re
from collections.abc import MutableSequence, Sequence  # pylint: disable=no-name-in-module
from typing import Union, Iterable, Any, Optional, KeysView, Tuple, List, cast, Dict

import pytz

from .datatypes import NA, Quantity, Coordinate, Ref
from .metadata import MetadataObject
from .sortabledict import SortableDict
from .type import Entity
from .version import Version, VER_3_0

log = logging.getLogger("ping.Provider")


# noinspection PyArgumentList
class Grid(MutableSequence):  # pytlint: disable=too-many-ancestors
    """A grid is basically a series of tabular records. The grid has a header
    which describes some metadata about the grid and its columns. This is
    followed by zero or more rows.

    The grid propose different standard operator.

    - It's possible to access an entity with the position in the grid: `grid[1]`
    - or if the entity has an `id`, with this `id`: `grid[Ref("abc")]`
    - To extract a portion of grid, use a slice: `grid[10:12]`
    - To check if a specific `id` is in the grid: `Ref("abc") in grid`
    - To calculate the difference between grid: `grid_v2 - grid_v1`
    - To merge two grid: `grid_a + grid_b`
    - To compare a grid: `grid_v1 + (grid_v2 - grid_v1) == grid_v2`
    - Size of grid: `len(grid)`
    - Replace an entity with `id`: `grid[Ref("abc")] = new_entity`
    - Replace a group of entities: `grid[2:3] = [new_entity1,new_entity2]`
    - Delete an entity with `id`: `del grid[Ref("abc")]`

    Args:
        version: The haystack version (See VERSION_...)
        metadata: A dictionary with the metadata associated with the grid.
        columns: A list of columns, or a dictionary with columns name and corresponding metadata
    """

    __slots__ = "_version", "_version_given", "metadata", "column", "_row", "_index"

    def __init__(self,
                 version: Union[str, Version, None] = None,
                 metadata: Union[None, Entity, MetadataObject, SortableDict] = None,
                 columns: Union[SortableDict,
                                Entity,
                                Iterable[Union[Tuple[str, Any], str]],
                                None] = None):
        version_given = version is not None
        if version_given:
            version = Version(version)  # type: ignore
        else:
            version = VER_3_0
        self._version = version
        self._version_given = version_given

        # Metadata
        self.metadata = MetadataObject(validate_fn=self._detect_or_validate)

        # The columns
        self.column = SortableDict()

        # Rows
        self._row: List[Entity] = []

        # Internal index
        self._index: Optional[Dict[Ref, Entity]] = None

        if metadata is not None:
            self.metadata.update(metadata.items())

        if columns is not None:
            if isinstance(columns, (dict, SortableDict)):
                columns = list(columns.items())
            elif isinstance(columns, Sequence) and columns and not isinstance(columns[0], tuple):
                columns = list(zip(columns, [{}] * len(columns)))

            for col_id, col_meta in columns:  # type: ignore
                # Convert sorted lists and dicts back to a list of items.
                if isinstance(col_meta, (dict, SortableDict)):
                    col_meta = list(col_meta.items())

                metadata_object = MetadataObject(validate_fn=self._detect_or_validate)
                metadata_object.extend(col_meta)
                self.column.add_item(col_id, metadata_object)

    # noinspection PyArgumentList
    @staticmethod
    def _approx_check(version_1: Any, version_2: Any) -> bool:
        """
        Compare two values with a tolerance

        Args:
            version_1: value one
            version_2: value two
        Returns:
            true if the values are approximately identical
        """
        if isinstance(version_1, numbers.Number) and isinstance(version_2, numbers.Number):
            # noinspection PyUnresolvedReferences
            return abs(version_1 - version_2) < 0.000001  # type: ignore
        # pylint: disable=C0123
        if type(version_1) != type(version_2) and \
                not (isinstance(version_1, str) and isinstance(version_2, str)):
            return False
        # pylint: enable=C0123
        if isinstance(version_1, datetime.time) and isinstance(version_2, datetime.time):
            # noinspection PyArgumentList
            return version_1.replace(microsecond=0) == version_2.replace(microsecond=0)
        if isinstance(version_1, datetime.datetime) and isinstance(version_2, datetime.datetime):
            dt1, dt2 = version_1.replace(tzinfo=pytz.UTC), version_2.replace(tzinfo=pytz.UTC)
            return dt1.date() == dt2.date() and Grid._approx_check(dt1.time(), dt2.time())
        if isinstance(version_1, Quantity) and isinstance(version_2, Quantity):
            return version_1.units == version_2.units and \
                   Grid._approx_check(version_1.m, version_2.m)
        if isinstance(version_1, Coordinate) and isinstance(version_2, Coordinate):
            return Grid._approx_check(version_1.latitude, version_2.latitude) and \
                   Grid._approx_check(version_1.longitude, version_2.longitude)
        if isinstance(version_1, dict) and isinstance(version_2, dict):
            for key, val in version_1.items():
                if not Grid._approx_check(val, version_2.get(key, None)):
                    return False
            for key, val in version_2.items():
                if key not in version_1 and not Grid._approx_check(version_1.get(key, None), val):
                    return False
            return True
        return version_1 == version_2

    def __eq__(self, other: 'Grid') -> bool:  # type: ignore
        """
        Campare two grid with tolerance.
        Args:
            other: Other grid
        Returns:
            true if equals
        """
        if not isinstance(other, Grid):
            return False
        if set(self.metadata.keys()) != set(other.metadata.keys()):
            return False
        for key in self.metadata.keys():
            if not Grid._approx_check(self.metadata[key], other.metadata[key]):
                return False
        # Check column matches
        if set(self.column.keys()) != set(other.column.keys()):
            return False

        for col_name in self.column.keys():
            if col_name not in other.column or \
                    len(self.column[col_name]) != len(other.column[col_name]):
                return False
            for key in self.column[col_name].keys():
                if not Grid._approx_check(self.column[col_name][key], other.column[col_name][key]):
                    return False
        # Check row matches
        if len(self) != len(other):
            return False

        pending_right_row = [id(row) for row in other if 'id' not in row]
        for left in self._row:
            # Search record in other with same values
            find = False
            if 'id' in left:
                if left['id'] in other and self._approx_check(left, other[left['id']]):  # type: ignore
                    find = True
            else:
                for right in other._row:
                    if id(right) not in pending_right_row:
                        continue
                    if self._approx_check(left, right):
                        find = True
                        pending_right_row.remove(id(right))
                        break
            if not find:
                return False

        return True

    def __sub__(self, other: 'Grid') -> 'Grid':
        """Calculate the difference between two grid. The result is a grid with
        only the attributs to update (change value, delete, etc) If a row with
        id must be removed, - if the row has an id, the result add a row with
        this id, and a tag 'remove_' - if the row has not an id, the result add
        a row with all values of the original row, and a tag 'remove_'

        It's possible to update all metadatas, the order of columns, add,
        remove or update some rows

        It's possible to apply the result in a grid, with the add operator.
        At all time, with gridA and gridB, gridA + (gridB - gridA) == gridB

        Args:
            other: grid to substract
        Returns:
            Only the difference between grid.
        """
        assert isinstance(other, Grid)
        from .grid_diff import grid_diff  # pylint: disable: import-outside-toplevel
        return grid_diff(other, self)

    def __add__(self, other: 'Grid') -> 'Grid':
        """Merge two grids. The metadata can be modified with the values from
        other. Some attributs can be removed if the `other` attributs is REMOVE.
        If a row have a 'remove_' tag, the corresponding row was removed.

        The result of __sub__() can be used to patch the current grid. At all
        time, with `gridA` and `gridB`, `gridA + (gridB - gridA) == gridB`

        Args:
            other: List of entities to updates
        Returns:
            A new grid
        """
        assert isinstance(other, Grid)
        from .grid_diff import grid_merge  # pylint: disable: import-outside-toplevel
        if 'diff_' in self.metadata:
            return grid_merge(other.copy(), self)
        return grid_merge(self.copy(), other)

    def __repr__(self) -> str:  # pragma: no cover
        """Return a representation of this grid."""
        parts = ['\tVersion: %s' % str(self.version)]
        if bool(self.metadata):
            parts.append('\tMetadata: %s' % self.metadata)

        column_meta = []
        for col_name, col_meta in self.column.items():
            if bool(col_meta):
                column_meta.append('\t\t%s: %s' % (col_name, col_meta))
            else:
                column_meta.append('\t\t%s' % col_name)

        if bool(column_meta):
            parts.append('\tColumns:\n%s' % '\n'.join(column_meta))
        elif self.column:
            parts.append('\tColumns: %s' % ', '.join(self.column.keys()))
        else:
            parts.append('\tNo columns')

        if bool(self):
            parts.extend([
                '\t---- Row %4d:\n\t%s' % (row, '\n\t'.join([
                    (('%s=%r' % (col_name, data[col_name]))
                     if col_name in data else
                     ('%s absent' % col_name)) for col_name in self.column.keys()]))
                for (row, data) in enumerate(self)
            ])
        else:
            parts.append('\tNo rows')
        class_name = self.__class__.__name__
        return '%s\n%s\n' % (
            class_name, '\n'.join(parts)
        )

    def __getitem__(self, key: Union[int, Ref, slice]) -> Union[Entity, 'Grid']:  # type: ignore
        """Retrieve the row at index. :param key: index, Haystack reference or
        slice

        Args:
            key: the position, the Reference or a slice

        Returns:
            The entity of an new grid with a portion of entities, with the same metadata and columns
        """
        if isinstance(key, int):
            return cast(Entity, self._row[key])
        if isinstance(key, slice):
            result = Grid(version=self.version, metadata=self.metadata, columns=self.column)
            result._row = self._row[key]
            result._index = None
            return result
        assert isinstance(key, Ref), "The 'key' must be a Ref or int"
        if not self._index:
            self.reindex()
        return cast(Entity, self._index[key])  # type: ignore

    def __contains__(self, key: Union[int, Ref]) -> bool:  # type: ignore
        """Return an entity with the corresponding id.

        Args:
            key: The position of id of entity

        Returns:
            'True' if the referenced entity is present
        """
        if isinstance(key, int):
            return 0 <= key < len(self._row)
        if not self._index:
            self.reindex()
        return key in self._index  # type: ignore

    def __len__(self) -> int:
        """Return the number of rows in the grid."""
        return len(self._row)

    def __setitem__(self, index: Union[int, Ref, slice],  # type: ignore
                    value: Union[Entity, List[Entity]]) -> 'Grid':
        """Replace the row at index.

        Args:
            index: position of reference, reference of slice
            value: the new entity
        Returns:
            `self`
        """
        if isinstance(value, dict):
            for val in value.values():
                self._detect_or_validate(val)
        if isinstance(index, int):
            if not isinstance(value, dict):
                raise TypeError('value must be a dict')
            if "id" in self._row[index]:
                self._index.pop(self._row[index]['id'], None)  # type: ignore
            self._row[index] = value
            if "id" in value:
                self._index[value["id"]] = value  # type: ignore
        elif isinstance(index, slice):
            if isinstance(value, dict):
                raise TypeError('value must be iterable, not a dict')
            self._index = None
            self._row[index] = value
            for row in value:
                for val in row.values():
                    self._detect_or_validate(val)
        else:
            if not isinstance(value, dict):
                raise TypeError('value must be a dict')
            if not self._index:
                self.reindex()
            idx = list.index(self._row, self._index[index])  # type: ignore
            if "id" in self._row[idx]:
                self._index.pop(self._row[idx]['id'], None)  # type: ignore
            self._row[idx] = value
            if "id" in value:
                self._index[value["id"]] = value  # type: ignore
        return self

    def __delitem__(self, key: Union[int, Ref]) -> Optional[Entity]:  # type: ignore
        """Delete the row at index.

        Args:
            key: The key to find the corresponding entity
        Returns:
            The entity or `None`
        """
        return self.pop(key)

    def clear(self):
        self._row = []
        self._index = None

    @property
    def version(self) -> Version:  # pragma: no cover
        """ The haystack version of grid """
        return self._version

    @property
    def nearest_version(self) -> Version:  # pragma: no cover
        """ The nearest haystack version of grid """
        return Version.nearest(self._version)

    def get(self, index: Ref, default: Optional[Entity] = None) -> Entity:
        """Return an entity with the corresponding id.

        Args:
            index: The id of entity
            default: The default value if the entity is not found

        Returns:
            The entity with the id == index or the default value
        """
        if not self._index:
            self.reindex()
        return cast(Entity, self._index.get(index, default))  # type: ignore

    def keys(self) -> KeysView[Ref]:
        """ Return the list of ids of entities with `id`

        Returns:
             The list of ids of entities with `id`
        """
        if not self._index:
            self.reindex()
        return self._index.keys()  # type: ignore

    def pop(self, *index: Union[int, Ref]) -> Optional[Entity]:
        """Delete the row at index or with specified Ref id. If multiple
        index/key was specified, all row was removed. Return the old value of
        the first deleted item.

        Args:
            *index: A list of index (position or reference)
        """
        ret_value = None
        for key in sorted(index, reverse=True):  # Remove index at the end
            if isinstance(key, int):
                if not 0 <= key < len(self._row):
                    ret_value = None
                else:
                    if "id" in self._row[key] and self._index:
                        del self._index[self._row[key]['id']]  # type: ignore
                    ret_value = self._row[key]
                    del self._row[key]
            else:
                if not self._index:
                    self.reindex()
                if key not in self._index:  # type: ignore
                    ret_value = None
                else:
                    self._row.remove(self._index[key])  # type: ignore
                    ret_value = self._index.pop(key)  # type: ignore
        return cast(Optional[Entity], ret_value)

    def insert(self, index: int, value: Entity) -> 'Grid':  # type: ignore
        """Insert a new entity before the index position.

        Args:
            index: The position where to insert
            value: The new entity to add
        Returns
            `self`
        """
        if not isinstance(value, dict):
            raise TypeError('value must be a dict')
        for val in value.values():
            self._detect_or_validate(val)
        self._row.insert(index, value)
        if "id" in value:
            if not self._index:
                self.reindex()
            self._index[value["id"]] = value  # type: ignore
        return self

    def reindex(self) -> 'Grid':
        """Reindex the grid if the user, update directly an id of a row.
        Returns
            `self`
        """
        self._index = {}
        for item in self._row:
            if "id" in item:
                assert isinstance(item["id"], Ref), "The 'id' tag must be a reference"
                self._index[item["id"]] = item
        return self

    def pack_columns(self) -> 'Grid':
        """
        Remove unused columns.
        Returns:
            `self`
        """
        using_columns = set()
        columns_keys = self.column.keys()
        for row in self._row:
            for col_name in columns_keys:
                if col_name in row:
                    using_columns.add(col_name)
                if len(using_columns) == len(columns_keys):  # All columns was found
                    return self
        self.column = {k: self.column[k] for k in using_columns}  # type: ignore
        return self

    def extends_columns(self) -> 'Grid':
        """
        Add missing columns

        Returns:
            `self`
        """
        new_cols = self.column.copy()
        for row in self._row:
            for k in row.keys():
                if k not in new_cols:
                    new_cols[k] = {}
        self.column = new_cols
        return self

    def extend(self, values: Iterable[Entity]) -> 'Grid':  # type: ignore
        """
        Add a list of entities inside the grid

        Args:
            values: The list of entities to insert.
        Returns:
            `self`
        """
        super().extend(values)
        for item in self._row:
            if "id" in item:
                self._index[item["id"]] = item  # type: ignore
        return self

    def sort(self, tag: str) -> 'Grid':
        """
        Sort the entity by a specific tag
        Args:
            tag: The tag to use to sort the entity
        Returns:
            `self`
        """
        self._row = sorted(self._row, key=lambda row: row[tag])  # type: ignore
        return self

    def copy(self) -> 'Grid':
        """ Create a copy of current grid.

        The corresponding entities were duplicate

        Returns:
            A copy of the current grid.
        """
        a_copy = copy.deepcopy(self)
        a_copy._index = None  # Remove index pylint: disable=protected-access
        return a_copy

    def filter(self, grid_filter: str, limit: int = 0) -> 'Grid':
        """Return a filter version of this grid.

        The entities were share between original grid and the result.

        Use a `grid.filter(...).deepcopy()` if you not want to share metadata, columns
        and rows

        Args:
            grid_filter: The filter expression (see specification)
            limit: The maximum number of result
        Returns:
            A new grid with only the selected entities.
        """
        assert limit >= 0
        from .grid_filter import filter_function  # pylint: disable: import-outside-toplevel
        if grid_filter is None or grid_filter.strip() == '':
            if limit == 0:
                return self
            result = Grid(version=self.version, metadata=self.metadata, columns=self.column)
            result.extend(self.__getitem__(slice(0, limit)))  # type: ignore
            return result

        result = Grid(version=self.version, metadata=self.metadata, columns=self.column)
        a_filter = filter_function(grid_filter)
        for row in self._row:
            if a_filter(self, row):
                result.append(row)
            if limit and len(result) == limit:
                break
        return result

    def select(self, select: Optional[str]) -> 'Grid':
        """
        Select only some tags in the grid.
        Args:
            select: A list a tags (accept operator ! to exclude some columns)
        Returns:
             A new grid with only selected columns. Use grid.purge_grid() to update the entities.
        """
        if select:
            select = select.strip()
            if select not in ["*", '']:
                if '!' in select:
                    new_cols = copy.deepcopy(self.column)
                    new_grid = Grid(version=self.version, metadata=self.metadata, columns=new_cols)
                    for col in re.split('[, ]', select):
                        col = col.strip()
                        if not col.startswith('!'):
                            raise ValueError("Impossible to merge positive and negative selection")
                        if col[1:] in new_cols:
                            del new_cols[col[1:]]
                    new_grid.column = new_cols
                    return new_grid
                new_cols = SortableDict()
                new_grid = cast(Grid, self[:])
                for col in re.split('[, ]', select):
                    col = col.strip()
                    if col.startswith('!'):
                        raise ValueError("Impossible to merge positive and negative selection")
                    if col in self.column:
                        new_cols[col] = self.column[col]
                    else:
                        new_cols[col] = {}

                new_grid.column = new_cols
                return cast(Grid, new_grid)
        return self.copy()

    def purge(self) -> 'Grid':
        """
        Remove all tags in all entities, not in columns
        Returns:
             A new grid with entities compatible with the columns
        """
        cols = self.column
        new_grid = Grid(version=self.version, metadata=self.metadata, columns=cols)
        for row in self:
            new_grid.append({key: val for key, val in row.items() if key in cols})
        return new_grid

    def _detect_or_validate(self, val: Any) -> bool:
        """Detect the version used from the row content, or validate against the
        version if given.
        """
        if (val is NA) \
                or isinstance(val, (list, dict, SortableDict, Grid)):
            # Project Haystack 3.0 type.
            self._assert_version(VER_3_0)
        return True

    def _assert_version(self, version: Version) -> None:
        """Assert that the grid version is equal to or above the given value. If
        no version is set, set the version.
        """
        if self.nearest_version < version:
            if self._version_given:
                raise ValueError(
                    'Data type requires version %s' % version)
            self._version = version
