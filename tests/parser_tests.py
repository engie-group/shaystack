# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import hszinc
import datetime

# These are examples taken from http://project-haystack.org/doc/Zinc

SIMPLE_EXAMPLE='''ver:"2.0"
firstName,bday
"Jack",1973-07-23
"Jill",1975-11-15
'''

def test_simple():
    grid_list = hszinc.parse(SIMPLE_EXAMPLE)
    assert len(grid_list) == 1
    grid = grid_list[0]
    check_simple(grid)

def check_row_keys(row, grid):
    assert set(row.keys()) == set(grid.column.keys())

def check_simple(grid):
    assert len(grid.metadata) == 0
    assert grid.column.keys() == ['firstName', 'bday']
    # Neither column should have metadata
    assert all([len(c) == 0 for c in grid.column.values()])

    # First row:
    row = grid[0]
    check_row_keys(row, grid)
    assert row['firstName'] == 'Jack'
    assert row['bday'] == datetime.date(1973,7,23)

    # Second row:
    row = grid[1]
    check_row_keys(row, grid)
    assert row['firstName'] == 'Jill'
    assert row['bday'] == datetime.date(1975,11,15)

METADATA_EXAMPLE='''ver:"2.0" database:"test" dis:"Site Energy Summary"
siteName dis:"Sites", val dis:"Value" unit:"kW"
"Site 1", 356.214kW
"Site 2", 463.028kW'''

def test_metadata():
    grid_list = hszinc.parse(METADATA_EXAMPLE)
    assert len(grid_list) == 1
    grid = grid_list[0]
    check_metadata(grid)

def check_metadata(grid):
    assert len(grid.metadata) == 2
    assert grid.metadata.keys() == ['database', 'dis']
    assert grid.metadata['database'] == 'test'
    assert grid.metadata['dis'] == 'Site Energy Summary'

    assert grid.column.keys() == ['siteName', 'val']
    col = grid.column['siteName']
    assert col.keys() == ['dis']
    assert col['dis'] == 'Sites'

    col = grid.column['val']
    assert col.keys() == ['dis', 'unit']
    assert col['dis'] == 'Value'
    assert col['unit'] == 'kW'

    # First row:
    row = grid[0]
    check_row_keys(row, grid)
    assert row['siteName'] == 'Site 1'
    val = row['val']
    assert isinstance(val, hszinc.Quantity)
    assert val.value == 356.214
    assert val.unit == 'kW'

    # Second row:
    row = grid[1]
    check_row_keys(row, grid)
    assert row['siteName'] == 'Site 2'
    val = row['val']
    assert isinstance(val, hszinc.Quantity)
    assert val.value == 463.028
    assert val.unit == 'kW'
