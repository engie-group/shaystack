# (C) 2020 Philippe PRADOS
# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
import datetime
import gc
from datetime import time, date, datetime

from iso8601 import iso8601

from hszinc import Grid, Uri, Ref, Coordinate, MARKER, XStr
from hszinc.filter_ast import FilterUnary, FilterBinary, FilterPath, FilterAST
from hszinc.grid_filter import hs_filter, _FnWrapper, filter_function
from hszinc.zoneinfo import timezone


def test_filter_ast():
    assert repr(FilterAST(None)) == 'AST:None'


def test_filter_tag_only():
    result = hs_filter.parseString('geo', parseAll=True)[0]
    assert isinstance(result, FilterUnary)
    assert result.op == "has"


def test_filter_tag_equal_values():
    result = hs_filter.parseString('bool == true', parseAll=True)[0]  # Zinc use TF
    assert isinstance(result.right, bool)
    assert result.right is True

    result = hs_filter.parseString('number == 1', parseAll=True)[0]
    assert isinstance(result.right, float)
    assert result.right == 1.0

    result = hs_filter.parseString('number == 1.0', parseAll=True)[0]
    assert isinstance(result.right, float)
    assert result.right == 1.0

    result = hs_filter.parseString('str == "str"', parseAll=True)[0]
    assert isinstance(result.right, str)
    assert result.right == "str"

    result = hs_filter.parseString('uri == `uri`', parseAll=True)[0]
    assert isinstance(result.right, Uri)
    assert result.right == Uri("uri")

    result = hs_filter.parseString('date == 1977-04-22', parseAll=True)[0]
    assert isinstance(result.right, date)
    assert result.right == date(1977, 4, 22)

    result = hs_filter.parseString('time == 11:11:11', parseAll=True)[0]
    assert isinstance(result.right, time)
    assert result.right == time(11, 11, 11)

    result = hs_filter.parseString('date_time == 1977-04-22T01:00:00-05:00', parseAll=True)[0]
    assert isinstance(result.right, datetime)
    assert result.right == iso8601.parse_date("1977-04-22T01:00:00-05:00")

    result = hs_filter.parseString('date_time == 1977-04-22T01:00:00 GMT+1', parseAll=True)[0]
    assert isinstance(result.right, datetime)
    assert result.right == iso8601.parse_date("1977-04-22T01:00:00").astimezone(timezone("GMT+1"))

    result = hs_filter.parseString('date_time == 1977-04-22T01:00:00 Paris', parseAll=True)[0]
    assert isinstance(result.right, datetime)
    assert result.right == iso8601.parse_date("1977-04-22T01:00:00").astimezone(timezone("Paris"))

    # --- Extended syntax (types not in specification)
    result = hs_filter.parseString('ref == @abc', parseAll=True)[0]
    assert isinstance(result.right, Ref)
    assert result.right == Ref("abc")

    result = hs_filter.parseString('geo == @abc "a"', parseAll=True)[0]
    assert isinstance(result.right, Ref)
    assert result.right == Ref("abc", "a")

    result = hs_filter.parseString('ref == C(1.0,-1.0)', parseAll=True)[0]
    assert isinstance(result.right, Coordinate)
    assert result.right == Coordinate(1.0, -1.0)

    result = hs_filter.parseString('list == [ 1, 2 ]', parseAll=True)[0]
    assert isinstance(result.right, list)
    assert result.right == [1, 2]

    result = hs_filter.parseString('dict == { a b:2 }', parseAll=True)[0]
    assert isinstance(result.right, dict)
    assert result.right == {"a": MARKER, "b": 2.0}

    result = hs_filter.parseString('map == hex("010203")', parseAll=True)[0]
    assert isinstance(result.right, XStr)
    assert result.right == XStr("hex", "010203")


