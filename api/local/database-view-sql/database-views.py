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

import common.utilities as utils
from common.pg_utilities import run_sql_script_file, execute_non_query


VIEW_SQL_FOLDER = './'
ENVIRONMENT_NAME = utils.get_environment_name()


def emph(string):
    return f'\033[92m\033[1m{string}\033[0m'


def create_all_views():
    def execute_sql_script(script_file, view_name):
        run_sql_script_file(VIEW_SQL_FOLDER + script_file, None)
        print(f'Successfully created or updated database view {emph(view_name)} on environment {emph(ENVIRONMENT_NAME)}')

    files_and_views = [
        ('view_project_group_users_create.sql', 'project_group_users'),
        ('view_project_testgroup_users_create.sql', 'project_testgroup_users'),
        ('view_projecttask_group_users_create.sql', 'projecttask_group_users'),
        ('view_projecttask_testgroup_users_create.sql', 'projecttask_testgroup_users'),
        ('view_user_tasks_with_external_ids.sql', 'user_tasks_with_external_ids'),
    ]

    for file, view in files_and_views:
        try:
            execute_sql_script(file, view)
        except psycopg2.errors.InvalidTableDefinition:  # added this here because CREATE OR REPLACE cannot rename columns (https://dba.stackexchange.com/a/589)
            sql = f'DROP VIEW IF EXISTS public.{view};'
            execute_non_query(sql, None, None)
            execute_sql_script(file, view)


if __name__ == "__main__":
    create_all_views()
