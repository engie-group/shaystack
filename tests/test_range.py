from datetime import datetime, date, timedelta

import pytz

from haystackapi import parse_date_range


def test_date_range_empty():
    date_min, date_max = parse_date_range("", pytz.UTC)
    assert date_min == datetime.min.replace(tzinfo=pytz.UTC)
    assert date_max == datetime.max.replace(tzinfo=pytz.UTC)


def test_date_range_today():
    date_min, date_max = parse_date_range("today", pytz.UTC)
    assert date_min == datetime.combine(date.today(), datetime.min.time()) \
        .replace(tzinfo=pytz.UTC)
    assert date_max == date_min + timedelta(days=1, milliseconds=-1)


def test_date_range_yesterday():
    date_min, date_max = parse_date_range("yesterday", pytz.UTC)
    assert date_min == datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
        .replace(tzinfo=pytz.UTC)
    assert date_max == date_min + timedelta(days=1, milliseconds=-1)


def test_date_range_date():
    date_min, date_max = parse_date_range("2020-12-24", pytz.UTC)
    assert date_min == datetime(2020, 12, 24).replace(tzinfo=pytz.UTC)
    assert date_max == date_min + timedelta(days=1, milliseconds=-1)


def test_date_range_date_date():
    date_min, date_max = parse_date_range("2020-12-24,2020-12-25", pytz.UTC)
    assert date_min == datetime(2020, 12, 24).replace(tzinfo=pytz.UTC)
    assert date_max == datetime(2020, 12, 25).replace(tzinfo=pytz.UTC)


def test_date_range_datetime():
    date_min, date_max = parse_date_range("2020-12-24T00:00:00+00:00", pytz.UTC)
    assert date_min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert date_max == date_min + timedelta(days=1, milliseconds=-1)


def test_date_range_datetime_datetime():
    date_min, date_max = parse_date_range("2020-12-24T00:00:00+00:00,2020-12-25T00:00:00+00:00", pytz.UTC)
    assert date_min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert date_max == datetime(2020, 12, 25, tzinfo=pytz.UTC)
