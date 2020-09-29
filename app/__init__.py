"""
A Flask layer to haystack interface.
"""
import os
import sys

import click
try:
    from flask import Flask, send_from_directory
except ImportError:
    print("To start haystackapi, use")
    print("pip install \"haystackapi[flask]\"")
    print("and set HAYSTACK_PROVIDER variable")
    print("HAYSTACK_PROVIDER=haystackapi.providers.ping haystackapi")
    sys.exit(-1)

from app.blueprint_haystack import haystack as haystack_blueprint

app = Flask(__name__)
app.register_blueprint(haystack_blueprint)


@app.route('/')
def index():
    return "Flask is up and running"


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@click.command()
@click.option('-h', '--host', default='0.0.0.0')
@click.option('-p', '--port', default=3000)
def main(host, port) -> int:
    debug = ("1" == os.environ.get("FLASK_DEBUG", "0"))
    app.run(host=host if not debug else 'localhost',
            port=port,
            debug=debug)
    return 0


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
