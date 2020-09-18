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
from hszinc import Grid, MODE_ZINC, MODE_CSV, MODE_JSON, VER_3_0
from http_tools import get_best_encoding_match
from lambda_types import LambdaProxyEvent, LambdaProxyResponse, AttrDict, LambdaEvent, LambdaContext, \
    cast_lambda_proxy_event
from providers.haystack_interface import get_provider, HaystackInterface

_DEFAULT_VERSION = VER_3_0
_DEFAULT_MIME_TYPE = MODE_CSV
_DEFAULT_MIME_TYPE_WITH_META = MODE_ZINC

# TODO See https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings.html
NO_COMPRESS = os.environ.get("NOCOMPRESS", "true").lower() == "true"
# See https://tinyurl.com/y8rgcw8p
if os.environ.get("DEBUGGING", "false").lower() == "true":
    # https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/ecs-debug.html
    # https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging-python.html
    import ptvsd  # type: ignore

    # Enable ptvsd on 0.0.0.0 address and on port 5890 that we'll connect later with our IDE
    ptvsd.enable_attach(address=('0.0.0.0', 5890), redirect_output=True)
    print("Connect debugger...")
    ptvsd.wait_for_attach()

log = logging.getLogger("haystack_api")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))


def _parse_request(event) -> Grid:
    if "Content-Encoding" in event.headers and event.isBase64Encoded:
        content_encoding = event.headers["Content-Encoding"]
        if content_encoding != "gzip":
            raise ValueError(f"Content-Encoding '{content_encoding}' not supported")
        body = codecs.decode(str.encode(event.body), 'unicode-escape')
        log.debug(f"decode body={body}")
        event.body = gzip.decompress(base64.b64decode(body)).decode("utf-8")
        event.isBase64Encoded = False
    if "Content-Type" not in event.headers:
        grid = Grid(VER_3_0)
    else:
        content_type = event.headers["Content-Type"]
        grid = hszinc.parse(event.body, mode=content_type)
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
    accept_type = get_best_match(accept, ['*/*', hszinc.MODE_CSV, hszinc.MODE_ZINC, hszinc.MODE_JSON])
    if accept_type:
        if accept_type in (_DEFAULT_MIME_TYPE, "*/*"):
            return (_DEFAULT_MIME_TYPE + "; charset=utf-8", hszinc.dump(grid, mode=_DEFAULT_MIME_TYPE))
        elif accept_type in (hszinc.MODE_ZINC):
            return (hszinc.MODE_ZINC + "; charset=utf-8", hszinc.dump(grid, mode=hszinc.MODE_ZINC))
        elif accept_type == hszinc.MODE_JSON:
            return (hszinc.MODE_JSON + "; charset=utf-8", hszinc.dump(grid, mode=hszinc.MODE_JSON))
        elif accept_type == hszinc.MODE_CSV:
            return (hszinc.MODE_CSV + "; charset=utf-8", hszinc.dump(grid, mode=hszinc.MODE_CSV))
    if default:
        return (default + "; charset=utf-8", hszinc.dump(grid, mode=default))

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
    log.debug(f'Provider={os.environ["HAYSTACK_PROVIDER"]}')
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
        if event.headers['Host'].startswith("localhost:"):
            home = "http://" + event.headers['Host'] + '/'
        else:
            home = 'https://' + event.headers['Host'] + '/' + event.requestContext['stage']
        grid_response = provider.about(home)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
                {"mime": MODE_ZINC, "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {"mime": MODE_JSON, "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {"mime": MODE_CSV, "receive": hszinc.MARKER, "send": hszinc.MARKER},
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        if 'filter' in grid_request.column:
            read_filter = grid_request[0].get('filter', '')
        else:
            read_filter = ''
        if 'limit' in grid_request.column:
            limit = int(grid_request[0].get('limit', 0))
        else:
            limit = 0
        # TODO: manage date_version. Default now()
        date_version=datetime.now()

        # Priority of query string
        if event.queryStringParameters:
            if 'filter' in event.queryStringParameters:
                read_filter = event.queryStringParameters['filter']
            if 'limit' in event.queryStringParameters:
                limit = int(event.queryStringParameters['limit'])

        grid_response = provider.read(read_filter, limit, date_version)
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception as e:  # pylint: disable=broad-except
        log.debug(e)
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def his_read(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `his_read` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        if 'id' in grid_request.column:
            entity_id = grid_request[0].get('id', '')
        else:
            entity_id = ''
        if 'range' in grid_request.column:
            date_range = grid_request[0].get('range', '')
        else:
            date_range = ''

        # Priority of query string
        log.debug(f"queryString={event.queryStringParameters}")
        if event.queryStringParameters:
            if 'id' in event.queryStringParameters:
                entity_id = event.queryStringParameters['id']
            if 'range' in event.queryStringParameters:
                date_range = event.queryStringParameters['range']  # FIXME: parse date_range
        log.debug(f"id={entity_id} range={date_range}")
        grid_response = provider.his_read(entity_id, (datetime.now(), datetime.now()))  # FIXME: use dates
        assert grid_response is not None
        response = _format_response(event, grid_response, 200)
    except Exception as e:  # pylint: disable=broad-except
        log.debug(e)
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc()
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def his_write(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `his_write` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    if event.body:
        event.body = codecs.decode(str.encode(event.body), 'unicode-escape')  # FIXME: pourquoi ?
    try:
        provider = _get_provider()
        grid_request = _parse_request(event)
        log.debug(grid_request)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
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
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_META)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)
