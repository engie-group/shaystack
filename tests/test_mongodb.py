# --------------------------------------------------------------------------------------
# Test generated sql request for Postgres.
# If the HAYSTACK_DB use postgresql://...,
# a real connection is open with Postgres.
import datetime
import logging
import os
from typing import cast, Dict, Any

import pytz

from shaystack.providers import get_provider
from shaystack.providers.db_mongo import _mongo_filter as mongo_filter
from shaystack.providers.mongodb import Provider as MongoProvider

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING"))

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


# If .env set the HAYSTACK_DB to postgres, check to execute the sql request
def _check_mongodb(mongo_request: Dict[str, Any]):
    if os.environ.get('HAYSTACK_DB', '').startswith("mongodb"):
        envs = {'HAYSTACK_DB': os.environ['HAYSTACK_DB']}
        provider = cast(MongoProvider, get_provider("shaystack.providers.mongodb", envs))
        collection = provider.get_collection()
        collection.find(mongo_request)


def test_tag():
    hs_filter = 'site'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_not_tag():
    hs_filter = 'not site'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_ref():
    hs_filter = 'a == @id'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_str():
    hs_filter = 'a == "abc"'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_int():
    hs_filter = 'a == 1'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_float():
    hs_filter = 'a == 1.0'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_bool():
    hs_filter = 'a == true'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_datetime():
    hs_filter = 'a == 1977-04-22T01:00:00-00:00'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_time():
    hs_filter = 'a == 01:00:00'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_date():
    hs_filter = 'a == 1977-04-22'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_coord():
    hs_filter = 'a == C(100,100)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_NA():
    hs_filter = 'a == NA'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_Null():
    hs_filter = 'a == N'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_not_equal_Null():
    hs_filter = 'a != N'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_Marker():
    hs_filter = 'a == M'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_uri():
    hs_filter = 'a == `http://l`'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_xstr():
    hs_filter = 'a == hex("deadbeef")'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_ltag_rtag():
    hs_filter = 'site and ref'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_andtag_rtag():
    hs_filter = '(site and ref) and his'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_ltag_andtag():
    hs_filter = 'his and (site and ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_andtag_andtag():
    hs_filter = '(his and point) and (site and ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_not_ltag_rtag():
    hs_filter = 'not site and not ref'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_not_andtag_rtag():
    hs_filter = '(not site and not ref) and not his'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_not_ltag_andtag():
    hs_filter = 'not his and (not site and not ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_not_andtag_andtag():
    hs_filter = '(not his and not point) and (not site and not ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal():
    hs_filter = 'geoPostal==78000'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_has_and_equal():
    hs_filter = 'site and geoPostal==78000'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_with_not():
    hs_filter = 'site and his and not geoPostal'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_equal_number():
    hs_filter = 'geoPostalCode==1111'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_greater_number():
    hs_filter = 'geoPostalCode > 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_greater_or_equal_number():
    hs_filter = 'geoPostalCode >= 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_lower_number():
    hs_filter = 'geoPostalCode < 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_lower_or_equal_number():
    hs_filter = 'geoPostalCode <= 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_greater_quantity():
    hs_filter = 'temp > 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_greater_or_equal_quantity():
    hs_filter = 'temp >= 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_path_equal_quantity():
    hs_filter = 'siteRef->temp == 55400deg'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_2path_greater_quantity():
    hs_filter = 'siteRef->temp >= 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_3path_greater_quantity():
    hs_filter = 'siteRef->ownerRef->temp >= 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_4path():
    hs_filter = 'siteRef->ownerRef->a->b'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_path():
    hs_filter = 'siteRef->geoPostalCode'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_path_and():
    hs_filter = 'siteRef->geoPostalCode and siteRef->geoCountry'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_path_or():
    hs_filter = 'siteRef->geoPostalCode or siteRef->geoCountry'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_or():
    hs_filter = '(a or b) and (c or d)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_or_and():
    hs_filter = 'site or (elect and point)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_or_and():
    hs_filter = 'site and (elect or point) and toto'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_and_or_path():
    hs_filter = '(a->b or c->d) and (e->f or g->h)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_complex():
    hs_filter = '(a->b or c->d) and e or (f and g->h)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_combine_and():
    hs_filter = '(a==1 and b==1) or (c==2 and d==3)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False


def test_select_with_id():
    hs_filter = 'id==@p:demo:r:23a44701-3a62fd7a'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(mongo_request)
    assert False