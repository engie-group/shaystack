# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from __future__ import unicode_literals

import datetime
import json
import math
import os
import warnings

import pytz
from nose.tools import assert_is

import hszinc
from hszinc import MARKER, Grid, MODE_JSON, XStr, dump_scalar, MODE_ZINC
from hszinc.zincparser import hs_row, _unescape, ZincParseException
from .pint_enable import _enable_pint

# These are examples taken from http://project-haystack.org/doc/Zinc

SIMPLE_EXAMPLE = '''ver:"2.0"
firstName,bday
"Jack",1973-07-23
"Jill",1975-11-15
'''

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

SIMPLE_EXAMPLE_JSON = {
    'meta': {'ver': '2.0'},
    'cols': [
        {'name': 'firstName'},
        {'name': 'bday'},
    ],
    'rows': [
        {'firstName': 's:Jack', 'bday': 'd:1973-07-23'},
        {'firstName': 's:Jill', 'bday': 'd:1975-11-15'},
    ],
}


def test_simple():
    yield _check_simple, False  # without pint
    yield _check_simple, True  # with pint


def _check_simple(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(SIMPLE_EXAMPLE, single=True)
    check_simple(grid)


def test_simple_encoded():
    yield _check_simple_encoded, False  # without pint
    yield _check_simple_encoded, True  # with pint


def _check_simple_encoded(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(SIMPLE_EXAMPLE.encode('us-ascii'),
                             charset='us-ascii', single=True)
    check_simple(grid)


def test_simple_json_str():
    yield _check_simple_json_str, False  # without pint
    yield _check_simple_json_str, True  # with pint


def _check_simple_json_str(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(json.dumps(SIMPLE_EXAMPLE_JSON),
                             mode=MODE_JSON,
                             single=True)
    check_simple(grid)


def test_wc1382_unicode_str():
    yield _check_wc1382_unicode_str, False  # without pint
    yield _check_wc1382_unicode_str, True  # with pint


def _check_wc1382_unicode_str(pint_en):
    _enable_pint(pint_en)
    # Don't use pint for this, we wish to see the actual quantity value.
    hszinc.use_pint(False)

    grid = hszinc.parse(
        open(os.path.join(THIS_DIR,
                          'data', 'wc1382-unicode-grid.txt'), 'rb').read(),
        mode=MODE_ZINC, single=True)

    assert len(grid) == 3

    # The values of all the 'temperature' points should have degree symbols.
    assert grid[0]['v1'].unit == u'\u00b0C'
    assert grid[1]['v6'].unit == u'\u00b0C'


def test_unsupported_old():
    yield _check_unsupported_old, False  # without pint
    yield _check_unsupported_old, True  # with pint


def _check_unsupported_old(pint_en):
    _enable_pint(pint_en)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        grid = hszinc.parse('''ver:"1.0"
comment
"Testing that we can handle an \\"old\\" version."
"We pretend it is compatible with v2.0"
''', mode=MODE_ZINC, single=True)
        assert grid._version == hszinc.Version('1.0')


def test_unsupported_newer():
    yield _check_unsupported_newer, False  # without pint
    yield _check_unsupported_newer, True  # with pint


def _check_unsupported_newer(pint_en):
    _enable_pint(pint_en)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        grid = hszinc.parse('''ver:"2.5"
comment
"Testing that we can handle a version between official versions."
["We pretend it is compatible with v3.0"]
''', mode=MODE_ZINC, single=True)
        assert grid._version == hszinc.Version('2.5')


def test_oddball_version():
    yield _check_oddball_version, False  # without pint
    yield _check_oddball_version, True  # with pint


def _check_oddball_version(pint_en):
    _enable_pint(pint_en)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        grid = hszinc.parse('''ver:"3"
comment
"Testing that we can handle a version expressed slightly differently to normal."
["We pretend it is compatible with v3.0"]
''', mode=MODE_ZINC, single=True)
        assert grid._version == hszinc.Version('3')

        # This should not have raised a warning
        assert len(w) == 0


def test_unsupported_bleedingedge():
    yield _check_unsupported_bleedingedge, False  # without pint
    yield _check_unsupported_bleedingedge, True  # with pint


def _check_unsupported_bleedingedge(pint_en):
    _enable_pint(pint_en)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        grid = hszinc.parse('''ver:"9999.9999"
comment
"Testing that we can handle a version that's newer than we support."
["We pretend it is compatible with v3.0"]
''', mode=MODE_ZINC, single=True)
        assert grid._version == hszinc.Version('9999.9999')


def test_malformed_grid():
    yield _check_malformed_grid, False  # without pint
    yield _check_malformed_grid, True  # with pint


def _check_malformed_grid(pint_en):
    _enable_pint(pint_en)
    try:
        hszinc.parse('''ver:2.0 comment:"This grid has no columns!"
''', single=True)
        assert False, 'Parsed a malformed grid.'
    except ValueError:
        pass


def test_malformed_version():
    yield _check_malformed_version, False  # without pint
    yield _check_malformed_version, True  # with pint


def _check_malformed_version(pint_en):
    _enable_pint(pint_en)
    try:
        hszinc.parse('''ver:TwoPointOh comment:"This grid has an invalid version!"
empty
''', single=True)
        assert False, 'Parsed a malformed version string.'
    except ValueError:
        pass


def check_row_keys(row, grid):
    assert set(row.keys()) == set(grid.column.keys())


def check_simple(grid):
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['firstName', 'bday']
    # Neither column should have metadata
    assert all([len(c) == 0 for c in grid.column.values()])

    assert len(grid) == 2

    # First row:
    row = grid[0]
    check_row_keys(row, grid)
    assert row['firstName'] == 'Jack'
    assert row['bday'] == datetime.date(1973, 7, 23)

    # Second row:
    row = grid[1]
    check_row_keys(row, grid)
    assert row['firstName'] == 'Jill'
    assert row['bday'] == datetime.date(1975, 11, 15)


METADATA_EXAMPLE = '''ver:"2.0" database:"test" dis:"Site Energy Summary"
siteName dis:"Sites", val dis:"Value" unit:"kW"
"Site 1", 356.214kW
"Site 2", 463.028kW
'''

METADATA_EXAMPLE_JSON = {
    'meta': {'ver': '2.0', 'database': 's:test',
             'dis': 's:Site Energy Summary'},
    'cols': [
        {'name': 'siteName', 'dis': 's:Sites'},
        {'name': 'val', 'dis': 's:Value', 'unit': 's:kW'},
    ],
    'rows': [
        {'siteName': 's:Site 1', 'val': 'n:356.214000 kW'},
        {'siteName': 's:Site 2', 'val': 'n:463.028000 kW'},
    ],
}


def test_metadata():
    yield _check_metadata, False  # without pint
    yield _check_metadata, True  # with pint


def _check_metadata(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(METADATA_EXAMPLE, single=True)
    check_metadata(grid)


def test_metadata_json():
    yield _check_metadata_json, False  # without pint
    yield _check_metadata_json, True  # with pint


def _check_metadata_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(METADATA_EXAMPLE_JSON, mode=MODE_JSON, single=True)
    check_metadata(grid, force_metadata_order=False)


def check_metadata(grid, force_metadata_order=True):
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
#    NA: NA
#    Marker: M
#    Remove: R
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

NULL_EXAMPLE = '''ver:"2.0"
str,null
"Implicit",
"Explict",N
'''
NULL_EXAMPLE_JSON = {
    'meta': {'ver': '2.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'null'},
    ],
    'rows': [
        {'str': 'Implicit', 'null': None},  # There's no "implicit" mode
        {'str': 'Explicit', 'null': None},
    ],
}


def check_null(grid):
    assert len(grid) == 2
    assert_is(grid[0]['null'], None)
    assert_is(grid[1]['null'], None)


def test_null():
    yield _check_null, False  # without pint
    yield _check_null, True  # with pint


def _check_null(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(NULL_EXAMPLE, single=True)
    check_null(grid)


def test_null_json():
    yield _check_null_json, False  # without pint
    yield _check_null_json, True  # with pint


def _check_null_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(NULL_EXAMPLE_JSON, mode=MODE_JSON, single=True)
    check_null(grid)


NA_EXAMPLE = '''ver:"3.0"
str,na
"NA value",NA
'''
NA_EXAMPLE_JSON = {
    'meta': {'ver': '3.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'na'},
    ],
    'rows': [
        {'str': 'NA value', 'na': 'z:'},
    ],
}


def check_na(grid):
    assert len(grid) == 1
    assert_is(grid[0]['na'], hszinc.NA)


def test_na():
    yield _check_na, False  # without pint
    yield _check_na, True  # with pint


def _check_na(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(NA_EXAMPLE, single=True)
    check_na(grid)


def test_na_json():
    yield _check_na_json, False  # without pint
    yield _check_na_json, True  # with pint


def _check_na_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(NA_EXAMPLE_JSON, mode=MODE_JSON, single=True)
    check_na(grid)


REMOVE_EXAMPLE = '''ver:"3.0"
str,remove
"v2 REMOVE value",R
"v3 REMOVE value",R
'''
REMOVE_EXAMPLE_JSON_V2 = {
    'meta': {'ver': '2.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'remove'},
    ],
    'rows': [
        {'str': 'v2 REMOVE value', 'remove': 'x:'},
        {'str': 'v3 REMOVE value', 'remove': '-:'},
    ],
}
REMOVE_EXAMPLE_JSON_V3 = {
    'meta': {'ver': '3.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'remove'},
    ],
    'rows': [
        {'str': 'v2 REMOVE value', 'remove': 'x:'},
        {'str': 'v3 REMOVE value', 'remove': '-:'},
    ],
}


def check_remove(grid):
    assert len(grid) == 2
    assert_is(grid[0]['remove'], hszinc.REMOVE)
    assert_is(grid[1]['remove'], hszinc.REMOVE)


def test_remove():
    yield _check_remove, False  # without pint
    yield _check_remove, True  # with pint


def _check_remove(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(REMOVE_EXAMPLE, single=True)
    check_remove(grid)


def test_remove_json_v2():
    yield _check_remove_json_v2, False  # without pint
    yield _check_remove_json_v2, True  # with pint


def test_remove_json_v3():
    yield _check_remove_json_v3, False  # without pint
    yield _check_remove_json_v3, True  # with pint


def _check_remove_json_v2(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(REMOVE_EXAMPLE_JSON_V2, mode=MODE_JSON, single=True)
    check_remove(grid)


def _check_remove_json_v3(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(REMOVE_EXAMPLE_JSON_V3, mode=MODE_JSON, single=True)
    check_remove(grid)


def test_marker_in_row():
    yield _check_marker_in_row, False  # without pint
    yield _check_marker_in_row, True  # with pint


def _check_marker_in_row(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
str,marker
"No Marker",
"Marker",M
''', single=True)
    assert len(grid) == 2
    assert_is(grid[0]['marker'], None)
    assert_is(grid[1]['marker'], hszinc.MARKER)


def test_marker_in_row_json():
    yield _check_marker_in_row_json, False  # without pint
    yield _check_marker_in_row_json, True  # with pint


def _check_marker_in_row_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'marker'},
        ],
        'rows': [
            {'str': 'No Marker', 'marker': None},
            {'str': 'Marker', 'marker': 'm:'},
        ],
    }, mode=MODE_JSON, single=True)
    assert grid[0]['marker'] is None
    assert grid[1]['marker'] is hszinc.MARKER


def test_bool():
    yield _check_bool, False  # without pint
    yield _check_bool, True  # with pint


def _check_bool(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
str,bool
"True",T
"False",F
''', single=True)
    assert len(grid) == 2
    assert grid[0]['bool'] == True
    assert grid[1]['bool'] == False


def test_bool_json():
    yield _check_bool_json, False  # without pint
    yield _check_bool_json, True  # with pint


def _check_bool_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'bool'},
        ],
        'rows': [
            {'str': 'True', 'bool': True},
            {'str': 'False', 'bool': False},
        ],
    }, mode=MODE_JSON, single=True)
    assert grid[0]['bool'] == True
    assert grid[1]['bool'] == False


def test_number():
    yield _check_number, False  # without pint
    yield _check_number, True  # with pint


def _check_number(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(u'''ver:"2.0"
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
''', single=True)
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
    yield _check_number_json, False  # without pint
    yield _check_number_json, True  # with pint


def _check_number_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'number'},
        ],
        'rows': [
            {'str': "Integer", 'number': u'n:1'},
            {'str': "Negative Integer", 'number': u'n:-34'},
            {'str': "With Separators", 'number': u'n:10000'},
            {'str': "Scientific", 'number': u'n:5.4e-45'},
            {'str': "Units mass", 'number': u'n:9.23 kg'},
            {'str': "Units time", 'number': u'n:4 min'},
            {'str': "Units temperature", 'number': u'n:74.2 °F'},
            {'str': "Positive Infinity", 'number': u'n:INF'},
            {'str': "Negative Infinity", 'number': u'n:-INF'},
            {'str': "Not a Number", 'number': u'n:NaN'},
        ],
    }, mode=MODE_JSON, single=True)
    check_number(grid)


def test_string():
    yield _check_string, False  # without pint
    yield _check_string, True  # with pint


def _check_string(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
str,strExample
"Empty",""
"Basic","Simple string"
"Escaped","This\\tIs\\nA\\r\\"Test\\"\\\\\\$"
''', single=True)

    assert len(grid) == 3
    assert grid[0]['strExample'] == ''
    assert grid[1]['strExample'] == 'Simple string'
    assert grid[2]['strExample'] == 'This\tIs\nA\r"Test"\\$'


def test_string_json():
    yield _check_string_json, False  # without pint
    yield _check_string_json, True  # with pint


def _check_string_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'strExample'},
        ],
        'rows': [
            {'str': "Empty", 'strExample': ''},
            {'str': "Implicit", 'strExample': 'a string'},
            {'str': "Literal", 'strExample': 's:an explicit string'},
            {'str': "With colons", 'strExample': 's:string:with:colons'},
        ],
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 4
    assert grid.pop(0)['strExample'] == ''
    assert grid.pop(0)['strExample'] == 'a string'
    assert grid.pop(0)['strExample'] == 'an explicit string'
    assert grid.pop(0)['strExample'] == 'string:with:colons'


def test_uri():
    yield _check_uri, False  # without pint
    yield _check_uri, True  # with pint


def _check_uri(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
uri
`http://www.vrt.com.au`
''', single=True)

    assert len(grid) == 1
    assert grid[0]['uri'] == hszinc.Uri('http://www.vrt.com.au')


def test_uri_json():
    yield _check_uri_json, False  # without pint
    yield _check_uri_json, True  # with pint


def _check_uri_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'uri'},
        ],
        'rows': [
            {'uri': 'u:http://www.vrt.com.au'},
        ],
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 1
    assert grid[0]['uri'] == hszinc.Uri('http://www.vrt.com.au')


