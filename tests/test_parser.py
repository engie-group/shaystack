# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from __future__ import unicode_literals

import datetime
import json
import math
import os
import textwrap
import warnings

import pytz
from nose.tools import assert_is

import haystackapi
from haystackapi import MARKER, Grid, MODE_JSON, XStr, MODE_CSV
from haystackapi.zincparser import _unescape, ZincParseException

# These are examples taken from http://project-haystack.org/doc/Zinc

SIMPLE_EXAMPLE_ZINC = '''ver:"2.0"
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

SIMPLE_EXAMPLE_CSV = '''firstName,bday
"Jack",1973-07-23
"Jill",1975-11-15
'''

METADATA_EXAMPLE_ZINC = '''ver:"2.0" database:"test" dis:"Site Energy Summary"
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
METADATA_EXAMPLE_CSV = '''siteName,val
"Site 1",356.214kW
"Site 2",463.028kW
'''

NULL_EXAMPLE_ZINC = '''ver:"2.0"
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

NULL_EXAMPLE_CSV = '''str,null
"Implicit",
"Explicit",N
'''

NA_EXAMPLE_ZINC = '''ver:"3.0"
str,na
"NA value",NA
'''

NA_EXAMPLE_JSON = json.dumps({
    'meta': {'ver': '3.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'na'},
    ],
    'rows': [
        {'str': 'NA value', 'na': 'z:'},
    ],
})

REMOVE_EXAMPLE_JSON_V2 = json.dumps({
    'meta': {'ver': '2.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'remove'},
    ],
    'rows': [
        {'str': 'v2 REMOVE value', 'remove': 'x:'},
        {'str': 'v3 REMOVE value', 'remove': '-:'},
    ],
})

REMOVE_EXAMPLE_JSON_V3 = json.dumps({
    'meta': {'ver': '3.0'},
    'cols': [
        {'name': 'str'},
        {'name': 'remove'},
    ],
    'rows': [
        {'str': 'v2 REMOVE value', 'remove': 'x:'},
        {'str': 'v3 REMOVE value', 'remove': '-:'},
    ],
})


def _check_row_keys(row, grid):
    """
    Args:
        row:
        grid:
    """
    assert set(row.keys()) == set(grid.column.keys())


def _check_simple(grid):
    """
    Args:
        grid:
    """
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['firstName', 'bday']
    # Neither column should have metadata
    assert all([len(c) == 0 for c in grid.column.values()])

    assert len(grid) == 2

    # First row:
    row = grid[0]
    _check_row_keys(row, grid)
    assert row['firstName'] == 'Jack'
    assert row['bday'] == datetime.date(1973, 7, 23)

    # Second row:
    row = grid[1]
    _check_row_keys(row, grid)
    assert row['firstName'] == 'Jill'
    assert row['bday'] == datetime.date(1975, 11, 15)


def _check_metadata(grid, force_metadata_order=True):
    """
    Args:
        grid:
        force_metadata_order:
    """
    assert len(grid.metadata) == 2
    if force_metadata_order:
        assert list(grid.metadata.keys()) == ['database', 'dis']
    else:
        assert set(grid.metadata.keys()) == {'database', 'dis'}

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
        assert set(col.keys()) == {'dis', 'unit'}
    assert col['dis'] == 'Value'
    assert col['unit'] == 'kW'

    # First row:
    row = grid[0]
    _check_row_keys(row, grid)
    assert row['siteName'] == 'Site 1'
    val = row['val']
    assert isinstance(val, haystackapi.Quantity)
    assert val.m == 356.214
    assert val.unit == 'kW'

    # Second row:
    row = grid[1]
    _check_row_keys(row, grid)
    assert row['siteName'] == 'Site 2'
    val = row['val']
    assert isinstance(val, haystackapi.Quantity)
    assert val.m == 463.028
    assert val.unit == 'kW'


def _check_null(grid):
    """
    Args:
        grid:
    """
    assert len(grid) == 2
    assert 'null' not in grid[0]
    assert 'null' not in grid[1]


def _check_na(grid):
    """
    Args:
        grid:
    """
    assert len(grid) == 1
    assert_is(grid[0]['na'], haystackapi.NA)


def _check_remove(grid):
    """
    Args:
        grid:
    """
    assert len(grid) == 2
    assert_is(grid[0]['remove'], haystackapi.REMOVE)
    assert_is(grid[1]['remove'], haystackapi.REMOVE)


def _check_number(grid):
    """
    Args:
        grid:
    """
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
    assert row['number'] == haystackapi.Quantity(9.23, 'kg')
    row = grid.pop(0)
    assert row['number'] == haystackapi.Quantity(4.0, 'min')
    row = grid.pop(0)
    assert row['number'] == haystackapi.Quantity(74.2, '°F')
    row = grid.pop(0)
    assert math.isinf(row['number'])
    assert row['number'] > 0
    row = grid.pop(0)
    assert math.isinf(row['number'])
    assert row['number'] < 0
    row = grid.pop(0)
    assert math.isnan(row['number'])


def _check_datetime(grid):
    """
    Args:
        grid:
    """
    assert len(grid) == 6
    row = grid.pop(0)
    assert isinstance(row['datetime'], datetime.datetime)
    assert row['datetime'] == \
           pytz.timezone('America/Los_Angeles').localize(
               datetime.datetime(2010, 11, 28, 7, 23, 2, 500000))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('Asia/Taipei').localize(
               datetime.datetime(2010, 11, 28, 23, 19, 29, 500000))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('Etc/GMT-3').localize(
               datetime.datetime(2010, 11, 28, 18, 21, 58, 0))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('Etc/GMT+3').localize(
               datetime.datetime(2010, 11, 28, 12, 22, 27, 0))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('UTC').localize(
               datetime.datetime(2010, 1, 8, 5, 0, 0, 0))
    row = grid.pop(0)
    assert row['datetime'] == \
           pytz.timezone('UTC').localize(
               datetime.datetime(2010, 1, 8, 5, 0, 0, 0))


def test_simple_zinc():
    grid = haystackapi.parse(SIMPLE_EXAMPLE_ZINC)
    _check_simple(grid)


def test_simple_json():
    grid = haystackapi.parse(json.dumps(SIMPLE_EXAMPLE_JSON),
                             mode=haystackapi.MODE_JSON)
    _check_simple(grid)


def test_simple_csv():
    grid = haystackapi.parse(SIMPLE_EXAMPLE_CSV,
                             mode=haystackapi.MODE_CSV)
    _check_simple(grid)


def test_simple_encoded_zinc():
    grid = haystackapi.parse(SIMPLE_EXAMPLE_ZINC)
    _check_simple(grid)



def test_wc1382_unicode_str_zinc():
    # Don't use pint for this, we wish to see the actual quantity value.

    grid = haystackapi.parse(
        open(os.path.join(THIS_DIR,
                          'wc1382-unicode-grid.txt'), 'rb').read(),
        mode=haystackapi.MODE_ZINC)
    assert len(grid) == 3

    # The values of all the 'temperature' points should have degree symbols.
    assert grid[0]['v1'].unit == 'degC'
    assert grid[1]['v6'].unit == 'degC'


def test_unsupported_old_zinc():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        grid = haystackapi.parse(textwrap.dedent('''
            ver:"1.0"
            comment
            "Testing that we can handle an \\"old\\" version."
            "We pretend it is compatible with v2.0"
            ''')[1:], mode=haystackapi.MODE_ZINC)
        assert grid._version == haystackapi.Version('1.0')


def test_unsupported_newer_zinc():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        grid = haystackapi.parse(textwrap.dedent('''
            ver:"2.5"
            comment
            "Testing that we can handle a version between official versions."
            ["We pretend it is compatible with v3.0"]
            ''')[1:], mode=haystackapi.MODE_ZINC)
        assert grid._version == haystackapi.Version('2.5')


def test_oddball_version_zinc():
    with warnings.catch_warnings(record=True) as warning:
        warnings.simplefilter("always")
        grid = haystackapi.parse(textwrap.dedent('''
            ver:"3"
            comment
            "Testing that we can handle a version expressed slightly differently to normal."
            ["We pretend it is compatible with v3.0"]
            ''')[1:], mode=haystackapi.MODE_ZINC)
        assert grid._version == haystackapi.Version('3')

        # This should not have raised a warning
        assert len(warning) == 0


def test_unsupported_bleedingedge_zinc():
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("ignore", category=DeprecationWarning)
        grid = haystackapi.parse(textwrap.dedent('''
            ver:"9999.9999"
            comment
            "Testing that we can handle a version that's newer than we support."
            ["We pretend it is compatible with v3.0"]
            ''')[1:], mode=haystackapi.MODE_ZINC)
        assert grid._version == haystackapi.Version('9999.9999')


def test_malformed_grid_zinc():
    try:
        haystackapi.parse(textwrap.dedent('''
            ver:2.0 comment:"This grid has no columns!"
            ''')[1:])
        assert False, 'Parsed a malformed grid.'
    except ValueError:
        pass


def test_malformed_version_zinc():
    try:
        haystackapi.parse(textwrap.dedent('''
            ver:TwoPointOh comment:"This grid has an invalid version!"
            empty
            ''')[1:])
        assert False, 'Parsed a malformed version string.'
    except ValueError:
        pass


def test_metadata_zinc():
    grid = haystackapi.parse(METADATA_EXAMPLE_ZINC)
    _check_metadata(grid)


def test_metadata_json():
    grid = haystackapi.parse(json.dumps(METADATA_EXAMPLE_JSON), mode=haystackapi.MODE_JSON)
    _check_metadata(grid, force_metadata_order=False)


def test_null_zinc():
    grid = haystackapi.parse(NULL_EXAMPLE_ZINC)
    _check_null(grid)


def test_null_json():
    grid = haystackapi.parse(json.dumps(NULL_EXAMPLE_JSON), mode=haystackapi.MODE_JSON)
    _check_null(grid)


def test_null_csv():
    grid = haystackapi.parse(NULL_EXAMPLE_CSV, mode=haystackapi.MODE_CSV)
    assert len(grid) == 2
    assert 'null' not in grid[0]
    assert 'null' not in grid[1]


def test_na_zinc():
    grid = haystackapi.parse(NA_EXAMPLE_ZINC)
    _check_na(grid)


def test_na_json():
    grid = haystackapi.parse(NA_EXAMPLE_JSON, mode=haystackapi.MODE_JSON)
    _check_na(grid)


def test_na_csv():
    grid = haystackapi.parse(NA_EXAMPLE_JSON, mode=haystackapi.MODE_JSON)
    _check_na(grid)


def test_remove_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
        str,remove
        "v2 REMOVE value",R
        "v3 REMOVE value",R
        ''')[1:])
    _check_remove(grid)


