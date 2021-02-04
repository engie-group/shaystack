# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
A top GraphQL query.

You can use a similar code to integrate the haystack graphql api in a bigger environment.
"""
import logging
import os
import sys

import click

try:
    from flask import Blueprint
    from flask_graphql import GraphQLView
except ImportError:
    os.abort()

import graphene
from .graphql_model import ReadHaystack

log = logging.getLogger("haystackapi")


class Query(graphene.ObjectType):
    """GraphQL haystack query. To integrate the haystack Graphql API with other
    GraphQL API, see `aws appsync` .
    """

    class Meta:  # pylint: disable=missing-class-docstring
        description = "Root for haystack api"

    haystack = graphene.Field(graphene.NonNull(ReadHaystack))

    @staticmethod
    def resolve_haystack(parent, info):
        """
        Args:
            parent:
            info:
        """
        return ReadHaystack()


schema = graphene.Schema(query=Query)

graphql_blueprint = Blueprint('graphql',
                              __name__,
                              url_prefix='/graphql')

graphql_blueprint.add_url_rule('',
                               view_func=GraphQLView.as_view(
                                   'graphql',
                                   schema=schema,
                                   graphiql=True,
                               ))


def _dump_haystack_schema() -> None:
    """Print haystack schema to insert in another global schema."""
    # Print only haystack schema
    from graphql.utils import schema_printer  # pylint: disable=import-outside-toplevel
    print(schema_printer.print_schema(schema))


@click.command()
def main() -> int:
    """Print the partial schema for haystack API.
    `GRAPHQL_SCHEMA=app/haystack_schema.json python app/blueprint_graphql.py`
    >partial_gql.graphql
    """
    _dump_haystack_schema()
    return 0


if __name__ == '__main__':
    sys.exit(main())
