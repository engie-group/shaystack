# --------------------------------------------------------------------------------------
# Test generated sql request for Postgres.
# If the HAYSTACK_DB use postgresql://...,
# a real connection is open with Postgres.
import datetime
import logging
import os
import textwrap
from typing import cast

import pytz

from shaystack.providers import get_provider
# noinspection PyProtectedMember
from shaystack.providers.db_postgres import _sql_filter as sql_filter
from shaystack.providers.sql import Provider as SQLProvider

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING"))

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


# If .env set the HAYSTACK_DB to postgres, check to execute the sql request
def _check_pg(sql_request: str):
    if os.environ.get('HAYSTACK_DB', '').startswith("postgres"):
        envs = {'HAYSTACK_DB': os.environ['HAYSTACK_DB']}
        provider = cast(SQLProvider, get_provider("shaystack.providers.sql", envs))
        conn = provider.get_connect()
        try:
            list(conn.cursor().execute(sql_request))
        finally:
            conn.rollback()


def test_tag():
    hs_filter = 'site'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- site
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity ? 'site'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_not_tag():
    hs_filter = 'not site'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- not site
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND NOT t1.entity ? 'site'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_ref():
    hs_filter = 'a == @id'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == @id
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' LIKE 'r:id%'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_str():
    hs_filter = 'a == "abc"'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == "abc"
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'a',3) = 'abc'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_int():
    hs_filter = 'a == 1'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == 1
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'n:1.000000'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_float():
    hs_filter = 'a == 1.0'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == 1.0
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'n:1.000000'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_bool():
    hs_filter = 'a == true'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == true
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'True'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_datetime():
    hs_filter = 'a == 1977-04-22T01:00:00-00:00'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == 1977-04-22T01:00:00-00:00
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'a',3,25)::TIMESTAMP = TIMESTAMP '1977-04-22T01:00:00+00:00'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_time():
    hs_filter = 'a == 01:00:00'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == 01:00:00
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'a',3)::TIME = TIME '01:00:00'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_date():
    hs_filter = 'a == 1977-04-22'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == 1977-04-22
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'a',3)::DATE = DATE '1977-04-22'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_coord():
    hs_filter = 'a == C(100,100)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == C(100,100)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'c:100.000000,100.000000'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_NA():
    hs_filter = 'a == NA'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == NA
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'z:'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_Null():
    hs_filter = 'a == N'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == N
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' IS NULL
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_not_equal_Null():
    hs_filter = 'a != N'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a != N
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' IS NOT NULL
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_Marker():
    hs_filter = 'a == M'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == M
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'm:'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_uri():
    hs_filter = 'a == `http://l`'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == `http://l`
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'a',3) = 'http://l'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_xstr():
    hs_filter = 'a == hex("deadbeef")'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- a == hex("deadbeef")
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'a' = 'x:hex:deadbeef'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_ltag_rtag():
    hs_filter = 'site and ref'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- site and ref
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity ?& array['site', 'ref']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_andtag_rtag():
    hs_filter = '(site and ref) and his'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (site and ref) and his
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_ltag_andtag():
    hs_filter = 'his and (site and ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- his and (site and ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_andtag_andtag():
    hs_filter = '(his and point) and (site and ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (his and point) and (site and ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity ?& array['his', 'point', 'site', 'ref']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_not_ltag_rtag():
    hs_filter = 'not site and not ref'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- not site and not ref
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND NOT t1.entity ?& array['site', 'ref']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_not_andtag_rtag():
    hs_filter = '(not site and not ref) and not his'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (not site and not ref) and not his
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND NOT t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_not_ltag_andtag():
    hs_filter = 'not his and (not site and not ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- not his and (not site and not ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND NOT t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_not_andtag_andtag():
    hs_filter = '(not his and not point) and (not site and not ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (not his and not point) and (not site and not ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND NOT t1.entity ?& array['his', 'point', 'site', 'ref']
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal():
    hs_filter = 'geoPostal==78000'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- geoPostal==78000
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'geoPostal' = 'n:78000.000000'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_has_and_equal():
    hs_filter = 'site and geoPostal==78000'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- site and geoPostal==78000
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND (t1.entity ? 'site')
        AND (t1.entity->>'geoPostal' = 'n:78000.000000')
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_with_not():
    hs_filter = 'site and his and not geoPostal'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- site and his and not geoPostal
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND (t1.entity ?& array['site', 'his'])
        AND (NOT t1.entity ? 'geoPostal')
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_equal_number():
    hs_filter = 'geoPostalCode==1111'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- geoPostalCode==1111
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'geoPostalCode' = 'n:1111.000000'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_greater_number():
    hs_filter = 'geoPostalCode > 55400'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- geoPostalCode > 55400
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'geoPostalCode',3)::float > 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_greater_or_equal_number():
    hs_filter = 'geoPostalCode >= 55400'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- geoPostalCode >= 55400
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'geoPostalCode',3)::float >= 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_lower_number():
    hs_filter = 'geoPostalCode < 55400'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- geoPostalCode < 55400
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'geoPostalCode',3)::float < 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_lower_or_equal_number():
    hs_filter = 'geoPostalCode <= 55400'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- geoPostalCode <= 55400
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'geoPostalCode',3)::float <= 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_greater_quantity():
    hs_filter = 'temp > 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- temp > 55400°
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'temp',3)::float > 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_greater_or_equal_quantity():
    hs_filter = 'temp >= 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- temp >= 55400°
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND SUBSTRING(t1.entity->>'temp',3)::float >= 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_path_equal_quantity():
    hs_filter = 'siteRef->temp == 55400deg'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->temp == 55400deg
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        AND t2.entity->>'temp' = 'n:55400.000000 deg'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_2path_greater_quantity():
    hs_filter = 'siteRef->temp >= 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->temp >= 55400°
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        AND SUBSTRING(t2.entity->>'temp',3)::float >= 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_3path_greater_quantity():
    hs_filter = 'siteRef->ownerRef->temp >= 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->ownerRef->temp >= 55400°
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        INNER JOIN haystack AS t3 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t3.start_datetime AND t3.end_datetime
        AND t3.customer_id='customer'
        AND t2.entity->'ownerRef' = t3.entity->'id'
        AND SUBSTRING(t3.entity->>'temp',3)::float >= 55400.0
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_4path():
    hs_filter = 'siteRef->ownerRef->a->b'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->ownerRef->a->b
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        INNER JOIN haystack AS t3 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t3.start_datetime AND t3.end_datetime
        AND t3.customer_id='customer'
        AND t2.entity->'ownerRef' = t3.entity->'id'
        INNER JOIN haystack AS t4 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t4.start_datetime AND t4.end_datetime
        AND t4.customer_id='customer'
        AND t3.entity->'a' = t4.entity->'id'
        AND t4.entity ? 'b'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_path():
    hs_filter = 'siteRef->geoPostalCode'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->geoPostalCode
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        AND t2.entity ? 'geoPostalCode'
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_path_and():
    hs_filter = 'siteRef->geoPostalCode and siteRef->geoCountry'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->geoPostalCode and siteRef->geoCountry
        (
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        AND t2.entity ? 'geoPostalCode'
        )
        INTERSECT
        (
        SELECT t3.entity
        FROM haystack as t3
        INNER JOIN haystack AS t4 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t3.start_datetime AND t3.end_datetime
        AND t3.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t4.start_datetime AND t4.end_datetime
        AND t4.customer_id='customer'
        AND t3.entity->'siteRef' = t4.entity->'id'
        AND t4.entity ? 'geoCountry'
        )
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_path_or():
    hs_filter = 'siteRef->geoPostalCode or siteRef->geoCountry'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- siteRef->geoPostalCode or siteRef->geoCountry
        (
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'siteRef' = t2.entity->'id'
        AND t2.entity ? 'geoPostalCode'
        )
        UNION
        (
        SELECT t3.entity
        FROM haystack as t3
        INNER JOIN haystack AS t4 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t3.start_datetime AND t3.end_datetime
        AND t3.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t4.start_datetime AND t4.end_datetime
        AND t4.customer_id='customer'
        AND t3.entity->'siteRef' = t4.entity->'id'
        AND t4.entity ? 'geoCountry'
        )
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_or():
    hs_filter = '(a or b) and (c or d)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (a or b) and (c or d)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND (t1.entity ?| array['a', 'b'])
        AND (t1.entity ?| array['c', 'd'])
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_or_and():
    hs_filter = 'site or (elect and point)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- site or (elect and point)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND (t1.entity ? 'site')
        OR (t1.entity ?& array['elect', 'point'])
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_or_and():
    hs_filter = 'site and (elect or point) and toto'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- site and (elect or point) and toto
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND ((t1.entity ? 'site')
        AND (t1.entity ?| array['elect', 'point']))
        AND (t1.entity ? 'toto')
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_and_or_path():
    hs_filter = '(a->b or c->d) and (e->f or g->h)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (a->b or c->d) and (e->f or g->h)
        (
        (
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'a' = t2.entity->'id'
        AND t2.entity ? 'b'
        )
        UNION
        (
        SELECT t3.entity
        FROM haystack as t3
        INNER JOIN haystack AS t4 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t3.start_datetime AND t3.end_datetime
        AND t3.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t4.start_datetime AND t4.end_datetime
        AND t4.customer_id='customer'
        AND t3.entity->'c' = t4.entity->'id'
        AND t4.entity ? 'd'
        )
        )
        INTERSECT
        (
        (
        SELECT t5.entity
        FROM haystack as t5
        INNER JOIN haystack AS t6 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t5.start_datetime AND t5.end_datetime
        AND t5.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t6.start_datetime AND t6.end_datetime
        AND t6.customer_id='customer'
        AND t5.entity->'e' = t6.entity->'id'
        AND t6.entity ? 'f'
        )
        UNION
        (
        SELECT t7.entity
        FROM haystack as t7
        INNER JOIN haystack AS t8 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t7.start_datetime AND t7.end_datetime
        AND t7.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t8.start_datetime AND t8.end_datetime
        AND t8.customer_id='customer'
        AND t7.entity->'g' = t8.entity->'id'
        AND t8.entity ? 'h'
        )
        )
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_complex():
    hs_filter = '(a->b or c->d) and e or (f and g->h)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (a->b or c->d) and e or (f and g->h)
        (
        (
        (
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t2.start_datetime AND t2.end_datetime
        AND t2.customer_id='customer'
        AND t1.entity->'a' = t2.entity->'id'
        AND t2.entity ? 'b'
        )
        UNION
        (
        SELECT t3.entity
        FROM haystack as t3
        INNER JOIN haystack AS t4 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t3.start_datetime AND t3.end_datetime
        AND t3.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t4.start_datetime AND t4.end_datetime
        AND t4.customer_id='customer'
        AND t3.entity->'c' = t4.entity->'id'
        AND t4.entity ? 'd'
        )
        )
        INTERSECT
        (
        SELECT t5.entity
        FROM haystack as t5
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t5.start_datetime AND t5.end_datetime
        AND t5.customer_id='customer'
        AND t5.entity ? 'e'
        )
        )
        UNION
        (
        (
        SELECT t6.entity
        FROM haystack as t6
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t6.start_datetime AND t6.end_datetime
        AND t6.customer_id='customer'
        AND t6.entity ? 'f'
        )
        INTERSECT
        (
        SELECT t7.entity
        FROM haystack as t7
        INNER JOIN haystack AS t8 ON
        '{FAKE_NOW.isoformat()}' BETWEEN t7.start_datetime AND t7.end_datetime
        AND t7.customer_id='customer'
        AND '{FAKE_NOW.isoformat()}' BETWEEN t8.start_datetime AND t8.end_datetime
        AND t8.customer_id='customer'
        AND t7.entity->'g' = t8.entity->'id'
        AND t8.entity ? 'h'
        )
        )
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_combine_and():
    hs_filter = '(a==1 and b==1) or (c==2 and d==3)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent(f"""\
        -- (a==1 and b==1) or (c==2 and d==3)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND ((t1.entity->>'a' = 'n:1.000000')
        AND (t1.entity->>'b' = 'n:1.000000'))
        OR ((t1.entity->>'c' = 'n:2.000000')
        AND (t1.entity->>'d' = 'n:3.000000'))
        LIMIT 1
        """)
    _check_pg(sql_request)


def test_select_with_id():
    hs_filter = 'id==@p:demo:r:23a44701-3a62fd7a'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    _check_pg(sql_request)
    assert sql_request == textwrap.dedent(f"""\
        -- id==@p:demo:r:23a44701-3a62fd7a
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '{FAKE_NOW.isoformat()}' BETWEEN t1.start_datetime AND t1.end_datetime
        AND t1.customer_id='customer'
        AND t1.entity->>'id' LIKE 'r:p:demo:r:23a44701-3a62fd7a%'
        LIMIT 1
        """)
