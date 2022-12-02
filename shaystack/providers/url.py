# -*- coding: utf-8 -*-
# URL Provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
An Haystack Read-Only API provider to expose an Haystack file via the Haystack API.
The file must be referenced with the environment variable HAYSTACK_DB and may be the form:
- sample/carytown.zinc
- http://.../ontology.json
- http://.../ontology.zinc.gz
- file:///var/task/.../ontology.json
- ftp://<user>:<passwd>@.../ontology.json
- s3://.../ontology.zinc (the lambda functions must have the privilege to read this file)
- ...

If the suffix is .gz, the body is unzipped.

If the AWS bucket use the versioning, the correct version are return, to correspond to
the version of the file at the `version_date`.

The time series to manage history must be referenced in entity:
- with inner ontology in tag 'history' or
- with the `hisURI` tag. This URI may be relative and MUST be in grid format.
"""
import base64
import functools
import glob
import gzip
import logging
import os
import threading
import urllib
import urllib.request
from collections import OrderedDict
from datetime import datetime, MAXYEAR, MINYEAR, timedelta
from hashlib import md5
from io import BytesIO
from multiprocessing.pool import ThreadPool
from os.path import dirname
from pathlib import Path
from threading import Lock
from typing import Optional, Tuple, Any, List, cast, Dict
from urllib.error import URLError
from urllib.parse import urlparse, ParseResult

import pytz
from overrides import overrides

from .db_haystack_interface import DBHaystackInterface
from .. import dump, EmptyGrid
from ..datatypes import Ref
from ..exception import HaystackException
from ..grid import Grid
from ..parser import parse
from ..parser import suffix_to_mode
from ..sortabledict import SortableDict
from ..type import Entity
from ..zincparser import ZincParseException

BOTO3_AVAILABLE = False
try:
    # noinspection PyUnresolvedReferences
    import boto3
    from botocore.client import BaseClient  # pylint: disable=ungrouped-imports
    # noinspection PyUnresolvedReferences
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BaseClient = Any  # type: ignore

Timestamp = datetime

log = logging.getLogger("url.Provider")

_VERIFY = True  # See https://tinyurl.com/y5tap6ys
_LRU_SIZE = 15
_POOL_SIZE = 20

lock = Lock()


def check_version_file(uri, parsed_uri):
    suffixes = ''.join(Path(uri).suffixes)
    uri_without_suffix = parsed_uri.path.replace(suffixes, '')
    unordered_all_versions = {}
    creation_date = None
    for file_path in glob.glob(f"{uri_without_suffix}*{suffixes}"):
        str_version = file_path[len(uri_without_suffix) + 1:-len(suffixes)]
        if not str_version:
            # User file date
            creation_date = datetime.fromtimestamp(os.path.getmtime(uri))
            unordered_all_versions[creation_date] = file_path
        else:
            unordered_all_versions[datetime.fromisoformat(str_version)] = file_path
    ordered_date_from_str_versions = sorted(unordered_all_versions.keys(), reverse=True)
    if len(ordered_date_from_str_versions) > 0 and creation_date\
            and creation_date < ordered_date_from_str_versions[0]:
        log.debug('Current file has not the latest version date')
        raise ValueError
    return unordered_all_versions, ordered_date_from_str_versions


def _download_uri(parsed_uri: ParseResult, envs: Dict[str, str]) -> bytes:
    """ Download data from s3 or classical url """
    if parsed_uri.scheme == "s3":
        s3_client = boto3.client(
            "s3",
            endpoint_url=envs.get("AWS_S3_ENDPOINT", None),
            verify=_VERIFY,  # See https://tinyurl.com/y5tap6ys
        )

        stream = BytesIO()
        s3_client.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream)
        data = stream.getvalue()
    else:
        # Manage default cwd
        uri = parsed_uri.geturl()
        unordered_all_versions, ordered_date_from_str_versions = check_version_file(uri, parsed_uri)
        if len(ordered_date_from_str_versions) > 0:
            new_file = unordered_all_versions[ordered_date_from_str_versions[0]]
            new_parsed_uri = urlparse(new_file, allow_fragments=False)
            new_parsed_uri = new_parsed_uri._replace(path=_absolute_path(new_parsed_uri.path))
            uri = new_parsed_uri.geturl()
            if not new_parsed_uri.scheme:
                uri = Path.cwd().joinpath(uri).as_uri().replace('%3A', ':')
            else:
                uri = new_parsed_uri.geturl()
        else:
            uri = Path.cwd().joinpath(uri).as_uri()
        with urllib.request.urlopen(uri) as response:
            data = response.read()
    return data


def _absolute_path(path: str) -> str:
    if not path.startswith("/"):
        return path
    path_splitted = path.split('/')
    result = []  # type: ignore
    for part in path_splitted:
        if part == '..':
            result.pop()
        else:
            result.append(part)
    return '/'.join(result)


def _get_hash_of_s3_file(s3_client, parsed: ParseResult) -> str:
    try:
        head = s3_client.head_object(Bucket=parsed.hostname,
                                     Key=parsed.path[1:],
                                     )
        return head["ETag"][1:-1]
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchKey':
            # Target key not found
            return ''
        raise


def merge_timeseries(source_grid: Grid,
                     destination_grid: Grid,
                     ) -> Grid:
    """ Merge different time series.

        If the destination time series has older values, insert these values at the beginning
        of the current time series.
        It is not to forget values.
        destination_grid += source_grid
        Args:
            source_grid: Source TS grid
            destination_grid: Target TS grid with
    """
    assert 'ts' in source_grid.column, "The source grid must have ts,value columns"
    assert 'ts' in destination_grid.column
    if id(destination_grid) != id(source_grid):
        destination_grid.sort('ts')
        source_grid.sort('ts')
        result_grid = destination_grid.copy()
        if destination_grid:
            start_destination = destination_grid[0]['ts']  # type: ignore
            result_grid.extend(filter(lambda row: row['ts'] < start_destination, source_grid))  # type: ignore
        else:
            result_grid.extend(source_grid)
        result_grid.sort('ts')
        return result_grid

    return destination_grid


def read_grid_from_uri(uri: str, envs: Dict[str, str]) -> Grid:
    """
    Read a grid from uri.
    Args:
        uri: The URI to reference the datas (accept classical url or s3 url).
        envs: The environment variables

    Returns:
        The grid.
    """
    parsed_uri = urlparse(uri, allow_fragments=False)
    parsed_uri = parsed_uri._replace(path=_absolute_path(parsed_uri.path))

    data = _download_uri(parsed_uri, envs)
    if parsed_uri.path.endswith(".gz"):
        data = gzip.decompress(data)
    suffix = Path(parsed_uri.path).suffix
    if suffix == ".gz":
        suffix = Path(parsed_uri.path).suffixes[-2]

    input_mode = suffix_to_mode(suffix)
    grid = parse(data.decode("utf-8-sig"), input_mode)  # type: ignore
    return grid


def _update_grid_on_file(parsed_source: ParseResult,  # pylint: disable=too-many-locals,too-many-arguments
                         parsed_destination: ParseResult,
                         customer_id: str,
                         compare_grid: bool,
                         update_time_series: bool,
                         force: bool,  # Copy even if the data is identical
                         merge_ts: bool,  # Merge current TS with the new period of TS
                         envs: Dict[str, str]
                         ) -> None:  # pylint: disable=too-many-arguments

    log.debug("update %s", (parsed_source.geturl(),))
    suffix = "".join(Path(parsed_source.path).suffixes)
    use_gzip = False

    # Copy from file to file
    source_data = _download_uri(parsed_source, envs)
    source_grid = None
    if suffix == ".gz":
        use_gzip = True
    if update_time_series or compare_grid or merge_ts:
        unzipped_source_data = source_data
        if use_gzip:
            unzipped_source_data = gzip.decompress(source_data)

        source_grid = parse(unzipped_source_data.decode("utf-8-sig"),
                            suffix_to_mode(suffix))  # type: ignore

        try:
            destination_data = _download_uri(parsed_destination, envs)
            if parsed_source.path.endswith(".gz"):
                destination_data = gzip.decompress(destination_data)
            destination_grid = parse(destination_data.decode("utf-8-sig"),
                                     suffix_to_mode(suffix))  # type: ignore
        except URLError:
            log.warning("URLError file not found under %s", (parsed_destination.geturl()))
            destination_grid = EmptyGrid.copy()

        except ZincParseException:
            # Ignore. Override target
            log.warning("Zinc parser exception with %s", (parsed_destination.geturl()))
            destination_grid = EmptyGrid

        if force or not compare_grid or (destination_grid - source_grid):
            if use_gzip:
                source_data = gzip.compress(source_data)
            # Rename default file to versionned file
            if not force:
                date_old_version = None
                file_path = Path(parsed_destination.path)
                old_filename_elements = file_path.name.split('/')[-1].split('.', 1)[0].split('-', 1)
                if len(old_filename_elements) > 1:
                    try:
                        date_old_version = datetime.strptime(old_filename_elements[1], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        log.error("Incorrect data format, should be YYYY-MM-DDThh:mm:dd")
                        raise

                if file_path.exists():
                    # attention vérifier si le nom du fichier à déjà la date, sinon on garde la date physique
                    # Une solution: Import d'un fichier d'une date ancienne interdit
                    if date_old_version:
                        prefix, suffix = file_path.name.split('.', 1)
                        prefix = prefix.split("-", 1)[0]
                    else:
                        date_old_version: datetime = datetime.fromtimestamp(  # type: ignore
                                os.path.getmtime(parsed_destination.path)
                            ).replace(tzinfo=None)
                        prefix, suffix = file_path.name.split('.', 1)

                    old_name = f"{prefix}-{date_old_version.isoformat()}.{suffix}"  # type: ignore
                    file_path.rename(Path(file_path.parent, old_name))

            with open(parsed_destination.path, "wb") as file:
                file.write(source_data)
            log.info("%s updated", parsed_source.geturl())
        else:
            log.debug("%s not modified (same grid)", parsed_source.geturl())
    if update_time_series:
        _import_ts(parsed_source, parsed_destination, source_grid,  # type: ignore
                   customer_id,
                   force, merge_ts, envs=envs)


def _update_grid_on_s3(parsed_source: ParseResult,  # pylint: disable=too-many-locals,too-many-arguments
                       parsed_destination: ParseResult,
                       customer_id: str,
                       compare_grid: bool,
                       update_time_series: bool,
                       force: bool,  # Copy even if the data is identical
                       merge_ts: bool,  # Merge current TS with the new period of TS
                       envs: Dict[str, str]
                       ) -> None:  # pylint: disable=too-many-arguments
    log.debug("update %s", (parsed_source.geturl(),))
    s3_client = boto3.client(
        "s3",
        endpoint_url=envs.get("AWS_S3_ENDPOINT", None),
    )
    suffix = "".join(Path(parsed_source.path).suffixes)
    use_gzip = False
    destination_grid = EmptyGrid.copy()
    source_grid = EmptyGrid.copy()

    if not compare_grid:
        # Try to copy from s3 to s3
        if update_time_series:
            source_data = _download_uri(parsed_source, envs)
            md5_digest = md5(source_data)
            source_etag = ''
            if not force:
                source_etag = md5_digest.hexdigest()
        else:
            source_etag = _get_hash_of_s3_file(s3_client, parsed_source)
        target_etag = _get_hash_of_s3_file(s3_client, parsed_destination)

        if force or source_etag != target_etag:
            s3_client.copy_object(Bucket=parsed_destination.hostname,
                                  Key=parsed_destination.path[1:],
                                  CopySource={'Bucket': parsed_source.hostname,
                                              'Key': parsed_source.path[1:]
                                              },
                                  )
            log.info("%s updated (copy between s3 bucket)", parsed_source.geturl())
        else:
            log.debug("%s not modified (same grid)", parsed_source.geturl())
    else:
        # Copy from local to s3
        source_data = _download_uri(parsed_source, envs)
        md5_digest = md5(source_data)
        b64_digest = base64.b64encode(md5_digest.digest()).decode("UTF8")
        source_etag = ''
        source_grid = None  # type: ignore
        if not force:
            source_etag = md5_digest.hexdigest()
        if update_time_series or compare_grid or merge_ts:
            unzipped_source_data = source_data
            if suffix.endswith('.gz'):
                use_gzip = True
                unzipped_source_data = gzip.decompress(source_data)
                suffix = suffix[:-3]

            try:
                source_grid = parse(unzipped_source_data.decode("utf-8-sig"),
                                    suffix_to_mode(suffix))  # type: ignore
                path = parsed_destination.path[1:]
                destination_data = s3_client.get_object(Bucket=parsed_destination.hostname,
                                                        Key=path,
                                                        IfNoneMatch=source_etag)['Body'].read()
                if parsed_source.path.endswith(".gz"):
                    destination_data = gzip.decompress(destination_data)
                destination_grid = parse(destination_data.decode("utf-8-sig"),
                                         suffix_to_mode(suffix))  # type: ignore

            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchKey':
                    # Target key not found
                    destination_grid = EmptyGrid.copy()
                    destination_grid.column = SortableDict({'ts': {}, 'val': {}})
                elif ex.response['Error']['Code'] == '304':
                    # Target not modified
                    if source_grid:
                        destination_grid = source_grid
                    else:
                        raise
                else:
                    raise
            except ZincParseException:
                # Ignore. Override target
                log.warning("Zinc parser exception with %s", (parsed_destination.geturl()))
                destination_grid = EmptyGrid

        if force or not compare_grid or (destination_grid - source_grid):
            if not force and merge_ts:  # PPR: if TS, limit the number of AWS versions ?
                destination_grid = merge_timeseries(source_grid, destination_grid)
                source_data = dump(destination_grid, suffix_to_mode(suffix)).encode('UTF8')  # type: ignore
                if use_gzip:
                    source_data = gzip.compress(source_data)
                md5_digest = md5(source_data)
                b64_digest = base64.b64encode(md5_digest.digest()).decode("UTF8")

            s3_client.put_object(Body=source_data,
                                 Bucket=parsed_destination.hostname,
                                 Key=parsed_destination.path[1:],
                                 ContentMD5=b64_digest
                                 )
            log.info("%s updated (put in s3 bucket)", parsed_source.geturl())
        else:
            log.debug("%s not modified (same grid)", parsed_source.geturl())
    if update_time_series:
        _import_ts(parsed_source, parsed_destination, source_grid,
                   customer_id,
                   force, merge_ts, envs=envs)


# noinspection PyUnusedLocal
def _import_ts(parsed_source: ParseResult,  # pylint: disable=too-many-locals,too-many-arguments
               parsed_destination: ParseResult,
               source_grid: Grid,
               customer_id: str,
               force: bool,  # Copy even if the data is identical
               merge_ts: bool,  # Merge current TS with the new period of TS
               envs: Dict[str, str],
               use_thread: bool = True):
    # Now, it's time to upload the referenced time-series
    if parsed_destination.scheme and parsed_destination.scheme in ["s3", "file"]:
        raise ValueError("I can not import the data with a URL that is not on s3 or file")
    source_url = parsed_source.geturl()
    source_home = source_url[0:source_url.rfind('/') + 1]
    destination_url = parsed_destination.geturl()
    destination_home = destination_url[0:destination_url.rfind('/') + 1]
    requests = []
    for row in source_grid:
        if "hisURI" in row:
            source_time_serie = source_home + row["hisURI"]
            destination_time_serie = destination_home + row["hisURI"]
            if use_thread:
                requests.append((
                    urlparse(source_time_serie),
                    urlparse(destination_time_serie),
                    customer_id,   # customer_id
                    True,  # compare_grid
                    False,  # update_time_series
                    True,  # force
                    True,  # merge_ts
                    envs))

            else:
                if parsed_destination.scheme == "s3":
                    _update_grid_on_s3(
                        urlparse(source_time_serie),
                        urlparse(destination_time_serie),
                        customer_id=customer_id,
                        compare_grid=True,
                        update_time_series=False,
                        force=True,
                        merge_ts=True,
                        envs=envs)
                else:
                    _update_grid_on_file(
                        urlparse(source_time_serie),
                        urlparse(destination_time_serie),
                        customer_id=customer_id,
                        compare_grid=True,
                        update_time_series=False,
                        force=True,
                        merge_ts=True,
                        envs=envs)

    if requests:
        if parsed_destination.scheme == "s3":
            with ThreadPool(processes=_POOL_SIZE) as pool:
                pool.starmap(_update_grid_on_s3, requests)
        else:
            with ThreadPool(processes=_POOL_SIZE) as pool:
                pool.starmap(_update_grid_on_file, requests)


# noinspection PyMethodMayBeStatic
class Provider(DBHaystackInterface):  # pylint: disable=too-many-instance-attributes
    """
    Expose an Haystack file via the Haystactk Rest API.
    """
    __slots__ = "_periodic_refresh", "_tls_verify", "_s3_client", "_lambda_client", "_lock", "_versions", \
                "_lru", "_timer", "_concurrency"

    @property
    def name(self) -> str:
        return "URL"

    def __init__(self, envs: Dict[str, str]):
        DBHaystackInterface.__init__(self, envs)
        self._periodic_refresh = int(envs.get("REFRESH", "15"))
        self._tls_verify = envs.get("TLS_VERIFY", "true") == "true"

        self._s3_client = None
        self._lambda_client = None
        self._lock = Lock()
        self._versions = {}   # type: ignore  # Dict of OrderedDict with date_version:version_id
        self._lru = []  # type: ignore
        self._timer = None
        self._concurrency = None
        log.info("Use %s", self._get_url())

    @overrides
    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        grid = self._download_grid(self._get_url(), date_version)
        return sorted({row[tag] for row in grid.filter(tag)})

    @overrides
    def versions(self) -> List[datetime]:
        parsed_uri = urlparse(self._get_url(), allow_fragments=False)
        self._refresh_versions(parsed_uri)
        return [date_version for date_version, _ in self._versions[parsed_uri.geturl()].items()]

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        about_data = cast(Entity, grid[0])
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
            entity_ids: Optional[List[Ref]] = None,
            grid_filter: Optional[str] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        """ Implement Haystack 'read' """
        log.debug(
            "----> Call read(limit=%s, select='%s', ids=%s grid_filter='%s' date_version=%s)",
            limit,
            select,
            entity_ids,
            grid_filter,
            date_version,
        )
        self.create_db()
        grid = self._download_grid(self._get_url(), date_version)
        if entity_ids:
            result = Grid(grid.version, metadata=grid.metadata, columns=grid.column)
            for ref in entity_ids:
                result.append(grid[ref])
        else:
            result = grid.filter(grid_filter, limit if limit else 0)  # type: ignore
        return result.select(select)

    @overrides
    def his_read(  # type: ignore
            self,
            entity_id: Ref,
            dates_range: Tuple[datetime, datetime],
            date_version: Optional[datetime] = None
    ) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(
            "----> Call his_read(id=%s , range=%s, " "date_version=%s)",
            entity_id,
            dates_range,
            date_version,
        )
        self.create_db()
        grid = self._download_grid(self._get_url(), date_version)
        if entity_id in grid:
            entity = grid[entity_id]
            # Different solution to retrieve the history value
            # 1. use a file in the dir(HAYSTACK_DB)+entity['hisURI']
            if "hisURI" in entity:
                base = dirname(self._get_url())
                his_uri = base + '/' + str(entity["hisURI"])  # type: ignore
                history = self._download_grid(his_uri, None)
                # assert history is sorted by date time
                # Remove data after the date_version
                history = history.copy()
                if not date_version:
                    date_version = datetime.now().replace(tzinfo=pytz.UTC)
                for row in history:
                    if row['ts'] >= date_version.replace(tzinfo=pytz.UTC):
                        history = history[0:history.index(row)]  # type: ignore
                        break

                # Remove data not in the range
                filter_history = [row for row in history if
                                  dates_range[0] <= cast(datetime, cast(Entity, row)['ts']) < dates_range[1]]
                history.clear()
                history.extend(filter_history)

                if history:
                    min_date = datetime(MAXYEAR, 1, 3, tzinfo=pytz.utc)
                    max_date = datetime(MINYEAR, 12, 31, tzinfo=pytz.utc)
                    for time_serie in history:
                        min_date = min(min_date, cast(datetime, cast(Entity, time_serie)["ts"]))
                        max_date = max(max_date, cast(datetime, cast(Entity, time_serie)["ts"]))
                else:
                    min_date = date_version
                    max_date = date_version

                history.metadata = {  # type: ignore
                    "id": entity_id,
                    "hisStart": min_date,
                    "hisEnd": max_date,
                }
                return history
            # 2. use the inner time series in tag 'history' with the type 'Grid'
            if "history" in entity:
                return entity["history"]  # type: ignore
            raise HaystackException(f"{entity_id} has no history")
        raise HaystackException(f"id '{entity_id}' not found")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """ Stop the timer """
        if self._timer:
            self._timer.cancel()

    def __del__(self):
        self.__exit__(None, None, None)

    def _get_url(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return self._envs.get("HAYSTACK_DB", "")

    def _lambda(self) -> BaseClient:
        if not self._lambda_client:  # Lazy init
            self._lambda_client = boto3.client("lambda",
                                               region_name=self._envs["AWS_REGION"],
                                               endpoint_url=self._envs.get("AWS_S3_ENDPOINT", None),
                                               verify=self._tls_verify,  # See https://tinyurl.com/y5tap6ys
                                               )
        return self._lambda_client  # type: ignore

    def _function_concurrency(self) -> int:  # pylint: disable=no-self-use
        return 1000
        # if not self._concurrency:
        #     try:
        #         self._concurrency = self._lambda().get_function_concurrency(
        #             FunctionName=os.environ['AWS_LAMBDA_FUNCTION_NAME'])['ReservedConcurrentExecutions']
        #     except (KeyError):
        #         log.warning("Impossible to get `ReservedConcurrentExecutions`")
        #         self._concurrency = 1000  # Default value if error
        # return self._concurrency

    def _s3(self) -> BaseClient:
        # AWS_S3_ENDPOINT may be http://localhost:9000 to use minio (make start-minio)
        if not self._s3_client:  # Lazy init
            self._s3_client = boto3.client(
                "s3",
                region_name=self._envs.get('AWS_REGION', ''),
                endpoint_url=self._envs.get("AWS_S3_ENDPOINT", None),
                verify=self._tls_verify,  # See https://tinyurl.com/y5tap6ys
            )
        return self._s3_client  # type: ignore

    def _download_uri(self, parsed_uri: ParseResult, effective_version: datetime) -> bytes:
        """Download bytes from URI.
        The uri must be a classic url (file://, http:// ...)
        or a s3 urn (s3://).
        The suffix describe the file format.

        Return decompressed data
        """
        assert parsed_uri
        assert effective_version
        log.info("_download_uri('%s')", parsed_uri.geturl())
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
            s3_client.download_fileobj(  # type: ignore
                parsed_uri.netloc, parsed_uri.path[1:], stream, ExtraArgs=extra_args
            )
            data = stream.getvalue()
        else:
            # Manage default cwd
            if not parsed_uri.scheme:
                parsed_uri = urlparse(Path.resolve(Path.cwd().joinpath(parsed_uri.geturl())).as_uri())
            with urllib.request.urlopen(parsed_uri.geturl()) as response:
                data = response.read()
        if parsed_uri.path.endswith(".gz"):
            return gzip.decompress(data)
        return data

    def _periodic_refresh_versions(self, parsed_uri: ParseResult, first_time: bool) -> None:
        """ Refresh list of versions """
        # Refresh at a rounded period, then all cloud instances refresh data at the same time.
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        minutes_delta = now.minute
        if self._periodic_refresh != 0:
            minutes_delta = (now.minute + self._periodic_refresh) // \
                            self._periodic_refresh * self._periodic_refresh
        else:
            self.cache_clear()
        next_time = now.replace(minute=0) + timedelta(minutes=minutes_delta)
        assert next_time >= now
        if parsed_uri.scheme == "s3":
            assert BOTO3_AVAILABLE, "Use 'pip install boto3'"
            start_of_current_period = \
                (next_time - timedelta(minutes=self._periodic_refresh)).replace(tzinfo=pytz.UTC)
            s3_client = self._s3()
            s3_obj_version = s3_client.list_object_versions(  # type: ignore
                Bucket=parsed_uri.netloc, Prefix=parsed_uri.path[1:]
            )
            if "Versions" in s3_obj_version:
                obj_versions = [
                    (v["LastModified"], v["VersionId"])
                    for v in s3_obj_version["Versions"]
                ]
            else:
                meta = s3_client.get_object(Bucket=parsed_uri.netloc, Key=parsed_uri.path[1:])  # type: ignore
                obj_versions = [meta["LastModified"], meta["VersionId"]]
            obj_versions = sorted(obj_versions, key=lambda x: x[0], reverse=True)
            self._lock.acquire()  # pylint: disable=consider-using-with
            unordered_all_versions = self._versions.get(parsed_uri.geturl(), OrderedDict())
            concurrency = self._function_concurrency()
            for date_version, version_id in obj_versions:
                if date_version not in unordered_all_versions:
                    # Purge refresh during current period. Then, all AWS instance see the
                    # same data and wait the end of the current period to refresh.
                    # Else, it's may be possible to have two different versions if an
                    # new AWS Lambda instance was created after an updated version.
                    if not first_time or concurrency <= 1 or date_version < start_of_current_period:
                        unordered_all_versions[date_version] = version_id  # Add a slot
                    else:
                        log.warning("Ignore the version '%s' ignore until the next period.\n" +
                                    "Then, all lambda instance are synchronized.", version_id)
            self._versions[parsed_uri.geturl()] = unordered_all_versions  # Lru and versions)
            self._lock.release()
        else:
            name, suffix = parsed_uri.path.split(".", 1)
            unordered_all_versions = {}
            creation_date = datetime.fromtimestamp(os.path.getmtime(parsed_uri.path)).replace(tzinfo=pytz.UTC)
            for file_path in glob.glob(f"{name}*.{suffix}"):
                str_version = file_path[len(name) + 1:-len(suffix) - 1]
                if str_version:
                    unordered_all_versions[datetime.fromisoformat(str_version).replace(tzinfo=pytz.UTC)]\
                        = file_path
            ordered_date_from_str_versions = sorted(unordered_all_versions.keys(), reverse=True)
            # On n'est pas censé l'accepter, péter une erreur (import file dans le bon ordre)
            if len(ordered_date_from_str_versions) > 0 and creation_date < ordered_date_from_str_versions[0]:
                creation_date = ordered_date_from_str_versions[0] + timedelta(days=1)
            unordered_all_versions[creation_date] = parsed_uri.path
            all_versions = OrderedDict()
            for k in sorted(unordered_all_versions.keys(), reverse=True):
                all_versions[k] = unordered_all_versions[k]
            self._versions[parsed_uri.geturl()] = all_versions

        if self._periodic_refresh:
            partial_refresh = functools.partial(
                self._periodic_refresh_versions, parsed_uri, False
            )
            self._timer = threading.Timer((next_time - now).seconds, partial_refresh)  # type: ignore
            self._timer.daemon = True  # type: ignore
            self._timer.start()  # type: ignore

    def _refresh_versions(self, parsed_uri: ParseResult) -> None:
        if not self._periodic_refresh or parsed_uri.geturl() not in self._versions:
            self._periodic_refresh_versions(parsed_uri, True)

    @functools.lru_cache(maxsize=_LRU_SIZE)
    def _download_grid_effective_version(self, uri: str,  # pylint: disable=method-hidden
                                         effective_version: datetime) -> Grid:
        log.info("_download_grid(%s,%s)", uri, effective_version)
        parsed_uri = urlparse(uri, allow_fragments=False)
        byte_array = self._download_uri(parsed_uri, effective_version)
        if byte_array[:2] == b'\xef\xbb':
            body = byte_array.decode("utf-8-sig")
        else:
            body = byte_array.decode("utf-8")
        if body is None:
            raise ValueError("Empty body not supported")
        if uri.endswith(".gz"):
            uri = uri[:-3]
        if '.hayson.json' in uri:
            suffix = '.hayson.json'
        else:
            suffix = os.path.splitext(uri)[1]
        mode = suffix_to_mode(suffix)
        if not mode:
            raise ValueError(
                "The file extension must be .(json|zinc|csv)[.gz]"
            )
        return parse(body, mode)

    def _download_grid(self, uri: str, date_version: Optional[datetime]) -> Grid:
        parsed_uri = urlparse(uri, allow_fragments=False)
        parsed_uri = parsed_uri._replace(path=_absolute_path(parsed_uri.path))
        response_grid = Grid(columns=["ts", "val"])
        if parsed_uri.scheme != 's3':
            if parsed_uri.scheme not in ['', 'file']:
                raise ValueError("A wrong url ! (url have to be ['file','s3','']")
        self._refresh_versions(parsed_uri)
        for version, version_url in self._versions[parsed_uri.geturl()].items():
            if not date_version or version <= date_version.replace(tzinfo=pytz.UTC):
                if parsed_uri.scheme == 's3':
                    response_grid = self._download_grid_effective_version(parsed_uri.geturl(), version)
                else:
                    response_grid = self._download_grid_effective_version(version_url, version)
                break
        return response_grid

    # pylint: disable=no-member
    def set_lru_size(self, size: int) -> None:
        # noinspection PyAttributeOutsideInit
        self._download_grid_effective_version = \
            functools.lru_cache(size,  # type: ignore
                                Provider._download_grid_effective_version.__wrapped__)  # type: ignore

    # pylint: enable=no-member

    def cache_clear(self) -> None:
        """ Force to clear the local cache. """
        # noinspection PyUnresolvedReferences
        self._download_grid_effective_version.cache_clear()  # pylint: disable=no-member

    @overrides
    def create_db(self) -> None:
        """
        Create the database and schema.
        """
        return

    @overrides
    def purge_db(self) -> None:
        """ Purge the current database. """
        return  # PPR: purge s3 files ?

    @overrides
    def import_data(self,  # pylint: disable=too-many-arguments
                    source_uri: str,
                    customer_id: str = '',
                    reset: bool = False,
                    version: Optional[datetime] = None
                    ) -> None:
        """
        Import source grid file on destination, only if something was changed.
        The source can use all kind of URL or relative path.
        The destination must be a s3 URL. If this URL end with '/' the source filename was used.

            Args:
                source_uri: The source URI.
                customer_id: The current customer id to inject in each records.
                reset: Remove all the current data before import the grid.
                version: The associated version time.
        """
        if not version:
            version = datetime.now(tz=pytz.UTC)

        parsed_uri = urlparse(self._get_url(), allow_fragments=False)
        parsed_destination, parsed_source = self._update_src_dst(source_uri)

        if parsed_uri.scheme == "s3":
            _update_grid_on_s3(parsed_source,
                               parsed_destination,
                               customer_id=customer_id,
                               compare_grid=True,
                               update_time_series=False,
                               force=reset,
                               merge_ts=False,
                               envs=self._envs
                               )
        else:
            _update_grid_on_file(parsed_source,
                                 parsed_destination,
                                 customer_id=customer_id,
                                 compare_grid=True,
                                 update_time_series=True,
                                 force=reset,
                                 merge_ts=True,
                                 envs=self._envs,
                                 )

    @overrides
    def import_ts(self,
                  source_uri: str,
                  customer_id: str = '',
                  version: Optional[datetime] = None
                  ):
        parsed_destination, parsed_source = self._update_src_dst(source_uri)
        if not customer_id:
            customer_id = self.get_customer_id()
        if parsed_destination.scheme and parsed_destination.scheme in ["s3", "file"]:
            raise ValueError("I can not import the data with a URL that is not on s3")

        if parsed_destination.scheme == "s3":
            _update_grid_on_s3(parsed_source,
                               parsed_destination,
                               customer_id,
                               compare_grid=True,
                               update_time_series=True,
                               force=False,
                               merge_ts=True,
                               envs=self._envs
                               )
        else:
            _update_grid_on_file(parsed_source,
                                 parsed_destination,
                                 customer_id=customer_id,
                                 compare_grid=True,
                                 update_time_series=True,
                                 force=False,
                                 merge_ts=True,
                                 envs=self._envs,
                                 )

    def _update_src_dst(self, source_uri):
        destination_uri = self._get_url()
        parsed_source = urlparse(source_uri)
        parsed_destination = urlparse(destination_uri)
        if not parsed_destination.path:
            destination_uri += "/"
        if destination_uri.endswith('/'):
            destination_uri += Path(parsed_source.path).name
        parsed_destination = urlparse(destination_uri)
        return parsed_destination, parsed_source

    @overrides
    def update_grid(self,
                    diff_grid: Grid,
                    version: Optional[datetime],
                    customer_id: Optional[str],
                    now: Optional[datetime] = None) -> None:
        if not diff_grid:
            return
        s3_client = self._s3()
        # Calculate the updated version of current Grid
        new_grid = self._download_grid(self._get_url(), None) + diff_grid

        parsed_target = urlparse(self._get_url())
        suffix = Path(parsed_target.path).suffix
        use_gzip = False
        if suffix == ".gz":
            use_gzip = True
            suffix = Path(parsed_target.path).suffixes[-2]

        target_data = dump(new_grid, suffix_to_mode(suffix)).encode('UTF8')  # type: ignore
        if use_gzip:
            target_data = gzip.compress(target_data)
        md5_digest = md5(target_data)
        b64_digest = base64.b64encode(md5_digest.digest()).decode("UTF8")
        # WARNING: the local version may not be update.
        # Waiting the next `REFRESH` period
        s3_client.put_object(Body=target_data,  # type: ignore
                             Bucket=parsed_target.hostname,
                             Key=parsed_target.path[1:],
                             ContentMD5=b64_digest
                             )

    @overrides
    def read_grid(self,
                  customer_id: str = '',
                  version: Optional[datetime] = None) -> Grid:
        return self._download_grid(self._get_url(), version)
