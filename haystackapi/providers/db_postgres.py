import logging
import textwrap
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from textwrap import dedent
from typing import List, Type, Any, Tuple, Optional, Dict, Union

from hszinc import parse_filter, jsondumper, Quantity
from hszinc.filter_ast import FilterPath, FilterBinary, FilterUnary, FilterNode

log = logging.getLogger("sql.Provider")


class _Root:
    pass


class _IsMerge(_Root):
    @abstractmethod
    def isMerge(self):
        pass


@dataclass
class _Has(_IsMerge):
    def isMerge(self):
        return len(self.tag.paths) > 1

    tag: str


@dataclass
class _NotHas(_IsMerge):
    def isMerge(self):
        return len(self.tag.paths) > 1

    tag: str


@dataclass
class _AndHasTags(_IsMerge):
    not_op: bool
    type: Type  # HasBlock or NotHasBloc
    tags: List[str]

    def isMerge(self):
        return False

    def to_sql(self):
        return f"entity ?& array{self.tag}"


@dataclass
class _OrHasTags(_IsMerge):
    not_op: bool
    type: Type  # HasBlock or NotHasBloc
    tags: List[str]

    def isMerge(self):
        return False

    def to_sql(self):
        return f"entity ?& array{self.tag}"


@dataclass
class _Intersect(_Root):
    left: _Root
    right: _Root


@dataclass
class _Union(_Root):
    left: _Root
    right: _Root


@dataclass
class _Path(_Root):
    paths: List[str]


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
            and len(right.tag.paths) == 1:
        left.tags.append(right.tag.paths[0])
        return left
    if isinstance(right, merged_class) and right.type == type_left \
            and len(left.tag.paths) == 1:
        right.tags.append(left.tag.paths[0])
        return right
    if isinstance(left, merged_class) and isinstance(right, merged_class) \
            and left.type == right.type:
        left.tags.extend(right.tags)
        return left
    if type_left == type_right \
            and type_left in (_Has, _NotHas) \
            and len(left.tag.paths) == 1 \
            and len(right.tag.paths) == 1:
        return merged_class(
            type_left == _NotHas,
            type_left, [left.tag.paths[0], right.tag.paths[0]])
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
                    isinstance(right, _IsMerge) and right.isMerge():
                return _Intersect(left, right)
            return _And(left, right)
        if node.operator == "or":
            merged = _merge_has_operators(left, right, _OrHasTags)
            if merged:
                return merged
            if isinstance(left, _IsMerge) and left.isMerge() or \
                    isinstance(right, _IsMerge) and right.isMerge():
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
                        node: _Root,
                        generated_sql: List[Union[str, List[str]]],
                        num_table: int,
                        limit,
                        version: datetime) -> List[Union[str, List[str]]]:
    prefix, new_num_table, lines = _generate_filter_in_sql(table_name,
                                                           customer_id,
                                                           node,
                                                           generated_sql,
                                                           num_table,
                                                           limit,
                                                           version)
    result = [textwrap.dedent(f"""\
            SELECT t{num_table}.entity
            FROM {table_name} as t{num_table}
            {prefix}
            """),
              lines,
              ]
    if limit:
        result.append(f"LIMIT {limit}\n")
    return result


def _select_version(version: datetime, num_table):
    return f"'{version.isoformat()}' >= t{num_table}.start_datetime AND " \
           f"('{version.isoformat()}' < t{num_table}.end_datetime or t{num_table}.end_datetime is NULL)\n" \
           f"AND\n"


def _generate_path(table_name: str,
                   customer_id: str,
                   node: _Path,
                   generated_sql: List[Union[str, List[str]]],
                   version: datetime,
                   num_table: int) -> Tuple[
    str, int, List[str]]:
    if len(node.paths) > 1:
        num_table += 1
        prefix = f"INNER JOIN {table_name} AS t{num_table} ON"
    else:
        prefix = "WHERE"
    if len(node.paths) == 1:
        return prefix, num_table, generated_sql
    first = True
    for path in node.paths[:-1]:
        if not first:
            generated_sql.append(
                f"INNER JOIN {table_name} AS t{num_table} ON\n",
            )
        first = False
        generated_sql.append(_select_version(version, num_table - 1))
        generated_sql.append(fr"t{num_table - 1}.customer_id='{customer_id}' AND ")
        generated_sql.append(
            f"t{num_table - 1}.entity->'{path}' = t{num_table}.entity->'id'\n"
        )
        num_table += 1
    return prefix, num_table - 1, generated_sql


