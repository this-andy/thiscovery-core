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

import json
from http import HTTPStatus
from unittest import TestCase

import api.common.pg_utilities as pg_utils
import api.endpoints.progress_process as prog_proc
import testing_utilities as tu
from api.common.utilities import set_running_unit_tests

TEST_DATA_FOLDER = '../test_data/'
DELETE_TEST_DATA = False


def clear_database():
    pg_utils.truncate_table('public.projects_usergroup')
    pg_utils.truncate_table('public.projects_usertask')
    pg_utils.truncate_table('public.projects_userproject')
    pg_utils.truncate_table('public.projects_user')
    pg_utils.truncate_table('public.projects_tasktype')
    pg_utils.truncate_table('public.projects_projecttask')
    pg_utils.truncate_table('public.projects_project')
    pg_utils.truncate_table('public.projects_externalsystem')


class MyTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

        # clear_database()
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'project_data_PSFU.csv', 'public.projects_project')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'projecttask_data_PSFU.csv', 'public.projects_projecttask')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'user_data_PSFU.csv', 'public.projects_user')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'userproject_PSFU.csv', 'public.projects_userproject')
        # pg_utils.insert_data_from_csv(TEST_DATA_FOLDER + 'usertask_PSFU.csv', 'public.projects_usertask')



    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            clear_database()
        set_running_unit_tests(False)

    def test_01_update_cochrane_progress(self):
        querystring_parameters = {'api_url': 'https://720c06c1-663e-4fd9-bcf9-63bf5d933779.mock.pstmn.io'}
        event = {'queryStringParameters': querystring_parameters}

        expected_result = {'updated_project_tasks': 1, 'updated_user_tasks': 2}
        result = prog_proc.update_cochrane_progress(event=event, context=None)
        self.assertEqual(expected_result, result)
