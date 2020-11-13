# --------------------------------------------------------------------------------------
# Test generated sql request for Postgres
import datetime
import logging
import os
import textwrap

import pytz

from haystackapi.providers import get_provider
from haystackapi.providers.db_postgres import _sql_filter as sql_filter

# Set this variable to True, to validate the parsing of the result by postgresql
check_postgres = True

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING"))

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


def check_pg(sql_request: str):
    if check_postgres:
        old = os.environ.get('HAYSTACK_DB')
        os.environ['HAYSTACK_DB'] = 'postgresql://postgres:password@172.17.0.2:5432/postgres#haystack'
        provider = get_provider("haystackapi.providers.sql")
        if old:
            os.environ['HAYSTACK_DB'] = old
        with provider.get_connect().cursor() as cursor:
            cursor.execute(sql_request)


def test_and_ltag_rtag():
    hs_filter = 'site and ref'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- site and ref
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?& array['site', 'ref']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_andtag_rtag():
    hs_filter = '(site and ref) and his'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- (site and ref) and his
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_ltag_andtag():
    hs_filter = 'his and (site and ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- his and (site and ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_andtag_andtag():
    hs_filter = '(his and point) and (site and ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- (his and point) and (site and ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?& array['his', 'point', 'site', 'ref']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_not_ltag_rtag():
    hs_filter = 'not site and not ref'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- not site and not ref
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND NOT t1.entity ?& array['site', 'ref']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_not_andtag_rtag():
    hs_filter = '(not site and not ref) and not his'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- (not site and not ref) and not his
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND NOT t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_not_ltag_andtag():
    hs_filter = 'not his and (not site and not ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- not his and (not site and not ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND NOT t1.entity ?& array['site', 'ref', 'his']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_not_andtag_andtag():
    hs_filter = '(not his and not point) and (not site and not ref)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- (not his and not point) and (not site and not ref)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND NOT t1.entity ?& array['his', 'point', 'site', 'ref']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal():
    hs_filter = 'geoPostal==78000'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- geoPostal==78000
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'geoPostal' = 'n:78000.000000'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_has_and_equal():
    hs_filter = 'site and geoPostal==78000'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- site and geoPostal==78000
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ? 'site'
        AND
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'geoPostal' = 'n:78000.000000'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_with_not():
    hs_filter = 'site and his and not geoPostal'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- site and his and not geoPostal
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?& array['site', 'his']
        AND
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND NOT t1.entity ? 'geoPostal'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_not_a_number():
    hs_filter = 'geoState=="MN"'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- geoState=="MN"
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'geoState' = 's:MN'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_number():
    hs_filter = 'geoPostalCode==1111'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- geoPostalCode==1111
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'geoPostalCode' = 'n:1111.000000'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_greater_number():
    hs_filter = 'geoPostalCode > 55400'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- geoPostalCode > 55400
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND substring(t1.entity->>'geoPostalCode' from 3)::float > 55400.0
        LIMIT 1
        """)
    check_pg(sql_request)


def test_greater_quantity():
    hs_filter = 'temp > 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- temp > 55400°
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND substring(t1.entity->>'temp' from 3)::float > 55400.0
        LIMIT 1
        """)
    check_pg(sql_request)


def test_path_equal_quantity():
    hs_filter = 'siteRef->temp == 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- siteRef->temp == 55400°
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->'siteRef' = t2.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t2.start_datetime AND ('2020-10-01T00:00:00+00:00' < t2.end_datetime or t2.end_datetime is NULL)
        AND
        t2.customer_id='customer' AND t2.entity->>'temp' = 'n:55400.000000 °'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_2path_greater_quantity():
    hs_filter = 'siteRef->temp >= 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- siteRef->temp >= 55400°
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->'siteRef' = t2.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t2.start_datetime AND ('2020-10-01T00:00:00+00:00' < t2.end_datetime or t2.end_datetime is NULL)
        AND
        t2.customer_id='customer' AND substring(t2.entity->>'temp' from 3)::float >= 55400.0
        LIMIT 1
        """)
    check_pg(sql_request)


def test_3path_greater_quantity():
    hs_filter = 'siteRef->ownerRef->temp >= 55400°'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- siteRef->ownerRef->temp >= 55400°
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->'siteRef' = t2.entity->'id'
        INNER JOIN haystack AS t3 ON
        '2020-10-01T00:00:00+00:00' >= t2.start_datetime AND ('2020-10-01T00:00:00+00:00' < t2.end_datetime or t2.end_datetime is NULL)
        AND
        t2.customer_id='customer' AND t2.entity->'ownerRef' = t3.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t3.start_datetime AND ('2020-10-01T00:00:00+00:00' < t3.end_datetime or t3.end_datetime is NULL)
        AND
        t3.customer_id='customer' AND substring(t3.entity->>'temp' from 3)::float >= 55400.0
        LIMIT 1
        """)
    check_pg(sql_request)


