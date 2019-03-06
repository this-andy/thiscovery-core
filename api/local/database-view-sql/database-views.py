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

import os
from api.common.pg_utilities import execute_query, execute_non_query, run_sql_script_file

VIEW_SQL_FOLDER = './'


def create_all_views():
    print (os.getcwd())
    run_sql_script_file(VIEW_SQL_FOLDER + 'view_project_group_users_create.sql', None)
    run_sql_script_file(VIEW_SQL_FOLDER + 'view_project_testgroup_users_create.sql', None)
    run_sql_script_file(VIEW_SQL_FOLDER + 'view_projecttask_group_users_create.sql', None)
    run_sql_script_file(VIEW_SQL_FOLDER + 'view_projecttask_testgroup_users_create.sql', None)

if __name__ == "__main__":
    create_all_views()
