# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import datetime
import json

import pytz

import hszinc
from .test_parser import SIMPLE_EXAMPLE, SIMPLE_EXAMPLE_JSON, \
    METADATA_EXAMPLE_JSON

# The metadata example is a little different, as we generate the grid without
# spaces around the commas.
METADATA_EXAMPLE = '''ver:"2.0" database:"test" dis:"Site Energy Summary"
siteName dis:"Sites",val dis:"Value" unit:"kW"
"Site 1",356.214kW
"Site 2",463.028kW
'''


def make_simple_grid(version=hszinc.VER_2_0):
    grid = hszinc.Grid(version=version)
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


def test_simple():
    grid = make_simple_grid()
    grid_str = hszinc.dump(grid)
    assert grid_str == SIMPLE_EXAMPLE


def test_simple_json():
    grid = make_simple_grid()
    grid_json = json.loads(hszinc.dump(grid, mode=hszinc.MODE_JSON))
    assert grid_json == SIMPLE_EXAMPLE_JSON


def make_metadata_grid(version=hszinc.VER_2_0):
    grid = hszinc.Grid(version=version)
    grid.metadata['database'] = 'test'
    grid.metadata['dis'] = 'Site Energy Summary'
    grid.column['siteName'] = {'dis': 'Sites'}
    grid.column['val'] = hszinc.MetadataObject()
    grid.column['val']['dis'] = 'Value'
    grid.column['val']['unit'] = 'kW'
    grid.extend([
        {
            'siteName': 'Site 1',
            'val': hszinc.Quantity(356.214, 'kW'),
        },
        {
            'siteName': 'Site 2',
            'val': hszinc.Quantity(463.028, 'kW'),
        },
    ])
    return grid


def test_metadata():
    grid = make_metadata_grid()
    grid_str = hszinc.dump(grid)
    assert grid_str == METADATA_EXAMPLE


def test_metadata_json():
    grid = make_metadata_grid()
    grid_json = json.loads(hszinc.dump(grid, mode=hszinc.MODE_JSON))
    assert grid_json == METADATA_EXAMPLE_JSON


def test_multi_grid():
    grids = [make_simple_grid(), make_metadata_grid()]
    grid_str = hszinc.dump(grids)

    assert grid_str == '\n'.join([SIMPLE_EXAMPLE, METADATA_EXAMPLE])


def test_multi_grid_json():
    grids = [make_simple_grid(), make_metadata_grid()]
    grid_json = json.loads(hszinc.dump(grids, mode=hszinc.MODE_JSON))

    assert grid_json[0] == SIMPLE_EXAMPLE_JSON
    assert grid_json[1] == METADATA_EXAMPLE_JSON


def make_grid_meta(version=hszinc.VER_2_0):
    grid = hszinc.Grid(version=version)
    grid.metadata['aString'] = 'aValue'
    grid.metadata['aNumber'] = 3.14159
    grid.metadata['aNull'] = None
    grid.metadata['aMarker'] = hszinc.MARKER
    grid.metadata['aQuantity'] = hszinc.Quantity(123, 'Hz')
    grid.column['empty'] = {}
    return grid


def test_grid_meta():
    grid_str = hszinc.dump(make_grid_meta())
    assert grid_str == '''ver:"2.0" aString:"aValue" aNumber:3.14159 aNull:N aMarker aQuantity:123Hz
empty
'''


def test_grid_meta_json():
    grid_json = json.loads(hszinc.dump(make_grid_meta(),
                                       mode=hszinc.MODE_JSON))
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


def make_col_meta(version=hszinc.VER_2_0):
    grid = hszinc.Grid(version=version)
    col_meta = hszinc.MetadataObject()
    col_meta['aString'] = 'aValue'
    col_meta['aNumber'] = 3.14159
    col_meta['aNull'] = None
    col_meta['aMarker'] = hszinc.MARKER
    col_meta['aQuantity'] = hszinc.Quantity(123, 'Hz')
    grid.column['empty'] = col_meta
    return grid


def test_col_meta():
    grid_str = hszinc.dump(make_col_meta())
    assert grid_str == '''ver:"2.0"
empty aString:"aValue" aNumber:3.14159 aNull:N aMarker aQuantity:123Hz
'''


def test_col_meta_json():
    grid_json = json.loads(hszinc.dump(make_col_meta(),
                                       mode=hszinc.MODE_JSON))
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


