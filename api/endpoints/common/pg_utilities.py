#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
import functools
import psycopg2

from thiscovery_lib.utilities import minimise_white_space, get_file_as_string, get_logger, ObjectDoesNotExistError, PatchOperationNotSupportedError, \
    PatchAttributeNotRecognisedError, PatchInvalidJsonError, DetailedIntegrityError, get_secret, new_correlation_id

import common.config as config


def _get_connection(correlation_id=None):
    logger = get_logger()
    if config.conn is None:
        env_dict = get_secret('database-connection')
        config.conn = psycopg2.connect(**env_dict)

        # using dsn obscures password
        logger.info('created database connection', extra={'conn_string': config.conn.dsn, 'correlation_id': correlation_id})

    return config.conn


def close_connection():
    if config.conn is not None:
        config.conn.close()
        config.conn = None


def _get_json_from_tuples(t):
    output = []
    for item in t:
        output.append(item[0])
    return output


def _jsonize_sql(base_sql):
    return 'SELECT row_to_json(row) FROM (' + base_sql + ') row'


def execute_query(base_sql, params=None, correlation_id=new_correlation_id(), return_json=True, jsonize_sql=True):
    """
    Use this method to query the database (e.g. using SELECT). Changes will not be committed to the database, so don't use this method for UPDATE and DELETE
    calls.

    Args:
        base_sql:
        params (tuple or list): http://initd.org/psycopg/docs/usage.html#passing-parameters-to-sql-queries
        correlation_id:
        return_json:
        jsonize_sql:

    Returns:

    """
    logger = get_logger()
    # tell sql to create json if that's what's wanted
    if return_json and jsonize_sql:
        sql = _jsonize_sql(base_sql)
    else:
        sql = base_sql
    sql = minimise_white_space(sql)
    param_str = str(params)
    logger.info('postgres query', extra={
        'query': sql,
        'parameters': param_str,
        'correlation_id': correlation_id
    })
    conn = _get_connection(correlation_id)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        records = cursor.fetchall()
    logger.info('postgres result', extra={'rows returned': str(len(records)), 'correlation_id': correlation_id})

    if return_json:
        return _get_json_from_tuples(records)
    else:
        return records



def execute_query_multiple(base_sql_tuple, params_tuple=None, correlation_id=new_correlation_id(), return_json=True, jsonize_sql=True):
    """
    Use this method to query the database (e.g. using SELECT). Changes will not be committed to the database, so don't use this method for UPDATE and DELETE
    calls.
    """
    logger = get_logger()
    conn = _get_connection(correlation_id)
    if params_tuple is None:
        params_tuple = tuple([None] * len(base_sql_tuple))
    results = []
    with conn.cursor() as cursor:
        for (base_sql, params) in zip(base_sql_tuple, params_tuple):
            # tell sql to create json if that's what's wanted
            if return_json and jsonize_sql:
                sql = _jsonize_sql(base_sql)
            else:
                sql = base_sql
            sql = minimise_white_space(sql)
            param_str = str(params)
            logger.info('postgres query', extra={'query': sql, 'parameters': param_str, 'correlation_id': correlation_id})

            cursor.execute(sql, params)
            records = cursor.fetchall()
            logger.info('postgres result', extra={'rows returned': str(len(records)), 'correlation_id': correlation_id})

            if return_json:
                results.append(_get_json_from_tuples(records))
            else:
                results.append(records)
    logger.info('Returning multiple results', extra={'results': results})
    return results


def execute_non_query(sql, params, correlation_id=new_correlation_id()):
    """
    Use this method to make changes that will be committed to the database (e.g. UPDATE, DELETE calls)
    """
    logger = get_logger()
    conn = _get_connection(correlation_id)
    sql = minimise_white_space(sql)
    param_str = str(params)
    logger.info('postgres query', extra={
        'query': sql,
        'parameters': param_str,
        'correlation_id': correlation_id
    })
    with conn.cursor() as cursor:
        try:
            cursor.execute(sql, params)
            rowcount = cursor.rowcount
            conn.commit()
        except psycopg2.IntegrityError as err:
            errorjson = {'error': err.args[0], 'correlation_id': str(correlation_id)}
            raise DetailedIntegrityError('Database integrity error', errorjson)
    return rowcount


def execute_non_query_multiple(sql_iterable, params_iterable, correlation_id=new_correlation_id()):
    """
    
    Args:
        sql_iterable (tuple, list, etc): iterable containing sql queries to be executed
        params_iterable (tuple, list, etc): iterable containing params for sql queries in sql_iterable
        correlation_id: 

    Returns:
        List of number of rows affected by each of the input sql queries

    """
    logger = get_logger()
    conn = _get_connection(correlation_id)
    results = []
    with conn.cursor() as cursor:
        for (sql, params) in zip(sql_iterable, params_iterable):
            sql = minimise_white_space(sql)
            param_str = str(params)
            logger.info('postgres query', extra={'query': sql, 'parameters': param_str, 'correlation_id': correlation_id})

            try:
                cursor.execute(sql, params)
            except psycopg2.IntegrityError as err:
                errorjson = {'error': err.args[0], 'correlation_id': str(correlation_id)}
                raise DetailedIntegrityError('Database integrity error', errorjson)
            except Exception as ex:
                raise ex

            rowcount = cursor.rowcount
            logger.info(f'postgres query updated {rowcount} rows', extra={'query': sql, 'parameters': param_str, 'correlation_id': correlation_id})
            results.append(rowcount)
    conn.commit()
    return results


def run_sql_script_file(sql_script_file, correlation_id=new_correlation_id()):
    sql = get_file_as_string(sql_script_file)
    execute_non_query(sql, None, correlation_id)


