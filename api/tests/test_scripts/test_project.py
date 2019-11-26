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
from api.common.dev_config import TIMEZONE_IS_BST, DELETE_TEST_DATA
from api.common.pg_utilities import insert_data_from_csv, truncate_table
from api.common.utilities import set_running_unit_tests
from api.tests.test_scripts.testing_utilities import test_get, test_post, test_patch

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'

ENTITY_BASE_URL = 'project'

# region expected bodies setup
if TIMEZONE_IS_BST:
    tz_hour = "13"
    tz_offset = "01:00"
    tz_closing_date_hour = "10"
else:
    tz_hour = "12"
    tz_offset = "00:00"
    tz_closing_date_hour = "09"

PROJECT_01_EXPECTED_BODY = {"id": "3ffc498f-8add-4448-b452-4fc7f463aa21",
     "name": "CTG Monitoring",
     "short_name": "CTG Monitoring",
     "created": f"2018-08-17T{tz_hour}:10:56.084487+{tz_offset}",
     "modified": f"2018-08-17T{tz_hour}:10:56.119612+{tz_offset}",
     "status": "complete",
     "visibility": "public",
     "tasks": [
         {"id": "c92c8289-3590-4a85-b699-98bc8171ccde",
          "description": "Systematic review for CTG monitoring",
          "created": f"2018-08-17T{tz_hour}:10:56.98669+{tz_offset}",
          "modified": f"2018-08-17T{tz_hour}:10:57.023286+{tz_offset}",
          "earliest_start_date": f"2018-09-15T{tz_hour}:00:00+{tz_offset}",
          "closing_date": f"2018-08-17T{tz_hour}:00:00+{tz_offset}",
          "signup_status": "not-open",
          "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6",
          "visibility": "public",
          "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
          "external_task_id": "1234", "base_url": 'http://crowd.cochrane.org/index.html', "status": "active"},
         {"id": "4ee70544-6797-4e21-8cec-5653c8d5b234", "description": "Midwife assessment for CTG monitoring",
          "created": f"2018-08-17T{tz_hour}:10:57.074321+{tz_offset}",
          "modified": f"2018-08-17T{tz_hour}:10:57.111495+{tz_offset}",
          "earliest_start_date": None,
          "closing_date": f"2018-08-17T{tz_closing_date_hour}:30:00+{tz_offset}",
          "signup_status": "open",
          "task_type_id": "d92d9935-cb9e-4422-9dbb-65c3423599b1", "visibility": "public",
          "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
          "external_task_id": None, "base_url": "https://www.qualtrics.com", "status": "active"}]
                            }

PROJECT_02_EXPECTED_BODY = {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment",
             "short_name": "Ambulance equipment",
             "created": f"2018-08-17T{tz_hour}:10:56.173198+{tz_offset}",
             "modified": f"2018-08-17T{tz_hour}:10:56.209544+{tz_offset}", "status": "active",
             "visibility":"private",
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag",
                  "created": f"2018-08-17T{tz_hour}:10:57.162016+{tz_offset}",
                  "modified": f"2018-08-17T{tz_hour}:10:57.198223+{tz_offset}",
                  "earliest_start_date": "2018-11-12T20:00:00+00:00",
                  "closing_date": None, "signup_status": "invitation",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "private",
                  "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
                  "external_task_id": "abcd", "base_url": "http://crowd.cochrane.org/index.html", "status": "active"},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment",
                  "created": f"2018-08-17T{tz_hour}:10:57.275273+{tz_offset}",
                  "modified": f"2018-08-17T{tz_hour}:10:57.311031+{tz_offset}",
                  "earliest_start_date": None, "closing_date": None, "signup_status": "closed",
                  "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "visibility": "private",
                  "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                  "external_task_id": "8e368360-a708-4336-8feb-a8903fde0210",
                  "base_url": 'https://www.qualtrics.com', "status": "complete"}]
             }
# endregion

class TestProject(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        set_running_unit_tests(True)

        truncate_table('public.projects_projecttask')
        truncate_table('public.projects_externalsystem')
        truncate_table('public.projects_tasktype')
        truncate_table('public.projects_project')
        truncate_table('public.projects_usergroup')

        insert_data_from_csv(TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        insert_data_from_csv(TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
        insert_data_from_csv(TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask')


    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            truncate_table('public.projects_projecttask')
            truncate_table('public.projects_externalsystem')
            truncate_table('public.projects_tasktype')
            truncate_table('public.projects_project')
            truncate_table('public.projects_usergroup')

        set_running_unit_tests(False)

    def test_1_list_projects_api(self):
        from api.endpoints.project import list_projects_api

        expected_status = HTTPStatus.OK
        expected_body = [PROJECT_01_EXPECTED_BODY, PROJECT_02_EXPECTED_BODY]

        # result = list_projects_api(None, None)
        result = test_get(list_projects_api, ENTITY_BASE_URL, None, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(len(expected_body), len(result_json))
        for (result, expected) in zip(result_json, expected_body):
            self.assertDictEqual(expected, result)

        # self.assertDictEqual(result_json[0], expected_body[0])
        # self.assertDictEqual(result_json[1], expected_body[1])

    def test_2_get_project_api_exists(self):
        from api.endpoints.project import get_project_api

        path_parameters = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceecd"}
        # event = {'pathParameters': path_parameters}

        expected_status = HTTPStatus.OK
        expected_body = [PROJECT_02_EXPECTED_BODY]
        # result = get_project_api(event, None)

        result = test_get(get_project_api, ENTITY_BASE_URL, path_parameters, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body[0], result_json[0])

    def test_3_get_project_api_not_exists(self):
        from api.endpoints.project import get_project_api

        path_parameters = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceece"}

        expected_status = HTTPStatus.NOT_FOUND

        result = test_get(get_project_api, ENTITY_BASE_URL, path_parameters, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'project does not exist')
