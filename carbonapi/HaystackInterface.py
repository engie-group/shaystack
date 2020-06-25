from abc import ABC, abstractmethod
from datetime import datetime
from importlib import import_module
from typing import Any, Tuple, Dict

import hszinc
from hszinc import Grid


class EmptyGrid(Grid):
    class _EmptyGrid():
        def __str__(self):
            return "EmptyGrid()"

    _empty = _EmptyGrid()

    def __new__(cls):
        return EmptyGrid._empty





class HaystackInterface(ABC):
    @abstractmethod
    def about(self) -> Grid:
        raise NotImplemented()

    def ops(self) -> Grid:  # TODO: faire un TU de cela
        """Automatically calcule the implemented version.
        """
        grid = hszinc.Grid(columns={
            "name": {},
            "summary": {},
        })
        all_haystack_ops = {
            "about": "Summary information for server",
            "ops": "Operations supported by this server",
            "formats": "Grid data formats supported by this server",
            "read": "The read op is used to read a set of entity records either by their unique identifier or using a filter.",
            "nav": "The nav op is used navigate a project for learning and discovery",
            "watchSub": "The watchSub operation is used to create new watches or add entities to an existing watch.",
            "watchUnsub": "The watchUnsub operation is used to close a watch entirely or remove entities from a watch.",
            "watchPoll": "The watchPoll operation is used to poll a watch for changes to the subscribed entity records.",
            "pointWrite": "The pointWrite op is used to: read the current status of a writable point's priority array or write to a given level",
            "hisRead": "The hisRead op is used to read a time-series data from historized point.",
            "hisWrite": "The hisWrite op is used to post new time-series data to a historized point.",
            "invokeAction": "The invokeAction op is used to invoke a user action on a target record.",
        }
        #    {"name": "extend_with_co2e", "summary": "Extend with with CO2e"},
        # Remove abstract method
        for x in self.__class__.__base__.__abstractmethods__:
            all_haystack_ops.pop(x, None)
        grid.extend([{"name": name, "summary": summary} for name,summary in all_haystack_ops.items()])
        return grid

    """Implement this method, only if you want to limited the format negociation"""
    def formats(self) -> Grid:
        return None

    @abstractmethod
    def read(self, filter: str, limit: int) -> Grid:
        raise NotImplemented()

    @abstractmethod
    def nav(self, navId:Grid) -> Any:  # FIXME Voir comment implementer
        raise NotImplemented()

    @abstractmethod
    def watchSub(self, watchId: Grid) -> Grid:
        raise NotImplemented()

    @abstractmethod
    def watchUnsub(self, watchId: Grid) -> EmptyGrid:
        raise NotImplemented()

    @abstractmethod
    def watchPoll(self, watchId: Grid) -> Grid:
        raise NotImplemented()

    @abstractmethod
    def pointWrite(self, id: str) -> Grid:
        raise NotImplemented()

    # Date range must be:
    # "today"
    # "yesterday"
    # "{date}"
    # "{date},{date}"
    # "{dateTime},{dateTime}"
    # "{dateTime}"
    @abstractmethod
    def hisRead(self, id: str, range: Tuple[datetime, datetime]) -> Grid:
        raise NotImplemented()

    @abstractmethod
    def hisWrite(self, id: str) -> EmptyGrid:
        raise NotImplemented()

    @abstractmethod
    def invokeAction(self, id: str, action: str, params: Dict[str, Any]) -> Grid:
        raise NotImplemented()


def get_provider(class_str) -> HaystackInterface:
    try:
        module_path, class_name = class_str.rsplit('.', 1)
        module = import_module(module_path)
        # Get the abstract class name
        class_ = getattr(module, class_name)
        # Implement all abstract method.
        # Then, it's possible to generate the Ops dynamically
        class FullInterface(class_):
            def about(self) -> Grid:
                return super().about()

            def read(self, filter: str, limit: int) -> Grid:
                return super().read(filter, limit)

            def nav(self, navId: Grid) -> Any:  # FIXME Voir comment implementer
                return super().nav(navId)

            def watchSub(self, watchId: Grid) -> Grid:
                return super().watchSub(watchId)

            def watchUnsub(self, watchId: Grid) -> EmptyGrid:
                return super().watchUnsub

            def watchPoll(self, watchId: Grid) -> Grid:
                return super().watchPoll(watchId)

            def pointWrite(self, id: str) -> Grid:
                return super().pointWrite(id)

            def hisRead(self, id: str, range: Tuple[datetime, datetime]) -> Grid:
                return super().hisRead(id, range)

            def hisWrite(self, id: str) -> EmptyGrid:
                return super().hisWrite(id)

            def invokeAction(self, id: str, action: str, params: Dict[str, Any]) -> Grid:
                return super().invokeAction()

        return FullInterface()
    except (ImportError, AttributeError) as e:
        raise ImportError(class_str)