def test_remove_v2_json():
    grid = haystackapi.parse(REMOVE_EXAMPLE_JSON_V2, mode=haystackapi.MODE_JSON)
    _check_remove(grid)


def test_remove_v3_json():
    grid = haystackapi.parse(REMOVE_EXAMPLE_JSON_V3, mode=haystackapi.MODE_JSON)
    _check_remove(grid)


def test_remove_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        str,remove
        "v2 REMOVE value",R
        "v3 REMOVE value",R
        ''')[1:], mode=haystackapi.MODE_CSV)
    _check_remove(grid)


def test_marker_in_row_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        str,marker
        "No Marker",
        "Marker",M
        ''')[1:])
    assert len(grid) == 2
    assert 'marker' not in grid[0]
    assert_is(grid[1]['marker'], haystackapi.MARKER)


def test_marker_in_row_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'marker'},
        ],
        'rows': [
            {'str': 'No Marker', 'marker': None},
            {'str': 'Marker', 'marker': 'm:'},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert 'marker' not in grid[0]
    assert grid[1]['marker'] is haystackapi.MARKER


def test_marker_in_row_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        str,marker
        "No Marker",
        "Marker",\u2713
        ''')[1:], mode=haystackapi.MODE_CSV)
    assert 'marker' not in grid[0]
    assert grid[1]['marker'] is haystackapi.MARKER


def test_bool_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        str,bool
        "True",T
        "False",F
        ''')[1:])
    assert len(grid) == 2
    assert grid[0]['bool']
    assert not grid[1]['bool']