def test_data_types_v2():
    grid = hszinc.Grid(version=hszinc.VER_2_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A null value',
            'value': None,
        },
        {
            'comment': 'A marker',
            'value': hszinc.MARKER,
        },
        {
            'comment': 'A "remove" object',
            'value': hszinc.REMOVE,
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
            'value': hszinc.Ref('a-ref'),
        },
        {
            'comment': 'A reference, with value',
            'value': hszinc.Ref('a-ref', 'a value'),
        },
        {
            'comment': 'A binary blob',
            'value': hszinc.Bin('text/plain'),
        },
        {
            'comment': 'A quantity',
            'value': hszinc.Quantity(500, 'miles'),
        },
        {
            'comment': 'A quantity without unit',
            'value': hszinc.Quantity(500, None),
        },
        {
            'comment': 'A coordinate',
            'value': hszinc.Coordinate(-27.4725, 153.003),
        },
        {
            'comment': 'A URI',
            'value': hszinc.Uri(u'http://www.example.com#`unicode:\u1234\u5678`'),
        },
        {
            'comment': 'A string',
            'value': u'This is a test\n' \
                     u'Line two of test\n' \
                     u'\tIndented with "quotes", \\backslashes\\ and ' \
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
            'value': pytz.timezone('Europe/Berlin').localize( \
                datetime.datetime(2016, 1, 13, 7, 51, 42, 12345)),
        },
        {
            'comment': 'A timestamp (UTC)',
            'value': pytz.timezone('UTC').localize( \
                datetime.datetime(2016, 1, 13, 7, 51, 42, 12345)),
        },
    ])
    grid_str = hszinc.dump(grid)
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


def test_data_types_v3():
    grid = hszinc.Grid(version=hszinc.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A NA',
            'value': hszinc.NA,
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
            'value': [hszinc.MARKER],
        },
        {
            'comment': 'Booleans',
            'value': [True, False],
        },
        {
            'comment': 'References',
            'value': [hszinc.Ref('a-ref'), hszinc.Ref('a-ref', 'a value')],
        },
        {
            'comment': 'A quantity',
            'value': [hszinc.Quantity(500, 'miles')],
        },
        {
            'comment': 'A XStr',
            'value': [hszinc.XStr("hex", 'deadbeef')],
        },
    ])
    grid_str = hszinc.dump(grid)
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


def test_data_types_json_v2():
    grid = hszinc.Grid(version=hszinc.VER_2_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A null value',
            'value': None,
        },
        {
            'comment': 'A marker',
            'value': hszinc.MARKER,
        },
        {
            'comment': 'A remove (2.0 version)',
            'value': hszinc.REMOVE,
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
            'value': hszinc.Ref('a-ref'),
        },
        {
            'comment': 'A reference, with value',
            'value': hszinc.Ref('a-ref', 'a value'),
        },
        {
            'comment': 'A binary blob',
            'value': hszinc.Bin('text/plain'),
        },
        {
            'comment': 'A quantity',
            'value': hszinc.Quantity(500, 'miles'),
        },
        {
            'comment': 'A quantity without unit',
            'value': hszinc.Quantity(500, None),
        },
        {
            'comment': 'A coordinate',
            'value': hszinc.Coordinate(-27.4725, 153.003),
        },
        {
            'comment': 'A URI',
            'value': hszinc.Uri('http://www.example.com'),
        },
        {
            'comment': 'A string',
            'value': 'This is a test\n' \
                     'Line two of test\n' \
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
            'value': pytz.timezone('Europe/Berlin').localize( \
                datetime.datetime(2016, 1, 13, 7, 51, 42, 12345)),
        },
        {
            'comment': 'A timestamp (UTC)',
            'value': pytz.timezone('UTC').localize( \
                datetime.datetime(2016, 1, 13, 7, 51, 42, 12345)),
        },
    ])
    grid_json = json.loads(hszinc.dump(grid, mode=hszinc.MODE_JSON))
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
             'value': 's:This is a test\n' \
                      'Line two of test\n' \
                      '\tIndented with \"quotes\" ' \
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


def test_data_types_json_v3():
    grid = hszinc.Grid(version=hszinc.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'A Remove (3.0 version)',
            'value': hszinc.REMOVE,
        },
        {
            'comment': 'A NA',
            'value': hszinc.NA,
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
            'value': [hszinc.MARKER],
        },
        {
            'comment': 'Booleans',
            'value': [True, False],
        },
        {
            'comment': 'References',
            'value': [hszinc.Ref('a-ref'), hszinc.Ref('a-ref', 'a value')],
        },
        {
            'comment': 'A quantity',
            'value': [hszinc.Quantity(500, 'miles')],
        },
        {
            'comment': 'A XStr',
            'value': [hszinc.XStr("hex", 'deadbeef')],
        },
    ])
    grid_json = json.loads(hszinc.dump(grid, mode=hszinc.MODE_JSON))
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


def test_scalar_dict_json_v3():
    grid = hszinc.Grid(version=hszinc.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": hszinc.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": hszinc.Ref('a-ref'), "ref2": hszinc.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": hszinc.Quantity(500, 'miles')},
        },
    ])
    grid_json = json.loads(hszinc.dump(grid, mode=hszinc.MODE_JSON))
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


