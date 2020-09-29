""" Haystack API implemented with HTTP generic layer.

    The environment variable `HAYSTACK_PROVIDER` is use to
    route the HTTP request to the specified provider.

    Upper of this API, you can find a Flask, AWS Lambda, etc.
"""
import base64
import codecs
import gzip
import logging
import os
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
# Matches 'gzip' or 'compress'
from typing import Optional, Any, Match, List
from typing import Tuple, Dict

from accept_types import AcceptableType, get_best_match

import hszinc
from hszinc.grid_filter import _parse_datetime
from .providers.haystack_interface import get_provider, HaystackInterface

_DEFAULT_VERSION = hszinc.VER_3_0
_DEFAULT_MIME_TYPE = hszinc.MODE_CSV
_DEFAULT_MIME_TYPE_WITH_METADATA = hszinc.MODE_ZINC

log = logging.getLogger("haystackapi")
log.setLevel(level=logging.getLevelName(os.environ.get("LOGLEVEL", "WARNING")))


@dataclass
class HaystackHttpRequest():
    body: str = ""
    args: Dict[str, str] = field(default_factory=lambda: ({}))
    is_base64: bool = False
    headers: Dict[str, str] = field(default_factory=lambda: (
        {'Host': 'localhost', 'Content-Type': 'text:text', 'Accept': '*/*'}))


@dataclass
class HaystackHttpResponse():
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=lambda: ({'Content-Type': 'text/text'}))
    body: str = ""


_COMPRESS_TYPE_STR = r'[a-zA-Z0-9._-]+'

# Matches either '*', 'image/*', or 'image/png'
_valid_encoding_type = re.compile(r'^(?:[a-zA-Z-]+)$')

# Matches the 'q=1.23' from the parameters of a Accept mime types
_q_match = re.compile(r'(?:^|;)\s*q=([0-9.-]+)(?:$|;)')


class _AcceptableEncoding:
    encoding_type = None
    weight = Decimal(1)
    pattern = None

    def __init__(self, raw_encoding_type):
        bits = raw_encoding_type.split(';', 1)

        encoding_type = bits[0]
        if not _valid_encoding_type.match(encoding_type):
            raise ValueError(f'"{encoding_type}" is not a valid encoding type')

        tail = ''
        if len(bits) > 1:
            tail = bits[1]

        self.encoding_type = encoding_type
        self.weight = _get_weight(tail)
        self.pattern = re.compile('^' + re.escape(encoding_type) + '$')

    def matches(self, encoding_type: str) -> Optional[Match[Any]]:
        return self.pattern.match(encoding_type)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        display = self.encoding_type
        if self.weight != Decimal(1):
            display += '; q=%0.2f' % self.weight

        return display

    def __repr__(self):
        return '<AcceptableType {0}>'.format(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _AcceptableEncoding):
            return False
        return (self.encoding_type, self.weight) == (other.encoding_type, other.weight)

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, _AcceptableEncoding):
            raise ValueError("Parameter invalid")
        return self.weight < other.weight


def get_best_encoding_match(header: str, available_encoding: List[str]) -> Optional[str]:
    acceptable_types = _parse_header(header)

    for acceptable_type in acceptable_types:
        for available_type in available_encoding:
            if acceptable_type.matches(available_type):
                return available_type

    return None


def _parse_header(header: str) -> List[AcceptableType]:
    """Parse an ``Accept`` header into a sorted list of :class:`AcceptableType`
    instances.
    """
    raw_encoding_types = header.split(',')
    encoding_types = []
    for raw_encoding_type in raw_encoding_types:
        try:
            encoding_types.append(_AcceptableEncoding(raw_encoding_type.strip()))
        except ValueError:
            pass

    return sorted(encoding_types, reverse=True)


def _get_weight(tail):
    """Given the tail of a mime type header (the bit after the first ``;``),
    find the ``q`` (weight, or quality) parameter.

    If no valid ``q`` parameter is found, default to ``1``, as per the spec.
    """
    match = re.search(_q_match, tail)
    if match:
        try:
            return Decimal(match.group(1))
        except ValueError:
            pass

    # Default weight is 1
    return Decimal(1)


def _parse_body(request: HaystackHttpRequest) -> hszinc.Grid:
    if "Content-Encoding" in request.headers and request.isBase64Encoded:
        content_encoding = request.headers["Content-Encoding"]
        if content_encoding != "gzip":
            raise ValueError(f"Content-Encoding '{content_encoding}' not supported")
        body = codecs.decode(str.encode(request.body), 'unicode-escape')
        log.debug(f"decode body={body}")
        request.body = gzip.decompress(base64.b64decode(body)).decode("utf-8")
        request.isBase64Encoded = False
    if "Content-Type" not in request.headers:
        grid = hszinc.Grid(version=_DEFAULT_VERSION)
    else:
        content_type = request.headers["Content-Type"]
        grid = hszinc.parse(request.body, mode=content_type)
    return grid


def _format_response(headers: Dict[str, str], grid_response: hszinc.Grid, status: int,
                     default=None) -> HaystackHttpResponse:
    hs_response = _dump_response(headers.get("Accept", _DEFAULT_MIME_TYPE), grid_response,
                                 default=default)

    response = HaystackHttpResponse(status_code=status,
                                    body=hs_response[1]
                                    )
    response.headers['Content-Type'] = hs_response[0]
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


# PPR: manage compression ?
def _compress_response(content_encoding: Optional[str], response):
    return response


def _get_provider() -> HaystackInterface:
    assert "HAYSTACK_PROVIDER" in os.environ, "Set 'HAYSTACK_PROVIDER' environment variable"
    log.debug(f'Provider={os.environ["HAYSTACK_PROVIDER"]}')
    return get_provider(os.environ["HAYSTACK_PROVIDER"])


