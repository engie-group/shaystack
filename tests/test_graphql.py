from datetime import datetime
from unittest.mock import patch

import pytz
from graphene.test import Client
from pytz import timezone

from app.schema_graphql import get_schema_for_provider
from shaystack import Grid, VER_3_0, Uri, Ref, Coordinate, MARKER
from shaystack.providers import get_provider
from shaystack.providers.url import Provider as URLProvider
from tests import _get_mock_s3


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, 'get_tz')
def test_about(mock):
    """
    Args:
        mock:
    """
    mock.return_value = timezone('UTC')
    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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
                                           'tz': 'UTC',
                                           # 'serverName': 'haystack_local',
                                           'productName': 'Haystack Provider',
                                           'productUri': 'http://localhost',
                                           'productVersion': '1.0',
                                           'moduleName': 'URLProvider',
                                           'moduleVersion': '1.0'
                                       }
                               }
                       }
               }


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
def test_ops():
    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url",
            'HAYSTACK_DB': ''
            }
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
def test_tag_values(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_versions(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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
                              ['2020-10-01T00:00:03+00:00 UTC',
                               '2020-10-01T00:00:02+00:00 UTC',
                               '2020-10-01T00:00:01+00:00 UTC']}}}


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_entities_with_id(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_entities_with_filter(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_entities_with_select(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_entities_with_limit(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
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


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_his_read_with_boolean(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["ts", "val"])
    his.extend([{"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": MARKER},
                {"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": False},
                {"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": 1},
                {"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": 1.0},
                {"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": ""},
                ]
               )
    mock_s3.return_value.history = his
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        schema = get_schema_for_provider(provider)
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    ts
                    val
                    bool
                }
            }
        }
        ''')
        assert executed == \
               {'data': {'haystack':
                             {'histories': [[{'ts': '2020-01-01T00:00:00+00:00 UTC', 'val': 'm:', 'bool': True},
                                             {'ts': '2020-01-01T00:00:00+00:00 UTC', 'val': False,
                                              'bool': False},
                                             {'ts': '2020-01-01T00:00:00+00:00 UTC', 'val': 'n:1.000000',
                                              'bool': True},
                                             {'ts': '2020-01-01T00:00:00+00:00 UTC', 'val': 'n:1.000000',
                                              'bool': True},
                                             {'ts': '2020-01-01T00:00:00+00:00 UTC', 'val': 's:',
                                              'bool': False}]]}}}


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_his_read_with_number(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()

    his = Grid(version=VER_3_0, columns=["ts", "val"])
    his.append({"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": 3.5})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 500
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        provider.cache_clear()
        schema = get_schema_for_provider(provider)
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    ts
                    val
                    int
                    float
                    str
                }
            }
        }
        ''')
        assert executed == \
               {'data':
                   {'haystack':
                       {'histories':
                           [[
                               {'ts': '2020-01-01T00:00:00+00:00 UTC',
                                'val': 'n:3.500000',
                                'int': 3,
                                'float': 3.5,
                                'str': '3.5'}]]}}}


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_his_read_with_uri(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["ts", "val"])
    his.append({"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": Uri("http://localhost")})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 100
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        provider.cache_clear()
        schema = get_schema_for_provider(provider)
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    ts
                    val
                    uri
                }
            }
        }
        ''')
        assert executed == \
               {'data':
                    {'haystack':
                         {'histories':
                              [[{'ts': '2020-01-01T00:00:00+00:00 UTC',
                                 'val': 'u:http://localhost', 'uri': 'http://localhost'}]]}}}


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_his_read_with_ref(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["ts", "val"])
    his.append({"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": Ref("id1")})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 200
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        provider.cache_clear()
        schema = get_schema_for_provider(provider)
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    ts
                    val
                    ref
                }
            }
        }
        ''')
        assert executed == \
               {'data':
                    {'haystack':
                         {'histories':
                              [[{'ts': '2020-01-01T00:00:00+00:00 UTC',
                                 'val': 'r:id1',
                                 'ref': '@id1'}]]}}}


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_his_read_with_datetime(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["ts", "val"])
    his.append({"ts": datetime(2020, 1, 1, tzinfo=pytz.utc),
                "val": datetime(2020, 1, 1, tzinfo=pytz.utc)})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 300
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        provider.cache_clear()
        schema = get_schema_for_provider(provider)
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    ts
                    val
                    date
                    time
                    #datetime
                }
            }
        }
        ''')
        assert executed == \
               {'data':
                    {'haystack':
                         {'histories':
                              [[{'ts': '2020-01-01T00:00:00+00:00 UTC',
                                 'val': 't:2020-01-01T00:00:00+00:00 UTC',
                                 'date': '2020-01-01T00:00:00+00:00',
                                 'time': '00:00:00'}]]}}}


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "shaystack.providers.url"})
@patch.object(URLProvider, '_get_url')
@patch.object(URLProvider, '_s3')
# noinspection PyPep8
def test_his_read_with_coordinate(mock_s3, mock_get_url):
    """
    Args:
        mock_s3:
        mock_get_url:
    """
    mock_s3.return_value = _get_mock_s3()
    his = Grid(version=VER_3_0, columns=["ts", "val"])
    his.append({"ts": datetime(2020, 1, 1, tzinfo=pytz.utc), "val": Coordinate(100.0, 150.0)})
    mock_s3.return_value.history = his
    mock_s3.return_value.his_count = 400
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    envs = {'HAYSTACK_PROVIDER': "shaystack.providers.url"}
    with get_provider("shaystack.providers.url", envs) as provider:
        provider.cache_clear()
        schema = get_schema_for_provider(provider)
        client = Client(schema)
        executed = client.execute('''
        { 
            haystack
            { 
                histories(ids:"@id1")
                {
                    ts
                    val
                    coord { latitude longitude }
                }
            }
        }
        ''')
        assert executed == \
               {'data':
                    {'haystack':
                         {'histories':
                              [[{'ts': '2020-01-01T00:00:00+00:00 UTC', 'val': 'c:100.000000,150.000000',
                                 'coord': {'latitude': 100.0, 'longitude': 150.0}}]]}}}
