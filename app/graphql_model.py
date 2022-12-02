# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Model to inject a another graphene model, to manage the haystack layer.
See the `blueprint_graphql` to see how to integrate this part of global GraphQL model.
"""
import json
import logging
from datetime import datetime, date, time
from typing import Optional, List, Any, Union, Type

import graphene
import pytz
from graphql.type import GraphQLResolveInfo as ResolveInfo
from graphql.language import StringValueNode, IntValueNode, FloatValueNode, BooleanValueNode, EnumValueNode

import shaystack
from shaystack import Ref, Uri, Coordinate, parse_hs_datetime_format, Grid
from shaystack.grid_filter import parse_hs_time_format, parse_hs_date_format
from shaystack.providers.haystack_interface import parse_date_range, HaystackInterface
from shaystack.type import Entity
# noinspection PyProtectedMember,PyProtectedMember,PyProtectedMember
from shaystack.zincdumper import _dump_hs_date_time, _dump_hs_time, _dump_hs_date

BOTO3_AVAILABLE = False
try:
    # Check the presence of boto3
    import boto3  # pylint: disable=unused-import

    BOTO3_AVAILABLE = True
except ImportError:
    pass

log = logging.getLogger("shaystack")


class HSScalar(graphene.Scalar):
    """Haystack Scalar"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Update name for AWS"""
        name = "AWSJSON" if BOTO3_AVAILABLE else "JSONString"

    @staticmethod
    def serialize(hs_scalar: Any) -> Any:
        """
        Convert scala value to Json
        Args:
            hs_scalar: Any value
        """
        return json.loads(shaystack.dump_scalar(hs_scalar,  # type: ignore
                                                shaystack.MODE_JSON,
                                                version=shaystack.VER_3_0))

    @staticmethod
    def parse_literal(node: Union[IntValueNode, FloatValueNode, StringValueNode,
                                  BooleanValueNode, EnumValueNode]) -> Any:
        """
        Parse to scalar value
        Args:
            node: The graphql node
        """
        if isinstance(node, StringValueNode):
            str_value = node.value
            if len(str_value) >= 2 and str_value[1] == ':':
                return shaystack.parse_scalar(node.value,
                                              shaystack.MODE_JSON)
        return node.value

    @staticmethod
    def parse_value(value: str) -> Any:
        """
        Args:
            value: The value to parse
        """
        return shaystack.parse_scalar(value, shaystack.MODE_JSON)


class HSDateTime(graphene.String):
    """Haystack compatible date format."""

    class Meta:  # pylint: disable=missing-class-docstring
        name = "AWSDateTime" if BOTO3_AVAILABLE else "DateTime"

    @staticmethod
    def serialize(date_time: datetime) -> str:
        """
        Convert date_time to json compatible string
        Args:
            date_time: The date time to convert to json
        """
        assert isinstance(date_time, datetime), \
            'Received not compatible datetime "{}"'.format(repr(date_time))
        return _dump_hs_date_time(date_time)

    @staticmethod
    def parse_literal(node: StringValueNode) -> datetime:  # pylint: disable=arguments-differ
        # Call to convert graphql parameter to python object
        """
        Convert a haystack json string to data time
        Args:
            node: GraphQL node to convert
        """
        assert isinstance(node, StringValueNode), \
            'Received not compatible datetime "{}"'.format(repr(node))
        return HSDateTime.parse_value(node.value)

    @staticmethod
    def parse_value(value: Union[datetime, date, str]) -> datetime:  # type: ignore
        # Call to convert graphql variable to python object
        """
        Args:
            value:
        """
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.max.time()).replace(tzinfo=pytz.UTC)
        return parse_hs_datetime_format(value, pytz.UTC)


class HSDate(graphene.String):
    """Haystack date for GraphQL"""

    class Meta:  # pylint: disable=missing-class-docstring
        name = "AWSDate" if BOTO3_AVAILABLE else "Date"

    @staticmethod
    def serialize(a_date: date) -> str:
        """
        Convert date to haystack json string.
        Args:
            a_date: A date
        """
        assert isinstance(a_date, date), 'Received not compatible date "{}"'.format(repr(a_date))
        return _dump_hs_date(a_date)

    @staticmethod
    def parse_literal(node: StringValueNode) -> date:  # pylint: disable=arguments-differ
        """
        Convert the Graphql string to date.
        Args:
            node: The graphql string
        """
        assert isinstance(node, StringValueNode), 'Received not compatible date "{}"'.format(repr(node))
        return HSDate.parse_value(node.value)

    @staticmethod
    def parse_value(value: Union[date, str]) -> date:  # type: ignore
        """
        Convert a date to haystack json.
        Args:
            value: The date
        """
        if isinstance(value, date):
            return value
        return parse_hs_date_format(value)


