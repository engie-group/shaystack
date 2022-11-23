# -*- coding: utf-8 -*-
# SQL + Athena provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Add the persistance of time-series with Athena database.

Set the HAYSTACK_TS with:
    "athena://shaystack?output_bucket_name=<S3 bucket name>&output_folder_name=<output folder>"
- output_bucket_name [REQUIRED]: The name of the bucket in which Athena will store the query results
- output_folder_name [REQUIRED]: The folder name in which Athena will store the query results
"""
import time as t
from csv import DictReader
from datetime import datetime, date, time
from typing import Optional, Tuple, Any, Dict, Union
from urllib.parse import parse_qs
from urllib.parse import urlparse

import boto3
import pytz
from botocore import exceptions
from overrides import overrides

from .db import Provider as DBProvider
from .db import log
from ..datatypes import Ref, MARKER, REMOVE, Coordinate, Quantity, NA, XStr
from ..grid import Grid
from ..period import Period


# noinspection PyUnusedLocal
class Provider(DBProvider):
    """
    Expose an Haystack data via the Haystack Rest API and SQL+TS databases
    """
    __slots__ = "_parsed_ts", "_ts_table_name", "_ts_database_name", "_boto", "_write_client", "_read_client"
    INTERMEDIATE_STATES = ('QUEUED', 'RUNNING',)
    FAILURE_STATES = ('FAILED', 'CANCELLED',)
    SUCCESS_STATES = ('SUCCEEDED',)

    @property
    def name(self) -> str:
        return "SQL+timeseries"

    def __init__(self, envs: Dict[str, str]):
        super().__init__(envs)
        log.info("Use %s", self._get_ts())
        self._parsed_ts = urlparse(self._get_ts())
        self._output_bucket_name = parse_qs(self._parsed_ts.query)['output_bucket_name'][0]
        self._output_folder_name = parse_qs(self._parsed_ts.query)['output_folder_name'][0]
        self._boto = None
        self._write_client = None
        self._read_client = None

    def _get_boto(self):
        if not self._boto:
            self._boto = boto3.session.Session()
        return self._boto

    def _get_ts(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return self._envs["HAYSTACK_TS"]

    def _get_read_client(self):
        # if not self._read_client:
        region = self._envs.get("AWS_REGION",
                                self._envs.get("AWS_DEFAULT_REGION"))
        session = self._get_boto()
        log.info("[BOTO SESSION]: session was created successfully! ")
        self._read_client = session.client('athena',
                                           region_name=region
                                           )
        log.info("[ATHENA BOTO]: was created successfully! " + str(self._read_client.meta))
        return self._read_client

    def _import_ts_in_db(self, **kwargs) -> None:
        raise NotImplementedError('Feature not implemented')

    @staticmethod
    def _cast_timeserie_to_hs(val: str,
                              python_type: str,
                              unit: Union[str, None] = None) -> Any:
        if val:
            if python_type == "str":
                return val
            if python_type == "float":
                return float(val)
            if python_type == "_PintQuantity":
                return Quantity(float(val), unit)
            if python_type == "Quantity":
                return Quantity(float(val), unit)
            if python_type == "bool":
                return val.lower() == 'true'
            if python_type == "int":
                return int(float(val))
            if python_type == "_MarkerType":
                return MARKER if val else None
            if python_type == "_RemoveType":
                return REMOVE if val else None
            if python_type == "_NAType":
                return NA if val else None
            if python_type == "Ref":
                return Ref(val)
            if python_type == "datetime":
                return datetime.fromtimestamp(int(val))
            if python_type == "date":
                return date.fromordinal(int(val))
            if python_type == "time":
                int_time = int(val)
                hour = ((int_time // 1000000) // 60) // 60
                minute = ((int_time // 1000000) // 60) % 60
                split = (int_time // 1000000) % 60
                mic = int_time % 1000000
                return time(hour, minute, split, mic)
            if python_type == "Coordinate":
                split = val.split(",")  # type: ignore
                return Coordinate(float(split[0]), float(split[1]))  # type: ignore
            if python_type == "XStr":
                split = val.split(",")  # type: ignore
                return XStr(*split)  # type: ignore
            if python_type == "NoneType":
                return None
            raise ValueError(f"Unknown type {python_type}")
        return None

    def get_query_results(self, query_execution_id: str) -> DictReader:
        """
        Download result file
        Args:
            query_execution_id (object): Str that represent the ExecutionId of athena query
        Output:
            CSV DictReader containing the query response
        """
        region = self._envs.get("AWS_REGION",
                                self._envs.get("AWS_DEFAULT_REGION"))
        reader = None
        try:
            resource = boto3.resource('s3', region)
            response = resource.Bucket(self._output_bucket_name).Object(
                key=f'{self._output_folder_name}/{query_execution_id}.csv').get()
            lines = response['Body'].read().decode('utf-8').splitlines(True)
            log.info("Query results CSV file contain [%s] row.", str(len(lines)))
            reader = DictReader(lines)
        except exceptions.ClientError as exc:
            if exc.response['Error']['Code'] == "404":
                print("The object does not exist.")
            raise
        return reader

    def check_query_status(self, query_execution_id: str) -> dict:
        """
        Fetch the status of submitted athena query. Returns None or one of valid query states.

        :param query_execution_id: Id of submitted athena query
        :type query_execution_id: str
        :return: dict E.g. {'State': 'SUCCEEDED'}
        """
        athena_client = self._get_read_client()
        query_status = {'State': None}
        try:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            query_status = response['QueryExecution']['Status']
        except exceptions.ClientError as ex:
            log.error('Exception while getting query state: %s', ex)
        return query_status

    def poll_query_status(self, query_execution_id: str) -> DictReader:
        """
        Get the status of the Athena request, i.e. "QUEUED", "RUNNING", "FAILED"
        or "CANCELLED", and get the results
        of successful requests

        Args:
            query_execution_id (str): unique Id of submitted athena query
        Output:
            CSV DictReader containing the query response
        """
        query_status = {'State': None}
        while query_status['State'] in self.INTERMEDIATE_STATES or query_status['State'] is None:

            query_status = self.check_query_status(query_execution_id)

            if query_status['State'] is None:
                log.info('Invalid query state. Retrying again')

            elif query_status['State'] in self.INTERMEDIATE_STATES:
                log.info('Query is still in an intermediate state - %s', query_status['State'])
            elif query_status['State'] in self.FAILURE_STATES:
                error_message = 'Athena query with executionId {} was {} '.format(
                    query_execution_id, query_status["State"])
                if "StateChangeReason" in query_status:
                    error_message = error_message + f'due to the following error:' \
                                                    f'{query_status["StateChangeReason"]}'
                raise Exception(error_message)
            else:
                log.info('Query execution completed. Final state is - %s', query_status['State'])
                break
            t.sleep(1)
        # getting the csv file that contain query results from s3 output bucket
        reader = self.get_query_results(query_execution_id)
        return reader

    @staticmethod
    def put_date_format(str_date: str, date_pattern: str) -> str:
        """
        Set the date to the correct date format specified in the "date_pattern" parameter

        Args:
            str_date (str): string date
            date_pattern (str): date pattern
        Output:
            STR date using Haystack date format
        """
        try:
            date_val = datetime.strptime(str_date, date_pattern)
        except ValueError as err:
            log.error("%s time data %s does not match format %s", err, str_date, date_pattern)
            raise
        return date_val.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def build_athena_query(his_uri: dict,
                           dates_range: tuple,
                           date_version: Union[datetime, None] = None) -> str:
        """
        Build up an Athena query based on the parameters that have been included in hisURI and apply
        filtering by a start date and an end date based on the date_range argument.
        Args:
             his_uri (dict): dict containing all the parameters needed to build the Athena query
             dates_range (tuple): (start_date, end_date) date range that represents the time period to query
             date_version (datetime): the date that represents the version of the ontology
        Output:
            STR Athena query (SELECT a, b from table ..)
        """
        hs_parts_keys = his_uri['partition_keys'].split("/")
        hs_date_column = list(his_uri["hs_date_column"].keys())[0]
        hs_value_column = list(his_uri["hs_value_column"].keys())
        hs_date_parts_keys = his_uri['date_part_keys']
        if not date_version:
            date_version = datetime.max.replace(tzinfo=pytz.UTC)

        date_range_period = Period(start=dates_range[0], end=dates_range[1])
        if dates_range and dates_range[1] > date_version:
            dates_range = list(dates_range)  # type: ignore
            dates_range[1] = date_version  # type: ignore

        select_all = f'SELECT DISTINCT {hs_date_column}, {", ".join(hs_value_column)}' \
                     f' FROM {his_uri["table_name"]}' \
                     f' WHERE {" ".join([str(item) + " AND" for item in hs_parts_keys[:-1]])}' \
                     f' {hs_parts_keys[-1]}'
        if dates_range:
            if hs_date_parts_keys.get('year_col'):
                select_all += f' AND {hs_date_parts_keys.get("year_col")} in' \
                              f' ({", ".join(map(str, date_range_period.years))})'
            if hs_date_parts_keys.get('month_col'):
                select_all += f' AND {hs_date_parts_keys.get("month_col")} in' \
                              f' ({", ".join(map(str, date_range_period.months))})'
            if hs_date_parts_keys.get('day_col'):
                select_all += f' AND {hs_date_parts_keys.get("day_col")} in' \
                              f' ({", ".join(map(str, date_range_period.days))})'

            select_all += f' AND time BETWEEN DATE(\'{dates_range[0].strftime("%Y-%m-%d")}\') ' \
                          f' AND DATE(\'{dates_range[1].strftime("%Y-%m-%d")}\') ORDER BY time ASC;'
        return select_all

    def create_history_grid(self, reader: DictReader, his_uri: dict) -> Grid:
        """
        Create a Grid and fill it with the data from the query result rows that were stored as a csv
        file in the s3 bucket.
        Args:
            reader (csv.DictReade): csv containing the query result rows
            his_uri (dict): dict containing all the parameters needed to build the Athena query
        Output:
            Grid filled with the data from athena query result
        """
        hs_date_column_name = list(his_uri["hs_date_column"].keys())[0]
        hs_value_column_names = list(his_uri["hs_value_column"].keys())
        hs_type = his_uri['hs_type']
        history = Grid(columns=["ts", "val"])
        if not hs_type:
            hs_type = "float"
        if reader:
            for row in reader:
                date_format = his_uri["hs_date_column"][hs_date_column_name]  # "%Y-%m-%d %H:%M:%S.%f"
                date_val = self.put_date_format(row[hs_date_column_name], date_format)
                hs_values = {key: row[key] for key in hs_value_column_names}
                if len(hs_values) == 1:
                    history.append({
                        "ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                        "val": Provider._cast_timeserie_to_hs(str(list(hs_values.values())[0]), hs_type)
                    })
                else:
                    val = dict(zip(
                        hs_values.keys(),
                        [Provider._cast_timeserie_to_hs(hs_values[hs_col], his_uri['hs_value_column'][hs_col])
                         for hs_col in hs_values.keys()]
                    ))
                    history.append({"ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                                    "val": val})  # ,unit
        return history

    def run_query(self, his_uri: dict, dates_range: tuple, date_version):
        """
        Process Athena query
        Args:
            his_uri (dict): dict containing all the parameters needed to
            build the Athena query, e.g. database name,
            table name, partition keys, ...
            dates_range (tuple): (start_date, end_date) date range that represents the time period to query
            date_version (datetime): the date that represents the version of the ontology
        Output:
            The grid response containing the results
        """
        athena_client = self._get_read_client()

        try:
            # Create the query
            select_all = self.build_athena_query(his_uri, dates_range, date_version)
            log.debug("[ATHENA QUERY]: " + select_all)

            # Start query execution
            response = athena_client.start_query_execution(
                QueryString=select_all,
                QueryExecutionContext={
                    'Database': his_uri['db_name']
                },
                ResultConfiguration={
                    'OutputLocation': 's3://' + self._output_bucket_name +
                                      '/' + self._output_folder_name + "/",
                }
            )
            # Get query results
            reader = self.poll_query_status(response["QueryExecutionId"])
            # Create timeseries history grid
            history = self.create_history_grid(reader, his_uri)
            return history

        except ValueError as err:
            log.error("Exception while running query: %s", err)
            raise

    @overrides
    def his_read(  # type: ignore
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        # To deduce the target type, read the haystack entity
        entity = self.read(1, None, [entity_id], None, date_version)[0]
        if not entity:
            raise ValueError(f" id '{entity_id} not found")

        his_uri = entity.get('hisURI', None)  # type: ignore
        if not his_uri:
            raise ValueError(f" hisURI '{his_uri} not found")

        customer_id = self.get_customer_id()
        if not customer_id:
            customer_id = ' '

        try:
            history = self.run_query(his_uri, dates_range, date_version)  # type: ignore

            if history:
                min_date = datetime.max.replace(tzinfo=pytz.UTC)
                max_date = datetime.min.replace(tzinfo=pytz.UTC)

                for time_serie in history:
                    min_date = min(min_date, time_serie["ts"])
                    max_date = max(max_date, time_serie["ts"])
            else:
                min_date = date_version  # type: ignore
                max_date = date_version  # type: ignore

            history.metadata = {
                "id": entity_id,
                "hisStart": min_date,
                "hisEnd": max_date,
            }
            return history
        except ValueError as err:
            log.error("Exception while running query: %s", err)
            raise
