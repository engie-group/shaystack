from shaystack.providers.url import _update_grid_on_file
from urllib.parse import urlparse
from shaystack import parse, MODE_HAYSON
import shutil
import pytest
import os


def read_ontology(file_path):
    with open(file_path) as f:
        grid = parse(f.read(), MODE_HAYSON)
    return grid

compare_grid = True
update_time_series = True
force = False
merge_ts = True

@pytest.fixture
def clean_directories():
    shutil.rmtree('imported_file_ontologies', ignore_errors=True)
    shutil.rmtree('source_file_ontologies', ignore_errors=True)
    os.mkdir('imported_file_ontologies')
    os.mkdir('source_file_ontologies')
    yield
    shutil.rmtree('imported_file_ontologies', ignore_errors=True)
    shutil.rmtree('source_file_ontologies', ignore_errors=True)

@pytest.mark.usefixtures('clean_directories')
def test_import():
    source_uri = 'sample/carytown.hayson.json'
    destination_uri = 'imported_file_ontologies/test2.hayson.json'
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    source_ontology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    assert 'test2.hayson.json' in os.listdir('imported_file_ontologies')
    assert len(os.listdir('imported_file_ontologies')) == 20  # 1 ontology + 19 TS files
    assert source_ontology == imported_ontology

@pytest.mark.usefixtures('clean_directories')
def test_import_when_version_is_2021():
    source_uri = 'sample/carytown-2021-11-01T16:30:00.hayson.json'
    destination_uri = 'imported_file_ontologies/test2.hayson.json'
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    source_pntology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    print(os.listdir('imported_file_ontologies'))
    assert 'test2.hayson.json' in os.listdir('imported_file_ontologies')
    assert source_pntology == imported_ontology
    assert len(os.listdir('imported_file_ontologies')) == 3  # 1 ontology + 2 TS files

@pytest.mark.usefixtures('clean_directories')
def test_import_when_version_is_2020():
    source_uri = 'sample/carytown-2020-11-01T16:30:00.hayson.json'
    destination_uri = 'imported_file_ontologies/test2.hayson.json'
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    source_pntology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    assert 'test2.hayson.json' in os.listdir('imported_file_ontologies')
    assert source_pntology == imported_ontology
    assert len(os.listdir('imported_file_ontologies')) == 1  # 1 ontology, no TS files

@pytest.mark.usefixtures('clean_directories')
def test_update_existant_ontology_with_new_version():
    # copy new ontology version & TS files to source directory
    source_uri = 'source_file_ontologies/carytown.hayson.json'
    shutil.copyfile('sample/carytown-2021-11-01T16:30:00.hayson.json',
                    'source_file_ontologies/carytown.hayson.json')
    shutil.copyfile('sample/p_demo_r_23a44701-4ea35663.zinc',
                    'source_file_ontologies/p_demo_r_23a44701-4ea35663.zinc')
    shutil.copyfile('sample/p_demo_r_23a44701-bbc36976.zinc',
                    'source_file_ontologies/p_demo_r_23a44701-bbc36976.zinc')
    assert len(os.listdir('source_file_ontologies')) == 3  # 1 ontology + 2 TS files

    # copy an initial ontology version to destination directory
    destination_uri = 'imported_file_ontologies/carytown.hayson.json'
    shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                    'imported_file_ontologies/carytown.hayson.json')

    # update the imported ontology with the one from source directory
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})

    source_pntology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    assert source_pntology == imported_ontology
    assert len(os.listdir('imported_file_ontologies')) == 4  # 2 ontology versions + 2 TS files

@pytest.mark.usefixtures('clean_directories')
def test_update_existant_ontology_with_exact_same_ontology():
    # copy 2020 ontology version to source directory
    source_uri = 'source_file_ontologies/carytown.hayson.json'
    shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                    source_uri)

    assert len(os.listdir('source_file_ontologies')) == 1  # 1 ontology 2020

    # copy 2020 same ontology version to destination directory
    destination_uri = 'imported_file_ontologies/carytown.hayson.json'
    shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                    destination_uri)

    # update the imported ontology with the one from source directory
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})

    source_pntology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    assert source_pntology == imported_ontology
    assert len(os.listdir('imported_file_ontologies')) == 1  # 1 ontology, no changes

@pytest.mark.usefixtures('clean_directories')
def test_update_existant_ontology_with_user_dated_ontology_but_same_entities():
    # copy 2020 ontology version to source directory
    source_uri = 'source_file_ontologies/carytown-2020-11-01T16:30:00.hayson.json'
    shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                    source_uri)

    assert len(os.listdir('source_file_ontologies')) == 1  # 1 ontology 2020

    # copy 2020 same ontology version to destination directory
    destination_uri = 'imported_file_ontologies/carytown.hayson.json'
    shutil.copyfile('sample/carytown-2020-11-01T16:30:00.hayson.json',
                    destination_uri)

    # update the imported ontology with the one from source directory
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    print(os.listdir('imported_file_ontologies'))
    source_pntology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    assert source_pntology == imported_ontology
    assert len(os.listdir('imported_file_ontologies')) == 1  # 1 ontology, no changes

@pytest.mark.usefixtures('clean_directories')
def test_update_existant_ontology_with_user_dated_ontology_but_different_entities():
    # copy 2021 ontology version to source directory
    source_uri = 'source_file_ontologies/carytown-2021-11-01T16:30:00.hayson.json'
    shutil.copyfile('sample/carytown-2021-11-01T16:30:00.hayson.json',
                    'source_file_ontologies/carytown-2021-11-01T16:30:00.hayson.json')
    shutil.copyfile('sample/p_demo_r_23a44701-4ea35663.zinc',
                    'source_file_ontologies/p_demo_r_23a44701-4ea35663.zinc')
    shutil.copyfile('sample/p_demo_r_23a44701-bbc36976.zinc',
                    'source_file_ontologies/p_demo_r_23a44701-bbc36976.zinc')
    assert len(os.listdir('source_file_ontologies')) == 3  # 1 ontology + 2 TS files

    # copy most recent and 2021 ontology version to destination directory
    destination_uri = 'imported_file_ontologies/carytown-2021-11-01T16:30:00.hayson.json'
    shutil.copyfile('sample/carytown.hayson.json',
                    'imported_file_ontologies/carytown.hayson.json')
    shutil.copyfile('sample/carytown-2021-11-01T16:30:00.hayson.json',
                    'imported_file_ontologies/carytown-2021-11-01T16:30:00.hayson.json')

    # update the imported ontology with the one from source directory
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(destination_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})

    source_pntology = read_ontology(source_uri)
    imported_ontology = read_ontology(destination_uri)
    assert source_pntology == imported_ontology
    assert len(os.listdir('imported_file_ontologies')) == 4  # 2 ontology versions, 2 TS files

@pytest.mark.usefixtures('clean_directories')
def test_when_file_without_version_extension_has_version_smaller_than_versionned_files():
    source_uri = 'source_file_ontologies/carytown.hayson.json'
    destination_uri = 'imported_file_ontologies/test2.hayson.json'
    print(os.listdir('source_file_ontologies'))
    shutil.copytree('sample/', 'source_file_ontologies/', dirs_exist_ok=True)
    os.rename('source_file_ontologies/carytown-2021-11-01T16:30:00.hayson.json','source_file_ontologies/carytown-2022-11-01T16:30:00.hayson.json')
    with pytest.raises(ValueError):
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(destination_uri),
                             '',
                             compare_grid,
                             update_time_series,
                             force,
                             merge_ts,
                             {})
