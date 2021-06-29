# -*- coding: utf-8 -*-
# Grid handling tests
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import copy
import datetime

from shaystack import mode_to_suffix, suffix_to_mode, Ref
from shaystack.grid import Grid, Version, VER_3_0, Quantity, Coordinate
from shaystack.sortabledict import SortableDict


def test_grid_given_metadata():
    # Test that when passing in metadata, it is set as given.
    meta = SortableDict()
    meta['first'] = 1
    meta['second'] = 2
    meta['third'] = 3
    meta['fourth'] = 4

    assert list(Grid(metadata=meta).metadata.items()) == [
        ('first', 1), ('second', 2), ('third', 3), ('fourth', 4)
    ]


def test_grid_given_column_list():
    col_list = [('col1', [('c1m1', None), ('c1m2', None)]),
                ('col2', [('c2m1', None), ('c2m2', None)])]
    grid = Grid(columns=col_list)
    assert list(grid.column.keys()) == ['col1', 'col2']
    for col, meta in col_list:
        assert list(grid.column[col].items()) == meta


def test_grid_given_column_dict():
    cols = SortableDict([('col1', [('c1m1', None), ('c1m2', None)]),
                         ('col2', [('c2m1', None), ('c2m2', None)])])
    grid = Grid(columns=cols)
    assert list(grid.column.keys()) == ['col1', 'col2']
    for col, meta in cols.items():
        assert list(grid.column[col].items()) == meta


def test_grid_given_column_meta_dict():
    cols = SortableDict([('col1', SortableDict([('c1m1', None), ('c1m2', None)])),
                         ('col2', SortableDict([('c2m1', None), ('c2m2', None)]))])
    grid = Grid(columns=cols)
    assert list(grid.column.keys()) == ['col1', 'col2']
    for col, meta in cols.items():
        assert list(grid.column[col].items()) == list(meta.items())


def test_grid_getitem():
    grid = Grid()
    grid.column['test'] = {}

    row = {'test': 'This is a test'}
    grid.append(row)
    assert grid[0] is row


def test_grid_getitem_with_id():
    grid = Grid()
    grid.column['id'] = {}
    grid.column['test'] = {}

    row = {'id': Ref('myid'), 'test': 'This is a test'}
    grid.append(row)
    assert grid[Ref('myid')] is row


def test_grid_setitem():
    grid = Grid()
    grid.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = {'test': 'This is another test'}
    grid.append(row_1)
    grid[0] = row_2
    assert grid[0] is row_2


def test_grid_append_notdict():
    grid = Grid()
    grid.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = 'This is not a dict'
    grid.append(row_1)
    try:
        grid.append(row_2)
        assert False
    except TypeError as exception:
        assert str(exception) == 'value must be a dict'
        assert len(grid) == 1


def test_grid_append_v2_list_fail():
    grid = Grid(version='2.0')
    grid.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = {'test': ['This should fail']}
    grid.append(row_1)
    try:
        grid.append(row_2)
        assert False, 'Appended invalid data type'
    except ValueError as exception:
        assert str(exception) == 'Data type requires version 3.0'


def test_grid_append_nover_list():
    grid = Grid(version=None)
    assert grid.version == Version('3.0')
    grid.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = {'test': ['This should fail']}
    grid.append(row_1)
    assert grid.version == Version('3.0')
    grid.append(row_2)
    assert grid.version == Version('3.0')


def test_grid_setitem_notdict():
    grid = Grid()
    grid.column['test'] = {}

    row = {'test': 'This is a test'}
    grid.append(row)

    try:
        # noinspection PyTypeChecker
        grid[0] = 'This is not a dict'  # type: ignore
        assert False, 'Accepted a string'
    except TypeError:
        pass
    assert len(grid) == 1
    assert grid[0]['test'] == 'This is a test'


def test_grid_del():
    grid = Grid(columns=['id', 'test'])
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3},
        {'id': Ref('myid')}
    ]
    grid.extend(rows)
    assert len(grid) == 4
    del grid[1]
    del grid[Ref('myid')]
    assert len(grid) == 2
    assert grid[0] is rows[0]
    assert grid[1] is rows[2]


