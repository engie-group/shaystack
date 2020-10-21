import logging
import os
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Optional, List

import graphene
from graphene import Scalar, Node
from graphql.language import ast

import hszinc
from haystackapi.providers.haystack_interface import get_singleton_provider
from hszinc import Ref, MODE_JSON

log = logging.getLogger("haystackapi")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))


# L'idée est d'avoir des valeurs avec typage, pour éviter les ambiguités
# C'est au client d'en tenir compte.

# Une autre idée est de produire un type "compatible" GraphQL/Json, mais on perd de l'info.

class _HSKind(Scalar):
    serialize = partial(hszinc.dump_scalar, mode=hszinc.MODE_JSON, version=hszinc.VER_3_0)

    # Parse from AST See https://tinyurl.com/y3fr76a4
    def parse_literal(node: Node):
        if isinstance(node, ast.StringValue):  # FIXME
            return hszinc.dump_scalar(ast.value, mode=hszinc.MODE_JSON, version=hszinc.VER_3_0)

    # Parse form json
    # FIXME parse_value = partial(hszinc.dump_scalar, mode=hszinc.MODE_JSON, version=hszinc.VER_3_0)
    def parse_value(value):
        return f"parse_value={value}"  # FIXME


class HSMarker(_HSKind):
    class Meta:
        description = "Haystack marker"


class HSBool(_HSKind):
    class Meta:
        description = "Haystack bool"


class HSNA(_HSKind):
    class Meta:
        description = "Haystack NA"


class HSNumber(_HSKind):
    class Meta:
        description = "Haystack Number with unit"


class HSStr(graphene.String):
    class Meta:
        description = "Haystack str"


class HSUri(_HSKind):
    class Meta:
        description = "Haystack uri"


class HSRef(_HSKind):
    class Meta:
        description = "Haystack reference"


class HSBin(_HSKind):
    class Meta:
        description = "Haystack bin"


class HSDate(_HSKind):
    class Meta:
        description = "Haystack date"


class HSTime(_HSKind):
    class Meta:
        description = "Haystack time"


class HSDateTime(_HSKind):
    class Meta:
        description = "Haystack DateTime"


class HSCoord(_HSKind):
    class Meta:
        description = "Haystack Coord"


class HSXStr(_HSKind):
    class Meta:
        description = "Haystack XStr"


class HSList(graphene.JSONString):
    class Meta:
        description = "Haystack List"


class HSDict(graphene.JSONString):
    class Meta:
        description = "Haystack dict"


class HSGrid(graphene.JSONString):
    class Meta:
        description = "Haystack grid"


class XEntity(graphene.ObjectType):
    id = graphene.Field(HSRef)
    site = graphene.Field(HSMarker)
    dis = graphene.String()
    toto = graphene.Field(_HSKind)


def _hskind_to_grafene(kind: str) -> str:
    kind = kind.lower()
    if kind == "marker":
        return "graphene.Field(HSMarker)"
    if kind == "bool":
        return "graphene.Field(HSBool)"
    if kind == "na":
        return "graphene.Field(HSNA)"
    if kind == "number":
        return "graphene.Field(HSNumber)"
    if kind == "str":
        return "graphene.String()"
    if kind == "uri":
        return "graphene.Field(HSUri)"
    if kind == "ref":
        return "graphene.Field(HSRef)"
    if kind == "bin":
        return "graphene.Field(HSBin)"
    if kind == "date":
        return "graphene.Field(HSDate)"
    if kind == "time":
        return "graphene.Field(HSTime)"
    if kind == "datetime":
        return "graphene.Field(HSDateTime)"
    if kind == "coord":
        return "graphene.Field(HSCoord)"
    if kind == "xstr":
        return "graphene.Field(HSXStr)"
    if kind == "list":
        return "graphene.Field(HSList)"
    if kind == "dict":
        return "graphene.Field(HSDict)"
    if kind == "grid":
        return "graphene.Field(HSGrid)"
    if kind == "obj":
        return "graphene.Field(_HSKind)"
    assert False, f"Invalid {kind}"