def about(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """ Implement Haystack 'about' with AWS Lambda """
    headers = request.headers
    log.debug(f'HAYSTACK_PROVIDER={os.environ.get("HAYSTACK_PROVIDER", None)}')
    log.debug(f'HAYSTACK_URL={os.environ.get("HAYSTACK_URL", None)}')
    try:
        provider = _get_provider()
        if headers['Host'].startswith("localhost:"):
            home = "http://" + headers['Host'] + '/'
        else:
            home = 'https://' + headers['Host'] + '/' + stage
        grid_response = provider.about(home)
        assert grid_response is not None
        return _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def ops(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """ Implement Haystack 'ops' with AWS Lambda """
    headers = request.headers
    try:
        provider = _get_provider()
        grid_response = provider.ops()
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def formats(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """ Implement Haystack 'formats' with AWS Lambda """
    headers = request.headers
    try:
        provider = _get_provider()
        grid_response = provider.formats()
        if grid_response is None:
            grid_response = hszinc.Grid(version=_DEFAULT_VERSION,
                                        columns={
                                            "mime": {},
                                            "receive": {},
                                            "send": {},
                                        })
            grid_response.extend([
                {"mime": hszinc.MODE_ZINC, "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {"mime": hszinc.MODE_JSON, "receive": hszinc.MARKER, "send": hszinc.MARKER},
                {"mime": hszinc.MODE_CSV, "receive": hszinc.MARKER, "send": hszinc.MARKER},
            ])
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def read(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `read` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        if 'filter' in grid_request.column:
            read_filter = grid_request[0].get('filter', '')
        else:
            read_filter = ''
        if 'limit' in grid_request.column:
            limit = int(grid_request[0].get('limit', 0))
        else:
            limit = 0
        date_version = grid_request[0].get('version', None) if len(grid_request) else None

        # Priority of query string
        if args:
            if 'filter' in args:
                read_filter = args['filter']
            if 'limit' in args:
                limit = int(args['limit'])
            if 'version' in args:
                date_version = _parse_datetime(args['version'].split(' '))

        log.debug(f"filter={read_filter} limit={limit}, date_version={date_version}")
        grid_response = provider.read(read_filter, limit, date_version)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception as e:  # pylint: disable=broad-except
        log.debug(e)
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def nav(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `nav` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        grid_response = provider.nav(grid_request)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def watch_sub(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `watch_sub` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        grid_response = provider.watch_sub(grid_request)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        log.error(traceback.format_exc())
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def watch_unsub(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `watch_unsub` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        grid_response = provider.watch_unsub(grid_request)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def watch_poll(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `watch_poll` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        grid_response = provider.watch_poll(grid_request)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def point_write(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `point_write` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        date_version = grid_request[0].get('version', None) if len(grid_request) else None
        # FIXME: check implementation
        grid_response = provider.point_write(grid_request, date_version)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def his_read(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `his_read` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        if 'id' in grid_request.column:
            entity_id = grid_request[0].get('id', '')
        else:
            entity_id = ''
        if 'range' in grid_request.column:
            date_range = grid_request[0].get('range', '')
        else:
            date_range = ''
        date_version = grid_request[0].get('version', None) if len(grid_request) else None

        # Priority of query string
        if args:
            if 'id' in args:
                entity_id = args['id']
            if 'range' in args:
                date_range = args['range']  # FIXME: parse date_range
            if 'version' in args:
                date_version = _parse_datetime(args['version'].split(' '))

        log.debug(f"id={entity_id} range={date_range}, date_version={date_version}")
        grid_response = provider.his_read(entity_id, (datetime.now(), datetime.now()), date_version)  # FIXME: use dates
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception as e:  # pylint: disable=broad-except
        log.debug(e)
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def his_write(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `his_write` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        if 'id' in grid_request.column:
            entity_id = grid_request[0].get('id', '')
        else:
            entity_id = ''
        date_version = grid_request[0].get('version', None) if len(grid_request) else None

        # Priority of query string
        if args:
            if 'id' in args:
                entity_id = args['id']
        if 'version' in args:
            date_version = _parse_datetime(args['version'].split(' '))
        grid_response = provider.his_write(entity_id, date_version)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)


def invoke_action(request: HaystackHttpRequest, stage: str) -> HaystackHttpResponse:
    """Implement the haystack `invoke_action` operation"""
    body, headers, args = (request.body, request.headers, request.args)
    try:
        provider = _get_provider()
        grid_request = _parse_body(request)
        if 'id' in grid_request.column:
            entity_id = grid_request[0].get('id', '')
        else:
            entity_id = ''
        if 'action' in grid_request.column:
            action = grid_request[0].get('action', '')
        else:
            action = ''
        # Priority of query string
        if args:
            if 'action' in args:
                entity_id = args['id']
            if 'id' in args:
                entity_id = args['action']
        params = grid_request[0] if grid_request else {}
        grid_response = provider.invoke_action(entity_id, action, params)
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200)
    except Exception:  # pylint: disable=broad-except
        error_grid = hszinc.Grid(version=_DEFAULT_VERSION,
                                 metadata={
                                     "err": hszinc.MARKER,
                                     "id": "badId",
                                     "errTrace": traceback.format_exc() if stage == "dev" else ""
                                 },
                                 columns=[
                                     ('id',
                                      [('meta', None)])])
        response = _format_response(headers, error_grid, 400, default=_DEFAULT_MIME_TYPE_WITH_METADATA)
    return _compress_response(headers.get("Accept-Encoding", None), response)
