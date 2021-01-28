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

from flask import Blueprint, Response
from flask import request as flash_request

# from werkzeug.local import LocalProxy
# log = LocalProxy(lambda: current_app.logger)
from haystackapi import \
    about, ops, formats, read, nav, watch_sub, \
    watch_unsub, watch_poll, point_write, his_read, his_write, invoke_action
from haystackapi.ops import HaystackHttpRequest, HaystackHttpResponse

haystack_blueprint = Blueprint('haystack', __name__,
                               static_folder='app/static',
                               url_prefix='/haystack')


def _as_request(request: flash_request) -> HaystackHttpRequest:
    """The interface must be similare to AWS Lambda events

    Args:
        request (flash_request):
    """
    haystack_request = HaystackHttpRequest()
    haystack_request.body = request.data
    haystack_request.headers = flash_request.headers
    haystack_request.args = flash_request.args
    return haystack_request


def _as_response(response: HaystackHttpResponse) -> Response:
    """
    Args:
        response (HaystackHttpResponse):
    """
    rep = Response()
    rep.status_code = response.status_code
    rep.headers = response.headers
    rep.data = response.body
    return rep


@haystack_blueprint.route('/about', methods=['POST', 'GET'])
def flask_about() -> Response:
    """Invoke about() from flask"""
    return _as_response(about(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/ops', methods=['POST', 'GET'])
def flask_ops() -> Response:
    """Invoke ops() from flask"""
    return _as_response(ops(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/formats', methods=['POST', 'GET'])
def flask_formats() -> Response:
    """Invoke formats() from flask"""
    return _as_response(formats(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/read', methods=['POST', 'GET'])
def flask_read() -> Response:
    """Invoke read() from flask"""
    return _as_response(read(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/nav', methods=['POST', 'GET'])
def flask_nav() -> Response:
    """Invoke nav() from flask"""
    return _as_response(nav(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/watchSub', methods=['POST', 'GET'])
def flask_watch_sub() -> Response:
    """Invoke watch_sub() from flask"""
    return _as_response(watch_sub(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/watchUnsub', methods=['POST', 'GET'])
def flask_watch_unsub() -> Response:
    """Invoke watch_unsub() from flask"""
    return _as_response(watch_unsub(_as_request(flash_request),
                                    os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/watchPoll', methods=['POST', 'GET'])
def flask_watch_poll() -> Response:
    """Invoke watch_poll() from flask"""
    return _as_response(watch_poll(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/pointWrite', methods=['POST', 'GET'])
def flask_point_write() -> Response:
    """Invoke point_write() from flask"""
    return _as_response(point_write(_as_request(flash_request),
                                    os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/hisRead', methods=['POST', 'GET'])
def flask_his_read() -> Response:
    """Invoke his_read() from flask"""
    return _as_response(his_read(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/hisWrite', methods=['POST', 'GET'])
def flask_his_write() -> Response:
    """Invoke his_write() from flask"""
    return _as_response(his_write(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack_blueprint.route('/invokeAction', methods=['POST', 'GET'])
def flask_invoke_action() -> Response:
    """Invoke invoke_action() from flask"""
    return _as_response(invoke_action(_as_request(flash_request),
                                      os.environ.get("FLASK_ENV", "prod")))
