# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import hszinc
import datetime
import math
import pytz

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
    assert list(grid.column.keys()) == ['firstName', 'bday']
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
"Site 2", 463.028kW
'''

def test_metadata():
    grid_list = hszinc.parse(METADATA_EXAMPLE)
    assert len(grid_list) == 1
    grid = grid_list[0]
    check_metadata(grid)

def check_metadata(grid):
    assert len(grid.metadata) == 2
    assert list(grid.metadata.keys()) == ['database', 'dis']
    assert grid.metadata['database'] == 'test'
    assert grid.metadata['dis'] == 'Site Energy Summary'

    assert list(grid.column.keys()) == ['siteName', 'val']
    col = grid.column['siteName']
    assert list(col.keys()) == ['dis']
    assert col['dis'] == 'Sites'

    col = grid.column['val']
    assert list(col.keys()) == ['dis', 'unit']
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

# Test examples used to test every data type defined in the Zinc standard.
#    Null: N
#    Marker: M
#    Bool: T or F (for true, false)
#    Number: 1, -34, 10_000, 5.4e-45, 9.23kg, 74.2°F, 4min, INF, -INF, NaN
#    Str: "hello" "foo\nbar\" (uses all standard escape chars as C like languages)
#    Uri: `http://project-haystack.com/`
#    Ref: @17eb0f3a-ad607713
#    Date: 2010-03-13 (YYYY-MM-DD)
#    Time: 08:12:05 (hh:mm:ss.FFF)
#    DateTime: 2010-03-11T23:55:00-05:00 New_York or 2009-11-09T15:39:00Z
#    Bin: Bin(text/plain)
#    Coord: C(37.55,-77.45)

NULL_EXAMPLE='''ver:"2.0"
str,null
"Implicit",
"Explict",N
'''

def check_null(grid):
    assert len(grid) == 2
    assert grid[0]['null'] is None
    assert grid[1]['null'] is None

def test_null():
    grid_list = hszinc.parse(NULL_EXAMPLE)
    assert len(grid_list) == 1
    check_null(grid_list[0])

def test_marker_in_row():
    grid_list = hszinc.parse('''ver:"2.0"
str,marker
"No Marker",
"Marker",M
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 2
    assert grid_list[0][0]['marker'] is None
    assert grid_list[0][1]['marker'] is hszinc.MARKER

