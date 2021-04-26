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
    from flask import Flask, send_from_directory, request, redirect
    from flask_cors import CORS
except ImportError as ex:
    print('Fail installing flask',
          file=sys.stderr)
    sys.exit(-1)

from app.blueprint_haystackui import haystackui_blueprint

app = Flask(__name__)
cors = CORS(app, resources={
    r"/haystack/*": {"origins": "*"},
})
_log_level = os.environ.get("LOG_LEVEL", "WARNING")
logging.basicConfig(level=_log_level)
app.logger.setLevel(_log_level)  # pylint: disable=no-member
app.register_blueprint(haystackui_blueprint)


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

    Envs:

        HAYSTACK_PROVIDER: to select a provider (shaystack.providers.db)
        HAYSTACK_DB: the URL to select the backend with the ontology
    """
    debug = (os.environ.get("FLASK_DEBUG", "0") == "1")
    app.run(host=host,
            port=port,
            debug=debug)
    return 0


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
