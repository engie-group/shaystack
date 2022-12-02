# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
A flask blueprint to manage Haystack API
"""
import os
from typing import Dict, cast

from flask import Blueprint, Response, send_from_directory
from flask import request as flash_request
from werkzeug.utils import safe_join  # type: ignore

from shaystack import \
    about, ops, formats, read, nav, watch_sub, \
    watch_unsub, watch_poll, point_write, his_read, his_write, invoke_action, HaystackInterface
from shaystack.ops import HaystackHttpRequest, HaystackHttpResponse


def create_haystack_bp(provider: HaystackInterface) -> Blueprint:

    # test if there is already a created provider and of the caching is enabled

    prefix = os.environ.get('URL_PREFIX') if os.environ.get('URL_PREFIX') else ''
    haystack_blueprint = Blueprint('haystack', __name__,
                                   static_folder=safe_join(os.path.dirname(__file__), 'haystackui'),
                                   url_prefix=f'{prefix}/haystack')

    @haystack_blueprint.route('/about', methods=['POST', 'GET'])
    def flask_about() -> Response:
        """Invoke about() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(about(envs, _as_request(flash_request), envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/ops', methods=['POST', 'GET'])
    def flask_ops() -> Response:
        """Invoke ops() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(ops(envs, _as_request(flash_request), envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/formats', methods=['POST', 'GET'])
    def flask_formats() -> Response:
        """Invoke formats() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(formats(envs, _as_request(flash_request),
                                    envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/read', methods=['POST', 'GET'])
    def flask_read() -> Response:
        """Invoke read() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(read(envs, _as_request(flash_request), envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/nav', methods=['POST', 'GET'])
    def flask_nav() -> Response:
        """Invoke nav() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(nav(envs, _as_request(flash_request), envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/watchSub', methods=['POST', 'GET'])
    def flask_watch_sub() -> Response:
        """Invoke watch_sub() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(watch_sub(envs, _as_request(flash_request),
                                      envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/watchUnsub', methods=['POST', 'GET'])
    def flask_watch_unsub() -> Response:
        """Invoke watch_unsub() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(watch_unsub(envs, _as_request(flash_request),
                                        envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/watchPoll', methods=['POST', 'GET'])
    def flask_watch_poll() -> Response:
        """Invoke watch_poll() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(watch_poll(envs, _as_request(flash_request),
                                       envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/pointWrite', methods=['POST', 'GET'])
    def flask_point_write() -> Response:
        """Invoke point_write() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(point_write(envs, _as_request(flash_request),
                                        envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/hisRead', methods=['POST', 'GET'])
    def flask_his_read() -> Response:
        """Invoke his_read() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(his_read(envs, _as_request(flash_request),
                                     envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/hisWrite', methods=['POST', 'GET'])
    def flask_his_write() -> Response:
        """Invoke his_write() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(his_write(envs, _as_request(flash_request),
                                      envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/invokeAction', methods=['POST', 'GET'])
    def flask_invoke_action() -> Response:
        """Invoke invoke_action() from flask.
        Returns:
            Flask HTTP response
        """
        envs = cast(Dict[str, str], os.environ)
        return _as_response(invoke_action(envs, _as_request(flash_request),
                                          envs.get("FLASK_ENV", "prod"), provider))

    @haystack_blueprint.route('/', methods=['GET'], defaults={'filename': 'index.html'})
    @haystack_blueprint.route('/<path:filename>', methods=['GET'])
    def flash_web_ui(filename) -> Response:
        if(os.environ.get('HAYSTACK_INTERFACE') and
                os.environ.get('HAYSTACK_INTERFACE') != ''
                and filename == 'plugins/customPlugin.js'):
            return send_from_directory(os.getcwd(), os.environ['HAYSTACK_INTERFACE'])
        return send_from_directory(haystack_blueprint.static_folder, filename)
    return haystack_blueprint


def _as_request(request: flash_request) -> HaystackHttpRequest:  # type: ignore
    """The interface must be similar to AWS Lambda events
    """
    haystack_request = HaystackHttpRequest()
    haystack_request.body = request.data  # type: ignore
    haystack_request.headers = flash_request.headers  # type: ignore
    haystack_request.args = flash_request.args
    return haystack_request


def _as_response(response: HaystackHttpResponse) -> Response:
    rep = Response()
    rep.status_code = response.status_code
    rep.headers = response.headers  # type: ignore
    rep.data = response.body
    return rep
