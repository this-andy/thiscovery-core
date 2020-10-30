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

from api.endpoints.common.pg_utilities import execute_query_multiple, execute_query
from api.endpoints.common.notifications import get_notifications


def multiple_query():
    sql1 = 'SELECT * FROM public.projects_tasktype'
    sql2 = 'SELECT * FROM public.projects_usergroup'
    sql = sql1 + ';' + sql2
    return execute_query_multiple((sql1,sql2), (None,None))


def check_task_signups():
    sql = 'select * from public.task_signups'
    signups_in_db = execute_query(sql)

    signups_notifications = get_notifications('type', ['task-signup'])

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
