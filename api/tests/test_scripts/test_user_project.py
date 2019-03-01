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
import testing.postgresql
import uuid
from http import HTTPStatus
from dateutil import parser
from unittest import TestCase
from api.common.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.common.utilities import new_correlation_id, now_with_tz

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'

class TestUserProject(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(cls.postgresql.dsn())

        cls.conn = _get_connection()
        cls.cursor = cls.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'usergroup_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_project_create.sql', correlation_id)

        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    def test_01_list_user_projects_api_ok(self):
        from api.endpoints.user_project import list_user_projects_api

        expected_status = HTTPStatus.OK
        # todo figure out how do do this properly!
        expected_body_gmt = [
            {'id': '3fd54ed7-d25c-40ba-9005-4c4da1321748', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '3ffc498f-8add-4448-b452-4fc7f463aa21', 'created': '2018-08-17T12:10:57.362814+00:00',
             'modified': '2018-08-17T12:10:57.401109+00:00', 'status': None},
            {'id': '8fdb6137-e196-4c17-8091-7a0d370fadba', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '0c137d9d-e087-448b-ba8d-24141b6ceecd', 'created': '2018-08-17T12:10:57.648741+00:00',
             'modified': '2018-08-17T12:10:57.683971+00:00', 'status': None}
        ]
        expected_body_bst = [
            {'id': '3fd54ed7-d25c-40ba-9005-4c4da1321748', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '3ffc498f-8add-4448-b452-4fc7f463aa21', 'created': '2018-08-17T13:10:57.362814+01:00',
             'modified': '2018-08-17T13:10:57.401109+01:00', 'status': None},
            {'id': '8fdb6137-e196-4c17-8091-7a0d370fadba', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '0c137d9d-e087-448b-ba8d-24141b6ceecd', 'created': '2018-08-17T13:10:57.648741+01:00',
             'modified': '2018-08-17T13:10:57.683971+01:00', 'status': None}
        ]
        expected_body = expected_body_bst

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_02_list_user_projects_api_user_not_exists(self):
        from api.endpoints.user_project import list_user_projects_api

        expected_status = HTTPStatus.NOT_FOUND

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e3'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_03_list_user_projects_api_no_results(self):
        from api.endpoints.user_project import list_user_projects_api

        expected_status = HTTPStatus.OK
        expected_body = []

        querystring_parameters = {'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(result_json, expected_body)


    def test_04_create_user_projects_api_ok_and_duplicate(self):
        from api.endpoints.user_project import create_user_project_api

        expected_status = HTTPStatus.CREATED
        up_json = {
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'project_id': "0c137d9d-e087-448b-ba8d-24141b6ceecd",
            'status': 'active',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(up_json)
        expected_body['modified'] = up_json['created']

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, expected_body)

        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_05_create_user_projects_api_with_defaults(self):
        from api.endpoints.user_project import create_user_project_api

        expected_status = HTTPStatus.CREATED
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'project_id': "0c137d9d-e087-448b-ba8d-24141b6ceecd"
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        id = result_json['id']
        del result_json['id']

        created = result_json['created']
        del result_json['created']

        modified = result_json['modified']
        del result_json['modified']

        status = result_json['status']
        del result_json['status']

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, result_json)

        # now check individual data items
        self.assertTrue(uuid.UUID(id).version == 4)

        result_datetime = parser.parse(created)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, 10)

        result_datetime = parser.parse(modified)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, 10)

        self.assertEqual(status, 'active')


    def test_06_create_user_projects_api_invalid_uuid(self):
        from api.endpoints.user_project import create_user_project_api

        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'id': '9620089b-e9a4-46fd-bb78-091c8449d77z',
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa21",
            'status': 'A'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'invalid' in result_json['message'])


    def test_07_create_user_projects_api_user_not_exists(self):
        from api.endpoints.user_project import create_user_project_api

        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa21",
            'status': 'active'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_08_create_user_projects_api_project_not_exists(self):
        from api.endpoints.user_project import create_user_project_api

        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa22",
            'status': 'active'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'integrity error' in result_json['message'])


    def test_09_create_user_projects_api_if_not_exists(self):
        from api.endpoints.user_project import create_user_project_if_not_exists

        user_id = "35224bd5-f8a8-41f6-8502-f96e12d6ddde"
        project_id = "0c137d9d-e087-448b-ba8d-24141b6ceecd"
        result = create_user_project_if_not_exists(user_id, project_id, None)

        # should return id of user_project created in test 4
        self.assertEqual(len(result), 1)
        self.assertEqual(result['id'], '9620089b-e9a4-46fd-bb78-091c8449d777')


    def test_10_create_user_projects_api_missing_params(self):
        from api.endpoints.user_project import create_user_project_api

        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516"
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('parameter' in result_json and 'project_id' in result_json['parameter'])
        self.assertTrue('message' in result_json and 'mandatory data missing' in result_json['message'])