def _generate_filter_in_sql(table_name: str,
                            customer_id: str,
                            node: _Root,
                            generated_sql: List[Union[str, List[str]]],
                            num_table: int,
                            limit: int,
                            version: datetime) -> (str, int, List[str]):
    # Use RootBlock nodes
    prefix = "WHERE"
    if isinstance(node, _Has):
        l = len(generated_sql)
        prefix, num_table, generated_sql = \
            _generate_path(table_name, customer_id, node.tag, generated_sql, version, num_table)
        if len(generated_sql) != l:
            generated_sql.append("AND\n")
        generated_sql.append(_select_version(version, num_table))
        generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
        generated_sql.append(f"t{num_table}.entity ? '{node.tag.paths[-1]}'\n")
    elif isinstance(node, _NotHas):
        l = len(generated_sql)
        prefix, num_table, _ = \
            _generate_path(table_name, customer_id, node.tag, generated_sql, version, num_table)
        if len(generated_sql) != l:
            generated_sql.append("AND\n")
        generated_sql.append(_select_version(version, num_table))
        generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
        generated_sql.append(f"NOT t{num_table}.entity ? '{node.tag.paths[-1]}'\n")
    elif isinstance(node, _AndHasTags):
        generated_sql.append(_select_version(version, num_table))
        generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
        if node.not_op:
            generated_sql.append("NOT ")
        if len(node.tags) == 1:
            generated_sql.append(f"t{num_table}.entity ? '{node.tags[0]}'\n")
        else:
            generated_sql.append(f"t{num_table}.entity ?& array{node.tags}\n")
    elif isinstance(node, _OrHasTags):
        generated_sql.append(_select_version(version, num_table))
        generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
        generated_sql.append(f"t{num_table}.entity ?| array{node.tags}\n")
    elif isinstance(node, _And):
        prefix, num_table, _ = _generate_filter_in_sql(table_name, customer_id, node.left, generated_sql, num_table,
                                                       limit,
                                                       version)
        generated_sql.append("AND\n")
        prefix, num_table, _ = _generate_filter_in_sql(table_name, customer_id, node.right, generated_sql, num_table,
                                                       limit, version)
    elif isinstance(node, _Intersect):
        prefix, num_table, _ = _generate_filter_in_sql(table_name, customer_id, node.left, generated_sql, num_table,
                                                       limit,
                                                       version)
        generated_sql.append("INTERSECT\n")
        num_table += 1
        generated_sql.append(
            _generate_sql_block(table_name, customer_id, node.right, [], num_table, 0, version))
    elif isinstance(node, _Or):
        prefix, num_table, _ = _generate_filter_in_sql(table_name, customer_id, node.left, generated_sql, num_table,
                                                       limit,
                                                       version)
        generated_sql.append("OR\n")
        prefix, num_table, _ = _generate_filter_in_sql(table_name, customer_id, node.right, generated_sql, num_table,
                                                       limit, version)
    elif isinstance(node, _Union):
        prefix, num_table, _ = _generate_filter_in_sql(table_name, customer_id, node.left, generated_sql, num_table,
                                                       limit,
                                                       version)
        generated_sql.append("UNION\n")
        num_table += 1
        generated_sql.append(
            _generate_sql_block(table_name, customer_id, node.right, [], num_table, 0, version))
    elif isinstance(node, _Path):
        if len(node.paths) == 1:
            # Simple case
            generated_sql.append(_select_version(version, num_table))
            generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
            generated_sql.append(f" t{num_table}.entity @? '$.{node.paths[0]}\n")
        else:
            # Path navigation. Use inner join
            inners_join = []
            last_path = node.paths[-1]
            inner_num_block = num_table
            inners_join.extend([
                f" INNER JOIN {table_name} as t{inner_num_block + 1} ON\n",
                ''.join(_generate_sql_block(table_name, customer_id, node.right, [], inner_num_block, "WHERE")),
                ' AND\n',
            ])
            generated_sql.append(_select_version(version, num_table))
            inners_join.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
            inners_join.append(
                f"t{inner_num_block + 1}.entity @? ('$.{last_path} ? (@ == \"r:' || t{inner_num_block}.id ||'\")')::jsonpath\n"
            )
            for path in node.paths[:-1].reverse():
                inner_num_block += 1
                inners_join.extend([
                    f"INNER JOIN {table_name} as t{inner_num_block} ON\n",
                    f"t{inner_num_block + 1}.entity @? ('$.{path} ? (@ == \"r:' || t{inner_num_block}.id ||'\")')::jsonpath\n"
                ])
            return [dedent("""
                    SELECT t{num_block}.entity 
                    FROM {table_name} as t{num_block}
                    """)]
    elif isinstance(node, _Compare):
        # _generate_filter_in_sql(table_name, node.path, def_filter, num_block)
        value = node.value
        if isinstance(value, Quantity):
            value = value.value
        if isinstance(value, (int, float)) and node.operator not in ('=', '!='):
            # Comparison with numbers. Must remove the header 'n:'
            l = len(generated_sql)
            prefix, num_table, generated_sql = \
                _generate_path(table_name, customer_id, node.path, generated_sql, version, num_table)
            if len(generated_sql) > l:
                generated_sql.append("AND\n")
            generated_sql.append(_select_version(version, num_table))
            generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
            generated_sql.extend([
                f"substring(t{num_table}.entity->>'{node.path.paths[-1]}' from 3)::float",
                f" {node.operator} {value}\n",
            ])
        else:
            assert node.operator in ('=', '!='), "Operator not supported for this type"
            l = len(generated_sql)
            prefix, num_table, generated_sql = \
                _generate_path(table_name, customer_id, node.path, generated_sql, version, num_table)
            if len(generated_sql) > l:
                generated_sql.append("AND\n")
            generated_sql.append(_select_version(version, num_table))
            generated_sql.append(fr"t{num_table}.customer_id='{customer_id}' AND ")
            v = jsondumper.dump_scalar(node.value)
            if v == None:
                if node.operator == '!=':
                    generated_sql.extend([
                        f"t{num_table}.entity->>'{node.path.paths[-1]}' IS NOT NULL\n"
                    ])
                else:
                    generated_sql.extend([
                        f"t{num_table}.entity->>'{node.path.paths[-1]}' IS NULL\n"
                    ])
            else:
                generated_sql.extend([
                    f"t{num_table}.entity->>'{node.path.paths[-1]}' {node.operator} '",
                    str(v),
                    "'\n"
                ])
    return prefix, num_table, generated_sql


