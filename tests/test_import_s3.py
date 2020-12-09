from datetime import datetime
from io import BytesIO

import pytz

from haystackapi import Grid, MODE_ZINC, parse, dump
from haystackapi.providers.import_s3 import merge_timeseries


def _get_mock_s3():
    class MockS3:
        def __init__(self):
            self.history = None
            self.his_count = 0

        def get_object(self, Bucket, Key, IfNoneMatch):
            if 'sample/carytown.zinc' == Key:
                grid = Grid(columns=["hisURI"])
                grid.append({"hisURL": "ts.zinc"})
            else:
                grid = Grid(columns=["tz", "value"])
                grid.append({"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
                             "value": 100})
            data = dump(grid, MODE_ZINC).encode("UTF8")
            return {"Body": BytesIO(data)}

        put_params = None

        def put_object(self,
                       **params):
            put_params = params

    return MockS3()


def test_merge_timeseries_with_same_ts():
    ts = Grid(columns=["ts", "value"])
    ts.append({"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
               "value": 100})
    data, _ = merge_timeseries(ts, ts, MODE_ZINC, compress=False)
    result_grid = parse(data.decode("UTF8"), MODE_ZINC)
    assert ts == result_grid


def test_merge_timeseries_with_diff_ts_same_values():
    destination = Grid(columns=["ts", "value"])
    destination.append({"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
                        "value": 100})
    source = destination.copy()
    data, _ = merge_timeseries(source, destination, MODE_ZINC, compress=False)
    result_grid = parse(data.decode("UTF8"), MODE_ZINC)
    assert source == result_grid


def test_merge_timeseries_source_overflow():
    destination = Grid(columns=["ts", "value"])
    destination.append({"ts": datetime(2020, 2, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
                        "value": 100})
    source = Grid(columns=["ts", "value"])
    source.extend(
        [
            {"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 3, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
        ])
    data, _ = merge_timeseries(source, destination, MODE_ZINC, compress=False)
    result_grid = parse(data.decode("UTF8"), MODE_ZINC)
    assert source == result_grid


def test_merge_timeseries_olds_values():
    """ The destination has old data. Reinject the history """
    destination = Grid(columns=["ts", "value"])
    destination.append(
        {"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100}
    )
    source = Grid(columns=["ts", "value"])
    source.extend(
        [
            {"ts": datetime(2020, 2, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 3, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
        ])
    data, _ = merge_timeseries(source, destination, MODE_ZINC, compress=False)
    expected_grid = Grid(columns=["ts", "value"])
    expected_grid.extend(
        [
            {"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 2, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 3, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
        ]
    )
    result_grid = parse(data.decode("UTF8"), MODE_ZINC)
    assert result_grid == expected_grid

# FIXME: Finish the tests
# @patch('haystackapi.providers.import_s3._download_uri')
# @patch.object(boto3, 'client')
# def test_update_grid_on_s3(mock_s3,mock_dowload):
#     mock_s3.return_value = _get_mock_s3()
#     grid = Grid(columns=["hisURI","tz","value"])
#     grid.append({"hisURL": "ts.zinc","tz":datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),"value":100})
#     mock_dowload.return_value = dump(grid,MODE_ZINC).encode("UTF8")
#     update_grid_on_s3(urlparse("sample.zinc"),
#                       urlparse("s3://bucket/sample/carytown.zinc"),
#                       compare_grid=True,
#                       time_series=True,
#                       force=False,
#                       merge_ts=False,
#                       use_thread=False
#                       )