def test_bool_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'bool'},
        ],
        'rows': [
            {'str': 'True', 'bool': True},
            {'str': 'False', 'bool': False},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert grid[0]['bool']
    assert not grid[1]['bool']


def test_bool_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        str,bool
        "True",true
        "False",false''')[1:], mode=haystackapi.MODE_CSV)
    assert grid[0]['bool']
    assert not grid[1]['bool']


def test_number_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
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
        ''')[1:])
    _check_number(grid)


def test_number_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'number'},
        ],
        'rows': [
            {'str': "Integer", 'number': 'n:1'},
            {'str': "Negative Integer", 'number': 'n:-34'},
            {'str': "With Separators", 'number': 'n:10000'},
            {'str': "Scientific", 'number': 'n:5.4e-45'},
            {'str': "Units mass", 'number': 'n:9.23 kg'},
            {'str': "Units time", 'number': 'n:4 min'},
            {'str': "Units temperature", 'number': 'n:74.2 °F'},
            {'str': "Positive Infinity", 'number': 'n:INF'},
            {'str': "Negative Infinity", 'number': 'n:-INF'},
            {'str': "Not a Number", 'number': 'n:NaN'},
        ],
    }), mode=haystackapi.MODE_JSON)
    _check_number(grid)


def test_number_csv():
    grid = haystackapi.parse(textwrap.dedent('''
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
        "Not a Number",NaN''')[1:], mode=haystackapi.MODE_CSV)
    _check_number(grid)


def test_string_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        str,strExample
        "Empty",""
        "Basic","Simple string"
        "Escaped","This\\tIs\\nA\\r\\"Test\\"\\\\\\$"
        ''')[1:])
    assert len(grid) == 3
    assert grid[0]['strExample'] == ''
    assert grid[1]['strExample'] == 'Simple string'
    assert grid[2]['strExample'] == 'This\tIs\nA\r"Test"\\$'


def test_string_json():
    grid = haystackapi.parse(json.dumps({
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
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 4
    assert grid.pop(0)['strExample'] == ''
    assert grid.pop(0)['strExample'] == 'a string'
    assert grid.pop(0)['strExample'] == 'an explicit string'
    assert grid.pop(0)['strExample'] == 'string:with:colons'


def test_string_csv():
    grid = haystackapi.parse(json.dumps({
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
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 4
    assert grid.pop(0)['strExample'] == ''
    assert grid.pop(0)['strExample'] == 'a string'
    assert grid.pop(0)['strExample'] == 'an explicit string'
    assert grid.pop(0)['strExample'] == 'string:with:colons'


def test_uri_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        uri
        `http://www.vrt.com.au`
        ''')[1:])
    assert len(grid) == 1
    assert grid[0]['uri'] == haystackapi.Uri('http://www.vrt.com.au')


def test_uri_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'uri'},
        ],
        'rows': [
            {'uri': 'u:http://www.vrt.com.au'},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    assert grid[0]['uri'] == haystackapi.Uri('http://www.vrt.com.au')


def test_uri_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        uri
        `http://www.vrt.com.au`''')[1:], mode=haystackapi.MODE_CSV)
    assert len(grid) == 1
    assert grid[0]['uri'] == haystackapi.Uri('http://www.vrt.com.au')


def test_ref_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        str,ref
        "Basic",@a-basic-ref
        "With value",@reference "With value"
        ''')[1:])
    assert len(grid) == 2
    assert grid[0]['ref'] == haystackapi.Ref('a-basic-ref')
    assert grid[1]['ref'] == haystackapi.Ref('reference', 'With value')


def test_ref_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'str'},
            {'name': 'ref'},
        ],
        'rows': [
            {'str': 'Basic', 'ref': 'r:a-basic-ref'},
            {'str': 'With value', 'ref': 'r:reference With value'},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 2
    assert grid[0]['ref'] == haystackapi.Ref('a-basic-ref')
    assert grid[1]['ref'] == haystackapi.Ref('reference', 'With value')


def test_ref_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        str,ref
        "Basic",@a-basic-ref
        "With value",@reference With value''')[1:],
                             mode=haystackapi.MODE_CSV)
    assert len(grid) == 2
    assert grid[0]['ref'] == haystackapi.Ref('a-basic-ref')
    assert grid[1]['ref'] == haystackapi.Ref('reference', 'With value')


def test_date_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        date
        2010-03-13
        ''')[1:])
    assert len(grid) == 1
    assert isinstance(grid[0]['date'], datetime.date)
    assert grid[0]['date'] == datetime.date(2010, 3, 13)


def test_date_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'date'},
        ],
        'rows': [
            {'date': 'd:2010-03-13'},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    assert isinstance(grid[0]['date'], datetime.date)
    assert grid[0]['date'] == datetime.date(2010, 3, 13)


def test_date_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        date
        2010-03-13''')[1:],
                             mode=haystackapi.MODE_CSV)
    assert len(grid) == 1
    assert isinstance(grid[0]['date'], datetime.date)
    assert grid[0]['date'] == datetime.date(2010, 3, 13)


def test_time_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        time
        08:12:05
        08:12:05.5
        ''')[1:])
    assert len(grid) == 2
    assert isinstance(grid[0]['time'], datetime.time)
    assert grid[0]['time'] == datetime.time(8, 12, 5)
    assert isinstance(grid[1]['time'], datetime.time)
    assert grid[1]['time'] == datetime.time(8, 12, 5, 500000)


def test_time_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'time'},
        ],
        'rows': [
            {'time': 'h:08:12'},
            {'time': 'h:08:12:05'},
            {'time': 'h:08:12:05.5'},
        ],
    }), mode=haystackapi.MODE_JSON)
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


