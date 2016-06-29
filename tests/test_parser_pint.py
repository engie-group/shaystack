# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import hszinc
import datetime
import math
import pytz
import json

# These are examples taken from http://project-haystack.org/doc/Zinc

hszinc.use_pint()

SIMPLE_EXAMPLE='''ver:"2.0"
firstName,bday
"Jack",1973-07-23
"Jill",1975-11-15
'''

SIMPLE_EXAMPLE_JSON={
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'firstName'},
            {'name':'bday'},
        ],
        'rows': [
            {'firstName': 's:Jack', 'bday':'d:1973-07-23'},
            {'firstName': 's:Jill', 'bday':'d:1975-11-15'},
        ],
}

def test_simple():
    grid_list = hszinc.parse(SIMPLE_EXAMPLE)
    assert len(grid_list) == 1
    grid = grid_list[0]
    check_simple(grid)

def test_simple_json_str():
    grid = hszinc.parse(json.dumps(SIMPLE_EXAMPLE_JSON),
            mode=hszinc.MODE_JSON)
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

METADATA_EXAMPLE_JSON={
        'meta': {'ver':'2.0', 'database':'s:test',
                'dis':'s:Site Energy Summary'},
        'cols': [
            {'name':'siteName', 'dis':'s:Sites'},
            {'name':'val', 'dis':'s:Value', 'unit':'s:kW'},
        ],
        'rows': [
            {'siteName': 's:Site 1', 'val': 'n:356.214000 kW'},
            {'siteName': 's:Site 2', 'val': 'n:463.028000 kW'},
        ],
}

def test_metadata():
    grid_list = hszinc.parse(METADATA_EXAMPLE)
    assert len(grid_list) == 1
    grid = grid_list[0]
    check_metadata(grid)

def test_metadata_json():
    grid = hszinc.parse(METADATA_EXAMPLE_JSON, mode=hszinc.MODE_JSON)
    check_metadata(grid, force_metadata_order=False)

def check_metadata(grid,force_metadata_order=True):
    assert len(grid.metadata) == 2
    if force_metadata_order:
        assert list(grid.metadata.keys()) == ['database', 'dis']
    else:
        assert set(grid.metadata.keys()) == set(['database', 'dis'])

    assert grid.metadata['database'] == 'test'
    assert grid.metadata['dis'] == 'Site Energy Summary'

    assert list(grid.column.keys()) == ['siteName', 'val']
    col = grid.column['siteName']
    assert list(col.keys()) == ['dis']
    assert col['dis'] == 'Sites'

    col = grid.column['val']
    if force_metadata_order:
        assert list(col.keys()) == ['dis', 'unit']
    else:
        assert set(col.keys()) == set(['dis', 'unit'])
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
NULL_EXAMPLE_JSON={
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'str'},
            {'name':'null'},
        ],
        'rows': [
            {'str': 'Implicit', 'null':None},   # There's no "implicit" mode
            {'str': 'Explicit', 'null':None},
        ],
}


def check_null(grid):
    assert len(grid) == 2
    assert grid[0]['null'] is None
    assert grid[1]['null'] is None

def test_null():
    grid_list = hszinc.parse(NULL_EXAMPLE)
    assert len(grid_list) == 1
    check_null(grid_list[0])

def test_null_json():
    grid = hszinc.parse(NULL_EXAMPLE_JSON, mode=hszinc.MODE_JSON)
    check_null(grid)

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

def test_marker_in_row_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'str'},
            {'name':'marker'},
        ],
        'rows': [
            {'str': 'No Marker',    'marker':None},
            {'str': 'Marker',       'marker':'m:'},
        ],
    }, mode=hszinc.MODE_JSON)
    assert grid[0]['marker'] is None
    assert grid[1]['marker'] is hszinc.MARKER

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

def test_bool_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'str'},
            {'name':'bool'},
        ],
        'rows': [
            {'str': 'True', 'bool':True},
            {'str': 'False','bool':False},
        ],
    }, mode=hszinc.MODE_JSON)
    assert grid[0]['bool'] == True
    assert grid[1]['bool'] == False

