# --------------------------------------------------------------------------------------
# Test generated sql request for Postgres.
# If the HAYSTACK_DB use postgresql://...,
# a real connection is open with Postgres.
import datetime
import logging
import os
from typing import cast, Dict, Any, List

import pytz

from shaystack.providers import get_provider
# noinspection PyProtectedMember
from shaystack.providers.db_mongo import _mongo_filter as mongo_filter
from shaystack.providers.mongodb import Provider as MongoProvider

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "WARNING"))

FAKE_NOW = datetime.datetime(2100, 1, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)


# If .env set the HAYSTACK_DB to postgres, check to execute the sql request
# noinspection PyUnusedLocal
def _check_mongodb(hs_filter: str,  # pylint: disable=unused-argument,unused-variable
                   mongo_request: List[Dict[str, Any]]):
    if os.environ.get('HAYSTACK_DB', '').startswith("mongodb"):
        envs = {'HAYSTACK_DB': os.environ['HAYSTACK_DB']}
        provider = cast(MongoProvider, get_provider("shaystack.providers.mongodb", envs))
        collection = provider.get_collection()
        result = list(collection.aggregate(mongo_request))   # type: ignore # pylint: disable=unused-variable
        # print(f"# {hs_filter}")
        # pprint.PrettyPrinter(indent=2).pprint(result)


def test_tag():
    hs_filter = 'site'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$ne': [{'$type': '$site'}, 'missing']}}}, {'$limit': 1}]


def test_not_tag():
    hs_filter = 'not site'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': [{'$type': '$site'}, 'missing']}}}, {'$limit': 1}]


