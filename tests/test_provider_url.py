import json
import os
import shutil
import unittest
from collections import OrderedDict
from datetime import datetime
from typing import cast
from unittest.mock import patch

import pytz

from shaystack import Ref
from shaystack.providers import get_provider
from shaystack.providers.url import Provider as URLProvider

ONTO = {"meta": {"ver": "3.0"},
        "cols": [{"name": "col1"}, {"name": "col2"}, {"name": "dis"}, {"name": "id"}],
        "rows": [
            {"dis": "dis1", "id": {"_kind": "Ref", "val": "p_demo_r_23a44701-a89a6c66", "dis": "dis"},
             "col1": "col 1 value", "col2": "col 2 value", "hisURI": "p_demo_r_23a44701-4ea35663.zinc"},
            {"dis": "dis2", "id": {"_kind": "Ref", "val": "p_demo_r_255555701-a89a6c66", "dis": "dis"},
             "col1": "col 1 value", "col2": "col 2 value", "hisURI": "p_demo_r_23a44701-bbc36976.zinc"},
            {"dis": "dis3", "id": {"_kind": "Ref", "val": "p_demo_r_255225701-a89a6c66", "dis": "dis"},
             "col1": "col 1 value", "col2": "col 2 value", "hisURI": "p_demo_r_23a44701-3940e690.zinc"}
        ]}

ONTO2021 = {"meta": {"ver": "3.0"},
            "cols": [{"name": "col1"}, {"name": "col2"}, {"name": "dis"}, {"name": "id"}],
            "rows": [
                {"dis": "dis1", "id": {"_kind": "Ref", "val": "p_demo_r_23a44701-a89a6c66", "dis": "dis"},
                 "col1": "col 1 value", "col2": "col 2 value", "hisURI": "p_demo_r_23a44701-4ea35663.zinc"},
                {"dis": "dis2", "id": {"_kind": "Ref", "val": "p_demo_r_255555701-a89a6c66", "dis": "dis"},
                 "col1": "col 1 value", "col2": "col 2 value", "hisURI": "p_demo_r_23a44701-bbc36976.zinc"}
            ]}

ONTO2020 = {"meta": {"ver": "3.0"},
            "cols": [{"name": "col1"}, {"name": "col2"}, {"name": "dis"}, {"name": "id"}],
            "rows": [
                {"dis": "dis1", "id": {"_kind": "Ref", "val": "p_demo_r_23a44701-a89a6c66", "dis": "dis"},
                 "col1": "col 1 value", "col2": "col 2 value"}
            ]}

TS1 = """ver:"3.0" hisStart:2020-07-01T00:00:00+00:00 UTC hisEnd:2020-12-01T00:00:00+00:00 UTC
ts,val
2021-07-01T00:00:00+00:00 UTC,11
2021-08-01T00:00:00+00:00 UTC,11
2021-09-01T00:00:00+00:00 UTC,15
2021-10-01T00:00:00+00:00 UTC,13
2021-11-01T00:00:00+00:00 UTC,16
2021-12-01T00:00:00+00:00 UTC,13
2022-01-01T00:00:00+00:00 UTC,13
2022-02-01T00:00:00+00:00 UTC,13
"""

TS2 = """ver:"3.0" hisStart:2020-07-01T00:00:00+00:00 UTC hisEnd:2020-12-01T00:00:00+00:00 UTC
ts,val
2020-07-01T00:00:00+00:00 UTC,11
2020-08-01T00:00:00+00:00 UTC,11
2020-09-01T00:00:00+00:00 UTC,15
2020-10-01T00:00:00+00:00 UTC,13
2020-11-01T00:00:00+00:00 UTC,16
2020-12-01T00:00:00+00:00 UTC,13
"""

TS3 = """ver:"3.0" hisStart:2020-07-01T00:00:00+00:00 UTC hisEnd:2020-12-01T00:00:00+00:00 UTC
ts,val
2020-07-01T00:00:00+00:00 UTC,11
2020-08-01T00:00:00+00:00 UTC,11
2020-09-01T00:00:00+00:00 UTC,15
2020-10-01T00:00:00+00:00 UTC,13
2020-11-01T00:00:00+00:00 UTC,16
2020-12-01T00:00:00+00:00 UTC,13
"""


