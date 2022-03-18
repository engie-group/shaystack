# -*- coding: utf-8 -*-
# SQL + TS provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Add the persistance of time-series with TS database.

Set the HAYSTACK_TS with Time-series database connection URL,
(timestream://HaystackDemo/?mem_ttl=1&mag_ttl=100#haystack)
"""
from datetime import datetime, date, time
from os.path import dirname
from typing import Optional, Tuple, Callable, Any, Dict
from urllib.parse import parse_qs
from urllib.parse import urlparse

import boto3
import pytz
from botocore.client import BaseClient
from botocore.config import Config
from overrides import overrides

from .db import Provider as DBProvider
from .db import log
from .url import read_grid_from_uri
from ..datatypes import Ref, MARKER, REMOVE, Coordinate, Quantity, NA, XStr
from ..grid import Grid

import csv
import time
from ..period import Period

_MAX_ROWS_BY_WRITE = 100
_DEFAULT_MEM_TTL = 8766
_DEFAULT_MAG_TTL = 400


def _create_database(client: BaseClient, #TODO
                     database: str) -> None:
    try:
        client.create_database(DatabaseName=database)
        log.info("Database [%s] created successfully.", database)
    except client.exceptions.ConflictException:
        # Database exists. Skipping database creation
        log.debug("Database [%s] exists. Skipping database creation.", database)


def _create_table(client: BaseClient, #TODO
                  database: str,
                  table_name: str,
                  mem_ttl: int,
                  mag_ttl: int) -> None:
    try:
        client.create_table(DatabaseName=database,
                            TableName=table_name,
                            RetentionProperties={
                                'MemoryStoreRetentionPeriodInHours': mem_ttl,
                                'MagneticStoreRetentionPeriodInDays': mag_ttl
                            })
        log.info("Table [%s] successfully created (memory ttl: %sh, magnetic ttl: %sd.",
                 table_name, mem_ttl, mag_ttl)
    except client.exceptions.ConflictException:
        # Table exists on database [{database}]. Skipping table creation"
        log.debug("Table [%s] exists. Skipping database creation.", table_name)


def _update_table(client: BaseClient,  #TODO
                  database: str,
                  table_name: str,
                  mem_ttl: int,
                  mag_ttl: int) -> None:
    client.update_table(DatabaseName=database,
                        TableName=table_name,
                        RetentionProperties={
                            'MemoryStoreRetentionPeriodInHours': mem_ttl,
                            'MagneticStoreRetentionPeriodInDays': mag_ttl
                        })
    log.info("Retention updated to %sh and %sd.", mem_ttl, mag_ttl)


def _delete_table(client: BaseClient,  #TODO
                  database: str,
                  table_name: str) -> None:
    try:
        client.delete_table(DatabaseName=database, TableName=table_name)
    except client.exceptions.ResourceNotFoundException:
        pass  # Ignore


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
        self._ts_table_name = self._parsed_ts.fragment
        if not self._ts_table_name:
            self._ts_table_name = "haystack"
        self._ts_database_name = self._parsed_ts.hostname
        self._output_bucket_name = parse_qs(self._parsed_ts.query)['output_bucket_name'][0]
        self._output_folder_name = parse_qs(self._parsed_ts.query)['output_folder_name'][0]
        self._hs_type = parse_qs(self._parsed_ts.query)['hs_type'][0]
        self._hs_column_name = parse_qs(self._parsed_ts.query)['hs_column_name'][0]
        self._hs_date_column_name = parse_qs(self._parsed_ts.query)['hs_date_column_name'][0]
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

    def _get_write_client(self) -> object:
        if not self._write_client:
            region = self._envs.get("AWS_REGION",
                                    self._envs.get("AWS_DEFAULT_REGION"))
            self._write_client = self._get_boto().client('timestream-write',
                                                         region_name=region,
                                                         config=Config(read_timeout=10,
                                                                       max_pool_connections=5000,
                                                                       retries={'max_attempts': 3},
                                                                       region_name=self._envs["AWS_REGION"],
                                                                       )
                                                         )
        return self._write_client

    def _get_read_client(self):
        # if not self._read_client:
        region = self._envs.get("AWS_REGION",
                                self._envs.get("AWS_DEFAULT_REGION"))
        session = self._get_boto()
        # _CDH_PROJECT_ROLE_ARN = "arn:aws:iam::482508239569:role/cdh_ontologyathenaagatheacc_78690"
        project_role_arn = self._envs.get('CDH_PROJECT_ROLE_ARN', '')
        print(project_role_arn)
        sts_client = session.client("sts", region_name=region)

        assumed_role_object = sts_client.assume_role(
            RoleArn=project_role_arn,
            RoleSessionName="AssumeRoleSession1",
        )
        credentials = assumed_role_object["Credentials"]
        self._read_client = session.client('athena', region_name=region,
                                           aws_access_key_id=credentials["AccessKeyId"],
                                           aws_secret_access_key=credentials["SecretAccessKey"],
                                           aws_session_token=credentials["SessionToken"]
                                           )
        return self._read_client

    # @overrides
    def _import_ts_in_db(self, time_series: Grid, #TODO
                         entity_id: Ref,
                         customer_id: Optional[str],
                         now: Optional[datetime] = None
                         ) -> None:
        client = self._get_write_client()
        try:
            if not time_series:
                return  # Empty
            value = time_series[0]["val"]  # Suppose all values share the same type
            cast_fn, target_type = Provider._hs_to_timestream_type(value)
            if not customer_id:  # Empty string ?
                customer_id = ' '
            common_attributs = {
                'Dimensions': list(filter(lambda x: x['Value'] is not None, [
                    {'Name': 'id', 'Value': entity_id.name},
                    {'Name': 'hs_type', 'Value': type(value).__name__},
                    {'Name': 'unit', 'Value': value.symbol if isinstance(value, Quantity) else " "},
                    {'Name': 'customer_id', 'Value': customer_id}
                ])),
                'MeasureName': 'val',
                'MeasureValueType': target_type,  # DOUBLE | BIGINT | VARCHAR | BOOLEAN
                'TimeUnit': 'MICROSECONDS',  # MILLISECONDS | SECONDS | MICROSECONDS | NANOSECONDS
                'Version': int(round(datetime.now().timestamp() * 1000000))
            }

            records = [{
                'Time': str(int(round(row["ts"].timestamp() * 1000000))),
                "MeasureValue": cast_fn(row["val"]),
            } for row in time_series]

            for i in range(0, len(records), _MAX_ROWS_BY_WRITE):
                result = client.write_records(DatabaseName=self._ts_database_name,
                                              TableName=self._ts_table_name,
                                              Records=records[i:i + _MAX_ROWS_BY_WRITE],
                                              CommonAttributes=common_attributs)
                log.debug("WriteRecords Status: [%s]", result['ResponseMetadata']['HTTPStatusCode'])
        except client.exceptions.RejectedRecordsException as err:
            log.error("RejectedRecords: %s", err)
            for rejected_record in err.response["RejectedRecords"]:
                log.error(' [%s:%s]: %s',
                          str(rejected_record["RecordIndex"]),
                          time_series[rejected_record["RecordIndex"]]["ts"],
                          rejected_record["Reason"]
                          )
            raise

    @staticmethod
    def _hs_to_timestream_type(value: Any) -> Tuple[Callable, str]:  #TODO
        cast_fn = str
        if isinstance(value, str):
            target_type = "VARCHAR"
        elif isinstance(value, float):
            target_type = "DOUBLE"
        elif isinstance(value, Quantity):
            target_type = "DOUBLE"
            cast_fn = lambda x: str(x.m)
        elif isinstance(value, bool):
            target_type = "BOOLEAN"
        elif isinstance(value, int):
            target_type = "DOUBLE"
        elif value is MARKER:
            target_type = "BOOLEAN"
            cast_fn = lambda x: str(x is MARKER)
        elif value is REMOVE:
            target_type = "BOOLEAN"
            cast_fn = lambda x: str(x is REMOVE)
        elif value is NA:
            target_type = 'BOOLEAN'
            cast_fn = lambda x: str(x is NA)
        elif isinstance(value, Ref):
            target_type = "VARCHAR"
            cast_fn = lambda x: x.name
        elif isinstance(value, datetime):
            target_type = "BIGINT"
            cast_fn = lambda x: str(int(round(x.timestamp())))
        elif isinstance(value, date):
            target_type = "BIGINT"
            cast_fn = lambda x: str(x.toordinal())
        elif isinstance(value, time):
            target_type = "BIGINT"
            cast_fn = lambda x: str(((x.hour * 60 + x.minute) * 60 + x.second) * 1000000 + x.microsecond)
        elif isinstance(value, Coordinate):
            target_type = "VARCHAR"
            cast_fn = lambda x: str(x.latitude) + "," + str(x.longitude)
        elif isinstance(value, XStr):
            target_type = "VARCHAR"
            cast_fn = lambda x: value.encoding + "," + value.data_to_string()
        elif value is None:
            target_type = "BOOLEAN"
            cast_fn = lambda x: str(False)
        else:
            raise ValueError("Unknwon type")
        return cast_fn, target_type

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

    _kind_type = {
        "marker": "BOOLEAN",
        "delete": "BOOLEAN",
        "bool": "BOOLEAN",
        "na": "BOOLEAN",
        "number": "DOUBLE",
        "remove": "BOOLEAN",
        "str": "VARCHAR",
        "uri": "VARCHAR",
        "ref": "VARCHAR",
        "date": "BIGINT",
        "time": "BIGINT",
        "datetime": "BIGINT",
        "coord": "VARCHAR",
        "xstr": "VARCHAR",
    }

    @staticmethod
    def _kind_to_timestream_type(kind: str) -> str:
        return Provider._kind_type[kind.lower()]

    def get_query_results(self, queryExecutionId):
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

    def run_query(self, query, res):
        try:
            query_status = None
            while query_status == 'QUEUED' or query_status == 'RUNNING' or query_status is None:
                query_status = \
                    self._get_read_client().get_query_execution(QueryExecutionId=res["QueryExecutionId"])[
                        'QueryExecution']['Status'][
                        'State']
                print(query_status)
                if query_status == 'FAILED' or query_status == 'CANCELLED':
                    error = self._get_read_client().get_query_execution(QueryExecutionId=res["QueryExecutionId"])[
                        'QueryExecution'][
                        'Status']['StateChangeReason']
                    raise Exception(
                        'Athena query with the string "{}" failed or was cancelled due to the following error:\n{}'.format(
                            query, error))
                time.sleep(10)
            print('FINISHED\nQuery "{}" finished.'.format(query))
            reader = self.get_query_results(res["QueryExecutionId"])
            return reader

        except Exception as e:
            print(e)

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
        params = hisURI.split("/")

        if not date_version:
            date_version = datetime.max.replace(tzinfo=pytz.UTC)

        prediction_period = Period(start=dates_range[0], end=dates_range[1])
        years = prediction_period.years
        if dates_range and dates_range[1] > date_version:
            dates_range = list(dates_range)
            dates_range[1] = date_version

        kind = entity.get("kind", "Number")
        timestream_type = Provider._kind_to_timestream_type(kind)
        customer_id = self.get_customer_id()
        if not customer_id:
            customer_id = ' '
        try:
            history = Grid(columns=["ts", "val"])
            select_all = f"SELECT * FROM {self._ts_table_name} WHERE " + \
                         " ".join([str(item) + " AND" for item in params[:-1]]) + \
                         " " + params[-1]

            if dates_range:
                select_all += f" AND year in {tuple(prediction_period.years)}" \
                              f" AND month in {tuple(prediction_period.months)}" \
                              f" AND day in {tuple(prediction_period.days)}" \
                              f" AND time BETWEEN DATE('{dates_range[0].strftime('%Y-%m-%d')}') " \
                              f" AND DATE('{dates_range[1].strftime('%Y-%m-%d')}');"

            # Execution
            response = client.start_query_execution(
                QueryString=select_all,
                QueryExecutionContext={
                    'Database': self._ts_database_name
                },
                ResultConfiguration={
                    'OutputLocation': 's3://' + self._output_bucket_name + '/' + self._output_folder_name + "/",
                }
            )

            reader = self.run_query(select_all, response)
            hs_type = self._hs_type
            for row in reader:
                # csv_header_key is the header keys which you have defined in your csv header
                str_val = row[self._hs_column_name]
                date_val = row[self._hs_date_column_name]
                if not self._hs_type:
                    hs_type = "float"
                history.append({"ts": datetime.fromisoformat(date_val).replace(tzinfo=pytz.UTC),
                                "val": Provider._cast_timeserie_to_hs(str_val, hs_type)})  # ,unit

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

    def create_ts(self) -> None:
        """ Create the time serie database and schema. """
        client = self._get_write_client()
        _create_database(client, self._ts_database_name)
        pqs = parse_qs(self._parsed_ts.query)
        mem_ttl = int(pqs["mem_ttl"][0]) if "mem_ttl" in pqs else _DEFAULT_MEM_TTL
        mag_ttl = int(pqs["mag_ttl"][0]) if "mag_ttl" in pqs else _DEFAULT_MAG_TTL
        _create_table(client, self._ts_database_name, self._ts_table_name, mem_ttl, mag_ttl)

    def purge_ts(self) -> None:
        """ Purge the timeserie database. """
        _delete_table(self._get_write_client(), self._ts_database_name, self._ts_table_name)

    @overrides
    def create_db(self) -> None:
        super().create_db()
        self.create_ts()

    @overrides
    def purge_db(self) -> None:
        super().purge_db()
        self.purge_ts()

    @overrides
    def import_ts(self,
                  source_uri: str,
                  customer_id: str = '',
                  version: Optional[datetime] = None
                  ):
        target_grid = read_grid_from_uri(source_uri, envs=self._envs)
        dir_name = dirname(source_uri)
        if not version:
            version = datetime.now(tz=pytz.UTC)

        for row in target_grid:
            if "hisURI" in row:
                assert "id" in row, "TS must have an id"
                uri = dir_name + '/' + row['hisURI']
                ts_grid = read_grid_from_uri(uri, envs=self._envs)
                self._import_ts_in_db(ts_grid, row["id"], customer_id, version)
                log.info("%s imported", uri)