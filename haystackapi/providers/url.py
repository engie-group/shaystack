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

The time series to manage history must be referenced in entity:
- with inner ontology in tag 'history' or
- with the `hisURI` tag. This URI may be relative and MUST be in parquet format, with UTC date time.
The `his_read` implementation, download the parquet file in memory, update the date/time to point timezone,
or the referenced site timezone and convert to the negotiated haystack format.
"""
import gzip
import logging
import os
import urllib.request
from datetime import datetime, MAXYEAR, MINYEAR
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Optional, Union, Tuple
from urllib.parse import urlparse

import boto3
import pytz
from overrides import overrides

import hszinc
from hszinc import Grid, MODE_ZINC, MODE_JSON, MODE_CSV
from .haystack_interface import HaystackInterface

Timestamp = datetime

log = logging.getLogger("url.Provider")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))

LRU_SIZE = 128


class Provider(HaystackInterface):
    """
    Expose an Haystack file via the Haystactk Rest API.
    """

    def _get_url(self):  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return os.environ.get("HAYSTACK_URL", "")

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

    @lru_cache(maxsize=LRU_SIZE)
    @overrides
    def read(self, grid_filter: str, limit: Optional[int],
             date_version: datetime) -> Grid:  # pylint: disable=unused-argument
        """ Implement Haystack 'read' """
        log.debug(f"----> Call read(grid_filter:'{grid_filter}', limit:{limit})")
        grid = Provider._download_grid(self._get_url())
        result = grid.filter(grid_filter, limit if limit else 0)
        return result

    @overrides
    def his_read(self, entity_id: str,
                 dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]]) -> Grid:
        """ Implement Haystack 'hisRead' """
        log.debug(f"----> Call his_read(id:{entity_id}, range:{dates_range}")

        grid = Provider._download_grid(self._get_url())
        if str(entity_id) in grid:  # FIXME: utiliser des ref pour les id d'indaxtion
            entity = grid[entity_id]
            # Different solution to retrieve the history value
            # 1. use a file in the dir(HAYSTACK_URL)+entity['hisURI']
            if "hisURI" in entity:
                his_uri = str(entity["hisURI"])
                base = self._get_url()
                parsed_relative = urlparse(his_uri, allow_fragments=False)
                if not parsed_relative.scheme:
                    his_uri = base[:base.rfind('/')] + "/" + his_uri

                history = Provider._download_grid(his_uri)

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

    @staticmethod
    def _download_uri(uri: str) -> bytes:
        """ Download Haystack from URI.
        The uri must be a classic url (file://, http:// ...)
        or a s3 urn (s3://).
        The suffix describe the file format.
        """
        assert uri
        log.info(f"_download_uri('{uri}')")
        parsed_uri = urlparse(uri, allow_fragments=False)
        if parsed_uri.scheme == "s3":
            # AWS_S3_ENDPOINT may be http://localhost:9000 to use minio (make start-minio)
            s3 = boto3.client('s3', endpoint_url=os.environ.get('AWS_S3_ENDPOINT', None))
            obj_versions = s3.list_object_versions(Bucket=parsed_uri.netloc,Prefix=parsed_uri.path[1:])['Versions']
            stream = BytesIO()
            s3.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream,
                                ExtraArgs={'VersionId': obj_versions[0]['VersionId']})
            data = stream.getvalue()
        else:
            # Manage default cwd
            if not parsed_uri.scheme:
                uri = Path(__file__).parent.parent.joinpath(uri).as_uri()
            with urllib.request.urlopen(uri) as response:
                data = response.read()
        if uri.endswith(".gz"):
            log.debug("Je dezip")
            return gzip.decompress(data)
        else:
            return data

    @staticmethod
    @lru_cache(maxsize=LRU_SIZE)
    def _download_grid(uri: str) -> Grid:
        log.debug(f"_download_grid({uri})")
        body = Provider._download_uri(uri).decode("utf-8")
        if body is None:
            raise ValueError("Empty body not supported")
        if uri.endswith(".gz"):
            uri = uri[:-3]
        if uri.endswith(".json"):
            mode = MODE_JSON
        elif uri.endswith(".zinc"):
            mode = MODE_ZINC
        elif uri.endswith(".csv"):
            mode = MODE_CSV
        else:
            raise ValueError("The file extension must be .(json|zinc|csv)[.gz]")
        return hszinc.parse(body, mode)
