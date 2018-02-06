# -*- coding: utf-8 -*-
# Grid handling tests
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

from hszinc import Grid, MARKER
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
    assert list(g.column.keys()) == ['col1','col2']
    for col, meta in col_list:
        assert list(g.column[col].items()) == meta

def test_grid_given_column_dict():
    cols = SortableDict([('col1', [('c1m1', None), ('c1m2', None)]),
                        ('col2', [('c2m1', None), ('c2m2', None)])])
    g = Grid(columns=cols)
    assert list(g.column.keys()) == ['col1','col2']
    for col, meta in cols.items():
        assert list(g.column[col].items()) == meta

def test_grid_given_column_meta_dict():
    cols = SortableDict([('col1', SortableDict([('c1m1', None), ('c1m2', None)])),
                        ('col2', SortableDict([('c2m1', None), ('c2m2', None)]))])
    g = Grid(columns=cols)
    assert list(g.column.keys()) == ['col1','col2']
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

def test_grid_setitem_notdict():
    g = Grid()
    g.column['test'] = {}

    row = {'test': 'This is a test'}
    g.append(row)

    try:
        g.append('This is not a dict')
        assert False, 'Accepted a string'
    except TypeError:
        pass
    assert len(g) == 1

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

