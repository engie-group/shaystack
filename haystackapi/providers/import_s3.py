"""
Import haystack file in S3 bucket. Manage the versions of files.
"""
import base64
import gzip
import logging
import os
import sys
import urllib
from hashlib import md5
from io import BytesIO
from multiprocessing.dummy import freeze_support
from multiprocessing.pool import ThreadPool
from pathlib import Path
from threading import Lock
from typing import Tuple
from urllib.parse import ParseResult, urlparse

import boto3
import click
from botocore.exceptions import ClientError

from .haystack_interface import EmptyGrid
from ..dumper import dump
from ..grid import Grid
from ..parser import parse, suffix_to_mode
from ..zincparser import ZincParseException

log = logging.getLogger("import_s3")

VERIFY = True
POOL_SIZE = 20

POOL = None

lock = Lock()


def _download_uri(parsed_uri: ParseResult) -> bytes:
    """ Return decompressed data from url """
    if parsed_uri.scheme == "s3":
        s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("AWS_S3_ENDPOINT", None),
            verify=VERIFY,  # See https://tinyurl.com/y5tap6ys
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
    return data


def _get_hash_of_s3_file(s3_client,
                         parsed):
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
                     mode: str,
                     compress: bool) -> Tuple[bytes, str]:
    """ Merge time series.
        If the destination time series has older values, insert these values at the beginning
        of the current time series.
        It is not to forget values
    """
    assert 'ts' in source_grid.column, "The source grid must have ts,value columns"
    if 'ts' in destination_grid.column:
        # destination_grid = destination_grid.copy()  # FIXME
        # destination_grid[0]['ts'] = destination_grid[0]['ts'] - timedelta(seconds=20)  # FIXME: Bug injecté
        if id(destination_grid) != id(source_grid):
            destination_grid.sort('ts')
            source_grid.sort('ts')
            start_source = source_grid[0]['ts']
            source_grid.extend(filter(lambda row: row['ts'] < start_source, destination_grid))
            source_grid.sort('ts')

    source_data = dump(source_grid, mode).encode('UTF8')
    if compress:
        source_data = gzip.compress(source_data)
    md5_digest = md5(source_data)
    b64_digest = base64.b64encode(md5_digest.digest()).decode("UTF8")
    return source_data, b64_digest


def update_grid_on_s3(parsed_source: ParseResult,
                      parsed_destination: ParseResult,
                      compare_grid: bool,
                      time_series: bool,
                      force: bool,
                      merge_ts: bool,
                      use_thread: bool = True
                      ) -> None:  # pylint: disable=too-many-locals
    log.debug("update %s", (parsed_source.geturl(),))
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("AWS_S3_ENDPOINT", None),
    )
    suffix = Path(parsed_source.path).suffix
    use_gzip = False
    if parsed_source.scheme == 's3' and not compare_grid:
        if time_series:
            source_data = _download_uri(parsed_source)
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
        source_data = _download_uri(parsed_source)
        md5_digest = md5(source_data)
        b64_digest = base64.b64encode(md5_digest.digest()).decode("UTF8")
        source_etag = ''
        source_grid = None
        if not force:
            source_etag = md5_digest.hexdigest()
        if time_series or compare_grid or merge_ts:
            unzipped_source_data = source_data
            if suffix == ".gz":
                use_gzip = True
                unzipped_source_data = gzip.decompress(source_data)
                suffix = Path(parsed_source.path).suffixes[-2]

            try:
                with lock:
                    source_grid = parse(unzipped_source_data.decode("utf-8-sig"),
                                        suffix_to_mode(suffix))
                destination_data = s3_client.get_object(Bucket=parsed_destination.hostname,
                                                        Key=parsed_destination.path[1:],
                                                        IfNoneMatch=source_etag)['Body'].read()
                if parsed_source.path.endswith(".gz"):
                    destination_data = gzip.decompress(destination_data)
                with lock:
                    destination_grid = parse(destination_data.decode("utf-8-sig"),
                                             suffix_to_mode(suffix))

            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchKey':
                    # Target key not found
                    destination_grid = EmptyGrid
                elif ex.response['Error']['Code'] == '304':
                    # Target not modified
                    if source_grid:
                        destination_grid = source_grid
                    else:
                        raise
                else:
                    raise
            except ZincParseException as ex:
                # Ignore. Override target
                log.warning("Zinc parser exception with %s", (parsed_destination.geturl()))
                destination_grid = EmptyGrid

        if force or not compare_grid or (destination_grid - source_grid):
            if not force and merge_ts:  # PPR: if TS, limite the number of AWS versions ?
                source_data, b64_digest = merge_timeseries(source_grid,
                                                           destination_grid,
                                                           suffix_to_mode(suffix), use_gzip)
            s3_client.put_object(Body=source_data,
                                 Bucket=parsed_destination.hostname,
                                 Key=parsed_destination.path[1:],
                                 ContentMD5=b64_digest
                                 )
            log.info("%s updated (put in s3 bucket)", parsed_source.geturl())
        else:
            log.debug("%s not modified (same grid)", parsed_source.geturl())

    # Now, it's time to upload the referenced time-series
    if time_series:
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
                        False,
                        False,
                        force,
                        True))
                else:
                    update_grid_on_s3(
                        urlparse(source_time_serie),
                        urlparse(destination_time_serie),
                        compare_grid=False,
                        time_series=False,
                        force=force,
                        merge_ts=True)
        if requests:
            with ThreadPool(processes=POOL_SIZE) as pool:  # FIXME: pool global ou local ?
                pool.starmap(update_grid_on_s3, requests)


