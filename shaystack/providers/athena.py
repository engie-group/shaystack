# -*- coding: utf-8 -*-
# SQL + Athena provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
from random import randint

from datetime import datetime, date, time
from typing import Optional, Tuple, Any, Dict
from urllib.parse import parse_qs
from urllib.parse import urlparse
from botocore import exceptions

import boto3
import pytz
from overrides import overrides

from .db import Provider as DBProvider
from .db import log
from ..datatypes import Ref, MARKER, REMOVE, Coordinate, Quantity, NA, XStr
from ..grid import Grid
from ..period import Period

from csv import DictReader
import time


# noinspection PyUnusedLocal
class Provider(DBProvider):
    """
    Expose an Haystack data via the Haystack Rest API and SQL+TS databases
    """
    __slots__ = "_parsed_ts", "_ts_table_name", "_ts_database_name", "_boto", "_write_client", "_read_client"

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
        #TODO remove the CDH_PROJECT_ROLE_ARN
        #######################################################################
        ############ JUST FOR TESTING IT WONT BE USED IN PROD #################
        #######################################################################
        project_role_arn = self._envs.get('CDH_PROJECT_ROLE_ARN', '')
        sts_client = session.client("sts", region_name=region)
        assumed_role_object = sts_client.assume_role(
             RoleArn=project_role_arn,
             RoleSessionName="AssumeRoleSession1")
        credentials = assumed_role_object["Credentials"]
        log.info("[STS BOTO]: client was created successfully! ")
        #######################################################################

        self._read_client = session.client('athena',
                                           region_name=region,
                                           aws_access_key_id=credentials["AccessKeyId"],
                                           aws_secret_access_key=credentials["SecretAccessKey"],
                                           aws_session_token=credentials["SessionToken"]
                                           )
        log.info("[ATHENA BOTO]: was created successfully! " + str(self._read_client.meta))
        return self._read_client

    # @overrides
    def _import_ts_in_db(self, **kwargs) -> None:
        raise NotImplementedError('Feature not implemented')

    @staticmethod
    def _cast_timeserie_to_hs(val: str,
                              python_type: str,
                              unit: str = None) -> Any:
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
                split = val.split(",")
                return Coordinate(float(split[0]), float(split[1]))
            if python_type == "XStr":
                split = val.split(",")
                return XStr(*split)
            if python_type == "NoneType":
                return None
            raise ValueError(f"Unknown type {python_type}")
        else:
            return None

    def get_query_results(self, query_execution_id: str) -> DictReader:
        """
        Download result file
        Args:
            query_execution_id (object): Str that represent the ExecutionId of athena query
        """
        region = self._envs.get("AWS_REGION",
                                self._envs.get("AWS_DEFAULT_REGION"))
        try:
            resource = boto3.resource('s3', region)
            response = resource.Bucket(self._output_bucket_name).Object(
                key=f'{self._output_folder_name}/{query_execution_id}.csv').get()
            lines = response['Body'].read().decode('utf-8').splitlines(True)
            log.info("Query results CSV file contain [%s] row.", str(len(lines)))
            reader = DictReader(lines)
            return reader
        except exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("The object does not exist.")
            else:
                raise

    def poll_query_status(self, query_response: dict) -> DictReader:
        """
        Get the status of the Athena request, i.e. "QUEUED", "RUNNING", "FAILED" or "CANCELLED", and get the results
        of successful requests

        Args:
            query_response (dict): all metadata that came within athena response
        """
        try:
            athena_client = self._get_read_client()
            query_status = {'State': None}
            while query_status['State'] in ['QUEUED', 'RUNNING', None]:
                query_status = \
                    athena_client.get_query_execution(QueryExecutionId=query_response["QueryExecutionId"])[
                        'QueryExecution']['Status']
                log.info(f'[QUERY STATUS]: {query_status["State"]}')
                if query_status['State'] == 'FAILED' or query_status['State'] == 'CANCELLED':
                    # Get error message from Athena
                    error_message = 'Athena query with executionId {} was {} '.format(
                        query_response["QueryExecutionId"],
                        query_status["State"])
                    if "StateChangeReason" in query_status:
                        raise Exception(error_message + f'due to the following error:\n'
                                                        f'{query_status["StateChangeReason"]}')
                    else:
                        raise Exception(error_message)
                time.sleep(1)
            # getting the csv file that contain query results from s3 output bucket
            reader = self.get_query_results(query_response["QueryExecutionId"])
            return reader
        except Exception as e:
            print(e)

    @staticmethod
    def put_date_format(str_date: str, date_pattern: str) -> str:
        """
        Set the date to the correct date format specified in the "date_pattern" parameter

        Args:
            str_date (str): string date
            date_pattern (str): date pattern
        """
        try:
            date_val = datetime.strptime(str_date, date_pattern)
        except ValueError:
            raise ValueError("time data %r does not match format %r" % (str_date, date_pattern))
        return date_val.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def build_athena_query(his_uri: dict, dates_range: tuple, date_version: datetime) -> str:
        """
        Build up an Athena query based on the parameters that have been included in hisURI and apply
        filtering by a start date and an end date based on the date_range argument.
        Args:
             his_uri (dict): dict containing all the parameters needed to build the Athena query
             dates_range (tuple): (start_date, end_date) date range that represents the time period to query
             date_version (datetime): the date that represents the version of the ontology
        """
        hs_parts_keys = his_uri['partition_keys'].split("/")
        hs_date_column = list(his_uri["hs_date_column"].keys())[0]
        hs_value_column = list(his_uri["hs_value_column"].keys())
        hs_date_parts_keys = his_uri['date_part_keys']
        if not date_version:
            date_version = datetime.max.replace(tzinfo=pytz.UTC)

        date_range_period = Period(start=dates_range[0], end=dates_range[1])
        if dates_range and dates_range[1] > date_version:
            dates_range = list(dates_range)
            dates_range[1] = date_version

        select_all = f'SELECT {hs_date_column}, {", ".join(hs_value_column)}' \
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
                          f' AND DATE(\'{dates_range[1].strftime("%Y-%m-%d")}\');'
        return select_all

    def create_history_grid(self, reader: DictReader, his_uri: dict) -> Grid:
        """
        Create a Grid and fill it with the data from the query result rows that were stored as a csv
        file in the s3 bucket.
        Args:
            reader (csv.DictReade): csv containing the query result rows
            his_uri (dict): dict containing all the parameters needed to build the Athena query
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
            his_uri (dict): dict containing all the parameters needed to build the Athena query, e.g. database name,
            table name, partition keys, ...
            dates_range (tuple): (start_date, end_date) date range that represents the time period to query
            date_version (datetime): the date that represents the version of the ontology
        """
        athena_client = self._get_read_client()

        try:
            # Create the query
            select_all = self.build_athena_query(his_uri, dates_range, date_version=None)
            log.debug("[ATHENA QUERY]: " + select_all)

            # Start query execution
            response = athena_client.start_query_execution(
                QueryString=select_all,
                QueryExecutionContext={
                    'Database': his_uri['db_name']
                },
                ResultConfiguration={
                    'OutputLocation': 's3://' + self._output_bucket_name + '/' + self._output_folder_name + "/",
                }
            )
            # Get query results
            reader = self.poll_query_status(response)
            # Create timeseries history grid
            history = self.create_history_grid(reader, his_uri)
            return history

        except ValueError as err:
            log.error("Exception while running query: %s", err)
            raise

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        # To deduce the target type, read the haystack entity
        entity = self.read(1, None, [entity_id], None, date_version)[0]
        if not entity:
            raise ValueError(f" id '{entity_id} not found")

        his_uri = entity.get('hisURI', None)
        if not his_uri:
            raise ValueError(f" hisURI '{his_uri} not found")

        customer_id = self.get_customer_id()
        if not customer_id:
            customer_id = ' '

        try:
            history = self.run_query(his_uri, dates_range, date_version)

            if history:
                min_date = datetime.max.replace(tzinfo=pytz.UTC)
                max_date = datetime.min.replace(tzinfo=pytz.UTC)

                for time_serie in history:
                    min_date = min(min_date, time_serie["ts"])
                    max_date = max(max_date, time_serie["ts"])
            else:
                min_date = date_version
                max_date = date_version

            history.metadata = {
                "id": entity_id,
                "hisStart": min_date,
                "hisEnd": max_date,
            }
            return history
        except ValueError as err:
            log.error("Exception while running query: %s", err)
            raise
