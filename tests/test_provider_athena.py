import csv
from datetime import datetime
from typing import cast
from unittest.mock import patch

import pytz
import pytest


from shaystack.grid import Grid
from shaystack.providers import get_provider
from shaystack.providers.athena import Provider as DBTSProvider

ENVIRON = {
    "HAYSTACK_PROVIDER": "shaystack.providers.athena",
    "HAYSTACK_DB": "s3://s3_input_bucket_name/ontology.hayson.json",
    "HAYSTACK_TS": "athena://shaystack?output_bucket_name=s3_output_bucket_name"
                   "&output_folder_name=athena_output_folder_name",
    "AWS_PROFILE": "fake_profile",
    "AWS_REGION": "eu-west-1",
    "FLASK_DEBUG": 1,
    "HAYSTACK_UI": "yes",
    "REFRESH": 1
}

ENTITY00 = {
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

ENTITY01 = {
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
        "partition_keys": "part_key_1='pk1'/part_key_2='pk2'",  # Only 2 partition keys
        "hs_type": "float",
        "hs_value_column": {
            "value": "float",
        },
        "hs_date_column": {
            "time": "%Y-%m-%d %H:%M:%S.%f"
        },
        "date_part_keys": {
            "year_col": "year",
            "month_col": "month",  # There is no 'day' partition key
        }
    },
    "point": {
        "_kind": "Marker"
    },
    "his": {
        "_kind": "Marker"
    },
}

TS_CSV_FILE = [
    '"time","value"\n',
    '"2021-05-03 09:59:00.000","0.04353"\n',
    '"2021-05-03 14:02:00.000","0.8818"\n',
    '"2021-05-03 15:12:00.000","0.67444"\n',
    '"2021-05-03 16:16:00.000","0.47537"\n',
    '"2021-05-03 06:54:00.000","-0.01311"\n',
    '"2021-05-03 08:18:00.000","0.04903"\n',
    '"2021-05-03 09:12:00.000","0.01854"\n',
    '"2021-05-03 10:05:00.000","-0.78323"\n',
    '"2021-05-03 11:51:00.000","1.3186"\n',
    '"2021-05-03 12:31:00.000","1.17972"\n',
    '"2021-05-03 13:51:00.000","0.85427"\n',
    '"2021-05-03 14:17:00.000","0.92032"\n'
]


def test_import_ts_in_db():
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        with pytest.raises(NotImplementedError):
            provider._import_ts_in_db()


def test_build_athena_prediction_query_of_entity_00():
    athena_query = "SELECT DISTINCT time, prediction, upper, lower FROM tast_table WHERE" \
                   " part_key_1='pk1' AND part_key_2='pk2' AND part_key_3='pk3' " \
                   "AND year in (2021) AND month in (5) AND day in (1, 2, 3, 4)" \
                   " AND time BETWEEN DATE('2021-05-01')  AND DATE('2021-05-04') ORDER BY time ASC;"

    date_range = (datetime(2021, 5, 1, 0, 0, tzinfo=pytz.UTC),
                  datetime(2021, 5, 4, 23, 59, 59, 999999, tzinfo=pytz.UTC))
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        assert athena_query == provider.build_athena_query(ENTITY00['hisURI'], date_range, None)


def test_build_athena_prediction_query_of_entity_01():
    athena_query = "SELECT DISTINCT time, value FROM tast_table WHERE " \
                   "part_key_1='pk1' AND part_key_2='pk2' " \
                   "AND year in (2021) AND month in (5) " \
                   "AND time BETWEEN DATE('2021-05-01')  AND DATE('2021-05-04') ORDER BY time ASC;"

    date_range = (datetime(2021, 5, 1, 0, 0, tzinfo=pytz.UTC),
                  datetime(2021, 5, 4, 23, 59, 59, 999999, tzinfo=pytz.UTC))
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        assert athena_query == provider.build_athena_query(ENTITY01['hisURI'], date_range, None)


def test_create_history_grid():
    initial_grid = Grid(columns=["ts", "val"])
    for row in csv.DictReader(TS_CSV_FILE):
        date_val = row['time']
        hs_values = {'value': row['value']}
        initial_grid.append({"ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                             "val": DBTSProvider._cast_timeserie_to_hs(str(list(hs_values.values())[0]),
                                                                       "float")})
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        created_grid = provider.create_history_grid(csv.DictReader(TS_CSV_FILE),
                                                    ENTITY01['hisURI'])
        assert initial_grid == created_grid


def test_create_history_empty_grid():
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        created_grid = provider.create_history_grid(None, ENTITY01['hisURI'])
        assert created_grid == Grid(columns=["ts", "val"])


def test_put_date_format():
    str_date = "2022/06/01"
    date_pattern = "%Y/%m/%d"
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        date_formated = provider.put_date_format(str_date, date_pattern)
        assert date_formated == "2022-06-01 00:00:00"


def test_put_date_format_value_error_exception():
    str_date = "2022/06/01"
    date_pattern = "%Y-%m-%d"
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        with pytest.raises(Exception):
            provider.put_date_format(str_date, date_pattern)


@patch('shaystack.providers.athena.Provider.poll_query_status')
def test_get_query_results_called_by_poll_query_status(mock_get_query_results):
    # Athena get_query_results response
    response = {
        'QueryExecutionId': '18b45861-36ee-4fc1-8639-2b4ebf424fa4',
        'Status': {'State': "SUCCEEDED"}
    }
    with cast(DBTSProvider, get_provider("shaystack.providers.athena", ENVIRON)) as provider:
        provider.poll_query_status(response)
        mock_get_query_results.assert_called_once()
