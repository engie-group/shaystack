# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import datetime
import json
from csv import reader

import pytz

import haystackapi
from haystackapi import dump_scalar
from .test_parser import SIMPLE_EXAMPLE_ZINC, SIMPLE_EXAMPLE_JSON, \
    METADATA_EXAMPLE_JSON, SIMPLE_EXAMPLE_CSV, METADATA_EXAMPLE_CSV

# The metadata example is a little different, as we generate the grid without
# spaces around the commas.
METADATA_EXAMPLE = '''ver:"2.0" database:"test" dis:"Site Energy Summary"
siteName dis:"Sites",val dis:"Value" unit:"kW"
"Site 1",356.214kW
"Site 2",463.028kW
'''


def make_simple_grid(version=haystackapi.VER_2_0):
    grid = haystackapi.Grid(version=version)
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
    grid_str = haystackapi.dump(grid)
    assert grid_str == SIMPLE_EXAMPLE_ZINC


def test_simple_json():
    grid = make_simple_grid()
    grid_json = json.loads(haystackapi.dump(grid, mode=haystackapi.MODE_JSON))
    assert grid_json == SIMPLE_EXAMPLE_JSON


def test_simple_csv():
    grid = make_simple_grid()
    grid_csv = haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == SIMPLE_EXAMPLE_CSV


def make_metadata_grid(version=haystackapi.VER_2_0):
    grid = haystackapi.Grid(version=version)
    grid.metadata['database'] = 'test'
    grid.metadata['dis'] = 'Site Energy Summary'
    grid.column['siteName'] = {'dis': 'Sites'}
    grid.column['val'] = haystackapi.MetadataObject()
    grid.column['val']['dis'] = 'Value'
    grid.column['val']['unit'] = 'kW'
    grid.extend([
        {
            'siteName': 'Site 1',
            'val': haystackapi.Quantity(356.214, 'kW'),
        },
        {
            'siteName': 'Site 2',
            'val': haystackapi.Quantity(463.028, 'kW'),
        },
    ])
    return grid


def test_metadata_zinc():
    grid = make_metadata_grid()
    grid_str = haystackapi.dump(grid)
    assert grid_str == METADATA_EXAMPLE


def test_metadata_json():
    grid = make_metadata_grid()
    grid_json = json.loads(haystackapi.dump(grid, mode=haystackapi.MODE_JSON))
    assert grid_json == METADATA_EXAMPLE_JSON


def test_metadata_csv():
    grid = make_metadata_grid()
    grid_csv = haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == METADATA_EXAMPLE_CSV


def test_multi_grid_zinc():
    grids = [make_simple_grid(), make_metadata_grid()]
    grid_str = haystackapi.dump(grids)

    assert grid_str == '\n'.join([SIMPLE_EXAMPLE_ZINC, METADATA_EXAMPLE])


def test_multi_grid_json():
    grids = [make_simple_grid(), make_metadata_grid()]
    grid_json = json.loads(haystackapi.dump(grids, mode=haystackapi.MODE_JSON))

    assert grid_json[0] == SIMPLE_EXAMPLE_JSON
    assert grid_json[1] == METADATA_EXAMPLE_JSON