def test_time_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        time
        08:12
        08:12:05
        08:12:05.5''')[1:], mode=haystackapi.MODE_CSV)
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


def test_datetime_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        datetime
        2010-11-28T07:23:02.500-08:00 Los_Angeles
        2010-11-28T23:19:29.500+08:00 Taipei
        2010-11-28T18:21:58+03:00 GMT-3
        2010-11-28T12:22:27-03:00 GMT+3
        2010-01-08T05:00:00Z UTC
        2010-01-08T05:00:00Z
        ''')[1:])
    _check_datetime(grid)


def test_datetime_json():
    grid = haystackapi.parse(json.dumps({
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
    }), mode=haystackapi.MODE_JSON)
    _check_datetime(grid)


def test_datetime_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        datetime
        2010-11-28T07:23:02.500-08:00 Los_Angeles
        2010-11-28T23:19:29.500+08:00 Taipei
        2010-11-28T18:21:58+03:00 GMT-3
        2010-11-28T12:22:27-03:00 GMT+3
        2010-01-08T05:00:00Z UTC
        2010-01-08T05:00:00Z''')[1:], mode=haystackapi.MODE_CSV)
    _check_datetime(grid)


def test_list_v2_zinc():
    try:
        haystackapi.parse(textwrap.dedent('''
            ver:"2.0"
            ix,list, dis
            00,[], "An empty list"
            01,[N], "A list with a NULL"
            ''')[1:])
        assert False, 'Project Haystack 2.0 does not support lists'
    except haystackapi.zincparser.ZincParseException:
        pass


def test_list_v2_json():
    # Version 2.0 does not support lists
    try:
        haystackapi.parse(json.dumps({
            'meta': {'ver': '2.0'},
            'cols': [
                {'name': 'list'},
            ],
            'rows': [
                {'list': ['s:my list', None, True, 'n:1234']}
            ]
        }), mode=haystackapi.MODE_JSON)
        assert False, 'Project Haystack 2.0 does not support lists'
    except ValueError:
        pass


def test_list_v3_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
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
        ''')[1:])
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
    assert grid[6]['list'] == [haystackapi.Quantity(3.14, unit='rad'),
                               haystackapi.Quantity(180, unit='°')]
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
                                haystackapi.Quantity(3.14, unit='rad'),
                                "a"]
    assert grid[12]['list'] == [1.0, 2.0, 3.0, 4.0]
    assert grid[13]['list'] == [1.0, 2.0, 3.0, 4.0]
    assert grid[14]['list'] == [[1.0, 2.0, 3.0], ["a", "b", "c"]]


def test_list_v3_json():
    # Simpler test case than the ZINC one, since the Python JSON parser
    # will take care of the elements for us.
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'list'},
        ],
        'rows': [
            {'list': ['s:my list', None, True, 'n:1234']}
        ]
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    lst = grid[0]['list']
    assert isinstance(lst, list)
    assert len(lst) == 4
    assert lst[0] == 'my list'
    assert_is(lst[1], None)
    assert_is(lst[2], True)
    assert lst[3] == 1234.0


def test_list_v3_csv():
    # Simpler test case than the ZINC one, since the Python JSON parser
    # will take care of the elements for us.
    grid = haystackapi.parse(textwrap.dedent('''
        ix,list,
        00,"[]","An empty list"
        01,"[N]","A list with a NULL"
        02,"[T,F]","Booleans in a list"
        03,"[1,2,3]","Integers"
        04,"[1.1,2.2,3.3]","Floats"
        05,"[1.1e3,2.2e6,3.3e9]","Exponential floats"
        06,"[3.14rad,180°]","Quantities"
        07,"[""a"",""b"",""c""]","Strings"
        08,"[1970-01-01,2000-01-01,2030-01-01]","Dates"
        09,"[06:00:00,12:00:00,18:00:00]","Times"
        10,"[1970-01-01T00:00:00Z,1970-01-01T10:00:00+10:00 Brisbane]","Date/Times"
        11,"[N,T,1,1.1,1.1e3,3.14rad,""a""]","Mixed data"
        12,"[  1,  2  ,  3 ,4  ]","Whitespace"
        13,"[1,2,3,4,]","Trailing comma"
        14,"[[1,2,3],[""a"",""b"",""c""]]","Nested lists"
        ''')[1:], mode=haystackapi.MODE_CSV)
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
    assert grid[6]['list'] == [haystackapi.Quantity(3.14, unit='rad'),
                               haystackapi.Quantity(180, unit='°')]
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
                                haystackapi.Quantity(3.14, unit='rad'),
                                "a"]
    assert grid[12]['list'] == [1.0, 2.0, 3.0, 4.0]
    assert grid[13]['list'] == [1.0, 2.0, 3.0, 4.0]
    assert grid[14]['list'] == [[1.0, 2.0, 3.0], ["a", "b", "c"]]


def test_dict_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
        ix,dict,                                                       dis
        00,{},                                                         "An empty dict"
        01,{marker},                                                   "A marker in a dict"
        02,{tag: 1},                                                   "A tag with number in a dict"
        03,{tag: [1,2]},                                               "A tag with list in a dict"
        04,{marker tag: [1,2]},                                        "A marker and tag with list in a dict"
        05,{tag: {marker}},                                            "A tag  with dict in a dict"
        ''')[1:])
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
    grid = haystackapi.parse(json.dumps({
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
    }), mode=haystackapi.MODE_JSON)

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


def test_dict_csv():
    grid = haystackapi.parse(json.dumps({
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
    }), mode=haystackapi.MODE_JSON)
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


def test_bin_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        bin
        Bin(text/plain)
        ''')[1:])

    assert len(grid) == 1
    assert grid[0]['bin'] == haystackapi.Bin('text/plain')


