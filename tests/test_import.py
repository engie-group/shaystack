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
    shutil.rmtree('test_import_files', ignore_errors=True)
    shutil.rmtree('test_src_files', ignore_errors=True)
    os.mkdir('test_import_files')
    yield
    shutil.rmtree('test_import_files', ignore_errors=True)
    shutil.rmtree('test_src_files', ignore_errors=True)

@pytest.mark.usefixtures('clean_directories')
def test_import():
    source_uri = 'sample/carytown.hayson.json'
    dest_uri = 'test_import_files/test2.hayson.json'
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(dest_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    src_ontology = read_ontology(source_uri)
    imported_ontology = read_ontology(dest_uri)
    assert 'test2.hayson.json' in os.listdir('test_import_files')
    assert len(os.listdir('test_import_files')) == 20
    assert src_ontology == imported_ontology

@pytest.mark.usefixtures('clean_directories')
def test_import_when_version_is_2021():
    source_uri = 'sample/carytown-2021-11-01T16:30:00.hayson.json'
    dest_uri = 'test_import_files/test2.hayson.json'
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(dest_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    src_ontology = read_ontology(source_uri)
    imported_ontology = read_ontology(dest_uri)
    assert 'test2.hayson.json' in os.listdir('test_import_files')
    assert src_ontology == imported_ontology
    assert len(os.listdir('test_import_files')) == 3

@pytest.mark.usefixtures('clean_directories')
def test_import_when_version_is_2020():
    source_uri = 'sample/carytown-2021-11-01T16:30:00.hayson.json'
    dest_uri = 'test_import_files/test2.hayson.json'
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(dest_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    src_ontology = read_ontology(source_uri)
    imported_ontology = read_ontology(dest_uri)
    assert 'test2.hayson.json' in os.listdir('test_import_files')
    assert src_ontology == imported_ontology
    assert len(os.listdir('test_import_files')) == 3

@pytest.mark.usefixtures('clean_directories')
def test_when_src_file_is_a_versionned_file():
    source_uri = 'test_src_files/carytown.hayson.json'
    dest_uri = 'test_import_files/test2.hayson.json'
    shutil.copytree('sample', 'test_src_files')
    os.remove('test_src_files/carytown.hayson.json')
    _update_grid_on_file(urlparse(source_uri),
                         urlparse(dest_uri),
                         '',
                         compare_grid,
                         update_time_series,
                         force,
                         merge_ts,
                         {})
    src_ontology = read_ontology('test_src_files/carytown-2021-11-01T16:30:00.hayson.json')
    imported_ontology = read_ontology(dest_uri)
    assert 'test2.hayson.json' in os.listdir('test_import_files')
    assert src_ontology == imported_ontology
    assert len(os.listdir('test_import_files')) == 3


@pytest.mark.usefixtures('clean_directories')
def test_when_file_without_version_extension_has_version_smaller_than_versionned_files():
    source_uri = 'test_src_files/carytown.hayson.json'
    dest_uri = 'test_import_files/test2.hayson.json'
    shutil.copytree('sample', 'test_src_files')
    os.rename('test_src_files/carytown-2021-11-01T16:30:00.hayson.json','test_src_files/carytown-2022-11-01T16:30:00.hayson.json')
    with pytest.raises(ValueError):
        _update_grid_on_file(urlparse(source_uri),
                             urlparse(dest_uri),
                             '',
                             compare_grid,
                             update_time_series,
                             force,
                             merge_ts,
                             {})
