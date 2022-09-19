from datetime import datetime

import pytz

from shaystack.datatypes import Ref
from shaystack.dumper import dump
from shaystack.grid import Grid, VER_3_0
from shaystack.parser import MODE_ZINC, parse


def _get_mock_s3():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col", "hisURI"])
    sample_grid.append({"id": Ref("id1"), "col": 1, "hisURI": "hist.zinc"})
    sample_grid.append({"id": Ref("id2"), "col": 2, "hisURI": "hist.zinc"})
    version_1 = datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
    version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
    version_3 = datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)

    # noinspection PyUnusedLocal
    class MockS3:
        __slots__ = "history", "his_count"

        def __init__(self):
            self.history = None
            self.his_count = 0

        # noinspection PyMethodMayBeStatic
        def list_object_versions(self, **args):  # pylint: disable=R0201, W0613
            return {
                "Versions":
                    [
                        {"VersionId": "1", "LastModified": version_1},
                        {"VersionId": "2", "LastModified": version_2},
                        {"VersionId": "3", "LastModified": version_3},
                    ]
            }

        def download_fileobj(self, bucket, path, stream, **params):  # pylint: disable=R0201, W0613
            if path == "grid.zinc":
                grid = sample_grid.copy()
                if params.get("ExtraArgs", None):
                    grid.metadata = {"v": params["ExtraArgs"]["VersionId"]}
                else:
                    grid.metadata = {"v": "last"}
                for row in grid:
                    row["hisURI"] = f"his{self.his_count}.zinc"
                    self.his_count += 1
                return stream.write(dump(grid, mode=MODE_ZINC).encode("utf-8"))
            return stream.write(dump(self.history, mode=MODE_ZINC).encode("utf-8"))

    return MockS3()


def _get_mock_s3_updated_ontology():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col", "hisURI"])
    sample_grid.append({"id": Ref("id1"), "col": 1, "hisURI": "hist.zinc"})
    sample_grid.append({"id": Ref("id2"), "col": 2, "hisURI": "hist.zinc"})
    sample_grid.append({"id": Ref("id3"), "col": 3, "hisURI": "hist.zinc"})
    version_1 = datetime(2020, 7, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
    version_2 = datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
    version_3 = datetime(2020, 12, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)

    his_grid = parse("""ver:"3.0" hisStart:2020-06-01T00:00:00+00:00 UTC hisEnd:2021-05-01T00:00:00+00:00 UTC
    ts,val
    2020-07-01T00:00:00+00:00 UTC,17
    2020-08-01T00:00:00+00:00 UTC,16
    2020-09-01T00:00:00+00:00 UTC,18
    2020-10-01T00:00:00+00:00 UTC,20
    2020-11-01T00:00:00+00:00 UTC,25
    2020-12-01T00:00:00+00:00 UTC,30""", mode=MODE_ZINC)

    class MockS3:
        __slots__ = "history", "his_count"

        def __init__(self):
            self.history = None
            self.his_count = 0

        def list_object_versions(self, **args):  # pylint: disable=unused-argument
            return {
                "Versions":
                    [
                        {"VersionId": "1", "LastModified": version_1},
                        {"VersionId": "2", "LastModified": version_2},
                        {"VersionId": "3", "LastModified": version_3},
                    ]
            }

        def download_fileobj(self, bucket, path, stream, **params):  # pylint: disable=unused-argument
            if path == "updated_grid.zinc":
                grid = sample_grid.copy()
                if params.get("ExtraArgs", None):
                    grid.metadata = {"v": params["ExtraArgs"]["VersionId"]}
                else:
                    grid.metadata = {"v": "last"}
                for row in grid:
                    row["hisURI"] = f"his{self.his_count}.zinc"
                    self.his_count += 1
                return stream.write(dump(grid, mode=MODE_ZINC).encode("utf-8"))

            if path in ["his0.zinc", "his1.zinc", "his2.zinc"]:
                return stream.write(dump(his_grid, mode=MODE_ZINC).encode("utf-8"))
            return stream.write(dump(self.history, mode=MODE_ZINC).encode("utf-8"))

    return MockS3()