def test_pop_key():
    grid = Grid(columns=["id", "a"])
    row = {"id": Ref("myid"), "a": 1, "b": 2}
    grid.append(row)
    old = grid.pop(Ref("myid"))
    assert not grid
    assert id(old) == id(row)


def test_pop_multiple_keys():
    grid = Grid(columns=["id", "a"])
    row1 = {"id": Ref("id1"), "a": 1, "b": 2}
    row2 = {"id": Ref("id2"), "a": 1, "b": 2}
    grid.append(row1)
    grid.append(row2)
    old = grid.pop(Ref("id1"), Ref("id2"))
    assert not grid
    assert id(old) == id(row1)


def test_pop_invalid_key():
    grid = Grid(columns=["id", "a"])
    row = {"id": Ref("myid"), "a": 1, "b": 2}
    grid.append(row)
    old = grid.pop(Ref("other_id"))
    assert grid
    assert not old


def test_pop_pos():
    grid = Grid(columns=["id", "a"])
    row = {"id": Ref("myid"), "a": 1, "b": 2}
    grid.append(row)
    old = grid.pop(0)
    assert not grid
    assert id(old) == id(row)


def test_pop_multiple_pos():
    grid = Grid(columns=["id", "a"])
    row = {"id": Ref("id2"), "a": 1, "b": 2}
    grid.append(row)
    old = grid.pop(0, 1)
    assert not grid
    assert id(old) == id(row)


def test_pop_invalid_pos():
    grid = Grid(columns=["id", "a"])
    row = {"id": Ref("myid"), "a": 1, "b": 2}
    grid.append(row)
    old = grid.pop(-1)
    assert grid
    assert not old


def test_grid_insert():
    grid = Grid()
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ]
    grid.column['test'] = {}
    grid.extend(rows)
    assert len(grid) == 3
    new_row = {'test': 'new'}
    grid.insert(1, new_row)
    assert len(grid) == 4
    assert grid[0] is rows[0]
    assert grid[1] is new_row
    assert grid[2] is rows[1]
    assert grid[3] is rows[2]


def test_grid_extend():
    grid = Grid(columns=['id'])
    grid.reindex()
    rows = [
        {'id': Ref('id1')},
        {'id': Ref('id2')},
        {'id': Ref('id3')}
    ]
    grid.extend(rows)
    assert len(grid) == 3
    assert Ref('id1') in grid._index
    assert Ref('id2') in grid._index


def test_grid_copy():
    grid = Grid(columns=['test'])
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ]
    grid.extend(rows)
    grid_2 = grid.copy()
    assert len(grid_2) == 3
    del grid[1]
    assert len(grid) == 2
    assert len(grid_2) == 3


def test_grid_str():
    grid = Grid(version=VER_3_0)
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ]
    grid.column['test'] = {}
    grid.extend(rows)
    assert repr(grid) == 'Grid\n' + \
           '\tVersion: 3.0\n' + \
           '\tColumns:\n' + \
           '\t\ttest\n' + \
           '\t---- Row    0:\n' + \
           '\ttest=1\n' + \
           '\t---- Row    1:\n' + \
           '\ttest=2\n' + \
           '\t---- Row    2:\n' + \
           '\ttest=3\n'


def test_grid_equal():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    assert ref == copy.deepcopy(ref)


def test_grid_equal_with_none():
    ref = Grid()
    ref.column['test', 'none'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    other = copy.deepcopy(ref)
    other[0]['none'] = None
    assert ref == other


def test_grid_equal_with_other_order():
    left = Grid()
    left.column['test'] = {}
    left.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    right = Grid()
    right.column['test'] = {}
    right.extend([
        {'test': 2},
        {'test': 1},
        {'test': 3}
    ])
    assert left == copy.deepcopy(right)


def test_grid_equal_with_complex_datas():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': datetime.datetime(2010, 11, 28, 7, 23, 2, 600000)},
        {'test': Quantity(500, 'kg')},
        {'test': Coordinate(100, 100)},
        {'test': 1.0},
    ])
    similar = Grid()
    similar.column['test'] = {}
    similar.extend([
        {'test': datetime.datetime(2010, 11, 28, 7, 23, 2, 500000)},
        {'test': Quantity(500.000001, 'kg')},
        {'test': Coordinate(100.000001, 100.000001)},
        {'test': 1.000001},
    ])

    assert ref == similar