def test_path():
    hs_filter = 'siteRef->geoPostalCode'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- siteRef->geoPostalCode
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->'siteRef' = t2.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t2.start_datetime AND ('2020-10-01T00:00:00+00:00' < t2.end_datetime or t2.end_datetime is NULL)
        AND
        t2.customer_id='customer' AND t2.entity ? 'geoPostalCode'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_path_and():
    hs_filter = 'siteRef->geoPostalCode and siteRef->geoCountry'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- siteRef->geoPostalCode and siteRef->geoCountry
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->'siteRef' = t2.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t2.start_datetime AND ('2020-10-01T00:00:00+00:00' < t2.end_datetime or t2.end_datetime is NULL)
        AND
        t2.customer_id='customer' AND t2.entity ? 'geoPostalCode'
        INTERSECT
        SELECT t3.entity
        FROM haystack as t3
        INNER JOIN haystack AS t4 ON
        '2020-10-01T00:00:00+00:00' >= t3.start_datetime AND ('2020-10-01T00:00:00+00:00' < t3.end_datetime or t3.end_datetime is NULL)
        AND
        t3.customer_id='customer' AND t3.entity->'siteRef' = t4.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t4.start_datetime AND ('2020-10-01T00:00:00+00:00' < t4.end_datetime or t4.end_datetime is NULL)
        AND
        t4.customer_id='customer' AND t4.entity ? 'geoCountry'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_path_or():
    hs_filter = 'siteRef->geoPostalCode or siteRef->geoCountry'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- siteRef->geoPostalCode or siteRef->geoCountry
        SELECT t1.entity
        FROM haystack as t1
        INNER JOIN haystack AS t2 ON
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->'siteRef' = t2.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t2.start_datetime AND ('2020-10-01T00:00:00+00:00' < t2.end_datetime or t2.end_datetime is NULL)
        AND
        t2.customer_id='customer' AND t2.entity ? 'geoPostalCode'
        UNION
        SELECT t3.entity
        FROM haystack as t3
        INNER JOIN haystack AS t4 ON
        '2020-10-01T00:00:00+00:00' >= t3.start_datetime AND ('2020-10-01T00:00:00+00:00' < t3.end_datetime or t3.end_datetime is NULL)
        AND
        t3.customer_id='customer' AND t3.entity->'siteRef' = t4.entity->'id'
        AND
        '2020-10-01T00:00:00+00:00' >= t4.start_datetime AND ('2020-10-01T00:00:00+00:00' < t4.end_datetime or t4.end_datetime is NULL)
        AND
        t4.customer_id='customer' AND t4.entity ? 'geoCountry'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_and_or():
    hs_filter = '(a or b) and (c or d)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- (a or b) and (c or d)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?| array['a', 'b']
        AND
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity ?| array['c', 'd']
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_ref():
    hs_filter = 'a == @id'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == @id
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'r:id'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_str():
    hs_filter = 'a == "abc"'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == "abc"
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 's:abc'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_int():
    hs_filter = 'a == 1'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == 1
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'n:1.000000'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_float():
    hs_filter = 'a == 1.0'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == 1.0
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'n:1.000000'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_bool():
    hs_filter = 'a == true'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == true
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'True'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_datetime():
    hs_filter = 'a == 1977-04-22T01:00:00-00:00'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == 1977-04-22T01:00:00-00:00
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 't:1977-04-22T01:00:00+00:00 UTC'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_time():
    hs_filter = 'a == 01:00:00'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == 01:00:00
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'h:01:00:00'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_date():
    hs_filter = 'a == 1977-04-22'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == 1977-04-22
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'd:1977-04-22'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_coord():
    hs_filter = 'a == C(100,100)'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == C(100,100)
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'c:100.000000,100.000000'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_NA():
    hs_filter = 'a == NA'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == NA
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'z:'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_Null():
    hs_filter = 'a == N'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == N
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' IS NULL
        LIMIT 1
        """)
    check_pg(sql_request)


def test_not_equal_Null():
    hs_filter = 'a != N'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a != N
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' IS NOT NULL
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_Marker():
    hs_filter = 'a == M'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == M
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'm:'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_uri():
    hs_filter = 'a == `http://l`'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == `http://l`
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'u:http://l'
        LIMIT 1
        """)
    check_pg(sql_request)


def test_equal_xstr():
    hs_filter = 'a == hex("deadbeef")'
    sql_request = sql_filter('haystack', hs_filter, FAKE_NOW, 1, "customer")
    assert sql_request == textwrap.dedent("""\
        -- a == hex("deadbeef")
        SELECT t1.entity
        FROM haystack as t1
        WHERE
        '2020-10-01T00:00:00+00:00' >= t1.start_datetime AND ('2020-10-01T00:00:00+00:00' < t1.end_datetime or t1.end_datetime is NULL)
        AND
        t1.customer_id='customer' AND t1.entity->>'a' = 'x:hex:deadbeef'
        LIMIT 1
        """)
    check_pg(sql_request)
