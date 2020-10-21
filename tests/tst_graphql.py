import logging
import os
from datetime import datetime
from typing import Optional, List

import graphene
from graphene import Scalar
from graphql.language import ast
from graphql.utils import schema_printer

import hszinc
from haystackapi.providers.haystack_interface import get_singleton_provider
from hszinc import Ref

log = logging.getLogger("haystackapi")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))

class HSRef(Scalar):
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


class HSMarker(Scalar):
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

class Entity(graphene.ObjectType):
    id = graphene.Field(HSRef)
    site = graphene.Field(HSMarker)
    dis = graphene.String()


class ReadHaystack(graphene.ObjectType):
    class Meta:
        description = 'Ontology conform with Haystack project'
        name = "Haystack"

    read = graphene.List(
        graphene.NonNull(Entity),
        ids=graphene.List(graphene.ID),
        select=graphene.String(default_value='*'),
        filter=graphene.String(default_value=''),
        limit=graphene.Int(default_value=0),
        version=graphene.DateTime()
    )

    # @staticmethod
    # def resolve_about(parent, info):
    #     log.debug(f"resolve_about(parent,info)")
    #     grid = get_singleton_provider().about("dev")  # FIXME: dev
    #     return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]
    #
    # @staticmethod
    # def resolve_ops(parent, info):
    #     log.debug(f"resolve_about(parent,info)")
    #     grid = get_singleton_provider().ops()
    #     return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

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
        entity = Entity()
        entity.dis = "hello"
        # return [Entity([HSTag(name, val) for name, val in entity.items()] for entity in grid]
        return [entity]

    # @staticmethod
    # def resolve_his_read(parent, info,
    #                      id: str,
    #                      dates_range: Optional[str] = None,
    #                      version: Optional[datetime] = None):
    #     log.debug(f"resolve_his_read(parent,info,id={id}, range={range}, datetime={datetime})")
    #     ref = Ref(ReadHaystack._filter_id(id))
    #     grid_date_range = parse_date_range(dates_range)
    #     grid = get_singleton_provider().his_read(ref, grid_date_range, version)
    #     # FIXME: format des TS
    #     return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]
    #
    # @staticmethod
    # def resolve_point_write(parent, info,
    #                         id: str,
    #                         version: Optional[datetime] = None):
    #     log.debug(f"resolve_point_write(parent,info, {id})")
    #     ref = Ref(ReadHaystack._filter_id(id))
    #     grid = get_singleton_provider().point_write_read(ref, version)
    #     return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

    @staticmethod
    def _filter_id(id: str) -> str:
        if id.startswith("r:"):
            return id[2:]
        if id.startswith('@'):
            return id[1:]
        return id


# TODO: WriteHaystack avec point_write_write et his_write

class Query(graphene.ObjectType):
    class Meta:
        description = 'Top query'

    haystack = graphene.Field(ReadHaystack)

    @staticmethod
    def resolve_haystack(parent, info):
        return ReadHaystack()


hs_schema = graphene.Schema(query=Query)
result = hs_schema.execute('''
{ 
    # haystack(select: "id,dis"ids: ["@customer-913"])
    haystack 
    {
        # about 
        # {
        #     name
        #     value
        # }
#         ops 
#         {
#             name
#             value
#         }
#         read(select: "id,dis" filter: "id", limit: 2)
       read
        { 
            site
            dis
        }
#         hisRead(id:"@elec-16514")
#         {
#             name
#             value
#         }
#         pointWrite(id:"@elec-16514")
#         {
#             name
#             value
#         }
    }
}
''')
print(schema_printer.print_schema(hs_schema))
print("result = " + str(result.data))
print("error = " + str(result.errors))
