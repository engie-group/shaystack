from datetime import datetime, date, timedelta

import pytz

from haystackapi import parse_date_range


def test_date_range_empty():
    min, max = parse_date_range("", pytz.UTC)
    assert min == datetime.min.replace(tzinfo=pytz.UTC)
    assert max == datetime.max.replace(tzinfo=pytz.UTC)


def test_date_range_today():
    min, max = parse_date_range("today", pytz.UTC)
    assert min == datetime.combine(date.today(), datetime.min.time()) \
        .replace(tzinfo=pytz.UTC)
    assert max == min + timedelta(days=1, milliseconds=-1)


def test_date_range_yesterday():
    min, max = parse_date_range("yesterday", pytz.UTC)
    assert min == datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
        .replace(tzinfo=pytz.UTC)
    assert max == min + timedelta(days=1, milliseconds=-1)


def test_date_range_date():
    min, max = parse_date_range("2020-12-24", pytz.UTC)
    assert min == datetime(2020, 12, 24).replace(tzinfo=pytz.UTC)
    assert max == min + timedelta(days=1, milliseconds=-1)


def test_date_range_date_date():
    min, max = parse_date_range("2020-12-24,2020-12-25", pytz.UTC)
    assert min == datetime(2020, 12, 24).replace(tzinfo=pytz.UTC)
    assert max == datetime(2020, 12, 25).replace(tzinfo=pytz.UTC)


def test_date_range_datetime():
    min, max = parse_date_range("2020-12-24T00:00:00+00:00", pytz.UTC)
    assert min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert max == min + timedelta(days=1, milliseconds=-1)


def test_date_range_datetime_datetime():
    min, max = parse_date_range("2020-12-24T00:00:00+00:00,2020-12-25T00:00:00+00:00", pytz.UTC)
    assert min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert max == datetime(2020, 12, 25, tzinfo=pytz.UTC)
