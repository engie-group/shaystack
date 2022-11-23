# -*- coding: utf-8 -*-
# Wrapper between HTTP request and Haystack provider
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
""" Wrapper between HTTP request and Haystack provider

    Create an `HaystackHttpRequest` and `HaystackHttpResponse`
    to create a link between HTTP technology and shift-4-haystack,
    and invoke the corresponding function.
"""
import logging
import re
import traceback
from ast import literal_eval
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any, List, cast
from typing import Tuple, Dict, Union

from accept_types import get_best_match
from pyparsing import ParseException

from .datatypes import Ref, Quantity, MARKER, MODE_TRIO, MODE
from .dumper import dump
from .empty_grid import EmptyGrid
from .exception import HaystackException
from .grid import Grid, VER_3_0
from .grid_filter import parse_hs_datetime_format
from .parser import MODE_ZINC, MODE_HAYSON, MODE_CSV, MODE_JSON, parse_scalar, parse, mode_to_suffix
from .providers.haystack_interface import (
    HttpError, parse_date_range, HaystackInterface,
)

_DEFAULT_VERSION = VER_3_0
DEFAULT_MIME_TYPE = MODE_CSV
_DEFAULT_MIME_TYPE_WITH_METADATA = MODE_ZINC

log = logging.getLogger("shaystack")


@dataclass
class HaystackHttpRequest:
    """
    A wrapper between http request and Haystack API provider.

    Convert the custom technology HTTP request to this format
    """

    body: str = ""
    args: Dict[str, str] = field(default_factory=lambda: ({}))
    headers: Dict[str, str] = field(
        default_factory=lambda: (
            {"Host": "localhost", "Content-Type": "text/text", "Accept": "*/*"}
        )
    )


@dataclass
class HaystackHttpResponse:
    """
    A wrapper between http response and Haystack API provider.

    Convert the custom technology HTTP request to this format
    """

    status_code: int = 200
    status: str = "OK"
    headers: Dict[str, str] = field(
        default_factory=lambda: ({"Content-Type": "text/text"})
    )
    body: str = ""


_COMPRESS_TYPE_STR = r"[a-zA-Z0-9._-]+"

# Matches either '*', 'image/*', or 'image/png'
_valid_encoding_type = re.compile(r"^(?:[a-zA-Z-]+)$")

# Matches the 'q=1.23' from the parameters of a Accept mime types
_q_match = re.compile(r"(?:^|;)\s*q=([0-9.-]+)(?:$|;)")


class _AcceptableEncoding:
    encoding_type = None
    weight = Decimal(1)
    pattern = None

    def __init__(self, raw_encoding_type: str):
        bits = raw_encoding_type.split(";", 1)

        encoding_type = bits[0]
        if not _valid_encoding_type.match(encoding_type):
            raise ValueError(f'"{encoding_type}" is not a valid encoding type')

        tail = ""
        if len(bits) > 1:
            tail = bits[1]

        self.encoding_type = encoding_type
        self.weight = _get_weight(tail)
        self.pattern = re.compile("^" + re.escape(encoding_type) + "$")

    def matches(self, encoding_type: str) -> bool:
        """
        Return true if encoding_type match the pattern
        """
        return self.pattern.match(encoding_type) is not None  # type: ignore

    def __str__(self) -> str:
        display = self.encoding_type
        if self.weight != Decimal(1):
            display += "; q=%0.2f" % self.weight  # type: ignore

        return display  # type: ignore

    def __repr__(self) -> str:
        return "<AcceptableType {0}>".format(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _AcceptableEncoding):
            return False
        return (self.encoding_type, self.weight) == (other.encoding_type, other.weight)

    def __lt__(self, other: '_AcceptableEncoding') -> bool:
        assert isinstance(other, _AcceptableEncoding)
        return self.weight < other.weight


def _get_best_encoding_match(
        header: str,
        available_encoding: List[str]
) -> Optional[str]:
    """
    Return best encoding match.
    """
    acceptable_types = _parse_header(header)

    for acceptable_type in acceptable_types:
        for available_type in available_encoding:
            if acceptable_type.matches(available_type):
                return available_type

    return None