def test_ref():
    yield _check_ref, False  # without pint
    yield _check_ref, True  # with pint


def _check_ref(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
str,ref
"Basic",@a-basic-ref
"With value",@reference "With value"
''', single=True)

    assert len(grid) == 2
    assert grid[0]['ref'] == hszinc.Ref('a-basic-ref')
    assert grid[1]['ref'] == hszinc.Ref('reference', 'With value')


def test_ref_json():
    yield _check_ref_json, False  # without pint
    yield _check_ref_json, True  # with pint


def _check_ref_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'ref'},
        ],
        'rows': [
            {'str': 'Basic', 'ref': 'r:a-basic-ref'},
            {'str': 'With value', 'ref': 'r:reference With value'},
        ],
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 2
    assert grid[0]['ref'] == hszinc.Ref('a-basic-ref')
    assert grid[1]['ref'] == hszinc.Ref('reference', 'With value')


def test_date():
    yield _check_date, False  # without pint
    yield _check_date, True  # with pint


def _check_date(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
date
2010-03-13
''', single=True)

    assert len(grid) == 1
    assert isinstance(grid[0]['date'], datetime.date)
    assert grid[0]['date'] == datetime.date(2010, 3, 13)


def test_date_json():
    yield _check_date_json, False  # without pint
    yield _check_date_json, True  # with pint


