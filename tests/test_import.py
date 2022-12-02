import json
import os
import shutil
import unittest
from urllib.parse import urlparse

import pytest

from shaystack import parse, MODE_HAYSON
from shaystack.providers.url import _update_grid_on_file

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

TS1 = """ver:"3.0" hisStart:2020-06-01T00:00:00+00:00 UTC hisEnd:2021-05-01T00:00:00+00:00 UTC
ts,val
2020-07-01T00:00:00+00:00 UTC,11
2020-08-01T00:00:00+00:00 UTC,11
2020-09-01T00:00:00+00:00 UTC,15
2020-10-01T00:00:00+00:00 UTC,13
2020-11-01T00:00:00+00:00 UTC,16
2020-12-01T00:00:00+00:00 UTC,13
"""

TS2 = """ver:"3.0" hisStart:2020-06-01T00:00:00+00:00 UTC hisEnd:2021-05-01T00:00:00+00:00 UTC
ts,val
2020-07-01T00:00:00+00:00 UTC,11
2020-08-01T00:00:00+00:00 UTC,11
2020-09-01T00:00:00+00:00 UTC,15
2020-10-01T00:00:00+00:00 UTC,13
2020-11-01T00:00:00+00:00 UTC,16
2020-12-01T00:00:00+00:00 UTC,13
"""

TS3 = """ver:"3.0" hisStart:2020-06-01T00:00:00+00:00 UTC hisEnd:2021-05-01T00:00:00+00:00 UTC
ts,val
2020-07-01T00:00:00+00:00 UTC,11
2020-08-01T00:00:00+00:00 UTC,11
2020-09-01T00:00:00+00:00 UTC,15
2020-10-01T00:00:00+00:00 UTC,13
2020-11-01T00:00:00+00:00 UTC,16
2020-12-01T00:00:00+00:00 UTC,13
"""


