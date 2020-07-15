"""Haystack API implemented with AWS Lambda.
Implements: About, Ops, Formats and extend_with_co2e
"""
import base64
import gzip
import logging
import os
import threading
import traceback
from datetime import datetime
from typing import cast, Tuple, Optional

from accept_types import get_best_match

import hszinc  # type: ignore
from hszinc import Grid, MODE_ZINC
from http_tools import get_best_encoding_match
from lambda_types import LambdaProxyEvent, LambdaProxyResponse, AttrDict, LambdaEvent, LambdaContext, \
    cast_lambda_proxy_event
# FIXME: With AWS: Runtime.MarshalError: Unable to marshal response
# TOTRY: https://github.com/awslabs/aws-sam-cli/issues/1163
from providers.HaystackInterface import get_provider, HaystackInterface

NO_COMPRESS = os.environ.get("NOCOMPRESS", "true").lower() == "true"
# See https://tinyurl.com/y8rgcw8p
if os.environ.get("DEBUGGING", "false").lower() == "true":
    # TOTRY: validate the attachement of debugger
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
    if "Content-Type" not in event.headers:
        raise ValueError("Content-Type must be set")
    if "Content-Encoding" in event.headers and event.isBase64Encoded:
        content_encoding = event.headers["Content-Encoding"]
        if content_encoding != "gzip":
            raise ValueError(f"Content-Encoding '{content_encoding}' not supported")
        event.body = gzip.decompress(base64.b64decode(event.body)).decode("utf-8")
        event.isBase64Encoded = False
    content_type = event.headers["Content-Type"]
    grid = hszinc.parse(event.body, mode=content_type)[0]
    return grid


def _format_response(event, grid_response, status, default=None):
    hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), grid_response,
                                 default=default)
    response = LambdaProxyResponse()
    response.statusCode = status
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
    assert "PROVIDER" in os.environ, "Set 'PROVIDER' environment variable"
    return get_provider(os.environ["PROVIDER"])


_tcontext = [
    threading.local()
]


def get_lambda_context():
    #   global _tcontext
    return None  # FIXME : Cela ne fonctionne pas de retrouver la variable du thread.


def about(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """ Implement Haystack 'about' with AWS Lambda """

    event = cast_lambda_proxy_event(_event)
    try:
        provider = _get_provider()
        # event = cast(LambdaProxyEvent, AttrDict(_event))
        grid_response = provider.about()
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def ops(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """ Implement Haystack 'ops' with AWS Lambda """
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        provider = _get_provider()
        grid_response = provider.ops()
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def formats(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """ Implement Haystack 'formats' with AWS Lambda """
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        provider = _get_provider()
        grid_response = provider.formats()
        if None == grid_response:
            grid_response = hszinc.Grid(columns={
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
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def read(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `read` operation"""
        provider = _get_provider()
        global _tcontext
        # FIXME _tcontext[0].context = context
        grid_request = _parse_request(event)
        filter = grid_request[0]['filter']  # FIXME: peut être absent
        limit = int(grid_request[0].get('limit', -1))
        grid_response = provider.read(filter, limit)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def nav(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `nav` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.nav(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watchSub(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `watchSub` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watchSub(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watchUnsub(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `watchUnsub` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watchUnsub(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watchPoll(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `watchPoll` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watchPoll(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def pointWrite(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `pointWrite` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.pointWrite(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def hisRead(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `hisRead` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.hisRead(grid_request, (datetime.now(), datetime.now()))  # FIXME: extraire dates
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def hisWrite(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `hisWrite` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.hisWrite(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def invokeAction(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        """Implement the haystack `invokeAction` operation"""
        provider = _get_provider()
        grid_request = _parse_request(event)
        id = grid_request.metadata["id"]
        action = grid_request.metadata["action"]
        params = grid_request[0] if len(grid_request) else {}
        grid_response = provider.invokeAction(id, action, params)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, default=_DEFAULT_MIME_TYPE)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)