def test_bin_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'bin'},
        ],
        'rows': [
            {'bin': 'b:text/plain'},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    assert grid[0]['bin'] == haystackapi.Bin('text/plain')


def test_dict_invalide_version_zinc():
    try:
        haystackapi.parse('''ver:"2.0"
        ix,dict,                                                       dis
        00,{},                                                         "An empty dict"
        ''')
        assert False
    except ZincParseException:
        pass


def test_xstr_hex_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
        bin
        hex("deadbeef")
        ''')[1:])
    assert len(grid) == 1
    assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'


def test_xstr_hex_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'bin'},
        ],
        'rows': [
            {'bin': 'x:hex:deadbeef'},
        ],
    }), mode=MODE_JSON)
    assert len(grid) == 1
    assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'


def test_xstr_hex_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        bin
        hex("deadbeef")''')[1:], mode=MODE_CSV)
    assert len(grid) == 1
    assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'


def test_xstr_b64_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
        bin
        b64("3q2+7w==")
        ''')[1:])
    assert len(grid) == 1
    assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'


def test_xstr_b64_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'bin'},
        ],
        'rows': [
            {'bin': 'x:b64:3q2+7w=='},
        ],
    }), mode=MODE_JSON)
    assert len(grid) == 1
    assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'


def test_xstr_b64_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        bin
        b64("3q2+7w==")''')[1:], mode=MODE_CSV)
    assert len(grid) == 1
    assert grid[0]['bin'].data == b'\xde\xad\xbe\xef'


def test_coord_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        coord
        C(37.55,-77.45)
        ''')[1:])

    assert len(grid) == 1
    assert grid[0]['coord'] == haystackapi.Coordinate(37.55, -77.45)


def test_coord_json():
    grid = haystackapi.parse(json.dumps({
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'coord'},
        ],
        'rows': [
            {'coord': 'c:37.55,-77.45'},
        ],
    }), mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    assert grid[0]['coord'] == haystackapi.Coordinate(37.55, -77.45)


def test_coord_csv():
    grid = haystackapi.parse(textwrap.dedent('''
        coord
        "C(37.55,-77.45)"
        ''')[1:], mode=haystackapi.MODE_CSV)
    assert len(grid) == 1
    assert grid[0]['coord'] == haystackapi.Coordinate(37.55, -77.45)


def test_multi_grid_zinc():
    # Multiple grids are separated by newlines.
    grid_list = haystackapi.parse('\n'.join([
        SIMPLE_EXAMPLE_ZINC, METADATA_EXAMPLE_ZINC, NULL_EXAMPLE_ZINC]),
        single=False)
    assert len(grid_list) == 3
    _check_simple(grid_list[0])
    _check_metadata(grid_list[1])
    _check_null(grid_list[2])


def test_multi_grid_json():
    # Multiple grids are separated by newlines.
    grid_list = haystackapi.parse([json.dumps(SIMPLE_EXAMPLE_JSON),
                                   json.dumps(METADATA_EXAMPLE_JSON),
                                   json.dumps(NULL_EXAMPLE_JSON)], mode=haystackapi.MODE_JSON, single=False)
    assert len(grid_list) == 3
    _check_simple(grid_list[0])
    _check_metadata(grid_list[1], force_metadata_order=False)
    _check_null(grid_list[2])


def test_multi_grid_csv():
    # Multiple grids are separated by newlines.
    grid_list = haystackapi.parse(list(map(json.dumps, [SIMPLE_EXAMPLE_JSON,
                                                        METADATA_EXAMPLE_JSON,
                                                        NULL_EXAMPLE_JSON])),
                                  mode=haystackapi.MODE_JSON, single=False)
    assert len(grid_list) == 3
    _check_simple(grid_list[0])
    _check_metadata(grid_list[1], force_metadata_order=False)
    _check_null(grid_list[2])


def test_grid_meta_zinc():
    grid = haystackapi.parse('ver:"3.0" '
                             'aString:"aValue" '
                             'aNumber:3.14159 '
                             'aNull:N '
                             'aMarker:M '
                             'anotherMarker '
                             'aQuantity:123Hz '
                             'aDate:2016-01-13 '
                             'aTime:06:44:00 '
                             'aTimestamp:2016-01-13T06:44:00+10:00 Brisbane '
                             'aPlace:C(-27.4725,153.003)\nempty\n')

    assert len(grid) == 0
    meta = grid.metadata
    assert list(meta.keys()) == ['aString', 'aNumber', 'aNull',
                                 'aMarker', 'anotherMarker', 'aQuantity', 'aDate', 'aTime',
                                 'aTimestamp', 'aPlace']
    assert meta['aString'] == 'aValue'
    assert meta['aNumber'] == 3.14159
    assert_is(meta['aNull'], None)
    assert_is(meta['aMarker'], haystackapi.MARKER)
    assert_is(meta['anotherMarker'], haystackapi.MARKER)
    assert isinstance(meta['aQuantity'], haystackapi.Quantity)
    assert meta['aQuantity'].m == 123
    assert meta['aQuantity'].unit == 'Hz'
    assert isinstance(meta['aDate'], datetime.date)
    assert meta['aDate'] == datetime.date(2016, 1, 13)
    assert isinstance(meta['aTime'], datetime.time)
    assert meta['aTime'] == datetime.time(6, 44)
    assert isinstance(meta['aTimestamp'], datetime.datetime)
    assert meta['aTimestamp'] == \
           pytz.timezone('Australia/Brisbane').localize(
               datetime.datetime(2016, 1, 13, 6, 44))
    assert isinstance(meta['aPlace'], haystackapi.Coordinate)
    assert meta['aPlace'].latitude == -27.4725
    assert meta['aPlace'].longitude == 153.003


def test_col_meta_zinc():
    grid = haystackapi.parse('ver:"3.0"\n'
                             'aColumn '
                             'aString:"aValue" '
                             'aNumber:3.14159 '
                             'aNull:N '
                             'aMarker:M '
                             'anotherMarker '
                             'aQuantity:123Hz aDate:2016-01-13 aTime:06:44:00 '
                             'aTimestamp:2016-01-13T06:44:00+10:00 Brisbane '
                             'aPlace:C(-27.4725,153.003)\n')

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
    assert_is(meta['aMarker'], haystackapi.MARKER)
    assert_is(meta['anotherMarker'], haystackapi.MARKER)
    assert isinstance(meta['aQuantity'], haystackapi.Quantity)
    assert meta['aQuantity'].m == 123
    assert meta['aQuantity'].unit == 'Hz'
    assert isinstance(meta['aDate'], datetime.date)
    assert meta['aDate'] == datetime.date(2016, 1, 13)
    assert isinstance(meta['aTime'], datetime.time)
    assert meta['aTime'] == datetime.time(6, 44)
    assert isinstance(meta['aTimestamp'], datetime.datetime)
    assert meta['aTimestamp'] == \
           pytz.timezone('Australia/Brisbane').localize(
               datetime.datetime(2016, 1, 13, 6, 44))
    assert isinstance(meta['aPlace'], haystackapi.Coordinate)
    assert meta['aPlace'].latitude == -27.4725
    assert meta['aPlace'].longitude == 153.003


def test_too_many_cells_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        col1, col2, col3
        "Val1", "Val2", "Val3", "Val4", "Val5"
        ''')[1:])
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['col1', 'col2', 'col3']

    row = grid[0]
    assert set(row.keys()) == {'col1', 'col2', 'col3'}
    assert row['col1'] == 'Val1'
    assert row['col2'] == 'Val2'
    assert row['col3'] == 'Val3'