def test_multi_grid_csv():
    grids = [make_simple_grid(), make_metadata_grid()]
    grid_csv = haystackapi.dump(grids, mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == '''firstName,bday
"Jack",1973-07-23
"Jill",1975-11-15

siteName,val
"Site 1",356.214kW
"Site 2",463.028kW
'''


def make_grid_meta(version=haystackapi.VER_2_0):
    grid = haystackapi.Grid(version=version)
    grid.metadata['aString'] = 'aValue'
    grid.metadata['aNumber'] = 3.14159
    grid.metadata['aNull'] = None
    grid.metadata['aMarker'] = haystackapi.MARKER
    grid.metadata['aQuantity'] = haystackapi.Quantity(123, 'Hz')
    grid.column['empty'] = {}
    return grid


def test_grid_meta():
    grid_str = haystackapi.dump(make_grid_meta())
    assert grid_str == '''ver:"2.0" aString:"aValue" aNumber:3.14159 aNull:N aMarker aQuantity:123Hz
empty
'''


def test_grid_meta_json():
    grid_json = json.loads(haystackapi.dump(make_grid_meta(),
                                            mode=haystackapi.MODE_JSON))
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


def test_grid_meta_csv():
    grid_csv = haystackapi.dump(make_grid_meta(), mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == 'empty\n'


def make_col_meta(version=haystackapi.VER_2_0):
    grid = haystackapi.Grid(version=version)
    col_meta = haystackapi.MetadataObject()
    col_meta['aString'] = 'aValue'
    col_meta['aNumber'] = 3.14159
    col_meta['aNull'] = None
    col_meta['aMarker'] = haystackapi.MARKER
    col_meta['aQuantity'] = haystackapi.Quantity(123, 'Hz')
    grid.column['empty'] = col_meta
    return grid


def test_col_meta_zinc():
    grid_str = haystackapi.dump(make_col_meta(), mode=haystackapi.MODE_ZINC)
    assert grid_str == '''ver:"2.0"
empty aString:"aValue" aNumber:3.14159 aNull:N aMarker aQuantity:123Hz
'''


def test_col_meta_json():
    grid_json = json.loads(haystackapi.dump(make_col_meta(),
                                            mode=haystackapi.MODE_JSON))
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


def test_col_meta_csv():
    grid_csv = haystackapi.dump(make_col_meta(), mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == 'empty\n'


def test_data_types_zinc_v2():
    grid = haystackapi.Grid(version=haystackapi.VER_2_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A null value',
            'value': None,
        },
        {
            'comment': 'A marker',
            'value': haystackapi.MARKER,
        },
        {
            'comment': 'A "remove" object',
            'value': haystackapi.REMOVE,
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
            'value': haystackapi.Ref('a-ref'),
        },
        {
            'comment': 'A reference, with value',
            'value': haystackapi.Ref('a-ref', 'a value'),
        },
        {
            'comment': 'A binary blob',
            'value': haystackapi.Bin('text/plain'),
        },
        {
            'comment': 'A quantity',
            'value': haystackapi.Quantity(500, 'miles'),
        },
        {
            'comment': 'A quantity without unit',
            'value': haystackapi.Quantity(500, None),
        },
        {
            'comment': 'A coordinate',
            'value': haystackapi.Coordinate(-27.4725, 153.003),
        },
        {
            'comment': 'A URI',
            'value': haystackapi.Uri(u'http://www.example.com#`unicode:\u1234\u5678`'),
        },
        {
            'comment': 'A string',
            'value': u'This is a test\n'
                     u'Line two of test\n'
                     u'\tIndented with "quotes", \\backslashes\\ and '
                     u'Unicode characters: \u1234\u5678 and a $ dollar sign',
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
    grid_str = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)
    ref_str = '''ver:"2.0"
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
"A URI",`http://www.example.com#\\`unicode:\\u1234\\u5678\\``
"A string","This is a test\\nLine two of test\\n\\tIndented with \\"quotes\\", \\\\backslashes\\\\ and Unicode characters: \\u1234\\u5678 and a \\$ dollar sign"
"A date",2016-01-13
"A time",07:51:43.012345
"A timestamp (non-UTC)",2016-01-13T07:51:42.012345+01:00 Berlin
"A timestamp (UTC)",2016-01-13T07:51:42.012345+00:00 UTC
'''
    assert grid_str == ref_str


def test_data_types_json_v2():
    grid = haystackapi.Grid(version=haystackapi.VER_2_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A null value',
            'value': None,
        },
        {
            'comment': 'A marker',
            'value': haystackapi.MARKER,
        },
        {
            'comment': 'A remove (2.0 version)',
            'value': haystackapi.REMOVE,
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
            'value': haystackapi.Ref('a-ref'),
        },
        {
            'comment': 'A reference, with value',
            'value': haystackapi.Ref('a-ref', 'a value'),
        },
        {
            'comment': 'A binary blob',
            'value': haystackapi.Bin('text/plain'),
        },
        {
            'comment': 'A quantity',
            'value': haystackapi.Quantity(500, 'miles'),
        },
        {
            'comment': 'A quantity without unit',
            'value': haystackapi.Quantity(500, None),
        },
        {
            'comment': 'A coordinate',
            'value': haystackapi.Coordinate(-27.4725, 153.003),
        },
        {
            'comment': 'A URI',
            'value': haystackapi.Uri('http://www.example.com'),
        },
        {
            'comment': 'A string',
            'value': 'This is a test\n'
                     'Line two of test\n'
                     '\tIndented with "quotes" and \\backslashes\\',
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
    grid_json = json.loads(haystackapi.dump(grid, mode=haystackapi.MODE_JSON))
    assert grid_json == {
        'meta': {'ver': '2.0'},
        'cols': [
            {'name': 'comment'},
            {'name': 'value'},
        ],
        'rows': [
            {'comment': 's:A null value',
             'value': None},
            {'comment': 's:A marker',
             'value': 'm:'},
            {'comment': 's:A remove (2.0 version)',
             'value': 'x:'},
            {'comment': 's:A boolean, indicating False',
             'value': False},
            {'comment': 's:A boolean, indicating True',
             'value': True},
            {'comment': 's:A reference, without value',
             'value': 'r:a-ref'},
            {'comment': 's:A reference, with value',
             'value': 'r:a-ref a value'},
            {'comment': 's:A binary blob',
             'value': 'b:text/plain'},
            {'comment': 's:A quantity',
             'value': 'n:500.000000 miles'},
            {'comment': 's:A quantity without unit',
             'value': 'n:500.000000'},
            {'comment': 's:A coordinate',
             'value': 'c:-27.472500,153.003000'},
            {'comment': 's:A URI',
             'value': 'u:http://www.example.com'},
            {'comment': 's:A string',
             'value': 's:This is a test\n'
                      'Line two of test\n'
                      '\tIndented with \"quotes\" '
                      'and \\backslashes\\'},
            {'comment': 's:A date',
             'value': 'd:2016-01-13'},
            {'comment': 's:A time',
             'value': 'h:07:51:43.012345'},
            {'comment': 's:A timestamp (non-UTC)',
             'value': 't:2016-01-13T07:51:42.012345+01:00 Berlin'},
            {'comment': 's:A timestamp (UTC)',
             'value': 't:2016-01-13T07:51:42.012345+00:00 UTC'},
        ],
    }


def test_data_types_csv_v2():
    grid = haystackapi.Grid(version=haystackapi.VER_2_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A null value',
            'value': None,
        },
        {
            'comment': 'A marker',
            'value': haystackapi.MARKER,
        },
        {
            'comment': 'A remove (2.0 version)',
            'value': haystackapi.REMOVE,
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
            'value': haystackapi.Ref('a-ref'),
        },
        {
            'comment': 'A reference, with value',
            'value': haystackapi.Ref('a-ref', 'a value'),
        },
        {
            'comment': 'A binary blob',
            'value': haystackapi.Bin('text/plain'),
        },
        {
            'comment': 'A quantity',
            'value': haystackapi.Quantity(500, 'miles'),
        },
        {
            'comment': 'A quantity without unit',
            'value': haystackapi.Quantity(500, None),
        },
        {
            'comment': 'A coordinate',
            'value': haystackapi.Coordinate(-27.4725, 153.003),
        },
        {
            'comment': 'A URI',
            'value': haystackapi.Uri('http://www.example.com'),
        },
        {
            'comment': 'A string',
            'value': 'This is a test\n'
                     'Line two of test\n'
                     '\tIndented with "quotes" and \\backslashes\\',
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
    grid_csv = haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == u'''comment,value
"A null value",
"A marker",\u2713
"A remove (2.0 version)",R
"A boolean, indicating False",false
"A boolean, indicating True",true
"A reference, without value",@a-ref
"A reference, with value",@a-ref a value
"A binary blob",Bin(text/plain)
"A quantity",500miles
"A quantity without unit",500
"A coordinate","C(-27.472500,153.003000)"
"A URI",`http://www.example.com`
"A string","This is a test\nLine two of test\n\tIndented with ""quotes"" and \\backslashes\\"
"A date",2016-01-13
"A time",07:51:43.012345
"A timestamp (non-UTC)",2016-01-13T07:51:42.012345+01:00
"A timestamp (UTC)",2016-01-13T07:51:42.012345+00:00
'''


def test_data_types_zinc_v3():
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A NA',
            'value': haystackapi.NA,
        },
        {
            'comment': 'An empty list',
            'value': [],
        },
        {
            'comment': 'A null value in a list',
            'value': [None],
        },
        {
            'comment': 'A marker in a list',
            'value': [haystackapi.MARKER],
        },
        {
            'comment': 'Booleans',
            'value': [True, False],
        },
        {
            'comment': 'References',
            'value': [haystackapi.Ref('a-ref'), haystackapi.Ref('a-ref', 'a value')],
        },
        {
            'comment': 'A quantity',
            'value': [haystackapi.Quantity(500, 'miles')],
        },
        {
            'comment': 'A XStr',
            'value': [haystackapi.XStr("hex", 'deadbeef')],
        },
    ])
    grid_str = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)
    ref_str = '''ver:"3.0"
comment,value
"A NA",NA
"An empty list",[]
"A null value in a list",[N]
"A marker in a list",[M]
"Booleans",[T,F]
"References",[@a-ref,@a-ref "a value"]
"A quantity",[500miles]
"A XStr",[hex("deadbeef")]
'''
    assert grid_str == ref_str


def test_data_types_json_v3():
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A Remove (3.0 version)',
            'value': haystackapi.REMOVE,
        },
        {
            'comment': 'A NA',
            'value': haystackapi.NA,
        },
        {
            'comment': 'An empty list',
            'value': [],
        },
        {
            'comment': 'A null value in a list',
            'value': [None],
        },
        {
            'comment': 'A marker in a list',
            'value': [haystackapi.MARKER],
        },
        {
            'comment': 'Booleans',
            'value': [True, False],
        },
        {
            'comment': 'References',
            'value': [haystackapi.Ref('a-ref'), haystackapi.Ref('a-ref', 'a value')],
        },
        {
            'comment': 'A quantity',
            'value': [haystackapi.Quantity(500, 'miles')],
        },
        {
            'comment': 'A XStr',
            'value': [haystackapi.XStr("hex", 'deadbeef')],
        },
    ])
    grid_json = json.loads(haystackapi.dump(grid, mode=haystackapi.MODE_JSON))
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
                'comment': 's:A Remove (3.0 version)',
                'value': '-:'
            },
            {
                'comment': 's:A NA',
                'value': 'z:'
            },
            {
                'comment': "s:An empty list",
                'value': []
            },
            {
                'comment': "s:A null value in a list",
                'value': [None]
            },
            {
                'comment': "s:A marker in a list",
                'value': ['m:']
            },
            {
                'comment': "s:Booleans",
                'value': [True, False]
            },
            {
                'comment': "s:References",
                'value': ['r:a-ref', 'r:a-ref a value']
            },
            {
                'comment': "s:A quantity",
                'value': ['n:500.000000 miles']  # Python is more precise
                # than The Proclaimers
            },
            {
                'comment': "s:A XStr",
                'value': ['x:hex:deadbeef']
            }
        ]
    }