def _check_date_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'date'},
        ],
        'rows': [
            {'date': 'd:2010-03-13'},
        ],
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 1
    assert isinstance(grid[0]['date'], datetime.date)
    assert grid[0]['date'] == datetime.date(2010, 3, 13)


def test_time():
    yield _check_time, False  # without pint
    yield _check_time, True  # with pint


def _check_time(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
time
08:12:05
08:12:05.5
''', single=True)

    assert len(grid) == 2
    assert isinstance(grid[0]['time'], datetime.time)
    assert grid[0]['time'] == datetime.time(8, 12, 5)
    assert isinstance(grid[1]['time'], datetime.time)
    assert grid[1]['time'] == datetime.time(8, 12, 5, 500000)


def test_time_json():
    yield _check_time_json, False  # without pint
    yield _check_time_json, True  # with pint


def _check_time_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'time'},
        ],
        'rows': [
            {'time': 'h:08:12'},
            {'time': 'h:08:12:05'},
            {'time': 'h:08:12:05.5'},
        ],
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 3
    row = grid.pop(0)
    assert isinstance(row['time'], datetime.time)
    assert row['time'] == datetime.time(8, 12)
    row = grid.pop(0)
    assert isinstance(row['time'], datetime.time)
    assert row['time'] == datetime.time(8, 12, 5)
    row = grid.pop(0)
    assert isinstance(row['time'], datetime.time)
    assert row['time'] == datetime.time(8, 12, 5, 500000)


def test_datetime():
    yield _check_datetime, False  # without pint
    yield _check_datetime, True  # with pint


def _check_datetime(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
datetime
2010-11-28T07:23:02.500-08:00 Los_Angeles
2010-11-28T23:19:29.500+08:00 Taipei
2010-11-28T18:21:58+03:00 GMT-3
2010-11-28T12:22:27-03:00 GMT+3
2010-01-08T05:00:00Z UTC
2010-01-08T05:00:00Z
''', single=True)

    check_datetime(grid)


def check_datetime(grid):
    assert len(grid) == 6
    row = grid.pop(0)
    assert isinstance(row['datetime'], datetime.datetime)
    assert row['datetime'] == \
           pytz.timezone('America/Los_Angeles').localize( \
               datetime.datetime(2010, 11, 28, 7, 23, 2, 500000))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('Asia/Taipei').localize( \
               datetime.datetime(2010, 11, 28, 23, 19, 29, 500000))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('Etc/GMT-3').localize( \
               datetime.datetime(2010, 11, 28, 18, 21, 58, 0))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('Etc/GMT+3').localize( \
               datetime.datetime(2010, 11, 28, 12, 22, 27, 0))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('UTC').localize( \
               datetime.datetime(2010, 1, 8, 5, 0, 0, 0))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('UTC').localize( \
               datetime.datetime(2010, 1, 8, 5, 0, 0, 0))


def test_datetime_json():
    yield _check_datetime_json, False  # without pint
    yield _check_datetime_json, True  # with pint


def _check_datetime_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'datetime'},
        ],
        'rows': [
            {'datetime': 't:2010-11-28T07:23:02.500-08:00 Los_Angeles'},
            {'datetime': 't:2010-11-28T23:19:29.500+08:00 Taipei'},
            {'datetime': 't:2010-11-28T18:21:58+03:00 GMT-3'},
            {'datetime': 't:2010-11-28T12:22:27-03:00 GMT+3'},
            {'datetime': 't:2010-01-08T05:00:00Z UTC'},
            {'datetime': 't:2010-01-08T05:00:00Z'},
        ],
    }, mode=MODE_JSON, single=True)
    check_datetime(grid)


def test_list():
    yield _check_list, False  # without pint
    yield _check_list, True  # with pint


