"""
Model to inject a another graphene model, to manage the haystack layer.
See the blueprint_graphql to see how to integrate this part of global GraphQL model.
"""
import logging
from datetime import datetime
from typing import Optional, List

import graphene
from graphql.language import ast

import hszinc
from haystackapi.providers.haystack_interface import get_singleton_provider, parse_date_range
from hszinc import Ref

BOTO3_AVAILABLE = False
try:
    import boto3
    from botocore.client import BaseClient

    BOTO3_AVAILABLE = True
except ImportError:
    pass

log = logging.getLogger("haystackapi")


# PPR: see the batch approch
# WARNING: At this time only public endpoints are supported by AWS AppSync

class HSScalar(graphene.Scalar):
    '''Haystack Scalar'''

    class Meta:
        name = "AWSJSON" if BOTO3_AVAILABLE else "JSONString"

    @staticmethod
    def serialize(hs_scalar):
        return hszinc.dump_scalar(hs_scalar, hszinc.MODE_JSON, version=hszinc.VER_3_0)

    @staticmethod
    # Parse from AST See https://tinyurl.com/y3fr76a4
    def parse_literal(node):
        if isinstance(node, ast.StringValue):  # FIXME: parse_literal in GraphQL API
            return f"node={node}"

    @staticmethod
    # Parse form json
    def parse_value(value):
        return f"parse_value={value}"  # FIXME: parse_value in GraphQL API


class HSDate(graphene.String):
    class Meta:
        name = "AWSDate" if BOTO3_AVAILABLE else "Date"

    pass


class HSTime(graphene.String):
    class Meta:
        name = "AWSTime" if BOTO3_AVAILABLE else "HSTime"

    pass


class HSDateTime(graphene.String):
    # class Meta:
    #     name = "AWSDateTime" if BOTO3_AVAILABLE else "DateTime"
    class Meta:
        name = "String"

    pass


class HSUri(graphene.String):
    class Meta:
        name = "AWSURL" if BOTO3_AVAILABLE else "HSURL"


class HSAbout(graphene.ObjectType):
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


class HSOps(graphene.ObjectType):
    """Result of 'ops' haystack operation"""

    name = graphene.String(description="Name of operation (see https://project-haystack.org/doc/Ops)")
    summary = graphene.String(description="Summary of operation")


class HSTS(graphene.ObjectType):
    """Result of 'hisRead' haystack operation"""
    date = graphene.Field(HSDateTime,
                          description="Date time of event")
    val = graphene.Field(HSScalar,
                         description="Value of event with unit")


class HSPointWrite(graphene.ObjectType):
    """Result of 'pointWrite' haystack operation"""
    level = graphene.Int(description="Current level")
    levelDis = graphene.String(description="Description of level")
    val = graphene.Field(HSScalar, description="Value")
    who = graphene.String(description="Who has updated the value")


