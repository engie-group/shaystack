import os

from flask import Blueprint
from flask import request as flash_request

# from werkzeug.local import LocalProxy
# log = LocalProxy(lambda: current_app.logger)
from haystackapi import *

haystack = Blueprint('haystack', __name__, static_folder='app/static')

def _update_request(request:flash_request):
    """The interface must be similare to AWS Lambda events"""
    request.isBase64Encoded = False
    request.body = request.data
    return request

@haystack.route('/haystack/about', methods=['POST', 'GET'])
def flask_about():
    return about(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/ops', methods=['POST', 'GET'])
def flask_ops():
    return ops(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/formats', methods=['POST', 'GET'])
def flask_formats():
    return formats(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/read', methods=['POST', 'GET'])
def flask_read():
    return read(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/nav', methods=['POST', 'GET'])
def flask_nav():
    return nav(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/watchSub', methods=['POST', 'GET'])
def flask_watch_sub():
    return watch_sub(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/watchUnsub', methods=['POST', 'GET'])
def flask_watch_unsub():
    return watch_unsub(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/watchPoll', methods=['POST', 'GET'])
def flask_watch_pool():
    return watch_poll(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/pointWrite', methods=['POST', 'GET'])
def flask_point_write():
    return point_write(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/hisRead', methods=['POST', 'GET'])
def flask_his_read():
    return his_read(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/hisWrite', methods=['POST', 'GET'])
def flask_his_write():
    return his_write(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))


@haystack.route('/haystack/invokeAction', methods=['POST', 'GET'])
def flask_invoke_action():
    return invoke_action(_update_request(flash_request), os.environ.get("FLASK_ENV", "prod"))
