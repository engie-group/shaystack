# -*- coding: utf-8 -*-
# Postgres db driver
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Save Haystack ontology in Postgres database (use JSon type).
Convert the haystack filter to postgres SQL equivalent syntax.
"""
import itertools
import json
import logging
import textwrap
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime, time, date
from typing import List, Type, Any, Union, Tuple, Optional, Dict, Iterator, Callable

from .sqldb_protocol import DBCursor
from .. import parse_filter, jsondumper, Quantity, Ref
from ..filter_ast import FilterPath, FilterBinary, FilterUnary, FilterNode

log = logging.getLogger("db.Provider")


def _sqlescape(a_str: str) -> str:
    return a_str.translate(
        str.maketrans({  # type: ignore
            "\0": "\\0",
            "\r": "\\r",
            "\x08": "\\b",
            "\x09": "\\t",
            "\x1a": "\\z",
            "\n": "\\n",
            "\"": "",
            "'": "",
            "\\": "\\\\",
            "%": "\\%"
        }))


class _Root(ABC):  # pylint: disable=missing-module-docstring
    pass


class _IsMerge(_Root):
    @abstractmethod
    def is_merge(self) -> bool:
        pass


@dataclass
class _Path(_Root):
    paths: List[str]


@dataclass
class _Has(_IsMerge):
    def is_merge(self) -> bool:
        return len(self.right.paths) > 1

    right: _Path


@dataclass
class _NotHas(_IsMerge):
    def is_merge(self) -> bool:
        return len(self.right.paths) > 1

    right: _Path


@dataclass
class _TypesHasTags(_IsMerge):
    not_op: bool
    type: Type  # HasBlock or NotHasBloc
    tags: List[str]

    def is_merge(self) -> bool:
        return False


@dataclass
class _AndHasTags(_TypesHasTags):
    pass


@dataclass
class _OrHasTags(_TypesHasTags):
    pass


@dataclass
class _Intersect(_Root):
    left: _Root
    right: _Root


@dataclass
class _Union(_Root):
    left: _Root
    right: _Root


@dataclass
class _Compare(_Root):
    # noinspection PyMethodMayBeStatic
    def is_merge(self) -> bool:  # pylint: disable=no-self-use
        return False

    operator: str
    path: _Path
    value: Any


@dataclass
class _And(_Root):
    left: _Root
    right: _Root


@dataclass
class _Or(_Root):
    left: _Root
    right: _Root


# noinspection PyUnresolvedReferences,PyTypeChecker
def _merge_has_operators(left, right, merged_class: Type) -> Optional[_Root]:
    type_left = type(left)
    type_right = type(right)
    if isinstance(left, merged_class) and left.type == type_right \
            and len(right.right.paths) == 1:
        left.tags.append(right.right.paths[0])
        return left
    if isinstance(right, merged_class) and right.type == type_left \
            and len(left.right.paths) == 1:
        right.tags.append(left.right.paths[0])
        return right
    if isinstance(left, merged_class) and isinstance(right, merged_class) \
            and left.type == right.type:
        left.tags.extend(right.tags)
        return left
    if type_left == type_right \
            and type_left in (_Has, _NotHas) \
            and len(left.right.paths) == 1 \
            and len(right.right.paths) == 1:
        return merged_class(
            type_left == _NotHas,
            type_left,
            [left.right.paths[0], right.right.paths[0]])
    return None


# Phase 1 : reorganize AST
# noinspection PyUnresolvedReferences,PyTypeChecker
def _optimize_filter_for_sql(node: FilterNode) -> Union[_Root, FilterNode]:
    if isinstance(node, FilterPath):
        return _Path(node.paths)
    if isinstance(node, FilterBinary):
        left = _optimize_filter_for_sql(node.left)
        right = _optimize_filter_for_sql(node.right)
        if node.operator == "and":
            merged = _merge_has_operators(left, right, _AndHasTags)
            if merged:
                return merged
            if isinstance(left, _IsMerge) and left.is_merge() or \
                    isinstance(right, _IsMerge) and right.is_merge() or \
                    isinstance(left, (_Union, _Intersect)) \
                    or isinstance(right, (_Union, _Intersect)):
                return _Intersect(left, right)  # type: ignore
            return _And(left, right)  # type: ignore
        if node.operator == "or":
            merged = _merge_has_operators(left, right, _OrHasTags)
            if merged:
                return merged
            if isinstance(left, _IsMerge) and left.is_merge() or \
                    isinstance(right, _IsMerge) and right.is_merge() or \
                    isinstance(left, (_Union, _Intersect)) or \
                    isinstance(right, (_Union, _Intersect)):  # pylint: disable=too-many-boolean-expressions
                return _Union(left, right)  # type: ignore
            return _Or(left, right)  # type: ignore
        assert isinstance(left, _Path)
        operator = node.operator
        if operator == "==":
            operator = "="
        return _Compare(operator, left, right)
    if isinstance(node, FilterUnary):
        if node.operator == "has":
            return _Has(_Path(node.right.paths))  # type: ignore
        if node.operator == "not":
            return _NotHas(_Path(node.right.paths))  # type: ignore
        assert 0, "Invalid operator"
    return node  # Value


# Phase 2: Generate SQL
def _generate_sql_block(table_name: str,
                        customer_id: str,
                        version: datetime,
                        limit: int,
                        node: _Root,
                        num_table: int) -> Tuple[int, str]:
    init_num_table = num_table
    select = [textwrap.dedent(f"""
        SELECT t{num_table}.entity
        FROM {table_name} as t{num_table}
        """)]
    where = [_select_version(version, num_table) +
             f"AND t{num_table}.customer_id='{customer_id}'\n"
             f"AND "
             ]
    num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                       select,
                                                       where,
                                                       node,
                                                       num_table
                                                       )

    generated_sql = "".join(_flatten(select))
    if init_num_table == num_table:
        generated_sql += "WHERE\n"
    generated_sql += "".join(_flatten(where))

    if limit > 0:
        generated_sql += f"LIMIT {limit}\n"
    return num_table, generated_sql


def _select_version(version: datetime, num_table: int) -> str:
    return f"'{version.isoformat()}' BETWEEN t{num_table}.start_datetime AND t{num_table}.end_datetime\n"


def _generate_path(table_name: str,
                   customer_id: str,
                   version: datetime,
                   select: Union[List[str], List[Any]],
                   where: Union[List[str], List[Any]],
                   node: _Path,
                   num_table: int) -> Tuple[int, Union[List[str], List[Any]], Union[List[str], List[Any]]]:
    if len(node.paths) == 1:
        return num_table, select, where
    first = True
    for path in node.paths[:-1]:
        num_table += 1
        if first:
            select.append(f"INNER JOIN {table_name} AS t{num_table} ON\n")
        else:
            select.append("".join(_flatten(where)))
            where = []
            select.append(f"INNER JOIN {table_name} AS t{num_table} ON\n")
        where.append(_select_version(version, num_table))
        where.append(f"AND t{num_table}.customer_id='{customer_id}'\n")
        first = False
        where.append(f"AND t{num_table - 1}.entity->'{path}' = t{num_table}.entity->'id'\n")
    where.append("AND ")
    return num_table, select, where


def _generate_filter_in_sql(table_name: str,
                            customer_id: str,
                            version: datetime,
                            select: Union[List[str], List[Any]],
                            where: Union[List[str], List[Any]],
                            node: _Root,
                            num_table: int
                            ) -> Tuple[int, Union[List[str], List[Any]], Union[List[str], List[Any]]]:
    # Use RootBlock nodes
    if isinstance(node, _Has):
        num_table, select, where = \
            _generate_path(table_name, customer_id, version,
                           select, where,
                           node.right,
                           num_table)
        where.append(f"t{num_table}.entity ? '{node.right.paths[-1]}'\n")
    elif isinstance(node, _NotHas):
        num_table, select, where = _generate_path(table_name, customer_id, version,
                                                  select, where,
                                                  node.right,
                                                  num_table)
        where.append(f"NOT t{num_table}.entity ? '{node.right.paths[-1]}'\n")
    elif isinstance(node, _AndHasTags):
        if node.not_op:
            where.append("NOT ")
        if len(node.tags) == 1:
            where.append(f"t{num_table}.entity ? '{node.tags[0]}'\n")
        else:
            where.append(f"t{num_table}.entity ?& array{node.tags}\n")
    elif isinstance(node, _OrHasTags):
        where.append(f"t{num_table}.entity ?| array{node.tags}\n")
    elif isinstance(node, _And):
        where.append("(")
        num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                           select,
                                                           where,
                                                           node.left,
                                                           num_table)
        where = ["".join(_flatten(where))[:-1], ")\nAND ("]
        num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                           select,
                                                           where,
                                                           node.right,
                                                           num_table)
        where = ["".join(_flatten(where))[:-1], ")\n"]
    elif isinstance(node, _Or):
        where.append("(")
        num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                           select,
                                                           where,
                                                           node.left,
                                                           num_table)
        where = ["".join(_flatten(where))[:-1], ")\nOR ("]
        num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                           select,
                                                           where,
                                                           node.right,
                                                           num_table)
        where = ["".join(_flatten(where))[:-1], ")\n"]
    elif isinstance(node, _Intersect):
        generated_sql = list()
        generated_sql.append('\n(')
        num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                             0,
                                             node.left,
                                             num_table)
        generated_sql.append(sql)
        generated_sql.append(")\nINTERSECT\n(")
        num_table += 1
        num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                             0,
                                             node.right,
                                             num_table)
        generated_sql.append(sql)
        generated_sql.append(")\n")
        select = generated_sql  # type: ignore
        where = []
    elif isinstance(node, _Union):
        generated_sql = list()
        generated_sql.append('\n(')
        num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                             0,
                                             node.left,
                                             num_table)
        generated_sql.append(sql)
        generated_sql.append(")\nUNION\n(")
        num_table += 1
        num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                             0,
                                             node.right,
                                             num_table)
        generated_sql.append(sql)
        generated_sql.append(")\n")
        select = generated_sql  # type: ignore
        where = []
    elif isinstance(node, _Compare):
        value = node.value
        if isinstance(value, Quantity):
            value = value.m
        if isinstance(value, (int, float)) and node.operator not in ('=', '!='):
            # Comparison with numbers. Must remove the header 'n:'
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            where.extend([
                f"SUBSTRING(t{num_table}.entity->>'{node.path.paths[-1]}',3)::float",
                f" {node.operator} {value}\n",
            ])
        elif isinstance(value, time) and node.operator not in ('==', '!='):
            # Comparison with time. Must remove the header 't:'
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            where.extend([
                f"SUBSTRING(t{num_table}.entity->>'{node.path.paths[-1]}',3)::TIME",
                f" {node.operator} TIME '{value}'\n",
            ])
        elif isinstance(value, datetime) and node.operator not in ('==', '!='):
            # Comparison with time. Must remove the header 't:'
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            where.extend([
                f"SUBSTRING(t{num_table}.entity->>'{node.path.paths[-1]}',3,25)::TIMESTAMP",
                f" {node.operator} TIMESTAMP '{value.isoformat()}'\n",
            ])
        elif isinstance(value, str) and node.operator not in ('==', '!='):
            # Comparison with time. Must remove the header 't:'
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            where.extend([
                f"SUBSTRING(t{num_table}.entity->>'{node.path.paths[-1]}',3)",
                f" {node.operator} '{_sqlescape(value)}'\n",
            ])
        elif isinstance(value, date) and node.operator not in ('==', '!='):
            # Comparison with time. Must remove the header 't:'
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            where.extend([
                f"SUBSTRING(t{num_table}.entity->>'{node.path.paths[-1]}',3)::DATE",
                f" {node.operator} DATE '{value}'\n",
            ])
        else:
            assert node.operator in ('=', '!='), "Operator not supported for this type"
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            value = json.loads(jsondumper.dump_scalar(node.value))
            if value is None:
                if node.operator == '!=':
                    where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' IS NOT NULL\n")
                else:
                    where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' IS NULL\n")
            else:
                if isinstance(node.value, Ref):
                    # Comparison with Ref. Use only the name
                    where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' "
                                 f"LIKE '{str(value)}%'\n")
                else:
                    where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' "
                                 f"{node.operator} '{str(value)}'\n")
    return num_table, select, where


def _flatten(a_list: List[Any]) -> Iterator[Any]:
    return itertools.chain.from_iterable(a_list)


def _sql_filter(table_name: str,
                grid_filter: Optional[str],
                version: datetime,
                limit: int = 0,
                customer_id: str = '') -> str:
    _, sql = _generate_sql_block(
        table_name,
        customer_id,
        version,
        limit,
        _optimize_filter_for_sql(parse_filter(grid_filter).head),  # type: ignore # pylint: disable=protected-access
        num_table=1)
    sql_request = f'-- {grid_filter}{sql}'
    return sql_request


def _exec_sql_filter(params: Dict[str, Any],
                     cursor,
                     table_name: str,
                     grid_filter: Optional[str],
                     version: datetime,
                     limit: int = 0,
                     customer_id: str = '') -> DBCursor:
    if grid_filter is None or grid_filter == '':
        cursor.execute(params["SELECT_ENTITY"], (version, customer_id))
        return cursor

    sql_request = _sql_filter(
        table_name,
        grid_filter,
        version,
        limit,
        customer_id)
    cursor.execute(sql_request)
    return cursor


MAX_DATE = '9999-12-31T23:59:59'


def get_db_parameters(table_name: str) -> Dict[str, Union[Callable, str]]:
    """ Return the SQL request and some lambda to manipulate a Postgres database.

    Args:
        table_name: The table name to use.
    Returns:
        A dictionary with SQL request or lambdas
    """
    return {
        "sql_type_to_json": lambda x: x,
        "exec_sql_filter": _exec_sql_filter,
        "field_to_datetime_tz": lambda val: val,
        "datetime_tz_to_field": lambda dt: dt,
        "CREATE_HAYSTACK_TABLE": textwrap.dedent(f'''
           CREATE TABLE IF NOT EXISTS {table_name}
               (
               id text,
               customer_id text NOT NULL,
               start_datetime timestamp WITH TIME ZONE NOT NULL,
               end_datetime timestamp WITH TIME ZONE NOT NULL,
               entity jsonb NOT NULL
               );
           '''),
        "CREATE_HAYSTACK_INDEX_1": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_index ON {table_name}
            (
                id, customer_id
            )
            '''),
        "CREATE_HAYSTACK_INDEX_2": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_index_gin ON {table_name} USING GIN (entity);
            '''),
        "CREATE_METADATA_TABLE": textwrap.dedent(f'''
           CREATE TABLE IF NOT EXISTS {table_name}_meta_datas
               (
               customer_id text NOT NULL,
               start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
               end_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
               metadata JSONB,
               cols JSONB
               );
               '''),
        "PURGE_TABLES_HAYSTACK": textwrap.dedent(f'''
            DELETE FROM {table_name} ;
            '''),
        "PURGE_TABLES_HAYSTACK_META": textwrap.dedent(f'''
            DELETE FROM {table_name}_meta_datas ;
            '''),
        "SELECT_META_DATA": textwrap.dedent(f'''
        SELECT metadata,cols from {table_name}_meta_datas
        WHERE %s BETWEEN start_datetime AND end_datetime
        AND customer_id = %s
        '''),
        "CLOSE_META_DATA": textwrap.dedent(f'''
            UPDATE {table_name}_meta_datas  SET end_datetime=%s
            WHERE %s >= start_datetime AND end_datetime = '9999-12-31T23:59:59'
            AND customer_id=%s
            '''),
        "UPDATE_META_DATA": textwrap.dedent(f'''
            INSERT INTO {table_name}_meta_datas VALUES (%s,%s,'9999-12-31T23:59:59',%s,%s)
            '''),
        "SELECT_ENTITY": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE %s BETWEEN start_datetime AND end_datetime
            AND customer_id = %s
            '''),
        "SELECT_ENTITY_WITH_ID": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE %s BETWEEN start_datetime AND end_datetime
            AND customer_id = %s
            AND id IN '''),
        "CLOSE_ENTITY": textwrap.dedent(f'''
            UPDATE {table_name} SET end_datetime=%s 
            WHERE 
            %s BETWEEN start_datetime AND end_datetime
            AND id=%s 
            AND customer_id=%s
            '''),
        "INSERT_ENTITY": textwrap.dedent(f'''
            INSERT INTO {table_name} VALUES (%s,%s,%s,'9999-12-31T23:59:59',%s)
            '''),
        "DISTINCT_VERSION": textwrap.dedent(f'''
            SELECT DISTINCT start_datetime
            FROM {table_name}
            WHERE customer_id=%s
            ORDER BY start_datetime
            '''),
        "DISTINCT_TAG_VALUES": textwrap.dedent(f'''
            SELECT DISTINCT entity->'[#]'
            FROM {table_name}
            WHERE customer_id = %s
            '''),

        "CREATE_TS_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}_ts
                (
                id TEXT NOT NULL, 
                customer_id TEXT NOT NULL, 
                date_time TIMESTAMP WITH TIME ZONE NOT NULL, 
                val JSONB NOT NULL
                );
        '''),
        "CREATE_TS_INDEX": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_ts_index ON {table_name}_ts(id,customer_id)
            '''),
        "CLEAN_TS": textwrap.dedent(f'''
            DELETE FROM {table_name}_ts
            WHERE customer_id = %s
            AND id = %s
            AND date_time BETWEEN %s AND %s
            '''),
        "INSERT_TS": textwrap.dedent(f'''
            INSERT INTO {table_name}_ts
            VALUES(%s,%s,%s,%s)
            '''),
        "SELECT_TS": textwrap.dedent(f'''
            SELECT date_time,val FROM {table_name}_ts
            WHERE customer_id = %s
            AND id = %s
            AND date_time BETWEEN %s AND %s
            ORDER BY date_time
            '''),
        "PURGE_TABLES_TS": textwrap.dedent(f'''
            DELETE FROM {table_name}_ts
            ''')
    }
