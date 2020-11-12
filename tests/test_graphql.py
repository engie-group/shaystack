from unittest.mock import patch

from graphene.test import Client

from app.blueprint_graphql import schema
from haystackapi.providers import get_provider
from haystackapi.providers.url import Provider
from tests import _get_mock_s3


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_about():
    with get_provider("haystackapi.providers.url") as provider:
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
        assert executed == {'data':
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
    with get_provider("haystackapi.providers.url") as provider:
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
               {'data':
                   {'haystack':
                       {
                           'ops':
                               [
                                   {'name': 'about', 'summary': 'Summary information for server'},
                                   {'name': 'ops', 'summary': 'Operations supported by this server'},
                                   {'name': 'formats',
                                    'summary': 'Grid data formats supported by this server'},
                                   {'name': 'read',
                                    'summary': 'The read op is used to read a set of entity records either by their unique '
                                               'identifier or using a filter.'},
                                   {'name': 'hisRead',
                                    'summary': 'The his_read op is used to read a time-series data from historized point.'}
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

    with get_provider("haystackapi.providers.url") as provider:
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

    with get_provider("haystackapi.providers.url") as provider:
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

    with get_provider("haystackapi.providers.url") as provider:
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
                                           {'id': 'r:id1', 'col': 'n:1.000000'},
                                           {'id': 'r:id2', 'col': 'n:2.000000'}
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

    with get_provider("haystackapi.providers.url") as provider:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            entities(filter:"id==@id1")
          }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'entities': [{'id': 'r:id1', 'col': 'n:1.000000'}]}}}


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
@patch.dict('os.environ', {'HAYSTACK_PROVIDER': "haystackapi.providers.url"})
def test_entities_with_select(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"

    with get_provider("haystackapi.providers.url") as provider:
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

    with get_provider("haystackapi.providers.url") as provider:
        client = Client(schema)
        executed = client.execute('''
        { haystack 
          {
            entities(filter:"id" limit:1)
          }
        }
        ''')
        assert executed == \
               {'data': {'haystack': {'entities': [{'id': 'r:id1', 'col': 'n:1.000000'}]}}}