def test_data_types_csv_v3():
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A Remove (3.0 version)',
            'value': haystackapi.REMOVE,
        },
        {
            'comment': 'A NA',
            'value': haystackapi.NA,
        },
        {
            'comment': 'An empty list',
            'value': [],
        },
        {
            'comment': 'A null value in a list',
            'value': [None],
        },
        {
            'comment': 'A marker in a list',
            'value': [haystackapi.MARKER],
        },
        {
            'comment': 'Booleans',
            'value': [True, False],
        },
        {
            'comment': 'References',
            'value': [haystackapi.Ref('a-ref'), haystackapi.Ref('a-ref', 'a value')],
        },
        {
            'comment': 'A quantity',
            'value': [haystackapi.Quantity(500, 'miles')],
        },
        {
            'comment': 'A XStr',
            'value': [haystackapi.XStr("hex", 'deadbeef')],
        },
    ])
    grid_csv = haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == u'''comment,value
"A Remove (3.0 version)",R
"A NA",NA
"An empty list","[]"
"A null value in a list","[N]"
"A marker in a list","[M]"
"Booleans","[T,F]"
"References","[@a-ref,@a-ref ""a value""]"
"A quantity","[500miles]"
"A XStr","[hex(""deadbeef"")]"
'''


def test_scalar_dict_zinc_v3():
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": haystackapi.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": haystackapi.Ref('a-ref'), "ref2": haystackapi.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": haystackapi.Quantity(500, 'miles')},
        },
    ])
    grid_str = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)
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


