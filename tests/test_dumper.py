# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import datetime
import json
import textwrap
from csv import reader
from typing import cast, List

import pytz

import shaystack
from shaystack import dump_scalar, MODE_TRIO, MODE_ZINC, MODE_CSV, Entity
from .test_parser import SIMPLE_EXAMPLE_ZINC, SIMPLE_EXAMPLE_JSON, \
    METADATA_EXAMPLE_JSON, SIMPLE_EXAMPLE_CSV, METADATA_EXAMPLE_CSV, SIMPLE_EXAMPLE_TRIO, \
    SIMPLE_EXAMPLE_HAYSON, METADATA_EXAMPLE_HAYSON

# The metadata example is a little different, as we generate the grid without
# spaces around the commas.
METADATA_EXAMPLE = '''
ver:"2.0" database:"test" dis:"Site Energy Summary"
siteName dis:"Sites",val dis:"Value" unit:"kW"
"Site 1",356.214kW
"Site 2",463.028kW
'''[1:]

grid_full_types = shaystack.Grid(version=shaystack.VER_2_0)
grid_full_types.column['comment'] = {}
grid_full_types.column['value'] = {}
grid_full_types.extend([
    {
        'comment': 'A null value',
        'value': None,
    },
    {
        'comment': 'A marker',
        'value': shaystack.MARKER,
    },
    {
        'comment': 'A "remove" object',
        'value': shaystack.REMOVE,
    },
    {
        'comment': 'A boolean, indicating False',
        'value': False,
    },
    {
        'comment': 'A boolean, indicating True',
        'value': True,
    },
    {
        'comment': 'A reference, without value',
        'value': shaystack.Ref('a-ref'),
    },
    {
        'comment': 'A reference, with value',
        'value': shaystack.Ref('a-ref', 'a value'),
    },
    {
        'comment': 'A binary blob',
        'value': shaystack.Bin('text/plain'),
    },
    {
        'comment': 'A quantity',
        'value': shaystack.Quantity(500, 'miles'),
    },
    {
        'comment': 'A quantity without unit',
        'value': shaystack.Quantity(500, None),
    },
    {
        'comment': 'A coordinate',
        'value': shaystack.Coordinate(-27.4725, 153.003),
    },
    {
        'comment': 'A URI',
        'value': shaystack.Uri('http://www.example.com#unicode:\u0109\u1000'),
    },
    {
        'comment': 'A string',
        'value': 'This is a test\n'
                 'Line two of test\n'
                 '\tIndented with "quotes", \\backslashes\\\n',
    },
    {
        'comment': 'A unicode string',
        'value': 'This is a Unicode characters: \u0109\u1000',
    },
    {
        'comment': 'A date',
        'value': datetime.date(2016, 1, 13),
    },
    {
        'comment': 'A time',
        'value': datetime.time(7, 51, 43, microsecond=12345),
    },
    {
        'comment': 'A timestamp (non-UTC)',
        'value': pytz.timezone('Europe/Berlin').localize(
            datetime.datetime(2016, 1, 13, 7, 51, 42, 12345)),
    },
    {
        'comment': 'A timestamp (UTC)',
        'value': pytz.timezone('UTC').localize(
            datetime.datetime(2016, 1, 13, 7, 51, 42, 12345)),
    },
])


def make_simple_grid(version=shaystack.VER_2_0):
    """
    Args:
        version:
    """
    grid = shaystack.Grid(version=version)
    grid.column['firstName'] = {}
    grid.column['bday'] = {}
    grid.extend([
        {
            'firstName': 'Jack',
            'bday': datetime.date(1973, 7, 23),
        },
        {
            'firstName': 'Jill',
            'bday': datetime.date(1975, 11, 15),
        },
    ])
    return grid


def test_simple_zinc():
    grid = make_simple_grid()
    grid_str = shaystack.dump(grid, MODE_ZINC)
    assert grid_str == SIMPLE_EXAMPLE_ZINC


def test_simple_trio():
    grid = make_simple_grid()
    grid_str = shaystack.dump(grid, MODE_TRIO)
    assert grid_str == SIMPLE_EXAMPLE_TRIO


