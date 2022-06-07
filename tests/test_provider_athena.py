import os
import csv
import pytz
import boto3
import pytest
from typing import cast
from datetime import datetime

from moto import mock_athena
from unittest.mock import patch
from botocore import exceptions
from moto.athena import athena_backends

from shaystack.grid import Grid
from shaystack.providers import get_provider
from shaystack.providers.athena import Provider as DBTSProvider


@pytest.fixture(scope="function", autouse=True)
def environ():
    env = {
        "HAYSTACK_PROVIDER": "shaystack.providers.athena",
        "HAYSTACK_DB": f"s3://s3_input_bucket_name/ontology.hayson.json",
        "HAYSTACK_TS": f"athena://shaystack?output_bucket_name=s3_output_bucket_name"
                       f"&output_folder_name=athena_output_folder_name",
        "AWS_PROFILE": "fake_profile",
        "AWS_REGION": "eu-west-1",
        "FLASK_DEBUG": 1,
        "HAYSTACK_UI": "yes",
        "REFRESH": 1,
        "CDH_PROJECT_ROLE_ARN": "arn:aws:iam::482508239569:role/cdh_ontologyathenaagatheacc_78690"
    }
    return env


@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture(scope="function", autouse=True)
def athena_client(environ):
    with mock_athena():
        athena_client = boto3.client("athena", region_name=environ["AWS_REGION"])
        yield athena_client


@pytest.fixture()
def entity_00():
    """Entity sample with composed time series (more than one value)"""
    return {
               "id": {
                   "_kind": "Ref",
                   "val": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
               },
               "rawId": "00000000-1111-2222-3333-444444444444",
               "sensorRef": {
                   "_kind": "Ref",
                   "val": "11111111-2222-3333-4444-555555555555"
               },
               "hisURI": {
                   "db_name": "test_data_base",
                   "table_name": "tast_table",
                   "partition_keys": "part_key_1='pk1'/part_key_2='pk2'/part_key_3='pk3'",
                   "hs_type": "dict",
                   "hs_value_column": {
                       "prediction": "float",
                       "upper": "float",
                       "lower": "float"
                   },
                   "hs_date_column": {
                       "time": "%Y-%m-%d %H:%M:%S.%f"
                   },
                   "date_part_keys": {
                       "year_col": "year",
                       "month_col": "month",
                       "day_col": "day"
                   }
               },
               "point": {
                   "_kind": "Marker"
               },
               "his": {
                   "_kind": "Marker"
               },
           }


@pytest.fixture()
def entity_01():
    """Entity sample with only one Timeseries value"""
    return {
               "id": {
                   "_kind": "Ref",
                   "val": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
               },
               "rawId": "00000000-1111-2222-3333-444444444444",
               "sensorRef": {
                   "_kind": "Ref",
                   "val": "11111111-2222-3333-4444-555555555555"
               },
               "hisURI": {
                   "db_name": "test_data_base",
                   "table_name": "tast_table",
                   "partition_keys": "part_key_1='pk1'/part_key_2='pk2'",    # Only 2 partition keys
                   "hs_type": "float",
                   "hs_value_column": {
                       "value": "float",
                   },
                   "hs_date_column": {
                       "time": "%Y-%m-%d %H:%M:%S.%f"
                   },
                   "date_part_keys": {
                       "year_col": "year",
                       "month_col": "month",   # There is no 'day' partition key
                   }
               },
               "point": {
                   "_kind": "Marker"
               },
               "his": {
                   "_kind": "Marker"
               },
           }


@pytest.fixture()
def time_series_csv_file_1():
    """CSV file containing time series data representing the results of a successful Athena query"""

    lines = ['"time","value"\n',
             '"2021-05-03 09:59:00.000","0.04353"\n', '"2021-05-03 14:02:00.000","0.8818"\n',
             '"2021-05-03 15:12:00.000","0.67444"\n', '"2021-05-03 16:16:00.000","0.47537"\n',
             '"2021-05-03 06:54:00.000","-0.01311"\n', '"2021-05-03 08:18:00.000","0.04903"\n',
             '"2021-05-03 09:12:00.000","0.01854"\n', '"2021-05-03 10:05:00.000","-0.78323"\n',
             '"2021-05-03 11:51:00.000","1.3186"\n', '"2021-05-03 12:31:00.000","1.17972"\n',
             '"2021-05-03 13:51:00.000","0.85427"\n', '"2021-05-03 14:17:00.000","0.92032"\n']

    return lines


