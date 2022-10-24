from datetime import datetime, date, timedelta

import pytz
from mock import patch
from tzlocal import get_localzone

import shaystack
from shaystack import Ref
from shaystack.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
from shaystack.providers import ping




@patch('shaystack.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_zinc(mock, no_cache) -> None:
    # GIVEN
    """
    Args:
        mock:
        no_cache:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    no_cache.return_value = True
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("1234"),
                                 (datetime.min.replace(tzinfo=pytz.UTC),
                                  datetime.max.replace(tzinfo=pytz.UTC)), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_args(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args['id'] = str(Ref("1234"))

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("1234"),
                                 (datetime.min.replace(tzinfo=pytz.UTC),
                                  datetime.max.replace(tzinfo=pytz.UTC)),
                                 None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_today(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', 'range'])
    grid.append({"id": Ref("1234"), "range": "today"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    today = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=get_localzone())
    mock.assert_called_once_with(Ref("1234"),
                                 (today,
                                  today + timedelta(days=1)
                                  ), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_yesterday(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', 'range'])
    grid.append({"id": Ref("1234"), "range": "yesterday"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    yesterday = datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
        .replace(tzinfo=get_localzone())
    mock.assert_called_once_with(Ref("1234"),
                                 (yesterday, yesterday + timedelta(days=1)), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_two_datetime(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', 'range'])
    datetime_1 = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    datetime_2 = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    grid.append({"id": Ref("1234"), "range": datetime_1.isoformat() + ',' + datetime_2.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("1234"), (datetime_1, datetime_2), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_one_datetime(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', 'range'])
    datetime_1 = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    grid.append({"id": Ref("1234"), "range": datetime_1.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    cur_datetime = datetime.combine(datetime_1, datetime.min.time()).replace(tzinfo=pytz.UTC)
    mock.assert_called_once_with(Ref("1234"),
                                 (cur_datetime,
                                  datetime.max.replace(tzinfo=pytz.UTC)
                                  ), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_two_date(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', 'range'])
    date_1 = date(2020, 1, 1)
    date_2 = date(2020, 1, 2)
    grid.append({"id": Ref("1234"), "range": date_1.isoformat() + ',' + date_2.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    mock.assert_called_once_with(Ref("1234"),
                                 (datetime(2020, 1, 1).replace(tzinfo=get_localzone()),
                                  datetime.combine(
                                      datetime(2020, 1, 2),
                                      datetime.max.time()).replace(tzinfo=get_localzone())
                                  ), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None


@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_one_date(mock) -> None:
    # GIVEN
    """
    Args:
        mock:
    """
    envs = {'HAYSTACK_PROVIDER': 'shaystack.providers.ping'}
    mock.return_value = ping._PingGrid
    mime_type = shaystack.MODE_ZINC
    request = HaystackHttpRequest()
    grid = shaystack.Grid(columns=['id', 'range'])
    date_1 = date(2020, 1, 1)
    grid.append({"id": Ref("1234"), "range": date_1.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = shaystack.dump(grid, mode=mime_type)

    # WHEN
    response = shaystack.his_read(envs, request, "dev", ping.Provider(envs))

    # THEN
    cur_datetime = datetime.combine(date_1, datetime.min.time()).replace(tzinfo=get_localzone())
    mock.assert_called_once_with(Ref("1234"),
                                 (cur_datetime,
                                  cur_datetime + timedelta(days=1)
                                  ), None)

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert shaystack.parse(response.body, mime_type) is not None