def test_equal_ref():
    hs_filter = 'id == @id_site'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$eq': [{'$let': {
                   'vars': {'id_regex_': {'$regexFind': {'input': '$id', 'regex': 'r:([:.~a-zA-Z0-9_-]+)'}}},
                   'in': {'$arrayElemAt': ['$$id_regex_.captures', 0]}}}, 'id_site']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_str():
    hs_filter = 'a == "abc"'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 's:abc']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_int():
    hs_filter = 'a == 1'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'n:1.000000']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_float():
    hs_filter = 'a == 1.0'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'n:1.000000']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_bool():
    hs_filter = 'a == true'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'ru']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_datetime():
    hs_filter = 'a == 1977-04-22T01:00:00-00:00'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 't:1977-04-22T01:00:00+00:00 UTC']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_time():
    hs_filter = 'a == 01:00:00'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'h:01:00:00']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_date():
    hs_filter = 'a == 1977-04-22'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'd:1977-04-22']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_coord():
    hs_filter = 'a == C(100,100)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'c:100.000000,100.000000']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_NA():
    hs_filter = 'a == NA'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'z:']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_Null():
    hs_filter = 'a == N'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'ul']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_not_equal_Null():
    hs_filter = 'a != N'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {
               '$lte': FAKE_NOW}, 'end_datetime': {
               '$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {
                '$match': {'$expr': {'$ne': ['$a', 'ul']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_Marker():
    hs_filter = 'a == M'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'm:']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_uri():
    hs_filter = 'a == `http://l`'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'u:http://l']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_xstr():
    hs_filter = 'a == hex("deadbeef")'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$a', 'x:hex:deadbeef']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_and_ltag_rtag():
    hs_filter = 'site and ref'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {'$ne': [{'$type': '$ref'}, 'missing']}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_andtag_rtag():
    hs_filter = '(site and ref) and his'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [
                   {'$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {'$ne': [{'$type': '$ref'}, 'missing']}]},
                   {'$ne': [{'$type': '$his'}, 'missing']}]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_and_ltag_andtag():
    hs_filter = 'his and (site and ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [{'$ne': [{'$type': '$his'}, 'missing']}, {
                   '$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {'$ne': [{'$type': '$ref'}, 'missing']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_andtag_andtag():
    hs_filter = '(his and point) and (site and ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [
                   {'$and': [{'$ne': [{'$type': '$his'}, 'missing']}, {'$ne': [{'$type': '$point'}, 'missing']}]},
                   {'$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {'$ne': [{'$type': '$ref'}, 'missing']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_not_ltag_rtag():
    hs_filter = 'not site and not ref'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [{'$eq': [{'$type': '$site'}, 'missing']}, {'$eq': [{'$type': '$ref'}, 'missing']}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_not_andtag_rtag():
    hs_filter = '(not site and not ref) and not his'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [
                   {'$and': [{'$eq': [{'$type': '$site'}, 'missing']}, {'$eq': [{'$type': '$ref'}, 'missing']}]},
                   {'$eq': [{'$type': '$his'}, 'missing']}]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_and_not_ltag_andtag():
    hs_filter = 'not his and (not site and not ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [{'$eq': [{'$type': '$his'}, 'missing']}, {
                   '$and': [{'$eq': [{'$type': '$site'}, 'missing']}, {'$eq': [{'$type': '$ref'}, 'missing']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_not_andtag_andtag():
    hs_filter = '(not his and not point) and (not site and not ref)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [
                   {'$and': [{'$eq': [{'$type': '$his'}, 'missing']}, {'$eq': [{'$type': '$point'}, 'missing']}]},
                   {'$and': [{'$eq': [{'$type': '$site'}, 'missing']}, {'$eq': [{'$type': '$ref'}, 'missing']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_equal():
    hs_filter = 'geoPostal==78000'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$geoPostal', 'n:78000.000000']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_has_and_equal():
    hs_filter = 'site and geoPostal==78000'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {
                   '$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {'$eq': ['$geoPostal', 'n:78000.000000']}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_with_not():
    hs_filter = 'site and his and not geoPostal'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [
                   {'$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {'$ne': [{'$type': '$his'}, 'missing']}]},
                   {'$eq': [{'$type': '$geoPostal'}, 'missing']}]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_equal_number():
    hs_filter = 'geoPostalCode==1111'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}},
            {'$match': {'$expr': {'$eq': ['$geoPostalCode', 'n:1111.000000']}}}, {'$limit': 1}]


# noinspection PyPep8
def test_greater_number():
    hs_filter = 'curVal > 1'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$gt': [{'$let': {'vars': {'curVal_regex_': {
                   '$regexFind': {'input': '$curVal', 'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                   'in': {'$toDouble': {'$arrayElemAt': ['$$curVal_regex_.captures', 0]}}}},
                   1.0]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_greater_or_equal_number():
    hs_filter = 'geoPostalCode >= 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$gte': [{'$let': {'vars': {'geoPostalCode_regex_': {
                   '$regexFind': {'input': '$geoPostalCode', 'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                   'in': {'$toDouble': {
                       '$arrayElemAt': ['$$geoPostalCode_regex_.captures', 0]}}}}, 55400.0]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_lower_number():
    hs_filter = 'geoPostalCode < 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$lt': [{'$let': {'vars': {'geoPostalCode_regex_': {
                   '$regexFind': {'input': '$geoPostalCode', 'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                   'in': {
                       '$toDouble': {'$arrayElemAt': ['$$geoPostalCode_regex_.captures', 0]}}}},
                   55400.0]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_lower_or_equal_number():
    hs_filter = 'geoPostalCode <= 55400'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$lte': [{'$let': {'vars': {'geoPostalCode_regex_': {
                   '$regexFind': {'input': '$geoPostalCode', 'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                   'in': {'$toDouble': {
                       '$arrayElemAt': ['$$geoPostalCode_regex_.captures', 0]}}}}, 55400.0]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_greater_quantity():
    hs_filter = 'temp > 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$gt': [{'$let': {'vars': {'temp_regex_': {
                   '$regexFind': {'input': '$temp', 'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                   'in': {'$toDouble': {'$arrayElemAt': ['$$temp_regex_.captures', 0]}}}},
                   55400.0]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_greater_or_equal_quantity():
    hs_filter = 'temp >= 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$gte': [{'$let': {'vars': {'temp_regex_': {
                   '$regexFind': {'input': '$temp', 'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                   'in': {'$toDouble': {'$arrayElemAt': ['$$temp_regex_.captures', 0]}}}},
                   55400.0]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_and_or():
    hs_filter = '(a or b) and (c or d)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {
                   '$and': [{'$or': [{'$ne': [{'$type': '$a'}, 'missing']}, {'$ne': [{'$type': '$b'}, 'missing']}]},
                            {'$or': [{'$ne': [{'$type': '$c'}, 'missing']}, {'$ne': [{'$type': '$d'}, 'missing']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_or_and():
    hs_filter = 'site or (elect and point)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$or': [{'$ne': [{'$type': '$site'}, 'missing']}, {
                   '$and': [{'$ne': [{'$type': '$elect'}, 'missing']}, {'$ne': [{'$type': '$point'}, 'missing']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_and_or_and():
    hs_filter = 'site and (elect or point) and toto'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$and': [{'$and': [{'$ne': [{'$type': '$site'}, 'missing']}, {
                   '$or': [{'$ne': [{'$type': '$elect'}, 'missing']}, {'$ne': [{'$type': '$point'}, 'missing']}]}]},
                                  {'$ne': [{'$type': '$toto'}, 'missing']}]}}}, {'$limit': 1}]


# noinspection PyPep8
def test_combine_and():
    hs_filter = '(a==1 and b==1) or (c==2 and d==3)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$or': [{'$and': [{'$eq': ['$a', 'n:1.000000']}, {'$eq': ['$b', 'n:1.000000']}]},
                                 {'$and': [{'$eq': ['$c', 'n:2.000000']}, {'$eq': ['$d', 'n:3.000000']}]}]}}},
            {'$limit': 1}]


# noinspection PyPep8
def test_select_with_id():
    hs_filter = 'id==@p:demo:r:23a44701-3a62fd7a'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 1, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {'$lte': FAKE_NOW},
                        'end_datetime': {'$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {'$match': {
               '$expr': {'$eq': [{'$let': {
                   'vars': {'id_regex_': {'$regexFind': {'input': '$id', 'regex': 'r:([:.~a-zA-Z0-9_-]+)'}}},
                   'in': {'$arrayElemAt': ['$$id_regex_.captures', 0]}}}, 'p:demo:r:23a44701-3a62fd7a']}}},
            {'$limit': 1}]


def test_path():
    hs_filter = 'equipRef->siteRef'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [
               {'$match': {
                   'customer_id': 'customer',
                   'start_datetime': {'$lte': FAKE_NOW},
                   'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'equipRef_entity_',
                   'let': {'equipRef_id_': '$equipRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$equipRef_id_']}]}}}]}},
               {'$set': {'equipRef_entity_': {'$arrayElemAt': ['$equipRef_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$ne': [{'$type': '$equipRef_entity_.siteRef'}, 'missing']}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


def test_not_path():
    hs_filter = 'not equipRef->siteRef'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [
               {'$match': {
                   'customer_id': 'customer',
                   'start_datetime': {'$lte': FAKE_NOW},
                   'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'equipRef_entity_',
                   'let': {'equipRef_id_': '$equipRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$equipRef_id_']}]}}}]}},
               {'$set': {'equipRef_entity_': {'$arrayElemAt': ['$equipRef_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$eq': [{'$type': '$equipRef_entity_.siteRef'}, 'missing']}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


def test_path_and():
    hs_filter = 'equipRef->siteRef and equipRef->siteRef'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [
               {'$match': {
                   'customer_id': 'customer',
                   'start_datetime': {'$lte': FAKE_NOW},
                   'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'equipRef_entity_',
                   'let': {'equipRef_id_': '$equipRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$equipRef_id_']}]}}}]}},
               {'$set': {'equipRef_entity_': {'$arrayElemAt': ['$equipRef_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$and': [
                   {'$ne': [{'$type': '$equipRef_entity_.siteRef'}, 'missing']},
                   {'$ne': [{'$type': '$equipRef_entity_.siteRef'}, 'missing']}]}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


# noinspection PyPep8
def test_path_or():
    hs_filter = 'siteRef->geoPostalCode or siteRef->geoCountry'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [{'$match': {'customer_id': 'customer', 'start_datetime': {
               '$lte': FAKE_NOW}, 'end_datetime': {
               '$gt': FAKE_NOW}}}, {'$replaceRoot': {'newRoot': '$entity'}}, {
                '$lookup': {
                    'from': 'haystack',
                    'as': 'siteRef_entity_',
                    'let': {'siteRef_id_': '$siteRef'},
                    'pipeline': [{
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {
                                        '$eq': [
                                            '$customer_id',
                                            'customer']},
                                    {
                                        '$lte': [
                                            '$start_datetime',
                                            FAKE_NOW]}, {
                                        '$gt': ['$end_datetime', FAKE_NOW]}, {
                                        '$eq': ['$entity.id', '$$siteRef_id_']}]}}}]}}, {'$set': {
               'siteRef_entity_': {'$arrayElemAt': ['$siteRef_entity_.entity', 0]}}},
            {
                '$lookup': {
                    'from': 'haystack', 'as': 'siteRef_entity_',
                    'let': {'siteRef_id_': '$siteRef'},
                    'pipeline': [{'$match': {'$expr': {'$and': [
                        {'$eq': ['$customer_id', 'customer']}, {
                            '$lte': ['$start_datetime',
                                     FAKE_NOW]}, {
                            '$gt': ['$end_datetime', FAKE_NOW]}, {
                            '$eq': ['$entity.id', '$$siteRef_id_']}]}}}]}},
            {'$set': {
                'siteRef_entity_': {'$arrayElemAt': ['$siteRef_entity_.entity', 0]}}},
            {'$match': {'$expr': {
                '$or': [{'$ne': [{'$type': '$siteRef_entity_.geoPostalCode'}, 'missing']},
                        {'$ne': [{'$type': '$siteRef_entity_.geoCountry'}, 'missing']}]}}},
            {
                '$replaceRoot': {'newRoot': '$$ROOT'}},
            {'$limit': 10}]


# noinspection PyPep8,PyPep8,PyPep8
def test_and_or_path():
    hs_filter = '(a->b or c->d) and (e->f or g->h)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    # noinspection PyPep8
    assert mongo_request == \
           [
               {'$match': {
                   'customer_id': 'customer',
                   'start_datetime': {
                       '$lte': FAKE_NOW},
                   'end_datetime': {
                       '$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {
                   '$lookup': {'from': 'haystack', 'as': 'a_entity_', 'let': {'a_id_': '$a'},
                               'pipeline': [{'$match': {'$expr': {
                                   '$and': [{'$eq': ['$customer_id', 'customer']},
                                            {'$lte': ['$start_datetime', FAKE_NOW]},
                                            {
                                                '$gt': ['$end_datetime', FAKE_NOW]},
                                            {
                                                '$eq': ['$entity.id', '$$a_id_']}]}}}]}},
               {'$set': {'a_entity_': {'$arrayElemAt': ['$a_entity_.entity', 0]}}},
               {
                   '$lookup': {'from': 'haystack', 'as': 'c_entity_', 'let': {'c_id_': '$c'},
                               'pipeline': [{'$match': {'$expr': {
                                   '$and': [{'$eq': ['$customer_id', 'customer']},
                                            {'$lte': ['$start_datetime', FAKE_NOW]}, {
                                                '$gt': ['$end_datetime', FAKE_NOW]},
                                            {
                                                '$eq': ['$entity.id', '$$c_id_']}]}}}]}},
               {'$set': {'c_entity_': {'$arrayElemAt': ['$c_entity_.entity', 0]}}},
               {
                   '$lookup': {'from': 'haystack', 'as': 'e_entity_', 'let': {'e_id_': '$e'}, 'pipeline': [
                       {'$match': {'$expr': {
                           '$and': [
                               {'$eq': ['$customer_id', 'customer']},
                               {'$lte': ['$start_datetime', FAKE_NOW]},
                               {
                                   '$gt': ['$end_datetime', FAKE_NOW]},
                               {
                                   '$eq': ['$entity.id', '$$e_id_']}]}}}]}},
               {'$set': {'e_entity_': {'$arrayElemAt': ['$e_entity_.entity', 0]}}}, {
               '$lookup': {
                   'from': 'haystack',
                   'as': 'g_entity_',
                   'let': {'g_id_': '$g'},
                   'pipeline': [{'$match': {'$expr': {
                       '$and': [{'$eq': ['$customer_id', 'customer']},
                                {'$lte': ['$start_datetime', FAKE_NOW]},
                                {
                                    '$gt': ['$end_datetime', FAKE_NOW]}, {
                                    '$eq': ['$entity.id', '$$g_id_']}]}}}]}},
               {'$set': {'g_entity_': {'$arrayElemAt': ['$g_entity_.entity', 0]}}}, {
               '$match': {'$expr': {'$and': [
                   {'$or': [{'$ne': [{'$type': '$a_entity_.b'}, 'missing']},
                            {'$ne': [{'$type': '$c_entity_.d'}, 'missing']}]},
                   {'$or': [{'$ne': [{'$type': '$e_entity_.f'}, 'missing']},
                            {'$ne': [{'$type': '$g_entity_.h'}, 'missing']}]}]}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {
                   '$limit': 10}]


def test_complex():
    hs_filter = '(a->b or c->d) and e or (f and g->h)'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {
               'customer_id': 'customer',
               'start_datetime': {'$lte': FAKE_NOW},
               'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'a_entity_',
                   'let': {'a_id_': '$a'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$a_id_']}]}}}]}},
               {'$set': {'a_entity_': {'$arrayElemAt': ['$a_entity_.entity', 0]}}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'c_entity_',
                   'let': {'c_id_': '$c'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$c_id_']}]}}}]}},
               {'$set': {'c_entity_': {'$arrayElemAt': ['$c_entity_.entity', 0]}}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'g_entity_',
                   'let': {'g_id_': '$g'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$g_id_']}]}}}]}},
               {'$set': {'g_entity_': {'$arrayElemAt': ['$g_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$or': [
                   {'$and': [{'$or': [
                       {'$ne': [{'$type': '$a_entity_.b'}, 'missing']},
                       {'$ne': [{'$type': '$c_entity_.d'}, 'missing']}]},
                       {'$ne': [{'$type': '$e'}, 'missing']}]},
                   {'$and': [
                       {'$ne': [{'$type': '$f'}, 'missing']},
                       {'$ne': [{'$type': '$g_entity_.h'}, 'missing']}]}]}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


def test_path_equal_quantity():
    hs_filter = 'siteRef->curVal == 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {
               'customer_id': 'customer',
               'start_datetime': {'$lte': FAKE_NOW},
               'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'siteRef_entity_',
                   'let': {'siteRef_id_': '$siteRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$siteRef_id_']}]}}}]}},
               {'$set': {'siteRef_entity_': {'$arrayElemAt': ['$siteRef_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$eq': ['$siteRef_entity_.curVal', 'n:55400.000000 \\u00b0']}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


# noinspection PyPep8
def test_2path_greater_quantity():
    hs_filter = 'siteRef->temp >= 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {
               'customer_id': 'customer',
               'start_datetime': {'$lte': FAKE_NOW},
               'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'siteRef_entity_',
                   'let': {'siteRef_id_': '$siteRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$siteRef_id_']}]}}}]}},
               {'$set': {'siteRef_entity_': {'$arrayElemAt': ['$siteRef_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$gte': [
                   {'$let': {'vars': {'siteRef_regex_': {
                       '$regexFind': {'input': '$siteRef_entity_.temp',
                                      'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                       'in': {'$toDouble': {'$arrayElemAt': ['$$siteRef_regex_.captures', 0]}}}}, 55400.0]}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


def test_3path_greater_quantity():
    hs_filter = 'siteRef->ownerRef->temp >= 55400°'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {
               'customer_id': 'customer',
               'start_datetime': {'$lte': FAKE_NOW},
               'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'siteRef_entity_',
                   'let': {'siteRef_id_': '$siteRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$siteRef_id_']}]}}}]}},
               {'$set': {'siteRef_entity_': {'$arrayElemAt': ['$siteRef_entity_.entity', 0]}}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'siteRef_entity_.ownerRef_entity_',
                   'let': {'ownerRef_id_': '$siteRef_entity_.ownerRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$ownerRef_id_']}]}}}]}},
               {'$set': {'siteRef_entity_.ownerRef_entity_': {
                   '$arrayElemAt': ['$siteRef_entity_.ownerRef_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$gte': [
                   {'$let': {'vars': {'siteRef_regex_': {
                       '$regexFind': {
                           'input': '$siteRef_entity_.ownerRef_entity_.temp',
                           'regex': 'n:([-+]?([0-9]*[.])?[0-9]+([eE][-+]?\\d+)?)'}}},
                       'in': {'$toDouble': {'$arrayElemAt': ['$$siteRef_regex_.captures', 0]}}}}, 55400.0]}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]


# noinspection PyPep8
def test_4path():
    hs_filter = 'equipRef->siteRef->a->b'
    mongo_request = mongo_filter(hs_filter, FAKE_NOW, 10, "customer")
    _check_mongodb(hs_filter, mongo_request)
    assert mongo_request == \
           [{'$match': {
               'customer_id': 'customer',
               'start_datetime': {'$lte': FAKE_NOW},
               'end_datetime': {'$gt': FAKE_NOW}}},
               {'$replaceRoot': {'newRoot': '$entity'}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'equipRef_entity_',
                   'let': {'equipRef_id_': '$equipRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$equipRef_id_']}]}}}]}},
               {'$set': {'equipRef_entity_': {'$arrayElemAt': ['$equipRef_entity_.entity', 0]}}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'equipRef_entity_.siteRef_entity_',
                   'let': {'siteRef_id_': '$equipRef_entity_.siteRef'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$siteRef_id_']}]}}}]}},
               {'$set': {'equipRef_entity_.siteRef_entity_': {
                   '$arrayElemAt': ['$equipRef_entity_.siteRef_entity_.entity', 0]}}},
               {'$lookup': {
                   'from': 'haystack',
                   'as': 'equipRef_entity_.siteRef_entity_.a_entity_',
                   'let': {'a_id_': '$equipRef_entity_.siteRef_entity_.a'},
                   'pipeline': [{'$match': {'$expr': {'$and': [
                       {'$eq': ['$customer_id', 'customer']},
                       {'$lte': ['$start_datetime', FAKE_NOW]},
                       {'$gt': ['$end_datetime', FAKE_NOW]},
                       {'$eq': ['$entity.id', '$$a_id_']}]}}}]}},
               {'$set': {'equipRef_entity_.siteRef_entity_.a_entity_':
                             {'$arrayElemAt': ['$equipRef_entity_.siteRef_entity_.a_entity_.entity', 0]}}},
               {'$match': {'$expr': {'$ne': [{'$type': '$equipRef_entity_.siteRef_entity_.a_entity_.b'}, 'missing']}}},
               {'$replaceRoot': {'newRoot': '$$ROOT'}},
               {'$limit': 10}]
