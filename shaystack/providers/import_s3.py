# -*- coding: utf-8 -*-
# Import data in S3 bucket
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Import haystack file in S3 bucket. Manage the versions of files.
"""
import logging
import os
import sys
from datetime import datetime
from multiprocessing.dummy import freeze_support
from typing import Optional, Dict, Union, cast

import click
import pytz

from shaystack.providers import get_provider
from shaystack.providers.haystack_interface import DBHaystackInterface

log = logging.getLogger("import_s3")

BOTO3_AVAILABLE = False
try:
    # Check the presence of boto3
    import boto3  # pylint: disable=unused-import
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    print("Use 'pip install boto3' before using AWS features", file=sys.stderr)
    sys.exit(-1)


def import_in_s3(source_uri: str,  # pylint: disable=too-many-arguments
                 destination_uri: str,
                 ts_uri: Optional[str],  # Ignore
                 customer_id: str,  # Ignore
                 import_time_series: bool,
                 reset: bool,
                 version: Optional[datetime],  # FIXE: update date of s3 file ?
                 envs: Union[Dict[str, str], os._Environ]  # pylint: disable=protected-access
                 ) -> None:
    """
    Import source grid file on destination, only if something was changed.
    The source can use all kind of URL or relative path.
    The destination must be a s3 URL. If this URL end with '/' the source filename was used.

        Args:
            source_uri: The source URI.
            destination_uri: The destination URI.
            ts_uri: The time-series database URI
            customer_id: The current customer id to inject in each records.
            import_time_series: True to import the time-series references via `hisURI` tag
            reset: Remove all the current data before import the grid.
            compare: Compare current version and new version to update the delta
            version: The associated version time.
    """
    envs["HAYSTACK_DB"] = destination_uri
    provider_name = "shaystack.providers.url"
    if ts_uri:
        envs["HAYSTACK_TS"] = ts_uri
        provider_name = "shaystack.providers.db_timestream"

    if not version:
        version = datetime.now(tz=pytz.UTC)
    try:
        with cast(DBHaystackInterface, get_provider(provider_name, envs)) as provider:
            provider.import_data(source_uri,
                                 customer_id,
                                 reset,
                                 version)
            if import_time_series:
                provider.import_ts(source_uri,
                                   customer_id,
                                   version)
    except ModuleNotFoundError as ex:
        log.error("Call `pip install` with the database driver - %s", ex.msg)  # type: ignore[attribute-error]


def aws_handler(event, context):
    """
    AWS Lambda Handler.
    Set the environment variable HAYSTACK_SOURCE_URL and HAYSTACK_DB
    """
    envs = os.environ
    hs_source_url = envs.get("HAYSTACK_SOURCE_DB")
    hs_target_url = envs.get("HAYSTACK_DB")
    assert hs_source_url, "Set `HAYSTACK_SOURCE_DB`"
    assert hs_target_url, "Set `HAYSTACK_DB`"
    import_in_s3(hs_source_url, hs_target_url,
                 ts_uri=None,
                 customer_id='',
                 import_time_series=True,
                 reset=False,
                 version=None,
                 envs=envs)


@click.command(short_help='Import haystack file in database')
@click.argument('source_uri',
                metavar='<haystack url>',
                # help='filename or url (may be s3:/...)'
                )
@click.argument('target_uri',
                metavar='<target uri>',
                # help='s3 url'
                )
@click.option("--customer",
              help='Data for a dedicated customer',
              )
@click.option("--time-series/--no-time-series",
              help='Import time-series referenced with hisURI tag',
              default=True
              )
@click.option("--reset",
              help='Force to upload data without verifications or update',
              is_flag=True
              )
def main(source_uri: str,
         target_uri: str,
         customer: Optional[str],
         time_series: bool,
         reset: bool) -> int:
    """
    Import haystack file for file or URL, to s3 bucket.
    Only the difference was imported, with a new version of ontology.
    If the destination time series exists, and old values are present, they are recovered
    at the beginning of the grid.
    """
    try:
        import_in_s3(source_uri,
                     target_uri,
                     ts_uri=None,
                     customer_id=customer,
                     import_time_series=time_series,
                     reset=reset,
                     version=None,
                     envs=os.environ)
        print(f"{source_uri} imported in {target_uri}")
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