@pytest.fixture()
def shaystack_grid_from_time_series_csv_file_1(time_series_csv_file_1):
    """Shaystack Grid object created from csv time series"""
    reader = csv.DictReader(time_series_csv_file_1)
    history = Grid(columns=["ts", "val"])
    for row in reader:
        date_val = row['time']
        hs_values = {'value': row['value']}
        history.append({"ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                        "val": DBTSProvider._cast_timeserie_to_hs(str(list(hs_values.values())[0]), "float")})
    return history


@pytest.fixture()
def shaystack_empty_grid():
    """Shaystack empty Grid object"""
    return Grid(columns=["ts", "val"])


def test_import_ts_in_db(environ):
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        with pytest.raises(NotImplementedError):
            assert provider._import_ts_in_db()


@patch('shaystack.providers.athena.Provider.get_query_results')
def test_get_query_results_called_by_poll_query_status(mock_get_query_execution, environ, athena_client):
    query = "SELECT stuff"
    location = "s3://bucket-name/prefix/"
    database = "database"
    # Start Query
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": location},
    )
    athena_backends['eu-west-1'].executions.get(response['QueryExecutionId']).status = "SUCCEEDED"

    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        provider.poll_query_status(response)
        mock_get_query_execution.assert_called_once()


def test_poll_query_status_raise_exception_when_querye_failed(environ, athena_client):
    query = "SELECT stuff"
    location = "s3://bucket-name/prefix/"
    database = "database"
    # Start Query
    response = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": location},
    )
    athena_backends['eu-west-1'].executions.get(response['QueryExecutionId']).status = "FAILED"
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        with pytest.raises(Exception):
            assert provider.poll_query_status(response)


def test_get_query_results_object_not_found(environ):
    fake_execution_id = '00000000-1111-2222-3333-444444444444'
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        with pytest.raises(exceptions.ClientError):
            assert provider.get_query_results(fake_execution_id)


def test_build_athena_prediction_query_of_entity_00(environ, entity_00):

    athena_query = "SELECT time, prediction, upper, lower FROM tast_table WHERE" \
                       " part_key_1='pk1' AND part_key_2='pk2' AND part_key_3='pk3' " \
                       "AND year in (2021) AND month in (5) AND day in (1, 2, 3, 4)" \
                       " AND time BETWEEN DATE('2021-05-01')  AND DATE('2021-05-04');"

    date_range = (datetime(2021, 5, 1, 0, 0, tzinfo=pytz.UTC),
                  datetime(2021, 5, 4, 23, 59, 59, 999999, tzinfo=pytz.UTC))
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        assert athena_query == provider.build_athena_query(entity_00['hisURI'], date_range, None)


def test_build_athena_prediction_query_of_entity_01(environ, entity_01):

    athena_query = "SELECT time, value FROM tast_table WHERE " \
                       "part_key_1='pk1' AND part_key_2='pk2' " \
                       "AND year in (2021) AND month in (5) " \
                       "AND time BETWEEN DATE('2021-05-01')  AND DATE('2021-05-04');"

    date_range = (datetime(2021, 5, 1, 0, 0, tzinfo=pytz.UTC),
                  datetime(2021, 5, 4, 23, 59, 59, 999999, tzinfo=pytz.UTC))
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        assert athena_query == provider.build_athena_query(entity_01['hisURI'], date_range, None)


def test_create_history_grid(environ, time_series_csv_file_1, entity_01, shaystack_grid_from_time_series_csv_file_1):
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        reader = csv.DictReader(time_series_csv_file_1)
        history = provider.create_history_grid(reader, entity_01['hisURI'])
        assert history == shaystack_grid_from_time_series_csv_file_1


def test_create_history_empty_grid(environ, shaystack_empty_grid, entity_01):
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        history = provider.create_history_grid(None, entity_01['hisURI'])
        assert history == shaystack_empty_grid


def test_put_date_format(environ):
    str_date = "2022/06/01"
    date_pattern = "%Y/%m/%d"
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        date_formated = provider.put_date_format(str_date, date_pattern)
        assert date_formated == "2022-06-01 00:00:00"


def test_put_date_format_value_error_exception(environ):
    str_date = "2022/06/01"
    date_pattern = "%Y-%m-%d"
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", environ)) as provider:
        with pytest.raises(ValueError):
            assert provider.put_date_format(str_date, date_pattern)
