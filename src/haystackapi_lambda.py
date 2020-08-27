"""Haystack API implemented with AWS Lambda.
Implements: About, Ops, Formats and extend_with_co2e
"""
import base64
import codecs
import gzip
import logging
import os
import threading
import traceback
from datetime import datetime
from typing import cast, Tuple, Optional

from accept_types import get_best_match

import hszinc  # type: ignore
from hszinc import Grid, MODE_ZINC, VER_3_0
from http_tools import get_best_encoding_match
from lambda_types import LambdaProxyEvent, LambdaProxyResponse, AttrDict, LambdaEvent, LambdaContext, \
    cast_lambda_proxy_event
from providers.haystack_interface import get_provider, HaystackInterface

_DEFAULT_VERSION = VER_3_0
NO_COMPRESS = os.environ.get("NOCOMPRESS", "true").lower() == "true"
# See https://tinyurl.com/y8rgcw8p
if os.environ.get("DEBUGGING", "false").lower() == "true":
    # https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging-python.html
    import ptvsd  # type: ignore

    # Enable ptvsd on 0.0.0.0 address and on port 5890 that we'll connect later with our IDE
    ptvsd.enable_attach(address=('0.0.0.0', 5890), redirect_output=True)
    print("Connect debugger...")
    ptvsd.wait_for_attach()

log = logging.getLogger("haystack_api")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))

_DEFAULT_MIME_TYPE = MODE_ZINC


def _parse_request(event) -> Grid:
    # log.debug(event)
    if "Content-Type" not in event.headers:
        raise ValueError("Content-Type must be set")
    if "Content-Encoding" in event.headers and event.isBase64Encoded:
        content_encoding = event.headers["Content-Encoding"]
        if content_encoding != "gzip":
            raise ValueError(f"Content-Encoding '{content_encoding}' not supported")
        body = codecs.decode(str.encode(event.body), 'unicode-escape')
        log.debug(f"decode body={body}")
        event.body = gzip.decompress(base64.b64decode(body)).decode("utf-8")
        event.isBase64Encoded = False
    content_type = event.headers["Content-Type"]
    grid = hszinc.parse(event.body, mode=content_type)[0]
    return grid


def _format_response(event, grid_response, status, default=None):
    hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), grid_response,
                                 default=default)
    response = LambdaProxyResponse()
    response.statusCode = status  # pylint: disable=invalid-name
    response.headers["Content-Type"] = hs_response[0]
    response.body = hs_response[1]
    return response


def _dump_response(accept: str, grid: hszinc.Grid, default: Optional[str] = None) -> Tuple[str, str]:
    accept_type = get_best_match(accept, ['*/*', 'text/zinc', 'application/json'])
    if accept_type in ("text/zinc", "*/*"):
        return ("text/zinc; charset=utf-8", hszinc.dump(grid, mode=hszinc.MODE_ZINC))
    elif accept_type == "application/json":
        return ("application/json; charset=utf-8", hszinc.dump(grid, mode=hszinc.MODE_JSON))
    if default:
        return ("text/zinc; charset=utf-8", hszinc.dump(grid, mode=default))

    raise ValueError(f"Accept:{accept} not supported")  # TODO: must return error 406


def _compress_response(content_encoding: Optional[str], response: LambdaProxyResponse) -> LambdaProxyResponse:
    if not content_encoding or NO_COMPRESS:
        return response
    encoding = get_best_encoding_match(content_encoding, ['gzip'])
    if not encoding:
        return response
    # TODO: accept other encoding format ?
    if encoding == "gzip":
        gzip_body = base64.b64encode(gzip.compress(response.body.decode("utf-8")))
        response.body = gzip_body
        response.headers["Content-Encoding"] = "gzip"
        response["isBase64Encoded"] = True
    return response


def _get_provider() -> HaystackInterface:
    assert "HAYSTACK_PROVIDER" in os.environ, "Set 'HAYSTACK_PROVIDER' environment variable"
    return get_provider(os.environ["HAYSTACK_PROVIDER"])


_tcontext = [
    threading.local()
]


# TODO: propagate lambda context in a thread variable
# def get_lambda_context():
#     #   global _tcontext
#     return None


def about(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """ Implement Haystack 'about' with AWS Lambda """
    event = cast_lambda_proxy_event(_event)
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        # event = cast(LambdaProxyEvent, AttrDict(_event))
        grid_response = provider.about()
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def ops(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """ Implement Haystack 'ops' with AWS Lambda """
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_response = provider.ops()
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def formats(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """ Implement Haystack 'formats' with AWS Lambda """
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_response = provider.formats()
        if grid_response is None:
            grid_response = hszinc.Grid(version=VER_3_0,
                                        columns={
                                            "mime": {},
                                            "receive": {},
                                            "send": {},
                                        })
            grid_response.extend([
                {"mime": "text/zinc", "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {"mime": "application/json", "receive": hszinc.MARKER, "send": hszinc.MARKER},
            ])
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def read(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `read` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        # global _tcontext
        # FIXME _tcontext[0].context = context
        grid_request = _parse_request(event)
        if 'filter' in grid_request[0]:
            read_filter = grid_request[0]['filter']
        else:
            read_filter = ''
        if 'limit' in grid_request[0]:
            limit = int(grid_request[0].get('limit', 0))
        else:
            limit = 0
        grid_response = provider.read(read_filter, limit)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def nav(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `nav` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.nav(grid_request)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watch_sub(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `watch_sub` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watch_sub(grid_request)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watch_unsub(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `watch_unsub` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watch_unsub(grid_request)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watch_poll(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `watch_poll` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watch_poll(grid_request)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def point_write(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `point_write` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.point_write(grid_request)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def his_read(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `his_read` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.his_read(grid_request, (datetime.now(), datetime.now()))  # FIXME: use dates
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def his_write(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `his_write` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        entity_id = grid_request[0]["id"]
        grid_response = provider.his_write(entity_id)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def invoke_action(_event: LambdaEvent,
                  context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `invoke_action` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        id_entity = grid_request.metadata["id"]
        action = grid_request.metadata["action"]
        params = grid_request[0] if grid_request else {}
        grid_response = provider.invoke_action(id_entity, action, params)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)