def test_nodehaystack_01_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
        fooBar33
        ''')[1:])
    assert len(grid) == 0
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['fooBar33']


def test_nodehaystack_02_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0" tag foo:"bar"
        xyz
        "val"
        ''')[1:])
    assert len(grid) == 1
    assert list(grid.metadata.keys()) == ['tag', 'foo']
    assert_is(grid.metadata['tag'], haystackapi.MARKER)
    assert grid.metadata['foo'] == 'bar'
    assert list(grid.column.keys()) == ['xyz']
    assert grid[0]['xyz'] == 'val'


def test_nodehaystack_03_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        val
        N
        ''')[1:])
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['val']
    assert 'val' not in grid[0]


def test_nodehaystack_04_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        a,b
        1,2
        3,4
        ''')[1:])
    assert len(grid) == 2
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b']
    assert grid[0]['a'] == 1
    assert grid[0]['b'] == 2
    assert grid[1]['a'] == 3
    assert grid[1]['b'] == 4


def test_nodehaystack_05_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"3.0"
        a,    b,      c,      d
        T,    F,      N,   -99
        2.3,  -5e-10, 2.4e20, 123e-10
        "",   "a",   "\\" \\\\ \\t \\n \\r", "\\uabcd"
        `path`, @12cbb082-0c02ae73, 4s, -2.5min
        M,R,hex("010203"),hex("010203")
        2009-12-31, 23:59:01, 01:02:03.123, 2009-02-03T04:05:06Z
        INF, -INF, "", NaN
        C(12,-34),C(0.123,-.789),C(84.5,-77.45),C(-90,180)
        ''')[1:])
    assert len(grid) == 8
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b', 'c', 'd']
    row = grid.pop(0)
    assert row['a']
    assert not row['b']
    assert 'c' not in row
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
    assert row['d'] == '\uabcd'
    row = grid.pop(0)
    assert row['a'] == haystackapi.Uri('path')
    assert row['b'] == haystackapi.Ref('12cbb082-0c02ae73')
    assert row['c'] == haystackapi.Quantity(4, 's')
    assert row['d'] == haystackapi.Quantity(-2.5, 'min')
    row = grid.pop(0)
    assert_is(row['a'], haystackapi.MARKER)
    assert_is(row['b'], haystackapi.REMOVE)
    assert row['c'] == XStr('hex', '010203')
    assert row['d'] == XStr('hex', '010203')
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
    assert row['a'] == haystackapi.Coordinate(12, -34)
    assert row['b'] == haystackapi.Coordinate(.123, -.789)
    assert row['c'] == haystackapi.Coordinate(84.5, -77.45)
    assert row['d'] == haystackapi.Coordinate(-90, 180)


def test_nodehaystack_06_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        foo
        `foo$20bar`
        `foo\\`bar`
        `file \\#2`
        "$15"
        ''')[1:])
    assert len(grid) == 4
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['foo']
    row = grid.pop(0)
    assert row['foo'] == haystackapi.Uri('foo$20bar')
    row = grid.pop(0)
    assert row['foo'] == haystackapi.Uri('foo`bar')
    row = grid.pop(0)
    assert row['foo'] == haystackapi.Uri('file \\#2')
    row = grid.pop(0)
    assert row['foo'] == '$15'


def test_nodehaystack_07_zinc():
    grid = haystackapi.parse(textwrap.dedent(u'''
        ver:"2.0"
        a, b
        -3.1kg,4kg
        5%,3.2%
        5kWh/ft\u00b2,-15kWh/m\u00b2
        123e+12kJ/kg_dry,74\u0394\u00b0F
        ''')[1:])
    assert len(grid) == 4
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b']
    row = grid.pop(0)
    assert row['a'] == haystackapi.Quantity(-3.1, 'kg')
    assert row['b'] == haystackapi.Quantity(4, 'kg')
    row = grid.pop(0)
    assert row['a'] == haystackapi.Quantity(5, '%')
    assert row['b'] == haystackapi.Quantity(3.2, '%')
    row = grid.pop(0)
    assert row['a'] == haystackapi.Quantity(5, 'kWh/ft\u00b2')
    assert row['b'] == haystackapi.Quantity(-15, 'kWh/m\u00b2')
    row = grid.pop(0)
    assert row['a'] == haystackapi.Quantity(123e12, 'kJ/kg_dry')
    assert row['b'] == haystackapi.Quantity(74, '\u0394\u00b0F')


