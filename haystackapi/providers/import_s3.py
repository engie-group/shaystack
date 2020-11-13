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
from urllib.parse import ParseResult, urlparse

import boto3
import click
from botocore.exceptions import ClientError

import hszinc
from haystackapi import EmptyGrid
from hszinc.zincparser import ZincParseException

log = logging.getLogger("import_s3")

VERIFY = True
POOL_SIZE = 20

pool = None

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
            uri = Path.cwd().joinpath(uri).as_uri()  # FIXME
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
        else:
            raise


# FIXME: use multithreading or async
def update_grid_on_s3(parsed_source: ParseResult,
                      parsed_destination: ParseResult,
                      compare_grid: bool,
                      time_series: bool,
                      force: bool,
                      ) -> None:
    log.info("update %s", (parsed_source.geturl(),))  # FIXME
    s3_client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("AWS_S3_ENDPOINT", None),
    )
    suffix = Path(parsed_source.path).suffix
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
        if not force:
            source_etag = md5_digest.hexdigest()
        if time_series or compare_grid:
            unzipped_source_data = source_data
            if suffix == ".gz":
                unzipped_source_data = gzip.decompress(source_data)
                suffix = Path(parsed_source.path).suffixes[-2]

            try:
                with lock:
                    source_grid = hszinc.parse(unzipped_source_data.decode("utf-8-sig"), hszinc.suffix_to_mode(suffix))
                destination_data = s3_client.get_object(Bucket=parsed_destination.hostname,
                                                        Key=parsed_destination.path[1:],
                                                        IfNoneMatch=source_etag)['Body'].read()
                if parsed_source.path.endswith(".gz"):
                    destination_data = gzip.decompress(destination_data)
                with lock:
                    destination_grid = hszinc.parse(destination_data.decode("utf-8-sig"), hszinc.suffix_to_mode(suffix))

            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchKey':
                    # Target key not found
                    destination_grid = EmptyGrid
                elif ex.response['Error']['Code'] == '304':
                    # Target not modified
                    destination_grid = source_grid
                    pass
                else:
                    raise
            except ZincParseException as ex:
                # Ignore. Override target
                log.warning("Zinc parser exception with %s", (parsed_destination.geturl()))
                destination_grid = EmptyGrid

        if force or not compare_grid or len(destination_grid - source_grid):
            s3_client.put_object(Body=source_data,
                                 Bucket=parsed_destination.hostname,
                                 Key=parsed_destination.path[1:],
                                 ContentMD5=b64_digest
                                 )
            log.info("%s updated (put in s3 bucket)", parsed_source.geturl())
        else:
            log.debug("%s not modified (same grid)", parsed_source.geturl())

    # Now, it's time to upload the referenced time-series
    THREAD = True
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
                if THREAD:
                    requests.append((
                        urlparse(source_time_serie),
                        urlparse(destination_time_serie),
                        False,
                        False,
                        force))
                else:
                    update_grid_on_s3(
                        urlparse(source_time_serie),
                        urlparse(destination_time_serie),
                        compare_grid=False,
                        time_series=False,
                        force=force)
        if requests:
            with ThreadPool(processes=POOL_SIZE) as pool:
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
                      )


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
              help='Compare grid before upload datas',
              default=True
              )
@click.option("--force/--no-force",
              help='Force to upload datas',
              default=False
              )
def main(source_url: str, target_url: str, compare: bool, time_series: bool, force: bool) -> int:
    """
    Import haystack file for file or URL, to database, to be used with sql provider.
    Only the difference was imported, with a new version of ontology.
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
    sys.exit(main())