def test_number():
    grid_list = hszinc.parse(u'''ver:"2.0"
str,number
"Integer",1
"Negative Integer",-34
"With Separators",10_000
"Scientific",5.4e-45
"Units mass",9.23kg
"Units time",4min
"Units temperature",74.2°F
"Positive Infinity",INF
"Negative Infinity",-INF
"Not a Number",NaN
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    check_number(grid)

def check_number(grid):
    assert len(grid) == 10
    row = grid.pop(0)
    assert row['number'] == 1.0
    row = grid.pop(0)
    assert row['number'] == -34.0
    row = grid.pop(0)
    assert row['number'] == 10000.0
    row = grid.pop(0)
    assert row['number'] == 5.4e-45
    row = grid.pop(0)
    assert row['number'] == hszinc.Quantity(9.23, 'kg')
    row = grid.pop(0)
    assert row['number'] == hszinc.Quantity(4.0, 'min')
    row = grid.pop(0)
    assert row['number'] == hszinc.Quantity(74.2, u'°F')
    row = grid.pop(0)
    assert math.isinf(row['number'])
    assert row['number'] > 0
    row = grid.pop(0)
    assert math.isinf(row['number'])
    assert row['number'] < 0
    row = grid.pop(0)
    assert math.isnan(row['number'])

def test_number_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'str'},
            {'name':'number'},
        ],
        'rows': [
            {'str': "Integer",              'number': u'n:1'},
            {'str': "Negative Integer",     'number': u'n:-34'},
            {'str': "With Separators",      'number': u'n:10000'},
            {'str': "Scientific",           'number': u'n:5.4e-45'},
            {'str': "Units mass",           'number': u'n:9.23 kg'},
            {'str': "Units time",           'number': u'n:4 min'},
            {'str': "Units temperature",    'number': u'n:74.2 °F'},
            {'str': "Positive Infinity",    'number': u'n:INF'},
            {'str': "Negative Infinity",    'number': u'n:-INF'},
            {'str': "Not a Number",         'number': u'n:NaN'},
        ],
    }, mode=hszinc.MODE_JSON)
    check_number(grid)

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

def test_string_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'str'},
            {'name':'strExample'},
        ],
        'rows': [
            {'str': "Empty",            'strExample': ''},
            {'str': "Implicit",         'strExample': 'a string'},
            {'str': "Literal",          'strExample': 's:an explicit string'},
            {'str': "With colons",      'strExample': 's:string:with:colons'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 4
    assert grid.pop(0)['strExample'] == ''
    assert grid.pop(0)['strExample'] == 'a string'
    assert grid.pop(0)['strExample'] == 'an explicit string'
    assert grid.pop(0)['strExample'] == 'string:with:colons'

def test_uri():
    grid_list = hszinc.parse('''ver:"2.0"
uri
`http://www.vrt.com.au`
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert grid_list[0][0]['uri'] == hszinc.Uri('http://www.vrt.com.au')

def test_uri_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'uri'},
        ],
        'rows': [
            {'uri': 'u:http://www.vrt.com.au'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 1
    assert grid[0]['uri'] == hszinc.Uri('http://www.vrt.com.au')

def test_ref():
    grid_list = hszinc.parse('''ver:"2.0"
str,ref
"Basic",@a-basic-ref
"With value",@reference "With value"
''')

    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 2
    assert grid[0]['ref'] == hszinc.Ref('a-basic-ref')
    assert grid[1]['ref'] == hszinc.Ref('reference', 'With value')

def test_ref_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'str'},
            {'name':'ref'},
        ],
        'rows': [
            {'str': 'Basic',        'ref': 'r:a-basic-ref'},
            {'str': 'With value',   'ref': 'r:reference With value'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 2
    assert grid[0]['ref'] == hszinc.Ref('a-basic-ref')
    assert grid[1]['ref'] == hszinc.Ref('reference', 'With value')

def test_date():
    grid_list = hszinc.parse('''ver:"2.0"
date
2010-03-13
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert isinstance(grid_list[0][0]['date'], datetime.date)
    assert grid_list[0][0]['date'] == datetime.date(2010,3,13)

def test_date_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'date'},
        ],
        'rows': [
            {'date': 'd:2010-03-13'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 1
    assert isinstance(grid[0]['date'], datetime.date)
    assert grid[0]['date'] == datetime.date(2010,3,13)

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

def test_time_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'time'},
        ],
        'rows': [
            {'time': 'h:08:12'},
            {'time': 'h:08:12:05'},
            {'time': 'h:08:12:05.5'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 3
    row = grid.pop(0)
    assert isinstance(row['time'], datetime.time)
    assert row['time'] == datetime.time(8,12)
    row = grid.pop(0)
    assert isinstance(row['time'], datetime.time)
    assert row['time'] == datetime.time(8,12,5)
    row = grid.pop(0)
    assert isinstance(row['time'], datetime.time)
    assert row['time'] == datetime.time(8,12,5,500000)

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
    check_datetime(grid_list.pop(0))

def check_datetime(grid):
    assert len(grid) == 6
    row = grid.pop(0)
    assert isinstance(row['datetime'], datetime.datetime)
    assert row['datetime'] == \
            pytz.timezone('America/Los_Angeles').localize(\
            datetime.datetime(2010,11,28,7,23,2,500000))
    row = grid.pop(0)
    assert row['datetime'] == \
            pytz.timezone('Asia/Taipei').localize(\
            datetime.datetime(2010,11,28,23,19,29,500000))
    row = grid.pop(0)
    assert row['datetime'] == \
            pytz.timezone('Etc/GMT-3').localize(\
            datetime.datetime(2010,11,28,18,21,58,0))
    row = grid.pop(0)
    assert row['datetime'] == \
            pytz.timezone('Etc/GMT+3').localize(\
            datetime.datetime(2010,11,28,12,22,27,0))
    row = grid.pop(0)
    assert row['datetime'] == \
            pytz.timezone('UTC').localize(\
            datetime.datetime(2010,1,8,5,0,0,0))
    row = grid.pop(0)
    assert row['datetime'] == \
            pytz.timezone('UTC').localize(\
            datetime.datetime(2010,1,8,5,0,0,0))

def test_datetime_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'datetime'},
        ],
        'rows': [
            {'datetime': 't:2010-11-28T07:23:02.500-08:00 Los_Angeles'},
            {'datetime': 't:2010-11-28T23:19:29.500+08:00 Taipei'},
            {'datetime': 't:2010-11-28T18:21:58+03:00 GMT-3'},
            {'datetime': 't:2010-11-28T12:22:27-03:00 GMT+3'},
            {'datetime': 't:2010-01-08T05:00:00Z UTC'},
            {'datetime': 't:2010-01-08T05:00:00Z'},
        ],
    }, mode=hszinc.MODE_JSON)
    check_datetime(grid)

def test_bin():
    grid_list = hszinc.parse('''ver:"2.0"
bin
Bin(text/plain)
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert grid_list[0][0]['bin'] == hszinc.Bin('text/plain')

def test_bin_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'bin'},
        ],
        'rows': [
            {'bin': 'b:text/plain'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 1
    assert grid[0]['bin'] == hszinc.Bin('text/plain')

def test_coord():
    grid_list = hszinc.parse('''ver:"2.0"
coord
C(37.55,-77.45)
''')

    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert grid_list[0][0]['coord'] == hszinc.Coordinate(37.55,-77.45)

def test_coord_json():
    grid = hszinc.parse({
        'meta': {'ver':'2.0'},
        'cols': [
            {'name':'coord'},
        ],
        'rows': [
            {'coord': 'c:37.55,-77.45'},
        ],
    }, mode=hszinc.MODE_JSON)

    assert len(grid) == 1
    assert grid[0]['coord'] == hszinc.Coordinate(37.55,-77.45)

def test_multi_grid():
    # Multiple grids are separated by newlines.
    grid_list = hszinc.parse('\n'.join([
        SIMPLE_EXAMPLE, METADATA_EXAMPLE, NULL_EXAMPLE]))
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1])
    check_null(grid_list[2])

def test_multi_grid_json():
    # Multiple grids are separated by newlines.
    grid_list = hszinc.parse([SIMPLE_EXAMPLE_JSON,
        METADATA_EXAMPLE_JSON, NULL_EXAMPLE_JSON], mode=hszinc.MODE_JSON)
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1], force_metadata_order=False)
    check_null(grid_list[2])

