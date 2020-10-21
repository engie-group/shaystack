"""
A top GraphQL query.

You can use a similar code to integrate the haystack graphql api in a bigger environment.
"""
import logging
import os
import sys

import click
import graphene
from flask import Blueprint
from flask_graphql import GraphQLView

from app.graphql_model import ReadHaystack

log = logging.getLogger("haystackapi")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))


class Query(graphene.ObjectType):
    class Meta:
        description = 'Top query'

    haystack = graphene.Field(ReadHaystack)

    @staticmethod
    def resolve_haystack(parent, info):
        return ReadHaystack()


schema = graphene.Schema(query=Query)

graphql_blueprint = Blueprint('graphql',
                              __name__,
                              url_prefix='/graphql')
gr_view = GraphQLView.as_view(
    'graphql',
    schema=schema,
    graphiql=True,
)
# gr_view.provide_automatic_options = False
# gr_view.methods=['GET', 'OPTIONS']
graphql_blueprint.add_url_rule('/',
                               view_func=gr_view)


def _dump_haystack_schema():
    """
    Print haystack schema to insert in another global schema.
    """
    # Print only haystack schema
    from graphql.utils import schema_printer
    print(schema_printer.print_schema(schema))


@click.command()
def main() -> int:
    """
    Print the partial schema for haystack API.
    `GRAPHQL_SCHEMA=app/haystack_schema.json python app/blueprint_graphql.py` >partial_gql.graphql
    """
    _dump_haystack_schema()
    return 0


if __name__ == '__main__':
    sys.exit(main())