def _check_list(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0"
ix,list,                                                       dis
00,[],                                                         "An empty list"
01,[N],                                                        "A list with a NULL"
02,[T,F],                                                      "Booleans in a list"
03,[1,2,3],                                                    "Integers"
04,[1.1,2.2,3.3],                                              "Floats"
05,[1.1e3,2.2e6,3.3e9],                                        "Exponential floats"
06,[3.14rad,180°],                                             "Quantities"
07,["a","b","c"],                                              "Strings"
08,[1970-01-01,2000-01-01,2030-01-01],                         "Dates"
09,[06:00:00,12:00:00,18:00:00],                               "Times"
10,[1970-01-01T00:00:00Z,1970-01-01T10:00:00+10:00 Brisbane],  "Date/Times"
11,[N,T,1,1.1,1.1e3,3.14rad,"a"],                              "Mixed data"
12,[  1,  2  ,  3 ,4  ],                                       "Whitespace"
13,[1,2,3,4,],                                                 "Trailing comma"
14,[[1,2,3],["a","b","c"]],                                    "Nested lists"
''', single=True)
    # There should be 15 rows
    assert len(grid) == 15
    for row in grid:
        assert isinstance(row['list'], list)
    assert grid[0]['list'] == []
    assert grid[1]['list'] == [None]
    assert grid[2]['list'] == [True, False]
    assert grid[3]['list'] == [1.0, 2.0, 3.0]
    assert grid[4]['list'] == [1.1, 2.2, 3.3]
    assert grid[5]['list'] == [1.1e3, 2.2e6, 3.3e9]
    assert grid[6]['list'] == [hszinc.Quantity(3.14, unit='rad'),
                               hszinc.Quantity(180, unit='°')]
    assert grid[7]['list'] == ["a", "b", "c"]
    assert grid[8]['list'] == [datetime.date(1970, 1, 1),
                               datetime.date(2000, 1, 1),
                               datetime.date(2030, 1, 1)]
    assert grid[9]['list'] == [datetime.time(6, 0, 0),
                               datetime.time(12, 0, 0),
                               datetime.time(18, 0, 0)]
    assert grid[10]['list'] == [pytz.utc.localize(
        datetime.datetime(1970, 1, 1, 0, 0)),
        pytz.timezone('Australia/Brisbane').localize(
            datetime.datetime(1970, 1, 1, 10, 0))]
    assert grid[11]['list'] == [None, True, 1.0, 1.1, 1.1e3,
                                hszinc.Quantity(3.14, unit='rad'),
                                "a"]
    assert grid[12]['list'] == [1.0, 2.0, 3.0, 4.0]
    assert grid[13]['list'] == [1.0, 2.0, 3.0, 4.0]
    assert grid[14]['list'] == [[1.0, 2.0, 3.0], ["a", "b", "c"]]


def test_list_v2():
    yield _check_list_v2, False  # without pint
    yield _check_list_v2, True  # with pint


def _check_list_v2(pint_en):
    _enable_pint(pint_en)
    try:
        hszinc.parse('''ver:"2.0"
ix,list,                                                       dis
00,[],                                                         "An empty list"
01,[N],                                                        "A list with a NULL"
''', single=True)
        assert False, 'Project Haystack 2.0 does not support lists'
    except hszinc.zincparser.ZincParseException:
        pass


def test_list_json():
    yield _check_list_json, False  # without pint
    yield _check_list_json, True  # with pint


def _check_list_json(pint_en):
    _enable_pint(pint_en)
    # Simpler test case than the ZINC one, since the Python JSON parser
    # will take care of the elements for us.
    grid = hszinc.parse({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'list'},
        ],
        'rows': [
            {'list': ['s:my list', None, True, 'n:1234']}
        ]
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 1
    lst = grid[0]['list']
    assert isinstance(lst, list)
    assert len(lst) == 4
    assert lst[0] == 'my list'
    assert_is(lst[1], None)
    assert_is(lst[2], True)
    assert lst[3] == 1234.0


def test_list_json_v2():
    yield _check_list_json_v2, False  # without pint
    yield _check_list_json_v2, True  # with pint


def _check_list_json_v2(pint_en):
    _enable_pint(pint_en)
    # Version 2.0 does not support lists
    try:
        hszinc.parse({
            'meta': {'ver': '2.0'},
            'cols': [
                {'name': 'list'},
            ],
            'rows': [
                {'list': ['s:my list', None, True, 'n:1234']}
            ]
        }, mode=MODE_JSON, single=True)
        assert False, 'Project Haystack 2.0 does not support lists'
    except ValueError:
        pass

def test_dict():
    yield _check_dict, False
    yield _check_dict, True

def _check_dict(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0"
ix,dict,                                                       dis
00,{},                                                         "An empty dict"
01,{marker},                                                   "A marker in a dict"
02,{tag: 1},                                                   "A tag with number in a dict"
03,{tag: [1,2]},                                               "A tag with list in a dict"
04,{marker tag: [1,2]},                                        "A marker and tag with list in a dict"
05,{tag: {marker}},                                            "A tag  with dict in a dict"
''', single=True)
    # There should be 4 rows
    assert len(grid) == 6
    for row in grid:
        assert isinstance(row['dict'], dict)
    assert grid[0]['dict'] == {}
    assert grid[1]['dict'] == {'marker': MARKER}
    assert grid[2]['dict'] == {'tag': 1.0}
    assert grid[3]['dict'] == {'tag': [1.0, 2.0]}
    assert grid[4]['dict'] == {'marker': MARKER, 'tag': [1.0, 2.0]}
    assert grid[5]['dict'] == {'tag': {'marker': MARKER}}


def test_dict_json():
    yield _check_dict_json, False
    yield _check_dict_json, True

def _check_dict_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'dict'},
        ],
        'rows': [
            {'dict': {}},
            {'dict': {'marker': 'm:'}},
            {'dict': {'tag': 1.0}},
            {'dict': {'tag': [1, 2]}},
            {'dict': {'marker': 'm:', 'tag': [1, 2]}},
            {'dict': {'tag': {'marker': 'm:'}}},
        ]
    }, mode=MODE_JSON, single=True)
    # There should be 4 rows
    assert len(grid) == 6
    for row in grid:
        assert isinstance(row['dict'], dict)
    assert grid[0]['dict'] == {}
    assert grid[1]['dict'] == {'marker': MARKER}
    assert grid[2]['dict'] == {'tag': 1.0}
    assert grid[3]['dict'] == {'tag': [1.0, 2.0]}
    assert grid[4]['dict'] == {'marker': MARKER, 'tag': [1.0, 2.0]}
    assert grid[5]['dict'] == {'tag': {'marker': MARKER}}

def test_dict_invalide_version():
    def _check_dict_invalide_version(pint_en):
        _enable_pint(pint_en)
        try:
            hszinc.parse('''ver:"2.0"
            ix,dict,                                                       dis
            00,{},                                                         "An empty dict"
            ''', single=True)
            assert False
        except ZincParseException as e:
            pass
    yield _check_dict_invalide_version, False
    yield _check_dict_invalide_version, True

def test_dump_invalide_scalar():
    assert dump_scalar(None)

def test_bin():
    yield _check_bin, False  # without pint
    yield _check_bin, True  # with pint


def _check_bin(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
bin
Bin(text/plain)
''', single=True)

    assert len(grid) == 1
    assert grid[0]['bin'] == hszinc.Bin('text/plain')


def test_dict():
    yield _check_dict, False
    yield _check_dict, True

def _check_dict(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0"
ix,dict,                                                       dis
00,{},                                                         "An empty dict"
01,{marker},                                                   "A marker in a dict"
02,{tag: 1},                                                   "A tag with number in a dict"
03,{tag: [1,2]},                                               "A tag with list in a dict"
04,{marker tag: [1,2]},                                        "A marker and tag with list in a dict"
05,{tag: {marker}},                                            "A tag  with dict in a dict"
''', single=True)
    # There should be 4 rows
    assert len(grid) == 6
    for row in grid:
        assert isinstance(row['dict'], dict)
    assert grid[0]['dict'] == {}
    assert grid[1]['dict'] == {'marker': MARKER}
    assert grid[2]['dict'] == {'tag': 1.0}
    assert grid[3]['dict'] == {'tag': [1.0, 2.0]}
    assert grid[4]['dict'] == {'marker': MARKER, 'tag': [1.0, 2.0]}
    assert grid[5]['dict'] == {'tag': {'marker': MARKER}}


def test_dict_json():
    yield _check_dict_json, False
    yield _check_dict_json, True

def _check_dict_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'dict'},
        ],
        'rows': [
            {'dict': {}},
            {'dict': {'marker': 'm:'}},
            {'dict': {'tag': 1.0}},
            {'dict': {'tag': [1, 2]}},
            {'dict': {'marker': 'm:', 'tag': [1, 2]}},
            {'dict': {'tag': {'marker': 'm:'}}},
        ]
    }, mode=MODE_JSON, single=True)

    # There should be 4 rows
    assert len(grid) == 6
    for row in grid:
        assert isinstance(row['dict'], dict)
    assert grid[0]['dict'] == {}
    assert grid[1]['dict'] == {'marker': MARKER}
    assert grid[2]['dict'] == {'tag': 1.0}
    assert grid[3]['dict'] == {'tag': [1.0, 2.0]}
    assert grid[4]['dict'] == {'marker': MARKER, 'tag': [1.0, 2.0]}
    assert grid[5]['dict'] == {'tag': {'marker': MARKER}}


def test_bin():
    yield _check_bin, False  # without pint
    yield _check_bin, True  # with pint


