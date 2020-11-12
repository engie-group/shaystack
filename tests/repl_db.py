import cmd
import datetime
import logging
import os
import sys
import traceback

import psycopg2
import pytz
from pyparsing import ParseException

from haystackapi.providers import get_provider
from haystackapi.providers.db_postgres import _sql_filter

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def main():
    """ Loop to test the postgres generation with REPL """

    conn = get_provider("haystackapi.providers.sql").get_connect()
    cursor = conn.cursor()

    class TstRequest(cmd.Cmd):
        def __init__(self, conn, cursor):
            super().__init__()
            self.conn = conn
            self.cursor = cursor

        def do_pg(self, arg):
            try:
                sql_request = _sql_filter("haystack", arg, FAKE_NOW, 1, "customer")
                print(sql_request)
                cursor.execute(sql_request)
                conn.rollback()
            except (psycopg2.errors.SyntaxError, ParseException, Exception):
                traceback.print_exc()
            finally:
                pass

        def do_bye(self, arg):
            self.close()

    TstRequest(conn, cursor).cmdloop()
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "ERROR"))
    sys.exit(main())
