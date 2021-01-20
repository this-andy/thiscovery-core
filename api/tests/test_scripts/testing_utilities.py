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
import api.local.dev_config  # sets env variables TEST_ON_AWS and AWS_TEST_API
import api.local.secrets  # sets env variables THISCOVERY_AFS25_PROFILE and THISCOVERY_AMP205_PROFILE
import csv
import os
from thiscovery_dev_tools.testing_tools import BaseTestCase

import api.endpoints.user as user
import api.endpoints.common.pg_utilities as pg_utils
import thiscovery_lib.utilities as utils
from api.endpoints.common.hubspot import HubSpotClient
from thiscovery_lib.notifications import delete_all_notifications
from api.endpoints.common.pg_utilities import truncate_table_multiple


BASE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..')  # thiscovery-core/
TEST_DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'test_data')


class DbTestCase(BaseTestCase):
    delete_test_data = False
    delete_notifications = False

    @classmethod
    @pg_utils.db_connection_handler
    def setUpClass(cls):
        # os.environ['TEST_ON_AWS'] = str(TEST_ON_AWS)
        super().setUpClass()
        cls.clear_test_data()
        delete_all_notifications()
        pg_utils.insert_data_from_csv_multiple(
            (os.path.join(TEST_DATA_FOLDER, 'usergroup_data.csv'), 'public.projects_usergroup'),
            (os.path.join(TEST_DATA_FOLDER, 'project_data_PSFU.csv'), 'public.projects_project'),
            (os.path.join(TEST_DATA_FOLDER, 'tasktype_data.csv'), 'public.projects_tasktype'),
            (os.path.join(TEST_DATA_FOLDER, 'external_system_data.csv'), 'public.projects_externalsystem'),
            (os.path.join(TEST_DATA_FOLDER, 'projecttask_data_PSFU.csv'), 'public.projects_projecttask'),
            (os.path.join(TEST_DATA_FOLDER, 'projectgroupvisibility_data.csv'), 'public.projects_projectgroupvisibility'),
            (os.path.join(TEST_DATA_FOLDER, 'projecttaskgroupvisibility_data.csv'), 'public.projects_projecttaskgroupvisibility'),
            (os.path.join(TEST_DATA_FOLDER, 'user_data_PSFU.csv'), 'public.projects_user'),
            (os.path.join(TEST_DATA_FOLDER, 'usergroupmembership_data.csv'), 'public.projects_usergroupmembership'),
            (os.path.join(TEST_DATA_FOLDER, 'userproject_PSFU.csv'), 'public.projects_userproject'),
            (os.path.join(TEST_DATA_FOLDER, 'usertask_PSFU.csv'), 'public.projects_usertask'),
        )

    @classmethod
    @pg_utils.db_connection_handler
    def tearDownClass(cls):
        if cls.delete_test_data:
            cls.clear_test_data()
        if cls.delete_notifications:
            delete_all_notifications()
        super().tearDownClass()

    @classmethod
    def clear_test_data(cls):
        """
        Clears all PostgreSQL database tables used by the test suite. Optionally deletes all notifications in AWS Dynamodb if cls.delete_notifications == True.
        """
        truncate_table_multiple(
            'public.projects_entityupdate',
            'public.projects_usertask',
            'public.projects_userproject',
            'public.projects_usergroupmembership',
            'public.projects_user',
            'public.projects_projecttaskgroupvisibility',
            'public.projects_projectgroupvisibility',
            'public.projects_projecttask',
            'public.projects_externalsystem',
            'public.projects_tasktype',
            'public.projects_project',
            'public.projects_usergroup',
            'public.projects_userexternalaccount',
        )


def post_sample_users_to_crm(user_test_data_csv, hs_client=None):
    if hs_client is None:
        hs_client = HubSpotClient()
    with open(user_test_data_csv) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            user_json = {
                "id": row[0],
                "created": row[1],
                "email": row[3],
                "first_name": row[5],
                "last_name": row[6],
                "country_code": row[9],
                "country_name": utils.get_country_name(row[9]),
                "avatar_string": f'{row[5][0].upper()}{row[6][0].upper()}',
                "status": "new"
            }

            hubspot_id, _ = hs_client.post_new_user_to_crm(user_json)
            user_jsonpatch = [
                {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
            ]
            user.patch_user(user_json['id'], user_jsonpatch, utils.now_with_tz(), correlation_id=None)
