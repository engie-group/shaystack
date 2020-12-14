"""
Base of haystack implementation.
"""
from __future__ import annotations

import logging
import os
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date, timedelta, tzinfo
from importlib import import_module
from typing import Any, Tuple, Dict, Union, Optional, List, cast

import pytz
from tzlocal import get_localzone

import haystackapi
from haystackapi import Grid, VER_3_0, Uri, Ref, Quantity, parse_hs_date_format

log = logging.getLogger("haystackapi")

EmptyGrid = Grid(version=VER_3_0, columns={"empty": {}})


def _to_camel(snake_str: str) -> str:
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


@dataclass
class HttpError(Exception):
    """
    Exception to propagate specific HTTP error
    """
    error: int
    msg: str


class HaystackInterface(ABC):
    """
    Interface to implement to be compatible with Haystack REST protocol.
    The subclasses may be abstract (implemented only a part of methods),
    the code detect that, and can calculate the set of implemented operations.
    """

    def __repr__(self):
        return self.name()

    def __str__(self):
        return self.__repr__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def name(self):
        pass

    def get_tz(self):
        return get_localzone()

    def get_customer_id(self) -> str:
        """ Override this for multi-tenant"""
        return ''

    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        """
        Return all differents values for a specific tag
        """
        raise NotImplementedError()

    def versions(self) -> List[datetime]:
        """
        Return datetime for each versions or empty array if is unknown
        """
        return []

    @abstractmethod
    def about(self, home: str) -> Grid:
        """
        Implement the Haystack 'about' ops
        :param home: Home url of the API
        Return the default 'about' grid.
        Must be completed with "productUri", "productVersion", "moduleName" abd "moduleVersion"
        """
        grid = haystackapi.Grid(
            version=VER_3_0,
            columns=[
                "haystackVersion",  # Str version of REST implementation
                "tz",  # Str of server's default timezone
                "serverName",  # Str name of the server or project database
                "serverTime",
                "serverBootTime",
                "productName",  # Str name of the server software product
                "productUri",
                "productVersion",
                # "moduleName",
                # module which implements Haystack server protocol
                # if its a plug-in to the product
                # "moduleVersion"  # Str version of moduleName
            ],
        )
        grid.append(
            {
                "haystackVersion": str(VER_3_0),
                "tz": str(get_localzone()),
                "serverName": "haystack_" + os.environ.get("AWS_REGION", "local"),
                "serverTime": datetime.now(tz=self.get_tz()).replace(microsecond=0),
                "serverBootTime": datetime.now(tz=self.get_tz()).replace(
                    microsecond=0
                ),
                "productName": "AWS Lamdda Haystack Provider",
                "productUri": Uri(home),
                "productVersion": "0.1",
                "moduleName": "URLProvider",
                "moduleVersion": "0.1",
            }
        )
        return grid

    def ops(self) -> Grid:
        """ Implement the Haystack 'ops' ops """
        # Automatically calculate the implemented version.
        grid = haystackapi.Grid(
            version=VER_3_0,
            columns={
                "name": {},
                "summary": {},
            },
        )
        all_haystack_ops = {
            "about": "Summary information for server",
            "ops": "Operations supported by this server",
            "formats": "Grid data formats supported by this server",
            "read": "The read op is used to read a set of entity records either by their unique "
                    "identifier or using a filter.",
            "nav": "The nav op is used navigate a project for learning and discovery",
            "watch_sub": "The watch_sub operation is used to create new watches "
                         "or add entities to an existing watch.",
            "watch_unsub": "The watch_unsub operation is used to close a watch entirely "
                           "or remove entities from a watch.",
            "watch_poll": "The watch_poll operation is used to poll a watch for "
                          "changes to the subscribed entity records.",
            "point_write": "The point_write_read op is used to: read the current status of a "
                           "writable point's priority array "
                           "or write to a given level",
            "his_read": "The his_read op is used to read a time-series data "
                        "from historized point.",
            "his_write": "The his_write op is used to post new time-series "
                         "data to a historized point.",
            "invoke_action": "The invoke_action op is used to invoke a "
                             "user action on a target record.",
        }
        # Remove abstract method
        for abstract_method in self.__class__.__base__.__abstractmethods__:
            all_haystack_ops.pop(abstract_method, None)
        if (
                "point_write_read" in self.__class__.__base__.__abstractmethods__
                or "point_write_write" in self.__class__.__base__.__abstractmethods__
        ):
            all_haystack_ops.pop("point_write", None)
        all_haystack_ops = {_to_camel(k): v for k, v in all_haystack_ops.items()}

        grid.extend(
            [
                {"name": name, "summary": summary}
                for name, summary in all_haystack_ops.items()
            ]
        )
        return grid

    # Implement this method, only if you want to limited the format negociation
    def formats(self) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'formats' ops """
        return None

    @abstractmethod
    def read(
            self,
            limit: int,
            select: Optional[str],
            entity_ids: Optional[Grid],
            grid_filter: Optional[str],
            date_version: Optional[datetime],
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'read' ops
        :param limit: The number of record to return or zero
        :param select: The selected tag separated with comma, else '' or '*'
        :param entity_ids: A list en ids. If set, grid_filter and limit are ignored
        :param grid_filter: A filter to apply. Ignored if entity_ids is set.
        :param date_version: The date to return of the last version.
        """
        # PPR: Add nextToken for paginate ?
        raise NotImplementedError()

    @abstractmethod
    def nav(self, nav_id: str) -> Any:  # pylint: disable=no-self-use
        """ Implement the Haystack 'nav' ops """
        raise NotImplementedError()

    @abstractmethod
    def watch_sub(
            self,
            watch_dis: str,
            watch_id: Optional[str],
            ids: List[Ref],
            lease: Optional[int],
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'watchSub' ops
        :param watch_dis: Watch description
        :param watch_id: The user watch_id to update or None
        :param ids: The list of ids to watch
        :param lease: Lease to apply
        """
        raise NotImplementedError()

    @abstractmethod
    def watch_unsub(
            self, watch_id: str, ids: List[Ref], close: bool
    ) -> None:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'watchUnsub' ops
        :param watch_id: The user watch_id to update or None
        :param ids: The list of ids to watch
        :param close: Set to True to close
        """
        raise NotImplementedError()

    @abstractmethod
    def watch_poll(
            self, watch_id: str, refresh: bool
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'watchPoll' ops
        :param watch_id: The user watch_id to update or None
        :param refresh: Set to True to refresh the data
        """
        raise NotImplementedError()

    @abstractmethod
    def point_write_read(
            self, entity_id: Ref, date_version: Optional[datetime]
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'pointWrite' ops
        :param entity_id: The entity to update
        :param date_version: The optional date version to update
        """
        raise NotImplementedError()

    @abstractmethod
    def point_write_write(
            self,
            entity_id: Ref,
            level: int,
            val: Optional[Any],
            duration: Quantity,
            who: Optional[str],
            date_version: Optional[datetime],
    ) -> None:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'pointWrite' ops
        :param entity_id: The entity to update
        :param level: Number from 1-17 for level to write
        :param val: Value to write or null to auto the level
        :param who: Optional username performing the write, otherwise user dis is used
        :param duration: Number with duration unit if setting level 8
        :param date_version: The optional date version to update
        """
        raise NotImplementedError()

    # Date dates_range must be:
    # "today"
    # "yesterday"
    # "{date}"
    # "{date},{date}"
    # "{dateTime},{dateTime}"
    # "{dateTime}"
    @abstractmethod
    def his_read(
            self,
            entity_id: Ref,
            dates_range: Optional[Tuple[datetime, datetime]],
            date_version: Optional[datetime],
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'hisRead' ops
        :param entity_id: The entity to read
        :param dates_range: The date range.
        May be "today", "yesterday", {date}, ({date},{date}), ({datetime},{datetime}), {dateTime}
        :param date_version: The optional date version to update
        """
        raise NotImplementedError()

    @abstractmethod
    def his_write(
            self, entity_id: Ref, time_serie: Grid,
            date_version: Optional[datetime]
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'hisWrite' ops
        :param entity_id: The entity to read
        :param time_serie: A grid with a time series
        :param date_version: The optional date version to update
        """
        raise NotImplementedError()

    @abstractmethod
    def invoke_action(
            self, entity_id: Ref, action: str, params: Dict[str, Any],
            date_version: Optional[datetime] = None

    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'invokeAction' ops
        :param entity_id: The entity to read
        :param action: The action string
        :param params: A dictionary with parameters
        :param date_version: The optional date version to update
        """
        raise NotImplementedError()


_providers = {}


def no_cache():
    """ Must be patched in unit test """
    return False


def get_provider(class_str) -> HaystackInterface:
    """Return an instance of the provider.
    If the provider is an abstract class, create a sub class with all the implementation
    and return an instance of this subclass. Then, the 'ops' method can analyse the current instance
    and detect the implemented and abstract methods.
    """
    try:
        if not class_str.endswith(".Provider"):
            class_str += ".Provider"
        if class_str in _providers:
            return _providers[class_str]
        module_path, class_name = class_str.rsplit(".", 1)
        module = import_module(module_path)
        # Get the abstract class name
        provider_class = getattr(module, class_name)

        # Implement all abstract method.
        # Then, it's possible to generate the Ops operator dynamically
        # pylint: disable=missing-function-docstring,useless-super-delegation
        class FullInterface(provider_class):  # pylint: disable=missing-class-docstring
            def __init__(self):
                super().__init__()

            def about(
                    self, home: str
            ) -> Grid:  # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().about(home)

            def read(
                    self,
                    limit: int,
                    select: Optional[str],
                    entity_id: Optional[Grid],
                    grid_filter: Optional[str],
                    date_version: Optional[datetime],
            ) -> Grid:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().read(limit, select, entity_id, grid_filter, date_version)

            def nav(self, nav_id: str) -> Any:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().nav(nav_id)

            def watch_sub(
                    self,
                    watch_dis: str,
                    watch_id: Optional[str],
                    ids: List[Ref],
                    lease: Optional[int],
            ) -> Grid:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().watch_sub(watch_dis, watch_id, ids, lease)

            def watch_unsub(
                    self, watch_id: str, ids: List[Ref], close_all: bool
            ) -> None:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().watch_unsub(watch_id, ids, close_all)

            def watch_poll(self, watch_id: str, refresh: bool) -> Grid:
                return super().watch_poll(watch_id, refresh)

            def point_write_read(  # pylint: disable=missing-function-docstring,useless-super-delegation
                    self, entity_id: Ref, date_version: Optional[datetime]
            ) -> Grid:
                return super().point_write_read(entity_id, date_version)

            def point_write_write(  # pylint: disable=missing-function-docstring,useless-super-delegation
                    self,
                    entity_id: Ref,
                    level: int,
                    val: Optional[Any],
                    duration: Quantity,
                    who: Optional[str],
                    date_version: Optional[datetime],
            ) -> None:  # pylint: disable=no-self-use
                return super().point_write_write(
                    entity_id, level, val, duration, who, date_version
                )

            def his_read(  # pylint: disable=missing-function-docstring,useless-super-delegation
                    self,
                    entity_id: Ref,
                    date_range: Optional[Tuple[datetime, datetime]],
                    date_version: Optional[datetime],
            ) -> Grid:
                return super().his_read(entity_id, date_range, date_version)

            def his_write(  # pylint: disable=missing-function-docstring, useless-super-delegation
                    self, entity_id: Ref, time_serie: Grid, date_version: Optional[datetime]
            ) -> Grid:
                return super().his_write(entity_id, time_serie, date_version)

            def invoke_action(  # pylint: disable=missing-function-docstring,useless-super-delegation
                    self,
                    entity_id: Ref,
                    action: str,
                    params: Dict[str, Any],
            ) -> Grid:
                return super().invoke_action(entity_id, action, params)

        _providers[class_str] = FullInterface()
        return _providers[class_str]
    except (ImportError, AttributeError):
        traceback.print_exc()
        raise


_singleton_provider = None


def get_singleton_provider() -> HaystackInterface:
    global _singleton_provider
    assert (
            "HAYSTACK_PROVIDER" in os.environ
    ), "Set 'HAYSTACK_PROVIDER' environment variable"
    if not _singleton_provider or no_cache():
        log.debug("Provider=%s", os.environ["HAYSTACK_PROVIDER"])
        _singleton_provider = get_provider(os.environ["HAYSTACK_PROVIDER"])
    return _singleton_provider


def parse_date_range(date_range: str, tz: tzinfo) -> Optional[
    Union[datetime, datetime],
]:
    if not date_range:
        return datetime.min.replace(tzinfo=pytz.UTC), \
               datetime.max.replace(tzinfo=pytz.UTC)
    if date_range not in ("today", "yesterday"):
        split_date = [parse_hs_date_format(x) for x in date_range.split(",")]
        if len(split_date) > 1:
            assert type(split_date[0]) == type(  # pylint: disable=C0123
                split_date[1]
            )
            if isinstance(split_date[0], datetime):
                return cast(Tuple[datetime, datetime], tuple(split_date))
            else:
                return \
                    (datetime.combine(split_date[0], datetime.min.time()).replace(tzinfo=tz),
                     datetime.combine(split_date[1], datetime.min.time()).replace(tzinfo=tz))
        else:
            if isinstance(split_date[0], datetime):
                return (split_date[0], split_date[0] + timedelta(days=1, milliseconds=-1))
            else:
                tzdate = datetime.combine(split_date[0], datetime.min.time()).replace(tzinfo=tz)
                return tzdate, tzdate + timedelta(days=1, milliseconds=-1)
    else:
        if date_range == "today":
            today = datetime.combine(date.today(), datetime.min.time()) \
                .replace(tzinfo=tz)
            return today, today + timedelta(days=1, milliseconds=-1)
        if date_range == "yesterday":
            yesterday = datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
                .replace(tzinfo=tz)
            return yesterday, yesterday + timedelta(days=1, milliseconds=-1)
        raise ValueError(f"date_range {date_range} unknown")