def test_scalar_dict_json_v3():
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": haystackapi.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": haystackapi.Ref('a-ref'), "ref2": haystackapi.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": haystackapi.Quantity(500, 'miles')},
        },
    ])
    grid_json = json.loads(haystackapi.dump(grid, mode=haystackapi.MODE_JSON))
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


def test_scalar_dict_csv_v3():
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": haystackapi.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": haystackapi.Ref('a-ref'), "ref2": haystackapi.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": haystackapi.Quantity(500, 'miles')},
        },
    ])
    grid_csv = haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
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
        haystackapi.dump_scalar({"a": "b"},
                                mode=haystackapi.MODE_ZINC, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_dict_json_ver():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar({"a": "b"},
                                mode=haystackapi.MODE_JSON, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_unknown_zinc():
    try:
        haystackapi.dump_scalar(haystackapi.VER_2_0,
                                mode=haystackapi.MODE_ZINC, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_scalar_unknown_json():
    try:
        haystackapi.dump_scalar(haystackapi.VER_2_0,
                                mode=haystackapi.MODE_JSON, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_scalar_unknown_csv():
    try:
        haystackapi.dump_scalar(haystackapi.VER_2_0,
                                mode=haystackapi.MODE_CSV, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass


def test_list_zinc_v2():
    try:
        grid = haystackapi.Grid(version=haystackapi.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_list_json_v2():
    try:
        grid = haystackapi.Grid(version=haystackapi.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        haystackapi.dump(grid, mode=haystackapi.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_list_csv_v2():
    try:
        grid = haystackapi.Grid(version=haystackapi.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_dict_zinc_v2():
    try:
        grid = haystackapi.Grid(version=haystackapi.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_dict_json_v2():
    try:
        grid = haystackapi.Grid(version=haystackapi.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        haystackapi.dump(grid, mode=haystackapi.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_dict_csv_v2():
    try:
        grid = haystackapi.Grid(version=haystackapi.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_scalar_zinc():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert haystackapi.dump_scalar(haystackapi.Ref('areference', 'a display name'),
                                   mode=haystackapi.MODE_ZINC) == '@areference "a display name"'


def test_scalar_json():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert haystackapi.dump_scalar(haystackapi.Ref('areference', 'a display name'),
                                   mode=haystackapi.MODE_JSON) == 'r:areference a display name'


def test_scalar_csv():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert haystackapi.dump_scalar(haystackapi.Ref('areference', 'a display name'),
                                   mode=haystackapi.MODE_CSV) == '@areference a display name'


def test_scalar_list_zinc_ver():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(["a list is not allowed in v2.0"],
                                mode=haystackapi.MODE_ZINC, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_json_ver():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(["a list is not allowed in v2.0"],
                                mode=haystackapi.MODE_JSON, version=haystackapi.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_zinc():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(haystackapi.NA,
                                mode=haystackapi.MODE_ZINC, version=haystackapi.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_json():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(haystackapi.NA,
                                mode=haystackapi.MODE_JSON, version=haystackapi.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver_csv():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(haystackapi.NA,
                                mode=haystackapi.MODE_CSV, version=haystackapi.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_zinc_ver():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(haystackapi.NA,
                                mode=haystackapi.MODE_ZINC, version=haystackapi.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_json_ver():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(haystackapi.NA,
                                mode=haystackapi.MODE_JSON, version=haystackapi.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_csv_ver():
    # Test that versions are respected.
    try:
        haystackapi.dump_scalar(haystackapi.NA,
                                mode=haystackapi.MODE_CSV, version=haystackapi.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_grid_types_zinc():
    innergrid = haystackapi.Grid(version=haystackapi.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['inner'] = {}
    grid.extend([
        {
            'inner': innergrid,
        },
    ])
    grid_str = haystackapi.dump(grid, mode=haystackapi.MODE_ZINC)
    assert grid_str == ('ver:"3.0"\n'
                        'inner\n'
                        '<<ver:"3.0"\n'
                        'comment\n'
                        '"A innergrid"\n'
                        '>>\n')


def test_grid_types_json():
    innergrid = haystackapi.Grid(version=haystackapi.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['inner'] = {}
    grid.extend([
        {
            'inner': innergrid,
        },
    ])
    grid_str = haystackapi.dump(grid, mode=haystackapi.MODE_JSON)
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


def test_grid_types_csv():
    innergrid = haystackapi.Grid(version=haystackapi.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = haystackapi.Grid(version=haystackapi.VER_3_0)
    grid.column['inner'] = {}
    grid.extend([
        {
            'inner': innergrid,
        },
    ])
    grid_csv = haystackapi.dump(grid, mode=haystackapi.MODE_CSV)
    assert list(reader(grid_csv.splitlines()))
    assert grid_csv == '''inner
"<<ver:""3.0""
comment
""A innergrid""
>>"
'''


def test_dump_invalide_scalar():
    assert dump_scalar(None)