def test_nodehaystack_08_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        a,b
        2010-03-01T23:55:00.013-05:00 GMT+5,2010-03-01T23:55:00.013+10:00 GMT-10
        ''')[1:])
    assert len(grid) == 1
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b']
    row = grid.pop(0)
    assert row['a'] == haystackapi.zoneinfo.timezone('GMT+5').localize(
        datetime.datetime(2010, 3, 1, 23, 55, 0, 13000))
    assert row['b'] == haystackapi.zoneinfo.timezone('GMT-10').localize(
        datetime.datetime(2010, 3, 1, 23, 55, 0, 13000))


def test_nodehaystack_09_zinc():
    grid = haystackapi.parse(textwrap.dedent(u'''
        ver:"2.0" a: 2009-02-03T04:05:06Z foo b: 2010-02-03T04:05:06Z UTC bar c: 2009-12-03T04:05:06Z London baz
        a
        3.814697265625E-6
        2010-12-18T14:11:30.924Z
        2010-12-18T14:11:30.925Z UTC
        2010-12-18T14:11:30.925Z London
        45$
        33\u00a3
        @12cbb08e-0c02ae73
        7.15625E-4kWh/ft\u00b2
        ''')[1:])
    assert len(grid) == 8
    assert list(grid.metadata.keys()) == ['a', 'foo', 'b', 'bar', 'c', 'baz']
    assert grid.metadata['a'] == pytz.utc.localize(
        datetime.datetime(2009, 2, 3, 4, 5, 6))
    assert grid.metadata['b'] == pytz.utc.localize(
        datetime.datetime(2010, 2, 3, 4, 5, 6))
    assert grid.metadata['c'] == pytz.timezone('Europe/London').localize(
        datetime.datetime(2009, 12, 3, 4, 5, 6))
    assert_is(grid.metadata['foo'], haystackapi.MARKER)
    assert_is(grid.metadata['bar'], haystackapi.MARKER)
    assert_is(grid.metadata['baz'], haystackapi.MARKER)
    assert list(grid.column.keys()) == ['a']
    assert grid.pop(0)['a'] == 3.814697265625E-6
    assert grid.pop(0)['a'] == pytz.utc.localize(
        datetime.datetime(2010, 12, 18, 14, 11, 30, 924000))
    assert grid.pop(0)['a'] == pytz.utc.localize(
        datetime.datetime(2010, 12, 18, 14, 11, 30, 925000))
    assert grid.pop(0)['a'] == pytz.timezone('Europe/London').localize(
        datetime.datetime(2010, 12, 18, 14, 11, 30, 925000))
    assert grid.pop(0)['a'] == haystackapi.Quantity(45, '$')
    assert grid.pop(0)['a'] == haystackapi.Quantity(33, '\u00a3')
    assert grid.pop(0)['a'] == haystackapi.Ref('12cbb08e-0c02ae73')
    assert grid.pop(0)['a'] == haystackapi.Quantity(7.15625E-4, 'kWh/ft\u00b2')


def test_nodehaystack_10_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0" bg: Bin(image/jpeg) mark
        file1 dis:"F1" icon: Bin(image/gif),file2 icon: Bin(image/jpg)
        Bin(text/plain),N
        4,Bin(image/png)
        Bin(text/html; a=foo; bar="sep"),Bin(text/html; charset=utf8)
        ''')[1:])
    assert len(grid) == 3
    assert list(grid.metadata.keys()) == ['bg', 'mark']
    assert grid.metadata['bg'] == haystackapi.Bin('image/jpeg')
    assert_is(grid.metadata['mark'], haystackapi.MARKER)
    assert list(grid.column.keys()) == ['file1', 'file2']
    assert list(grid.column['file1'].keys()) == ['dis', 'icon']
    assert grid.column['file1']['dis'] == 'F1'
    assert grid.column['file1']['icon'] == haystackapi.Bin('image/gif')
    assert list(grid.column['file2'].keys()) == ['icon']
    assert grid.column['file2']['icon'] == haystackapi.Bin('image/jpg')
    row = grid.pop(0)
    assert row['file1'] == haystackapi.Bin('text/plain')
    assert 'file2' not in row
    row = grid.pop(0)
    assert row['file1'] == 4
    assert row['file2'] == haystackapi.Bin('image/png')
    row = grid.pop(0)
    assert row['file1'] == haystackapi.Bin('text/html; a=foo; bar="sep"')
    assert row['file2'] == haystackapi.Bin('text/html; charset=utf8')


def test_nodehaystack_11_zinc():
    grid = haystackapi.parse(textwrap.dedent('''
        ver:"2.0"
        a, b, c
        , 1, 2
        3, , 5
        6, 7_000,
        ,,10
        ,,
        14,,
        ''')[1:])
    assert len(grid) == 6
    assert len(grid.metadata) == 0
    assert list(grid.column.keys()) == ['a', 'b', 'c']
    row = grid.pop(0)
    assert 'a' not in row
    assert row['b'] == 1
    assert row['c'] == 2
    row = grid.pop(0)
    assert row['a'] == 3
    assert 'b' not in row
    assert row['c'] == 5
    row = grid.pop(0)
    assert row['a'] == 6
    assert row['b'] == 7000
    assert 'c' not in row
    row = grid.pop(0)
    assert 'a' not in row
    assert 'b' not in row
    assert row['c'] == 10
    row = grid.pop(0)
    assert 'a' not in row
    assert 'b' not in row
    assert 'c' not in row
    row = grid.pop(0)
    assert row['a'] == 14
    assert 'b' not in row
    assert 'c' not in row


def test_scalar_bytestring_zinc():
    assert haystackapi.parse_scalar(b'"Testing"',
                                    mode=haystackapi.MODE_ZINC) \
           == "Testing"
    assert haystackapi.parse_scalar(b'50Hz',
                                    mode=haystackapi.MODE_ZINC) \
           == haystackapi.Quantity(50, unit='Hz')


def test_scalar_version_zinc():
    # This should forbid us trying to parse a list.
    try:
        haystackapi.parse_scalar('[1,2,3]', mode=haystackapi.MODE_ZINC,
                                 version=haystackapi.VER_2_0)
        assert False, 'Version was ignored'
    except haystackapi.zincparser.ZincParseException:
        pass


def test_scalar_version_json():
    # This should forbid us trying to parse a list.
    try:
        res = haystackapi.parse_scalar('[ "n:1","n:2","n:3" ]',
                                       mode=haystackapi.MODE_JSON, version=haystackapi.VER_2_0)
        assert False, 'Version was ignored; got %r' % res
    except ValueError:
        pass