class CurrentDirectory:
    def __init__(self, in_dir, out_dir):
        self.in_dir = in_dir
        self.out_dir = out_dir
        if not os.path.exists(self.in_dir):
            os.makedirs(self.in_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

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

def read_ontology(file_path):
    with open(file_path) as f:
        grid = parse(f.read(), MODE_HAYSON)
    return grid

class TestImportLocalFile(unittest.TestCase):

    def setUp(self):
        self.imported_file_ontologies = f'{os.getcwd()}/imported_file_ontologies'
        self.source_file_ontologies = f'{os.getcwd()}/ontology_files_to_import'
        self.compare_grid = True
        self.update_time_series = True
        self.force = False
        self.merge_ts = True
        self.current_directory = CurrentDirectory(self.source_file_ontologies, self.imported_file_ontologies)
        self.current_directory.create_files()

    def tearDown(self):
        shutil.rmtree(self.imported_file_ontologies, ignore_errors=True)
        shutil.rmtree(self.source_file_ontologies, ignore_errors=True)

    def test_import(self):
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = read_ontology(source_uri)
        imported_ontology = read_ontology(destination_uri)
        assert 'carytown.hayson.json' in os.listdir(self.imported_file_ontologies)
        assert len(os.listdir(self.imported_file_ontologies)) == 4  # 1 ontology + 3 TS files
        assert source_ontology == imported_ontology
        assert len(imported_ontology._row) == 3

    def test_import_when_version_is_2021(self):
        source_uri = f'{self.source_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = read_ontology(source_uri)
        imported_ontology = read_ontology(destination_uri)
        assert 'carytown.hayson.json' in os.listdir(self.imported_file_ontologies)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 3  # 1 ontology + 2 TS files
        assert len(imported_ontology._row) == 2

    def test_import_when_version_is_2020(self):
        source_uri = f'{self.source_file_ontologies}/carytown-2020-11-01T16:30:00.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = read_ontology(source_uri)
        imported_ontology = read_ontology(destination_uri)
        assert 'carytown.hayson.json' in os.listdir(self.imported_file_ontologies)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 1  # 1 ontology
        assert len(imported_ontology._row) == 1

    def test_update_existant_ontology_with_new_version(self):
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'
        assert len(os.listdir(self.source_file_ontologies)) == 6  # 3 ontology + 3 TS files

        # copy an initial ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        shutil.copyfile(f'{self.source_file_ontologies}/carytown-2020-11-01T16:30:00.hayson.json',
                        f'{self.imported_file_ontologies}/carytown.hayson.json')

        # update the imported ontology with the one from source directory
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = read_ontology(source_uri)
        imported_ontology = read_ontology(destination_uri)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 5  # 2 ontology versions + 3 TS files
        assert len(imported_ontology._row) == 3  # 3 entities

    def test_update_existant_ontology_with_exact_same_ontology(self):
        # use the current ontology to be imported
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'

        # copy the same ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        shutil.copyfile(f'{self.source_file_ontologies}/carytown.hayson.json',
                        destination_uri)
        shutil.copyfile(f'{self.source_file_ontologies}/p_demo_r_23a44701-4ea35663.zinc',
                        f'{self.imported_file_ontologies}/p_demo_r_23a44701-4ea35663.zinc')
        shutil.copyfile(f'{self.source_file_ontologies}/p_demo_r_23a44701-bbc36976.zinc',
                        f'{self.imported_file_ontologies}/p_demo_r_23a44701-bbc36976.zinc')
        shutil.copyfile(f'{self.source_file_ontologies}/p_demo_r_23a44701-3940e690.zinc',
                        f'{self.imported_file_ontologies}/p_demo_r_23a44701-3940e690.zinc')
        assert len(os.listdir(self.imported_file_ontologies)) == 4  # 1 ontology + 3 TS files

        # update the imported ontology with the one from source directory
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})

        source_ontology = read_ontology(source_uri)
        imported_ontology = read_ontology(destination_uri)
        assert source_ontology == imported_ontology  # no change since same ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 4  # 1 ontology + 3 TS files
        assert len(imported_ontology._row) == 3  # 3 entities

    def test_update_existant_ontology_with_user_dated_ontology_but_same_entities(self):
        # copy 2020 ontology version to source directory
        source_uri = f'{self.source_file_ontologies}/carytown-2020-11-01T16:30:00.hayson.json'

        # copy 2020 same ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        shutil.copyfile(f'{self.source_file_ontologies}/carytown-2020-11-01T16:30:00.hayson.json',
                        destination_uri)

        # update the imported ontology with the one from source directory
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = read_ontology(source_uri)
        imported_ontology = read_ontology(destination_uri)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 1  # 1 ontology, no changes
        assert len(imported_ontology._row) == 1  # 1 entities

    def test_update_existant_ontology_with_user_dated_ontology_but_different_entities(self):
        # Use 2021 ontology version from source directory
        source_uri = f'{self.source_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json'

        # copy 2021 ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json'
        shutil.copyfile(f'{self.source_file_ontologies}/carytown-2020-11-01T16:30:00.hayson.json',
                        f'{self.imported_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json')
        shutil.copyfile(f'{self.source_file_ontologies}/carytown.hayson.json',
                        f'{self.imported_file_ontologies}/carytown.hayson.json')
        shutil.copyfile(f'{self.source_file_ontologies}/p_demo_r_23a44701-4ea35663.zinc',
                        f'{self.imported_file_ontologies}/p_demo_r_23a44701-4ea35663.zinc')
        shutil.copyfile(f'{self.source_file_ontologies}/p_demo_r_23a44701-bbc36976.zinc',
                        f'{self.imported_file_ontologies}/p_demo_r_23a44701-bbc36976.zinc')
        shutil.copyfile(f'{self.source_file_ontologies}/p_demo_r_23a44701-3940e690.zinc',
                        f'{self.imported_file_ontologies}/p_demo_r_23a44701-3940e690.zinc')
        # check the number of entities of the version 2021 before the update
        last2021_version = read_ontology(destination_uri)
        assert len(last2021_version._row) == 1  # 1 entities

        # update the imported ontology with the one from source directory
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = read_ontology(source_uri)
        naw_imported2021_version = read_ontology(destination_uri)
        assert source_ontology == naw_imported2021_version
        assert len(os.listdir(self.imported_file_ontologies)) == 5  # 2 ontology versions, 3 TS files
        # check the number of entities of the version 2021 after the update
        assert len(naw_imported2021_version._row) == 2  # 2 entities

    def test_when_file_without_version_extension_has_version_smaller_than_versionned_files(self):
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/test2.hayson.json'
        os.rename(f'{self.source_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json',
                  f'{self.source_file_ontologies}/carytown-2050-11-01T16:30:00.hayson.json')

        with pytest.raises(ValueError):
            _update_grid_on_file(
                urlparse(source_uri),
                urlparse(destination_uri),
                '',
                self.compare_grid,
                self.update_time_series,
                self.force,
                self.merge_ts,
                {}
            )