# FIXME: voir import
def reserve_word(col: str) -> str:
    if col in ("import", "def", "if"):  # FIXME
        col = col + "_"


def generate_entity_from_schema(filename: Path):
    with open(filename) as f:
        schema = hszinc.parse(f.read(), MODE_JSON)
    body = [f"\t{col} = {_hskind_to_grafene(meta['kind'])}" for col, meta in schema.column.items()]
    entity_source_code = "class Entity(graphene.ObjectType):\n" + "\n".join(body)
    # print(entity_source_code)
    exec(entity_source_code, globals(), locals())
    return locals()['Entity']


Entity = generate_entity_from_schema(Path("tests/marriott_schema.json"))


# FIXME Entity = generate_entity_from_schema(Path("tests/haystack_schema.json"))

class About(graphene.ObjectType):
    haystackVersion = graphene.String()
    tz = graphene.String()
    serverName = graphene.String()
    serverTime = graphene.Field(HSTime)
    serverBootTime = graphene.Field(HSTime)
    productName = graphene.String()
    productUri = graphene.Field(HSUri)
    productVersion = graphene.String()
    moduleName = graphene.String()
    moduleVersion = graphene.String()


class ReadHaystack(graphene.ObjectType):
    class Meta:
        description = 'Ontology conform with Haystack project'
        name = "Haystack"

    about = graphene.List(
        graphene.NonNull(About),
    )

    read = graphene.List(
        graphene.NonNull(Entity),
        ids=graphene.List(graphene.ID),
        filter=graphene.String(default_value=''),
        limit=graphene.Int(default_value=0),
        version=graphene.DateTime()
    )

    @staticmethod
    def resolve_about(parent, info):
        log.debug(f"resolve_about(parent,info)")
        grid = get_singleton_provider().about("dev")  # FIXME: dev
        result = []
        for row in grid:
            about = About()
            for key, val in row.items():
                if key in about.__dict__:
                    about.__setattr__(key, val)
            result.append(about)
        return result

    # @staticmethod
    # def resolve_ops(parent, info):
    #     log.debug(f"resolve_about(parent,info)")
    #     grid = get_singleton_provider().ops()
    #     return [[HSTag(name, val) for name, val in entity.items()] for entity in grid]

    @staticmethod
    def resolve_read(parent, info,
                     ids: Optional[List[str]] = None,
                     filter: str = '',
                     limit: int = 0,
                     version: Optional[datetime] = None):
        log.debug(f"resolve_haystack(parent,info,ids={ids}, filter={filter}, limit={limit}, datetime={datetime})")
        # Extraction des fields à récuperer
        field_selected = [field.name.value for field in info.field_asts[0].selection_set.selections]
        # FIXME: modifier type de select pour avoir directement un liste ?
        select = ",".join(field_selected)
        if ids:
            ids = [Ref(ReadHaystack._filter_id(id)) for id in ids]
        grid = get_singleton_provider().read(limit, select, ids, filter, version)
        # FIXME: normalement Entity(**grid[0])
        # return [ Entity(*row) for row in grid]
        result = []
        for row in grid:
            entity = Entity()
            for key, val in row.items():
                if key in entity.__dict__:
                    entity.__setattr__(key, val)
            result.append(entity)
        return result

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


def dump_graphql_schema():
    # Print only haystack schema
    from graphql.utils import schema_printer
    print(schema_printer.print_schema(graphene.Schema(query=ReadHaystack)))


result = hs_schema.execute('''
{ 
    # haystack(select: "id,dis"ids: ["@customer-913"])
    haystack 
    {
        about {
            haystackVersion
            tz
            serverName
            serverTime
            serverBootTime
            productName
            productUri
            productVersion
            moduleName
            moduleVersion
        }
#         ops 
#         {
#             name
#             value
#         }
#         read(filter: "site", limit: 2)
#         { 
#             site
#             dis
#         }
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
# dump_graphql_schema()
print("result = " + str(result.data))
print("error = " + str(result.errors))

