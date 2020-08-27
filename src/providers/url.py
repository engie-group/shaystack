"""
An Haystack Read-Only API provider to expose an Haystack file via the Haystack API.
The file must be referenced with the environment variable HAYSTACK_URL and may be the form:
- http://.../ontology.json
- http://.../ontology.zinc
- file://.../ontology.zinc
- ftp://.../ontology.json
- s3://.../ontology.zinc (the lambda functions must have the privilege to read this file)
- ...

The time series to manage history must be referenced in entity, with the `hisURI` tag.
This URI may be relative and MUST be in parquet format. The `his_read` implementation,
download the parquet file in memory and convert to the negotiated haystack format.
"""
import logging
import os
import urllib
from array import array
from datetime import datetime, MAXYEAR, timezone, MINYEAR
from functools import lru_cache
from io import BytesIO
from typing import cast, Optional, Union, Tuple
from urllib.parse import urlparse

import boto3
from fastparquet import ParquetFile
from fastparquet.compression import compressions, decompressions
from fastparquet.util import default_open
from overrides import overrides
from pandas import DataFrame
from pandas.io.s3 import s3fs
from snappy import snappy

import hszinc
from hszinc import Grid, Uri, MODE_ZINC, MODE_JSON
from .haystack_interface import HaystackInterface, get_default_about

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
    def about(self) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'about' operation """
        grid = get_default_about()
        grid[0].update({  # pylint: disable=no-member
            "productUri": Uri("http://localhost:80"),  # FIXME indiquer le port et trouver l'URL ?
            "productVersion": None,  # FIXME: set the product version
            "moduleName": "URLProvider",
            "moduleVersion": None  # FIXME: set the module version
        })
        return grid

    @lru_cache(maxsize=LRU_SIZE)
    @overrides
    def read(self, grid_filter: str, limit: Optional[int]) -> Grid:  # pylint: disable=unused-argument
        """ Implement Haystack 'read' """
        grid = Provider._download_grid(self._get_url())
        return grid.filter(grid_filter, limit if limit else 0)

    @overrides
    def his_read(self, entity_id: str,
                 dates_range: Union[Union[datetime, str], Tuple[datetime, datetime]]) -> Grid:
        """ Implement Haystack 'read' """
        log.info("----> Call his_read API")
        grid = Provider._download_grid(self._get_url())

        for row in grid:
            if "id" in row and row["id"] == entity_id:
                # Find entity
                if "hisURI" not in row:
                    raise ValueError(f"hisURI not found in entity {id}")
                his_uri = str(row["hisURI"])
                base = self._get_url()
                parsed_relative = urlparse(str(his_uri), allow_fragments=False)
                if not parsed_relative.scheme:
                    his_uri = base[:base.rfind('/')] + "/" + his_uri

                df = cast(DataFrame, Provider._load_parquet(his_uri))
                history = []
                unit = None
                min_date = datetime(MAXYEAR, 12, 31, tzinfo=timezone.utc)  # FIXME: Manage local or UTC ?
                max_date = datetime(MINYEAR, 1, 1, tzinfo=timezone.utc)

                for i in range(len(df)):
                    start_date = cast(Timestamp, df.loc[i, 'StartDate'].to_pydatetime()).replace(tzinfo=timezone.utc)
                    end_date = cast(Timestamp, df.loc[i, 'EndDate'].to_pydatetime()).replace(tzinfo=timezone.utc)
                    history.append({"ts": end_date,  # TODO: optimize this code
                                    "value": float(df.loc[i, 'Value'])
                                    })
                    # TODO unit = row['Unit']
                    min_date = min(min_date, start_date)
                    max_date = max(max_date, end_date)

                result = Grid(version=grid.version,
                              metadata={"id": entity_id,
                                        "hisStart": min_date,
                                        "hisEnd": max_date,
                                        "unit": unit},
                              columns={"ts": {}, "val": {}})
                result.extend(history)
                return result
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
            s3 = boto3.client('s3')
            stream = BytesIO()
            s3.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream)
            return stream.getvalue()
        else:
            with urllib.request.urlopen(uri) as response:
                return response.read()
        # if (uri.endwith(".gz")): ...  # TODO : a valider

    @staticmethod
    @lru_cache(maxsize=LRU_SIZE)
    def _download_grid(uri: str) -> Grid:
        body = Provider._download_uri(uri).decode("utf-8")
        if body is None:
            raise ValueError("Empty body not supported")
        mode = MODE_JSON if (uri.endswith(".json")) else MODE_ZINC
        log.debug(f"_download_grid({uri})")
        return hszinc.parse(body, mode)[0]

    @staticmethod
    @lru_cache(maxsize=LRU_SIZE)
    def _load_parquet(uri: str) -> array:
        s3 = s3fs.S3FileSystem()

        open_with = s3.open
        if uri.startswith("file://"):
            open_with = default_open
            uri = uri[7:]
        log.debug(f"_load_parquet({uri})")
        pf = ParquetFile(uri, open_with=open_with)
        return pf.to_pandas()
