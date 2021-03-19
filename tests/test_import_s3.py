from datetime import datetime
from io import BytesIO

import pytz

from shaystack import Grid, MODE_ZINC, dump
from shaystack.providers.url import merge_timeseries


def _get_mock_s3():
    class MockS3:
        def __init__(self):
            self.history = None
            self.his_count = 0

        # noinspection PyMethodMayBeStatic,PyPep8Naming,PyUnusedLocal
        def get_object(self, Bucket, Key, IfNoneMatch):  # pylint: disable=unused-argument, no-self-use
            if Key == 'sample/carytown.zinc':
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
            self.put_params = params

    return MockS3()


def test_merge_timeseries_with_same_ts():
    ts = Grid(columns=["ts", "value"])
    ts.append({"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
               "value": 100})
    result_grid = merge_timeseries(ts, ts)
    assert ts == result_grid


def test_merge_timeseries_with_diff_ts_same_values():
    destination = Grid(columns=["ts", "value"])
    destination.append({"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
                        "value": 100})
    source = destination.copy()
    result_grid = merge_timeseries(source, destination)
    assert source == result_grid


def test_merge_timeseries_source_overflow():
    source = Grid(columns=["ts", "value"])
    source.append({"ts": datetime(2020, 2, 1, 0, 0, 2, 0, tzinfo=pytz.UTC),
                   "value": 100})
    destination = Grid(columns=["ts", "value"])
    destination.extend(
        [
            {"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 3, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
        ])
    result_grid = merge_timeseries(source, destination)
    assert destination == result_grid


def test_merge_timeseries_olds_values():
    """The destination has old data. Reinject the history"""
    source = Grid(columns=["ts", "value"])
    source.append(
        {"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100}
    )
    destination = Grid(columns=["ts", "value"])
    destination.extend(
        [
            {"ts": datetime(2020, 2, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 3, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
        ])
    expected_grid = Grid(columns=["ts", "value"])
    expected_grid.extend(
        [
            {"ts": datetime(2020, 1, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 2, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
            {"ts": datetime(2020, 3, 1, 0, 0, 2, 0, tzinfo=pytz.UTC), "value": 100},
        ]
    )
    result_grid = merge_timeseries(source, destination)
    assert result_grid == expected_grid
