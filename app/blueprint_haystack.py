import os

from flask import Blueprint
from flask import request as flash_request
from flask import Response as flask_response

# from werkzeug.local import LocalProxy
# log = LocalProxy(lambda: current_app.logger)
from haystackapi import *
from haystackapi import HaystackHttpRequest, HaystackHttpResponse

haystack = Blueprint('haystack', __name__, static_folder='app/static')


def _as_request(request: flash_request) -> HaystackHttpRequest:
    """The interface must be similare to AWS Lambda events"""
    haystack_request = HaystackHttpRequest()
    haystack_request.body = request.data
    haystack_request.headers = flash_request.headers
    return request

def _as_response(response: HaystackHttpResponse) -> flask_response:
    rep = flask_response()
    rep.status_code = response.status_code
    rep.headers = response.headers
    rep.data = response.body
    return rep

@haystack.route('/haystack/about', methods=['POST', 'GET'])
def flask_about():
    return _as_response(about(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/ops', methods=['POST', 'GET'])
def flask_ops():
    return _as_response(ops(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/formats', methods=['POST', 'GET'])
def flask_formats():
    return _as_response(formats(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/read', methods=['POST', 'GET'])
def flask_read():
    return _as_response(read(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/nav', methods=['POST', 'GET'])
def flask_nav():
    return _as_response(nav(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/watchSub', methods=['POST', 'GET'])
def flask_watch_sub():
    return _as_response(watch_sub(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/watchUnsub', methods=['POST', 'GET'])
def flask_watch_unsub():
    return _as_response(watch_unsub(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/watchPoll', methods=['POST', 'GET'])
def flask_watch_pool():
    return _as_response(watch_poll(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/pointWrite', methods=['POST', 'GET'])
def flask_point_write():
    return _as_response(point_write(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/hisRead', methods=['POST', 'GET'])
def flask_his_read():
    return _as_response(his_read(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))


@haystack.route('/haystack/hisWrite', methods=['POST', 'GET'])
def flask_his_write():
    return his_write(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/invokeAction', methods=['POST', 'GET'])
def flask_invoke_action():
    return _as_response(invoke_action(_as_request(flash_request), os.environ.get("FLASK_ENV", "prod")))