def _parse_header(header: str) -> List[_AcceptableEncoding]:
    """Parse an ``Accept`` header into a sorted list of :class:`AcceptableType`
    instances.
    """
    raw_encoding_types = header.split(",")
    encoding_types = []
    for raw_encoding_type in raw_encoding_types:
        try:
            encoding_types.append(_AcceptableEncoding(raw_encoding_type.strip()))
        except ValueError:
            pass

    return sorted(encoding_types, reverse=True)


def _get_weight(tail: str) -> Decimal:
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


def _parse_body(request: HaystackHttpRequest) -> Grid:
    """
    Convert the HTTP request to grid.

    Use the `Content-Type` in header.
    If the `Content-Type` is not found, use the DEFAULT_MIME_TYPE
    Args:
        request: The HTTP request

    Returns:
        The grid
    """
    if "Content-Type" not in request.headers:
        grid = parse(request.body, mode=DEFAULT_MIME_TYPE)
    else:
        content_type = cast(MODE, request.headers["Content-Type"])
        if mode_to_suffix(cast(MODE, content_type)):
            grid = parse(request.body, mode=content_type)
        elif request.body:
            raise HttpError(406, f"Content-Type '{content_type}' not supported")
        else:
            grid = Grid(version=VER_3_0)
    if grid is None:
        grid = EmptyGrid
    return grid


def _format_response(
        headers: Dict[str, str],
        grid_response: Grid,
        status_code: int,
        status_msg: str,
        default: Optional[MODE] = None,
) -> HaystackHttpResponse:
    """
    Convert the grid and HTTP status to HTTP response.

    Args:
        headers: A list of headers
        grid_response: The grid to return
        status_code: The status code
        status_msg: and corresponding message
        default: Use the default MIME_TYPE

    Returns:

    """
    if "Accept" not in headers:
        raise HttpError(406, "required header 'Accept' not found")
    hs_response = _dump_response(
        headers.get("Accept", DEFAULT_MIME_TYPE), grid_response, default=default
    )

    response = HaystackHttpResponse(
        status_code=status_code, status=status_msg, body=hs_response[1]
    )
    response.headers["Content-Type"] = hs_response[0]
    return response


def _dump_response(
        accept: str, grid: Grid, default: Optional[MODE] = None
) -> Tuple[str, str]:
    """
    Dump the response and return the mime type and body
    Args:
        accept: the `Accept` header
        grid: The grid to dump
        default: The default `Accept` value

    Returns:
        A tuple with the mime type and the body
    """
    accept_type = get_best_match(
        accept, ["*/*", MODE_CSV, MODE_TRIO, MODE_ZINC, MODE_JSON, MODE_HAYSON]
    )
    if accept_type:
        if accept_type in (DEFAULT_MIME_TYPE, "*/*"):
            return (
                DEFAULT_MIME_TYPE + "; charset=utf-8",
                dump(grid, mode=DEFAULT_MIME_TYPE),
            )
        if accept_type == MODE_ZINC:
            return (
                MODE_ZINC + "; charset=utf-8",
                dump(grid, mode=MODE_ZINC),
            )
        if accept_type == MODE_TRIO:
            return (
                MODE_ZINC + "; charset=utf-8",
                dump(grid, mode=MODE_TRIO),
            )
        if accept_type == MODE_JSON:
            return (
                MODE_JSON + "; charset=utf-8",
                dump(grid, mode=MODE_JSON),
            )
        if accept_type == MODE_CSV:
            return (
                MODE_CSV + "; charset=utf-8",
                dump(grid, mode=MODE_CSV),
            )
        if accept_type == MODE_HAYSON:
            return (
                MODE_HAYSON,
                dump(grid, mode=MODE_HAYSON),
            )
    if default:
        return (
            default + "; charset=utf-8",
            dump(grid, mode=default),
        )  # Return HTTP 403 ?

    raise HttpError(406, f"Accept '{accept}' not supported")


