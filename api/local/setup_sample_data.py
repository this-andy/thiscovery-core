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
import csv
import os

import api.common.hubspot as hs
import api.endpoints.user as user
from api.common.pg_utilities import insert_data_from_csv, truncate_table, populate_table_from_csv
from api.common.utilities import get_aws_namespace, get_country_name, now_with_tz

# TEST_DATA_FOLDER = '../tests/test_data/'
TEST_DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'tests', 'test_data')
USER_DATA_FILE = os.path.join(TEST_DATA_FOLDER, 'user_data_PSFU.csv')


def post_sample_users_to_crm():
    with open(USER_DATA_FILE) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            user_json = {
                "id": row[0],
                "created": row[1],
                "email": row[3],
                "first_name": row[5],
                "last_name": row[6],
                "country_code": row[12],
                "country_name": get_country_name(row[12]),
                "avatar_string": f'{row[5][0].upper()}{row[6][0].upper()}',
                "status": "new"
            }

            hubspot_id, _ = hs.post_new_user_to_crm(user_json, correlation_id=None)
            user_jsonpatch = [
                {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
            ]
            user.patch_user(user_json['id'], user_jsonpatch, now_with_tz(), correlation_id=None)


def populate_database():
    insert_data_from_csv(TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
    insert_data_from_csv(TEST_DATA_FOLDER + 'project_data_PSFU.csv', 'public.projects_project')
    insert_data_from_csv(TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
    insert_data_from_csv(TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
    insert_data_from_csv(TEST_DATA_FOLDER + 'projecttask_data_PSFU.csv', 'public.projects_projecttask')
    insert_data_from_csv(TEST_DATA_FOLDER + 'projectgroupvisibility_data.csv', 'public.projects_projectgroupvisibility')
    insert_data_from_csv(TEST_DATA_FOLDER + 'projecttaskgroupvisibility_data.csv', 'public.projects_projecttaskgroupvisibility')
    insert_data_from_csv(USER_DATA_FILE, 'public.projects_user')
    insert_data_from_csv(TEST_DATA_FOLDER + 'usergroupmembership_data.csv', 'public.projects_usergroupmembership')
    insert_data_from_csv(TEST_DATA_FOLDER + 'userproject_PSFU.csv', 'public.projects_userproject')
    insert_data_from_csv(TEST_DATA_FOLDER + 'usertask_PSFU.csv', 'public.projects_usertask')


def populate_database_london_dev():
    data_folder = '../local/london_data/'
    populate_table_from_csv(data_folder,'projects_usergroup')
    populate_table_from_csv(data_folder,'projects_project')
    populate_table_from_csv(data_folder,'projects_tasktype')
    populate_table_from_csv(data_folder,'projects_externalsystem')
    populate_table_from_csv(data_folder,'projects_projecttask')
    populate_table_from_csv(data_folder,'projects_projectgroupvisibility')
    populate_table_from_csv(data_folder,'projects_projecttaskgroupvisibility')
    populate_table_from_csv(data_folder,'projects_user')
    populate_table_from_csv(data_folder,'projects_usergroupmembership')
    populate_table_from_csv(data_folder,'projects_userproject')
    populate_table_from_csv(data_folder,'projects_usertask')
    populate_table_from_csv(data_folder,'projects_userexternalaccount')
    populate_table_from_csv(data_folder,'projects_entityupdate', '\t')


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
    namespace = get_aws_namespace()
    print('***************')
    print('About to update environment: ' + namespace)
    answer = input('To confirm retype environment name (anything else cancels): ')
    if answer == namespace:
        print ('Updating ' + namespace)
        # pass
        # clear_database()
        populate_database()
        post_sample_users_to_crm()
        # populate_database_london_dev()
    else:
        print ('Action cancelled')
