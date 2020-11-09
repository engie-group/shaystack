import json
import logging
import textwrap
from datetime import datetime
from typing import Dict, Any, Optional

log = logging.getLogger("sql.Provider")


def _sql_filter(params: Dict[str, Any],
                cursor,
                table_name: str,
                grid_filter: Optional[str],
                version: datetime,
                limit: int = 0,
                customer: Optional[str] = None):
    if grid_filter is None or grid_filter == '':
        if customer:
            cursor.execute(params["SELECT_ENTITY_WITH_CUSTOMER"], (version, version, customer))
        else:
            cursor.execute(params["SELECT_ENTITY"], (version, version))
        return cursor
    raise NotImplementedError("Complex request not implemted")


def _exec_sql_filter(params: Dict[str, Any],
                     cursor,
                     table_name: str,
                     grid_filter: Optional[str],
                     version: datetime,
                     limit: int = 0,
                     customer: Optional[str] = None):
    if grid_filter is None or grid_filter == '':
        if customer:
            cursor.execute(params["SELECT_ENTITY_WITH_CUSTOMER"], (version, version, customer))
        else:
            cursor.execute(params["SELECT_ENTITY"], (version, version))
        return

    sql_request = _sql_filter(
        table_name,
        grid_filter,
        version,
        limit,
        customer)
    log.debug(sql_request)
    cursor.execute(sql_request)
    return cursor


def get_db_parameters(table_name: str) -> Dict[str, Any]:
    return {
        "sql_type_to_json": lambda x: json.loads(x),
        "exec_sql_filter": _exec_sql_filter,
        "CREATE_HAYSTACK_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}
                (
                id text, 
                customer text, 
                start_datetime text NOT NULL, 
                end_datetime text, 
                entity text NOT NULL
                );
            '''),
        "CREATE_HAYSTACK_INDEX_1": textwrap.dedent(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_index ON {table_name}(id)
            '''),
        "CREATE_HAYSTACK_INDEX_2": textwrap.dedent(f'''
            '''),
        "CREATE_METADATA_TABLE": textwrap.dedent(f'''
            CREATE TABLE IF NOT EXISTS {table_name}_meta_datas
               (
                customer text, 
                start_datetime text NOT NULL, 
                end_datetime text, 
                metadata text,
                cols text
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
            WHERE ? >= DATETIME(start_datetime) AND (? < DATETIME(end_datetime) OR end_datetime IS NULL)
            '''),
        "SELECT_META_DATA_WITH_CUSTOMER": textwrap.dedent(f'''
            SELECT metadata,cols FROM {table_name}_meta_datas
            WHERE ? >= DATETIME(start_datetime) AND (? < DATETIME(end_datetime) OR end_datetime IS NULL)
            AND customer=?
            '''),
        "CLOSE_META_DATA": textwrap.dedent(f'''
            UPDATE {table_name}_meta_datas  SET end_datetime=?
            WHERE end_datetime IS NULL
            '''),
        "UDPATE_META_DATA": textwrap.dedent(f'''
            INSERT INTO {table_name}_meta_datas VALUES (?,?,NULL,?,?)
            '''),
        "SELECT_ENTITY": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE ? >= DATETIME(start_datetime) AND (? < DATETIME(end_datetime) OR end_datetime IS NULL)
            '''),
        "SELECT_ENTITY_WITH_CUSTOMER": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE ? >= DATETIME(start_datetime) AND (? < DATETIME(end_datetime) OR end_datetime IS NULL)
            AND customer = ?
            '''),
        "SELECT_ENTITY_WITH_ID": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE ? >= DATETIME(start_datetime) AND (? < DATETIME(end_datetime) OR end_datetime IS NULL)
            AND id IN '''),
        "SELECT_ENTITY_WITH_ID_AND_CUSTOMER": textwrap.dedent(f'''
            SELECT entity FROM {table_name}
            WHERE ? >= DATETIME(start_datetime) AND (? < DATETIME(end_datetime) OR end_datetime IS NULL)
            AND customer = ?
            AND id IN '''),
        "CLOSE_ENTITY": textwrap.dedent(f'''
            UPDATE {table_name} SET end_datetime=? 
            WHERE id=? AND end_datetime IS NULL
            '''),
        "INSERT_ENTITY": textwrap.dedent(f'''
            INSERT INTO {table_name} VALUES (?,?,?,null,?)
            '''),
        "DISTINCT_VERSION": textwrap.dedent(f'''
            SELECT DISTINCT start_datetime
            FROM {table_name};
            '''),
    }
