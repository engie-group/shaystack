import cmd
import datetime
import logging
import os
import sys
import traceback
from typing import cast

import psycopg2
import pytz
from pyparsing import ParseException

from haystackapi.providers import get_provider
from haystackapi.providers.db_postgres import _sql_filter
from haystackapi.providers.sql import Provider

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def main():
    """ Loop to test the postgres generation with REPL """
    x = get_provider("haystackapi.providers.sql")
    print(type(x))
    conn = cast(Provider, get_provider("haystackapi.providers.sql")).get_connect()

    class TstRequest(cmd.Cmd):
        def __init__(self, conn):
            super().__init__()
            self.conn = conn

        def do_pg(self, arg):
            try:
                with self.conn.cursor() as cursor:
                    sql_request = _sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                    print(sql_request)
                    cursor.execute(sql_request)
            except (psycopg2.errors.SyntaxError, ParseException, Exception):
                traceback.print_exc()
            finally:
                conn.rollback()
                pass

        def do_bye(self, arg):
            self.close()

    TstRequest(conn).cmdloop()
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())
