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

import psycopg2
from api.common.pg_utilities import execute_non_query, execute_query_multiple, execute_query
from api.common.dynamodb_utilities import scan
from api.common.notification_send import NOTIFICATION_TABLE_NAME


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


def check_task_signups():
    sql = 'select * from public.task_signups'
    signups_in_db = execute_query(sql)

    signups_notifications = scan(NOTIFICATION_TABLE_NAME, 'type', 'task-signup')

    print('Database:' + str(len(signups_in_db)) + ', notifications:' + str(len(signups_notifications)))

    for db_signup in signups_in_db:
        user_task_id = db_signup['user_task_id']
        found = False
        for notification in signups_notifications:
            if not found and notification['details']['id'] == user_task_id:
                # print ('match: ' + db_signup['email'])
                found = True
        if not found:
            print('no match: ' + db_signup['user_task_id'] + ', ' + db_signup['email'] + ', ' + db_signup['created'])

if __name__ == "__main__":
    result = check_task_signups()
    # print('result=' + str(result))