def test_bool():
    grid_list = hszinc.parse('''ver:"2.0"
str,bool
"True",T
"False",F
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 2
    assert grid_list[0][0]['bool'] == True
    assert grid_list[0][1]['bool'] == False

def test_number():
    grid_list = hszinc.parse('''ver:"2.0"
str,number
"Integer",1
"Negative Integer",-34
"With Separators",10_000
"Scientific",5.4e-45
"Units mass",9.23kg
"Units time",4min
"Positive Infinity",INF
"Negative Infinity",-INF
"Not a Number",NaN
''')

    # TODO:
    # "Units temperature",74.2°F -- according to Haystack grammar, not allowed,
    # but they give it as an example anyway.
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 9
    assert grid_list[0][0]['number'] == 1.0
    assert grid_list[0][1]['number'] == -34.0
    assert grid_list[0][2]['number'] == 10000.0
    assert grid_list[0][3]['number'] == 5.4e-45
    assert isinstance(grid_list[0][4]['number'], hszinc.Quantity)
    assert grid_list[0][4]['number'].value == 9.23
    assert grid_list[0][4]['number'].unit == 'kg'
    assert isinstance(grid_list[0][5]['number'], hszinc.Quantity)
    assert grid_list[0][5]['number'].value == 4.0
    assert grid_list[0][5]['number'].unit == 'min'
    assert math.isinf(grid_list[0][6]['number'])
    assert grid_list[0][6]['number'] > 0
    assert math.isinf(grid_list[0][7]['number'])
    assert grid_list[0][7]['number'] < 0
    assert math.isnan(grid_list[0][8]['number'])

def test_string():
    grid_list = hszinc.parse('''ver:"2.0"
str,strExample
"Empty",""
"Basic","Simple string"
"Escaped","This\\tIs\\nA\\r\\"Test\\"\\\\"
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 3
    assert grid_list[0][0]['strExample'] == ''
    assert grid_list[0][1]['strExample'] == 'Simple string'
    assert grid_list[0][2]['strExample'] == 'This\tIs\nA\r"Test"\\'

def test_uri():
    grid_list = hszinc.parse('''ver:"2.0"
uri
`http://www.vrt.com.au`
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert isinstance(grid_list[0][0]['uri'], hszinc.Uri)
    assert grid_list[0][0]['uri'] == 'http://www.vrt.com.au'

def test_ref():
    grid_list = hszinc.parse('''ver:"2.0"
str,ref
"Basic",@a-basic-ref
"With value",@reference "With value"
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 2
    assert isinstance(grid_list[0][0]['ref'], hszinc.Ref)
    assert grid_list[0][0]['ref'].name == 'a-basic-ref'
    assert not grid_list[0][0]['ref'].has_value
    assert isinstance(grid_list[0][1]['ref'], hszinc.Ref)
    assert grid_list[0][1]['ref'].name == 'reference'
    assert grid_list[0][1]['ref'].has_value
    assert grid_list[0][1]['ref'].value == 'With value'

def test_date():
    grid_list = hszinc.parse('''ver:"2.0"
date
2010-03-13
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert isinstance(grid_list[0][0]['date'], datetime.date)
    assert grid_list[0][0]['date'] == datetime.date(2010,3,13)

def test_time():
    grid_list = hszinc.parse('''ver:"2.0"
time
08:12:05
08:12:05.5
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 2
    assert isinstance(grid_list[0][0]['time'], datetime.time)
    assert grid_list[0][0]['time'] == datetime.time(8,12,5)
    assert isinstance(grid_list[0][1]['time'], datetime.time)
    assert grid_list[0][1]['time'] == datetime.time(8,12,5,500000)

def test_datetime():
    grid_list = hszinc.parse('''ver:"2.0"
datetime
2010-11-28T07:23:02.500-08:00 Los_Angeles
2010-11-28T23:19:29.500+08:00 Taipei
2010-11-28T18:21:58+03:00 GMT-3
2010-11-28T12:22:27-03:00 GMT+3
2010-01-08T05:00:00Z UTC
2010-01-08T05:00:00Z
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 6
    assert isinstance(grid_list[0][0]['datetime'], datetime.datetime)
    assert grid_list[0][0]['datetime'] == \
            pytz.timezone('America/Los_Angeles').localize(\
            datetime.datetime(2010,11,28,7,23,2,500000))
    assert grid_list[0][1]['datetime'] == \
            pytz.timezone('Asia/Taipei').localize(\
            datetime.datetime(2010,11,28,23,19,29,500000))
    assert grid_list[0][2]['datetime'] == \
            pytz.timezone('Etc/GMT-3').localize(\
            datetime.datetime(2010,11,28,18,21,58,0))
    assert grid_list[0][3]['datetime'] == \
            pytz.timezone('Etc/GMT+3').localize(\
            datetime.datetime(2010,11,28,12,22,27,0))
    assert grid_list[0][4]['datetime'] == \
            pytz.timezone('UTC').localize(\
            datetime.datetime(2010,1,8,5,0,0,0))
    assert grid_list[0][5]['datetime'] == \
            pytz.timezone('UTC').localize(\
            datetime.datetime(2010,1,8,5,0,0,0))

def test_bin():
    grid_list = hszinc.parse('''ver:"2.0"
bin
Bin(text/plain)
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert isinstance(grid_list[0][0]['bin'], hszinc.Bin)
    assert grid_list[0][0]['bin'] == 'text/plain'

def test_coord():
    grid_list = hszinc.parse('''ver:"2.0"
coord
C(37.55,-77.45)
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert isinstance(grid_list[0][0]['coord'], hszinc.Coordinate)
    assert grid_list[0][0]['coord'].latitude == 37.55
    assert grid_list[0][0]['coord'].longitude == -77.45

def test_multi_grid():
    # Multiple grids are separated by newlines.
    grid_list = hszinc.parse('\n'.join([
        SIMPLE_EXAMPLE, METADATA_EXAMPLE, NULL_EXAMPLE]))
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1])
    check_null(grid_list[2])

def test_grid_meta():
    grid_list = hszinc.parse('''ver:"2.0" aString:"aValue" aNumber:3.14159 aNull:N aMarker:M anotherMarker aQuantity:123Hz aDate:2016-01-13 aTime:06:44:00 aTimestamp:2016-01-13T06:44:00+10:00 Brisbane aPlace:C(-27.4725,153.003)
empty
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 0
    meta = grid_list[0].metadata
    assert list(meta.keys()) == ['aString', 'aNumber', 'aNull',
            'aMarker', 'anotherMarker', 'aQuantity', 'aDate', 'aTime',
            'aTimestamp', 'aPlace']
    assert meta['aString'] == 'aValue'
    assert meta['aNumber'] == 3.14159
    assert meta['aNull'] is None
    assert meta['aMarker'] is hszinc.MARKER
    assert meta['anotherMarker'] is hszinc.MARKER
    assert isinstance(meta['aQuantity'], hszinc.Quantity)
    assert meta['aQuantity'].value == 123
    assert meta['aQuantity'].unit == 'Hz'
    assert isinstance(meta['aDate'], datetime.date)
    assert meta['aDate'] == datetime.date(2016,1,13)
    assert isinstance(meta['aTime'], datetime.time)
    assert meta['aTime'] == datetime.time(6,44)
    assert isinstance(meta['aTimestamp'], datetime.datetime)
    assert meta['aTimestamp'] == \
            pytz.timezone('Australia/Brisbane').localize(\
                datetime.datetime(2016,1,13,6,44))
    assert isinstance(meta['aPlace'], hszinc.Coordinate)
    assert meta['aPlace'].latitude == -27.4725
    assert meta['aPlace'].longitude == 153.003

def test_col_meta():
    grid_list = hszinc.parse('''ver:"2.0"
aColumn aString:"aValue" aNumber:3.14159 aNull:N aMarker:M anotherMarker aQuantity:123Hz aDate:2016-01-13 aTime:06:44:00 aTimestamp:2016-01-13T06:44:00+10:00 Brisbane aPlace:C(-27.4725,153.003)
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 0
    assert len(grid_list[0].metadata) == 0
    assert list(grid_list[0].column.keys()) == ['aColumn']
    meta = grid_list[0].column['aColumn']
    assert list(meta.keys()) == ['aString', 'aNumber', 'aNull',
            'aMarker', 'anotherMarker', 'aQuantity', 'aDate', 'aTime',
            'aTimestamp', 'aPlace']
    assert meta['aString'] == 'aValue'
    assert meta['aNumber'] == 3.14159
    assert meta['aNull'] is None
    assert meta['aMarker'] is hszinc.MARKER
    assert meta['anotherMarker'] is hszinc.MARKER
    assert isinstance(meta['aQuantity'], hszinc.Quantity)
    assert meta['aQuantity'].value == 123
    assert meta['aQuantity'].unit == 'Hz'
    assert isinstance(meta['aDate'], datetime.date)
    assert meta['aDate'] == datetime.date(2016,1,13)
    assert isinstance(meta['aTime'], datetime.time)
    assert meta['aTime'] == datetime.time(6,44)
    assert isinstance(meta['aTimestamp'], datetime.datetime)
    assert meta['aTimestamp'] == \
            pytz.timezone('Australia/Brisbane').localize(\
                datetime.datetime(2016,1,13,6,44))
    assert isinstance(meta['aPlace'], hszinc.Coordinate)
    assert meta['aPlace'].latitude == -27.4725
    assert meta['aPlace'].longitude == 153.003

def test_too_many_cells():
    grid_list = hszinc.parse('''ver:"2.0"
col1, col2, col3
"Val1", "Val2", "Val3", "Val4", "Val5"
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert len(grid_list[0].metadata) == 0
    assert list(grid_list[0].column.keys()) == ['col1','col2','col3']

    row = grid_list[0][0]
    assert set(row.keys()) == set(['col1','col2','col3'])
    assert row['col1'] == 'Val1'
    assert row['col2'] == 'Val2'
    assert row['col3'] == 'Val3'
