"""
An Haystack Read-Only API provider to expose an Haystack file via the Haystack API.
The file must be referenced with the environment variable HAYSTACK_URL and may be the form:
- http://.../ontology.json
- http://.../ontology.zinc.gz
- file:///var/task/.../ontology.json
- .../ontology.json (implicitly prefixed with file:///var/task/)
- ftp://.../ontology.json
- s3://.../ontology.zinc (the lambda functions must have the privilege to read this file)
- ...

If the suffix is .gz, the body is unzipped.

If the AWS bucket use the versionning, the correct version are return, to correspond to
the version of the file at the `version_date`.

The time series to manage history must be referenced in entity:
- with inner ontology in tag 'history' or
- with the `hisURI` tag. This URI may be relative and MUST be in grid format.
"""
from __future__ import annotations

import functools
import gzip
import logging
import os
import threading
import urllib.request
from collections import OrderedDict
from datetime import datetime, MAXYEAR, MINYEAR, timedelta
from io import BytesIO
from pathlib import Path
from threading import Lock
from typing import Optional, Union, Tuple, Dict, Any, Set, List
from urllib.parse import urlparse, ParseResult

import pytz
from overrides import overrides

import hszinc
from hszinc import Grid, suffix_to_mode, Ref, MetadataObject
from hszinc.sortabledict import SortableDict
from .haystack_interface import HaystackInterface

BOTO3_AVAILABLE = False
try:
    import boto3
    from botocore.client import BaseClient

    BOTO3_AVAILABLE = True
except ImportError:
    pass

Timestamp = datetime

log = logging.getLogger("url.Provider")

LRU_SIZE, PERIODIC_REFRESH = 15, int(os.environ.get("REFRESH", "15"))