def test_simple_json():
    grid = make_simple_grid()
    grid_json = json.loads(shaystack.dump(grid, mode=shaystack.MODE_JSON))
    assert grid_json == SIMPLE_EXAMPLE_JSON


def test_simple_hayson():
    grid = make_simple_grid()
    grid_json = json.loads(shaystack.dump(grid, mode=shaystack.MODE_HAYSON))
    assert grid_json == SIMPLE_EXAMPLE_HAYSON


def test_simple_csv():
    grid = make_simple_grid()
    grid_csv = shaystack.dump(grid, mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == SIMPLE_EXAMPLE_CSV


def make_metadata_grid(version=shaystack.VER_2_0):
    """
    Args:
        version:
    """
    grid = shaystack.Grid(version=version)
    grid.metadata['database'] = 'test'
    grid.metadata['dis'] = 'Site Energy Summary'
    grid.column['siteName'] = {'dis': 'Sites'}
    grid.column['val'] = shaystack.MetadataObject()
    grid.column['val']['dis'] = 'Value'
    grid.column['val']['unit'] = 'kW'
    grid.extend([
        {
            'siteName': 'Site 1',
            'val': shaystack.Quantity(356.214, 'kW'),
        },
        {
            'siteName': 'Site 2',
            'val': shaystack.Quantity(463.028, 'kW'),
        },
    ])
    return grid


def test_metadata_zinc():
    grid = make_metadata_grid()
    grid_str = shaystack.dump(grid)
    assert grid_str == METADATA_EXAMPLE


def test_metadata_json():
    grid = make_metadata_grid()
    grid_json = json.loads(shaystack.dump(grid, mode=shaystack.MODE_JSON))
    assert grid_json == METADATA_EXAMPLE_JSON


def test_metadata_hayson():
    grid = make_metadata_grid()
    grid_json = json.loads(shaystack.dump(grid, mode=shaystack.MODE_HAYSON))
    assert grid_json == METADATA_EXAMPLE_HAYSON


def test_metadata_csv():
    grid = make_metadata_grid()
    grid_csv = shaystack.dump(grid, mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == METADATA_EXAMPLE_CSV


def make_grid_meta(version=shaystack.VER_2_0):
    """
    Args:
        version:
    """
    grid = shaystack.Grid(version=version)
    grid.metadata['aString'] = 'aValue'
    grid.metadata['aNumber'] = 3.14159
    grid.metadata['aNull'] = None
    grid.metadata['aMarker'] = shaystack.MARKER
    grid.metadata['aQuantity'] = shaystack.Quantity(123, 'Hz')
    grid.column['empty'] = {}
    return grid


def test_grid_meta():
    grid_str = shaystack.dump(make_grid_meta())
    assert grid_str == '''
ver:"2.0" aString:"aValue" aNumber:3.14159 aNull:N aMarker aQuantity:123Hz
empty
'''[1:]


def test_grid_meta_json():
    grid_json = json.loads(shaystack.dump(make_grid_meta(),
                                          mode=shaystack.MODE_JSON))
    assert grid_json == {
        'meta': {
            'ver': '2.0',
            'aString': 's:aValue',
            'aNumber': 'n:3.141590',
            'aNull': None,
            'aMarker': 'm:',
            'aQuantity': 'n:123.000000 Hz',
        },
        'cols': [
            {'name': 'empty'},
        ],
        'rows': [],
    }


def test_grid_meta_hayson():
    grid_hayson = json.loads(shaystack.dump(make_grid_meta(),
                                          mode=shaystack.MODE_HAYSON))

    assert grid_hayson == {
        'meta': {
            'ver': '2.0',
            'aString': 'aValue',
            'aNumber': 3.141590,
            'aNull': None,
            'aMarker': {'_kind': 'Marker'},
            'aQuantity': {'_kind': 'Num', 'val': 123.000000, 'unit': 'Hz'},
        },
        'cols': [
            {'name': 'empty'},
        ],
        'rows': [],
    }


def test_grid_meta_csv():
    grid_csv = shaystack.dump(make_grid_meta(), mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == 'empty\n'


def make_col_meta(version=shaystack.VER_2_0):
    """
    Args:
        version:
    """
    grid = shaystack.Grid(version=version)
    col_meta = shaystack.MetadataObject()
    col_meta['aString'] = 'aValue'
    col_meta['aNumber'] = 3.14159
    col_meta['aNull'] = None
    col_meta['aMarker'] = shaystack.MARKER
    col_meta['aQuantity'] = shaystack.Quantity(123, 'Hz')
    grid.column['empty'] = col_meta
    return grid


def test_col_meta_zinc():
    grid_str = shaystack.dump(make_col_meta(), mode=shaystack.MODE_ZINC)
    assert grid_str == '''
ver:"2.0"
empty aString:"aValue" aNumber:3.14159 aNull:N aMarker aQuantity:123Hz
'''[1:]


def test_col_meta_json():
    grid_json = json.loads(shaystack.dump(make_col_meta(),
                                          mode=shaystack.MODE_JSON))
    assert grid_json == {
        'meta': {
            'ver': '2.0',
        },
        'cols': [
            {'name': 'empty',
             'aString': 's:aValue',
             'aNumber': 'n:3.141590',
             'aNull': None,
             'aMarker': 'm:',
             'aQuantity': 'n:123.000000 Hz',
             },
        ],
        'rows': [],
    }


def test_col_meta_hayson():
    grid_json = json.loads(shaystack.dump(make_col_meta(),
                                          mode=shaystack.MODE_HAYSON))
    assert grid_json == {
        'meta': {
            'ver': '2.0',
        },
        'cols': [
            {'name': 'empty',
             'aString': 'aValue',
             'aNumber': 3.141590,
             'aNull': None,
             'aMarker': {'_kind': 'Marker'},
             'aQuantity': {'_kind': 'Num', 'val': 123.000000, 'unit': 'Hz'},
             },
        ],
        'rows': [],
    }


def test_col_meta_csv():
    grid_csv = shaystack.dump(make_col_meta(), mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == 'empty\n'


def test_data_types_zinc_v2():
    grid_str = shaystack.dump(grid_full_types, mode=shaystack.MODE_ZINC)
    ref_str = '''
ver:"2.0"
comment,value
"A null value",N
"A marker",M
"A \\"remove\\" object",R
"A boolean, indicating False",F
"A boolean, indicating True",T
"A reference, without value",@a-ref
"A reference, with value",@a-ref "a value"
"A binary blob",Bin(text/plain)
"A quantity",500miles
"A quantity without unit",500
"A coordinate",C(-27.472500,153.003000)
"A URI",`http://www.example.com#unicode:\u0109\u1000`
"A string","This is a test\\nLine two of test\\n\\tIndented with \\"quotes\\", \\\\backslashes\\\\\\n"
"A unicode string","This is a Unicode characters: \u0109\u1000"
"A date",2016-01-13
"A time",07:51:43.012345
"A timestamp (non-UTC)",2016-01-13T07:51:42.012345+01:00 Berlin
"A timestamp (UTC)",2016-01-13T07:51:42.012345+00:00 UTC
'''[1:]
    assert grid_str == ref_str


def test_data_types_json_v2():
    grid_json = json.loads(shaystack.dump(grid_full_types, mode=shaystack.MODE_JSON))
    assert grid_json == \
           {'meta': {'ver': '2.0'},
            'cols': [{'name': 'comment'}, {'name': 'value'}],
            'rows': [
                {'comment': 's:A null value', 'value': None}, {'comment': 's:A marker', 'value': 'm:'},
                {'comment': 's:A "remove" object', 'value': 'x:'},
                {'comment': 's:A boolean, indicating False', 'value': False},
                {'comment': 's:A boolean, indicating True', 'value': True},
                {'comment': 's:A reference, without value', 'value': 'r:a-ref'},
                {'comment': 's:A reference, with value', 'value': 'r:a-ref a value'},
                {'comment': 's:A binary blob', 'value': 'b:text/plain'},
                {'comment': 's:A quantity', 'value': 'n:500.000000 miles'},
                {'comment': 's:A quantity without unit', 'value': 'n:500.000000'},
                {'comment': 's:A coordinate', 'value': 'c:-27.472500,153.003000'},
                {'comment': 's:A URI', 'value': 'u:http://www.example.com#unicode:\u0109\u1000'},
                {'comment': 's:A string',
                 'value': 's:This is a test\nLine two of test\n\tIndented with "quotes", \\backslashes\\\n'},
                {'comment': 's:A unicode string', 'value': 's:This is a Unicode characters: \u0109\u1000'},
                {'comment': 's:A date', 'value': 'd:2016-01-13'},
                {'comment': 's:A time', 'value': 'h:07:51:43.012345'},
                {'comment': 's:A timestamp (non-UTC)', 'value': 't:2016-01-13T07:51:42.012345+01:00 Berlin'},
                {'comment': 's:A timestamp (UTC)', 'value': 't:2016-01-13T07:51:42.012345+00:00 UTC'}]}


def test_data_types_csv_v2():
    grid_csv = shaystack.dump(grid_full_types, mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    ref_str = '''
comment,value
"A null value",
"A marker",✓
"A ""remove"" object",R
"A boolean, indicating False",false
"A boolean, indicating True",true
"A reference, without value",@a-ref
"A reference, with value",@a-ref a value
"A binary blob",Bin(text/plain)
"A quantity",500miles
"A quantity without unit",500
"A coordinate","C(-27.472500,153.003000)"
"A URI","`http://www.example.com#unicode:\u0109\u1000`"
"A string","This is a test\nLine two of test\n\tIndented with ""quotes"", \\backslashes\\\n"
"A unicode string","This is a Unicode characters: \u0109\u1000"
"A date",2016-01-13
"A time",07:51:43.012345
"A timestamp (non-UTC)",2016-01-13T07:51:42.012345+01:00
"A timestamp (UTC)",2016-01-13T07:51:42.012345+00:00
'''[1:]
    assert grid_csv == ref_str


def test_data_types_zinc_v3():
    grid_str = shaystack.dump(grid_full_types, mode=shaystack.MODE_ZINC)
    ref_str = '''
ver:"2.0"
comment,value
"A null value",N
"A marker",M
"A \\"remove\\" object",R
"A boolean, indicating False",F
"A boolean, indicating True",T
"A reference, without value",@a-ref
"A reference, with value",@a-ref "a value"
"A binary blob",Bin(text/plain)
"A quantity",500miles
"A quantity without unit",500
"A coordinate",C(-27.472500,153.003000)
"A URI",`http://www.example.com#unicode:\u0109\u1000`
"A string","This is a test\\nLine two of test\\n\\tIndented with \\"quotes\\", \\\\backslashes\\\\\\n"
"A unicode string","This is a Unicode characters: \u0109\u1000"
"A date",2016-01-13
"A time",07:51:43.012345
"A timestamp (non-UTC)",2016-01-13T07:51:42.012345+01:00 Berlin
"A timestamp (UTC)",2016-01-13T07:51:42.012345+00:00 UTC
'''[1:]
    assert grid_str == ref_str


def test_data_types_trio_v3():
    grid_str = shaystack.dump(grid_full_types, mode=shaystack.MODE_TRIO)
    ref_str = '''
comment: A null value
value: N
---
comment: A marker
value: M
---
comment: "A \\"remove\\" object"
value: R
---
comment: A boolean, indicating False
value: F
---
comment: A boolean, indicating True
value: T
---
comment: A reference, without value
value: @a-ref
---
comment: A reference, with value
value: @a-ref "a value"
---
comment: A binary blob
value: text/plain
---
comment: A quantity
value: 500miles
---
comment: A quantity without unit
value: 500
---
comment: A coordinate
value: C(-27.472500,153.003000)
---
comment: A URI
value: `http://www.example.com#unicode:ĉက`
---
comment: A string
value: 
  This is a test
  Line two of test
  \\tIndented with \\"quotes\\", \\\\backslashes\\\\
---
comment: A unicode string
value: This is a Unicode characters: ĉက
---
comment: A date
value: 2016-01-13
---
comment: A time
value: 07:51:43.012345
---
comment: A timestamp (non-UTC)
value: 2016-01-13T07:51:42.012345+01:00 Berlin
---
comment: A timestamp (UTC)
value: 2016-01-13T07:51:42.012345+00:00 UTC
'''[1:]
    assert grid_str == ref_str


def test_data_types_json_v3():
    grid_json = json.loads(shaystack.dump(grid_full_types, mode=shaystack.MODE_JSON))
    assert grid_json == \
           {'meta': {'ver': '2.0'},
            'cols': [{'name': 'comment'}, {'name': 'value'}],
            'rows':
                [{'comment': 's:A null value', 'value': None},
                 {'comment': 's:A marker', 'value': 'm:'},
                 {'comment': 's:A "remove" object', 'value': 'x:'},
                 {'comment': 's:A boolean, indicating False', 'value': False},
                 {'comment': 's:A boolean, indicating True', 'value': True},
                 {'comment': 's:A reference, without value', 'value': 'r:a-ref'},
                 {'comment': 's:A reference, with value', 'value': 'r:a-ref a value'},
                 {'comment': 's:A binary blob', 'value': 'b:text/plain'},
                 {'comment': 's:A quantity', 'value': 'n:500.000000 miles'},
                 {'comment': 's:A quantity without unit', 'value': 'n:500.000000'},
                 {'comment': 's:A coordinate', 'value': 'c:-27.472500,153.003000'},
                 {'comment': 's:A URI', 'value': 'u:http://www.example.com#unicode:\u0109\u1000'},
                 {'comment': 's:A string',
                  'value': 's:This is a test\nLine two of test\n'
                           '\tIndented with "quotes", \\backslashes\\\n'},
                 {'comment': 's:A unicode string', 'value': 's:This is a Unicode characters: \u0109\u1000'},
                 {'comment': 's:A date', 'value': 'd:2016-01-13'},
                 {'comment': 's:A time', 'value': 'h:07:51:43.012345'},
                 {'comment': 's:A timestamp (non-UTC)',
                  'value': 't:2016-01-13T07:51:42.012345+01:00 Berlin'},
                 {'comment': 's:A timestamp (UTC)',
                  'value': 't:2016-01-13T07:51:42.012345+00:00 UTC'}]}


def test_data_types_hayson_v3():
    grid_json = json.loads(shaystack.dump(grid_full_types, mode=shaystack.MODE_HAYSON))
    assert grid_json == \
           {'meta': {'ver': '2.0'},
            'cols': [{'name': 'comment'}, {'name': 'value'}],
            'rows': [{'comment': 'A null value', 'value': None},
                     {'comment': 'A marker', 'value': {'_kind': 'Marker'}},
                     {'comment': 'A "remove" object', 'value': {'_kind': 'Remove'}},
                     {'comment': 'A boolean, indicating False', 'value': False},
                     {'comment': 'A boolean, indicating True', 'value': True},
                     {'comment': 'A reference, without value',
                      'value': {'_kind': 'Ref', 'val': 'a-ref'}},
                     {'comment': 'A reference, with value',
                      'value': {'_kind': 'Ref', 'dis': 'a value', 'val': 'a-ref'}},
                     {'comment': 'A binary blob',
                      'value': {'_kind': 'Bin', 'val': 'text/plain'}},
                     {'comment': 'A quantity',
                      'value': {'_kind': 'Num', 'unit': 'miles', 'val': 500}},
                     {'comment': 'A quantity without unit', 'value': 500},
                     {'comment': 'A coordinate',
                      'value': {'_kind': 'Coord', 'lat': -27.4725, 'lng': 153.003}},
                     {'comment': 'A URI',
                      'value': {'_kind': 'Uri',
                                'val': 'http://www.example.com#unicode:ĉက'}},
                     {'comment': 'A string',
                      'value': 'This is a test\nLine two of test\n'
                               '\tIndented with "quotes", \\backslashes\\\n'},
                     {'comment': 'A unicode string',
                      'value': 'This is a Unicode characters: ĉက'},
                     {'comment': 'A date',
                      'value': {'_kind': 'Date', 'val': '2016-01-13'}},
                     {'comment': 'A time',
                      'value': {'_kind': 'Time', 'val': '07:51:43.012345'}},
                     {'comment': 'A timestamp (non-UTC)',
                      'value': {'_kind': 'DateTime',
                                'tz': 'Berlin',
                                'val': '2016-01-13T07:51:42.012345+01:00'}},
                     {'comment': 'A timestamp (UTC)',
                      'value': {'_kind': 'DateTime',
                                'tz': 'UTC',
                                'val': '2016-01-13T07:51:42.012345+00:00'}}]}


def test_data_types_csv_v3():
    grid_csv = shaystack.dump(grid_full_types, mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    ref_str = '''
comment,value
"A null value",
"A marker",✓
"A ""remove"" object",R
"A boolean, indicating False",false
"A boolean, indicating True",true
"A reference, without value",@a-ref
"A reference, with value",@a-ref a value
"A binary blob",Bin(text/plain)
"A quantity",500miles
"A quantity without unit",500
"A coordinate","C(-27.472500,153.003000)"
"A URI","`http://www.example.com#unicode:\u0109\u1000`"
"A string","This is a test\nLine two of test\n\tIndented with ""quotes"", \\backslashes\\\n"
"A unicode string","This is a Unicode characters: \u0109\u1000"
"A date",2016-01-13
"A time",07:51:43.012345
"A timestamp (non-UTC)",2016-01-13T07:51:42.012345+01:00
"A timestamp (UTC)",2016-01-13T07:51:42.012345+00:00
'''[1:]
    assert grid_csv == ref_str


def test_scalar_dict_zinc_v3():
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": shaystack.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": shaystack.Ref('a-ref'), "ref2": shaystack.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": shaystack.Quantity(500, 'miles')},
        },
    ])
    grid_str = shaystack.dump(grid, mode=shaystack.MODE_ZINC)
    assert grid_str == ("ver:\"3.0\"\n"
                        "comment,value\n"
                        "\"An empty dict\",{}\n"
                        "\"A marker in a dict\",{marker:M}\n"
                        "\"A references in a dict\",{" +
                        " ".join([str(k) + ":" + str(v)
                                  for k, v in {"ref": "@a-ref", "ref2": "@a-ref"}.items()])
                        .replace("ref2:@a-ref", "ref2:@a-ref \"a value\"") +
                        "}\n"
                        "\"A quantity in a dict\",{quantity:500miles}\n")


# noinspection PyPep8
def test_scalar_dict_trio_v3():
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": shaystack.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": shaystack.Ref('a-ref'), "ref2": shaystack.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": shaystack.Quantity(500, 'miles')},
        },
    ])
    grid_str = shaystack.dump(grid, mode=shaystack.MODE_TRIO)
    # noinspection PyPep8,PyPep8
    ref_str = textwrap.dedent('''
        comment: An empty dict
        value: {}
        ---
        comment: A marker in a dict
        value: {marker:M}
        ---
        comment: A references in a dict
        value: {'''[1:]) + \
              (" ".join([str(k) + ":" + str(v)
                         for k, v in {"ref": "@a-ref", "ref2": "@a-ref"}.items()])
               .replace("ref2:@a-ref", "ref2:@a-ref \"a value\"")) + \
              textwrap.dedent('''
        }
        ---
        comment: A quantity in a dict
        value: {quantity:500miles}
        '''[1:])
    assert grid_str == ref_str