def test_grid_equal_with_complex_datas_and_ids():
    ref = Grid()
    ref.column['id'] = {}
    ref.column['test'] = {}
    ref.extend([
        {'id': Ref('id1'), 'test': datetime.datetime(2010, 11, 28, 7, 23, 2, 600000)},
        {'id': Ref('id2'), 'test': Quantity(500, 'kg')},
        {'id': Ref('id3'), 'test': Coordinate(100, 100)},
        {'id': Ref('id4'), 'test': 1.0},
    ])
    similar = Grid()
    similar.column['id'] = {}
    similar.column['test'] = {}
    similar.extend([
        {'id': Ref('id1'), 'test': datetime.datetime(2010, 11, 28, 7, 23, 2, 500000)},
        {'id': Ref('id2'), 'test': Quantity(500.000001, 'kg')},
        {'id': Ref('id3'), 'test': Coordinate(100.000001, 100.000001)},
        {'id': Ref('id4'), 'test': 1.000001},
    ])

    assert ref == similar


def test_grid_not_equal_metadata():
    ref = Grid(metadata={"x": {}})
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff.metadata.append('add')
    assert ref != diff

    diff = copy.deepcopy(ref)
    diff.metadata["x"] = 1
    assert ref != diff


def test_grid_not_equal_col_with_new_metadata():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff: Grid = copy.deepcopy(ref)
    diff.column.add_item(key='test', value='add')  # type: ignore
    assert ref != diff


def test_grid_not_equal__with_new_col():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff.column["added"] = {}
    assert ref != diff


def test_grid_not_equal_col_with_change_col_name():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff: Grid = copy.deepcopy(ref)
    diff.column.pop('test')
    diff.column.add_item(key='new', value='add')  # type: ignore
    assert ref != diff


def test_grid_not_equal_col_with_updated_metadata():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff.column['test']['test'] = None
    assert ref != diff


def test_grid_not_equal_with_updated_value():
    ref = Grid()
    ref.column['test'] = {"a": 1}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff.column['test'] = {"a": ""}
    assert ref != diff


def test_grid_new_row():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff.append({'test': 4})
    assert ref != diff


def test_grid_not_equal_row():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff[0] = {'test': 4}
    assert ref != diff


def test_grid_index():
    grid = Grid()
    grid.column['id'] = {}
    grid.column['val'] = {}
    grid.insert(0, {'id': Ref('idx1')})
    assert Ref('idx1') in grid._index
    assert grid[Ref('idx1')]
    assert grid.get(Ref('idx1'))
    grid.insert(1, {'id': Ref('idx2')})
    assert Ref('idx1') in grid._index
    assert Ref('idx2') in grid._index
    assert grid.get(Ref('idx2'))
    grid[0] = {'id': Ref('idx3')}
    assert Ref('idx1') not in grid._index
    assert Ref('idx3') in grid._index
    assert grid.get(Ref('idx3'))
    del grid[1]
    assert Ref('idx2') not in grid._index
    grid.extend([
        {'id': Ref('idx5')},
        {'id': Ref('idx6')},
    ])
    assert Ref('idx5') in grid._index
    assert Ref('idx6') in grid._index
    grid[0]['id'] = Ref('idx4')
    grid.reindex()
    assert Ref('idx4') in grid._index
    assert grid.get(Ref('idx4'))


def test_slice():
    grid = Grid(columns=['id', 'site'])
    grid.append({'id': Ref('id1'), })
    grid.append({'id': Ref('id2')})
    grid.append({'id': Ref('id3')})

    result = grid[0:2]
    assert isinstance(result, Grid)
    assert len(result) == 2
    assert result[Ref('id1')]  # pylint: disable=invalid-sequence-index
    assert result[Ref('id2')]  # pylint: disable=invalid-sequence-index


