import os
from datetime import datetime, date, time
from typing import Optional, Tuple, Callable, Any
from urllib.parse import parse_qs
from urllib.parse import urlparse

import boto3
import dateutil
from botocore.client import BaseClient
from botocore.config import Config
from overrides import overrides

from .sql import Provider as SQLProvider
from .sql import log
from ..datatypes import Ref, MARKER, REMOVE, Coordinate, Quantity, NA
from ..grid import Grid


def _create_database(client: BaseClient,
                     database: str) -> None:
    try:
        client.create_database(DatabaseName=database)
        log.info(f"Database [{database}] created successfully.")
    except client.exceptions.ConflictException:
        # Database exists. Skipping database creation
        log.debug(f"Database [{database}] exists. Skipping database creation.")


def _create_table(client: BaseClient,
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
        log.info(f"Table [{table_name}] successfully created (memory ttl: {mem_ttl}h magnetic ttl: {mag_ttl}d.")
    except client.exceptions.ConflictException:
        # Table exists on database [{database}]. Skipping table creation"
        log.debug(f"Table [{table_name}] exists. Skipping database creation.")


def _update_table(client: BaseClient,
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
    log.info(f"Retention updated to {mem_ttl}h and {mag_ttl}d.")


def _delete_table(client: BaseClient,
                  database: str,
                  table_name: str) -> None:
    try:
        client.delete_table(DatabaseName=database, TableName=table_name)
    except client.exceptions.ResourceNotFoundException:
        pass  # Ignore


class Provider(SQLProvider):
    @property
    def name(self) -> str:
        return "SQL+timeseries"

    def __init__(self):
        super().__init__()
        log.info("Use %s", self._get_ts())
        self._parsed_ts = urlparse(self._get_ts())
        self._ts_table_name = self._parsed_ts.fragment
        if not self._ts_table_name:
            self._ts_table_name = "haystack"
        self._ts_database_name = self._parsed_ts.hostname
        self._boto = None
        self._write_client = None
        self._read_client = None

    def _get_boto(self):
        if not self._boto:
            self._boto = boto3.Session()
        return self._boto

    def _get_ts(self) -> str:  # pylint: disable=no-self-use
        """ Return the url to the file to expose. """
        return os.environ["HAYSTACK_TS"]

    def _get_write_client(self):
        if not self._write_client:
            region = os.environ.get("AWS_REGION",
                                    os.environ.get("AWS_DEFAULT_REGION"))
            self._write_client = self._get_boto().client('timestream-write',
                                                         region_name=region,
                                                         config=Config(read_timeout=10,
                                                                       max_pool_connections=5000,
                                                                       retries={'max_attempts': 3}
                                                                       )
                                                         )
        return self._write_client

    def _get_read_client(self):
        if not self._read_client:
            region = os.environ.get("AWS_REGION",
                                    os.environ.get("AWS_DEFAULT_REGION"))
            self._read_client = self._get_boto().client('timestream-query',
                                                        region_name=region)
        return self._read_client

    @staticmethod
    def _print_rejected_records_exceptions(err):
        log.error(f"RejectedRecords: {err}")
        for rr in err.response["RejectedRecords"]:
            log.error(f'Rejected Index {str(rr["RecordIndex"])}: {rr["Reason"]}')
            if "ExistingVersion" in rr:
                log.error(f'Rejected record existing version: {rr["ExistingVersion"]}')

    @overrides
    def import_ts_in_db(self, time_series: Grid,
                        version: datetime,
                        entity_id: Ref,
                        customer_id: Optional[str],
                        now: Optional[datetime] = None
                        ) -> None:
        # FIXME: travailler en microsecond ?
        try:
            client = self._get_write_client()

            if not time_series:
                return  # Empty
            v = time_series[0]["val"]  # Suppose all values share the same type
            cast_fn, target_type = self._hs_to_timestream_type(v)
            common_attributs = {
                'Dimensions': [
                    {'Name': 'id', 'Value': entity_id.name},
                    {'Name': 'hs_type', 'Value': type(v).__name__},
                    {'Name': 'unit', 'Value': v.unit if isinstance(v, Quantity) else " "},
                    {'Name': 'customer', 'Value': customer_id}
                ],
                'MeasureName': 'val',
                'MeasureValueType': target_type,  # DOUBLE | BIGINT | VARCHAR | BOOLEAN
                'TimeUnit': 'MILLISECONDS',  # MILLISECONDS | SECONDS | MICROSECONDS | NANOSECONDS
                # See https://docs.aws.amazon.com/timestream/latest/developerguide/API_WriteRecords.html
                'Version': int(round(version.timestamp() * 1000))
            }

            # FIXME : Maximum number of 100 items.
            records = [{
                'Time': str(int(round(row["ts"].timestamp() * 1000))),
                "MeasureValue": cast_fn(row["val"]),
            } for row in time_series]

            result = client.write_records(DatabaseName=self._ts_database_name,
                                          TableName=self._ts_table_name,
                                          Records=records,
                                          CommonAttributes=common_attributs)
            log.debug(f"WriteRecords Status: [{result['ResponseMetadata']['HTTPStatusCode']}]")
        except client.exceptions.RejectedRecordsException as err:
            self._print_rejected_records_exceptions(err)
            raise

    def _hs_to_timestream_type(self, v: Any) -> Tuple[Callable, str]:
        target_type = None
        cast_fn = lambda x: str(x)
        if isinstance(v, str):
            target_type = "VARCHAR"
        elif isinstance(v, float):
            target_type = "DOUBLE"
        elif isinstance(v, Quantity):
            target_type = "DOUBLE"
            cast_fn = lambda x: str(x.value)
        elif isinstance(v, bool):
            target_type = "BOOLEAN"
        elif isinstance(v, int):
            target_type = "DOUBLE"
        elif v is MARKER:
            target_type = "BOOLEAN"
            cast_fn = lambda x: str(x is MARKER)
        elif v is REMOVE:
            target_type = "BOOLEAN"
            cast_fn = lambda x: str(x is REMOVE)
        elif v is NA:
            target_type = 'DOUBLE'
            cast_fn = lambda x: float('nan')
        elif isinstance(v, Ref):
            target_type = "VARCHAR"
            cast_fn = lambda x: x.name
        elif isinstance(v, datetime):
            target_type = "BIGINT"
            cast_fn = lambda x: str(int(round(x.timestamp())))
        elif isinstance(v, date):
            target_type = "BIGINT"
            cast_fn = lambda x: str(x.toordinal())
        elif isinstance(v, time):
            target_type = "BIGINT"
            cast_fn = lambda x: str(((x.hour * 60 + x.minute) * 60 + x.second) * 1000000 + x.microsecond)
        elif isinstance(v, Coordinate):
            target_type = "VARCHAR"
            cast_fn = lambda x: str(x.latitude) + "," + str(x.longitude)
        elif v == None:
            target_type = "BOOLEAN"
            cast_fn = lambda x: str(x)
        else:
            raise ValueError("Unknwon type")
        return cast_fn, target_type

    def _cast_timeserie_to_hs(self,
                              val: str,
                              t: str,
                              unit: str) -> Any:
        if t == "str":
            return val
        if t == "float":
            return float(val)
        if t == "PintQuantity":
            return Quantity(float(val), unit)
        if t == "Quantity":
            return Quantity(float(val), unit)
        if t == "bool":
            return val.lower() == 'true'
        if t == "int":
            return int(float(val))
        if t == "MarkerType":
            return MARKER if val else None
        if t == "RemoveType":
            return REMOVE if val else None
        if t == "NAType":
            return NA if val else None
        if t == "Ref":
            return Ref(val)
        if t == "datetime":
            return datetime.fromtimestamp(int(val))
        if t == "date":
            return date.fromordinal(int(val))
        if t == "time":
            int_time = int(val)
            h = ((int_time // 1000000) // 60) // 60
            m = ((int_time // 1000000) // 60) % 60
            s = (int_time // 1000000) % 60
            mic = int_time % 1000000
            return time(h, m, s, mic)
        if t == "Coordinate":
            s = val.split(",")
            return Coordinate(float(s[0]), float(s[1]))
        if t == "NoneType":
            return None

    def _kind_to_timestream_type(self, kind: str) -> str:
        switcher = {  # FIXME: static
            "marker": "BOOLEAN",
            "bool": "BOOLEAN",
            "na": "BOOLEAN",  # FIXME
            "number": "DOUBLE",
            "remove": "BOOLEAN",
            "marker": "BOOLEAN",
            "str": "VARCHAR",
            "uri": "VARCHAR",  # FIXME
            "ref": "VARCHAR",
            "bin": "VARCHAR",  # FIXME
            "date": "BIGINT",
            "time": "BIGINT",
            "datetime": "BIGINT",
            "coord": "VARCHAR",
            "xstr": "VARCHAR",  # FIXME
        }
        return switcher[kind.lower()]

    @overrides
    def create_db(self) -> None:
        super().create_db()
        self.create_ts()

    @overrides
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]] = None,
            date_version: Optional[datetime] = None,
    ) -> Grid:
        paginator = self._get_read_client().get_paginator('query')
        # To deduce the target type, read the haystack entity
        entity = self.read(1, None, [entity_id], None, date_version)[0]
        if not entity:
            raise ValueError(f" id '{entity_id} not found")
        kind = entity.get("kind", "Number")
        timestream_type = self._kind_to_timestream_type(kind)
        try:
            grid = Grid(columns=["ts", "val"])
            # TODO: customer ?
            # TODO: date_range et date_version

            SELECT_ALL = f"SELECT time,hs_type,unit,measure_value::{timestream_type} FROM {self._ts_database_name}.{self._ts_table_name} " \
                         f"WHERE id='{entity_id.name}' and customer='{self.get_customer_id()}'"
            page_iterator = paginator.paginate(QueryString=SELECT_ALL)
            for page in page_iterator:

                for row in page['Rows']:
                    datas = row['Data']
                    ts = dateutil.parser.isoparse(datas[0]['ScalarValue'])
                    hs_type = datas[1]['ScalarValue']
                    unit = datas[2]['ScalarValue'].strip()
                    str_val = datas[3]['ScalarValue']

                    grid.append({"ts": ts, "val": self._cast_timeserie_to_hs(str_val, hs_type, unit)})
            return grid
        except ValueError as err:
            log.error("Exception while running query:", err)

    def create_ts(self) -> None:
        client = self._get_write_client()
        _create_database(client, self._ts_database_name)
        mem_ttl = int(parse_qs(self._parsed_ts.query).get("mem_ttl", 24)[0])
        mag_ttl = int(parse_qs(self._parsed_ts.query).get("mag_ttl", 365)[0])
        _create_table(client, self._ts_database_name, self._ts_table_name, mem_ttl, mag_ttl)

    def delete_ts(self) -> None:
        _delete_table(self._get_write_client(), self._ts_database_name, self._ts_table_name)