def insert_data_from_csv(source_file, destination_table, separator=',', header_row=False):
    conn = _get_connection()

    with open(source_file, 'r') as f:
        if header_row:
            next(f)  # Skip the header row.
        conn.cursor().copy_from(f, destination_table, sep=separator, null='')
    conn.commit()


def insert_data_from_csv_multiple(*args, separator=',', header_row=False):
    """
    Populates database with data from multiple files in a single connection

    Args:
        *args: one or more tuples in the format (path_to_source_csv_file, name_of_destination_table)
        separator (str): csv file separator
        header_row (bool): whether or not csv file contains a header row

    Returns: None
    """
    conn = _get_connection()
    with conn.cursor() as cursor:
        for source_file, destination_table in args:
            with open(source_file, 'r') as f:
                if header_row:
                    next(f)  # Skip the header row.
                cursor.copy_from(f, destination_table, sep=separator, null='')
    conn.commit()


def populate_table_from_csv(source_folder, destination_table_name, separator=','):
    if separator == ',':
        extn = '.csv'
    else:
        extn = '.tsv'
    source_file = source_folder + destination_table_name + extn
    destination_table = 'public.' + destination_table_name
    insert_data_from_csv(source_file, destination_table, separator)


def truncate_table(table_name):
    sql = 'TRUNCATE TABLE ' + table_name + ' CASCADE'
    execute_non_query(sql, None)


def truncate_table_multiple(*args):
    """
    Args:
        *args: one or more table names to truncate

    Returns: None
    """
    table_names_str = ', '.join(args)
    sql = 'TRUNCATE TABLE ' + table_names_str + ' CASCADE'
    execute_non_query(sql, None)


def create_updates_list_from_jsonpatch(mappings, jsonpatch, correlation_id=new_correlation_id()):
    tables_to_update = set()
    columns_to_update = []
    # process each attribute update and figure out where it belongs in database
    for update in jsonpatch:
        # remove leading '/' if present in jsonpatch
        try:
            if update['path'][0] == '/':
                attribute = update['path'][1:]
            else:
                attribute = update['path']
        except KeyError:
            errorjson = {'update': update, 'correlation_id': str(correlation_id)}
            raise PatchInvalidJsonError('path not found in jsonpatch', errorjson)

        # get mapping for this particular attribute
        if attribute not in mappings:
            errorjson = {'attribute': attribute, 'correlation_id': str(correlation_id)}
            raise PatchAttributeNotRecognisedError('Patch attribute not recognised', errorjson)

        mapping = mappings[attribute]

        try:
            operation = update['op']
        except KeyError:
            errorjson = {'update': update, 'correlation_id': str(correlation_id)}
            raise PatchInvalidJsonError('op not found in jsonpatch', errorjson)

        if operation != 'replace':
            errorjson = {'operation': operation, 'correlation_id': str(correlation_id)}
            raise PatchOperationNotSupportedError('Patch operation not currently supported', errorjson)

        try:
            value = update['value']
        except KeyError:
            errorjson = {'update': update, 'correlation_id': str(correlation_id)}
            raise PatchInvalidJsonError('value not found in jsonpatch', errorjson)

        # add table to list that need to be updated
        table_name = mapping['table_name']
        tables_to_update.add(table_name)

        # add column to list of cols that need to be updated
        column_name = mapping['column_name']
        columns_to_update.append({'table_name': table_name, 'column_name': column_name, 'value': value})

    return tables_to_update, columns_to_update


def create_sql_from_updates_list(tables_to_update, columns_to_update, id_column, id_to_update, modified_time):
    sql_updates = []
    for table_name in tables_to_update:
        # create update columns SQL
        cols_sql = ''
        params = ()
        for update in columns_to_update:
            if update['table_name'] == table_name:
                cols_sql += update['column_name'] + ' = %s, '
                params += (update['value'],)

        # add update to modified column
        cols_sql += 'modified = %s'
        params += (str(modified_time),)

        table_sql = 'UPDATE ' + table_name + ' SET ' + cols_sql + ' WHERE ' + id_column + ' = %s'
        params += (id_to_update,)
        sql_updates.append((table_sql, params))
    return sql_updates


def execute_jsonpatch(id_column, id_to_update, mappings, patch_json, modified_time, correlation_id=new_correlation_id()):
    """

    Args:
        id_column:
        id_to_update:
        mappings:
        patch_json:
        modified_time:
        correlation_id:

    Returns:
        Total number of rows updated in RDS database

    """
    # todo - wrap in transaction if ever extended to multi table updates
    updated_rows = 0
    try:
        tables_to_update, columns_to_update = create_updates_list_from_jsonpatch(mappings, patch_json, correlation_id)
        sql_updates = create_sql_from_updates_list(tables_to_update, columns_to_update, id_column, id_to_update, modified_time)
        for (sql_update, params) in sql_updates:
            rowcount = execute_non_query(sql_update, params, correlation_id)
            if rowcount == 0:
                errorjson = {'id_column': id_column, 'id_to_update': id_to_update, 'sql_update': sql_update, 'correlation_id': str(correlation_id)}
                raise ObjectDoesNotExistError('user does not exist', errorjson)
            updated_rows += rowcount
        return updated_rows
    except Exception as ex:
        # all exceptions will be dealt with by calling method
        raise ex


def dict_from_dataset(dataset, key_name):
    dataset_as_dict = {}
    for datarow in dataset:
        dataset_as_dict[datarow[key_name]] = datarow
    return dataset_as_dict


# region decorators
def db_connection_handler(func):
    """
    Ensures connection to the database is closed if lambda function fails. Use as innermost decorator:
        @lambda_wrapper
        @api_error_handler
        @db_connection_handler
        def decorated_function():
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            close_connection()
            return result
        except Exception:
            close_connection()
            raise
    return wrapper
# endregion
