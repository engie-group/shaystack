from datetime import datetime
from unittest.mock import patch

import pytz

import hszinc
from haystackapi import Ref
from haystackapi.providers import get_provider
from haystackapi.providers.url import Provider
from hszinc import Grid, VER_3_0, MODE_ZINC, MetadataObject


def _get_mock_s3():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col"])
    sample_grid.append({"id": Ref("id1"), "col": 1})
    sample_grid.append({"id": Ref("id2"), "col": 2})
    version_1 = datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)
    version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
    version_3 = datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)

    class MockS3:
        def list_object_versions(self, **args):  # pylint: disable=R0201, W0613
            return {"Versions":
                        [{"VersionId": "1", "LastModified": version_1},
                         {"VersionId": "2", "LastModified": version_2},
                         {"VersionId": "3", "LastModified": version_3},
                         ]
                    }

        def download_fileobj(self, bucket, path, stream, **params):  # pylint: disable=R0201, W0613
            grid = sample_grid.copy()
            if params.get("ExtraArgs", None):
                grid.metadata = {"v": params["ExtraArgs"]["VersionId"]}
            else:
                grid.metadata = {"v": "last"}
            return stream.write(hszinc.dump(grid, mode=MODE_ZINC).encode("utf-8"))

    return MockS3()


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
def test_values_for_tag(mock_s3, mock_get_url):
    mock_s3.return_value = _get_mock_s3()
    mock_get_url.return_value = "s3://bucket/grid.zinc"
    provider = get_provider("haystackapi.providers.url")
    result = provider.values_for_tag("col")
    assert result == {1.0, 2.0}
    result = provider.values_for_tag("id")
    assert result == {Ref("id1"), Ref("id2")}


def test_ops():
    try:
        provider = get_provider("haystackapi.providers.url")
        result = provider.ops()
        assert len(result) == 5
    finally:
        provider.cancel()


def test_about():
    try:
        provider = get_provider("haystackapi.providers.url")
        result = provider.about("http://localhost")
        assert result[0]['moduleName'] == 'URLProvider'
    finally:
        provider.cancel()


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
def test_read_last_without_filter(mock_s3, mock_get_url):
    try:
        mock_s3.return_value = _get_mock_s3()
        mock_get_url.return_value = "s3://bucket/grid.zinc"
        provider = get_provider("haystackapi.providers.url")
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "last"
    finally:
        provider.cancel()


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
def test_read_version_without_filter(mock_s3, mock_get_url):
    try:
        mock_s3.return_value = _get_mock_s3()
        mock_get_url.return_value = "s3://bucket/grid.zinc"
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        provider = get_provider("haystackapi.providers.url")
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"
    finally:
        provider.cancel()


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
def test_read_version_with_filter(mock_s3, mock_get_url):
    try:
        mock_s3.return_value = _get_mock_s3()
        mock_get_url.return_value = "s3://bucket/grid.zinc"
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        provider = get_provider("haystackapi.providers.url")
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")
    finally:
        provider.cancel()


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
def test_read_version_with_filter(mock_s3, mock_get_url):
    try:
        mock_s3.return_value = _get_mock_s3()
        mock_get_url.return_value = "s3://bucket/grid.zinc"
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        provider = get_provider("haystackapi.providers.url")
        result = provider.read(0, "id,other", None, "id==@id1", version_2)
        assert result.column == {"id": MetadataObject(), "other": MetadataObject()}
    finally:
        provider.cancel()


@patch.object(Provider, '_get_url')
@patch.object(Provider, '_s3')
def test_read_version_with_ids(mock_s3, mock_get_url):
    try:
        mock_s3.return_value = _get_mock_s3()
        mock_get_url.return_value = "s3://bucket/grid.zinc"
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        provider = get_provider("haystackapi.providers.url")
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[0]['id'] == Ref("id1")
    finally:
        provider.cancel()


@patch.object(Provider, '_s3')
def test_lru_version(mock):
    provider = get_provider("haystackapi.providers.url")
    try:
        version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        version_3 = datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
        version_4 = datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)

        last = None
        mock.return_value = _get_mock_s3()
        url = "s3://bucket/grid.zinc"
        assert provider._download_grid(url, last).metadata["v"] == "last"
        assert provider._download_grid(url, last).metadata["v"] == "last"
        assert provider._download_grid(url, version_2).metadata["v"] == "2"
        assert provider._download_grid(url, version_3).metadata["v"] == "3"
        try:
            provider._download_grid(url, version_4)  # Not present
            assert False
        except ValueError:
            pass
    finally:
        provider.cancel()


# TODO: tester le boot avec un doc rescent, avec ou sans concurrency à 1 ou +

@patch.object(Provider, '_s3')
def test_version(mock):
    mock.return_value = _get_mock_s3()
    provider = get_provider("haystackapi.providers.url")
    versions = provider.versions()
    assert len(versions) == 3
