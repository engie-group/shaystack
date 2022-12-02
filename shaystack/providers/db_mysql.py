# -*- coding: utf-8 -*-
# MYSql db driver
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Save Haystack ontology in SQLite database with JSon extension.
Convert the haystack filter to sqlite SQL equivalent syntax.
"""
import itertools
import json
import logging
import textwrap
from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Dict, Any, Optional, List, Tuple, Union, Iterator, Callable, cast

import pytz

from .sqldb_protocol import DBCursor
from .. import parse_filter, jsondumper, Quantity, Ref
from ..filter_ast import FilterNode, FilterUnary, FilterBinary, FilterPath

log = logging.getLogger("db.Provider")

_map_operator = \
    {"==": "=",
     "!=": "!="
     }


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
                   version: datetime,
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
             f"AND t{num_table - 1}.entity->'$.{path}' = "
             f"t{num_table}.entity->'$.id')\n"
             ])
        first = False
    where.append("AND ")
    return num_table, select, where


def _generate_filter_in_sql(table_name: str,
                            customer_id: str,
                            version: datetime,
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
            where.append(f"t{num_table}.entity->'$.{node.right.paths[-1]}' IS NOT NULL\n")
        elif node.operator == "not":
            assert isinstance(node.right, FilterPath)
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.right,
                               num_table)
            where.append(f"t{num_table}.entity->'$.{node.right.paths[-1]}' IS NULL\n")
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

                if node.operator == "and":
                    num_table += 1
                    num_table, left_sql = _generate_sql_block(table_name, customer_id, version,
                                                              0,
                                                              node.left,
                                                              num_table)
                    num_table += 1
                    num_table, right_sql = _generate_sql_block(table_name, customer_id, version,
                                                               0,
                                                               node.right,
                                                               num_table)

                    num_table += 1
                    generated_sql.append(f"\nSELECT t{num_table}.entity FROM haystack as t{num_table}\n")
                    generated_sql.append("WHERE entity->'$.id' in (")
                    generated_sql.append(left_sql)
                    generated_sql.append(")\nAND entity->'$.id' in (")
                    generated_sql.append(right_sql)
                    generated_sql.append(")\n")
                    select = generated_sql  # type: ignore
                    where = []
                else:
                    num_table, sql = _generate_sql_block(table_name, customer_id, version,
                                                         0,
                                                         node.left,
                                                         num_table)
                    generated_sql.append(sql)
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
                    f"CAST(SUBSTR(t{num_table}.entity->"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}',3) AS REAL)",
                    f" {node.operator} {value}\n",
                ])
            elif isinstance(value, time) and node.operator not in ('==', '!='):
                # Comparison with numbers. Must remove the header 'n:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"CAST(SUBSTR(t{num_table}.entity->"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}',4,8) AS TIME)",
                    f" {node.operator} CAST('{value}' AS TIME)\n",
                ])
            elif isinstance(value, datetime) and node.operator not in ('==', '!='):
                # Comparison with numbers. Must remove the header 'n:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"CAST(SUBSTR(t{num_table}.entity->"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}',4,10) AS DATETIME)",
                    f" {node.operator} CAST('{value}' AS DATETIME)\n",
                ])
            elif isinstance(value, date) and node.operator not in ('==', '!='):
                # Comparison with numbers. Must remove the header 'n:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"CAST(SUBSTR(t{num_table}.entity->"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}',4,25) AS DATE)",
                    f" {node.operator} CAST('{value}' AS DATE)\n",
                ])
            elif isinstance(value, str) and node.operator not in ('==', '!='):
                # Comparison with numbers. Must remove the header 'n:'
                num_table, select, where = \
                    _generate_path(table_name, customer_id, version,
                                   select, where,
                                   cast(FilterPath, node.left),
                                   num_table)
                where.extend([
                    f"(SUBSTR(t{num_table}.entity->"
                    f"'$.{cast(FilterPath, node.left).paths[-1]}'",
                    f",4,LENGTH('$.{cast(FilterPath, node.left).paths[-1]}')-4)"
                    f" {node.operator} '{value}')\n",
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
                            f"t{num_table}.entity->'$.{cast(FilterPath, node.left).paths[-1]}' "
                            f"IS NOT NULL\n")
                    else:
                        where.append(
                            f"t{num_table}.entity->'$.{cast(FilterPath, node.left).paths[-1]}' "
                            f"IS NULL\n")
                else:
                    if isinstance(value, Ref):
                        where.append(
                            f"t{num_table}.entity->'$.{cast(FilterPath, node.left).paths[-1]}' "
                            f"LIKE '\"{str(json.loads(jsondumper.dump_scalar(value)))}%\"'\n")
                    else:
                        where.append(
                            f"t{num_table}.entity->'$.{cast(FilterPath, node.left).paths[-1]}' "
                            f"{_map_operator[node.operator]} "
                            f"'{str(json.loads(jsondumper.dump_scalar(value)))}'\n")

    else:
        assert False, "Invalid node"
    return num_table, select, where


def _flatten(a_list: List[Any]) -> Iterator[Any]:
    return itertools.chain.from_iterable(a_list)


def _select_version(version: datetime, num_table: int) -> str:
    return f"'{version.isoformat()}' " \
           f"BETWEEN t{num_table}.start_datetime " \
           f"AND t{num_table}.end_datetime\n"


@dataclass
class _FilterDate(FilterNode):
    version: datetime
    num_table: int
    customer_id: str


def _generate_sql_block(table_name: str,
                        customer_id: str,
                        version: datetime,
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
                version: datetime,
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
                     version: datetime,
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


def get_db_parameters(database_name: str, table_name: str) -> Dict[str, Union[Callable, str]]:
    """ Return the SQL request and some lambda to manipulate a SuperSQLite database.

    Args:
        database_name: The database name.
        table_name: The table name to use.
    Returns:
        A dictionary with SQL request or lamdas
    """
    return {
        "sql_type_to_json": json.loads,
        "exec_sql_filter": _exec_sql_filter,
        "field_to_datetime_tz": lambda val: val.replace(tzinfo=pytz.utc),
        "datetime_tz_to_field": lambda dt: datetime(dt.year, dt.month, dt.day,
                                                    dt.hour, dt.minute, dt.second, dt.microsecond,
                                                    tzinfo=dt.tzinfo).replace(tzinfo=pytz.utc).isoformat(),
        "CREATE_HAYSTACK_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}
                (
                id VARCHAR(256), 
                customer_id VARCHAR(128) NOT NULL, 
                start_datetime DATETIME(6) NOT NULL, 
                end_datetime DATETIME(6) NOT NULL, 
                entity JSON NOT NULL
                );
            '''),
        "CREATE_HAYSTACK_INDEX_1": textwrap.dedent(f'''
            select if (
                    exists(
                        select distinct index_name from information_schema.statistics 
                        where table_schema = '{database_name}'
                        and table_name = '{table_name}' and index_name like 'index_1'
                    )
                    ,'select ''index index_1 exists'' _______;'
                    ,'create index index_1 on {table_name}(id, customer_id)') into @a;
                PREPARE stmt1 FROM @a;
                EXECUTE stmt1;
                DEALLOCATE PREPARE stmt1;
            '''),
        "CREATE_HAYSTACK_INDEX_2": '',
        "CREATE_METADATA_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}_meta_datas
               (
                customer_id VARCHAR(256) NOT NULL, 
                start_datetime DATETIME(6) NOT NULL, 
                end_datetime DATETIME(6) NOT NULL, 
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
            WHERE %s BETWEEN start_datetime AND end_datetime
            AND customer_id=%s
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
            WHERE %s > start_datetime AND end_datetime = '9999-12-31T23:59:59'
            AND id=%s 
            AND customer_id = %s
            '''),
        "INSERT_ENTITY": textwrap.dedent(f'''
            INSERT INTO {table_name} VALUES (%s,%s,%s,'9999-12-31T23:59:59',%s)
            '''),
        "DISTINCT_VERSION": textwrap.dedent(f'''
            SELECT DISTINCT start_datetime
            FROM {table_name}
            WHERE customer_id = %s
            ORDER BY start_datetime
            '''),
        "DISTINCT_TAG_VALUES": textwrap.dedent(f'''
            SELECT DISTINCT json_extract(entity,'$.[#]')
            FROM {table_name}
            WHERE customer_id = %s
            '''),

        "CREATE_TS_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}_ts
                (
                id VARCHAR(256) NOT NULL, 
                customer_id VARCHAR(128) NOT NULL, 
                date_time DATETIME(6) NOT NULL, 
                val JSON NOT NULL
                );
            '''),
        "CREATE_TS_INDEX": textwrap.dedent(f'''
            select if (
                    exists(
                        select distinct index_name from information_schema.statistics 
                        where table_schema = '{database_name}'
                        and table_name = '{table_name}_ts' and index_name like 'index_1'
                    )
                    ,'select ''index index_1 exists'' _______;'
                    ,'create index index_1 on {table_name}_ts(id, customer_id)') into @a;
                PREPARE stmt1 FROM @a;
                EXECUTE stmt1;
                DEALLOCATE PREPARE stmt1;
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
