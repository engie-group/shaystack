# -*- coding: utf-8 -*-
# Protocol to using SQL driver
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Typing wrapper for sql drivers
"""
# Typing for DB driver
import sys
from typing import Tuple, Optional, List, Iterable, Iterator

# type: ignore
if sys.version_info[0:2] == (3, 7):
    from typing import Type

    Protocol = Type
else:
    from typing import Protocol  # pylint: disable=no-name-in-module


# pylint: disable=multiple-statements, no-self-use, missing-class-docstring
class DBCursor(Protocol):
    def execute(self, cmd: str, args: Optional[Tuple] = None) -> Iterable[Tuple]: ...

    def fetchall(self) -> List[List]: ...

    def fetchone(self) -> Iterable: ...

    def executemany(self, sql: str, params: Iterable) -> None: ...

    def close(self) -> None: ...

    def __iter__(self) -> Iterator[List]: return [].__iter__()


class DBConnection(Protocol):  # pylint: disable=multiple-statements,no-self-use, missing-class-docstring
    def cursor(self) -> DBCursor: ...

    def commit(self) -> None: ...

    def close(self) -> None: ...

    def rollback(self) -> None: ...

    def execute(self, cmd: str, params: Optional[Tuple] = None): ...
