# -*- coding: utf-8 -*-
# Grid handling tests
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import copy
import datetime

from hszinc import Grid, Version, VER_3_0, Quantity, Coordinate
from hszinc.sortabledict import SortableDict


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
    g = Grid(columns=col_list)
    assert list(g.column.keys()) == ['col1', 'col2']
    for col, meta in col_list:
        assert list(g.column[col].items()) == meta


def test_grid_given_column_dict():
    cols = SortableDict([('col1', [('c1m1', None), ('c1m2', None)]),
                         ('col2', [('c2m1', None), ('c2m2', None)])])
    g = Grid(columns=cols)
    assert list(g.column.keys()) == ['col1', 'col2']
    for col, meta in cols.items():
        assert list(g.column[col].items()) == meta


def test_grid_given_column_meta_dict():
    cols = SortableDict([('col1', SortableDict([('c1m1', None), ('c1m2', None)])),
                         ('col2', SortableDict([('c2m1', None), ('c2m2', None)]))])
    g = Grid(columns=cols)
    assert list(g.column.keys()) == ['col1', 'col2']
    for col, meta in cols.items():
        assert list(g.column[col].items()) == list(meta.items())


def test_grid_getitem():
    g = Grid()
    g.column['test'] = {}

    row = {'test': 'This is a test'}
    g.append(row)
    assert g[0] is row


def test_grid_setitem():
    g = Grid()
    g.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = {'test': 'This is another test'}
    g.append(row_1)
    g[0] = row_2
    assert g[0] is row_2


def test_grid_append_notdict():
    g = Grid()
    g.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = 'This is not a dict'
    g.append(row_1)
    try:
        g.append(row_2)
        assert False
    except TypeError as e:
        assert str(e) == 'value must be a dict'
        assert len(g) == 1


def test_grid_append_v2_list_fail():
    g = Grid(version='2.0')
    g.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = {'test': ['This should fail']}
    g.append(row_1)
    try:
        g.append(row_2)
        assert False, 'Appended invalid data type'
    except ValueError as e:
        assert str(e) == 'Data type requires version 3.0'


def test_grid_append_nover_list():
    g = Grid()
    assert g.version == Version('2.0')
    g.column['test'] = {}

    row_1 = {'test': 'This is a test'}
    row_2 = {'test': ['This should fail']}
    g.append(row_1)
    assert g.version == Version('2.0')
    g.append(row_2)
    assert g.version == Version('3.0')


def test_grid_setitem_notdict():
    g = Grid()
    g.column['test'] = {}

    row = {'test': 'This is a test'}
    g.append(row)

    try:
        g[0] = 'This is not a dict'
        assert False, 'Accepted a string'
    except TypeError:
        pass
    assert len(g) == 1
    assert g[0]['test'] == 'This is a test'


def test_grid_del():
    g = Grid()
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ]
    g.column['test'] = {}
    g.extend(rows)
    assert len(g) == 3
    del g[1]
    assert len(g) == 2
    assert g[0] is rows[0]
    assert g[1] is rows[2]


def test_grid_insert():
    g = Grid()
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ]
    g.column['test'] = {}
    g.extend(rows)
    assert len(g) == 3
    new_row = {'test': 'new'}
    g.insert(1, new_row)
    assert len(g) == 4
    assert g[0] is rows[0]
    assert g[1] is new_row
    assert g[2] is rows[1]
    assert g[3] is rows[2]


def test_grid_str():
    g = Grid(version=VER_3_0)
    rows = [
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ]
    g.column['test'] = {}
    g.extend(rows)
    assert repr(g) == '<Grid>\n' \
                      '\tVersion: 3.0\n' \
                      '\tColumns:\n' \
                      '\t\ttest\n' \
                      '\tRow    0:\n' \
                      '\ttest=1\n' \
                      '\tRow    1:\n' \
                      '\ttest=2\n' \
                      '\tRow    2:\n' \
                      '\ttest=3\n' \
                      '</Grid>'


def test_grid_equal():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    assert ref == copy.deepcopy(ref)


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
    diff = copy.deepcopy(ref)
    diff.column.add_item('test', 'add')
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


def test_grid_not_equal_col_with_updated_metadata():
    ref = Grid()
    ref.column['test'] = {}
    ref.extend([
        {'test': 1},
        {'test': 2},
        {'test': 3}
    ])
    diff = copy.deepcopy(ref)
    diff.column.pop('test')
    diff.column.add_item('new', 'add')
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
    grid.insert(0, {'id': 'idx1'})
    assert 'idx1' in grid._index
    assert grid['idx1']
    assert grid.get('idx1')
    grid.insert(1, {'id': 'idx2'})
    assert 'idx1' in grid._index
    assert 'idx2' in grid._index
    assert grid.get('idx2')
    grid[0] = {'id': 'idx3'}
    assert not 'idx1' in grid._index
    assert 'idx3' in grid._index
    assert grid.get('idx3')
    del grid[1]
    assert not 'idx2' in grid._index
    grid.extend([
        {'id': 'idx5'},
        {'id': 'idx6'},
    ])
    assert 'idx5' in grid._index
    assert 'idx6' in grid._index
    grid[0]['id'] = 'idx4'
    grid.reindex()
    assert 'idx4' in grid._index
    assert grid.get('idx4')


def test_slice():
    grid = Grid(columns={'id': {}, 'site': {}})
    grid.append({'id': 'id1', })
    grid.append({'id': 'id2'})
    grid.append({'id': 'id3'})

    result = grid[0:2]
    assert len(result) == 2
    assert result['id1']
    assert result['id2']
