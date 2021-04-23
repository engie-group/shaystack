# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
A Flask layer to haystack interface.
"""
import sys

import click as click
from flask import Response

from app.__init__ import main as shaystack_main, haystack_blueprint
from app.blueprint_haystack import flash_web_ui as shaystack_flash_web_ui


@haystack_blueprint.route('/', methods=['GET'], defaults={'filename': 'index.html'})
@haystack_blueprint.route('/<path:filename>', methods=['GET'])
def flash_web_ui(filename) -> Response:
    if (filename == "extention.js"):
        pass  # ...
    else:
        return shaystack_flash_web_ui(filename)


@click.command()
@click.option('-h', '--host', default='localhost')
@click.option('-p', '--port', default=3000, type=int)
def main(host: str, port: int) -> int:
    return shaystack_main(host, port)


if __name__ == '__main__':
    sys.exit(main())  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