def _check_bin(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
bin
Bin(text/plain)
''', single=True)
    assert len(grid) == 1
    assert grid[0]['bin'] == hszinc.Bin('text/plain')

def test_xstr_hex():
    def _check_xstr(pint_en):
        _enable_pint(pint_en)
        grid = hszinc.parse('''ver:"3.0"
bin
hex("deadbeef")
''', single=True)
        assert len(grid) == 1
        assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'
    yield _check_xstr, False
    yield _check_xstr, True


def test_xstr_b64():
    def _check_xstr(pint_en):
        _enable_pint(pint_en)
        grid = hszinc.parse('''ver:"3.0"
bin
b64("3q2+7w==")
''', single=True)
        assert len(grid) == 1
        assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'
    yield _check_xstr, False
    yield _check_xstr, True


def test_xstr_hex_json():
    def _check_xstr(pint_en):
        _enable_pint(pint_en)
        grid = hszinc.parse({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'bin'},
        ],
        'rows': [
            {'bin': 'x:hex:deadbeef'},
        ],
    }, mode=MODE_JSON, single=True)
        assert len(grid) == 1
        assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'
    yield _check_xstr, False
    yield _check_xstr, True


def test_xstr_b64_json():
    def _check_xstr(pint_en):
        _enable_pint(pint_en)
        grid = hszinc.parse({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'bin'},
        ],
        'rows': [
            {'bin': 'x:b64:3q2+7w=='},
        ],
    }, mode=MODE_JSON, single=True)
        assert len(grid) == 1
        assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'
    yield _check_xstr, False
    yield _check_xstr, True


def test_bin_json():
    yield _check_bin_json, False  # without pint
    yield _check_bin_json, True  # with pint


def _check_bin_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'bin'},
        ],
        'rows': [
            {'bin': 'b:text/plain'},
        ],
    }, mode=MODE_JSON, single=True)
    assert len(grid) == 1
    assert grid[0]['bin'] == hszinc.Bin('text/plain')


def test_coord():
    yield _check_coord, False  # without pint
    yield _check_coord, True  # with pint


def _check_coord(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
coord
C(37.55,-77.45)
''', single=True)

    assert len(grid) == 1
    assert grid[0]['coord'] == hszinc.Coordinate(37.55, -77.45)


def test_coord_json():
    yield _check_coord_json, False  # without pint
    yield _check_coord_json, True  # with pint


def _check_coord_json(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'coord'},
        ],
        'rows': [
            {'coord': 'c:37.55,-77.45'},
        ],
    }, mode=MODE_JSON, single=True)

    assert len(grid) == 1
    assert grid[0]['coord'] == hszinc.Coordinate(37.55, -77.45)


def test_multi_grid():
    yield _check_multi_grid, False  # without pint
    yield _check_multi_grid, True  # with pint


def _check_multi_grid(pint_en):
    _enable_pint(pint_en)
    # Multiple grids are separated by newlines.
    grid_list = hszinc.parse('\n'.join([
        SIMPLE_EXAMPLE, METADATA_EXAMPLE, NULL_EXAMPLE]), single=False)
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1])
    check_null(grid_list[2])


def test_multi_grid_json():
    yield _check_multi_grid_json, False  # without pint
    yield _check_multi_grid_json, True  # with pint


def _check_multi_grid_json(pint_en):
    _enable_pint(pint_en)
    # Multiple grids are separated by newlines.
    grid_list = hszinc.parse([SIMPLE_EXAMPLE_JSON,
                              METADATA_EXAMPLE_JSON, NULL_EXAMPLE_JSON],
                              mode=MODE_JSON, single=False)
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1], force_metadata_order=False)
    check_null(grid_list[2])


def test_multi_grid_json_str():
    yield _check_multi_grid_json_str, False  # without pint
    yield _check_multi_grid_json_str, True  # with pint


def _check_multi_grid_json_str(pint_en):
    _enable_pint(pint_en)
    grid_list = hszinc.parse(json.dumps([SIMPLE_EXAMPLE_JSON,
                                                   METADATA_EXAMPLE_JSON,
                                                   NULL_EXAMPLE_JSON]),
                                                   mode=MODE_JSON,
                                                   single=False)
    assert len(grid_list) == 3
    check_simple(grid_list[0])
    check_metadata(grid_list[1], force_metadata_order=False)
    check_null(grid_list[2])


def test_grid_meta():
    yield _check_grid_meta, False  # without pint
    yield _check_grid_meta, True  # with pint


def _check_grid_meta(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0" aString:"aValue" aNumber:3.14159 aNull:N aMarker:M anotherMarker aQuantity:123Hz aDate:2016-01-13 aTime:06:44:00 aTimestamp:2016-01-13T06:44:00+10:00 Brisbane aPlace:C(-27.4725,153.003)
empty
''', single=True)

    assert len(grid) == 0
    meta = grid.metadata
    assert list(meta.keys()) == ['aString', 'aNumber', 'aNull',
                                 'aMarker', 'anotherMarker', 'aQuantity', 'aDate', 'aTime',
                                 'aTimestamp', 'aPlace']
    assert meta['aString'] == 'aValue'
    assert meta['aNumber'] == 3.14159
    assert_is(meta['aNull'], None)
    assert_is(meta['aMarker'], hszinc.MARKER)
    assert_is(meta['anotherMarker'], hszinc.MARKER)
    assert isinstance(meta['aQuantity'], hszinc.Quantity)
    assert meta['aQuantity'].value == 123
    assert meta['aQuantity'].unit == 'Hz'
    assert isinstance(meta['aDate'], datetime.date)
    assert meta['aDate'] == datetime.date(2016, 1, 13)
    assert isinstance(meta['aTime'], datetime.time)
    assert meta['aTime'] == datetime.time(6, 44)
    assert isinstance(meta['aTimestamp'], datetime.datetime)
    assert meta['aTimestamp'] == \
           pytz.timezone('Australia/Brisbane').localize( \
               datetime.datetime(2016, 1, 13, 6, 44))
    assert isinstance(meta['aPlace'], hszinc.Coordinate)
    assert meta['aPlace'].latitude == -27.4725
    assert meta['aPlace'].longitude == 153.003


def test_col_meta():
    yield _check_col_meta, False  # without pint
    yield _check_col_meta, True  # with pint


def _check_col_meta(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0"
aColumn aString:"aValue" aNumber:3.14159 aNull:N aMarker:M anotherMarker aQuantity:123Hz aDate:2016-01-13 aTime:06:44:00 aTimestamp:2016-01-13T06:44:00+10:00 Brisbane aPlace:C(-27.4725,153.003)
''', single=True)

    assert len(grid) == 0
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['aColumn']
    meta = grid.column['aColumn']
    assert list(meta.keys()) == ['aString', 'aNumber', 'aNull',
                                 'aMarker', 'anotherMarker', 'aQuantity', 'aDate', 'aTime',
                                 'aTimestamp', 'aPlace']
    assert meta['aString'] == 'aValue'
    assert meta['aNumber'] == 3.14159
    assert_is(meta['aNull'], None)
    assert_is(meta['aMarker'], hszinc.MARKER)
    assert_is(meta['anotherMarker'], hszinc.MARKER)
    assert isinstance(meta['aQuantity'], hszinc.Quantity)
    assert meta['aQuantity'].value == 123
    assert meta['aQuantity'].unit == 'Hz'
    assert isinstance(meta['aDate'], datetime.date)
    assert meta['aDate'] == datetime.date(2016, 1, 13)
    assert isinstance(meta['aTime'], datetime.time)
    assert meta['aTime'] == datetime.time(6, 44)
    assert isinstance(meta['aTimestamp'], datetime.datetime)
    assert meta['aTimestamp'] == \
           pytz.timezone('Australia/Brisbane').localize( \
               datetime.datetime(2016, 1, 13, 6, 44))
    assert isinstance(meta['aPlace'], hszinc.Coordinate)
    assert meta['aPlace'].latitude == -27.4725
    assert meta['aPlace'].longitude == 153.003


def test_too_many_cells():
    yield _check_too_many_cells, False  # without pint
    yield _check_too_many_cells, True  # with pint


