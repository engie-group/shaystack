"""
Base of haystack implementation.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from importlib import import_module
from typing import Any, Tuple, Dict, Union, Optional, List

from tzlocal import get_localzone

import hszinc
from hszinc import Grid, VER_3_0, Uri, Ref, Quantity

EmptyGrid = Grid(version=VER_3_0, columns={"empty": {}})


def _to_camel(snake_str: str) -> str:
    first, *others = snake_str.split('_')
    return ''.join([first.lower(), *map(str.title, others)])


@dataclass
class HttpError(Exception):
    error: int
    msg: str

class HaystackInterface(ABC):
    """
    Interface to implement to be compatible with Haystack REST protocol.
    The subclasses may be abstract (implemented only a part of methods),
    the code detect that, and can calculate the set of implemented operations.
    """

    def __repr__(self):
        return repr(self.__class__.__subclasses__())

    def __str__(self):
        return self.__repr__()

    @abstractmethod
    def about(self, home: str) -> Grid:
        """ Implement the Haystack 'about' ops
        :param home: Home url of the API
        Return the default 'about' grid.
        Must be completed with "productUri", "productVersion", "moduleName" abd "moduleVersion"
        """
        grid = hszinc.Grid(version=VER_3_0,
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
                               # module which implements Haystack server protocol if its a plug-in to the product
                               # "moduleVersion"  # Str version of moduleName
                           ])
        grid.append(
            {
                "haystackVersion": str(VER_3_0),
                "tz": str(get_localzone()),
                "serverName": "haystack_" + os.environ.get("AWS_REGION", "local"),
                "serverTime": datetime.now(tz=get_localzone()).replace(microsecond=0),
                "serverBootTime": datetime.now(tz=get_localzone()).replace(microsecond=0),
                "productName": "AWS Lamdda Haystack Provider",
                "productUri": Uri(home),
                "productVersion": "0.1",
                "moduleName": "URLProvider",
                "moduleVersion": "0.1"
            })
        return grid

    def ops(self) -> Grid:
        """ Implement the Haystack 'ops' ops """
        # Automatically calculate the implemented version.
        grid = hszinc.Grid(version=VER_3_0, columns={
            "name": {},
            "summary": {},
        })
        all_haystack_ops = {
            "about": "Summary information for server",
            "ops": "Operations supported by this server",
            "formats": "Grid data formats supported by this server",
            "read": "The read op is used to read a set of entity records either by their unique "
                    "identifier or using a filter.",
            "nav": "The nav op is used navigate a project for learning and discovery",
            "watch_sub": "The watch_sub operation is used to create new watches or add entities to an existing watch.",
            "watch_unsub": "The watch_unsub operation is used to close a watch entirely "
                           "or remove entities from a watch.",
            "watch_poll": "The watch_poll operation is used to poll a watch for "
                          "changes to the subscribed entity records.",
            "point_write": "The point_write_read op is used to: read the current status of a "
                           "writable point's priority array "
                           "or write to a given level",
            "his_read": "The his_read op is used to read a time-series data from historized point.",
            "his_write": "The his_write op is used to post new time-series data to a historized point.",
            "invoke_action": "The invoke_action op is used to invoke a user action on a target record.",
        }
        # Remove abstract method
        for x in self.__class__.__base__.__abstractmethods__:
            all_haystack_ops.pop(x, None)
        if "point_write_read" in self.__class__.__base__.__abstractmethods__ or \
                "point_write_write" in self.__class__.__base__.__abstractmethods__:
            all_haystack_ops.pop("point_write", None)
        all_haystack_ops = {_to_camel(k): v for k, v in all_haystack_ops.items()}

        grid.extend([{"name": name, "summary": summary} for name, summary in all_haystack_ops.items()])
        return grid

    # Implement this method, only if you want to limited the format negociation
    def formats(self) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'formats' ops """
        return None

    @abstractmethod
    def read(self, limit: int, entity_ids: Optional[Grid], grid_filter: Optional[str],
             date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'read' ops """
        raise NotImplementedError()

    @abstractmethod
    def nav(self, nav_id: str) -> Any:  # pylint: disable=no-self-use
        """ Implement the Haystack 'nav' ops """
        raise NotImplementedError()

    @abstractmethod
    def watch_sub(self, watch_dis: str, watch_id: str, ids: List[Ref],
                  lease: Optional[int]) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'watchSub' ops """
        raise NotImplementedError()

    @abstractmethod
    def watch_unsub(self, watch_id: str, ids: List[Ref], close: bool) -> None:  # pylint: disable=no-self-use
        """ Implement the Haystack 'watchUnsub' ops """
        raise NotImplementedError()

    @abstractmethod
    def watch_poll(self, watch_id: str, refresh: bool) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'watchPoll' ops """
        raise NotImplementedError()

    @abstractmethod
    def point_write_read(self,
                         entity_id: Ref,
                         date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'pointWrite' ops """
        raise NotImplementedError()

    @abstractmethod
    def point_write_write(self,
                          entity_id: Ref,
                          level: int,
                          val: Optional[Any],
                          duration: Quantity,
                          who: Optional[str],
                          date_version: Optional[datetime]) -> None:  # pylint: disable=no-self-use
        """ Implement the Haystack 'pointWrite' ops """
        raise NotImplementedError()

    # Date dates_range must be:
    # "today"
    # "yesterday"
    # "{date}"
    # "{date},{date}"
    # "{dateTime},{dateTime}"
    # "{dateTime}"
    @abstractmethod
    def his_read(self, entity_ids: Ref,
                 dates_range: Optional[Union[Union[datetime, str],
                                             Tuple[datetime, Optional[datetime]],
                                             Tuple[date, Optional[date]]]],
                 date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'hisRead' ops """
        raise NotImplementedError()

    @abstractmethod
    def his_write(self,
                  entity_id: Ref,
                  ts: Grid,
                  date_version: Optional[datetime]) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'hisWrite' ops """
        raise NotImplementedError()

    @abstractmethod
    def invoke_action(self, entity_id: Ref, action: str, params: Dict[str, Any]) -> Grid:  # pylint: disable=no-self-use
        """ Implement the Haystack 'invokeAction' ops """
        raise NotImplementedError()


_providers = {}  # Cached providers


def get_provider(class_str) -> HaystackInterface:
    """ Return an instance of the provider.
    If the provider is an abstract class, create a sub class with all the implementation
    and return an instance of this subclass. Then, the 'ops' method can analyse the current instance
    and detect the implemented and abstract methods.
    """
    try:
        if not class_str.endswith(".Provider"):
            class_str = class_str + ".Provider"
        if class_str in _providers:
            return _providers[class_str]

        module_path, class_name = class_str.rsplit('.', 1)
        module = import_module(module_path)
        # Get the abstract class name
        provider_class = getattr(module, class_name)

        # Implement all abstract method.
        # Then, it's possible to generate the Ops operator dynamically
        class FullInterface(provider_class):  # pylint: disable=missing-class-docstring
            def about(self, home: str) -> Grid:  # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().about(home)

            def read(self, limit: int, entity_id: Optional[Grid], grid_filter: Optional[str],
                     date_version: Optional[datetime]) -> Grid:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().read(limit, entity_id, grid_filter, date_version)

            def nav(self, nav_id: str) -> Any:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().nav(nav_id)

            def watch_sub(self, watch_dis: str, watch_id: str, ids: List[Ref], lease: Optional[int]) -> Grid:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().watch_sub(watch_dis, watch_id, ids, lease)

            def watch_unsub(self, watch_id: str, ids: List[Ref], close_all: bool) -> None:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().watch_unsub(watch_id, ids, close_all)

            def watch_poll(self, watch_id: str, refresh: bool) -> Grid:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().watch_poll(watch_id, refresh)

            def point_write_read(self, entity_id: Ref, date_version: Optional[datetime]) -> Grid:
                # pylint: disable=missing-function-docstring,useless-super-delegation
                return super().point_write_read(entity_id, date_version)

            def point_write_write(self,
                                  entity_id: Ref,
                                  level: int,
                                  val: Optional[Any],
                                  duration: Quantity,
                                  who: Optional[str],
                                  date_version: Optional[datetime]) -> None:  # pylint: disable=no-self-use
                return super().point_write_write(entity_id, level, val, duration, who, date_version)

            def his_read(self, entity_id: Ref,
                         # pylint: disable=missing-function-docstring,useless-super-delegation
                         date_range: Optional[Union[Union[datetime, str],
                                                    Tuple[datetime, Optional[datetime]],
                                                    Tuple[date, Optional[date]]]],
                         date_version: Optional[datetime]) -> Grid:
                return super().his_read(entity_id, date_range, date_version)

            def his_write(self, entity_id: Ref,
                          ts: Grid,
                          date_version: Optional[datetime]) -> Grid:
                # pylint: disable=missing-function-docstring, useless-super-delegation
                return super().his_write(entity_id, ts, date_version)

            def invoke_action(self,  # pylint: disable=missing-function-docstring,useless-super-delegation
                              entity_id: Ref, action: str, params: Dict[str, Any]) -> Grid:
                return super().invoke_action(entity_id, action, params)

        _providers[class_str] = FullInterface()
        return _providers[class_str]
    except (ImportError, AttributeError):
        raise ImportError(class_str)  # pylint: disable=raise-missing-from
