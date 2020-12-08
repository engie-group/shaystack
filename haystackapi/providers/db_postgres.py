import logging
import textwrap
from abc import abstractmethod, ABC
from dataclasses import dataclass
from datetime import datetime
from typing import List, Type, Any, Union, Tuple, Optional, Dict

from haystackapi import parse_filter, jsondumper, Quantity
from haystackapi.filter_ast import FilterPath, FilterBinary, FilterUnary, FilterNode

log = logging.getLogger("sql.Provider")


class _Root(ABC):
    pass


class _IsMerge(_Root):
    @abstractmethod
    def isMerge(self):
        pass


@dataclass
class _Path(_Root):
    paths: List[str]


@dataclass
class _Has(_IsMerge):
    def isMerge(self):
        return len(self.right.paths) > 1

    right: _Path


@dataclass
class _NotHas(_IsMerge):
    def isMerge(self):
        return len(self.right.paths) > 1

    right: _Path


@dataclass
class _AndHasTags(_IsMerge):
    not_op: bool
    type: Type  # HasBlock or NotHasBloc
    tags: List[str]

    def isMerge(self):
        return False


@dataclass
class _OrHasTags(_IsMerge):
    not_op: bool
    type: Type  # HasBlock or NotHasBloc
    tags: List[str]

    def isMerge(self):
        return False


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
    def isMerge(self):
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


def _merge_has_operators(left, right, merged_class):
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
def _optimize_filter_for_sql(node: FilterNode) -> _Root:
    if isinstance(node, FilterPath):
        return _Path(node.paths)
    elif isinstance(node, FilterBinary):
        left = _optimize_filter_for_sql(node.left)
        right = _optimize_filter_for_sql(node.right)
        if node.operator == "and":
            merged = _merge_has_operators(left, right, _AndHasTags)
            if merged:
                return merged
            if isinstance(left, _IsMerge) and left.isMerge() or \
                    isinstance(right, _IsMerge) and right.isMerge() or \
                    isinstance(left, (_Union, _Intersect)) or isinstance(right, (_Union, _Intersect)):
                return _Intersect(left, right)
            return _And(left, right)
        if node.operator == "or":
            merged = _merge_has_operators(left, right, _OrHasTags)
            if merged:
                return merged
            if isinstance(left, _IsMerge) and left.isMerge() or \
                    isinstance(right, _IsMerge) and right.isMerge() or \
                    isinstance(left, (_Union, _Intersect)) or isinstance(right, (_Union, _Intersect)):
                return _Union(left, right)
            return _Or(left, right)
        assert isinstance(left, _Path)
        operator = node.operator
        if operator == "==":
            operator = "="
        return _Compare(operator, left, right)
    elif isinstance(node, FilterUnary):
        if node.operator == "has":
            # right = _optimize_filter_for_sql(node.right)
            return _Has(_Path(node.right.paths))
        elif node.operator == "not":
            return _NotHas(_Path(node.right.paths))
        else:  # pragma: no cover
            assert 0, "Invalid operator"
    else:
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
    where = [_select_version(version, num_table) + \
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


def _select_version(version: datetime, num_table):
    return f"'{version.isoformat()}' BETWEEN t{num_table}.start_datetime AND t{num_table}.end_datetime\n"


def _generate_path(table_name: str,
                   customer_id: str,
                   version: datetime,
                   select: List[Union[str, List[Any]]],
                   where: List[Union[str, List[Any]]],
                   node: _Path,
                   num_table: int) -> Tuple[int, List[Union[str, List[Any]]], List[Union[str, List[Any]]]]:
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
                            select: List[Union[str, List[Any]]],
                            where: List[Union[str, List[Any]]],
                            node: _Root,
                            num_table: int
                            ) -> Tuple[int, List[Union[str, List[Any]]], List[Union[str, List[Any]]]]:
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
        generated_sql = []
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
        select = generated_sql
        where = []
    elif isinstance(node, _Union):
        generated_sql = []
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
        select = generated_sql
        where = []
    elif isinstance(node, _Compare):
        value = node.value
        if isinstance(value, Quantity):
            value = value.value
        if isinstance(value, (int, float)) and node.operator not in ('=', '!='):
            # Comparison with numbers. Must remove the header 'n:'
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            where.extend([
                f"substring(t{num_table}.entity->>'{node.path.paths[-1]}' from 3)::float",
                f" {node.operator} {value}\n",
            ])
        else:
            assert node.operator in ('=', '!='), "Operator not supported for this type"
            num_table, select, where = \
                _generate_path(table_name, customer_id, version,
                               select, where,
                               node.path,
                               num_table)
            v = jsondumper.dump_scalar(node.value)
            if v is None:
                if node.operator == '!=':
                    where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' IS NOT NULL\n")
                else:
                    where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' IS NULL\n")
            else:
                where.append(f"t{num_table}.entity->>'{node.path.paths[-1]}' {node.operator} '{str(v)}'\n")
    return num_table, select, where


def _flatten(l: List[Any]) -> List[Any]:
    if not l:
        return l
    if isinstance(l[0], list):
        return _flatten(l[0]) + _flatten(l[1:])
    return l[:1] + _flatten(l[1:])


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
        _optimize_filter_for_sql(parse_filter(grid_filter)._head),
        num_table=1)
    sql_request = f'-- {grid_filter}{sql}'
    return sql_request


def _exec_sql_filter(params: Dict[str, Any],
                     cursor,
                     table_name: str,
                     grid_filter: Optional[str],
                     version: datetime,
                     limit: int = 0,
                     customer_id: str = ''):
    if grid_filter is None or grid_filter == '':
        cursor.execute(params["SELECT_ENTITY"], (version, customer_id))
        return

    sql_request = _sql_filter(
        table_name,
        grid_filter,
        version,
        limit,
        customer_id)
    cursor.execute(sql_request)
    return cursor


MAX_DATE = '9999-12-31T23:59:59'


def get_db_parameters(table_name: str) -> Dict[str, Any]:
    return {
        "sql_type_to_json": lambda x: x,
        "exec_sql_filter": _exec_sql_filter,
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
               start_datetime timestamp WITH TIME ZONE NOT NULL,
               end_datetime timestamp WITH TIME ZONE NOT NULL,
               metadata jsonb,
               cols jsonb
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
    }
