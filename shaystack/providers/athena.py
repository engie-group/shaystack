# -*- coding: utf-8 -*-
# SQL + Athena provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

from datetime import datetime, date, time
from typing import Optional, Tuple, Any, Dict
from urllib.parse import parse_qs
from urllib.parse import urlparse

import boto3
import pytz
from overrides import overrides

from .db import Provider as DBProvider
from .db import log
from ..datatypes import Ref, MARKER, REMOVE, Coordinate, Quantity, NA, XStr
from ..grid import Grid

import csv
import time
from ..period import Period


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

        self._read_client = session.client('athena', region_name=region,
                                           aws_access_key_id=credentials["AccessKeyId"],
                                           aws_secret_access_key=credentials["SecretAccessKey"],
                                           aws_session_token=credentials["SessionToken"]
                                           )
        log.debug("[ATHENA BOTO]: was created successfully! " + str(self._read_client.meta))
        return self._read_client

    # @overrides
    def _import_ts_in_db(self, time_series: Grid,  # TODO
                         entity_id: Ref,
                         customer_id: Optional[str],
                         now: Optional[datetime] = None
                         ) -> None:
        raise NotImplementedError('Format not implemented: %s' % mode)

    @staticmethod
    def _cast_timeserie_to_hs(val: str,
                              python_type: str,
                              unit: str = None) -> Any:
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

    def get_query_results(self, queryExecutionId:str)-> csv.DictReader:
        """

        Args:
            queryExecutionId (object): Str that represent the ExecutionId of athena query 
        """
        region = self._envs.get("AWS_REGION",
                                self._envs.get("AWS_DEFAULT_REGION"))
        try:
            resource = boto3.resource('s3', region)
            response = resource.Bucket(self._output_bucket_name).Object(
                key=self._output_folder_name + "/" + queryExecutionId + '.csv') \
                .get()

            lines = response['Body'].read().decode('utf-8').splitlines(True)

            reader = csv.DictReader(lines)

            return reader
        except Exception as e:
            print(e)

    def run_query(self, query: str, query_response: dict) -> csv.DictReader:
        """

        Args:
            query (str): athena compatible query
            query_response (dict): all metadata that came within athena response
        """
        try:
            query_status = None
            while query_status == 'QUEUED' or query_status == 'RUNNING' or query_status is None:
                query_status = \
                    self._get_read_client().get_query_execution(QueryExecutionId=query_response["QueryExecutionId"])[
                        'QueryExecution']['Status'][
                        'State']
                # print(query_status)
                log.info("[QUERY STATUS]: " + query_status)
                if query_status == 'FAILED' or query_status == 'CANCELLED':
                    error = self._get_read_client().get_query_execution(QueryExecutionId=query_response["QueryExecutionId"])[
                        'QueryExecution']['Status']['StateChangeReason']
                    raise Exception(
                        'Athena query with the string "{}" failed or was cancelled due to the following error:\n{}'.format(
                            query, error))
                time.sleep(10)
            # print('FINISHED\nQuery "{}" finished.'.format(query))
            reader = self.get_query_results(query_response["QueryExecutionId"])
            return reader

        except Exception as e:
            print(e)

    def get_date(self, str_date: str, date_pattern: str):
        """

        Args:
            str_date (str): string date
            date_pattern (str): date pattern
        """
        try:
            date_val = datetime.strptime(str_date, date_pattern)
        except ValueError:
            raise ValueError("time data %r does not match format %r" % (str_date, date_pattern))

        return date_val.strftime("%Y-%m-%d %H:%M:%S")

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        client = self._get_read_client()
        # To deduce the target type, read the haystack entity
        entity = self.read(1, None, [entity_id], None, date_version)[0]
        if not entity:
            raise ValueError(f" id '{entity_id} not found")

        hisURI = entity.get('hisURI', None)
        if not hisURI:
            raise ValueError(f" hisURI '{hisURI} not found")
        his_params = hisURI['partition_keys'].split("/")
        hs_date_column = list(hisURI["hs_date_column"].keys())[0]
        hs_value_column = list(hisURI["hs_value_column"].keys())
        date_part_keys = hisURI['date_part_keys']
        if not date_version:
            date_version = datetime.max.replace(tzinfo=pytz.UTC)

        date_range_period = Period(start=dates_range[0], end=dates_range[1])
        if dates_range and dates_range[1] > date_version:
            dates_range = list(dates_range)
            dates_range[1] = date_version

        # kind = entity.get("kind", "Number")
        customer_id = self.get_customer_id()
        if not customer_id:
            customer_id = ' '
        try:
            history = Grid(columns=["ts", "val"])

            select_all = f'SELECT {hs_date_column}, {", ".join(hs_value_column)}' \
                         f' FROM {hisURI["table_name"]}' \
                         f' WHERE {" ".join([str(item) + " AND" for item in his_params[:-1]])}' \
                         f' {his_params[-1]}'
            if dates_range:
                if date_part_keys.get('year_col'):
                    select_all += f' AND {date_part_keys.get("year_col")} in ({", ".join(map(str,date_range_period.years))})'
                if date_part_keys.get('month_col'):
                    select_all += f' AND {date_part_keys.get("month_col")} in ({", ".join(map(str,date_range_period.months))})'
                if date_part_keys.get('day_col'):
                    select_all += f' AND {date_part_keys.get("day_col")} in ({", ".join(map(str,date_range_period.days))})'

                select_all += f' AND time BETWEEN DATE(\'{dates_range[0].strftime("%Y-%m-%d")}\') '\
                              f' AND DATE(\'{dates_range[1].strftime("%Y-%m-%d")}\');'
            # f' AND day in {tuple(date_range_period.days)}' \

            log.debug("[ATHENA QUERY]: " + select_all)
            # Execution
            response = client.start_query_execution(
                QueryString=select_all,
                QueryExecutionContext={
                    'Database': hisURI['db_name']
                },
                ResultConfiguration={
                    'OutputLocation': 's3://' + self._output_bucket_name + '/' + self._output_folder_name + "/",
                }
            )

            reader = self.run_query(select_all, response)
            hs_type = hisURI['hs_type']
            if not hs_type:
                hs_type = "float"
            for row in reader:
                date_format = hisURI["hs_date_column"][hs_date_column] #"%Y-%m-%d %H:%M:%S.%f"
                # date_val = datetime.strptime(row[hisURI['hs_date_column_name']], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)
                date_val = self.get_date(row[hs_date_column], date_format)
                # date_val = row[hisURI['hs_date_column']]
                hs_values = {key: row[key] for key in hs_value_column}

                if len(hs_values) == 1:
                    # str_val = str(list(val.values())[0])
                    history.append({"ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                                    "val": Provider._cast_timeserie_to_hs(str(list(hs_values.values())[0])
                                                                          , hs_type)})  # ,unit
                else:
                    val = dict(zip(hs_values.keys(),
                                   [Provider._cast_timeserie_to_hs(hs_values[hs_col], hisURI['hs_value_column'][hs_col])
                                    for hs_col in hs_values.keys()]))
                    history.append({"ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                                    "val": val})  # ,unit

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
