# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import random

from shaystack.datatypes import REMOVE
from shaystack.grid import Grid
from shaystack.grid_diff import grid_diff, grid_merge
from .test_acid import gen_random_grid, gen_random_scalar, gen_random_str

GENERATION_NUMBER, PERCENT_PATCH, PERCENT_MOVE_COL, PERCENT_ADD_VAL, PERCENT_DUPLICATE = (10, 30, 5, 10, 5)


class RefuseRemove(BaseException):
    pass


def _patch_dict(a_dict, cols=None):
    """
    Args:
        a_dict:
        cols:
    """
    a_dict = a_dict.copy()
    max_rand = int(len(a_dict) * (PERCENT_PATCH / 100))
    keys = list(a_dict.keys())
    # Remove REMOVE flag
    for val in a_dict.values():
        if val is REMOVE:
            raise RefuseRemove()
    if keys:
        for _ in range(0, random.randint(0, max_rand) + 1):
            j = random.randint(0, len(keys) - 1)
            k = keys[j]
            if k != 'id':
                while True:
                    a_dict[k] = gen_random_scalar()
                    if a_dict[k] is not REMOVE:
                        break
    # Add keys
    if cols and random.randint(0, 100) < PERCENT_ADD_VAL:
        k = list(cols.keys())[random.randint(0, len(cols) - 1)]
        if k != 'id':
            a_dict[k] = gen_random_str()
    return a_dict


def gen_diff_metadata(metadata):
    """
    Args:
        metadata:
    """
    return _patch_dict(metadata)


def gen_diff_meta_cols(cols):
    """
    Args:
        cols:
    """
    cols = cols.copy()
    for col in cols:
        cols[col] = gen_diff_metadata(cols[col])

    # Move col
    if random.randint(0, 100) < PERCENT_MOVE_COL:
        i = random.randint(0, len(cols) - 1)
        j = random.randint(0, len(cols) - 1)
        k = cols.at(i)
        col = cols.pop_at(i)
        cols.add_item(k, col, index=j)
    return cols


def gen_new_row(grid):
    """
    Args:
        grid:
    """
    for row in grid:
        row = _patch_dict(row, grid.column)
        yield _patch_dict(row)


def gen_diff(orig):
    """
    Args:
        orig:
    """
    new_metadata = gen_diff_metadata(orig.metadata)
    new_meta_cols = gen_diff_meta_cols(orig.column)
    grid = Grid(orig.version, metadata=new_metadata, columns=new_meta_cols)
    for row in gen_new_row(orig):
        grid.append(row)
        if "id" not in row and random.randint(0, 100) < PERCENT_DUPLICATE:
            grid.append(row.copy())
    return grid


def _try_diff():
    while True:
        try:
            orig_grid = gen_random_grid()
            delta_grid = gen_diff(orig_grid)
            _validate_grid(orig_grid)
            _validate_grid(delta_grid)
            diff = grid_diff(orig_grid, delta_grid)
            _validate_grid(diff)
            apply = grid_merge(orig_grid.copy(), diff)
            _validate_grid(apply)
            assert apply == delta_grid
            return
        except RefuseRemove:
            pass


def _validate_grid(grid):
    """
    Args:
        grid:
    """
    # noinspection PyProtectedMember
    addr = [id(row) for row in grid._row]
    assert len(addr) == len(set(addr)), "Row in multiple place in grid"
    ids = [x['id'] for x in grid if 'id' in x]
    assert len(ids) == len(set(ids)), "Same id in multiple place in grid"


def test_multiple_diff():
    random.seed(0)
    for _ in range(0, GENERATION_NUMBER):
        _try_diff()
