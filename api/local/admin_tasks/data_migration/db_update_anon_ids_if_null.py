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
import common.pg_utilities as pg_utils


UPDATE_EXT_USER_PROJECT_ID_IF_NULL = '''
    UPDATE public.projects_userproject
    SET ext_user_project_id = user_id
    WHERE ext_user_project_id IS NULL;
'''

UPDATE_EXT_USER_TASK_ID_IF_NULL = '''
    UPDATE public.projects_usertask
    SET ext_user_task_id = id
    WHERE ext_user_task_id IS NULL;
'''

UPDATE_ANON_PROJECT_SPECIFIC_USER_ID_IF_NULL = '''
    UPDATE public.projects_userproject
    SET anon_project_specific_user_id = ext_user_project_id
    WHERE anon_project_specific_user_id IS NULL;
'''

UPDATE_ANON_USER_TASK_ID_IF_NULL = '''
    UPDATE public.projects_usertask
    SET anon_user_task_id = ext_user_task_id
    WHERE anon_user_task_id IS NULL;
'''


def main():
    pg_utils.execute_non_query_multiple(
        [
            UPDATE_EXT_USER_PROJECT_ID_IF_NULL,
            # UPDATE_EXT_USER_TASK_ID_IF_NULL
        ], [
            None,
            # None
        ]
    )
    pg_utils.execute_non_query_multiple(
        [
            UPDATE_ANON_PROJECT_SPECIFIC_USER_ID_IF_NULL,
            # UPDATE_ANON_USER_TASK_ID_IF_NULL
        ], [
            None,
            # None
        ]
    )


if __name__ == "__main__":
    main()