class Provider(HaystackInterface):
    """
    Expose an Haystack file via the Haystactk Rest API.
    """

    def __init__(self):
        self._s3_client = None
        self._lambda_client = None
        self._lock = Lock()
        self._versions = {}  # Dict of OrderedDict with date_version:version_id
        self._lru = []
        self._timer = None
        self._concurrency = None

    @overrides
    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> Set[Any]:
        grid = self._download_grid(self._get_url(), date_version)
        return {row[tag] for row in grid.filter(tag)}

    @overrides
    def versions(self) -> List[datetime]:
        parsed_uri = urlparse(self._get_url(), allow_fragments=False)
        self._refresh_versions(parsed_uri)
        return [date_version for date_version, _ in self._versions[parsed_uri.geturl()].items()]

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        about_data: Dict[str, Any] = grid[0]
        about_data.update(
            {  # pylint: disable=no-member
                "productVersion": "1.0",
                "moduleName": "URLProvider",
                "moduleVersion": "1.0",
            }
        )
        return grid

    @overrides
    def read(
            self,
            limit: int,
            select: Optional[str],
            entity_ids: Optional[Grid] = None,
            grid_filter: Optional[str] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:  # pylint: disable=unused-argument
        """ Implement Haystack 'read' """
        log.debug(
            "----> Call read(limit=%s, select='%s', ids=%s grid_filter='%s' date_version=%s)",
            limit,
            select,
            entity_ids,
            grid_filter,
            date_version,
        )
        grid = self._download_grid(self._get_url(), date_version)
        if entity_ids:
            result = Grid(grid.version, metadata=grid.metadata, columns=grid.column)
            for ref in entity_ids:
                result.append(grid[ref])
        else:
            result = grid.filter(grid_filter, limit if limit else 0)
        return self.select_grid(result, select)

    @staticmethod
    def select_grid(grid, select) -> Grid:
        if select:
            select = select.strip()
            if select not in ["*", '']:
                new_grid = Grid(version=grid.version, columns=grid.column, metadata=grid.metadata)
                new_cols = SortableDict()
                for col in select.split(','):
                    new_cols[col] = MetadataObject()
                for col, meta in grid.column.items():
                    if col in new_cols:
                        new_cols[col] = meta
                new_grid.column = new_cols
                for row in grid:
                    new_grid.append({key: val for key, val in row.items() if key in new_cols})
                return new_grid
        return grid

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]],
            date_version: Optional[datetime],
    ) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(
            "----> Call his_read(id=%s , range=%s, " "date_version=%s)",
            entity_id,
            dates_range,
            date_version,
        )

        grid = self._download_grid(self._get_url(), date_version)
        if entity_id in grid:
            entity = grid[entity_id]
            # Different solution to retrieve the history value
            # 1. use a file in the dir(HAYSTACK_URL)+entity['hisURI']
            if "hisURI" in entity:
                his_uri = str(entity["hisURI"])
                base = self._get_url()
                parsed_relative = urlparse(his_uri, allow_fragments=False)
                if not parsed_relative.scheme:
                    his_uri = base[: base.rfind("/")] + "/" + his_uri

                history = self._download_grid(his_uri, date_version)

                min_date = datetime(MAXYEAR, 1, 3, tzinfo=pytz.utc)
                max_date = datetime(MINYEAR, 12, 31, tzinfo=pytz.utc)

                for time_serie in history:
                    min_date = min(min_date, time_serie["date"])
                    max_date = max(max_date, time_serie["date"])

                grid.metadata = {
                    "id": entity_id,
                    "hisStart": min_date,
                    "hisEnd": max_date,
                }
                return history
            # 2. use the inner time series in tag 'history' with the type 'Grid'
            if "history" in entity:
                return entity["history"]
            raise ValueError(f"{entity_id} has no history")
        raise ValueError(f"id '{entity_id}' not found")

    def cancel(self):
        """ Stop the timer """
        if self._timer:
            self._timer.cancel()

    def _get_url(self):  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return os.environ.get("HAYSTACK_URL", "")

    def _lambda(self) -> BaseClient:
        if not self._lambda_client:  # Lazy init
            self._lambda_client = boto3.client("lambda",
                                               region_name=os.environ["AWS_REGION"],
                                               endpoint_url=os.environ.get("AWS_S3_ENDPOINT", None),
                                               verify=False,  # See https://tinyurl.com/y5tap6ys
                                               )
        return self._lambda_client

    def _function_concurrency(self) -> int:
        # if not self._concurrency:
        #     try:
        #         self._concurrency = self._lambda().get_function_concurrency(
        #             FunctionName=os.environ['AWS_LAMBDA_FUNCTION_NAME'])['ReservedConcurrentExecutions']
        #     except (KeyError):
        #         log.warning("Impossible to get `ReservedConcurrentExecutions`")
        #         self._concurrency = 1000  # Default value if error
        # return self._concurrency
        return 1000

    def _s3(self) -> BaseClient:
        # AWS_S3_ENDPOINT may be http://localhost:9000 to use minio (make start-minio)
        if not self._s3_client:  # Lazy init
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=os.environ.get("AWS_S3_ENDPOINT", None),
                verify=False,  # See https://tinyurl.com/y5tap6ys
            )
        return self._s3_client

    def _download_uri(self, parsed_uri: ParseResult, effective_version: datetime) -> bytes:
        """Download bytes from URI.
        The uri must be a classic url (file://, http:// ...)
        or a s3 urn (s3://).
        The suffix describe the file format.

        Return decompressed data
        """
        assert parsed_uri
        assert effective_version
        log.error("_download_uri('%s')", parsed_uri.geturl())
        if parsed_uri.scheme == "s3":
            assert BOTO3_AVAILABLE, "Use 'pip install boto3'"
            s3_client = self._s3()
            extra_args = None
            obj_versions = self._versions[parsed_uri.geturl()]
            version_id = None
            for date_version, version_id in obj_versions.items():
                if date_version == effective_version:
                    extra_args = {"VersionId": version_id}
                    break
            assert version_id, "Version not found"

            stream = BytesIO()
            s3_client.download_fileobj(
                parsed_uri.netloc, parsed_uri.path[1:], stream, ExtraArgs=extra_args
            )
            data = stream.getvalue()
        else:
            # Manage default cwd
            if not parsed_uri.scheme:
                uri = Path.cwd().joinpath(parsed_uri.geturl()).as_uri()
            with urllib.request.urlopen(uri) as response:
                data = response.read()
        if parsed_uri.path.endswith(".gz"):
            return gzip.decompress(data)
        return data

    def _periodic_refresh_versions(self, parsed_uri: ParseResult, first_time: bool):
        """ Refresh list of versions """
        # Refresh at a rounded period, then all cloud instances refresh data at the same time.
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        next_time = now.replace(minute=0, second=0) + timedelta(
            minutes=(now.minute + PERIODIC_REFRESH)
                    // PERIODIC_REFRESH
                    * PERIODIC_REFRESH
        )
        assert next_time > now
        if parsed_uri.scheme == "s3":
            assert BOTO3_AVAILABLE, "Use 'pip install boto3'"
            # FIXME: tester
            start_of_current_period = (next_time - timedelta(minutes=PERIODIC_REFRESH)).replace(tzinfo=pytz.UTC)
            s3_client = self._s3()
            obj_versions = [
                (v["LastModified"], v["VersionId"])
                for v in s3_client.list_object_versions(
                    Bucket=parsed_uri.netloc, Prefix=parsed_uri.path[1:]
                )["Versions"]
            ]
            self._lock.acquire()
            all_versions = self._versions.get(parsed_uri.geturl(), OrderedDict())
            concurrency = self._function_concurrency()
            for date_version, version_id in obj_versions:
                if date_version not in all_versions:
                    # Purge refresh during current period. Then, all AWS instance see the
                    # same data and wait the end of the current period to refresh.
                    # Else, it's may be possible to have two different versions if an
                    # new AWS Lambda instance was created after an updated version.
                    if not first_time or concurrency <= 1 or date_version < start_of_current_period:
                        all_versions[date_version] = version_id  # Add a slot
                    else:
                        log.warning("Ignore the version '%s' ignore until the next period.\n" +
                                    "Then, all lambda instance are synchronized.", version_id)
            self._versions[parsed_uri.geturl()] = all_versions  # Lru and versions)
            self._lock.release()
        else:
            self._versions[parsed_uri.geturl()] = {datetime.min: "direct_file"}

        if PERIODIC_REFRESH:
            partial_refresh = functools.partial(
                self._periodic_refresh_versions, parsed_uri, False
            )
            self._timer = threading.Timer((next_time - now).seconds, partial_refresh)
            self._timer.start()

    def _refresh_versions(self, parsed_uri: ParseResult):
        if not PERIODIC_REFRESH or parsed_uri.geturl() not in self._versions:
            self._periodic_refresh_versions(parsed_uri, True)

    @functools.lru_cache
    def _download_grid_effective_version(self, uri: str, effective_version: datetime) -> Grid:
        log.info("_download_grid(%s,%s)", uri, effective_version)
        parsed_uri = urlparse(uri, allow_fragments=False)
        body = self._download_uri(parsed_uri, effective_version).decode("utf-8")
        if body is None:
            raise ValueError("Empty body not supported")
        if uri.endswith(".gz"):
            uri = uri[:-3]

        mode = suffix_to_mode(os.path.splitext(uri)[1])
        if not mode:
            raise ValueError(
                "The file extension must be .(json|zinc|csv)[.gz]"
            )
        return hszinc.parse(body, mode)

    def _download_grid(self, uri: str, date_version: Optional[datetime]) -> Grid:
        parsed_uri = urlparse(uri, allow_fragments=False)
        self._refresh_versions(parsed_uri)
        effective_version = None  # The effective date to use
        for version, _ in self._versions[uri].items():
            if not date_version or version <= date_version:
                return self._download_grid_effective_version(uri, version)
        raise ValueError("Empty body not supported")
