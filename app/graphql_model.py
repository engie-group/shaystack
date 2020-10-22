"""
Model to inject a another graphene model, to manage the haystack layer.
See the blueprint_graphql to see how to integrate this part of global GraphQL model.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional, List

import click
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

# Alias of AWS scalar type (see https://docs.aws.amazon.com/appsync/latest/devguide/scalars.html)
class AWSDate(graphene.Date):
    pass


class AWSTime(graphene.Time):
    pass


class AWSDateTime(graphene.DateTime):
    pass


# class AWSTimestamp(graphene.String):
#     pass


class AWSJSON(graphene.JSONString):
    pass


class AWSURL(graphene.String):
    pass


class AWSPhone(graphene.String):
    pass


class AWSIPAddress(graphene.String):
    pass


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


# TODO: ajouter un filter sur le name ? name(q="site") ?
class HSTag(graphene.ObjectType):
    # FIXME: Add primary key to auto-save ?
    name = graphene.String()
    value = graphene.Field(HSScalar)


# TODO: voir l'approche Batch
class ReadHaystack(graphene.ObjectType):
    class Meta:
        description = 'Ontology conform with Haystack project'
        name = "Haystack"

    # TODO: values_for_tag
    about = graphene.List(
        graphene.NonNull(graphene.List(graphene.NonNull(HSTag))),
    )

    ops = graphene.List(
        graphene.NonNull(graphene.List(graphene.NonNull(HSTag))),
    )

    # TODO: voir comment en faire une classe et réorganiser le code
    # TODO: proxy Appsync https://stackoverflow.com/questions/60361326/proxy-request-to-graphql-server-through-aws-appsync
    # TODO: wrapper all values for tag
    read = graphene.List(
        graphene.NonNull(graphene.List(graphene.NonNull(HSTag))),
        ids=graphene.List(graphene.ID),
        select=graphene.String(default_value='*'),
        filter=graphene.String(default_value=''),
        limit=graphene.Int(default_value=0),
        version=HSScalar()
    )

    his_read = graphene.List(
        graphene.NonNull(graphene.List(graphene.NonNull(HSTag))),
        id=graphene.ID(required=True),
        dates_range=graphene.String(),
        version=HSScalar()
    )

    point_write = graphene.List(
        graphene.NonNull(graphene.List(graphene.NonNull(HSTag))),
        id=graphene.ID(required=True),
        version=HSScalar()
    )

    @staticmethod
    def resolve_about(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().about("dev")  # FIXME: dev
        return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

    @staticmethod
    def resolve_ops(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().ops()
        return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

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
        return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

    @staticmethod
    def resolve_his_read(parent, info,
                         id: str,
                         dates_range: Optional[str] = None,
                         version: Optional[datetime] = None):
        log.debug(f"resolve_his_read(parent,info,id={id}, range={range}, datetime={datetime})")
        ref = Ref(ReadHaystack._filter_id(id))
        grid_date_range = parse_date_range(dates_range)
        grid = get_singleton_provider().his_read(ref, grid_date_range, version)
        # FIXME: format des TS
        return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

    @staticmethod
    def resolve_point_write(parent, info,
                            id: str,
                            version: Optional[datetime] = None):
        log.debug(f"resolve_point_write(parent,info, {id})")
        ref = Ref(ReadHaystack._filter_id(id))
        grid = get_singleton_provider().point_write_read(ref, version)
        return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

    @staticmethod
    def _filter_id(id: str) -> str:
        if id.startswith("r:"):
            return id[2:]
        if id.startswith('@'):
            return id[1:]
        return id


def _dump_haystack_schema():
    """
    Print haystack schema to insert in another global schema.
    """
    # Print only haystack schema
    from graphql.utils import schema_printer
    print(schema_printer.print_schema(graphene.Schema(query=ReadHaystack)))


@click.command()
def main() -> int:
    """
    Print the partial schema for haystack API.
    `GRAPHQL_SCHEMA=app/haystack_schema.json python app/graphql_model.py` >partial_gql.graphql
    """
    _dump_haystack_schema()
    return 0


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
