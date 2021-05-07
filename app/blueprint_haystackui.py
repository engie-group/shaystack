# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
A flask blueprint to manage Haystack Interface
"""
import os

from flask import Blueprint, Response, send_from_directory, safe_join

def initiate_haystackui_bp(name='haystackui'):
    return Blueprint(name, __name__,
                           static_folder=safe_join(os.path.dirname(__file__), 'haystackui'),
                           url_prefix='/haystack')

def create_haystackui_bp():
    haystackui_blueprint = initiate_haystackui_bp()
    @haystackui_blueprint.route('/', methods=['GET'], defaults={'filename': 'index.html'})
    @haystackui_blueprint.route('/<path:filename>', methods=['GET'])
    def flash_web_ui(filename) -> Response:
        if(os.environ.get('HAYSTACK_INTERFACE') and os.environ.get('HAYSTACK_INTERFACE')!='' and filename == 'plugins/customPlugin.js'):
            return send_from_directory(os.getcwd(), os.environ['HAYSTACK_INTERFACE'])
        else:
            return send_from_directory(haystackui_blueprint.static_folder, filename)
    return haystackui_blueprint