def test_filter_tag_comparaison_operator():
    result = hs_filter.parseString('bool == true', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == '=='

    result = hs_filter.parseString('bool <= true', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == '<='

    result = hs_filter.parseString('bool >= true', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == '>='

    result = hs_filter.parseString('bool != true', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == '!='

    result = hs_filter.parseString('bool < true', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == '<'

    result = hs_filter.parseString('bool > true', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == '>'


def test_filter_navigation():
    result = hs_filter.parseString('a->b', parseAll=True)[0]
    assert isinstance(result, FilterUnary)
    assert isinstance(result.right, FilterPath)
    assert result.right.path == ['a', 'b']

    result = hs_filter.parseString('a->b->c', parseAll=True)[0]
    assert isinstance(result, FilterUnary)
    assert isinstance(result.right, FilterPath)
    assert result.right.path == ['a', 'b', 'c']


def test_filter_boolean_operator():
    result = hs_filter.parseString('bool and bool', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == "and"

    result = hs_filter.parseString('bool==true and bool!=false', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == "and"
    assert result.left.op == "=="
    assert result.right.op == "!="

    result = hs_filter.parseString('bool>=true or bool<=false', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == "or"
    assert result.left.op == ">="
    assert result.right.op == "<="

    result = hs_filter.parseString('(bool<true or bool>false) and not bool', parseAll=True)[0]
    assert isinstance(result, FilterBinary)
    assert result.op == "and"
    assert isinstance(result.left, FilterBinary)
    assert result.left.op == "or"
    assert isinstance(result.right, FilterUnary)
    assert result.right.op == 'not'

    result = hs_filter.parseString('equip and siteRef->geoCity == "Chicago"', parseAll=True)[0]
    repr(result)
    assert isinstance(result, FilterBinary)
    assert result.op == "and"
    assert isinstance(result.left, FilterUnary)
    assert result.left.op == "has"
    assert isinstance(result.right, FilterBinary)
    assert result.right.op == "=="
    assert result.right.left.path == ["siteRef", "geoCity"]


def test_generated_filter():
    assert filter_function('equip == "Chicago"')(None, {"equip": "Chicago"})
    assert filter_function('equip == "Chicago" or not titi')(None, {"equip": "Chicago"})
    assert filter_function('equip == "Chicago" or not titi')(None, {"equip": "NewYork"})
    assert not filter_function('equip == "Chicago" or not titi')(None, {"titi": MARKER})


def test_generated_filter_with_reference():
    grid = Grid(columns={'id': {}})
    grid.insert(0, {'id': 'id1'})
    assert filter_function('ref == @id1')(None, {"ref": Ref("id1")})


def test_grid_filter():
    grid = Grid(columns={'id': {}, 'site': {}, 'equip':{},'geoPostalCode':{},'ahu':{},
                         'geoCity':{},'curVal':{},'hvac':{},'siteRef':{}})
    grid.append({'id': 'id1', 'site': MARKER, 'equip': 'Chicago', 'geoPostalCode': "78280", 'ahu': MARKER,
                 'geoCity': 'Chicago', 'curVal': 76})
    grid.append({'id': 'id2', 'hvac': MARKER, 'geoPostalCode': "23220", 'curVal': 75})
    grid.append({'equip': 'Chicago', 'hvac': MARKER, 'siteRef': Ref('id1'), 'curVal': 74})
    result = grid.filter('site')
    assert len(result) == 1
    assert result['id1']

    result = grid.filter('equip == "Chicago"')
    assert len(result) == 2
    assert result[0]['id'] == 'id1'
    assert result[1]['equip'] == 'Chicago'

    result = grid.filter('not id')
    assert len(result) == 1
    assert result[0]['equip'] == 'Chicago'


def test_grid_specification_filter_sample():
    grid = Grid(columns={'id': {}, 'site': {}, 'equip':{},'geoPostalCode':{},'ahu':{},
                         'geoCity':{},'curVal':{},'hvac':{},'siteRef':{}})
    grid.append({'id': 'id1', 'site': MARKER, 'equip': 'Chicago', 'geoPostalCode': "78280", 'ahu': MARKER,
                 'geoCity': 'Chicago', 'curVal': 76})
    grid.append({'id': 'id2', 'hvac': MARKER, 'geoPostalCode': "23220", 'curVal': 75})
    grid.append({'equip': 'Chicago', 'hvac': MARKER, 'siteRef': Ref('id1'), 'curVal': 74})

    # specification samples
    result = grid.filter('geoPostalCode == "23220"')
    assert len(result) == 1
    assert result[0]['id'] == 'id2'

    result = grid.filter('geoPostalCode != "23220"')
    assert len(result) == 1
    assert result[0]['id'] == 'id1'

    result = grid.filter('curVal < 75')
    assert len(result) == 1
    assert result[0]['siteRef'] == Ref('id1')

    result = grid.filter('curVal <= 75')
    assert len(result) == 2
    assert result[0]['id'] == 'id2'
    assert result[1]['siteRef'] == Ref('id1')

    result = grid.filter('curVal > 75')
    assert len(result) == 1
    assert result[0]['id'] == 'id1'

    result = grid.filter('curVal >= 75')
    assert len(result) == 2
    assert result[0]['id'] == 'id1'
    assert result[1]['id'] == 'id2'

    result = grid.filter('site or equip')
    assert len(result) == 2
    assert result[0]['id'] == 'id1'
    assert result[1]['siteRef'] == Ref('id1')

    result = grid.filter('equip and hvac')
    assert len(result) == 1
    assert result[0]['siteRef'] == Ref('id1')

    result = grid.filter('equip and not ahu')
    assert len(result) == 1
    assert result[0]['siteRef'] == Ref('id1')

    result = grid.filter('equip and siteRef->geoCity == "Chicago"')
    assert len(result) == 1
    assert result[0]['equip'] == 'Chicago'


def test_if_generated_function_removed():
    # Check if the generated function will be removed
    import hszinc.grid_filter
    wrapper = _FnWrapper("_acme", "def _acme(): pass")
    assert hszinc.grid_filter._acme
    del wrapper
    gc.collect()
    try:
        hszinc.grid_filter._acme
        assert False
    except AttributeError:
        pass


def test_slide_get():
    grid = Grid(columns={'id': {}, 'site': {}, 'equip':{},'geoPostalCode':{},'ahu':{},
                         'geoCity':{},'curVal':{},'hvac':{},'siteRef':{}})
    grid.append({'id': 'id1', 'site': MARKER, 'equip': 'Chicago', 'geoPostalCode': "78280", 'ahu': MARKER,
                 'geoCity': 'Chicago', 'curVal': 76})
    grid.append({'id': 'id2', 'hvac': MARKER, 'geoPostalCode': "23220", 'curVal': 75})
    grid.append({'equip': 'Chicago', 'hvac': MARKER, 'siteRef': Ref('id1'), 'curVal': 74})
    assert len(grid[0:1]) == 1
    assert len(grid[1:]) == 2
    assert len(grid[:]) == 3


def test_empty_filter():
    grid = Grid(columns={'id': {}, 'site': {}, 'equip':{},'geoPostalCode':{},'ahu':{},
                         'geoCity':{},'curVal':{},'hvac':{},'siteRef':{}})
    grid.append({'id': 'id1', 'site': MARKER, 'equip': 'Chicago', 'geoPostalCode': "78280", 'ahu': MARKER,
                 'geoCity': 'Chicago', 'curVal': 76})
    grid.append({'id': 'id2', 'hvac': MARKER, 'geoPostalCode': "23220", 'curVal': 75})
    grid.append({'equip': 'Chicago', 'hvac': MARKER, 'siteRef': Ref('id1'), 'curVal': 74})
    assert len(grid.filter('')) == 3


def test_empty_filter_and_limit():
    grid = Grid(columns={'id': {}, 'site': {}})
    grid.append({'id': 'id1', 'site': MARKER, 'equip': 'Chicago', 'geoPostalCode': "78280", 'ahu': MARKER,
                 'geoCity': 'Chicago', 'curVal': 76})
    grid.append({'id': 'id2', 'hvac': MARKER, 'geoPostalCode': "23220", 'curVal': 75})
    grid.append({'equip': 'Chicago', 'hvac': MARKER, 'siteRef': Ref('id1'), 'curVal': 74})
    assert len(grid.filter('', limit=1)) == 1
    assert len(grid.filter('', limit=2)) == 2


def test_filter_and_limit():
    grid = Grid(columns={'id': {}, 'site': {}})
    grid.append({'id': 'id1', 'site': MARKER, 'equip': 'Chicago', 'geoPostalCode': "78280", 'ahu': MARKER,
                 'geoCity': 'Chicago', 'curVal': 76})
    grid.append({'id': 'id2', 'hvac': MARKER, 'geoPostalCode': "23220", 'curVal': 75})
    grid.append({'equip': 'Chicago', 'hvac': MARKER, 'siteRef': Ref('id1'), 'curVal': 74})

    assert len(grid.filter('not acme', limit=1)) == 1
