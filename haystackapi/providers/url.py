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

If the AWS bucket use the versionning, the correct version are return, to correspond to the version of the file
at the `version_date`.

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
from typing import Optional, Union, Tuple
from urllib.parse import urlparse, ParseResultBytes

import boto3
import pytz
from botocore.client import BaseClient
from overrides import overrides

import hszinc
from hszinc import Grid, suffix_to_mode, Ref
from .haystack_interface import HaystackInterface

Timestamp = datetime

log = logging.getLogger("url.Provider")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))

LRU_SIZE, PERIODIC_REFRESH = 16, 15


class Provider(HaystackInterface):
    """
    Expose an Haystack file via the Haystactk Rest API.
    """

    def __init__(self):
        self._s3_client = None
        self._lock = Lock()
        self._versions = {}  # Dict of OrderedDict with versions
        self._lru = []
        self._timer = None

    @overrides
    def about(self, home: str) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = super().about(home)
        grid[0].update({  # pylint: disable=no-member
            "productVersion": "1.0",
            "moduleName": "URLProvider",
            "moduleVersion": "1.0"
        })
        return grid

    @overrides
    def read(self, limit: int, entity_ids: Optional[Grid] = None, grid_filter: Optional[str] = None,
             date_version: Optional[datetime] = None) -> Grid:  # pylint: disable=unused-argument
        """ Implement Haystack 'read' """
        log.debug(
            f"----> Call read(limit:{limit}, ids:{entity_ids} grid_filter:'{grid_filter}' date_version={date_version})")
        grid = self._download_grid(self._get_url(), date_version)
        if entity_ids:
            result = Grid(grid.version, metadata=grid.metadata, columns=grid.column)
            for ref in entity_ids:
                result.append(grid[ref])
        else:
            result = grid.filter(grid_filter, limit if limit else 0)
        return result

    @overrides
    def his_read(self, entity_id: Ref,
                 dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]],
                 date_version: Optional[datetime]) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(f"----> Call his_read(id={entity_id}, range={dates_range}, date_version={date_version})")

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
                    his_uri = base[:base.rfind('/')] + "/" + his_uri

                history = self._download_grid(his_uri, date_version)

                min_date = datetime(MAXYEAR, 1, 3, tzinfo=pytz.utc)
                max_date = datetime(MINYEAR, 12, 31, tzinfo=pytz.utc)

                for r in history:
                    min_date = min(min_date, r['date'])
                    max_date = max(max_date, r['date'])

                grid.metadata = {'id': entity_id,
                                 'hisStart': min_date,
                                 'hisEnd': max_date,
                                 }
                return history
            # 2. use the inner time series in tag 'history' with the type 'Grid'
            elif 'history' in entity:
                return entity['history']
            else:
                ValueError(f"{entity_id} has not history")
        else:
            raise ValueError(f"id '{entity_id}' not found")

    def cancel(self):
        if self._timer:
            self._timer.cancel()

    def _get_url(self):  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return os.environ.get("HAYSTACK_URL", "")

    def _s3(self) -> BaseClient:
        # AWS_S3_ENDPOINT may be http://localhost:9000 to use minio (make start-minio)
        if not self._s3_client:  # Lazy init
            self._s3_client = boto3.client('s3',
                                           endpoint_url=os.environ.get('AWS_S3_ENDPOINT', None),
                                           verify=False  # See https://tinyurl.com/y5tap6ys
                                           )
        return self._s3_client

    def _download_uri(self, parsed_uri: ParseResultBytes, date_ask: datetime) -> bytes:
        """ Download Haystack from URI.
        The uri must be a classic url (file://, http:// ...)
        or a s3 urn (s3://).
        The suffix describe the file format.
        """
        assert parsed_uri
        log.info(f"_download_uri('{parsed_uri.geturl()}')")
        if parsed_uri.scheme == "s3":
            s3 = self._s3()
            extra_args = None
            if date_ask:
                obj_versions = self._versions[parsed_uri.geturl()]
                for date_version, (version_id, _) in obj_versions.items():
                    if date_version <= date_ask:
                        extra_args = {"VersionId": version_id}
                        break
                if not version_id:  # At this date, this file was not exist
                    raise KeyError(parsed_uri.path[1:])

            stream = BytesIO()
            log.debug(f"bucket={parsed_uri.netloc} path={parsed_uri.path[1:]} extra={extra_args}")
            s3.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream,
                                ExtraArgs=extra_args)
            data = stream.getvalue()
        else:
            # Manage default cwd
            if not parsed_uri.scheme:
                uri = Path.cwd().joinpath(parsed_uri.geturl()).as_uri()
            with urllib.request.urlopen(uri) as response:
                data = response.read()
        if parsed_uri.path.endswith(".gz"):
            return gzip.decompress(data)
        else:
            return data

    def _periodic_refresh_versions(self, parsed_uri: ParseResultBytes):
        """ Refresh list of versions """
        # Refresh at a rounded period, then all cloud instances refresh data at the same time.
        if parsed_uri.scheme == "s3":
            s3 = self._s3()
            obj_versions = [(v['LastModified'], v['VersionId']) for v in
                            s3.list_object_versions(Bucket=parsed_uri.netloc, Prefix=parsed_uri.path[1:])['Versions']]
            self._lock.acquire()
            url_version = self._versions.get(parsed_uri.geturl(), OrderedDict())
            for date_version, version_id in obj_versions:
                if date_version not in url_version:
                    url_version[date_version] = (version_id, None)  # Add a slot
            self._versions[parsed_uri.geturl()] = url_version
            self._lock.release()
        else:
            self._versions[datetime.min] = ("", None)
        if PERIODIC_REFRESH:
            now = datetime.utcnow()
            to = now.replace(minute=0, second=0) + timedelta(
                minutes=(now.minute + PERIODIC_REFRESH) // PERIODIC_REFRESH * PERIODIC_REFRESH)
            assert to > now
            partial_refresh = functools.partial(self._periodic_refresh_versions, self, parsed_uri)
            self._timer = threading.Timer((to - now).seconds, partial_refresh)
            self._timer.start()

    def _refresh_versions(self, parsed_uri: ParseResultBytes):
        if not PERIODIC_REFRESH or parsed_uri.geturl() not in self._versions:
            self._periodic_refresh_versions(parsed_uri)

    def _download_grid(self, uri: str, date_version: Optional[datetime]) -> Grid:
        parsed_uri = urlparse(uri, allow_fragments=False)
        self._refresh_versions(parsed_uri)
        for version, (version_id, grid) in self._versions[uri].items():
            if not date_version or version <= date_version:
                if not grid:
                    log.debug(f"_download_grid({parsed_uri.geturl()},{date_version})")
                    body = self._download_uri(parsed_uri, date_version).decode("utf-8")
                    if body is None:
                        raise ValueError("Empty body not supported")
                    if uri.endswith(".gz"):
                        uri = uri[:-3]

                    mode = suffix_to_mode(os.path.splitext(uri)[1])
                    if not mode:
                        raise ValueError("The file extension must be .(json|zinc|csv)[.gz]")
                    grid = hszinc.parse(body, mode)
                self._lock.acquire()
                self._versions[version] = grid
                if version in self._lru:
                    self._lru.remove(version)
                self._lru.append(version)
                # Purge LRU
                if len(self._lru) > LRU_SIZE:
                    split = len(self._lru) - LRU_SIZE
                    for version in self._lru[0:split]:
                        self._versions[version] = None
                    self._lru = self._lru[split:]
                self._lock.release()
                return grid
        raise ValueError("Empty body not supported")
