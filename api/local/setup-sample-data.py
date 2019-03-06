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

from api.common.pg_utilities import insert_data_from_csv, truncate_table

TEST_DATA_FOLDER = '../tests/test_data/'


def populate_database():
    insert_data_from_csv(TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
    insert_data_from_csv(TEST_DATA_FOLDER + 'project_data_PSFU.csv', 'public.projects_project')
    insert_data_from_csv(TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
    insert_data_from_csv(TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
    insert_data_from_csv(TEST_DATA_FOLDER + 'projecttask_data_PSFU.csv', 'public.projects_projecttask')
    insert_data_from_csv(TEST_DATA_FOLDER + 'projectgroupvisibility_data.csv', 'public.projects_projectgroupvisibility')
    insert_data_from_csv(TEST_DATA_FOLDER + 'projecttaskgroupvisibility_data.csv', 'public.projects_projecttaskgroupvisibility')
    insert_data_from_csv(TEST_DATA_FOLDER + 'user_data_PSFU.csv', 'public.projects_user')
    insert_data_from_csv(TEST_DATA_FOLDER + 'usergroupmembership_data.csv', 'public.projects_usergroupmembership')
    insert_data_from_csv(TEST_DATA_FOLDER + 'userproject_PSFU.csv', 'public.projects_userproject')
    insert_data_from_csv(TEST_DATA_FOLDER + 'usertask_PSFU.csv', 'public.projects_usertask')


def clear_database():
    truncate_table('public.projects_usergroupmembership')
    truncate_table('public.projects_usergroup')
    truncate_table('public.projects_usertask')
    truncate_table('public.projects_userproject')
    truncate_table('public.projects_userexternalaccount')
    truncate_table('public.projects_user')
    truncate_table('public.projects_tasktype')
    truncate_table('public.projects_projecttask')
    truncate_table('public.projects_projecttaskgroupvisibility')
    truncate_table('public.projects_projectgroupvisibility')
    truncate_table('public.projects_project')
    truncate_table('public.projects_externalsystem')

    truncate_table('public.projects_entityupdate')


if __name__ == "__main__":
    populate_database()
    # clear_database()
