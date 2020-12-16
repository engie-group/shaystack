# Typing for DB driver
from typing import Tuple, Optional, List, Iterable, Iterator


class DBCursor:  # pylint: disable=multiple-statements,no-self-use, missing-class-docstring
    def execute(self, cmd: str, args: Optional[Tuple] = None) -> None: ...

    def fetchall(self) -> List[List]: return []

    def fetchone(self) -> Iterable: return []

    def executemany(self, sql: str, params: Iterable) -> None: ...

    def close(self) -> None: ...

    def __iter__(self) -> Iterator[List]: return [].__iter__()


class DBConnection:  # pylint: disable=multiple-statements,no-self-use, missing-class-docstring
    def cursor(self) -> DBCursor: return DBCursor()

    def commit(self) -> None: ...

    def close(self) -> None: ...

    def rollback(self) -> None: ...

    def execute(self, cmd: str, params: Optional[Tuple] = None): ...