def test_scalar_dict_json_v3():
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": shaystack.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": shaystack.Ref('a-ref'), "ref2": shaystack.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": shaystack.Quantity(500, 'miles')},
        },
    ])
    grid_json = json.loads(shaystack.dump(grid, mode=shaystack.MODE_JSON))
    assert grid_json == {
        'meta': {
            'ver': '3.0'
        },
        'cols': [
            {'name': 'comment'},
            {'name': 'value'},
        ],
        'rows': [
            {
                'comment': "s:An empty dict",
                'value': {}
            },
            {
                'comment': "s:A marker in a dict",
                'value': {'marker': 'm:'}
            },
            {
                'comment': "s:A references in a dict",
                'value': {'ref': 'r:a-ref', 'ref2': 'r:a-ref a value'}
            },
            {
                'comment': "s:A quantity in a dict",
                'value': {"quantity": 'n:500.000000 miles'}
            }
        ]
    }


def test_scalar_dict_hayson_v3():
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": shaystack.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": shaystack.Ref('a-ref'), "ref2": shaystack.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": shaystack.Quantity(500, 'miles')},
        },
    ])
    grid_json = json.loads(shaystack.dump(grid, mode=shaystack.MODE_HAYSON))
    assert grid_json == {
        'cols': [{'name': 'comment'}, {'name': 'value'}],
        'meta': {'ver': '3.0'},
        'rows': [{'comment': 'An empty dict', 'value': {}},
                 {'comment': 'A marker in a dict', 'value': {'marker': {'_kind': 'Marker'}}},
                 {'comment': 'A references in a dict', 'value': {'ref': {'_kind': 'Ref', 'val': 'a-ref'},
                                                                 'ref2': {'_kind': 'Ref',
                                                                          'dis': 'a value',
                                                                          'val': 'a-ref'}}},
                 {'comment': 'A quantity in a dict', 'value':
                     {'quantity': {'_kind': 'Num', 'unit': 'miles', 'val': 500}}
                  }
                 ]
    }


