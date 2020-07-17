from datetime import datetime
from typing import Union, Tuple, Dict, Any

from overrides import overrides

from hszinc import Grid
from providers.haystack_interface import HaystackInterface, get_provider


class _NoImplementation(HaystackInterface):
    pass


def test_ops_without_implementation():
    # GIVEN
    provider = get_provider('test_haystack_interface._NoImplementation')

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 2


class _ReadImplementation(HaystackInterface):
    @overrides
    def read(self, grid_filter: str, limit: int) -> Grid:
        pass

    @overrides
    def his_read(self, id: str,
                 range: Union[Union[datetime, str], Tuple[Union[datetime, str], Union[datetime, str]]]) -> Grid:
        pass


def test_ops_with_readonly():
    # GIVEN
    provider = get_provider('test_haystack_interface._ReadImplementation')

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 4
    assert ops[2]['name'] == 'read'
    assert ops[3]['name'] == 'hisRead'


class _WriteImplementation(HaystackInterface):
    @overrides
    def point_write(self, id: str) -> Grid:
        pass

    @overrides
    def his_write(self, id: str) -> Grid:
        pass


def test_ops_with_writeonly():
    # GIVEN
    provider = get_provider('test_haystack_interface._WriteImplementation')

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 4
    assert ops[2]['name'] == 'pointWrite'
    assert ops[3]['name'] == 'hisWrite'


class _SubscribeImplementation(HaystackInterface):
    @overrides
    def watch_poll(self, watchId: Grid) -> Grid:
        pass

    @overrides
    def watch_sub(self, watchId: Grid) -> Grid:
        pass

    @overrides
    def watch_unsub(self, watchId: Grid) -> Grid:
        pass


def test_ops_with_subscribe():
    # GIVEN
    provider = get_provider('test_haystack_interface._SubscribeImplementation')

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 5
    assert ops[2]['name'] == 'watchSub'
    assert ops[3]['name'] == 'watchUnsub'
    assert ops[4]['name'] == 'watchPoll'


class _InvokeActionImplementation(HaystackInterface):
    @overrides
    def invoke_action(self, id: str, action: str, params: Dict[str, Any]) -> Grid:
        pass


def test_ops_with_invoke_action():
    # GIVEN
    provider = get_provider('test_haystack_interface._InvokeActionImplementation')

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 3
    assert ops[2]['name'] == 'invokeAction'


class _NavImplementation(HaystackInterface):
    @overrides
    def nav(self, nav_id: Grid) -> Any:
        pass


def test_ops_with_nav():
    # GIVEN
    provider = get_provider('test_haystack_interface._NavImplementation')

    # WHEN
    ops = provider.ops()

    # THEN
    assert len(ops) == 3
    assert ops[2]['name'] == 'nav'