def test_multi_grid_json_str():
    # Multiple grids are separated by newlines.
    grid_list = hszinc.parse(list(map(json.dumps, [SIMPLE_EXAMPLE_JSON,
        METADATA_EXAMPLE_JSON, NULL_EXAMPLE_JSON])), mode=hszinc.MODE_JSON)
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1], force_metadata_order=False)
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

def test_nodehaystack_01():
    grid_list = hszinc.parse('''ver:"2.0"
fooBar33
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 0
    assert len(grid_list[0].metadata) == 0
    assert list(grid_list[0].column.keys()) == ['fooBar33']

def test_nodehaystack_02():
    grid_list = hszinc.parse('''ver:"2.0" tag foo:"bar"
xyz
"val"
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert list(grid_list[0].metadata.keys()) == ['tag', 'foo']
    assert grid_list[0].metadata['tag'] is hszinc.MARKER
    assert grid_list[0].metadata['foo'] == 'bar'
    assert list(grid_list[0].column.keys()) == ['xyz']
    assert grid_list[0][0]['xyz'] == 'val'

def test_nodehaystack_03():
    grid_list = hszinc.parse('''ver:"2.0"
val
N
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 1
    assert len(grid_list[0].metadata) == 0
    assert list(grid_list[0].column.keys()) == ['val']
    assert grid_list[0][0]['val'] is None

def test_nodehaystack_04():
    grid_list = hszinc.parse('''ver:"2.0"
a,b
1,2
3,4
''')
    assert len(grid_list) == 1
    assert len(grid_list[0]) == 2
    assert len(grid_list[0].metadata) == 0
    assert list(grid_list[0].column.keys()) == ['a','b']
    assert grid_list[0][0]['a'] == 1
    assert grid_list[0][0]['b'] == 2
    assert grid_list[0][1]['a'] == 3
    assert grid_list[0][1]['b'] == 4

def test_nodehaystack_05():
    grid_list = hszinc.parse('''ver:"2.0"
a,    b,      c,      d
T,    F,      N,   -99
2.3,  -5e-10, 2.4e20, 123e-10
"",   "a",   "\\" \\\\ \\t \\n \\r", "\\uabcd"
`path`, @12cbb082-0c02ae73, 4s, -2.5min
M,R,Bin(image/png),Bin(image/png)
2009-12-31, 23:59:01, 01:02:03.123, 2009-02-03T04:05:06Z
INF, -INF, "", NaN
C(12,-34),C(0.123,-.789),C(84.5,-77.45),C(-90,180)
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 8
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a','b','c','d']
    row = grid.pop(0)
    assert row['a'] == True
    assert row['b'] == False
    assert row['c'] is None
    assert row['d'] == -99.0
    row = grid.pop(0)
    assert row['a'] == 2.3
    assert row['b'] == -5e-10
    assert row['c'] == 2.4e20
    assert row['d'] == 123e-10
    row = grid.pop(0)
    assert row['a'] == ''
    assert row['b'] == 'a'
    assert row['c'] == '\" \\ \t \n \r'
    assert row['d'] == u'\uabcd'
    row = grid.pop(0)
    assert row['a'] == hszinc.Uri('path')
    assert row['b'] == hszinc.Ref('12cbb082-0c02ae73')
    assert row['c'] == hszinc.Quantity(4, 's')
    assert row['d'] == hszinc.Quantity(-2.5, 'min')
    row = grid.pop(0)
    assert row['a'] is hszinc.MARKER
    assert row['b'] is hszinc.REMOVE
    assert row['c'] == hszinc.Bin('image/png')
    assert row['d'] == hszinc.Bin('image/png')
    row = grid.pop(0)
    assert row['a'] == datetime.date(2009,12,31)
    assert row['b'] == datetime.time(23,59,1)
    assert row['c'] == datetime.time(1,2,3,123000)
    assert row['d'] == \
            datetime.datetime(2009,2,3,4,5,6,tzinfo=pytz.utc)
    row = grid.pop(0)
    assert math.isinf(row['a']) and (row['a'] > 0)
    assert math.isinf(row['b']) and (row['b'] < 0)
    assert row['c'] == ''
    assert math.isnan(row['d'])
    row = grid.pop(0)
    assert row['a'] == hszinc.Coordinate(12,-34)
    assert row['b'] == hszinc.Coordinate(.123,-.789)
    assert row['c'] == hszinc.Coordinate(84.5,-77.45)
    assert row['d'] == hszinc.Coordinate(-90,180)

def test_nodehaystack_06():
    grid_list = hszinc.parse('''ver:"2.0"
foo
`foo$20bar`
`foo\\`bar`
`file \\#2`
"$15"
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 4
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['foo']
    row = grid.pop(0)
    assert row['foo'] == hszinc.Uri('foo$20bar')
    row = grid.pop(0)
    assert row['foo'] == hszinc.Uri('foo`bar')
    row = grid.pop(0)
    assert row['foo'] == hszinc.Uri('file \\#2')
    row = grid.pop(0)
    assert row['foo'] == '$15'


def test_nodehaystack_07():
    grid_list = hszinc.parse(u'''ver:"2.0"
a, b
-3.1kg,4kg
5%,3.2%
5kWh/ft\u00b2,-15kWh/m\u00b2
123e+12kJ/kg_dry,74\u0394\u00b0F
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 4
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a','b']
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(-3.1,'kg')
    assert row['b'] == hszinc.Quantity(4,'kg')
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(5,'%')
    assert row['b'] == hszinc.Quantity(3.2,'%')
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(5,u'kWh/ft\u00b2')
    assert row['b'] == hszinc.Quantity(-15,u'kWh/m\u00b2')
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(123e12,'kJ/kg_dry')
    assert row['b'] == hszinc.Quantity(74,u'\u0394\u00b0F')

def test_nodehaystack_08():
    grid_list = hszinc.parse('''ver:"2.0"
a,b
2010-03-01T23:55:00.013-05:00 GMT+5,2010-03-01T23:55:00.013+10:00 GMT-10
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a','b']
    row = grid.pop(0)
    assert row['a'] == hszinc.zoneinfo.timezone('GMT+5').localize(\
            datetime.datetime(2010,3,1,23,55,0,13000))
    assert row['b'] == hszinc.zoneinfo.timezone('GMT-10').localize(\
            datetime.datetime(2010,3,1,23,55,0,13000))

def test_nodehaystack_09():
    grid_list = hszinc.parse(u'''ver:"2.0" a: 2009-02-03T04:05:06Z foo b: 2010-02-03T04:05:06Z UTC bar c: 2009-12-03T04:05:06Z London baz
a
3.814697265625E-6
2010-12-18T14:11:30.924Z
2010-12-18T14:11:30.925Z UTC
2010-12-18T14:11:30.925Z London
45$
33\u00a3
@12cbb08e-0c02ae73
7.15625E-4kWh/ft\u00b2
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 8
    assert list(grid.metadata.keys()) == ['a','foo','b','bar','c','baz']
    assert grid.metadata['a'] == pytz.utc.localize(\
            datetime.datetime(2009,2,3,4,5,6))
    assert grid.metadata['b'] == pytz.utc.localize(\
            datetime.datetime(2010,2,3,4,5,6))
    assert grid.metadata['c'] == pytz.timezone('Europe/London').localize(\
            datetime.datetime(2009,12,3,4,5,6))
    assert grid.metadata['foo'] is hszinc.MARKER
    assert grid.metadata['bar'] is hszinc.MARKER
    assert grid.metadata['baz'] is hszinc.MARKER
    assert list(grid.column.keys()) == ['a']
    assert grid.pop(0)['a'] == 3.814697265625E-6
    assert grid.pop(0)['a'] == pytz.utc.localize(\
            datetime.datetime(2010,12,18,14,11,30,924000))
    assert grid.pop(0)['a'] == pytz.utc.localize(\
            datetime.datetime(2010,12,18,14,11,30,925000))
    assert grid.pop(0)['a'] == pytz.timezone('Europe/London').localize(\
            datetime.datetime(2010,12,18,14,11,30,925000))
    assert grid.pop(0)['a'] == hszinc.Quantity(45,'$')
    assert grid.pop(0)['a'] == hszinc.Quantity(33,u'\u00a3')
    assert grid.pop(0)['a'] == hszinc.Ref('12cbb08e-0c02ae73')
    assert grid.pop(0)['a'] == hszinc.Quantity(7.15625E-4,u'kWh/ft\u00b2')

def test_nodehaystack_10():
    grid_list = hszinc.parse('''ver:"2.0" bg: Bin(image/jpeg) mark
file1 dis:"F1" icon: Bin(image/gif),file2 icon: Bin(image/jpg)
Bin(text/plain),N
4,Bin(image/png)
Bin(text/html; a=foo; bar="sep"),Bin(text/html; charset=utf8)
''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 3
    assert list(grid.metadata.keys()) == ['bg','mark']
    assert grid.metadata['bg'] == hszinc.Bin('image/jpeg')
    assert grid.metadata['mark'] is hszinc.MARKER
    assert list(grid.column.keys()) == ['file1','file2']
    assert list(grid.column['file1'].keys()) == ['dis','icon']
    assert grid.column['file1']['dis'] == 'F1'
    assert grid.column['file1']['icon'] == hszinc.Bin('image/gif')
    assert list(grid.column['file2'].keys()) == ['icon']
    assert grid.column['file2']['icon'] == hszinc.Bin('image/jpg')
    row = grid.pop(0)
    assert row['file1'] == hszinc.Bin('text/plain')
    assert row['file2'] is None
    row = grid.pop(0)
    assert row['file1'] == 4
    assert row['file2'] == hszinc.Bin('image/png')
    row = grid.pop(0)
    assert row['file1'] == hszinc.Bin('text/html; a=foo; bar="sep"')
    assert row['file2'] == hszinc.Bin('text/html; charset=utf8')

def test_nodehaystack_11():
    grid_list = hszinc.parse('''ver:"2.0"
a, b, c
, 1, 2
3, , 5
6, 7_000,
,,10
,,
14,,

''')
    assert len(grid_list) == 1
    grid = grid_list.pop(0)
    assert len(grid) == 6
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a','b','c']
    row = grid.pop(0)
    assert row['a'] is None
    assert row['b'] == 1
    assert row['c'] == 2
    row = grid.pop(0)
    assert row['a'] == 3
    assert row['b'] is None
    assert row['c'] == 5
    row = grid.pop(0)
    assert row['a'] == 6
    assert row['b'] == 7000
    assert row['c'] is None
    row = grid.pop(0)
    assert row['a'] is None
    assert row['b'] is None
    assert row['c'] == 10
    row = grid.pop(0)
    assert row['a'] is None
    assert row['b'] is None
    assert row['c'] is None
    row = grid.pop(0)
    assert row['a'] == 14
    assert row['b'] is None
    assert row['c'] is None