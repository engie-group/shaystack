# -*- coding: utf-8 -*-
# Abstract interface
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Base of haystack implementation.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date, timedelta, tzinfo
from importlib import import_module
from typing import Any, Tuple, Dict, Optional, List, cast

import pytz
from pytz import BaseTzInfo
from tzlocal import get_localzone

from ..datatypes import Ref, Quantity, Uri
from ..grid import Grid, VER_3_0
from ..grid_filter import parse_hs_datetime_format

log = logging.getLogger("shaystack")


def _to_camel(snake_str: str) -> str:
    first, *others = snake_str.split("_")
    return "".join([first.lower(), *map(str.title, others)])


@dataclass
class HttpError(Exception):
    """
    Exception to propagate a specific HTTP error
    """
    error: int
    msg: str


# noinspection PyMethodMayBeStatic
class HaystackInterface(ABC):
    """
    Interface to implement to be compatible with Haystack REST protocol.
    The subclasses may be abstract (implemented only a part of methods),
    the 'ops' code detect that, and can calculate the set of implemented operations.
    """
    __slots__ = ['_envs']

    def __init__(self, envs: Dict[str, str]):
        assert envs is not None
        self._envs = envs

    @property
    @abstractmethod
    def name(self) -> str:
        """ The name of the provider. """
        raise NotImplementedError()

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.__repr__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    # noinspection PyMethodMayBeStatic
    def get_tz(self) -> BaseTzInfo:  # pylint: disable=no-self-use
        """ Return server time zone. """
        return get_localzone()

    def get_customer_id(self) -> str:  # pylint: disable=no-self-use
        """ Override this for multi-tenant.
        May be, extract the customer id from the current `Principal`.
        """
        return ''

    def values_for_tag(self, tag: str,
                       date_version: Optional[datetime] = None) -> List[Any]:
        """Get all values for a given tag.

        Args:
            tag: The tag to analyse.
            date_version: version date of the ontology.

        Returns:
            All unique values for a specific tag
        """
        raise NotImplementedError()

    def versions(self) -> List[datetime]:  # pylint: disable=no-self-use
        """
        Return a list of versions fot the current ontology.
        Returns:
            datetime for each version or empty array if unknown
        """
        return []

    @abstractmethod
    def about(self, home: str) -> Grid:
        """Implement the Haystack 'about' ops.

        The subclasse must complet the result with "productUri", "productVersion", "moduleName"
        and "moduleVersion"

        Args:
            home: Home url of the API

        Returns:
            The default 'about' grid.
        """
        grid = Grid(
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
                # module which implements Haystack server protocol
                "moduleName",
                # if its a plug-in to the product
                "moduleVersion"  # Str version of moduleName
            ],
        )
        grid.append(
            {
                "haystackVersion": str(VER_3_0),
                "tz": str(self.get_tz()),
                "serverName": "haystack_" + self._envs.get("AWS_REGION", "local"),
                "serverTime": datetime.now(tz=self.get_tz()).replace(microsecond=0),
                "serverBootTime": datetime.now(tz=self.get_tz()).replace(
                    microsecond=0
                ),
                "productName": "Haystack Provider",
                "productUri": Uri(home),
                "productVersion": "0.1",
                "moduleName": "AbstractProvider",
                "moduleVersion": "0.1",
            }
        )
        return grid

    # noinspection PyUnresolvedReferences
    def ops(self) -> Grid:
        """ Implement the Haystack 'ops' ops.

        Notes:
            Automatically calculate the implemented version.

        Returns:
            A Grid containing 'ops' name operations and its related description
        """
        grid = Grid(
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
        # noinspection PyUnresolvedReferences
        for abstract_method in self.__class__.__base__.__abstractmethods__:  # type: ignore
            all_haystack_ops.pop(abstract_method, None)
        if (
                "point_write_read" in self.__class__.__base__.__abstractmethods__  # type: ignore
                or "point_write_write" in self.__class__.__base__.__abstractmethods__  # type: ignore
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

    def formats(self) -> Optional[Grid]:  # pylint: disable=no-self-use
        """ Implement the Haystack 'formats' ops.

        Notes:
            Implement this method, only if you want to limit the format negotiation
        Returns:
            The grid format or None. If None, the API accept all formats ZINC, TRIO, JSON and CSV.
        """
        return None  # type: ignore

    @abstractmethod
    def read(
            self,
            limit: int,
            select: Optional[str],
            entity_ids: Optional[List[Ref]],
            grid_filter: Optional[str],
            date_version: Optional[datetime],
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'read' ops.

        Args:
            limit: The number of record to return or zero
            select: The selected tag separated with comma, else '' or '*'
            entity_ids: A list en ids. If set, grid_filter and limit are ignored.
            grid_filter: A filter to apply. Ignored if entity_ids is set.
            date_version: The date of the ontology version.

        Returns:
            The requested Grid
        """
        raise NotImplementedError()

    @abstractmethod
    def nav(self, nav_id: str) -> Any:  # pylint: disable=no-self-use
        """ Implement the Haystack 'nav' ops.
        This operation allows servers to expose the database in a human-friendly tree (or graph)
        that can be explored

        Args:
             nav_id: The string for nav id column
        """
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
        Implement the Haystack 'watchSub' ops.

        Args:
            watch_dis: Watch description
            watch_id: The user watch_id to update or None.
            ids: The list of ids to watch.
            lease: Lease to apply.

        Returns:
            A Grid
        """
        raise NotImplementedError()

    @abstractmethod
    def watch_unsub(
            self, watch_id: str, ids: List[Ref], close: bool
    ) -> Grid:  # pylint: disable=no-self-use
        """
        Implement the Haystack 'watchUnsub' ops.

        Args:
            watch_id: The user watch_id to update or None
            ids: The list of ids to watch
            close: Set to True to close

        Returns:
            A Grid
        """
        raise NotImplementedError()

    @abstractmethod
    def watch_poll(
            self, watch_id: str, refresh: bool
    ) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'watchPoll' ops.

        Args:
            watch_id: The user watch_id to update or None
            refresh: Set to True for refreshing the data

        Returns:
            A Grid where each row corresponds to a watched entity.
        """
        raise NotImplementedError()

    @abstractmethod
    def point_write_read(
            self, entity_id: Ref, date_version: Optional[datetime]
    ) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'pointWrite' ops.

        Args:
            entity_id: The entity to update
            date_version: The optional date version to update

        Returns:
            A Grid
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
            date_version: Optional[datetime] = None,
    ) -> None:  # pylint: disable=no-self-use
        """ Implement the Haystack 'pointWrite' ops.

        Args:
            entity_id: The entity to update
            level: Number from 1-17 for level to write
            val: Value to write or null to auto the level
            duration: Number with duration unit if setting level 8
            who: Optional username performing the write, otherwise user dis is used
            date_version: The optional date version to update

        Returns:
            None
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
            dates_range: Tuple[datetime, datetime],
            date_version: Optional[datetime] = None,
    ) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'hisRead' ops.

        Args:
            entity_id: The entity to read
            dates_range: May be "today", "yesterday", {date}, ({date},{date}), ({datetime},{datetime}),
            {dateTime}
            date_version: The optional date version to read

        Returns:
            A grid
        """
        raise NotImplementedError()

    @abstractmethod
    def his_write(
            self,
            entity_id: Ref,
            time_series: Grid,
            date_version: Optional[datetime] = None
    ) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'hisWrite' ops.

        Args:
            entity_id: The entity to read
            time_series: A grid with a time series
            date_version: The optional date version to update

        Returns:
            A grid
        """
        raise NotImplementedError()

    @abstractmethod
    def invoke_action(
            self,
            entity_id: Ref,
            action: str,
            params: Dict[str, Any],
            date_version: Optional[datetime] = None
    ) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'invokeAction' ops.

        Args:
            entity_id: The entity to read
            action: The action string
            params: A dictionary with parameters
            date_version: The optional date version to update

        Returns:
            A grid
        """
        raise NotImplementedError()


_providers = {}


def no_cache(envs: Dict[str, str]):
    """ Must be patched in unit test """
    return int(envs.get("REFRESH", "15")) == 0


# noinspection PyProtectedMember,PyUnresolvedReferences
def get_provider(class_str: str, envs: Dict[str, str],  # pylint: disable=protected-access
                 ) -> HaystackInterface:
    """Return an instance of the provider.
    If the provider is an abstract class, create a sub class with all the implementation
    and return an instance of this subclass. Then, the 'ops' method can analyse the current instance
    and detect the implemented and abstract methods.

    Args:
        class_str: The name of the module that contains the provider.
        envs: Environement variable (os.env ?)

    Returns:
        A instance of this subclass if it exists
    """
    if not class_str.endswith(".Provider"):
        class_str += ".Provider"

    module_path, class_name = class_str.rsplit(".", 1)
    module = import_module(module_path)
    # Get the abstract class name
    provider_class = getattr(module, class_name)

    # Implement all abstract method.
    # Then, it's possible to generate the Ops operator dynamically
    # pylint: disable=missing-function-docstring,useless-super-delegation
    # noinspection PyShadowingNames
    class FullInterface(provider_class):   # type: ignore # pylint: disable=missing-class-docstring
        def __init__(self, envs: Dict[str, str]):
            provider_class.__init__(self, envs)

        def name(self) -> str:
            return super().name()

        def about(
                self, home: str
        ) -> Grid:  # pylint: disable=missing-function-docstring,useless-super-delegation
            return super().about(home)

        def read(
                self,
                limit: int,
                select: Optional[str],
                entity_ids: Optional[List[Ref]],
                grid_filter: Optional[str],
                date_version: Optional[datetime],
        ) -> Grid:
            # pylint: disable=missing-function-docstring,useless-super-delegation
            return super().read(limit, select, entity_ids, grid_filter, date_version)

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

    _providers[class_str] = FullInterface(envs)
    return _providers[class_str]


_DATETIME_MIN_TZ = datetime.min.replace(tzinfo=pytz.utc)
_DATETIME_MAX_TZ = datetime.max.replace(tzinfo=pytz.utc)


def parse_date_range(date_range: str, timezone: tzinfo) -> Tuple[datetime, datetime]:
    """
    Parse a date_range string.
    Args:
        date_range: The string with different acceptable format.
        timezone: The current time-zone to convert the date to datetime.

    Returns:
        A tuple with the begin (inclusive) and end datetime (exclusive).
    """
    if not date_range:
        return datetime.min.replace(tzinfo=pytz.UTC), \
               datetime.max.replace(tzinfo=pytz.UTC)
    if date_range not in ("today", "yesterday"):
        str_date = date_range.split(",")
        split_date = [parse_hs_datetime_format(x, timezone) if x else None for x in str_date]
        if len(str_date) > 1:
            if str_date[1] in ("today", "yesterday"):
                split_date[1] += timedelta(days=1)  # type: ignore

            # Convert to same type
            if isinstance(split_date[0], datetime) or isinstance(split_date[1], datetime):
                # One is a datetime. The other must be convert to datetime
                if not split_date[0]:
                    split_date[0] = _DATETIME_MIN_TZ
                if not isinstance(split_date[0], datetime):
                    split_date[0] = datetime.combine(split_date[0], datetime.min.time())  # type: ignore
                if not split_date[1]:
                    split_date[1] = _DATETIME_MAX_TZ
                if not isinstance(split_date[1], datetime):
                    split_date[1] = datetime.combine(split_date[1], datetime.min.time())  # type: ignore

            # Add missing tzinfo
            if isinstance(split_date[0], datetime) and not split_date[0].tzinfo:
                split_date[0] = split_date[0].replace(tzinfo=timezone)
            if len(str_date) > 1 and isinstance(split_date[1], datetime) and not split_date[1].tzinfo:
                split_date[1] = split_date[1].replace(tzinfo=timezone)

            # Add missing part
            if isinstance(split_date[0], datetime) or isinstance(split_date[1], datetime):
                if not split_date[0]:
                    split_date[0] = _DATETIME_MIN_TZ
                if not split_date[1]:
                    split_date[1] = _DATETIME_MAX_TZ
            elif isinstance(split_date[0], date) or isinstance(split_date[1], date):
                if not split_date[0]:
                    split_date[0] = _DATETIME_MIN_TZ
                if not split_date[1]:
                    split_date[1] = _DATETIME_MAX_TZ
                if not isinstance(split_date[0], datetime):
                    if split_date[0] == date.min:
                        split_date[0] = _DATETIME_MIN_TZ
                    else:
                        split_date[0] = datetime.combine(split_date[0],
                                                         datetime.min.time()).replace(tzinfo=timezone)

                if not isinstance(split_date[1], datetime):
                    if split_date[1] == date.max:
                        split_date[1] = _DATETIME_MAX_TZ
                    else:
                        split_date[1] = datetime.combine(split_date[1],
                                                         datetime.max.time()).replace(tzinfo=timezone)
            return cast(Tuple[datetime, datetime], (split_date[0], split_date[1]))
        if isinstance(split_date[0], datetime):
            if not split_date[0].tzinfo:
                split_date[0] = split_date[0].replace(tzinfo=timezone)
            return split_date[0], _DATETIME_MAX_TZ
        assert isinstance(split_date[0], date)
        split_date[0] = datetime.combine(split_date[0], datetime.min.time()).replace(tzinfo=timezone)
        return split_date[0], split_date[0] + timedelta(days=1)

    if date_range == "today":
        today = datetime.combine(date.today(), datetime.min.time()) \
            .replace(tzinfo=timezone)
        return today, today + timedelta(days=1)
    if date_range == "yesterday":
        yesterday = datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) \
            .replace(tzinfo=timezone)
        return yesterday, yesterday + timedelta(days=1)
    raise ValueError(f"date_range {date_range} unknown")
