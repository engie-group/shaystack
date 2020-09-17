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

The time series to manage history must be referenced in entity, with the `hisURI` tag.
This URI may be relative and MUST be in parquet format. The `his_read` implementation,
download the parquet file in memory and convert to the negotiated haystack format.
"""
import gzip
import logging
import os
import urllib.request
from array import array
from datetime import datetime, MAXYEAR, timezone, MINYEAR
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import cast, Optional, Union, Tuple
from urllib.parse import urlparse

import boto3
from fastparquet import ParquetFile
from fastparquet.compression import compressions, decompressions
from fastparquet.util import default_open
from overrides import overrides
from pandas import DataFrame
# from pandas.io.s3 import s3fs
from s3fs import S3FileSystem
from snappy import snappy

import hszinc
from hszinc import Grid, MODE_ZINC, MODE_JSON, MODE_CSV
from .haystack_interface import HaystackInterface

Timestamp = datetime

log = logging.getLogger("url.Provider")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))

LRU_SIZE = 32


# -- Initialize fastparquet
def snappy_decompress(data, uncompressed_size):  # pylint: disable=unused-argument
    """ decompress snappy data """
    return snappy.decompress(data)


compressions['SNAPPY'] = snappy.compress
decompressions['SNAPPY'] = snappy_decompress


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
    def read(self, grid_filter: str, limit: Optional[int], date_version: datetime) -> Grid:  # pylint: disable=unused-argument
        """ Implement Haystack 'read' """
        log.info(f"----> Call read(grid_filter:'{grid_filter}', limit:{limit})")
        grid = Provider._download_grid(self._get_url())
        result = grid.filter(grid_filter, limit if limit else 0)
        return result

    @overrides
    def his_read(self, entity_id: str,
                 dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]]) -> Grid:
        """ Implement Haystack 'read' """
        log.info(f"----> Call his_read(id:{entity_id}, range:{dates_range}")
        grid = Provider._download_grid(self._get_url())
        if entity_id in grid:
            entity = grid[entity_id]

            # Differents solution to retreive the history value
            # 1. use a parquet file in the dir(HAYSTACK_URL)+entity['hisURI']
            # 2. use history tag with a type Grid
            if "hisURI" in entity:
                log.debug("J'ai bien hisURL")
                his_uri = str(entity["hisURI"])
                base = self._get_url()
                parsed_relative = urlparse(str(his_uri), allow_fragments=False)
                if not parsed_relative.scheme:
                    his_uri = base[:base.rfind('/')] + "/" + his_uri

                log.debug(f"hisURL complet est {his_uri}")

                df = cast(DataFrame, Provider._load_parquet(his_uri))

                history = Grid(columns=['ts', 'val'])
                unit = None
                min_date = datetime(MAXYEAR, 12, 31, tzinfo=timezone.utc)  # FIXME: Manage local or UTC ?
                max_date = datetime(MINYEAR, 1, 1, tzinfo=timezone.utc)

                for i in range(len(df)):
                    start_date = cast(Timestamp, df.loc[i, 'StartDate'].to_pydatetime()).replace(tzinfo=timezone.utc)
                    end_date = cast(Timestamp, df.loc[i, 'EndDate'].to_pydatetime()).replace(tzinfo=timezone.utc)
                    history.append({"ts": end_date,
                                    "val": float(df.loc[i, 'Value'])
                                    })
                    # TODO unit = row['Unit']
                    min_date = min(min_date, start_date)
                    max_date = max(max_date, end_date)

                grid.metadata = {'id': '@' + entity_id,
                                 'hisStart': min_date,
                                 'hisEnd': max_date,
                                 }
                return history
            elif 'history' in entity:
                return entity['history']
        raise ValueError(f"id {entity_id} not found")

    @staticmethod
    def _download_uri(uri: str) -> bytes:
        """ Download Haystack from URI.
        The uri must be a classic url (file://, http:// ...)
        or a s3 urn (s3://).
        The suffix describe the file format.
        """
        assert uri
        parsed_uri = urlparse(uri, allow_fragments=False)
        if parsed_uri.scheme == "s3":
            # TODO: manage version
            if False:
                # https://docs.min.io/docs/how-to-use-aws-sdk-for-python-with-minio-server.html
                bucket_name = 'haystackapi'

                s3 = boto3.resource('s3')
                versioning = s3.BucketVersioning(bucket_name)
                # check status
                log.debug(versioning.status)
                # enable versioning
                versioning.enable()

                # Retreive object
                # See https://avilpage.com/2019/07/aws-s3-bucket-objects-versions.html
                # https://docs.min.io/docs/how-to-use-aws-sdk-for-python-with-minio-server.html
                s3 = boto3.resource('s3',
                                    endpoint_url='http://localhost:9000',
                                    aws_access_key_id='YOUR-ACCESSKEYID',
                                    aws_secret_access_key='YOUR-SECRETACCESSKEY',
                                    config=Config(signature_version='s3v4'),
                                    region_name='us-east-1')
                versions = s3.list_object_versions(Bucket=bucket_name)
                for version in versions:
                    version_id = versions['Versions'][0]['VersionId']
                    file_key = versions['Versions'][0]['Key']

                    response = s3.get_object(
                        Bucket=bucket_name,
                        Key=file_key,
                        VersionId=version_id,
                    )
                    data = response['Body'].read()
                    print(data)
            # AWS_S3_ENDPOINT may be http://localhost:9000 to use minio (make start-minio)
            s3 = boto3.client('s3', endpoint_url=os.environ.get('AWS_S3_ENDPOINT', None))
            stream = BytesIO()
            s3.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream)
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

    @staticmethod
    @lru_cache(maxsize=LRU_SIZE)
    def _load_parquet(uri: str) -> array:
        s3 = S3FileSystem()

        open_with = s3.open
        if uri.startswith("file://"):
            open_with = default_open
            uri = uri[7:]
        log.debug(f"_load_parquet({uri})")
        pf = ParquetFile(uri, open_with=open_with)
        return pf.to_pandas()
