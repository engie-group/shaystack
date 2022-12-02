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

from shaystack import HaystackInterface
from shaystack.providers import get_provider
from app.schema_graphql import get_schema_for_provider

try:
    from flask import Blueprint
    from graphql_server.flask import GraphQLView
except ImportError:
    os.abort()

log = logging.getLogger("shaystack")


# noinspection PyTypeChecker
def create_graphql_bp(provider: HaystackInterface) -> Blueprint:
    schema = get_schema_for_provider(provider)
    graphql_blueprint = Blueprint('graphql',
                                  __name__,
                                  url_prefix='/graphql')
    graphql_blueprint.add_url_rule('',
                                   view_func=GraphQLView.as_view(
                                       'graphql',
                                       schema=schema.graphql_schema,
                                       graphiql=True,
                                   ))
    return graphql_blueprint


def _dump_haystack_schema(provider) -> None:
    """Print haystack schema to insert in another global schema."""
    # Print only haystack schema
    from graphql.utilities import print_schema
    schema = get_schema_for_provider(provider)

    print(print_schema(schema.graphql_schema))


@click.command()
def main() -> int:
    """Print the partial schema for haystack API.
    `GRAPHQL_SCHEMA=app/haystack_schema.json python app/blueprint_graphql.py`
    >partial_gql.graphql
    """
    provider_name = os.environ.get("HAYSTACK_PROVIDER", "shaystack.providers.db")
    provider = get_provider(provider_name, dict(os.environ))
    _dump_haystack_schema(provider)
    return 0


if __name__ == '__main__':
    sys.exit(main())
