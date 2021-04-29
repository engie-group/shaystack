# -*- coding: utf-8 -*-
# User interface to print the translation between filter syntax to others syntaxes.
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
User interface to print the translation between filter syntax to others syntaxes.
"""
import cmd
import datetime
import logging
import os
import pprint
import sys
import traceback
from typing import cast, Dict
from urllib.parse import urlparse

import pytz

from shaystack.grid_filter import _filter_to_python
from shaystack.providers import get_provider
from shaystack.providers.db_mongo import _mongo_filter
from shaystack.providers.db_mysql import _sql_filter as mysql_sql_filter
from shaystack.providers.db_postgres import _sql_filter as pg_sql_filter
from shaystack.providers.db_sqlite import _sql_filter as sqlite_sql_filter
from shaystack.providers.sql import Provider as SQLProvider

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def main():
    """Loop to test the postgres generation with REPL"""
    envs = cast(Dict[str, str], os.environ)
    if "HAYSTACK_DB" not in envs:
        envs["HAYSTACK_DB"] = "sqlite3+sqlite3:///:memory:"
    if "HAYSTACK_PROVIDER" not in envs:
        envs["HAYSTACK_PROVIDER"] = "shaystack.providers.db"
    provider = get_provider(envs["HAYSTACK_PROVIDER"], envs)
    scheme = urlparse(envs["HAYSTACK_DB"]).scheme

    # noinspection PyMethodMayBeStatic
    class HaystackRequest(cmd.Cmd):
        """ Haystack REPL interface """
        __slots__ = ("provider",)

        # noinspection PyShadowingNames
        def __init__(self, provider):
            super().__init__()
            self.provider = provider

        def do_python(self, arg: str) -> None:  # pylint: disable=no-self-use
            # noinspection PyBroadException
            try:
                _, python_code = _filter_to_python(arg)
                print(python_code)
                print()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

        def do_pg(self, arg: str) -> None:
            # noinspection PyBroadException
            try:
                sql_request = pg_sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                print(sql_request)
                print()
                if scheme.startswith("postgres") and isinstance(self.provider, SQLProvider):
                    cursor = self.provider.get_connect().cursor()
                    cursor.execute(sql_request)
                    cursor.close()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

        def do_mysql(self, arg: str) -> None:
            # noinspection PyBroadException
            try:
                sql_request = mysql_sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                print(sql_request)
                print()
                if scheme.startswith("mysql") and isinstance(self.provider, SQLProvider):
                    cursor = self.provider.get_connect().cursor()
                    cursor.execute(sql_request)
                    cursor.close()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

        def do_sqlite(self, arg: str) -> None:
            # noinspection PyBroadException
            try:
                sql_request = sqlite_sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                print(sql_request)
                print()
                if scheme.startswith("sqlite") and isinstance(self.provider, SQLProvider):
                    cursor = self.provider.get_connect().cursor()
                    cursor.execute(sql_request)
                    cursor.close()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

        def do_mongo(self, arg: str) -> None:  # pylint: disable=no-self-use
            # noinspection PyBroadException
            try:
                mongo_request = _mongo_filter(arg, FAKE_NOW, 1, "customer")
                pprint.PrettyPrinter(indent=4).pprint(mongo_request)
                print()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

        def do_bye(self, _: str) -> bool:  # pylint: disable=unused-argument,no-self-use
            return True

    try:
        HaystackRequest(provider).cmdloop()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())