def _flatten(l: List[Any]) -> List[Any]:
    if l == []:
        return l
    if isinstance(l[0], list):
        return _flatten(l[0]) + _flatten(l[1:])
    return l[:1] + _flatten(l[1:])


def _sql_filter(table_name: str,
                grid_filter: Optional[str],
                version: datetime,
                limit: int = 0,
                customer_id: str = ''):
    generated_sql = _generate_sql_block(
        table_name,
        customer_id,
        _optimize_filter_for_sql(parse_filter(grid_filter)._head),
        [],
        1,
        limit,
        version)
    sql_request = f'-- {grid_filter}\n' + \
                  ''.join(_flatten(generated_sql))
    log.debug(sql_request)
    return sql_request


def _exec_sql_filter(params: Dict[str, Any],
                     cursor,
                     table_name: str,
                     grid_filter: Optional[str],
                     version: datetime,
                     limit: int = 0,
                     customer_id: str = ''):
    if grid_filter is None or grid_filter == '':
        cursor.execute(params["SELECT_ENTITY"], (version, version, customer_id))
        return

    sql_request = _sql_filter(
        table_name,
        grid_filter,
        version,
        limit,
        customer_id)
    log.debug(sql_request)
    cursor.execute(sql_request)
    return cursor


def get_db_parameters(table_name: str) -> Dict[str, Any]:
    return {
        "sql_type_to_json": lambda x: x,
        "exec_sql_filter": _exec_sql_filter,
        "CREATE_HAYSTACK_TABLE": textwrap.dedent(f'''
           CREATE TABLE IF NOT EXISTS {table_name}
               (
               id text,
               customer_id text NOT NULL,
               start_datetime timestamp NOT NULL,
               end_datetime timestamp,
               entity jsonb NOT NULL
               );
           '''),
        "CREATE_HAYSTACK_INDEX_1": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_index ON {table_name} USING hash
            (
                id
            )
            '''),
        "CREATE_HAYSTACK_INDEX_2": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_index_gin ON {table_name} USING GIN (entity);
            '''),
        "CREATE_METADATA_TABLE": textwrap.dedent(f'''
           CREATE TABLE IF NOT EXISTS {table_name}_meta_datas
               (
               customer_id text NOT NULL,
               start_datetime timestamp NOT NULL,
               end_datetime timestamp,
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
        WHERE %s >= start_datetime AND (%s < end_datetime or end_datetime is NULL)
        AND customer_id = %s
        '''),
        "CLOSE_META_DATA": textwrap.dedent(f'''
            UPDATE {table_name}_meta_datas  SET end_datetime=%s
            WHERE end_datetime IS NULL
            AND customer_id=%s
            '''),
        "UDPATE_META_DATA": textwrap.dedent(f'''
            INSERT INTO {table_name}_meta_datas VALUES (%s,%s,null,%s,%s)
            '''),
        "SELECT_ENTITY": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE %s >= start_datetime AND (%s < end_datetime or end_datetime is NULL)
            AND customer_id = %s
            '''),
        "SELECT_ENTITY_WITH_ID": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE %s >= start_datetime AND (%s < end_datetime or end_datetime is NULL)
            AND customer_id = %s
            AND id IN '''),
        "CLOSE_ENTITY": textwrap.dedent(f'''
            UPDATE {table_name} SET end_datetime=%s 
            WHERE id=%s AND end_datetime IS NULL
            AND customer_id=%s
            '''),
        "INSERT_ENTITY": textwrap.dedent(f'''
            INSERT INTO {table_name} VALUES (%s,%s,%s,null,%s)
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
