# -*- coding: utf-8 -*-
# Protocol to using SQL driver
# Use license Apache V2.0
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Typing wrapper for sql drivers
"""
# Typing for DB driver
import sys
from typing import Tuple, Optional, List, Iterable, Iterator

if sys.version_info[0:2] == (3, 7):
    from typing import Type

    Protocol = Type
else:
    from typing import Protocol


class DBCursor(Protocol):  # pylint: disable=multiple-statements,no-self-use, missing-class-docstring
    def execute(self, cmd: str, args: Optional[Tuple] = None) -> None: ...

    def fetchall(self) -> List[List]: ...

    def fetchone(self) -> Iterable: ...

    def executemany(self, sql: str, params: Iterable) -> None: ...

    def close(self) -> None: ...

    def __iter__(self) -> Iterator[List]: ...


class DBConnection(Protocol):  # pylint: disable=multiple-statements,no-self-use, missing-class-docstring
    def cursor(self) -> DBCursor: ...

    def commit(self) -> None: ...

    def close(self) -> None: ...

    def rollback(self) -> None: ...

    def execute(self, cmd: str, params: Optional[Tuple] = None): ...
