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
from typing import cast
from urllib.parse import urlparse

import pytz

from shaystack.grid_filter import _filter_to_python
from shaystack.providers import get_provider
from shaystack.providers.db_mongo import _mongo_filter
from shaystack.providers.db_postgres import _sql_filter as pg_sql_filter
from shaystack.providers.db_sqlite import _sql_filter as sqlite_sql_filter
from shaystack.providers.sql import Provider as SQLProvider

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)

def main():
    """Loop to test the postgres generation with REPL"""
    envs = os.environ
    if "HAYSTACK_DB" not in envs:
        envs["HAYSTACK_DB"] = "sqlite3:///:memory:"
    provider = get_provider("shaystack.providers.sql", envs)
    conn = cast(SQLProvider, provider).get_connect()
    scheme = urlparse(envs["HAYSTACK_DB"]).scheme

    class HaystackRequest(cmd.Cmd):
        """ Haystack REPL interface """

        def __init__(self, conn):
            super().__init__()
            self.conn = conn

        def do_python(self, arg: str) -> None:  # pylint: disable=no-self-use
            try:
                _, python_code = _filter_to_python(arg)
                print(python_code)
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()

        def do_pg(self, arg: str) -> None:
            try:
                sql_request = pg_sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                print(sql_request)
                if scheme.startswith("postgres"):
                    cursor = self.conn.cursor()
                    cursor.execute(sql_request)
                    cursor.close()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()
            finally:
                conn.rollback()

        def do_sqlite(self, arg: str) -> None:
            try:
                sql_request = sqlite_sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                print(sql_request)
                if scheme.startswith("sqlite"):
                    cursor = self.conn.cursor()
                    cursor.execute(sql_request)
                    cursor.close()
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()
            finally:
                conn.rollback()

        def do_mongo(self, arg: str) -> None:  # pylint: disable=no-self-use
            try:
                mongo_request = _mongo_filter(arg, FAKE_NOW, 1, "customer")
                pprint.PrettyPrinter(indent=4).pprint(mongo_request)
            except Exception:  # pylint: disable=broad-except
                traceback.print_exc()
            finally:
                conn.rollback()

        def do_bye(self, _: str) -> bool:  # pylint: disable=unused-argument,no-self-use
            return True

    HaystackRequest(conn).cmdloop()
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())
