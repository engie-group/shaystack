"""
Model to inject a another graphene model, to manage the haystack layer.
See the blueprint_graphql to see how to integrate this part of global GraphQL model.
"""
import logging
import os
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
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))


# TODO: voir la batch approche
# PPR: autre modèle possible, retourner un JSon, valide partout
# WARNING: At this time only public endpoints are supported by AWS AppSync

# ---------------
# AWS Scalar : https://docs.aws.amazon.com/appsync/latest/devguide/scalars.html
# TODO: utiliser les parametres dans l'URL en plus du POST ?
# Dans Zappa, il faut ajouter un handler Voir page 320
# pour voir le event envoyé à la lambda par AppSync.
# Il faut probablement ajouter un handler spécifique.
# Voir page 317 https://docs.aws.amazon.com/appsync/latest/devguide/appsync-dg.pdf
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
        if isinstance(node, ast.StringValue):  # FIXME
            return f"node={node}"

    @staticmethod
    # Parse form json
    def parse_value(value):
        return f"parse_value={value}"  # FIXME


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
    class Meta:
        description = "Result of 'about' haystack operation"

    haystackVersion = graphene.String(required=True)  # TODO: auto require pour les HSType ?
    tz = graphene.String(required=True)
    serverName = graphene.String(required=True)
    serverTime = graphene.Field(graphene.NonNull(HSDateTime))
    serverBootTime = graphene.Field(graphene.NonNull(HSDateTime))
    productName = graphene.String(required=True)
    productUri = graphene.Field(graphene.NonNull(HSUri))
    productVersion = graphene.String(required=True)
    moduleName = graphene.String(required=True)
    moduleVersion = graphene.String(required=True)


class HSOps(graphene.ObjectType):
    class Meta:
        description = "Result of 'ops' haystack operation"

    name = graphene.String()
    summary = graphene.String()


class HSTS(graphene.ObjectType):
    class Meta:
        description = "Result of 'hisRead' haystack operation"

    date = graphene.Field(HSDateTime)
    val = graphene.Field(HSScalar)


class PointWrite(graphene.ObjectType):
    class Meta:
        description = "Result of 'pointWrite' haystack operation"

    level = graphene.Int()
    levelDis = graphene.String()
    val = graphene.Field(HSScalar)
    who = graphene.String()


# TODO: voir l'approche Batch
class ReadHaystack(graphene.ObjectType):
    class Meta:
        description = 'Ontology conform with Haystack project'
        name = "Haystack"

    values = graphene.List(graphene.NonNull(HSScalar),
                           tag=graphene.String(required=True),
                           version=HSDateTime()
                           )

    about = graphene.NonNull(HSAbout)

    ops = graphene.NonNull(graphene.List(
        graphene.NonNull(HSOps)))

    read = graphene.List(
        graphene.NonNull(HSScalar),
        ids=graphene.List(graphene.ID),
        select=graphene.String(default_value='*'),
        limit=graphene.Int(default_value=0),
        filter=graphene.String(default_value=''),
        version=HSDateTime()
    )

    his_read = graphene.Field(graphene.NonNull(HSScalar),
                              id=graphene.ID(required=True),
                              dates_range=graphene.String(),
                              version=HSDateTime()
                              )

    # Retourne une liste, car on ne peut pas avoir de paramètres sur les scalar
    point_write = graphene.List(
        graphene.NonNull(PointWrite),
        id=graphene.ID(required=True),
        version=HSDateTime()
    )

    @staticmethod
    def resolve_values(parent, info, tag: str, version: Optional[datetime] = None):
        log.debug("resolve_values(parent,info,%s)", tag)
        return get_singleton_provider().values_for_tag(tag, version)

    @staticmethod
    def resolve_about(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().about("http://localhost")  # FIXME
        rc = ReadHaystack._conv_entity(HSAbout, grid[0])
        # FIXME rc.serverTime=grid[0]["serverTime"].isoformat()
        # rc.bootTime=grid[0]["bootTime"].isoformat()
        return rc

    @staticmethod
    def resolve_ops(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().ops()
        return ReadHaystack._conv_list_to_object_type(HSOps, grid)

    @staticmethod
    def resolve_read(parent, info,
                     ids: Optional[List[str]] = None,
                     select: str = '*',
                     filter: str = '',
                     limit: int = 0,
                     version: Optional[datetime] = None):
        log.debug(f"resolve_haystack(parent,info,ids={ids}, query={filter}, limit={limit}, datetime={datetime})")
        if ids:
            ids = [Ref(ReadHaystack._filter_id(id)) for id in ids]
        grid = get_singleton_provider().read(limit, select, ids, filter, version)
        return grid

    @staticmethod
    def resolve_his_read(parent, info,
                         id: str,
                         dates_range: Optional[str] = None,
                         version: Optional[datetime] = None):
        log.debug(f"resolve_his_read(parent,info,id={id}, range={range}, datetime={datetime})")
        ref = Ref(ReadHaystack._filter_id(id))
        grid_date_range = parse_date_range(dates_range)
        grid_ts = get_singleton_provider().his_read(ref, grid_date_range, version)
        return list(grid_ts)

    @staticmethod
    def resolve_point_write(parent, info,
                            id: str,
                            version: Optional[datetime] = None):
        log.debug(f"resolve_point_write(parent,info, id={id}, version={version})")
        ref = Ref(ReadHaystack._filter_id(id))
        grid = get_singleton_provider().point_write_read(ref, version)
        return ReadHaystack._conv_list_to_object_type(PointWrite, grid)

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