class HSTime(graphene.String):
    """Haystack time for GraphQL"""

    class Meta:  # pylint: disable=missing-class-docstring
        name = "AWSTime" if BOTO3_AVAILABLE else "Time"

    @staticmethod
    def serialize(a_time: time) -> str:
        """
        Convert a time to Haystack json string
        Args:
            a_time: The time.
        """
        assert isinstance(a_time, time), 'Received not compatible time "{}"'.format(repr(a_time))
        return _dump_hs_time(a_time)

    @staticmethod
    def parse_literal(node: StringValueNode) -> time:  # pylint: disable=arguments-differ
        """
        Convert a haystack json string to time
        Args:
            node: The string
        """
        assert isinstance(node, StringValueNode), 'Received not compatible time "{}"'.format(repr(node))
        return HSTime.parse_value(node.value)

    @staticmethod
    def parse_value(value: Union[time, str]) -> time:  # type: ignore
        """
        Args:
            value:
        """
        if isinstance(value, time):
            return value
        return parse_hs_time_format(value)


class HSUri(graphene.String):
    """Haystack URI for GraphQL"""

    class Meta:  # pylint: disable=too-few-public-methods,missing-class-docstring
        name = "AWSURL" if BOTO3_AVAILABLE else "HSURL"

    @staticmethod
    def serialize(a_uri: Uri) -> str:
        """
        Convert an Uri to Haystack json string
        Args:
            a_uri: The Uri
        """
        assert isinstance(a_uri, Uri), 'Received not compatible uri "{}"'.format(repr(a_uri))
        return str(a_uri)

    @staticmethod
    def parse_literal(node: StringValueNode) -> Uri:  # pylint: disable=arguments-differ
        """
        Convert the Graphql string to Uri
        Args:
            node: The string
        """
        return HSUri.parse_value(node.value)

    @staticmethod
    def parse_value(value: str) -> Uri:
        """
        Convert a haystack json string to Uri.
        Args:
            value: The string
        """
        if value.startswith("u:"):
            return shaystack.parse_scalar(value, shaystack.MODE_JSON, version=shaystack.VER_3_0)
        return Uri(value)


