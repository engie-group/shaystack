import gzip
import logging
import os
import sys
import urllib
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, cast
from urllib.parse import urlparse, ParseResult

import click
from haystackapi.providers import sql

import hszinc
from app.graphql_model import BOTO3_AVAILABLE
from .haystack_interface import get_provider

log = logging.getLogger(__name__)

if BOTO3_AVAILABLE:
    import boto3


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


def _read_grid(uri):
    parsed_uri = urlparse(uri, allow_fragments=False)

    data = _download_uri(parsed_uri)
    suffix = Path(parsed_uri.path).suffix
    if suffix == ".gz":
        suffix = Path(parsed_uri.path).suffixes[-2]

    input_mode = hszinc.suffix_to_mode(suffix)
    grid = hszinc.parse(data.decode("utf-8-sig"), input_mode)
    return grid


# May be an handler for Lambda
# TODO: imported les TS
def import_in_db(source: str,
                 destination: str,
                 customer_id: str = '',
                 reset: bool = False,
                 version: Optional[datetime] = None):
    os.environ["HAYSTACK_DB"] = destination
    with get_provider("haystackapi.providers.sql") as provider:
        provider = cast(sql.Provider, provider)
        if reset:
            provider.purge_db()
        original_grid = provider.export_grid_from_db(customer_id, version)
        target_grid = _read_grid(source)
        provider.import_diff_grid_in_db(target_grid - original_grid, customer_id, version)


def aws_handler(event, context):
    """
    AWS Handler.
    Set the environment variable HAYSTACK_URL and HAYSTACK_DB
    """
    hs_url = os.environ.get("HAYSTACK_URL")
    db = os.environ.get("HAYSTACK_DB")
    customer = event.get("CUSTOMER")
    assert hs_url, "Set `HAYSTACK_URL`"
    assert db, "Set `HAYSTACK_DB`"
    import_in_db(hs_url, db, customer)


@click.command(short_help='Import haystack file in database')
@click.argument('haystack_url',
                metavar='<haystack file url>',
                # help='filename or url (may be s3:/...)'
                )
@click.argument('database_url',
                metavar='<db url>',
                # help='url to describe db connection'
                )
@click.option("--customer",
              help='Data for a dedicated customer',
              )
@click.option("--clean",
              help='Clean the database before import the first version',
              is_flag=True)
@click.option("--time-series/--no-time-series",
              help='Compare grid before upload datas',
              default=True
              )
def main(haystack_url: str, database_url: str, customer: Optional[str], clean: bool, time_series: bool) -> int:
    """
    Import haystack file for file or URL, to database, to be used with sql provider.
    Only the difference was imported, with a new version of ontology.
    """
    if customer is None:
        customer = ''
    if clean is None:
        clean = False
    import_in_db(haystack_url, database_url, customer, clean)
    print(f"{haystack_url} imported in {database_url}")
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())
