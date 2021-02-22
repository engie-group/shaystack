import cmd
import datetime
import logging
import os
import sys
import traceback
from typing import cast
from urllib.parse import urlparse

import pytz

from shaystack.providers import get_provider
from shaystack.providers.db_postgres import _sql_filter as pg_sql_filter
from shaystack.providers.db_sqlite import _sql_filter as sqlite_sql_filter
from shaystack.providers.sql import Provider as SQLProvider

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def main():
    """Loop to test the postgres generation with REPL"""
    if "HAYSTACK_DB" not in os.environ:
        os.environ["HAYSTACK_DB"] = "sqlite3:///:memory:"
    provider = get_provider("shaystack.providers.sql")
    conn = cast(SQLProvider, provider).get_connect()
    scheme = urlparse(os.environ["HAYSTACK_DB"]).scheme

    class TstRequest(cmd.Cmd):
        def __init__(self, conn):
            super().__init__()
            self.conn = conn

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

        def do_bye(self, arg: str) -> bool:  # pylint: disable=unused-argument,no-self-use
            return True

    TstRequest(conn).cmdloop()
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())