# Scalar parsing tests… no need to be exhaustive here because the grid tests
# cover the underlying cases.  This is basically checking that bytestring decoding
# works and versions are passed through.

def test_scalar_simple_zinc():
    assert haystackapi.parse_scalar('"Testing"', mode=haystackapi.MODE_ZINC) \
           == "Testing"
    assert haystackapi.parse_scalar('50Hz', mode=haystackapi.MODE_ZINC) \
           == haystackapi.Quantity(50, unit='Hz')


def test_scalar_simple_json():
    assert haystackapi.parse_scalar('"s:Testing"', mode=haystackapi.MODE_JSON) \
           == "Testing"
    assert haystackapi.parse_scalar('"n:50 Hz"', mode=haystackapi.MODE_JSON) \
           == haystackapi.Quantity(50, unit='Hz')


def test_scalar_simple_csv():
    assert haystackapi.parse_scalar('Testing', mode=haystackapi.MODE_CSV) \
           == "Testing"
    assert haystackapi.parse_scalar('50Hz', mode=haystackapi.MODE_CSV) \
           == haystackapi.Quantity(50, unit='Hz')


def test_scalar_preparsed_json():
    assert haystackapi.parse_scalar('s:Testing', mode=haystackapi.MODE_JSON) \
           == "Testing"
    assert haystackapi.parse_scalar('n:50 Hz', mode=haystackapi.MODE_JSON) \
           == haystackapi.Quantity(50, unit='Hz')


def test_scalar_bytestring_json():
    assert haystackapi.parse_scalar(b'"s:Testing"',
                                    mode=haystackapi.MODE_JSON) \
           == "Testing"
    assert haystackapi.parse_scalar(b'"n:50 Hz"',
                                    mode=haystackapi.MODE_JSON) \
           == haystackapi.Quantity(50, unit='Hz')


def test_str_version():
    # This should assume v3.0, and parse successfully.
    val = haystackapi.parse_scalar('[1,2,3]', mode=haystackapi.MODE_ZINC,
                                   version='2.5')
    assert val == [1.0, 2.0, 3.0]


def test_malformed_grid_meta_zinc():
    try:
        haystackapi.parse(textwrap.dedent('''
            ver:"2.0" ThisIsNotATag
            empty
            
            ''')[1:])
        assert False, 'Parsed a clearly invalid grid'
    except haystackapi.zincparser.ZincParseException as zpe:
        assert zpe.line == 1
        assert zpe.col == 11


def test_malformed_col_meta_zinc():
    try:
        haystackapi.parse(textwrap.dedent('''
            ver:"2.0"
            c1 goodSoFar, c2 WHOOPSIE
            ,
            ''')[1:])
        assert False, 'Parsed a clearly invalid grid'
    except haystackapi.zincparser.ZincParseException as zpe:
        assert zpe.line == 2
        assert zpe.col == 18


def test_malformed_row_zinc():
    try:
        haystackapi.parse(textwrap.dedent('''
            ver:"2.0"
            c1, c2
            1, "No problems here"
            2, We should fail here
            3, "No issue, but we won't get this far"
            4, We won't see this error
            ''')[1:])
        assert False, 'Parsed a clearly invalid grid'
    except haystackapi.zincparser.ZincParseException as zpe:
        assert zpe.line == 4
        assert zpe.col == 1



def test_malformed_scalar_zinc():
    # This should always raise an error after logging
    try:
        haystackapi.parse_scalar(12341234, mode=haystackapi.MODE_ZINC)  # type: ignore
        assert False, 'Should have failed'
    except AttributeError:
        pass


def test_grid_in_grid_zinc():
    grid = haystackapi.parse('ver:"3.0"\n'
                             'inner\n'
                             '<<ver:"3.0"\n'
                             'comment\n'
                             '"A innergrid"\n'
                             '>>\n', mode=haystackapi.MODE_ZINC)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert inner[0]['comment'] == 'A innergrid'


def test_grid_in_grid_json():
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
    grid = haystackapi.parse(xstr, mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert inner[0]['comment'] == 'A innergrid'


def test_grid_in_grid_csv():
    xstr = textwrap.dedent('''
        inner
        "<<ver:""3.0""
        comment
        ""A innergrid""
        >>"
        '''[1:])
    grid = haystackapi.parse(xstr, mode=haystackapi.MODE_CSV)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert inner[0]['comment'] == 'A innergrid'


def test_grid_in_grid_in_grid_zinc():
    grid = haystackapi.parse('ver:"3.0"\n'
                             'inner\n'
                             '<<ver:"3.0"\n'
                             'innerinner\n'
                             '<<ver:"3.0"\n'
                             'comment\n'
                             '"A innerinnergrid"\n'
                             '>>\n'
                             '>>\n', mode=haystackapi.MODE_ZINC)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert isinstance(inner[0]['innerinner'], Grid)
    assert inner[0]['innerinner'][0]['comment'] == "A innerinnergrid"


def test_grid_in_grid_in_grid_json():
    str_grid = \
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
    grid = haystackapi.parse(str_grid, mode=haystackapi.MODE_JSON)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert isinstance(inner[0]['innerinner'], Grid)
    assert inner[0]['innerinner'][0]['comment'] == "A innerinnergrid"


def test_grid_in_grid_in_grid_csv():
    str_grid = textwrap.dedent('''
        inner
        "<<ver:""3.0""
        innerinner
        <<ver:""3.0""
        comment
        ""A innerinnergrid""
        >>
        >>"'''[1:])
    grid = haystackapi.parse(str_grid, mode=haystackapi.MODE_CSV)
    assert len(grid) == 1
    inner = grid[0]['inner']
    assert isinstance(inner, Grid)
    assert len(inner) == 1
    assert isinstance(inner[0]['innerinner'], Grid)
    assert inner[0]['innerinner'][0]['comment'] == "A innerinnergrid"



def test_unescape():
    assert _unescape("a\\nb") == "a\nb"
