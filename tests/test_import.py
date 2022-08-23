from shaystack.providers.url import _update_grid_on_file
from urllib.parse import urlparse
from shaystack import parse, MODE_HAYSON
import shutil
import os
import unittest
from nose.tools import assert_raises

class TestImportLocalFile(unittest.TestCase):

    def setUp(self):
        self.imported_file_ontologies = './imported_file_ontologies'
        self.source_file_ontologies = './ontology_files_to_import'
        self.compare_grid = True
        self.update_time_series = True
        self.force = False
        self.merge_ts = True
        os.chdir("../")
        print("\nHere we are: " + os.getcwd())
        if not os.path.exists(self.imported_file_ontologies):
            os.makedirs(self.imported_file_ontologies)
        if not os.path.exists(self.source_file_ontologies):
            os.makedirs(self.source_file_ontologies)

    def tearDown(self):
        shutil.rmtree(self.imported_file_ontologies, ignore_errors=True)
        shutil.rmtree(self.source_file_ontologies, ignore_errors=True)

    def read_ontology(self, file_path):
        with open(file_path) as f:
            grid = parse(f.read(), MODE_HAYSON)
        return grid

    def test_import(self):
        source_uri = f'sample/carytown.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert 'carytown.hayson.json' in os.listdir(self.imported_file_ontologies)
        assert len(os.listdir(self.imported_file_ontologies)) == 20  # 1 ontology + 19 TS files
        assert source_ontology == imported_ontology

    def test_import_when_version_is_2021(self):
        source_uri = 'sample/carytown-2021-11-01T16:30:00.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert 'carytown.hayson.json' in os.listdir(self.imported_file_ontologies)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 3  # 1 ontology + 2 TS files

    def test_import_when_version_is_2020(self):
        source_uri = 'sample/carytown-2020-11-01T16:30:00.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})
        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert 'carytown.hayson.json' in os.listdir(self.imported_file_ontologies)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 1  # 1 ontology, no TS files

    def test_update_existant_ontology_with_new_version(self):
        # copy new ontology version & TS files to source directory
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'
        shutil.copyfile('sample/carytown-2021-11-01T16:30:00.hayson.json',
                        f'{self.source_file_ontologies}/carytown.hayson.json')
        shutil.copyfile('sample/p_demo_r_23a44701-4ea35663.zinc',
                        f'{self.source_file_ontologies}/p_demo_r_23a44701-4ea35663.zinc')
        shutil.copyfile('sample/p_demo_r_23a44701-bbc36976.zinc',
                        f'{self.source_file_ontologies}/p_demo_r_23a44701-bbc36976.zinc')
        assert len(os.listdir(self.source_file_ontologies)) == 3  # 1 ontology + 2 TS files

        # copy an initial ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
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

        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 4  # 2 ontology versions + 2 TS files

    def test_update_existant_ontology_with_exact_same_ontology(self):
        # copy 2020 ontology version to source directory
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'
        shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                        source_uri)

        assert len(os.listdir(self.source_file_ontologies)) == 1  # 1 ontology 2020

        # copy 2020 same ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
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

        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert source_ontology == imported_ontology  # no change since same ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 1  # 1 ontology, no changes

    def test_update_existant_ontology_with_user_dated_ontology_but_same_entities(self):
        # copy 2020 ontology version to source directory
        source_uri = f'{self.source_file_ontologies}/carytown-2020-11-01T16:30:00.hayson.json'
        shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                        source_uri)

        assert len(os.listdir(self.source_file_ontologies)) == 1  # 1 ontology 2020

        # copy 2020 same ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown.hayson.json'
        shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
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
        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 1  # 1 ontology, no changes

    def test_update_existant_ontology_with_user_dated_ontology_but_different_entities(self):
        # copy 2021 ontology version to source directory
        source_uri = f'{self.source_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json'
        shutil.copyfile('sample/carytown-2021-11-01T16:30:00.hayson.json',
                        f'{self.source_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json')
        shutil.copyfile('sample/p_demo_r_23a44701-4ea35663.zinc',
                        f'{self.source_file_ontologies}/p_demo_r_23a44701-4ea35663.zinc')
        shutil.copyfile('sample/p_demo_r_23a44701-bbc36976.zinc',
                        f'{self.source_file_ontologies}/p_demo_r_23a44701-bbc36976.zinc')
        assert len(os.listdir(self.source_file_ontologies)) == 3  # 1 ontology + 2 TS files

        # copy most recent and 2021 ontology version to destination directory
        destination_uri = f'{self.imported_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json'
        shutil.copyfile('sample/carytown.hayson.json',
                        f'{self.imported_file_ontologies}/carytown.hayson.json')
        shutil.copyfile('sample/carytown-2021-11-01T16:30:00.hayson.json',
                        f'{self.imported_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json')

        # update the imported ontology with the one from source directory
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             self.compare_grid,
                             self.update_time_series,
                             self.force,
                             self.merge_ts,
                             {})

        source_ontology = self.read_ontology(source_uri)
        imported_ontology = self.read_ontology(destination_uri)
        assert source_ontology == imported_ontology
        assert len(os.listdir(self.imported_file_ontologies)) == 4  # 2 ontology versions, 2 TS files

    def test_when_file_without_version_extension_has_version_smaller_than_versionned_files(self):
        source_uri = f'{self.source_file_ontologies}/carytown.hayson.json'
        destination_uri = f'{self.imported_file_ontologies}/test2.hayson.json'
        print(os.listdir(self.source_file_ontologies))
        shutil.copytree('sample/', f'{self.source_file_ontologies}/', dirs_exist_ok=True)
        os.rename(f'{self.source_file_ontologies}/carytown-2021-11-01T16:30:00.hayson.json',
                  f'{self.source_file_ontologies}/carytown-2022-11-01T16:30:00.hayson.json')

        assert_raises(ValueError,
                      _update_grid_on_file,
                      urlparse(source_uri),
                      urlparse(destination_uri),
                      '',
                      self.compare_grid,
                      self.update_time_series,
                      self.force,
                      self.merge_ts,
                      {}
                      )

