from datetime import datetime

import pytz

import hszinc
from hszinc import MODE_ZINC, VER_3_0, Ref, Grid


def _get_mock_s3():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col"])
    sample_grid.append({"id": Ref("id1"), "col": 1})
    sample_grid.append({"id": Ref("id2"), "col": 2})
    version_1 = datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
    version_2 = datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
    version_3 = datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)

    class MockS3:
        def list_object_versions(self, **args):  # pylint: disable=R0201, W0613
            return {"Versions":
                [
                    {"VersionId": "1", "LastModified": version_1},
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
