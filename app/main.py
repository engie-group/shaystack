# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
A Flask layer to haystack interface.
"""
import logging
import os
import sys

import click
from flask import Flask, send_from_directory

from shaystack.providers import get_provider

try:
    from flask_cors import CORS
    from app.blueprint_haystack import create_haystack_bp
except ImportError as ex:
    print('To start shift-4-haystack, use \'pip install "shaystack[flask]"\' or '
          '\'pip install "shaystack[flask,graphql]"\' and set \'HAYSTACK_PROVIDER\' variable',
          file=sys.stderr)
    sys.exit(-1)

USE_GRAPHQL = False
try:
    import graphene  # pylint: disable=unused-import
    from app.blueprint_graphql import create_graphql_bp  # pylint: disable=ungrouped-imports

    USE_GRAPHQL = True
except ImportError:
    USE_GRAPHQL = False

_log_level = os.environ.get("LOG_LEVEL", "WARNING")
logging.basicConfig(level=_log_level)


def init_app(app: Flask) -> Flask:
    @app.route('/')
    def index():
        """Empty page to check the deployment"""
        redirect_js = """
        <script>
        if (! window.location.pathname.toString().endsWith("/")) {
          document.location.href=window.location+"/"; 
        }
        </script>
        """
        if USE_GRAPHQL:
            return f"""
                {redirect_js}
                <body>
                <a href="haystack">Haystack API</a><br />
                <a href="graphql">Haystack GraphQL API</a><br />
                </body>
                """
        return f"""
            {redirect_js}
            <body>
            <a href="haystack">Haystack API</a><br />
            </body>
            """

    @app.route('/favicon.ico')
    def favicon():
        """Return the favorite icon"""
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

    app.logger.setLevel(_log_level)  # pylint: disable=no-member
    return app


def add_blueprints(app: Flask) -> Flask:
    provider_name = os.environ.get("HAYSTACK_PROVIDER", "shaystack.providers.db")
    provider = get_provider(provider_name, dict(os.environ))
    app.register_blueprint(create_haystack_bp(provider))
    if USE_GRAPHQL:
        app.register_blueprint(create_graphql_bp(provider))
    CORS(app, resources={
        r"/haystack/*": {"origins": "*"},
        r"/graphql/*": {"origins": "*"}}, )
    return app


def create_app() -> Flask:
    return add_blueprints(init_app(Flask(__name__)))


def start_shaystack(host: str, port: int, app: Flask) -> int:
    """Stack a flask server. The command line must set the host and port.

    Args:

        app: Flask app instance
        host: Network to listen (0.0.0.0 to accept call from all network)
        port: Port to listen

    Envs:

        HAYSTACK_PROVIDER: to select a provider (shaystack.providers.db)
        HAYSTACK_DB: the URL to select the backend with the ontology
    """
    debug = (os.environ.get("FLASK_DEBUG", "0") == "1")
    app.run(host=host,
            port=port,
            debug=debug)
    return 0


app_instance = create_app()


@click.command()
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default=3000, type=int)
def main(host, port):
    return start_shaystack(host, port, app_instance)


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
