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
import json
from http import HTTPStatus
import testing.postgresql
from unittest import TestCase
from api.common.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv, truncate_table
from api.common.utilities import new_correlation_id

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'

TEST_ON_AWS = True  # set to False for local testing

class TestProject(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

        if not TEST_ON_AWS:
            cls.postgresql = testing.postgresql.Postgresql(port=7654)

            # setup environment variable for get_connection to use
            os.environ["TEST_DSN"] = str(cls.postgresql.dsn())

            cls.conn = _get_connection()
            cls.cursor = cls.conn.cursor()

            correlation_id = new_correlation_id()
            run_sql_script_file(TEST_SQL_FOLDER + 'usergroup_create.sql', correlation_id)
            run_sql_script_file(TEST_SQL_FOLDER + 'project_create.sql', correlation_id)
            run_sql_script_file(TEST_SQL_FOLDER + 'tasktype_create.sql', correlation_id)
            run_sql_script_file(TEST_SQL_FOLDER + 'external_system_create.sql', correlation_id)
            run_sql_script_file(TEST_SQL_FOLDER + 'projecttask_create.sql', correlation_id)

        insert_data_from_csv(TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        insert_data_from_csv(TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
        insert_data_from_csv(TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask')

        # insert_data_from_csv_OLD(None, None, TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        # insert_data_from_csv_OLD(None, None, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        # insert_data_from_csv_OLD(None, None, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        # insert_data_from_csv_OLD(None, None, TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
        # insert_data_from_csv_OLD(None, None, TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask')


    @classmethod
    def tearDownClass(cls):
        if TEST_ON_AWS:
            truncate_table('public.projects_projecttask')
            truncate_table('public.projects_externalsystem')
            truncate_table('public.projects_tasktype')
            truncate_table('public.projects_project')
            truncate_table('public.projects_usergroup')
        else:
            cls.conn.close()
            os.unsetenv("TEST_DSN")
            cls.postgresql.stop()


    def test_1_list_projects_api(self):
        from api.endpoints.project import list_projects_api

        expected_status = HTTPStatus.OK
        # todo figure out how do do this properly!
        expected_body_bst = [
            {"id": "3ffc498f-8add-4448-b452-4fc7f463aa21", "name": "CTG Monitoring", "short_name": "CTG Monitoring",
             "created": "2018-08-17T13:10:56.084487+01:00", "modified": "2018-08-17T13:10:56.119612+01:00", "status": "complete",
             "visibility":"public",
             "tasks": [
                 {"id": "c92c8289-3590-4a85-b699-98bc8171ccde", "description": "Systematic review for CTG monitoring",
                  "created": "2018-08-17T13:10:56.98669+01:00", "modified": "2018-08-17T13:10:57.023286+01:00",
                  "earliest_start_date": "2018-09-15T13:00:00+01:00", "closing_date": "2018-08-17T13:00:00+01:00", "signup_status": "not-open",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "public", "external_system_id": None,
                  "external_task_id": "1234", "status": "active"},
                 {"id": "4ee70544-6797-4e21-8cec-5653c8d5b234", "description": "Midwife assessment for CTG monitoring",
                  "created": "2018-08-17T13:10:57.074321+01:00", "modified": "2018-08-17T13:10:57.111495+01:00",
                  "earliest_start_date": None, "closing_date": "2018-08-17T10:30:00+01:00", "signup_status": "open",
                  "task_type_id": "d92d9935-cb9e-4422-9dbb-65c3423599b1", "visibility": "public", "external_system_id": None,
                  "external_task_id": None, "status": "active"}]},
            {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment", "short_name": "Ambulance equipment",
             "created": "2018-08-17T13:10:56.173198+01:00", "modified": "2018-08-17T13:10:56.209544+01:00", "status": "active",
             "visibility":"private",
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag",
                  "created": "2018-08-17T13:10:57.162016+01:00", "modified": "2018-08-17T13:10:57.198223+01:00",
                  "earliest_start_date": "2018-11-12T20:00:00+00:00", "closing_date": None, "signup_status": "invitation",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "private", "external_system_id": None,
                  "external_task_id": "abcd", "status": "active"},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment",
                  "created": "2018-08-17T13:10:57.275273+01:00", "modified": "2018-08-17T13:10:57.311031+01:00",
                  "earliest_start_date": None, "closing_date": None, "signup_status": "closed",
                  "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "visibility": "private", "external_system_id": None,
                  "external_task_id": "8e368360-a708-4336-8feb-a8903fde0210", "status": "complete"}]
             }]

        expected_body_gmt = [
            {"id": "3ffc498f-8add-4448-b452-4fc7f463aa21", "name": "CTG Monitoring", "short_name": "CTG Monitoring",
             "created": "2018-08-17T12:10:56.084487+00:00", "modified": "2018-08-17T12:10:56.119612+00:00", "status": "complete",
             "visibility":"public",
             "tasks": [
                 {"id": "c92c8289-3590-4a85-b699-98bc8171ccde", "description": "Systematic review for CTG monitoring",
                  "created": "2018-08-17T12:10:56.98669+00:00", "modified": "2018-08-17T12:10:57.023286+00:00",
                  "earliest_start_date": "2018-09-15T12:00:00+00:00", "closing_date": "2018-08-17T12:00:00+00:00", "signup_status": "not-open",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "public", "external_system_id": None,
                  "external_task_id": "1234", "status": "active"},
                 {"id": "4ee70544-6797-4e21-8cec-5653c8d5b234", "description": "Midwife assessment for CTG monitoring",
                  "created": "2018-08-17T12:10:57.074321+00:00", "modified": "2018-08-17T12:10:57.111495+00:00",
                  "earliest_start_date": None, "closing_date": "2018-08-17T09:30:00+00:00", "signup_status": "open",
                  "task_type_id": "d92d9935-cb9e-4422-9dbb-65c3423599b1", "visibility": "public", "external_system_id": None,
                  "external_task_id": None, "status": "active"}]},
            {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment", "short_name": "Ambulance equipment",
             "created": "2018-08-17T12:10:56.173198+00:00", "modified": "2018-08-17T12:10:56.209544+00:00", "status": "active",
             "visibility":"private",
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag",
                  "created": "2018-08-17T12:10:57.162016+00:00", "modified": "2018-08-17T12:10:57.198223+00:00",
                  "earliest_start_date": "2018-11-12T20:00:00+00:00", "closing_date": None, "signup_status": "invitation",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "private", "external_system_id": None,
                  "external_task_id": "abcd", "status": "active"},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment",
                  "created": "2018-08-17T12:10:57.275273+00:00", "modified": "2018-08-17T12:10:57.311031+00:00",
                  "earliest_start_date": None, "closing_date": None, "signup_status": "closed",
                  "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "visibility": "private", "external_system_id": None,
                  "external_task_id": "8e368360-a708-4336-8feb-a8903fde0210", "status": "complete"}]
             }]

        expected_body = expected_body_gmt
        result = list_projects_api(None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(len(result_json), len(expected_body))
        for (result, expected) in zip(result_json, expected_body):
            self.assertDictEqual(result, expected)

        # self.assertDictEqual(result_json[0], expected_body[0])
        # self.assertDictEqual(result_json[1], expected_body[1])


    def test_2_get_project_api_exists(self):
        from api.endpoints.project import get_project_api

        path_parameters = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceecd"}
        event = {'pathParameters': path_parameters}

        expected_status = HTTPStatus.OK
        # todo figure out how do do this properly!
        expected_body_bst = [
            {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment", "short_name": "Ambulance equipment",
             "created": "2018-08-17T13:10:56.173198+01:00", "modified": "2018-08-17T13:10:56.209544+01:00", "status": "active",
             "visibility":"private",
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag",
                  "created": "2018-08-17T13:10:57.162016+01:00", "modified": "2018-08-17T13:10:57.198223+01:00",
                  "earliest_start_date": "2018-11-12T20:00:00+00:00", "closing_date": None, "signup_status": "invitation",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "private", "external_system_id": None,
                  "external_task_id": "abcd", "status": "active"},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment",
                  "created": "2018-08-17T13:10:57.275273+01:00", "modified": "2018-08-17T13:10:57.311031+01:00",
                  "earliest_start_date": None, "closing_date": None, "signup_status": "closed",
                  "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "visibility": "private", "external_system_id": None,
                  "external_task_id": "8e368360-a708-4336-8feb-a8903fde0210", "status": "complete"}
             ]}
        ]

        expected_body_gmt = [
            {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment", "short_name": "Ambulance equipment",
             "created": "2018-08-17T12:10:56.173198+00:00", "modified": "2018-08-17T12:10:56.209544+00:00", "status": "active",
             "visibility":"private",
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag",
                  "created": "2018-08-17T12:10:57.162016+00:00", "modified": "2018-08-17T12:10:57.198223+00:00",
                  "earliest_start_date": "2018-11-12T20:00:00+00:00", "closing_date": None, "signup_status": "invitation",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "visibility": "private", "external_system_id": None,
                  "external_task_id": "abcd", "status": "active"},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment",
                  "created": "2018-08-17T12:10:57.275273+00:00", "modified": "2018-08-17T12:10:57.311031+00:00",
                  "earliest_start_date": None, "closing_date": None, "signup_status": "closed",
                  "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "visibility": "private", "external_system_id": None,
                  "external_task_id": "8e368360-a708-4336-8feb-a8903fde0210", "status": "complete"}
             ]}
        ]

        expected_body = expected_body_gmt
        result = get_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_3_get_project_api_not_exists(self):
        from api.endpoints.project import get_project_api

        path_parameters = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceece"}
        event = {'pathParameters': path_parameters}

        expected_status = HTTPStatus.NOT_FOUND

        result = get_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'project does not exist')