def _check_too_many_cells(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
col1, col2, col3
"Val1", "Val2", "Val3", "Val4", "Val5"
''', single=True)
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['col1', 'col2', 'col3']

    row = grid[0]
    assert set(row.keys()) == set(['col1', 'col2', 'col3'])
    assert row['col1'] == 'Val1'
    assert row['col2'] == 'Val2'
    assert row['col3'] == 'Val3'


def test_nodehaystack_01():
    yield _check_nodehaystack_01, False  # without pint
    yield _check_nodehaystack_01, True  # with pint


def _check_nodehaystack_01(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0"
fooBar33
''', single=True)
    assert len(grid) == 0
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['fooBar33']


def test_nodehaystack_02():
    yield _check_nodehaystack_02, False  # without pint
    yield _check_nodehaystack_02, True  # with pint


def _check_nodehaystack_02(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0" tag foo:"bar"
xyz
"val"
''', single=True)
    assert len(grid) == 1
    assert list(grid.metadata.keys()) == ['tag', 'foo']
    assert_is(grid.metadata['tag'], hszinc.MARKER)
    assert grid.metadata['foo'] == 'bar'
    assert list(grid.column.keys()) == ['xyz']
    assert grid[0]['xyz'] == 'val'


def test_nodehaystack_03():
    yield _check_nodehaystack_03, False  # without pint
    yield _check_nodehaystack_03, True  # with pint


def _check_nodehaystack_03(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
val
N
''', single=True)
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['val']
    assert_is(grid[0]['val'], None)


def test_nodehaystack_04():
    yield _check_nodehaystack_04, False  # without pint
    yield _check_nodehaystack_04, True  # with pint


def _check_nodehaystack_04(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
a,b
1,2
3,4
''', single=True)
    assert len(grid) == 2
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b']
    assert grid[0]['a'] == 1
    assert grid[0]['b'] == 2
    assert grid[1]['a'] == 3
    assert grid[1]['b'] == 4


def test_nodehaystack_05():
    yield _check_nodehaystack_05, False  # without pint
    yield _check_nodehaystack_05, True  # with pint


def _check_nodehaystack_05(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"3.0"
a,    b,      c,      d
T,    F,      N,   -99
2.3,  -5e-10, 2.4e20, 123e-10
"",   "a",   "\\" \\\\ \\t \\n \\r", "\\uabcd"
`path`, @12cbb082-0c02ae73, 4s, -2.5min
M,R,hex("010203"),hex("010203")
2009-12-31, 23:59:01, 01:02:03.123, 2009-02-03T04:05:06Z
INF, -INF, "", NaN
C(12,-34),C(0.123,-.789),C(84.5,-77.45),C(-90,180)
''', single=True)
    assert len(grid) == 8
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b', 'c', 'd']
    row = grid.pop(0)
    assert row['a'] == True
    assert row['b'] == False
    assert_is(row['c'], None)
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
    assert_is(row['a'], hszinc.MARKER)
    assert_is(row['b'], hszinc.REMOVE)
    assert row['c'] == XStr('hex','010203')
    assert row['d'] == XStr('hex','010203')
    row = grid.pop(0)
    assert row['a'] == datetime.date(2009, 12, 31)
    assert row['b'] == datetime.time(23, 59, 1)
    assert row['c'] == datetime.time(1, 2, 3, 123000)
    assert row['d'] == \
           datetime.datetime(2009, 2, 3, 4, 5, 6, tzinfo=pytz.utc)
    row = grid.pop(0)
    assert math.isinf(row['a']) and (row['a'] > 0)
    assert math.isinf(row['b']) and (row['b'] < 0)
    assert row['c'] == ''
    assert math.isnan(row['d'])
    row = grid.pop(0)
    assert row['a'] == hszinc.Coordinate(12, -34)
    assert row['b'] == hszinc.Coordinate(.123, -.789)
    assert row['c'] == hszinc.Coordinate(84.5, -77.45)
    assert row['d'] == hszinc.Coordinate(-90, 180)


def test_nodehaystack_06():
    yield _check_nodehaystack_06, False  # without pint
    yield _check_nodehaystack_06, True  # with pint


def _check_nodehaystack_06(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
foo
`foo$20bar`
`foo\\`bar`
`file \\#2`
"$15"
''', single=True)
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
    yield _check_nodehaystack_07, False  # without pint
    yield _check_nodehaystack_07, True  # with pint


def _check_nodehaystack_07(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(u'''ver:"2.0"
a, b
-3.1kg,4kg
5%,3.2%
5kWh/ft\u00b2,-15kWh/m\u00b2
123e+12kJ/kg_dry,74\u0394\u00b0F
''', single=True)
    assert len(grid) == 4
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b']
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(-3.1, 'kg')
    assert row['b'] == hszinc.Quantity(4, 'kg')
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(5, '%')
    assert row['b'] == hszinc.Quantity(3.2, '%')
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(5, u'kWh/ft\u00b2')
    assert row['b'] == hszinc.Quantity(-15, u'kWh/m\u00b2')
    row = grid.pop(0)
    assert row['a'] == hszinc.Quantity(123e12, 'kJ/kg_dry')
    assert row['b'] == hszinc.Quantity(74, u'\u0394\u00b0F')


def test_nodehaystack_08():
    yield _check_nodehaystack_08, False  # without pint
    yield _check_nodehaystack_08, True  # with pint


def _check_nodehaystack_08(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
a,b
2010-03-01T23:55:00.013-05:00 GMT+5,2010-03-01T23:55:00.013+10:00 GMT-10
''', single=True)
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b']
    row = grid.pop(0)
    assert row['a'] == hszinc.zoneinfo.timezone('GMT+5').localize( \
        datetime.datetime(2010, 3, 1, 23, 55, 0, 13000))
    assert row['b'] == hszinc.zoneinfo.timezone('GMT-10').localize( \
        datetime.datetime(2010, 3, 1, 23, 55, 0, 13000))


def test_nodehaystack_09():
    yield _check_nodehaystack_09, False  # without pint
    yield _check_nodehaystack_09, True  # with pint