def _manage_exception(
        headers: Dict[str, str], ex: Exception, stage: str
) -> HaystackHttpResponse:
    """
    Manage an exception to generate an HTTP response.
    Args:
        headers: The headers
        ex: The exception
        stage: The current stage

    Returns:
        An HTTP response.
    """
    log.error(traceback.format_exc())
    error_grid = Grid(
        version=_DEFAULT_VERSION,
        metadata={
            "err": MARKER,
            "dis": "Error",
            "errTrace": traceback.format_exc() if stage == "dev" else "",
        },
        columns=[("id", [("meta", None)])],
    )
    status_code = 400
    status_msg = "ERROR"
    if isinstance(ex, HttpError):
        ex_http = cast(HttpError, ex)
        status_code = ex_http.error
        status_msg = ex_http.msg
    if isinstance(ex, ParseException):
        status_code = 200
        status_msg = f"Parsing error with '{ex.line}'"  # type: ignore
        error_grid.metadata["dis"] = status_msg
    if isinstance(ex, HaystackException):
        status_code = 200
        status_msg = ex.msg
        error_grid.metadata["dis"] = status_msg
    return _format_response(
        headers,
        error_grid,
        status_code,
        status_msg,
        default=_DEFAULT_MIME_TYPE_WITH_METADATA,
    )


