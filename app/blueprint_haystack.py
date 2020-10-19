"""
A flask blueprint to manage Haystack API
"""
import os

from flask import Blueprint
from flask import Response as flask_response
from flask import request as flash_request

# from werkzeug.local import LocalProxy
# log = LocalProxy(lambda: current_app.logger)
from haystackapi import HaystackHttpRequest, HaystackHttpResponse, \
    about, ops, formats, read, nav, watch_sub, \
    watch_unsub, watch_poll, point_write, his_read, his_write, invoke_action

haystack = Blueprint('haystack', __name__, static_folder='app/static')


def _as_request(request: flash_request) -> HaystackHttpRequest:
    """The interface must be similare to AWS Lambda events"""
    haystack_request = HaystackHttpRequest()
    haystack_request.body = request.data
    haystack_request.headers = flash_request.headers
    haystack_request.args = flash_request.args
    return haystack_request


def _as_response(response: HaystackHttpResponse) -> flask_response:
    rep = flask_response()
    rep.status_code = response.status_code
    rep.headers = response.headers
    rep.data = response.body
    return rep


@haystack.route('/haystack/about', methods=['POST', 'GET'])
def flask_about():
    """
    Invoke about() from flask
    """
    return _as_response(about(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/ops', methods=['POST', 'GET'])
def flask_ops():
    """
    Invoke ops() from flask
    """
    return _as_response(ops(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/formats', methods=['POST', 'GET'])
def flask_formats():
    """
    Invoke formats() from flask
    """
    return _as_response(formats(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/read', methods=['POST', 'GET'])
def flask_read():
    """
    Invoke read() from flask
    """
    return _as_response(read(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/nav', methods=['POST', 'GET'])
def flask_nav():
    """
    Invoke nav() from flask
    """
    return _as_response(nav(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/watchSub', methods=['POST', 'GET'])
def flask_watch_sub():
    """
    Invoke watch_sub() from flask
    """
    return _as_response(watch_sub(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/watchUnsub', methods=['POST', 'GET'])
def flask_watch_unsub():
    """
    Invoke watch_unsub() from flask
    """
    return _as_response(watch_unsub(_as_request(flash_request),
                                    os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/watchPoll', methods=['POST', 'GET'])
def flask_watch_poll():
    """
    Invoke watch_poll() from flask
    """
    return _as_response(watch_poll(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/pointWrite', methods=['POST', 'GET'])
def flask_point_write():
    """
    Invoke point_write() from flask
    """
    return _as_response(point_write(_as_request(flash_request),
                                    os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/hisRead', methods=['POST', 'GET'])
def flask_his_read():
    """
    Invoke his_read() from flask
    """
    return _as_response(his_read(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/hisWrite', methods=['POST', 'GET'])
def flask_his_write():
    """
    Invoke his_write() from flask
    """
    return his_write(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/invokeAction', methods=['POST', 'GET'])
def flask_invoke_action():
    """
    Invoke invoke_action() from flask
    """
    return _as_response(invoke_action(_as_request(flash_request),
                                      os.environ.get("FLASK_ENV", "prod")))
