# -*- coding: utf-8 -*-
# Import data in SQL database
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Import haystack file in SQL database.
"""
import logging
import os
import sys
import traceback
from datetime import datetime
from multiprocessing.dummy import freeze_support
from typing import Optional, cast, List, Dict

import click
import pytz

from .db_haystack_interface import DBHaystackInterface
from .haystack_interface import get_provider
from .url import BOTO3_AVAILABLE

log = logging.getLogger(__name__)


# May be an handler for Lambda
# typing:ignore
def import_in_db(source_uri: str,  # pylint: disable=too-many-arguments
                 destination_uri: str,
                 ts_uri: Optional[str],  # Ignore
                 customer_id: str,  # Ignore
                 import_time_series: bool,
                 reset: bool,
                 version: Optional[datetime],
                 envs: Dict[str, str]  # pylint: disable=protected-access
                 ) -> None:
    """
    Import source URI to database.
    Args:
            source_uri: The source URI.
            destination_uri: The destination URI.
            ts_uri: The time-series database URI
            customer_id: The current customer id to inject in each records.
            import_time_series: True to import the time-series references via `hisURI` tag
            reset: Remove all the current data before import the grid.
            version: The associated version time.
            envs: Environment (like os.environ)
    """
    envs["HAYSTACK_DB"] = destination_uri
    provider_name = "shaystack.providers.db"
    if ts_uri:
        envs["HAYSTACK_TS"] = ts_uri
        provider_name = "shaystack.providers.timestream"

    if not version:
        version = datetime.now(tz=pytz.UTC)
    try:
        with cast(DBHaystackInterface, get_provider(provider_name, envs)) as provider:
            provider.create_db()
            provider.import_data(source_uri,
                                 customer_id,
                                 reset,
                                 version)
            if import_time_series:
                provider.import_ts(source_uri,
                                   customer_id,
                                   version)
    except ModuleNotFoundError as ex:
        # noinspection PyUnresolvedReferences
        log.error("Call `pip install` with the database "
                  "driver - %s", ex.msg)  # pytype: disable=attribute-error


@click.command(short_help='Import haystack file in database')
@click.argument('source_uri',
                metavar='<source uri>',
                )
@click.argument('target_uris',
                metavar='<target uri>',
                nargs=-1
                )
@click.option("--customer",
              help='Data for a dedicated customer',
              )
@click.option("--time-series/--no-time-series",
              help='Import time series',
              default=True
              )
@click.option("--reset",
              help='Clean the database before import',
              is_flag=True)
def main(source_uri: str,
         target_uris: List[str],
         customer: Optional[str],
         reset: bool,
         time_series: bool) -> int:
    """
    Import haystack file for file or URL, to database, to be used with sql provider.
    Only the difference was imported, with a new version of ontology.
    """
    if len(target_uris) > 2:
        click.echo('Use maximum 2 url database url')
        raise click.Abort()
    database_uri = target_uris[0]
    ts_uri = target_uris[1] if len(target_uris) > 1 else None
    if ts_uri and not BOTO3_AVAILABLE:
        print("Use 'pip install boto3' before using AWS features", file=sys.stderr)
        return -1
    if customer is None:
        customer = ''
    try:
        import_in_db(source_uri, database_uri, ts_uri,
                     customer,
                     import_time_series=time_series,
                     reset=reset,
                     version=None,
                     envs=cast(Dict[str, str], os.environ))
        if ts_uri:
            print(f"{source_uri} imported in {database_uri} and {ts_uri}")
        else:
            print(f"{source_uri} imported in {database_uri}")
        return 0
    except Exception as ex:  # pylint: disable=broad-except
        print(f"Impossible to import data ({ex})", file=sys.stderr)
        traceback.print_exc()
        return -1


if __name__ == '__main__':
    freeze_support()
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())  # pylint: disable=no-value-for-parameter
