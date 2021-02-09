# -*- coding: utf-8 -*-
# Import data in SQL database
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Import haystack file in SQL database.
"""
import gzip
import logging
import os
import sys
import urllib
from datetime import datetime
from io import BytesIO
from os.path import dirname
from pathlib import Path
from typing import Optional, cast, List
from urllib.parse import urlparse, ParseResult

import click
import pytz

from . import sql
from .haystack_interface import get_provider
from .. import suffix_to_mode, parse, Grid

BOTO3_AVAILABLE = False
try:
    # Check the presence of boto3
    import boto3  # pylint: disable=unused-import

    BOTO3_AVAILABLE = True
except ImportError:
    pass

log = logging.getLogger(__name__)


def _download_uri(parsed_uri: ParseResult) -> bytes:
    """ Return decompressed data from url """
    if parsed_uri.scheme == "s3":
        assert BOTO3_AVAILABLE, "Use 'pip install boto3'"
        s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("AWS_S3_ENDPOINT", None),
            verify=False,  # See https://tinyurl.com/y5tap6ys
        )

        stream = BytesIO()
        s3_client.download_fileobj(parsed_uri.netloc, parsed_uri.path[1:], stream)
        data = stream.getvalue()
    else:
        # Manage default cwd
        uri = parsed_uri.geturl()
        if not parsed_uri.scheme:
            uri = Path.cwd().joinpath(uri).as_uri()
        with urllib.request.urlopen(uri) as response:
            data = response.read()
    if parsed_uri.path.endswith(".gz"):
        return gzip.decompress(data)
    return data


def _read_grid(uri: str) -> Grid:
    """
    Read a grid from uri.
    Args:
        uri: The URI to reference the datas.

    Returns:
        The grid.
    """
    parsed_uri = urlparse(uri, allow_fragments=False)

    data = _download_uri(parsed_uri)
    suffix = Path(parsed_uri.path).suffix
    if suffix == ".gz":
        suffix = Path(parsed_uri.path).suffixes[-2]

    input_mode = suffix_to_mode(suffix)
    grid = parse(data.decode("utf-8-sig"), input_mode)
    return grid


# May be an handler for Lambda
def import_in_db(source: str,
                 database_url: str,
                 ts_url: Optional[str],
                 customer_id: str = '',
                 time_series: bool = True,
                 reset: bool = False,
                 version: Optional[datetime] = None) -> None:
    """
    Import source URI to database.
    Args:
        source: The source URI.
        database_url: The database URI.
        ts_url: The time-series database URI
        customer_id: The current customer id to inject in each records.
        time_series: True to import the time-series references via `hisURI` tag
        reset: Remove all the current data before import the grid.
        version: The associated version time.
    """
    os.environ["HAYSTACK_DB"] = database_url
    provider_name = "haystackapi.providers.sql"
    if ts_url:
        os.environ["HAYSTACK_TS"] = ts_url
        provider_name = "haystackapi.providers.sql_ts"

    if not version:
        version = datetime.now(tz=pytz.UTC)
    try:
        with get_provider(provider_name) as provider:
            provider = cast(sql.Provider, provider)
            if reset:
                provider.purge_db()
            provider.create_db()
            original_grid = provider.read_grid_from_db(customer_id, version)
            target_grid = _read_grid(source)
            provider.update_grid_in_db(target_grid - original_grid, version, customer_id)
            log.debug("%s imported", source)

            if time_series:
                dir_name = dirname(source)
                for row in target_grid:
                    if "hisURI" in row:
                        assert "id" in row, "TS must have an id"
                        uri = dir_name + '/' + row['hisURI']
                        ts_grid = _read_grid(uri)
                        provider.import_ts_in_db(ts_grid, row["id"], customer_id)
                        log.debug("%s imported", uri)
    except ModuleNotFoundError as ex:
        log.error("Call `pip install` with the database driver - %s", ex.msg)  # type: ignore[attribute-error]


def aws_handler(event, context):
    """
    AWS Lambda Handler.
    Set the environment variable HAYSTACK_URL and HAYSTACK_DB
    """
    hs_url = os.environ.get("HAYSTACK_URL")
    database_url = os.environ.get("HAYSTACK_DB")
    database_ts = os.environ.get("HAYSTACK_TS")
    customer = event.get("CUSTOMER")
    assert hs_url, "Set `HAYSTACK_URL`"
    assert database_url, "Set `HAYSTACK_DB`"
    import_in_db(hs_url, database_url, database_ts, customer)


@click.command(short_help='Import haystack file in database')
@click.argument('haystack_url',
                metavar='<haystack file url>',
                # help='filename or url (may be s3:/...)'
                )
@click.argument('database_urls',
                metavar='<db url>',
                # help='url to describe db connection'
                nargs=-1
                )
@click.option("--customer",
              help='Data for a dedicated customer',
              )
@click.option("--time-series/--no-time-series",
              help='Compare grid before upload datas',
              default=True
              )
@click.option("--clean",
              help='Clean the database before import the first version',
              is_flag=True)
def main(haystack_url: str,
         database_urls: List[str],
         customer: Optional[str],
         clean: bool,
         time_series: bool) -> int:
    """
    Import haystack file for file or URL, to database, to be used with sql provider.
    Only the difference was imported, with a new version of ontology.
    """
    if len(database_urls) > 2:
        click.echo('Use maximum 2 url database url')
        raise click.Abort()
    database_url = database_urls[0]
    ts_url = database_urls[1] if len(database_urls) > 1 else None
    if ts_url and not BOTO3_AVAILABLE:
        print("Use 'pip install boto3' before using AWS features", file=sys.stderr)
        return -1
    if customer is None:
        customer = ''
    if clean is None:
        clean = False
    try:
        import_in_db(haystack_url, database_url, ts_url, customer, time_series, clean)
        if ts_url:
            print(f"{haystack_url} imported in {database_url} and {ts_url}")
        else:
            print(f"{haystack_url} imported in {database_url}")
        return 0
    except Exception as ex:  # pylint: disable=broad-except
        print(f"Impossible to import data ({ex})", file=sys.stderr)
        return -1


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())  # pylint: disable=no-value-for-parameter