def test_grid_contain():
    grid = Grid(columns=['id', 'site'])
    grid.append({'id': Ref('id1'), })
    grid.append({'id': Ref('id2')})
    grid.append({'id': Ref('id3')})

    assert Ref('id1') in grid
    assert Ref('id2') in grid


def test_grid_keys():
    grid = Grid(columns=['id', 'site'])
    grid.append({'id': Ref('id1'), })
    grid.append({'id': Ref('id2')})
    grid.append({'id': Ref('id3')})

    assert sorted(list(grid.keys())) == sorted([Ref('id1'), Ref('id2'), Ref('id3')])


def test_grid_sub():
    left = Grid(columns=["id", "a", "b"])
    left.append({"id": Ref("my_id"), "a": 1})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("my_id"), "a": 3, "b": 4})

    diff = right - left
    assert isinstance(diff, Grid)
    assert len(diff) == 1

    diff = left - right
    assert isinstance(diff, Grid)
    assert len(diff) == 1


def test_grid_add():
    left = Grid(columns=["id", "a", "b"])
    left.append({"id": Ref("my_id"), "a": 1, "b": 2})
    right = Grid(columns={"id": {}, "a": {}, "b": {}})
    right.append({"id": Ref("my_id"), "a": 3, "c": 4})

    add_grid = left + right
    assert isinstance(add_grid, Grid)
    assert len(add_grid) == 1


def test_pack_columns_with_unused_columns():
    grid = Grid(columns=["id", "a", "b"])
    grid.append({"id": Ref("myid"), "a": 1})
    grid.pack_columns()
    assert set(grid.column.keys()) == {"id", "a"}


def test_pack_columns_with_all_columns():
    grid = Grid(columns=["id", "a", "b"])
    grid.append({"id": Ref("myid"), "a": 1, "b": 2})
    grid.pack_columns()
    assert set(grid.column.keys()) == {"id", "a", "b"}


def test_extends_columns():
    grid = Grid(columns=["id", "a"])
    grid.append({"id": Ref("myid"), "a": 1, "b": 2})
    grid.extends_columns()
    assert "b" in grid.column


def test_mode_to_suffix():
    assert mode_to_suffix(suffix_to_mode(".csv")) == ".csv"
    assert mode_to_suffix(suffix_to_mode(".zinc")) == ".zinc"
    assert mode_to_suffix(suffix_to_mode(".json")) == ".json"
    assert mode_to_suffix(suffix_to_mode(".hayson.json")) == ".hayson.json"


def test_grid_update_slide():
    grid = Grid(columns=["id", "a"])
    grid.append({"id": Ref("myid1")})
    grid.append({"id": Ref("myid2")})
    grid.append({"id": Ref("myid3")})
    grid.append({"id": Ref("myid4")})
    grid[0:1] = [{"id": Ref("myid5")}]
    assert grid[0]['id'] == Ref("myid5")
    grid[1:3] = [{"id": Ref("myid6")}, {"id": Ref("myid7")}]
    assert grid[0]['id'] == Ref("myid5")
    assert grid[1]['id'] == Ref("myid6")
    assert grid[2]['id'] == Ref("myid7")
    assert grid[3]['id'] == Ref("myid4")


def test_select_grid():
    grid = Grid(columns=["id", "a", "b"])
    grid.append({"id": Ref("myid1"), "a": 1, "b": 2})
    grid.append({"id": Ref("myid2"), "a": 1, "b": 2})
    assert grid.select("id,a").column == {"id": {}, 'a': {}}
    assert grid.select("id,b").column == {"id": {}, 'b': {}}
    assert grid.select("!a").column == {"id": {}, 'b': {}}
    assert grid.select("!id,!b").column == {'a': {}}


def test_purge_grid():
    grid = Grid(columns=["id", "a", "b"])
    grid.append({"id": Ref("myid1"), "a": 1, "b": 2, "c": 3})
    grid.append({"id": Ref("myid2"), "a": 1, "b": 2, "d": 4})
    assert grid.purge()[0] == {"id": Ref("myid1"), "a": 1, "b": 2}
    assert grid.purge()[1] == {"id": Ref("myid2"), "a": 1, "b": 2}
