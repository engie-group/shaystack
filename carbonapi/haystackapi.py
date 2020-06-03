"""Haystack API implemented with AWS Lambda.
Implements: About, Ops, Formats and extend_with_co2e
"""
import base64
import gzip
import logging
import os
import traceback
from typing import cast, Tuple, Optional

from accept_types import get_best_match
import hszinc  # type: ignore
from hszinc import Uri

from http_tools import get_best_encoding_match
from lambda_types import LambdaProxyEvent, LambdaProxyResponse, AttrDict, LambdaEvent, LambdaContext, \
    cast_lambda_proxy_event

# FIXME: With AWS: Runtime.MarshalError: Unable to marshal response
NO_COMPRESS = os.environ.get("NOCOMPRESS", "false").lower() == "true"
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


def about(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `about` operation"""
    event = cast_lambda_proxy_event(_event)
    # event = cast(LambdaProxyEvent, AttrDict(_event))
    log.info(event)
    log.info(event["headers"])
    grid = hszinc.Grid(columns={
        "haystackVersion": {},  # Str version of REST implementation
        "tz": {},  # Str of server's default timezone
        "serverName": {},  # Str name of the server or project database
        "serverTime": {},  # TODO: type current DateTime of server's clock
        "serverBootTime": {},  # TODO: type DateTime when server was booted up
        "productName": {},  # Str name of the server software product
        "productUri": {},  # TODO: type Uri of the product's web site
        "productVersion": {},  # TODO: from git label. version of the server software product
        # "moduleName": {},  # module which implements Haystack server protocol if its a plug-in to the product
        # "moduleVersion": {}  # Str version of moduleName
    })
    grid.append(
        {
            "haystackVersion": "3.0",
            "tz": None,  # FIXME: set the tz
            "serverName": "localhost",  # FIXME: set the server name
            "serverTime": None,  # FIXME: set the serverTime
            "serverBootTime": None,  # FIXME: set the serverBootTime
            "productName": "carbonapi",
            "productUri": Uri("http://localhost:1234"),  # FIXME indiquer le port ?
            "productVersion": None,  # FIXME: set the product version
            "moduleName": "carbonapi",
            "moduleVersion": None  # FIXME: set the module version
        })
    response = LambdaProxyResponse()
    response.statusCode = 200
    hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), grid)
    response.headers["Content-Type"] = hs_response[0]
    response.body = hs_response[1]
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def ops(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `ops` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    grid = hszinc.Grid(columns={
        "name": {},
        "summary": {},
    })
    grid.extend([
        {"name": "about", "summary": "Summary information for server"},
        {"name": "ops", "summary": "Operations supported by this server"},
        {"name": "formats", "summary": "Grid data formats supported by this server"},
        {"name": "extend_with_co2e", "summary": "Extend with with CO2e"},
    ])
    response = LambdaProxyResponse()
    response.statusCode = 200
    hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), grid)
    response.headers["Content-Type"] = hs_response[0]
    response.body = hs_response[1]
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def formats(_event: LambdaEvent, context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """Implement the haystack `format` operation"""
    event = cast(LambdaProxyEvent, AttrDict(_event))
    grid = hszinc.Grid(columns={
        "mime": {},
        "receive": {},
        "send": {},
    })
    grid.extend([
        {"mime": "text/zinc", "receive": hszinc.MARKER, "send": hszinc.MARKER},
        {"mime": "application/json", "receive": hszinc.MARKER, "send": hszinc.MARKER},
    ])
    response = LambdaProxyResponse()
    response.statusCode = 200
    hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), grid)
    response.headers["Content-Type"] = hs_response[0]
    response.body = hs_response[1]
    return _compress_response(event.headers.get("Accept-Encoding", None), response)


def extend_with_co2e(_event: LambdaEvent,
                     context: LambdaContext) -> LambdaProxyResponse:  # pylint: disable=unused-argument
    """
    Read a haystack grid, inject CO2e, and return the same grid
    Parameters
    ----------
    _event Proxy event
    context AWS Lambda context

    Returns Proxy response
    -------

    """
    event = cast(LambdaProxyEvent, AttrDict(_event))
    try:
        if "Content-Type" not in event.headers:
            raise ValueError("Content-Type must be set")

        if "Content-Encoding" in event.headers and event.isBase64Encoded:
            content_encoding = event.headers["Content-Encoding"]
            if content_encoding != "gzip":
                raise ValueError(f"Content-Encoding '{content_encoding}' not supported")
            event.body = gzip.decompress(base64.b64decode(event.body)).decode("utf-8")
            event.isBase64Encoded = False

        content_type = event.headers["Content-Type"]
        if content_type.startswith("text/zinc"):
            grid = hszinc.parse(event.body, mode=hszinc.MODE_ZINC)
        elif content_type.startswith("application/json"):
            grid = hszinc.parse(event.body, mode=hszinc.MODE_JSON)
        else:
            raise ValueError(f"Content-Type '{content_type}' not supported")

        log.info("----> Call Carbon core calculation to update Haystack Grid")

        response = LambdaProxyResponse()
        response.statusCode = 200
        hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), grid)
        response.headers["Content-Type"] = hs_response[0]
        response.body = hs_response[1]
    except ValueError:
        error_grid = hszinc.Grid(metadata={
            "err": hszinc.MARKER,
            "id": "badId",
            "errTrace": traceback.format_exc()
        }, columns=[('id', [('meta', None)])])  # FIXME: pourquoi columns est nécessaire ? Devrait être None
        response = LambdaProxyResponse()
        response.statusCode = 400
        hs_response = _dump_response(event.headers.get("Accept", _DEFAULT_MIME_TYPE), error_grid,
                                     default=hszinc.MODE_ZINC)
        response.headers["Content-Type"] = hs_response[0]
        response.body = hs_response[1]

    return _compress_response(event.headers.get("Accept-Encoding", None), response)
