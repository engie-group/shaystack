from datetime import datetime
from unittest.mock import patch

import pytz
from graphene.test import Client

from app.blueprint_graphql import schema
from haystackapi.providers import get_provider
from haystackapi.providers.url import Provider
from hszinc import Grid, VER_3_0, Uri, Ref, Coordinate, MARKER
from tests import _get_mock_s3


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_about():
    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            about
            {
              haystackVersion
              tz
              # serverName
              # serverTime
              # serverBootTime
              productName
              productUri
              productVersion
              moduleName
              moduleVersion
            }
          }
        }
        ''')
        assert executed == \
               {
                   'data':
                       {
                           'haystack':
                               {
                                   'about':
                                       {
                                           'haystackVersion': '3.0',
                                           'tz': 'Europe/Paris',
                                           # 'serverName': 'haystack_local',
                                           'productName': 'AWS Lamdda Haystack Provider',
                                           'productUri': 'http://localhost',
                                           'productVersion': '1.0',
                                           'moduleName': 'URLProvider',
                                           'moduleVersion': '1.0'
                                       }
                               }
                       }
               }


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_ops():
    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            ops 
            {
              name
              summary
            }
          }
        }
        ''')
        assert executed == \
               {
                   'data':
                       {
                           'haystack':
                               {
                                   'ops':
                                       [
                                           {'name': 'about', 'summary': 'Summary information for server'},
                                           {'name': 'ops', 'summary': 'Operations supported by this server'},
                                           {'name': 'formats',
                                            'summary': 'Grid data formats supported by this server'},
                                           {'name': 'read',
                                            'summary': 'The read op is used to read a set of entity '
                                                       'records either by their unique '
                                                       'identifier or using a filter.'},
                                           {'name': 'hisRead',
                                            'summary': 'The his_read op is used to read a time-series '
                                                       'data from historized point.'}
                                       ]
                               }
                       }
               }


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_tag_values(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            tagValues(tag:"id")
          }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'tagValues': ['@id1', '@id2']}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_versions(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            versions
          }
        }
        ''')
        assert executed == \
               {'data':
                   {'haystack':
                       {'versions':
                           [
                               '2020-10-01 00:00:03+00:00',
                               '2020-10-01 00:00:02+00:00',
                               '2020-10-01 00:00:01+00:00'
                           ]
                       }
                   }
               }


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_entities_with_id(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            entities(ids:["@id1","@id2"])
          }
        }
        ''')
        assert executed == \
               {
                   'data':
                       {
                           'haystack':
                               {
                                   'entities':
                                       [
                                           {'id': 'r:id1', 'col': 'n:1.000000', 'hisURI': 's:his0.zinc'},
                                           {'id': 'r:id2', 'col': 'n:2.000000', 'hisURI': 's:his1.zinc'}
                                       ]
                               }
                       }
               }


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_entities_with_filter(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            entities(filter:"id==@id1")
          }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'entities':
                   [
                       {'id': 'r:id1', 'col': 'n:1.000000', 'hisURI': 's:his0.zinc', }]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_entities_with_select(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            entities(filter:"id==@id1" select:"id")
          }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'entities': [{'id': 'r:id1'}]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_entities_with_limit(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            entities(filter:"id" limit:1)
          }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'entities':
                   [
                       {'id': 'r:id1', 'col': 'n:1.000000', 'hisURI': 's:his0.zinc', }]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_his_read_with_boolean(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["date", "val"])
    his.extend([{"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": MARKER},
                {"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": False},
                {"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": 1},
                {"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": 1.0},
                {"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": ""},
                ]
               )
    mock_s3.return_value.history = his
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as _:
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    date
                    val
                    bool
                }
            }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'histories':
                   [[
                       {'date': '2020-01-01 00:00:00+00:00',
                        'val': 'm:',
                        'bool': True,
                        },
                       {'date': '2020-01-01 00:00:00+00:00',
                        'val': False,
                        'bool': False,
                        },
                       {'date': '2020-01-01 00:00:00+00:00',
                        'val': 'n:1.000000',
                        'bool': True,
                        },
                       {'date': '2020-01-01 00:00:00+00:00',
                        'val': 'n:1.000000',
                        'bool': True,
                        },
                       {'date': '2020-01-01 00:00:00+00:00',
                        'val': 's:',
                        'bool': False,
                        }
                   ]]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_his_read_with_number(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()

    his = Grid(version=VER_3_0, columns=["date", "val"])
    his.append({"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": 3.5})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 500
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as provider:
        provider.cache_clear()
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    date
                    val
                    int
                    float
                    str
                }
            }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'histories':
                   [[
                       {
                           'date': '2020-01-01 00:00:00+00:00',
                           'val': 'n:3.500000',
                           "int": 3,
                           "float": 3.5,
                           "str": "3.5"
                       }
                   ]]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_his_read_with_uri(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["date", "val"])
    his.append({"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": Uri("http://localhost")})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 100
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as provider:
        provider.cache_clear()
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    date
                    val
                    uri
                }
            }
        }
        ''')
        print(executed)
        assert executed == \
               {'data': {'haystack': {'histories':
                   [[
                       {
                           'date': '2020-01-01 00:00:00+00:00',
                           'val': 'u:http://localhost',
                           'uri': 'http://localhost',
                       }
                   ]]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_his_read_with_ref(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["date", "val"])
    his.append({"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": Ref("id1")})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 200
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as provider:
        provider.cache_clear()
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    date
                    val
                    ref
                }
            }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'histories':
                   [[
                       {
                           'date': '2020-01-01 00:00:00+00:00',
                           'val': 'r:id1',
                           'ref': '@id1',
                       }
                   ]]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_his_read_with_datetime(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["date", "val"])
    his.append({"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": datetime(2020, 1, 1, tzinfo=pytz.utc)})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 300
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as provider:
        provider.cache_clear()
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    date
                    val
                    date
                    time
                    datetime
                }
            }
        }
        ''')
        print(executed)
        assert executed == \
               {'data': {'haystack': {'histories':
                   [[
                       {
                           'date': '2020-01-01 00:00:00+00:00',
                           'val': 't:2020-01-01T00:00:00+00:00 UTC',
                           'datetime': '2020-01-01 00:00:00+00:00',
                           'time': '00:00:00',
                       }
                   ]]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_his_read_with_coordinate(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["date", "val"])
    his.append({"date": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": Coordinate(100.0, 150.0)})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 400
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as provider:
        provider.cache_clear()
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    date
                    val
                    coord { lat long }
                }
            }
        }
        ''')
        print(executed)
        assert executed == \
               {'data': {'haystack': {'histories':
                   [[
                       {
                           'date': '2020-01-01 00:00:00+00:00',
                           'val': 'c:100.000000,150.000000',
                           'coord': {'lat': 100.0, 'long': 150.0},
                       }
                   ]]}}}
