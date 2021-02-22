# -*- coding: utf-8 -*-
# Time zone handling/parsing tests
# (C) 2018 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Assume unicode literals as per Python 3
from __future__ import unicode_literals

import datetime

import iso8601
import pytz

from shaystack import zoneinfo


def test_get_tz_map():
    # This should return a mapping of all possible timezone names.
    tz_map = zoneinfo._get_tz_map()
    assert isinstance(tz_map, dict)

    # There are some timezones that aren't supported in pytz but are present
    # in Project Haystack.  Since it's impossible to know which ones, let's
    # try some well-known ones.
    assert tz_map['Adelaide'] == 'Australia/Adelaide'
    assert tz_map['Detroit'] == 'America/Detroit'
    assert tz_map['GMT'] == 'Etc/GMT'
    for etc_tz in (('GMT',) +
                   tuple(['GMT-%d' % n for n in range(1, 13)]) +  # pylint: disable=consider-using-generator
                   tuple(['GMT+%d' % n for n in range(1, 13)])):  # pylint: disable=consider-using-generator
        assert tz_map[etc_tz] == 'Etc/%s' % etc_tz


def test_get_tz_rmap():
    # This should return a mapping of all possible timezone names.
    # The keys and values are swapped compared to _get_tz_map.
    tz_rmap = zoneinfo._get_tz_rmap()
    tz_map = zoneinfo._get_tz_map()

    for iana_tz, hs_tz in tz_rmap.items():
        assert tz_map[hs_tz] == iana_tz


def test_valid_timezone():
    assert zoneinfo.timezone('Brisbane') is pytz.timezone('Australia/Brisbane')


def test_invalid_timezone():
    try:
        zoneinfo.timezone('ThisDoesNotExist')
        assert False, 'Returned a value for invalid time zone'
    except ValueError:
        pass


def test_naive_datetime():
    try:
        zoneinfo.timezone_name(datetime.datetime.now())
        assert False, 'Returned a value for naive timestamp'
    except ValueError:
        pass


def test_iso8601_datetime():
    # We don't know which one it'll pick, so pick one.
    name = zoneinfo.timezone_name(
        iso8601.parse_date('2017-01-01T00:00+10:00'))
    assert name in {
        'Brisbane',
        'Chuuk',
        'DumontDUrville',
        'GMT-10',
        'Guam',
        'Lindeman',
        'Port_Moresby',
        'Saipan',
        'Ust-Nera',
        'Vladivostok'}


def test_oddball_iso8601_datetime():
    # We won't have a matching one for this.
    try:
        zoneinfo.timezone_name(
            iso8601.parse_date('2017-01-01T00:00+12:34'))
        assert False, 'Matched an oddball timezone'
    except ValueError:
        pass
