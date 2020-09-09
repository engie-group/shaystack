#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
from copy import deepcopy

from .datatypes import REMOVE, MARKER
from .grid import Grid
from .metadata import MetadataObject
from .sortabledict import SortableDict


def grid_diff(left, right):
    diff = Grid(version=right._version, metadata={})
    metadata = diff.metadata
    metadata["diff_"] = MARKER  # Mark the grid to be a difference between grid

    # Calculate diff of metadata
    for k in left.metadata:
        if right.metadata and k in right.metadata:
            if left.metadata[k] != right.metadata[k]:
                metadata[k] = right.metadata[k]
        else:
            metadata[k] = REMOVE

    # Add metadata only in right
    for k in right.metadata:
        if k not in left.metadata:
            metadata[k] = right.metadata[k]

    # Calculate diff of columns
    columns = SortableDict()
    for k in right.column:
        columns[k] = MetadataObject()
    for right_col in right.column:
        if right_col not in left.column:
            # New column
            columns[right_col] = right.column[right_col]
        else:
            # Calculate diff
            m = MetadataObject()
            left_row = left.column[right_col]
            right_row = right.column[right_col]
            for k, v in right.column[right_col].items():
                if k in left_row:
                    if left_row[k] != v:
                        m[k] = v
                else:
                    m[k] = v

            for k, v in left_row.items():
                if k not in right_row:
                    m[k] = REMOVE
            columns[right_col] = m
    diff.column = columns

    # Add removed left columns
    for left_col in left.column:
        if left_col not in right.column:
            columns[left_col] = {'remove_': REMOVE}

    # Calculate diff of row
    pending_right_row = [id(row) for row in right if 'id' not in row]
    managed_right_row = []
    for left_row in left:
        if 'id' in left_row:
            left_id = left_row['id']
            if left_id in right:
                # row with same id in left and right
                right_row = right[left_id]
                diff_row = {"id": left_id}
                for col in left.column:
                    if col in left_row:
                        # Left has col
                        val_left = left_row[col]
                        if col in right_row:
                            # col is in left and right
                            val_right = right_row[col]
                            if val_left != val_right:
                                if col not in diff.column:
                                    diff.column[col] = right.column[col]
                                diff_row[col] = val_right
                        else:
                            # col is not in right
                            if col not in diff.column:
                                diff.column[col] = deepcopy(left.column[col])
                                diff.column[col] = {"des": "Removed column"}
                            diff_row[col] = REMOVE
                    else:
                        # Left has not col
                        if col in right_row:
                            if col not in diff.column:
                                diff.column[col] = right.column[col]
                            diff_row[col] = right_row[col]
                # Check add cols in right
                for col in right.column:
                    if col not in left.column:
                        diff_row[col] = right_row[col]
                diff.append(diff_row)
            else:
                # left id is not in right. row is deleted
                if 'id' not in diff.column:
                    diff.column['id'] = left.column['id']
                diff.append({"id": left_id, "remove_": REMOVE})
        else:
            same_values = False
            # Manage row without id
            # Search record in right, with the same values
            for right_row in right:
                if 'id' not in right_row:
                    if id(right_row) in managed_right_row:
                        continue
                    same_values = True
                    for col in left.column:
                        # Right have the same col
                        if left_row.get(col, None) != right_row.get(col, None):
                            same_values = False
                            break
                    if same_values:
                        # Found record with same value if left and right
                        if id(right_row) in pending_right_row:
                            pending_right_row.remove(id(right_row))
                            managed_right_row.append(id(right_row))
                        break
            # remove left row ?
            if not same_values:
                diff_row = left_row.copy()
                diff_row['remove_'] = REMOVE
                diff.append(diff_row)

    # Add the row with id, if it's only in right
    for k in right.keys():
        if k not in left:
            pending_right_row.append(id(right[k]))

    # Now, the pending_right_row have the not associated row
    for right_row in right:
        if id(right_row) in pending_right_row:
            diff.append(right_row)
    return diff


def grid_merge(orig_grid, diff):
    orig_grid._version = diff._version

    # Apply diff of metadata
    left_metadata = orig_grid.metadata

    for k_metadata, v_metadata in diff.metadata.items():
        if k_metadata == 'diff_' and v_metadata == MARKER:
            pass
        elif REMOVE == v_metadata:
            del left_metadata[k_metadata]
        else:
            left_metadata[k_metadata] = v_metadata

    # Apply diff of columns
    new_cols = diff.column.copy()  # Order describe by diff
    for col, v_col in diff.column.items():
        if 'remove_' in v_col:
            del new_cols[col]
        else:
            if col in orig_grid.column:
                map_col = orig_grid.column[col].copy()
            else:
                map_col = MetadataObject()
            for k, v in v_col.items():
                if v is REMOVE:
                    del map_col[k]
                else:
                    map_col[k] = v
            for k, v in diff.column[col].items():
                if k not in map_col and v is not REMOVE:
                    map_col[k] = v
            new_cols[col] = map_col
    orig_grid.column = new_cols

    # Apply diff of rows
    for diff_row in diff:
        if 'id' in diff_row:
            id_diff = diff_row['id']
            if id_diff in orig_grid:
                if 'remove_' in diff_row:
                    orig_grid.remove(id_diff)
                else:
                    left_row = orig_grid[id_diff]
                    for col in diff.column:
                        if col in diff_row:
                            val = diff_row[col]
                            if val is REMOVE:
                                del left_row[col]
                            else:
                                left_row[col] = val
            else:
                # New row with id
                orig_grid.append(diff_row)
        else:
            if 'remove_' in diff_row:
                copy_diff_row = diff_row.copy()
                del copy_diff_row['remove_']
                # Search same record
                for pos, grid_row in enumerate(orig_grid):
                    if grid_row == copy_diff_row:
                        orig_grid.remove(pos)
                        break
            else:
                # Add a new record
                orig_grid.append(diff_row)
    return orig_grid
