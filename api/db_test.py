import psycopg2
from api.pg_utilities import execute_non_query


def duplicate_insert():
    sql = 'INSERT INTO public.test_refs(int_id, fk) VALUES (%s, %s);'
    params = (2, "226435d7-e36a-4b0b-a0bd-63e0216cbc0c")

    try:
        result = execute_non_query(sql, params, None)
        return result
    except psycopg2.IntegrityError as ex:
        print('integrity error' + str(ex.args))



if __name__ == "__main__":
    result = duplicate_insert()
    print('result=' + str(result))
