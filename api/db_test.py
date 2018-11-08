import psycopg2
from api.pg_utilities import execute_non_query, execute_query, execute_query_multiple


def duplicate_insert():
    sql = 'INSERT INTO public.test_refs(int_id, fk) VALUES (%s, %s);'
    params = (2, "226435d7-e36a-4b0b-a0bd-63e0216cbc0c")

    try:
        result = execute_non_query(sql, params, None)
        return result
    except psycopg2.IntegrityError as ex:
        print('integrity error' + str(ex.args))


def multiple_query():
    sql1 = 'SELECT * FROM public.projects_tasktype'
    sql2 = 'SELECT * FROM public.projects_usergroup'
    sql = sql1 + ';' + sql2
    return execute_query_multiple((sql1,sql2), (None,None))


if __name__ == "__main__":
    result = multiple_query()
    print('result=' + str(result))