class CurrentDirectory:
    def __init__(self, in_dir):
        self.in_dir = in_dir
        if not os.path.exists(self.in_dir):
            os.makedirs(self.in_dir)

    def create_files(self):
        with open(f'{self.in_dir}/carytown.hayson.json', 'w') as outfile:
            outfile.write(json.dumps(ONTO))
        with open(f'{self.in_dir}/carytown-2021-11-01T16:30:00.hayson.json', 'w') as outfile:
            outfile.write(json.dumps(ONTO2021))
        with open(f'{self.in_dir}/carytown-2020-11-01T16:30:00.hayson.json', 'w') as outfile:
            outfile.write(json.dumps(ONTO2020))
        with open(f'{self.in_dir}/p_demo_r_23a44701-4ea35663.zinc', 'w') as outfile:
            outfile.write(TS1)
        with open(f'{self.in_dir}/p_demo_r_23a44701-bbc36976.zinc', 'w') as outfile:
            outfile.write(TS2)
        with open(f'{self.in_dir}/p_demo_r_23a44701-3940e690.zinc', 'w') as outfile:
            outfile.write(TS3)


class TestImportLocalFile(unittest.TestCase):

    def setUp(self):
        self.input_file_ontologies = f'{os.getcwd()}/input_ontolog_files'
        self.environ = {
            "HAYSTACK_PROVIDER": "shaystack.providers.url",
            "HAYSTACK_DB": f"{self.input_file_ontologies}/carytown.hayson.json"
        }
        self.current_directory = CurrentDirectory(self.input_file_ontologies)
        self.current_directory.create_files()

    def tearDown(self):
        shutil.rmtree(self.input_file_ontologies, ignore_errors=True)

    @patch.object(URLProvider, '_get_url')
    def test_values_for_tag(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with cast(URLProvider, get_provider("shaystack.providers.url", self.environ)) as provider:
            provider._periodic_refresh = 2
            result = provider.values_for_tag("id")
            assert len(result) == 3

    def test_ops(self):
        provider = get_provider("shaystack.providers.url", {})
        result = provider.ops()
        assert len(result) == 5

    def test_about(self, ):
        """
        Args:
            mock_get_url:
        """
        with get_provider("shaystack.providers.url", self.environ) as provider:
            result = provider.about("http://localhost")
            assert result[0]['moduleName'] == 'URLProvider'

    @patch.object(URLProvider, '_get_url')
    def test_read_last_without_version_without_filter(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with cast(URLProvider, get_provider("shaystack.providers.url", self.environ)) as provider:
            provider._periodic_refresh = 2
            result = provider.read(40, None, None, None, None)
            assert len(result) == 3

    @patch.object(URLProvider, '_get_url')
    def test_read_with_the_exact_version_date(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version = datetime(2020, 11, 1, 16, 30, 0, 0, tzinfo=None)

            result = provider.read(0, None, None, None, date_version=version)
            assert len(result) == 1

    @patch.object(URLProvider, '_get_url')
    def test_read_with_version_earlier_than_all_versions(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_2 = datetime(2005, 11, 2, 0, 0, 2, 0, tzinfo=None)
            result = provider.read(0, None, None, None, date_version=version_2)
            assert len(result) == 0

    @patch.object(URLProvider, '_get_url')
    def test_read_with_version_more_recent_than_all_versions(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_2 = datetime(2050, 11, 1, 16, 30, 0, 0, tzinfo=None)
            result = provider.read(0, None, None, None, date_version=version_2)
            assert len(result) == 3

    @patch.object(URLProvider, '_get_url')
    def test_read_with_version_without_select_and_gridfilter(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_2 = datetime(2020, 11, 1, 16, 30, 0, 0, tzinfo=None)
            result = provider.read(0, None, None, None, date_version=version_2)
            assert len(result) == 1

    @patch.object(URLProvider, '_get_url')
    def test_read_version_with_select_and_gridfilter(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_1 = datetime(2020, 11, 10, 0, 0, 2, 0, tzinfo=None)
            result = provider.read(0, None, None, "id==@p_demo_r_23a44701-a89a6c66", version_1)
            assert len(result) == 1
            assert result[0]['id'] == Ref("@p_demo_r_23a44701-a89a6c66")

            version_2 = datetime(2021, 11, 3, 0, 0, 2, 0, tzinfo=None)
            result = provider.read(0, "id,dis", None, "id==@p_demo_r_23a44701-a89a6c66", version_2)
            assert list(result.column) == ['id', 'dis']
            assert list(result.keys()) == [Ref('p_demo_r_23a44701-a89a6c66', 'Carytown')]

    @patch.object(URLProvider, '_get_url')
    def test_read_version_with_ids(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_2 = datetime(2020, 11, 10, 0, 0, 2, 0, tzinfo=None)
            result = provider.read(0, None, [Ref("p_demo_r_23a44701-a89a6c66")], None, version_2)
            assert len(result) == 1
            assert result[0]['id'] == Ref("p_demo_r_23a44701-a89a6c66")

    @patch.object(URLProvider, '_get_url')
    def test_unexistant_version(self, mock_get_url):
        """
        Args:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
            version_0 = datetime(2018, 8, 1, 0, 0, 3, 0, tzinfo=None)
            url = f'{self.input_file_ontologies}/carytown.hayson.json'
            result = provider._download_grid(url, version_0)
            assert len(result) == 0

    @patch.object(URLProvider, '_get_url')
    def test_list_versions(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            versions = provider.versions()
            assert len(versions) == 3

    @patch.object(URLProvider, '_get_url')
    def test_given_wrong_url(self, mock_get_url):
        """
        Args:
            mock_refresh_version:
        """
        wrong_url = "wrongsheme://temp/url.zinc"
        mock_get_url.return_value = wrong_url
        with cast(URLProvider, get_provider("shaystack.providers.url", {})) as provider:
            provider._versions = {
                wrong_url:
                    OrderedDict([
                        (datetime(2021, 12, 8, 10, 55, 39, 50626, tzinfo=None), wrong_url)
                    ])
            }
            with self.assertRaises(ValueError) as cm:
                provider._download_grid(wrong_url, None)
            self.assertEqual(cm.exception.args[0], "A wrong url ! (url have to be ['file','s3','']")

    @patch.object(URLProvider, '_get_url')
    def test_his_read_with_version(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_2 = datetime(2021, 11, 1, 16, 30, 0, 0, tzinfo=None)
            result = provider.his_read(entity_id=Ref('p_demo_r_23a44701-a89a6c66'),
                                       date_version=version_2,
                                       date_range=(
                                           datetime.min.replace(tzinfo=pytz.UTC),
                                           datetime.max.replace(tzinfo=pytz.UTC)
                                       ))
            assert (len(result._row)) == 5  # 5 out of 8 since getting all TSs under 2021-11-01T16:30:00
            assert result._row[4] == {'ts': datetime(2021, 11, 1, 0, 0, tzinfo=pytz.UTC), 'val': 16.0}

    @patch.object(URLProvider, '_get_url')
    def test_his_read_with_version_with_dateRange(self, mock_get_url):
        """
        Args:
            mock_get_url:
        """
        mock_get_url.return_value = f"{self.input_file_ontologies}/carytown.hayson.json"
        with get_provider("shaystack.providers.url", self.environ) as provider:
            version_2 = datetime(2021, 11, 1, 16, 30, 0, 0, tzinfo=None)
            result = provider.his_read(entity_id=Ref('p_demo_r_23a44701-a89a6c66'),
                                       date_version=version_2,
                                       date_range=(

                                           datetime(2021, 9, 1, 16, 30, 0, 0, tzinfo=pytz.UTC),
                                           datetime(2022, 10, 1, 16, 30, 0, 0, tzinfo=pytz.UTC)
                                       ))
            print(result)
            assert (len(result._row)) == 2  # 5 out of 8 since getting all TSs < 2021-11-01T16:30:00
            # also between 2021-09-01T16:30:00 and 2022-10-01T16:30:00
            assert result._row[1] == {'ts': datetime(2021, 11, 1, 0, 0, tzinfo=pytz.UTC), 'val': 16.0}