def test_scalar_dict_csv_v3():
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": shaystack.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": shaystack.Ref('a-ref'), "ref2": shaystack.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": shaystack.Quantity(500, 'miles')},
        },
    ])
    grid_csv = shaystack.dump(grid, mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == u'''comment,value
"An empty dict","{}"
"A marker in a dict","{marker:M}"
"A references in a dict","{''' + \
           " ".join([k + ":" + v
                     for k, v in {'ref': '@a-ref', 'ref2': '@a-ref ""a value""'}.items()]) + \
           '''}"
"A quantity in a dict","{quantity:500miles}"
'''


def test_scalar_dict_zinc_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar({"a": "b"},
                              mode=shaystack.MODE_ZINC, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_dict_json_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar({"a": "b"},
                              mode=shaystack.MODE_JSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_dict_hayson_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar({"a": "b"},
                              mode=shaystack.MODE_HAYSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_unknown_zinc():
    try:
        shaystack.dump_scalar(shaystack.VER_2_0,
                              mode=shaystack.MODE_ZINC, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_scalar_unknown_trio():
    try:
        shaystack.dump_scalar(shaystack.VER_3_0,
                              mode=shaystack.MODE_TRIO, version=shaystack.VER_3_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_scalar_unknown_json():
    try:
        shaystack.dump_scalar(shaystack.VER_2_0,
                              mode=shaystack.MODE_JSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_scalar_unknown_hayson():
    try:
        shaystack.dump_scalar(shaystack.VER_2_0,
                              mode=shaystack.MODE_HAYSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_scalar_unknown_csv():
    try:
        shaystack.dump_scalar(shaystack.VER_2_0,
                              mode=shaystack.MODE_CSV, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_list_zinc_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_ZINC)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_list_json_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_list_hayson_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_list_csv_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_CSV)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_dict_zinc_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_ZINC)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_dict_json_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_dict_hayson_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_HAYSON)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_dict_csv_v2():
    try:
        grid = shaystack.Grid(version=shaystack.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        shaystack.dump(grid, mode=shaystack.MODE_CSV)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_scalar_ref_zinc():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert shaystack.dump_scalar(shaystack.Ref('areference', 'a display name'),
                                 mode=shaystack.MODE_ZINC) == '@areference "a display name"'


def test_scalar_ref_trio():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert shaystack.dump_scalar(shaystack.Ref('areference', 'a display name'),
                                 mode=shaystack.MODE_TRIO) == '@areference "a display name"'


def test_scalar_ref_json():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert shaystack.dump_scalar(shaystack.Ref('areference', 'a display name'),
                                 mode=shaystack.MODE_JSON) == '"r:areference a display name"'


def test_scalar_ref_hayson():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert shaystack.dump_scalar(shaystack.Ref('areference', 'a display name'),
                                 mode=shaystack.MODE_HAYSON) == \
           '{"_kind": "Ref", "val": "areference", "dis": "a display name"}'


def test_scalar_ref_csv():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert shaystack.dump_scalar(shaystack.Ref('areference', 'a display name'),
                                 mode=shaystack.MODE_CSV) == '@areference a display name'


def test_scalar_list_zinc_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(["a list is not allowed in v2.0"],
                              mode=shaystack.MODE_ZINC, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_json_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(["a list is not allowed in v2.0"],
                              mode=shaystack.MODE_JSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_hayson_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(["a list is not allowed in v2.0"],
                              mode=shaystack.MODE_HAYSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_zinc():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_ZINC, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_json():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_JSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_hayson():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_HAYSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_csv():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_CSV, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_zinc_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_ZINC, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_json_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_JSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_hayson_ver():
    # Test that versions are respected.
    try:
        print('HEYYYYY', shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_HAYSON, version=shaystack.VER_2_0))
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_HAYSON, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_csv_ver():
    # Test that versions are respected.
    try:
        shaystack.dump_scalar(shaystack.NA,
                              mode=shaystack.MODE_CSV, version=shaystack.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_grid_types_zinc():
    innergrid = shaystack.Grid(version=shaystack.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['inner'] = {}
    grid.extend(cast(List[Entity], [
        {
            'inner': innergrid,
        },
    ]))
    grid_str = shaystack.dump(grid, mode=shaystack.MODE_ZINC)
    assert grid_str == ('ver:"3.0"\n'
                        'inner\n'
                        '<<ver:"3.0"\n'
                        'comment\n'
                        '"A innergrid"\n'
                        '>>\n')


def test_grid_types_trio():
    innergrid = shaystack.Grid(version=shaystack.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['inner'] = {}
    grid.extend(cast(List[Entity], [
        {
            'inner': innergrid,
        },
    ]))
    grid_str = shaystack.dump(grid, mode=shaystack.MODE_TRIO)
    ref_str = textwrap.dedent('''
        inner: Zinc:
          ver:"3.0"
          comment
          "A innergrid"
        '''[1:])
    assert grid_str == ref_str


def test_grid_types_json():
    innergrid = shaystack.Grid(version=shaystack.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['inner'] = {}
    grid.extend(cast(List[Entity], [
        {
            'inner': innergrid,
        },
    ]))
    grid_str = shaystack.dump(grid, mode=shaystack.MODE_JSON)
    grid_json = json.loads(grid_str)
    assert grid_json == {
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'inner'},
        ],
        'rows': [
            {'inner': {
                'meta': {'ver': '3.0'},
                'cols': [
                    {'name': 'comment'},
                ],
                'rows': [
                    {'comment': 's:A innergrid'},
                ],
            }},
        ],
    }


def test_grid_types_hayson():
    innergrid = shaystack.Grid(version=shaystack.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['inner'] = {}
    grid.extend(cast(List[Entity], [
        {
            'inner': innergrid,
        },
    ]))
    grid_str = shaystack.dump(grid, mode=shaystack.MODE_HAYSON)
    grid_json = json.loads(grid_str)
    assert grid_json == {
        'meta': {'ver': '3.0'},
        'cols': [
            {'name': 'inner'},
        ],
        'rows': [
            {'inner': {
                'meta': {'ver': '3.0'},
                'cols': [
                    {'name': 'comment'},
                ],
                'rows': [
                    {'comment': 'A innergrid'},
                ],
            }},
        ],
    }


def test_grid_types_csv():
    innergrid = shaystack.Grid(version=shaystack.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = shaystack.Grid(version=shaystack.VER_3_0)
    grid.column['inner'] = {}
    grid.extend(cast(List[Entity], [
        {
            'inner': innergrid,
        },
    ]))
    grid_csv = shaystack.dump(grid, mode=shaystack.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == '''
inner
"<<ver:""3.0""
comment
""A innergrid""
>>"
'''[1:]


def test_dump_invalide_scalar():
    assert dump_scalar(None)


def test_dump_ambiguous_scalar():
    assert dump_scalar("F", MODE_CSV) == '"""F"""'
    assert dump_scalar("°F", MODE_TRIO) == '"°F"'
