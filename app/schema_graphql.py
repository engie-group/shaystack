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
import graphene

from shaystack import HaystackInterface
from shaystack.providers import get_provider
from app.graphql_model import ReadHaystack  # type: ignore

log = logging.getLogger("shaystack")


# noinspection PyTypeChecker

def get_schema_for_provider(provider: HaystackInterface) -> graphene.types.schema.Schema:
    class Query(graphene.ObjectType):
        """GraphQL haystack query. To integrate the haystack Graphql API with other
        GraphQL API, see `aws appsync` .
        """

        class Meta:  # pylint: disable=missing-class-docstring
            description = "Root for haystack api"

        haystack = graphene.Field(graphene.NonNull(ReadHaystack))

        # noinspection PyUnusedLocal
        @staticmethod
        def resolve_haystack(parent, info):
            """
            Args:
                parent:
                info:
            """
            return ReadHaystack(provider)

    return graphene.Schema(query=Query)


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