class HSCoordinate(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Haystack coordinate for GraphQL"""
    latitude = graphene.Float(required=True,
                              description="Latitude")
    longitude = graphene.Float(required=True,
                               description="Longitude")


class HSAbout(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Result of 'about' haystack operation"""
    haystackVersion = graphene.String(required=True,
                                      description="Haystack version implemented")
    tz = graphene.String(required=True,
                         description="Server time zone")
    serverName = graphene.String(required=True,
                                 description="Server name")
    serverTime = graphene.Field(graphene.NonNull(HSDateTime),
                                description="Server current time")
    serverBootTime = graphene.Field(graphene.NonNull(HSDateTime),
                                    description="Server boot time")
    productName = graphene.String(required=True,
                                  description="Server Product name")
    productUri = graphene.Field(graphene.NonNull(HSUri),
                                description="Server URL")
    productVersion = graphene.String(required=True,
                                     description="Product version")
    moduleName = graphene.String(required=True,
                                 description="Module name")
    moduleVersion = graphene.String(required=True,
                                    description="Module version")


class HSOps(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Result of 'ops' haystack operation"""

    name = graphene.String(description="Name of operation "
                                       "(see https://project-haystack.org/doc/docHaystack/Ops)")
    summary = graphene.String(description="Summary of operation")


class HSTS(graphene.ObjectType):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Result of 'hisRead' haystack operation"""
    ts = graphene.Field(HSDateTime, description="Date time of event")
    val = graphene.Field(HSScalar, description="Haystack JSON format of value")

    int = graphene.Int(required=False, description="Integer version of the value")
    float = graphene.Float(required=False, description="Float version of the value")
    str = graphene.String(required=False, description="Float version of the value")
    bool = graphene.Boolean(required=False, description="Boolean version of the value")
    uri = graphene.String(required=False, description="URI version of the value")
    ref = graphene.String(required=False, description="Reference version of the value")
    date = HSDate(required=False, description="Date version of the value")
    time = HSTime(required=False, description="Time version of the value")
    datetime = HSDateTime(required=False, description="Date time version of the value")
    coord = graphene.Field(HSCoordinate,
                           description="Geographic Coordinate")


class HSPointWrite(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Result of 'pointWrite' haystack operation"""
    level = graphene.Int(description="Current level")
    levelDis = graphene.String(description="Description of level")
    val = graphene.Field(HSScalar, description="Value")
    who = graphene.String(description="Who has updated the value")


# PPR: see the batch approach
class ReadHaystack(graphene.ObjectType):
    """Ontology conform with Haystack project"""

    def __init__(self, provider: HaystackInterface):
        super().__init__()
        self.provider = provider

    class Meta:  # pylint: disable=too-few-public-methods,missing-class-docstring
        name = "Haystack"

    about = graphene.NonNull(HSAbout,
                             description="Versions of api")

    ops = graphene.NonNull(graphene.List(
        graphene.NonNull(HSOps)),
        description="List of operation implemented")

    tag_values = graphene.NonNull(graphene.List(graphene.NonNull(graphene.String),
                                                ),
                                  tag=graphene.String(required=True,
                                                      description="Tag name"),
                                  version=HSDateTime(description="Date of the version "
                                                                 "or nothing for the last version"),
                                  description="All values for a specific tag")

    versions = graphene.NonNull(graphene.List(graphene.NonNull(HSDateTime)),
                                description="All versions of data")

    entities = graphene.List(
        graphene.NonNull(HSScalar),
        ids=graphene.List(graphene.ID,
                          description="List of ids to return (if set, ignore filter and limit)"),
        select=graphene.String(default_value='*',
                               description="List of tags to return"),
        limit=graphene.Int(default_value=0,
                           description="Maximum number of items to return"),
        filter=graphene.String(default_value='',
                               description="Filter or item (see "
                                           "https://project-haystack.org/doc/docHaystack/Filters"),
        version=HSDateTime(description="Date of the version or nothing for the last version"),
        description="Selected entities of ontology"
    )

    histories = graphene.List(graphene.NonNull(graphene.List(graphene.NonNull(HSTS))),
                              ids=graphene.List(graphene.ID,
                                                description="List of ids to return"),
                              dates_range=graphene.String(description="today, yesterday, "
                                                                      "{date}, {date},{date}, "
                                                                      "{datetime}, "
                                                                      "{datetime},{datetime}"
                                                          ),
                              version=HSDateTime(
                                  description="Date of the version or nothing for the last version"),
                              description="Selected time series")

    point_write = graphene.List(
        graphene.NonNull(HSPointWrite),
        id=graphene.ID(required=True,
                       description="Id to read (accept @xxx, r:xxx or xxx)"),
        version=HSDateTime(description="Date of the version or nothing for the last version"),
        description="Point write values"
    )

    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_about(parent: 'ReadHaystack',
                      info: ResolveInfo):
        log.debug("resolve_about(parent,info)")
        provider = parent.provider
        grid = provider.about("http://localhost")
        result = ReadHaystack._conv_entity(HSAbout, grid[0])  # type: ignore
        result.serverTime = grid[0]["serverTime"]   # type: ignore # pylint: disable=invalid-name
        result.bootTime = grid[0]["serverBootTime"]   # type: ignore #pylint: disable=invalid-name, attribute-defined-outside-init
        return result

    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_ops(parent: 'ReadHaystack',
                    info: ResolveInfo):
        log.debug("resolve_about(parent,info)")
        grid = parent.provider.ops()
        return ReadHaystack._conv_list_to_object_type(HSOps, grid)

    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_tag_values(parent: 'ReadHaystack',
                           info: ResolveInfo,
                           tag: str,
                           version: Optional[HSDateTime] = None):
        log.debug("resolve_values(parent,info,%s)", tag)
        return parent.provider.values_for_tag(tag, version)  # type: ignore

    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_versions(parent: 'ReadHaystack',
                         info: ResolveInfo):
        log.debug("resolve_versions(parent,info)")
        return parent.provider.versions()

    # noinspection PyShadowingBuiltins
    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_entities(parent: 'ReadHaystack',
                         info: ResolveInfo,
                         ids: Optional[List[str]] = None,
                         select: str = '*',
                         filter: str = '',  # pylint: disable=redefined-builtin
                         limit: int = 0,
                         version: Optional[HSDateTime] = None):
        log.debug(
            "resolve_entities(parent,info,ids=%s, "
            "select=%s, filter=%s, "
            "limit=%s, version=%s)", ids, select, filter, limit, version)
        if ids:
            ids = [Ref(ReadHaystack._filter_id(entity_id)) for entity_id in ids]  # type: ignore
        grid = parent.provider.read(limit, select, ids, filter, version)  # type: ignore
        return grid.purge()

    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_histories(parent: 'ReadHaystack',
                          info: ResolveInfo,
                          ids: Optional[List[str]] = None,
                          dates_range: Optional[str] = None,
                          version: Union[str, datetime, date, None] = None):
        if version:
            version = HSDateTime.parse_value(version)
        log.debug("resolve_histories(parent,info,ids=%s, range=%s, version=%s)",
                  ids, dates_range, version)
        grid_date_range = parse_date_range(dates_range, parent.provider.get_tz())  # type: ignore
        return [ReadHaystack._conv_history(
            parent.provider.his_read(Ref(ReadHaystack._filter_id(entity_id)),
                                     grid_date_range, version),  # type: ignore
            info
        )
            for entity_id in ids]  # type: ignore

    # noinspection PyUnusedLocal
    @staticmethod
    def resolve_point_write(parent: 'ReadHaystack',
                            info: ResolveInfo,
                            entity_id: str,
                            version: Union[datetime, str, None] = None):
        if version:
            version = HSDateTime.parse_value(version)
        log.debug("resolve_point_write(parent,info, entity_id=%s, version=%s)",
                  entity_id, version)
        ref = Ref(ReadHaystack._filter_id(entity_id))
        grid = parent.provider.point_write_read(ref, version)  # type: ignore
        return ReadHaystack._conv_list_to_object_type(HSPointWrite, grid)

    @staticmethod
    def _conv_value(entity: Entity,
                    info: ResolveInfo) -> HSTS:
        selection = info.field_nodes[0].selection_set.selections  # type: ignore
        cast_value = HSTS()
        value = entity["val"]
        cast_value.ts = entity["ts"]  # type: ignore # pylint: disable=invalid-name
        cast_value.val = value  # type: ignore
        for sel in selection:
            name = sel.name.value  # type: ignore
            if name in ['ts', 'val']:
                continue

            if name == 'int' and isinstance(value, (int, float)):
                cast_value.int = int(value)  # type: ignore
            elif name == 'float' and isinstance(value, float):
                cast_value.float = value  # type: ignore
            elif name == 'str':
                cast_value.str = str(value)  # type: ignore
            elif name == 'bool':
                cast_value.bool = bool(value)  # type: ignore
            elif name == 'uri' and isinstance(value, Uri):
                cast_value.uri = str(value)  # type: ignore
            elif name == 'ref' and isinstance(value, Ref):
                cast_value.ref = '@' + value.name  # type: ignore
            elif name == 'date' and isinstance(value, date):
                cast_value.date = value  # type: ignore
            elif name == 'date' and isinstance(value, datetime):
                cast_value.date = value.date()  # type: ignore
            elif name == 'time' and isinstance(value, time):
                cast_value.time = value  # type: ignore
            elif name == 'time' and isinstance(value, datetime):
                cast_value.time = value.time()  # type: ignore
            elif name == 'datetime' and isinstance(value, datetime):
                cast_value.datetime = value  # type: ignore
            elif name == 'coord' and isinstance(value, Coordinate):
                cast_value.coord = HSCoordinate(value.latitude, value.longitude)  # type: ignore
        return cast_value

    @staticmethod
    def _conv_history(entities: Grid, info: ResolveInfo):
        return [ReadHaystack._conv_value(entity, info) for entity in entities]

    @staticmethod
    def _filter_id(entity_id: str) -> str:
        if entity_id.startswith("r:"):
            return entity_id[2:]
        if entity_id.startswith('@'):
            return entity_id[1:]
        return entity_id

    @staticmethod
    def _conv_entity(target_class: Type, entity: Entity):
        entity_result = target_class()
        for key, val in entity.items():
            if key in entity:
                entity_result.__setattr__(key, val)
        return entity_result

    @staticmethod
    def _conv_list_to_object_type(target_class: Type, grid: Grid):
        result = []
        for row in grid:
            result.append(ReadHaystack._conv_entity(target_class, row))
        return result
