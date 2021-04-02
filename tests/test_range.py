from datetime import datetime, date, timedelta

import pytz

from shaystack.providers.haystack_interface import parse_date_range, _DATETIME_MAX_TZ, _DATETIME_MIN_TZ

_TZ_PARIS = pytz.timezone("Europe/Paris")


def test_date_range_empty():
    date_min, date_max = parse_date_range("", _TZ_PARIS)
    assert date_min == datetime.min.replace(tzinfo=pytz.UTC)
    assert date_max == datetime.max.replace(tzinfo=pytz.UTC)


def test_date_range_today():
    date_min, date_max = parse_date_range("today", _TZ_PARIS)
    assert date_min == datetime.combine(date.today(), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS)
    assert date_max == date_min + timedelta(days=1)


def test_date_range_today_date():
    date_min, date_max = parse_date_range("today,2100-01-01", _TZ_PARIS)
    assert date_min == datetime.combine(date.today(), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS)
    assert date_max == datetime.combine(datetime(2100, 1, 1), datetime.min.time()).replace(tzinfo=_TZ_PARIS)


def test_date_range_date_today():
    date_min, date_max = parse_date_range("2021-01-01,today", _TZ_PARIS)
    assert date_min == datetime.combine(datetime(2021, 1, 1), datetime.min.time()).replace(tzinfo=_TZ_PARIS)
    assert date_max == datetime.combine(date.today(), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS) + timedelta(days=1)


def test_date_range_yesterday():
    date_min, date_max = parse_date_range("yesterday", _TZ_PARIS)
    assert date_min == datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS)
    assert date_max == date_min + timedelta(days=1)


def test_date_range_yesterday_date():
    date_min, date_max = parse_date_range("yesterday,2100-01-01", _TZ_PARIS)
    assert date_min == datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS)
    assert date_max == datetime.combine(date(2100, 1, 1), datetime.min.time()).replace(tzinfo=_TZ_PARIS)


def test_date_range_date_yesterday():
    date_min, date_max = parse_date_range("2021-01-01,yesterday", _TZ_PARIS)
    assert date_min == datetime.combine(date(2021, 1, 1), datetime.min.time()).replace(tzinfo=_TZ_PARIS)
    assert date_max == datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=_TZ_PARIS)


def test_date_range_yesterday_today():
    date_min, date_max = parse_date_range("yesterday,today", _TZ_PARIS)
    assert date_min == datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS)
    assert date_max == datetime.combine(date.today(), datetime.min.time()) \
        .replace(tzinfo=_TZ_PARIS) + timedelta(days=1)


def test_date_range_date():
    date_min, date_max = parse_date_range("2020-12-24", _TZ_PARIS)
    assert date_min == datetime(2020, 12, 24, tzinfo=_TZ_PARIS)
    assert date_max == datetime(2020, 12, 25, tzinfo=_TZ_PARIS)


def test_date_range_date_comma():
    date_min, date_max = parse_date_range("2020-12-24,", _TZ_PARIS)
    assert date_min == datetime(2020, 12, 24, tzinfo=_TZ_PARIS)
    assert date_max == _DATETIME_MAX_TZ


def test_date_range_comma_date():
    date_min, date_max = parse_date_range(",2100-12-24", _TZ_PARIS)
    assert date_min == _DATETIME_MIN_TZ
    assert date_max == datetime.combine(datetime(2100, 12, 24),
                                        datetime.max.time()).replace(tzinfo=_TZ_PARIS)


def test_date_range_date_date():
    date_min, date_max = parse_date_range("2020-12-24,2020-12-25", _TZ_PARIS)
    assert date_min == datetime(2020, 12, 24, tzinfo=_TZ_PARIS)
    assert date_max == datetime.combine(datetime(2020, 12, 25),
                                        datetime.max.time()).replace(tzinfo=_TZ_PARIS)


def test_date_range_datetime():
    date_min, date_max = parse_date_range("2020-12-24T00:00:00+00:00", _TZ_PARIS)
    assert date_min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert date_max == _DATETIME_MAX_TZ


def test_date_range_datetime_comma():
    date_min, date_max = parse_date_range("2020-12-24T00:00:00+00:00,", _TZ_PARIS)
    assert date_min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert date_max == _DATETIME_MAX_TZ


def test_date_range_comma_datetime():
    date_min, date_max = parse_date_range(",2100-12-24T00:00:00+00:00", _TZ_PARIS)
    assert date_min == _DATETIME_MIN_TZ
    assert date_max == datetime(2100, 12, 24, tzinfo=pytz.UTC)


def test_date_range_datetime_datetime():
    date_min, date_max = parse_date_range("2020-12-24T00:00:00+00:00,2020-12-25T00:00:00+00:00", _TZ_PARIS)
    assert date_min == datetime(2020, 12, 24, tzinfo=pytz.UTC)
    assert date_max == datetime(2020, 12, 25, tzinfo=pytz.UTC)


def test_date_range_date_limit():
    date_min, date_max = parse_date_range("0001-01-01,9999-12-31", _TZ_PARIS)
    assert date_min == _DATETIME_MIN_TZ
    assert date_max == _DATETIME_MAX_TZ
