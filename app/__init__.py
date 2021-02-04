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

try:
    from flask import Flask, send_from_directory
    from flask_cors import CORS
    from app.blueprint_haystack import haystack_blueprint
except ImportError as ex:
    print('To start haystackapi, use \'pip install "haystackapi[flask]"\' or '
          '\'pip install "haystackapi[flask,graphql]"\' and set \'HAYSTACK_PROVIDER\' variable',
          file=sys.stderr)
    sys.exit(-1)

USE_GRAPHQL = False
try:
    import graphene  # pylint: disable=ungrouped-imports
    from app.blueprint_graphql import graphql_blueprint

    USE_GRAPHQL = True
except ImportError:
    print("To use GraphQL feature, use "
          "'pip install \"haystackapi[graphql]\"'", file=sys.stderr)
    sys.exit(-1)

app = Flask(__name__)
cors = CORS(app, resources={
    r"/haystack/*": {"origins": "*"},
    r"/graphql/*": {"origins": "*"}}, )

_log_level = os.environ.get("LOG_LEVEL", "WARNING")
logging.basicConfig(level=_log_level)
app.logger.setLevel(_log_level)  # pylint: disable=no-member
app.register_blueprint(haystack_blueprint)
if USE_GRAPHQL:
    app.register_blueprint(graphql_blueprint)


@app.route('/')
def index():
    """Empty page to check the deployment"""
    return "Flask is up and running"


@app.route('/favicon.ico')
def favicon():
    """Return the favorite icon"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@click.command()
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default=3000, type=int)
def main(host: str, port: int) -> int:
    """Stack a flask server. The command line must set the host and port.

    Args:
        host: Network to listen (0.0.0.0 to accept call from all network)
        port: Port to listen
    """
    if not "HAYSTACKAPI_PROVIDER" in os.environ:
        print("Set 'HAYSTACKAPI_PROVIDER' to use 'haystackapi'", file=sys.stderr)
        sys.exit(-1)

    debug = (os.environ.get("FLASK_DEBUG", "0") == "1")
    app.run(host=host,
            port=port,
            debug=debug)
    return 0


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
