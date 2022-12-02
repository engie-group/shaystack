# -*- coding: utf-8 -*-
# SQLite db driver
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Save Haystack ontology in SQLite database with JSon extension.
Convert the haystack filter to sqlite SQL equivalent syntax.
"""
import datetime
import itertools
import json
import logging
import textwrap
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple, Union, Iterator, Callable, cast

import pytz

from .sqldb_protocol import DBCursor
from .. import parse_filter, jsondumper, Quantity, Ref
from ..filter_ast import FilterNode, FilterUnary, FilterBinary, FilterPath

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


def _use_inner_join(node: FilterNode) -> bool:
    """ Return True if the tree must use inner join """
    if isinstance(node, FilterUnary):
        return len(cast(FilterPath, node.right).paths) > 1
    if isinstance(node, FilterBinary):
        if isinstance(node.left, _FilterDate):
            return False
        return _use_inner_join(node.left) or _use_inner_join(node.right)
    return False


def _generate_path(table_name: str,
                   customer_id: str,
                   version: datetime.datetime,
                   select: List[Union[str, List[Any]]],
                   where: List[Union[str, List[Any]]],
                   node: FilterPath,
                   num_table: int) -> Tuple[int, List[Union[str, List[Any]]], List[Union[str, List[Any]]]]:
    if len(node.paths) == 1:
        return num_table, select, where
    first = True
    for path in node.paths[:-1]:
        num_table += 1
        if first:
            select.append(f"INNER JOIN {table_name} AS t{num_table} ON\n")
        else:
            select.append("".join(_flatten(where)) + ")\n")
            where = []
            select.append(f"INNER JOIN {table_name} AS t{num_table} ON\n")
            where.append('(')
        where.extend(
            ['(',
             _select_version(version, num_table),
             f"AND t{num_table}.customer_id='{customer_id}'\n",
             f"AND json_object(json(t{num_table - 1}.entity),'$.{path}') = "
             f"json_object(json(t{num_table}.entity),'$.id'))\n"
             ])
        first = False
    where.append("AND ")
    return num_table, select, where


def _generate_filter_in_sql(table_name: str,
                            customer_id: str,
                            version: datetime.datetime,
                            select: List[Union[str, List[Any]]],
                            where: List[Union[str, List[Any]]],
                            node: FilterNode,
                            num_table: int
                            ) -> Tuple[int, List[Union[str, List[Any]]], List[Union[str, List[Any]]]]:
    # Use RootBlock nodes
    if isinstance(node, _FilterDate):
        where.extend(
            ["(",
             _select_version(node.version, node.num_table),
             f"AND t{node.num_table}.customer_id='{node.customer_id}')\n"
             ])

    elif isinstance(node, FilterUnary):
        if node.operator == "has":
            assert isinstance(node.right, FilterPath)
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.right,
                               num_table)
            where.append(f"json_extract(json(t{num_table}.entity),'$.{node.right.paths[-1]}') IS NOT NULL\n")
        elif node.operator == "not":
            assert isinstance(node.right, FilterPath)
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.right,
                               num_table)
            where.append(f"json_extract(json(t{num_table}.entity),'$.{node.right.paths[-1]}') IS NULL\n")
        else:
            assert False

    elif isinstance(node, FilterBinary):
        if node.operator in ["and", "or"]:
            use_inner = _use_inner_join(node)
            if use_inner:
                if isinstance(node.left, FilterBinary) and _use_inner_join(node.left):
                    log.warning("SQLite can not implement this request. Result may be invalid")
                if isinstance(node.right, FilterBinary) and _use_inner_join(node.right):
                    log.warning("SQLite can not implement this request. Result may be invalid")
                generated_sql = []
                num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                                     0,
                                                     node.left,
                                                     num_table)
                generated_sql.append(sql)
                if node.operator == "and":
                    generated_sql.append("INTERSECT")
                else:
                    generated_sql.append("UNION")
                num_table += 1
                num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                                     0,
                                                     node.right,
                                                     num_table)
                generated_sql.append(sql)
                select = generated_sql  # type: ignore
                where = []
            else:
                where.append('(')
                parent_left = isinstance(node.left, FilterBinary) and node.left.operator in ["and", "or"]
                num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                                   select,
                                                                   where,
                                                                   node.left,
                                                                   num_table)
                if parent_left:
                    where = \
                        ["".join(_flatten(where))[:-1],
                         f"\n{node.operator.upper()} "
                         ]
                else:
                    where.append(f"{node.operator.upper()} ")
                num_table, select, where = _generate_filter_in_sql(table_name, customer_id, version,
                                                                   select,
                                                                   where,
                                                                   node.right,
                                                                   num_table)
                if where:
                    where.append(")\n")
        else:
            value = node.right
            if isinstance(value, Quantity):
                value = value.m
            if isinstance(value, (int, float)) and node.operator not in ('==', '!='):
                # Comparison with numbers. Must remove the header 'n:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"CAST(substr(json_extract(json(t{num_table}.entity),"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}'),3) AS REAL)",
                    f" {node.operator} {value}\n",
                ])
            elif isinstance(value, datetime.time) and node.operator not in ('==', '!='):
                # Comparison with hour. Must remove the header 'h:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"time(substr(json_extract(json(t{num_table}.entity),"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}'),3))",
                    f" {node.operator} time('{value}')\n",
                ])
            elif isinstance(value, datetime.datetime) and node.operator not in ('==', '!='):
                # Comparison with numbers. Must remove the header 't:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"datetime(substr(json_extract(json(t{num_table}.entity),"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}'),3,25))",
                    f" {node.operator} datetime('{value.isoformat()}')\n",
                ])
            elif isinstance(value, datetime.date) and node.operator not in ('==', '!='):
                # Comparison with date. Must remove the header 'd:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"date(substr(json_extract(json(t{num_table}.entity),"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}'),3))",
                    f" {node.operator} date('{value}')\n",
                ])
            elif isinstance(value, str) and node.operator not in ('==', '!='):
                # Comparison with str. Must remove the header 's:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"substr(json_extract(json(t{num_table}.entity),"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}'),3)",
                    f" {node.operator} '{_sqlescape(value)}'\n",
                ])
            else:
                assert node.operator in ('==', '!='), "Operator not supported for this type"
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                if value is None:
                    if node.operator == '!=':
                        where.append(
                            f"json_extract(json(t{num_table}.entity),"
                            f"'$.{cast(FilterPath, node.left).paths[-1]}') "
                            f"IS NOT NULL\n")
                    else:
                        where.append(
                            f"json_extract(json(t{num_table}.entity),"
                            f"'$.{cast(FilterPath, node.left).paths[-1]}') "
                            f"IS NULL\n")
                else:
                    if isinstance(value, Ref):
                        where.append(
                            f"json_extract(json(t{num_table}.entity),"
                            f"'$.{cast(FilterPath, node.left).paths[-1]}') "
                            f"LIKE '{str(json.loads(jsondumper.dump_scalar(value)))}%'\n")
                    else:
                        where.append(
                            f"json_extract(json(t{num_table}.entity),"
                            f"'$.{cast(FilterPath, node.left).paths[-1]}') "
                            f"{node.operator} '{str(json.loads(jsondumper.dump_scalar(value)))}'\n")

    else:
        assert False, "Invalid node"
    return num_table, select, where


def _flatten(a_list: List[Any]) -> Iterator[Any]:
    return itertools.chain.from_iterable(a_list)


def _select_version(version: datetime.datetime, num_table: int) -> str:
    return f"datetime('{version.isoformat()}') " \
           f"BETWEEN datetime(t{num_table}.start_datetime) " \
           f"AND datetime(t{num_table}.end_datetime)\n"


@dataclass
class _FilterDate(FilterNode):
    version: datetime.datetime
    num_table: int
    customer_id: str


def _generate_sql_block(table_name: str,
                        customer_id: str,
                        version: datetime.datetime,
                        limit: int,
                        node: FilterNode,
                        num_table: int) -> Tuple[int, str]:
    init_num_table = num_table
    select = [textwrap.dedent(f"""
        SELECT t{num_table}.entity
        FROM {table_name} as t{num_table}
        """)]

    num_table, select, where = _generate_filter_in_sql(
        table_name, customer_id, version,
        select,  # type: ignore
        [],
        FilterBinary("and", _FilterDate(version, num_table, customer_id), node),
        num_table
    )

    generated_sql = "".join(_flatten(select))
    if init_num_table == num_table:
        generated_sql += "WHERE\n"
    generated_sql += "".join(_flatten(where))

    if limit > 0:
        generated_sql += f"LIMIT {limit}\n"
    return num_table, generated_sql


def _sql_filter(table_name: str,
                grid_filter: Optional[str],
                version: datetime.datetime,
                limit: int = 0,
                customer_id: str = '') -> str:
    _, sql = _generate_sql_block(
        table_name,
        customer_id,
        version,
        limit,
        parse_filter(grid_filter).head,  # type: ignore
        num_table=1)
    sql_request = f'-- {grid_filter}{sql}'
    return sql_request


def _exec_sql_filter(params: Dict[str, Any],
                     cursor,
                     table_name: str,
                     grid_filter: Optional[str],
                     version: datetime.datetime,
                     limit: int = 0,
                     customer_id: Optional[str] = None) -> DBCursor:
    if grid_filter is None or grid_filter == '':
        cursor.execute(params["SELECT_ENTITY"], (version, customer_id))
        return cursor

    sql_request = _sql_filter(
        table_name,
        grid_filter,
        version,
        limit,
        customer_id)  # type: ignore
    cursor.execute(sql_request)
    return cursor


def get_db_parameters(table_name: str) -> Dict[str, Union[Callable, str]]:
    """ Return the SQL request and some lambda to manipulate a SuperSQLite database.

    Args:
        table_name: The table name to use.
    Returns:
        A dictionary with SQL request or lamdas
    """
    return {
        "sql_type_to_json": json.loads,
        "exec_sql_filter": _exec_sql_filter,
        "field_to_datetime_tz": lambda val:
        datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc),
        "datetime_tz_to_field": lambda dt: datetime.datetime(dt.year, dt.month, dt.day,
                                                             dt.hour, dt.minute, dt.second, dt.microsecond,
                                                             tzinfo=dt.tzinfo)
            .replace(tzinfo=pytz.utc).isoformat(),
        "CREATE_HAYSTACK_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}
                (
                id TEXT, 
                customer_id TEXT NOT NULL, 
                start_datetime TEXT NOT NULL, 
                end_datetime TEXT NOT NULL, 
                entity JSON NOT NULL
                );
            '''),
        "CREATE_HAYSTACK_INDEX_1": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_index ON {table_name}(id, customer_id)
            '''),
        "CREATE_HAYSTACK_INDEX_2": textwrap.dedent('''
            '''),
        "CREATE_METADATA_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}_meta_datas
               (
                customer_id TEXT NOT NULL, 
                start_datetime TEXT NOT NULL, 
                end_datetime TEXT NOT NULL, 
                metadata JSON,
                cols JSON
               );
           '''),
        "PURGE_TABLES_HAYSTACK": textwrap.dedent(f'''
            DELETE FROM {table_name} ;
            '''),
        "PURGE_TABLES_HAYSTACK_META": textwrap.dedent(f'''
            DELETE FROM {table_name}_meta_datas ;
            '''),
        "SELECT_META_DATA": textwrap.dedent(f'''
            SELECT metadata,cols FROM {table_name}_meta_datas
            WHERE datetime(?) BETWEEN datetime(start_datetime) AND datetime(end_datetime)
            AND customer_id=?
            '''),
        "CLOSE_META_DATA": textwrap.dedent(f'''
            UPDATE {table_name}_meta_datas  SET end_datetime=?
            WHERE datetime(?) >= datetime(start_datetime) AND end_datetime = '9999-12-31T23:59:59'
            AND customer_id=?
            '''),
        "UPDATE_META_DATA": textwrap.dedent(f'''
            INSERT INTO {table_name}_meta_datas VALUES (?,?,'9999-12-31T23:59:59',json(?),json(?))
            '''),
        "SELECT_ENTITY": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE datetime(?) BETWEEN datetime(start_datetime) AND datetime(end_datetime)
            AND customer_id = ?
            '''),
        "SELECT_ENTITY_WITH_ID": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE datetime(?) BETWEEN datetime(start_datetime) AND datetime(end_datetime)
            AND customer_id = ?
            AND id IN '''),
        "CLOSE_ENTITY": textwrap.dedent(f'''
            UPDATE {table_name} SET end_datetime=? 
            WHERE datetime(?) > datetime(start_datetime) AND end_datetime = '9999-12-31T23:59:59'
            AND id=? 
            AND customer_id = ?
            '''),
        "INSERT_ENTITY": textwrap.dedent(f'''
            INSERT INTO {table_name} VALUES (?,?,?,'9999-12-31T23:59:59',json(?))
            '''),
        "DISTINCT_VERSION": textwrap.dedent(f'''
            SELECT DISTINCT datetime(start_datetime)
            FROM {table_name}
            WHERE customer_id = ?
            ORDER BY datetime(start_datetime)
            '''),
        "DISTINCT_TAG_VALUES": textwrap.dedent(f'''
            SELECT DISTINCT json_extract(entity,'$.[#]')
            FROM {table_name}
            WHERE customer_id = ?
            '''),

        "CREATE_TS_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}_ts
                (
                id TEXT NOT NULL, 
                customer_id TEXT NOT NULL, 
                date_time TEXT NOT NULL, 
                val JSON NOT NULL
                );
            '''),
        "CREATE_TS_INDEX": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_ts_index ON {table_name}_ts(id,customer_id)
            '''),
        "CLEAN_TS": textwrap.dedent(f'''
            DELETE FROM {table_name}_ts
            WHERE customer_id = ?
            AND id = ?
            AND datetime(date_time) BETWEEN datetime(?) AND datetime(?)
            '''),
        "INSERT_TS": textwrap.dedent(f'''
            INSERT INTO {table_name}_ts
            VALUES(?,?,datetime(?),json(?))
            '''),
        "SELECT_TS": textwrap.dedent(f'''
            SELECT date_time,val FROM {table_name}_ts
            WHERE customer_id = ?
            AND id = ?
            AND datetime(date_time) BETWEEN datetime(?) AND datetime(?) 
            ORDER BY datetime(date_time)
            '''),
        "PURGE_TABLES_TS": textwrap.dedent(f'''
            DELETE FROM {table_name}_ts
            ''')
    }