def import_in_s3(source: str,
                 destination: str,
                 compare: bool = False,
                 time_series: bool = True,
                 force: bool = False):
    """
    Import source grid file on destination, only if something was changed.
    The source can use all kind of URL or relative path.
    The destination must be an s3 URL. If this URL end with '/' the source filename was used.
    """
    parsed_source = urlparse(source)
    if destination.endswith('/'):
        destination += Path(parsed_source.path).name
    parsed_destination = urlparse(destination)

    update_grid_on_s3(parsed_source,
                      parsed_destination,
                      compare,
                      time_series,
                      force,
                      merge_ts=False
                      )


def aws_handler(event, context):
    """
    AWS Handler.
    Set the environment variable HAYSTACK_URL and HAYSTACK_DB
    """
    hs_source_url = os.environ.get("HAYSTACK_SOURCE_URL")
    hs_target_url = os.environ.get("HAYSTACK_URL")
    assert hs_source_url, "Set `HAYSTACK_SOURCE_URL`"
    assert hs_target_url, "Set `HAYSTACK_URL`"
    import_in_s3(hs_source_url, hs_target_url)


@click.command(short_help='Import haystack file in database')
@click.argument('source_url',
                metavar='<haystack url>',
                # help='filename or url (may be s3:/...)'
                )
@click.argument('target_url',
                metavar='<s3 target url>',
                # help='s3 url'
                )
@click.option("--compare/--no-compare",
              help='Compare grid before upload datas',
              default=True
              )
@click.option("--time-series/--no-time-series",
              help='Import time-series referenced with hisURI tag',
              default=True
              )
@click.option("--force/--no-force",
              help='Force to upload data without verifications or update',
              default=False
              )
def main(source_url: str, target_url: str, compare: bool, time_series: bool, force: bool) -> int:
    """
    Import haystack file for file or URL, to s3 bucket.
    Only the difference was imported, with a new version of ontology.
    If the destination time series exists, and old values are present, they are recovered
    at the beginning of the grid.
    """
    try:
        import_in_s3(source_url, target_url, compare, time_series, force)
        print(f"{source_url} imported in {target_url}")
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ExpiredToken':
            logging.error("Refresh the token.")
        else:
            raise

    return 0


if __name__ == '__main__':
    freeze_support()
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())  # pylint: disable=no-value-for-parameter
