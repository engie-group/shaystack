from datetime import datetime

import pytz

from shaystack.datatypes import Ref
from shaystack.dumper import dump
from shaystack.grid import Grid, VER_3_0
from shaystack.parser import MODE_ZINC


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