def test_scalar_dict_zinc_v3():
    grid = hszinc.Grid(version=hszinc.VER_3_0)
    grid.column['comment'] = {}
    grid.column['value'] = {}
    grid.extend([
        {
            'comment': 'An empty dict',
            'value': {},
        },
        {
            'comment': 'A marker in a dict',
            'value': {"marker": hszinc.MARKER},
        },
        {
            'comment': 'A references in a dict',
            'value': {"ref": hszinc.Ref('a-ref'), "ref2": hszinc.Ref('a-ref', 'a value')},
        },
        {
            'comment': 'A quantity in a dict',
            'value': {"quantity": hszinc.Quantity(500, 'miles')},
        },
    ])
    grid_str = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
    assert grid_str == ("ver:\"3.0\"\n"
                        "comment,value\n"
                        "\"An empty dict\",{}\n"
                        "\"A marker in a dict\",{marker:M}\n"
                        "\"A references in a dict\",{" +
                        " ".join([str(k) + ":" + str(v) for k, v in {"ref": "@a-ref", "ref2": "@a-ref"}.items()]) \
                        .replace("ref2:@a-ref", "ref2:@a-ref \"a value\"") + \
                        "}\n"
                        "\"A quantity in a dict\",{quantity:500miles}\n")

def test_scalar_dict_zinc_ver():
    # Test that versions are respected.
    try:
        hszinc.dump_scalar({"a":"b"},
                           mode=hszinc.MODE_ZINC, version=hszinc.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_unknown():
    try:
        hszinc.dump_scalar(hszinc.VER_2_0,
                           mode=hszinc.MODE_ZINC, version=hszinc.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except NotImplementedError:
        pass

def test_list_zinc_v2():
    try:
        grid = hszinc.Grid(version=hszinc.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        hszinc.dump(grid, mode=hszinc.MODE_ZINC)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_dict_zinc_v2():
    try:
        grid = hszinc.Grid(version=hszinc.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        hszinc.dump(grid, mode=hszinc.MODE_ZINC)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_list_json_v2():
    try:
        grid = hszinc.Grid(version=hszinc.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty list',
                'value': [],
            }
        ])
        hszinc.dump(grid, mode=hszinc.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support lists'
    except ValueError:
        pass


def test_dict_json_v2():
    try:
        grid = hszinc.Grid(version=hszinc.VER_2_0)
        grid.column['comment'] = {}
        grid.column['value'] = {}
        grid.extend([
            {
                'comment': 'An empty dict',
                'value': {},
            }
        ])
        hszinc.dump(grid, mode=hszinc.MODE_JSON)
        assert False, 'Project Haystack 2.0 doesn\'t support dict'
    except ValueError:
        pass


def test_scalar_zinc():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert hszinc.dump_scalar(hszinc.Ref('areference', 'a display name'),
                              mode=hszinc.MODE_ZINC) == '@areference "a display name"'


def test_scalar_list_zinc_ver():
    # Test that versions are respected.
    try:
        hszinc.dump_scalar(["a list is not allowed in v2.0"],
                           mode=hszinc.MODE_ZINC, version=hszinc.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_list_na_ver():
    # Test that versions are respected.
    try:
        hszinc.dump_scalar(hszinc.NA,
                           mode=hszinc.MODE_ZINC, version=hszinc.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_json():
    # No need to be exhaustive, the underlying function is tested heavily by
    # the grid dump tests.
    assert hszinc.dump_scalar(hszinc.Ref('areference', 'a display name'),
                              mode=hszinc.MODE_JSON) == 'r:areference a display name'


def test_scalar_list_json_ver():
    # Test that versions are respected.
    try:
        hszinc.dump_scalar(["a list is not allowed in v2.0"],
                           mode=hszinc.MODE_JSON, version=hszinc.VER_2_0)
        assert False, 'Serialised a list in Haystack v2.0'
    except ValueError:
        pass


def test_scalar_na_json_ver():
    # Test that versions are respected.
    try:
        hszinc.dump_scalar(hszinc.NA,
                           mode=hszinc.MODE_JSON, version=hszinc.VER_2_0)
        assert False, 'Serialised a NA in Haystack v2.0'
    except ValueError:
        pass


def test_grid_types_zinc():
    innergrid = hszinc.Grid(version=hszinc.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = hszinc.Grid(version=hszinc.VER_3_0)
    grid.column['inner'] = {}
    grid.extend([
        {
            'inner': innergrid,
        },
    ])
    grid_str = hszinc.dump(grid, mode=hszinc.MODE_ZINC)
    assert grid_str == ('ver:"3.0"\n'
                        'inner\n'
                        '<<ver:"3.0"\n'
                        'comment\n'
                        '"A innergrid"\n'
                        '>>\n')


def test_grid_types_json():
    innergrid = hszinc.Grid(version=hszinc.VER_3_0)
    innergrid.column['comment'] = {}
    innergrid.extend([
        {
            'comment': 'A innergrid',
        },
    ])
    grid = hszinc.Grid(version=hszinc.VER_3_0)
    grid.column['inner'] = {}
    grid.extend([
        {
            'inner': innergrid,
        },
    ])
    grid_str = hszinc.dump(grid, mode=hszinc.MODE_JSON)
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