# PPR: see the batch approch
class ReadHaystack(graphene.ObjectType):
    """ Ontology conform with Haystack project """

    class Meta:
        name = "Haystack"

    about = graphene.NonNull(HSAbout,
                             description="Versions of api")

    ops = graphene.NonNull(graphene.List(
        graphene.NonNull(HSOps)),
        description="List of operation implemented")

    tag_values = graphene.NonNull(graphene.List(graphene.NonNull(HSScalar),
                                                tag=graphene.String(required=True,
                                                                    description="Tag name"),
                                                version=HSDateTime(description="Date of the version "
                                                                               "or nothing for the last version")
                                                ),
                                  description="All values for a specific tag")

    versions = graphene.NonNull(graphene.List(graphene.NonNull(HSDateTime)),
                                description="All versions of datas")

    entities = graphene.List(
        graphene.NonNull(HSScalar),
        ids=graphene.List(graphene.ID,
                          description="List of ids to return (if set, ignore filter and limit)"),
        select=graphene.String(default_value='*',
                               description="List of tags to return"),
        limit=graphene.Int(default_value=0,
                           description="Maximum number of items to return"),
        filter=graphene.String(default_value='',
                               description="Filter or item (see https://project-haystack.org/doc/Filters"),
        version=HSDateTime(description="Date of the version or nothing for the last version"),
        description="Selected entities of ontology"
    )

    histories = graphene.List(graphene.NonNull(graphene.List(graphene.NonNull(HSScalar))),
                              ids=graphene.List(graphene.ID,
                                                description="List of ids to return"),
                              dates_range=graphene.String(description="today, yesterday, "
                                                                      "{date}, {date},{date}, "
                                                                      "{datetime}, "
                                                                      "{datetime},{datetime}"
                                                          ),
                              version=HSDateTime(description="Date of the version or nothing for the last version"),
                              description="Selected time series")

    # Retourne une liste, car on ne peut pas avoir de paramètres sur les scalar
    point_write = graphene.List(
        graphene.NonNull(HSPointWrite),
        id=graphene.ID(required=True,
                       description="Id to read (accept @xxx, r:xxx or xxx)"),
        version=HSDateTime(description="Date of the version or nothing for the last version"),
        description="Point write values"
    )

    @staticmethod
    def resolve_about(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().about("http://localhost")
        rc = ReadHaystack._conv_entity(HSAbout, grid[0])
        rc.serverTime = grid[0]["serverTime"].isoformat()
        rc.bootTime = grid[0]["bootTime"].isoformat()
        return rc

    @staticmethod
    def resolve_ops(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().ops()
        return ReadHaystack._conv_list_to_object_type(HSOps, grid)

    @staticmethod
    def resolve_tag_values(parent, info, tag: str, version: Optional[datetime] = None):
        log.debug("resolve_values(parent,info,%s)", tag)
        return get_singleton_provider().values_for_tag(tag, version)

    @staticmethod
    def resolve_versions(parent, info):
        log.debug("resolve_versions(parent,info)")
        return get_singleton_provider().versions()

    @staticmethod
    def resolve_entities(parent, info,
                         ids: Optional[List[str]] = None,
                         select: str = '*',
                         filter: str = '',
                         limit: int = 0,
                         version: Optional[datetime] = None):
        log.debug(f"resolve_entities(parent,info,ids={ids}, query={filter}, limit={limit}, datetime={datetime})")
        if ids:
            ids = [Ref(ReadHaystack._filter_id(id)) for id in ids]
        grid = get_singleton_provider().read(limit, select, ids, filter, version)
        return grid

    @staticmethod
    def resolve_histories(parent, info,
                          ids: Optional[List[str]] = None,
                          dates_range: Optional[str] = None,
                          version: Optional[datetime] = None):
        log.debug(f"resolve_histories(parent,info,id={id}, range={range}, datetime={datetime})")
        grid_date_range = parse_date_range(dates_range)
        return [get_singleton_provider().his_read(Ref(ReadHaystack._filter_id(id)), grid_date_range, version)
                for id in ids]

    @staticmethod
    def resolve_point_write(parent, info,
                            id: str,
                            version: Optional[datetime] = None):
        log.debug(f"resolve_point_write(parent,info, id={id}, version={version})")
        ref = Ref(ReadHaystack._filter_id(id))
        grid = get_singleton_provider().point_write_read(ref, version)
        return ReadHaystack._conv_list_to_object_type(HSPointWrite, grid)

    @staticmethod
    def _filter_id(id: str) -> str:
        if id.startswith("r:"):
            return id[2:]
        if id.startswith('@'):
            return id[1:]
        return id

    @staticmethod
    def _conv_entity(cls, entity):
        entity_result = cls()
        for key, val in entity.items():
            if key in entity:
                entity_result.__setattr__(key, val)
        return entity_result

    @staticmethod
    def _conv_list_to_object_type(cls, grid):
        result = []
        for row in grid:
            result.append(ReadHaystack._conv_entity(cls, row))
        return result
