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
from HaystackInterface import HaystackInterface, get_provider
from hszinc import Grid, MODE_ZINC
from http_tools import get_best_encoding_match
from lambda_types import LambdaProxyEvent, LambdaProxyResponse, AttrDict, LambdaEvent, LambdaContext, \
    cast_lambda_proxy_event

# FIXME: With AWS: Runtime.MarshalError: Unable to marshal response
# TOTRY: https://github.com/awslabs/aws-sam-cli/issues/1163
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

log = logging.getLogger("carnonapi")
log.setLevel(level=os.environ.get("LOGLEVEL", "WARNING"))

_DEFAULT_MIME_TYPE = "text/zinc"


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

    raise ValueError(f"Accept:{accept} not supported")


def _compress_response(content_encoding: Optional[str], response: LambdaProxyResponse) -> LambdaProxyResponse:
    if not content_encoding or NO_COMPRESS:
        return response
    encoding = get_best_encoding_match(content_encoding, ['gzip'])
    if not encoding:
        return response
    # TODO: accept other encoding format ?
    if encoding == "gzip":
        gzip_body = base64.b64encode(gzip.compress(response.body.encode("utf-8")))
        response.body = gzip_body
        response.headers["Content-Encoding"] = "gzip"
        response["isBase64Encoded"] = True
    return response


def _get_provider() -> HaystackInterface:
    return get_provider(os.environ["provider"])


_tcontext = [
    threading.local()
]


def get_lambda_context():
    #   global _tcontext
    return None  # FIXME : Cela ne fonctionne pas de retrouver la variable du thread.


def about(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `about` operation"""

    try:
        provider = _get_provider()
        event = cast_lambda_proxy_event(_event)
        # event = cast(LambdaProxyEvent, AttrDict(_event))
        grid_response = provider.about()
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def ops(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `ops` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_response = provider.ops()
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def formats(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `format` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
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
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def read(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `read` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        global _tcontext
        # FIXME _tcontext[0].context = context
        grid_request = _parse_request(event)
        filter = grid_request[0]['filter']
        limit = int(grid_request[0].get('limit', -1))
        grid_response = provider.read(filter, limit)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def nav(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `nav` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.nav(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watchSub(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `watchSub` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watchSub(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watchUnsub(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `watchUnsub` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watchUnsub(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def watchPoll(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `watchPoll` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.watchPoll(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def pointWrite(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `pointWrite` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.pointWrite(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def hisRead(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `hisRead` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.hisRead(grid_request, (datetime.now(), datetime.now()))  # FIXME: extraire dates
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def hisWrite(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `hisWrite` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        grid_response = provider.hisWrite(grid_request)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def invokeAction(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    try:
        """Implement the haystack `hisWrite` operation"""
        event = cast(LambdaProxyEvent, AttrDict(_event))
        provider = _get_provider()
        grid_request = _parse_request(event)
        id = grid_request.metadata["id"]
        action = grid_request.metadata["action"]
        params = grid_request[0] if len(grid_request) else {}
        grid_response = provider.invokeAction(id, action, params)
        assert None != grid_response
        response = _format_response(event, grid_response, 200)
    except:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = _format_response(event, error_grid, 400, MODE_ZINC)
    return _compress_response(event.headers.get("Accept-Encoding", None), response)