def about(envs: Dict[str, str], request: HaystackHttpRequest, stage: str,
          provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack about.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        envs: The environments variables
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers = request.headers
    log.debug("HAYSTACK_PROVIDER=%s", envs.get("HAYSTACK_PROVIDER", None))
    log.debug("HAYSTACK_DB=%s", envs.get("HAYSTACK_DB", None))
    try:
        if headers["Host"].startswith("localhost:"):
            home = "http://" + headers["Host"] + "/"
        else:
            home = "https://" + headers["Host"] + "/" + stage
        grid_response = provider.about(home)
        assert grid_response is not None
        return _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def ops(envs: Dict[str, str], request: HaystackHttpRequest, stage: str,
        provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack `ops`.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers = request.headers
    try:
        grid_response = provider.ops()
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def formats(envs: Dict[str, str], request: HaystackHttpRequest,
            stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'formats'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers = request.headers
    try:
        grid_response = provider.formats()
        if grid_response is None:
            grid_response = Grid(
                version=_DEFAULT_VERSION,
                columns={
                    "mime": {},
                    "receive": {},
                    "send": {},
                },
            )
            grid_response.extend(
                [
                    {
                        "mime": MODE_ZINC,
                        "receive": MARKER,
                        "send": MARKER,
                    },
                    {
                        "mime": MODE_TRIO,
                        "receive": MARKER,
                        "send": MARKER,
                    },
                    {
                        "mime": MODE_JSON,
                        "receive": MARKER,
                        "send": MARKER,
                    },
                    {
                        "mime": MODE_CSV,
                        "receive": MARKER,
                        "send": MARKER,
                    },
                ]
            )
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def convert_version(version: Union[datetime, date]) -> datetime:
    """
    Converts the given version to str and uses 23:59:59 for the time when the version
    is based only on the date in order to get the most recent version at that date.

    :param version: either date or datetime version of ontology file in S3
    """
    if not isinstance(version, datetime):
        version = datetime.combine(version, datetime.min.time()).replace(
            hour=23, minute=59, second=59)
    elif version.hour == 0 & version.minute == 0 & version.second == 0:
        version = version.replace(hour=23, minute=59, second=59)

    return version


def read(envs: Dict[str, str], request: HaystackHttpRequest, stage: str,
         provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack `read`
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        read_ids: Optional[List[Ref]] = None
        select = read_filter = date_version = None
        limit = 0
        default_tz = provider.get_tz()
        if grid_request:
            if "id" in grid_request.column:
                read_ids = [row["id"] for row in grid_request]
            else:
                if "filter" in grid_request.column:
                    read_filter = grid_request[0].get("filter", "")  # type: ignore
                else:
                    read_filter = ""
                if "limit" in grid_request.column:
                    limit = int(grid_request[0].get("limit", 0))  # type: ignore
            if "select" in grid_request.column:
                select = grid_request[0].get("select", "*")  # type: ignore
            date_version = (
                grid_request[0].get("version", None) if grid_request else None  # type: ignore
            )
        # Priority of query string
        if args:
            if "id" in args:
                read_ids = [Ref(entity_id) for entity_id in args["id"].split(",")]
            else:
                if "filter" in args:
                    read_filter = args["filter"]
                if "limit" in args:
                    limit = int(args["limit"])
            if "select" in args:
                select = args["select"]
            if "version" in args:
                date_version = parse_hs_datetime_format(args["version"], default_tz)
                date_version = convert_version(date_version)
        if read_filter is None:
            read_filter = ""
        if read_ids is None and read_filter is None:
            raise ValueError("'id' or 'filter' must be set")
        log.debug(
            "id=%s select='%s' filter='%s' limit=%s, date_version=%s",
            read_ids,
            select,
            read_filter,
            limit,
            date_version,
        )
        grid_response = provider.read(limit, select, read_ids, read_filter, date_version)  # type: ignore
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def nav(envs: Dict[str, str], request: HaystackHttpRequest, stage: str,
        provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'nav'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        nav_id = None
        if grid_request and "navId" in grid_request.column:
            nav_id = grid_request[0]["navId"]  # type: ignore
        if args and "navId" in args:
            nav_id = args["navId"]
        grid_response = provider.nav(nav_id=nav_id)  # type: ignore
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def watch_sub(envs: Dict[str, str], request: HaystackHttpRequest,
              stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'watchSub'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        watch_dis = watch_id = lease = None
        ids = []
        if grid_request:
            watch_dis = grid_request.metadata["watchDis"]
            watch_id = grid_request.metadata.get("watchId", None)
            if "lease" in grid_request.metadata:
                lease = int(grid_request.metadata["lease"])
            ids = [row["id"] for row in grid_request]

        if args:
            if "watchDis" in args:
                watch_dis = args["watchDis"]
            if "watchId" in args:
                watch_id = args["watchId"]
            if "lease" in args:
                lease = int(args["lease"])
            if "ids" in args:  # Use list of str
                ids = [Ref(x[1:]) for x in literal_eval(args["ids"])]
        if not watch_dis:
            raise ValueError("'watchDis' and 'watchId' must be setted")
        grid_response = provider.watch_sub(watch_dis, watch_id, ids, lease)
        assert grid_response is not None
        assert "watchId" in grid_response.metadata
        assert "lease" in grid_response.metadata
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def watch_unsub(envs: Dict[str, str], request: HaystackHttpRequest,
                stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'watchUnsub'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        close = False
        watch_id = False
        ids = []
        if grid_request:
            if "watchId" in grid_request.metadata:
                watch_id = grid_request.metadata["watchId"]
            if "close" in grid_request.metadata:
                close = bool(grid_request.metadata["close"])
            ids = [row["id"] for row in grid_request]

        if args:
            if "watchId" in args:
                watch_id = args["watchId"]  # type: ignore
            if "close" in args:
                close = bool(args["close"])
            if "ids" in args:  # Use list of str
                ids = {Ref(x[1:]) for x in literal_eval(args["ids"])}  # type: ignore

        if not watch_id:
            raise ValueError("'watchId' must be set")
        provider.watch_unsub(watch_id, ids, close)  # type: ignore
        grid_response = EmptyGrid
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def watch_poll(envs: Dict[str, str], request: HaystackHttpRequest,
               stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'watchPoll'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        watch_id = None
        refresh = False
        if grid_request:
            if "watchId" in grid_request.metadata:
                watch_id = grid_request.metadata["watchId"]
            if "refresh" in grid_request.metadata:
                refresh = True
        if args:
            if "watchId" in args:
                watch_id = args["watchId"]
            if "refresh" in args:
                refresh = True

        grid_response = provider.watch_poll(watch_id, refresh)  # type: ignore
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def point_write(envs: Dict[str, str], request: HaystackHttpRequest,
                stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'pointWrite'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        date_version = None
        level = 17
        val = who = duration = None
        entity_id = None
        default_tz = provider.get_tz()
        if grid_request:
            entity_id = grid_request[0]["id"]  # type: ignore
            date_version = grid_request[0].get("version", None)  # type: ignore
            if "level" in grid_request[0]:
                level = int(grid_request[0]["level"])  # type: ignore
            val = grid_request[0].get("val")  # type: ignore
            who = grid_request[0].get("who")  # type: ignore
            duration = grid_request[0].get("duration")  # type: ignore # Must be quantity

        if "id" in args:
            entity_id = Ref(args["id"][1:])
        if "level" in args:
            level = int(args["level"])
        if "val" in args:
            val = parse_scalar(
                args["val"],
                mode=MODE_ZINC,
            )
        if "who" in args:
            val = args["who"]
        if "duration" in args:
            duration = parse_scalar(args["duration"])
            assert isinstance(duration, Quantity)
        if "version" in args:
            date_version = parse_hs_datetime_format(args["version"], default_tz)
        if entity_id is None:
            raise ValueError("'id' must be set")
        if val is not None:
            provider.point_write_write(
                entity_id, level, val, who, duration, date_version  # type: ignore
            )
            grid_response = EmptyGrid
        else:
            grid_response = provider.point_write_read(entity_id, date_version)  # type: ignore
            assert grid_response is not None
            assert "level" in grid_response.column
            assert "levelDis" in grid_response.column
            assert "val" in grid_response.column
            assert "who" in grid_response.column
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def his_read(envs: Dict[str, str], request: HaystackHttpRequest,
             stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'hisRead'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        entity_id = date_version = None
        date_range = None
        default_tz = provider.get_tz()
        if grid_request:
            if "id" in grid_request.column:
                entity_id = grid_request[0].get("id", "")  # type: ignore
            if "range" in grid_request.column:
                date_range = grid_request[0].get("range", "")  # type: ignore
            date_version = (
                grid_request[0].get("version", None) if grid_request else None  # type: ignore
            )

        # Priority of query string
        if args:
            if "id" in args:
                entity_id = Ref(args["id"][1:])
            if "range" in args:
                date_range = args["range"]
            if "version" in args:
                date_version = parse_hs_datetime_format(args["version"], default_tz)
                date_version = convert_version(date_version)

        grid_date_range = parse_date_range(date_range, provider.get_tz())  # type: ignore
        log.debug(
            "id=%s range=%s, date_version=%s", entity_id, grid_date_range, date_version
        )
        if date_version:
            if isinstance(date_version, date):
                date_version = datetime.combine(date_version, datetime.max.time()) \
                    .replace(tzinfo=provider.get_tz())
            if grid_date_range[1] > date_version:  # type: ignore
                grid_date_range = (grid_date_range[0], date_version)  # type: ignore
        grid_response = provider.his_read(entity_id, grid_date_range, date_version)  # type: ignore
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def his_write(envs: Dict[str, str], request: HaystackHttpRequest,
              stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'hisWrite'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        entity_id = grid_request.metadata.get("id")
        date_version = grid_request.metadata.get("version")
        time_serie_grid = grid_request
        default_tz = provider.get_tz()

        # Priority of query string
        if args:
            if "id" in args:
                entity_id = Ref(args["id"][1:])
            if "ts" in args:  # Array of tuple
                time_serie_grid = Grid(version=VER_3_0, columns=["date", "val"])
                time_serie_grid.extend(
                    [
                        {"date": parse_hs_datetime_format(d, default_tz), "val": v}
                        for d, v in literal_eval(args["ts"])
                    ]
                )
        if "version" in args:
            date_version = parse_hs_datetime_format(args["version"], default_tz)
        grid_response = provider.his_write(entity_id, time_serie_grid, date_version)  # type: ignore
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response


def invoke_action(envs: Dict[str, str], request: HaystackHttpRequest,
                  stage: str, provider: HaystackInterface) -> HaystackHttpResponse:
    """
    Implement Haystack 'invokeAction'.
    Args:
        envs: The environments variables
        provider: HaystackInterface provider to be used
        request: The HTTP Request
        stage: The current stage (`prod`, `dev`, etc.)

    Returns:
        The HTTP Response
    """
    headers, args = (request.headers, request.args)
    try:
        grid_request = _parse_body(request)
        entity_id = grid_request.metadata.get("id")
        action = grid_request.metadata.get("action")
        # Priority of query string
        if args:
            if "id" in args:
                entity_id = Ref(args["id"][1:])
            if "action" in args:
                action = args["action"]
        params = grid_request[0] if grid_request else {}
        grid_response = provider.invoke_action(entity_id, action, params)  # type: ignore
        assert grid_response is not None
        response = _format_response(headers, grid_response, 200, "OK")
    except Exception as ex:  # pylint: disable=broad-except
        response = _manage_exception(headers, ex, stage)
    return response