def _check_nodehaystack_09(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse(u'''ver:"2.0" a: 2009-02-03T04:05:06Z foo b: 2010-02-03T04:05:06Z UTC bar c: 2009-12-03T04:05:06Z London baz
a
3.814697265625E-6
2010-12-18T14:11:30.924Z
2010-12-18T14:11:30.925Z UTC
2010-12-18T14:11:30.925Z London
45$
33\u00a3
@12cbb08e-0c02ae73
7.15625E-4kWh/ft\u00b2
''', single=True)
    assert len(grid) == 8
    assert list(grid.metadata.keys()) == ['a', 'foo', 'b', 'bar', 'c', 'baz']
    assert grid.metadata['a'] == pytz.utc.localize( \
        datetime.datetime(2009, 2, 3, 4, 5, 6))
    assert grid.metadata['b'] == pytz.utc.localize( \
        datetime.datetime(2010, 2, 3, 4, 5, 6))
    assert grid.metadata['c'] == pytz.timezone('Europe/London').localize( \
        datetime.datetime(2009, 12, 3, 4, 5, 6))
    assert_is(grid.metadata['foo'], hszinc.MARKER)
    assert_is(grid.metadata['bar'], hszinc.MARKER)
    assert_is(grid.metadata['baz'], hszinc.MARKER)
    assert list(grid.column.keys()) == ['a']
    assert grid.pop(0)['a'] == 3.814697265625E-6
    assert grid.pop(0)['a'] == pytz.utc.localize( \
        datetime.datetime(2010, 12, 18, 14, 11, 30, 924000))
    assert grid.pop(0)['a'] == pytz.utc.localize( \
        datetime.datetime(2010, 12, 18, 14, 11, 30, 925000))
    assert grid.pop(0)['a'] == pytz.timezone('Europe/London').localize( \
        datetime.datetime(2010, 12, 18, 14, 11, 30, 925000))
    assert grid.pop(0)['a'] == hszinc.Quantity(45, '$')
    assert grid.pop(0)['a'] == hszinc.Quantity(33, u'\u00a3')
    assert grid.pop(0)['a'] == hszinc.Ref('12cbb08e-0c02ae73')
    assert grid.pop(0)['a'] == hszinc.Quantity(7.15625E-4, u'kWh/ft\u00b2')


def test_nodehaystack_10():
    yield _check_nodehaystack_10, False  # without pint
    yield _check_nodehaystack_10, True  # with pint


def _check_nodehaystack_10(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0" bg: Bin(image/jpeg) mark
file1 dis:"F1" icon: Bin(image/gif),file2 icon: Bin(image/jpg)
Bin(text/plain),N
4,Bin(image/png)
Bin(text/html; a=foo; bar="sep"),Bin(text/html; charset=utf8)
''', single=True)
    assert len(grid) == 3
    assert list(grid.metadata.keys()) == ['bg', 'mark']
    assert grid.metadata['bg'] == hszinc.Bin('image/jpeg')
    assert_is(grid.metadata['mark'], hszinc.MARKER)
    assert list(grid.column.keys()) == ['file1', 'file2']
    assert list(grid.column['file1'].keys()) == ['dis', 'icon']
    assert grid.column['file1']['dis'] == 'F1'
    assert grid.column['file1']['icon'] == hszinc.Bin('image/gif')
    assert list(grid.column['file2'].keys()) == ['icon']
    assert grid.column['file2']['icon'] == hszinc.Bin('image/jpg')
    row = grid.pop(0)
    assert row['file1'] == hszinc.Bin('text/plain')
    assert_is(row['file2'], None)
    row = grid.pop(0)
    assert row['file1'] == 4
    assert row['file2'] == hszinc.Bin('image/png')
    row = grid.pop(0)
    assert row['file1'] == hszinc.Bin('text/html; a=foo; bar="sep"')
    assert row['file2'] == hszinc.Bin('text/html; charset=utf8')


def test_nodehaystack_11():
    yield _check_nodehaystack_11, False  # without pint
    yield _check_nodehaystack_11, True  # with pint


def _check_nodehaystack_11(pint_en):
    _enable_pint(pint_en)
    grid = hszinc.parse('''ver:"2.0"
a, b, c
, 1, 2
3, , 5
6, 7_000,
,,10
,,
14,,
''', single=True)
    assert len(grid) == 6
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b', 'c']
    row = grid.pop(0)
    assert_is(row['a'], None)
    assert row['b'] == 1
    assert row['c'] == 2
    row = grid.pop(0)
    assert row['a'] == 3
    assert_is(row['b'], None)
    assert row['c'] == 5
    row = grid.pop(0)
    assert row['a'] == 6
    assert row['b'] == 7000
    assert_is(row['c'], None)
    row = grid.pop(0)
    assert_is(row['a'], None)
    assert_is(row['b'], None)
    assert row['c'] == 10
    row = grid.pop(0)
    assert_is(row['a'], None)
    assert_is(row['b'], None)
    assert_is(row['c'], None)
    row = grid.pop(0)
    assert row['a'] == 14
    assert_is(row['b'], None)
    assert_is(row['c'], None)


# Scalar parsing tests… no need to be exhaustive here because the grid tests
# cover the underlying cases.  This is basically checking that bytestring decoding
# works and versions are passed through.

def test_scalar_simple_zinc():
    yield _check_scalar_simple_zinc, False  # without pint
    yield _check_scalar_simple_zinc, True  # with pint


def _check_scalar_simple_zinc(pint_en):
    _enable_pint(pint_en)
    assert hszinc.parse_scalar('"Testing"', mode=MODE_ZINC) \
           == "Testing"
    assert hszinc.parse_scalar('50Hz', mode=MODE_ZINC) \
           == hszinc.Quantity(50, unit='Hz')


def test_scalar_bytestring_zinc():
    yield _check_scalar_bytestring_zinc, False  # without pint
    yield _check_scalar_bytestring_zinc, True  # with pint


def _check_scalar_bytestring_zinc(pint_en):
    _enable_pint(pint_en)
    assert hszinc.parse_scalar(b'"Testing"',
                               mode=MODE_ZINC, charset='us-ascii') \
           == "Testing"
    assert hszinc.parse_scalar(b'50Hz',
                               mode=MODE_ZINC, charset='us-ascii') \
           == hszinc.Quantity(50, unit='Hz')


def test_scalar_version_zinc():
    yield _check_scalar_version_zinc, False  # without pint
    yield _check_scalar_version_zinc, True  # with pint


def _check_scalar_version_zinc(pint_en):
    _enable_pint(pint_en)
    # This should forbid us trying to parse a list.
    try:
        hszinc.parse_scalar('[1,2,3]', mode=MODE_ZINC,
                            version=hszinc.VER_2_0)
        assert False, 'Version was ignored'
    except hszinc.zincparser.ZincParseException:
        pass


def test_scalar_simple_json():
    yield _check_scalar_simple_json, False  # without pint
    yield _check_scalar_simple_json, True  # with pint


def _check_scalar_simple_json(pint_en):
    _enable_pint(pint_en)
    assert hszinc.parse_scalar('"s:Testing"', mode=MODE_JSON) \
           == "Testing"
    assert hszinc.parse_scalar('"n:50 Hz"', mode=MODE_JSON) \
           == hszinc.Quantity(50, unit='Hz')


def test_scalar_preparsed_json():
    yield _check_scalar_preparsed_json, False  # without pint
    yield _check_scalar_preparsed_json, True  # with pint


def _check_scalar_preparsed_json(pint_en):
    _enable_pint(pint_en)
    assert hszinc.parse_scalar('s:Testing', mode=MODE_JSON) \
           == "Testing"
    assert hszinc.parse_scalar('n:50 Hz', mode=MODE_JSON) \
           == hszinc.Quantity(50, unit='Hz')


def test_scalar_bytestring_json():
    yield _check_scalar_bytestring_json, False  # without pint
    yield _check_scalar_bytestring_json, True  # with pint


def _check_scalar_bytestring_json(pint_en):
    _enable_pint(pint_en)
    assert hszinc.parse_scalar(b'"s:Testing"',
                               mode=MODE_JSON, charset='us-ascii') \
           == "Testing"
    assert hszinc.parse_scalar(b'"n:50 Hz"',
                               mode=MODE_JSON, charset='us-ascii') \
           == hszinc.Quantity(50, unit='Hz')


def test_scalar_version_json():
    yield _check_scalar_version_json, False  # without pint
    yield _check_scalar_version_json, True  # with pint


def _check_scalar_version_json(pint_en):
    _enable_pint(pint_en)
    # This should forbid us trying to parse a list.
    try:
        res = hszinc.parse_scalar('[ "n:1","n:2","n:3" ]',
                                  mode=MODE_JSON, version=hszinc.VER_2_0)
        assert False, 'Version was ignored; got %r' % res
    except ValueError:
        pass


def test_scalar_json_rawnum():
    yield _check_scalar_json_rawnum, False  # without pint
    yield _check_scalar_json_rawnum, True  # with pint


def _check_scalar_json_rawnum(pint_en):
    _enable_pint(pint_en)
    # Test handling of raw numbers
    assert hszinc.parse_scalar(123, mode=MODE_JSON) == 123
    assert hszinc.parse_scalar(123.45, mode=MODE_JSON) == 123.45


def test_str_version():
    yield _check_str_version, False  # without pint
    yield _check_str_version, True  # with pint


def _check_str_version(pint_en):
    _enable_pint(pint_en)
    # This should assume v3.0, and parse successfully.
    val = hszinc.parse_scalar('[1,2,3]', mode=MODE_ZINC,
                              version='2.5')
    assert val == [1.0, 2.0, 3.0]


def test_malformed_grid_meta():
    yield _check_malformed_grid_meta, False  # without pint
    yield _check_malformed_grid_meta, True  # with pint


def _check_malformed_grid_meta(pint_en):
    _enable_pint(pint_en)
    try:
        hszinc.parse('''ver:"2.0" ThisIsNotATag
empty

''', single=True)
        assert False, 'Parsed a clearly invalid grid'
    except hszinc.zincparser.ZincParseException as zpe:
        assert zpe.line == 1
        assert zpe.col == 11


def test_malformed_col_meta():
    yield _check_malformed_col_meta, False  # without pint
    yield _check_malformed_col_meta, True  # with pint


def _check_malformed_col_meta(pint_en):
    _enable_pint(pint_en)
    try:
        hszinc.parse('''ver:"2.0"
c1 goodSoFar, c2 WHOOPSIE
,
''', single=True)
        assert False, 'Parsed a clearly invalid grid'
    except hszinc.zincparser.ZincParseException as zpe:
        assert zpe.line == 2
        assert zpe.col == 18


def test_malformed_row():
    yield _check_malformed_row, False  # without pint
    yield _check_malformed_row, True  # with pint


def _check_malformed_row(pint_en):
    _enable_pint(pint_en)
    try:
        hszinc.parse('''ver:"2.0"
c1, c2
1, "No problems here"
2, We should fail here
3, "No issue, but we won't get this far"
4, We won't see this error
''', single=True)
        assert False, 'Parsed a clearly invalid grid'
    except hszinc.zincparser.ZincParseException as zpe:
        assert zpe.line == 4
        assert zpe.col == 1


def test_malformed_zinc_scalar():
    # This should always raise an error after logging
    try:
        hszinc.parse_scalar(12341234, mode=MODE_ZINC)
        assert False, 'Should have failed'
    except AssertionError:
        raise
    except:
        pass

def test_skyspark_status_zinc():
    """
    Test parsing a ZINC grid with a string like "{state}" does not fail.
    """
    # Reference: https://github.com/widesky/hszinc/issues/25
    grid_str = '''ver:"2.0"
test
"{state}"
'''
    grid = hszinc.parse(grid_str, mode=MODE_ZINC, single=True)
    assert isinstance(grid, hszinc.Grid), 'Not returned a grid'
    assert len(grid) == 1, 'Too many rows returned'
    assert set(grid[0].keys()) == set(['test'])
    assert grid[0]['test'] == '{state}'

def test_skyspark_status_json():
    """
    Test parsing a JSON grid with a string like "{state}" does not fail.
    """
    # Reference: https://github.com/widesky/hszinc/issues/25
    grid_str = '''{
    "meta": {"ver": "2.0"},
    "cols": [
        {"name": "test"}
    ],
    "rows": [
        {"test": "{state}"}
    ]
}'''
    grid = hszinc.parse(grid_str, mode=MODE_JSON, single=True)
    assert isinstance(grid, hszinc.Grid), 'Not returned a grid (got %r)' % grid
    assert len(grid) == 1, 'Too many rows returned'
    assert set(grid[0].keys()) == set(['test'])
    assert grid[0]['test'] == '{state}'

def test_skyspark_status_json_prefix():
    """
    Test parsing a JSON grid with a string like "s:{state}" does not fail.
    """
    # Reference: https://github.com/widesky/hszinc/issues/25
    grid_str = '''{
    "meta": {"ver": "2.0"},
    "cols": [
        {"name": "test"}
    ],
    "rows": [
        {"test": "s:{state}"}
    ]
}'''
    grid = hszinc.parse(grid_str, mode=MODE_JSON, single=True)
    assert isinstance(grid, hszinc.Grid), 'Not returned a grid (got %r)' % grid
    assert len(grid) == 1, 'Too many rows returned'
    assert set(grid[0].keys()) == set(['test'])
    assert grid[0]['test'] == '{state}'

def test_grid_in_grid():
    yield _check_grid_in_grid, False  # without pint
    yield _check_grid_in_grid, True  # with pint


def _check_grid_in_grid(pint_en=True):
    _enable_pint(pint_en)
    grid = hszinc.parse('ver:"3.0"\n'
                             'inner\n'
                             '<<ver:"3.0"\n'
                             'comment\n'
                             '"A innergrid"\n'
                             '>>\n', mode=MODE_ZINC, single=True)

    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert inner[0]['comment'] == 'A innergrid'


def test_grid_in_grid_json():
    yield _check_grid_in_grid_json, False  # without pint
    yield _check_grid_in_grid_json, True  # with pint


def _check_grid_in_grid_json(pint_en=True):
    _enable_pint(pint_en)
    xstr = \
        '{"meta": {"ver": "3.0"},' \
        ' "cols": [{"name": "inner"}], ' \
        '"rows": [' \
        '{"type":"grid","inner": {' \
        '"meta": {"ver": "3.0"}, ' \
        '"cols": [{"name": "comment"}], ' \
        '"rows": [{"comment": "s:A innergrid"}]}' \
        '}]' \
        '}'
    grid = hszinc.parse(xstr, mode=MODE_JSON, single=True)

    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert inner[0]['comment'] == 'A innergrid'

def test_grid_in_grid_in_grid():
    yield _check_grid_in_grid_in_grid, False  # without pint
    yield _check_grid_in_grid_in_grid, True  # with pint


def _check_grid_in_grid_in_grid(pint_en=True):
    _enable_pint(pint_en)
    grid = hszinc.parse('ver:"3.0"\n'
                        'inner\n'
                        '<<ver:"3.0"\n'
                          'innerinner\n'
                          '<<ver:"3.0"\n'
                            'comment\n'
                            '"A innerinnergrid"\n'
                          '>>\n'
                        '>>\n', mode=MODE_ZINC, single=True)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert isinstance(inner[0]['innerinner'], Grid)
    assert inner[0]['innerinner'][0]['comment'] == "A innerinnergrid"


def test_grid_in_grid_in_grid_json():
    yield _check_grid_in_grid_in_grid_json, False  # without pint
    yield _check_grid_in_grid_in_grid_json, True  # with pint


def _check_grid_in_grid_in_grid_json(pint_en=True):
    _enable_pint(pint_en)
    x = \
        '{"meta": {"ver": "3.0"},' \
        ' "cols": [{"name": "inner"}], ' \
        '"rows": [' \
        '{"inner": ' \
        '{ "meta": {"ver": "3.0"}, ' \
        '"cols": [{"name": "innerinner"}], ' \
        '"rows": [' \
        '{"innerinner": {' \
        '"meta": {"ver": "3.0"}, ' \
        '"cols": [{"name": "comment"}], ' \
        '"rows": [{"comment": "s:A innerinnergrid"}]}' \
        '}]' \
        '}' \
        '}]' \
        '}'
    grid = hszinc.parse(x, mode=MODE_JSON, single=True)

    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert isinstance(inner[0]['innerinner'], Grid)
    assert inner[0]['innerinner'][0]['comment'] == "A innerinnergrid"

def test_unescape():
    assert _unescape("a\\nb") == "a\nb"

def test_bidon():
    hszinc.parse('''ver:"3.0"
filter
"a"\n''',mode=MODE_ZINC, single=True)
