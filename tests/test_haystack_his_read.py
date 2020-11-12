from datetime import datetime, date, timedelta

import pytz
from mock import patch

import haystackapi
import hszinc
from haystackapi import Ref
from haystackapi.ops import HaystackHttpRequest, DEFAULT_MIME_TYPE
from haystackapi.providers import ping


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch('haystackapi.providers.haystack_interface.no_cache')
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_zinc(mock, no_cache) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    no_cache.return_value = True
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns={'id': {}})
    grid.append({"id": Ref("1234")})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), None, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_args(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = DEFAULT_MIME_TYPE
    request = HaystackHttpRequest()
    request.args['id'] = str(Ref("1234"))

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), None, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_today(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', 'range'])
    grid.append({"id": Ref("1234"), "range": "today"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), (date.today(),), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_yesterday(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', 'range'])
    grid.append({"id": Ref("1234"), "range": "yesterday"})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), (date.today() - timedelta(days=1),), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_two_datetime(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', 'range'])
    datetime_1 = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    datetime_2 = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    grid.append({"id": Ref("1234"), "range": datetime_1.isoformat() + ',' + datetime_2.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), (datetime_1, datetime_2), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_one_datetime(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', 'range'])
    datetime_1 = datetime(2020, 1, 1, 0, 0, 0, tzinfo=pytz.UTC)
    grid.append({"id": Ref("1234"), "range": datetime_1.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), (datetime_1, None), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_two_date(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', 'range'])
    date_1 = date(2020, 1, 1)
    date_2 = date(2020, 1, 1)
    grid.append({"id": Ref("1234"), "range": date_1.isoformat() + ',' + date_2.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), (date_1, date_2), None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None


@patch.dict('os.environ', {'HAYSTACK_PROVIDER': 'haystackapi.providers.ping'})
@patch.object(ping.Provider, 'his_read')
def test_his_read_with_range_one_date(mock) -> None:
    # GIVEN
    mock.return_value = ping.PingGrid
    mime_type = hszinc.MODE_ZINC
    request = HaystackHttpRequest()
    grid = hszinc.Grid(columns=['id', 'range'])
    date_1 = date(2020, 1, 1)
    grid.append({"id": Ref("1234"), "range": date_1.isoformat()})
    request.headers["Content-Type"] = mime_type
    request.headers["Accept"] = mime_type
    request.body = hszinc.dump(grid, mode=mime_type)

    # WHEN
    response = haystackapi.his_read(request, "dev")

    # THEN
    mock.assert_called_once_with(Ref("1234"), date_1, None)
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith(mime_type)
    assert hszinc.parse(response.body, mime_type) is not None
