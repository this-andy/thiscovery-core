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
import testing_utilities as test_utils  # this should be the first import; it sets env variables
import json
from http import HTTPStatus

from api.local.dev_config import TIMEZONE_IS_BST
from api.endpoints.user_project import list_user_projects_api, create_user_project_api, \
    create_user_project_if_not_exists
from thiscovery_dev_tools.testing_tools import test_get, test_post

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'

ENTITY_BASE_URL = 'v1/userproject'

# region expected bodies setup
if TIMEZONE_IS_BST:
    tz_hour = "12"
    tz_offset = "01:00"
else:
    tz_hour = "11"
    tz_offset = "00:00"


USER_PROJECT_01_EXPECTED_BODY = {
        "id": "000aa7fd-759b-4a8e-9fa8-f2457108e16f",
        "user_id": "851f7b34-f76c-49de-a382-7e4089b744e2",
        "project_id": "a099d03b-11e3-424c-9e97-d1c095f9823b",
        "created": f"2018-11-05T{tz_hour}:14:13.182231+{tz_offset}",
        "modified": f"2018-11-05T{tz_hour}:14:13.182304+{tz_offset}",
        "status": None,
        'anon_project_specific_user_id': '754d3468-f6f9-46ba-8e30-e29132b925b4',
}

USER_PROJECT_02_EXPECTED_BODY = {
        "id": "53320854-72f1-491a-b562-d84c252f4252",
        "user_id": "851f7b34-f76c-49de-a382-7e4089b744e2",
        "project_id": "5907275b-6d75-4ec0-ada8-5854b44fb955",
        "created": f"2018-11-05T{tz_hour}:14:23.005412+{tz_offset}",
        "modified": f"2018-11-05T{tz_hour}:14:23.005449+{tz_offset}",
        "status": None,
        'anon_project_specific_user_id': 'd4714343-305d-40b7-adc1-1b50f5575983',
}
# endregion


class TestUserProject(test_utils.DbTestCase):

    def test_01_list_user_projects_api_ok(self):
        expected_status = HTTPStatus.OK
        expected_body = [USER_PROJECT_01_EXPECTED_BODY, USER_PROJECT_02_EXPECTED_BODY]
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body[0], result_json[0])

    def test_02_list_user_projects_api_user_not_exists(self):
        expected_status = HTTPStatus.NOT_FOUND
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e3'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('does not exist' in result_json['message'])
        )

    def test_03_list_user_projects_api_no_results(self):
        expected_status = HTTPStatus.OK
        expected_body = []
        querystring_parameters = {'user_id': 'dceac123-03a7-4e29-ab5a-739e347b374d'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_body, result_json)

    def test_04_create_user_projects_api_ok_and_duplicate(self):
        expected_status = HTTPStatus.CREATED
        up_json = {
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'project_id': "5907275b-6d75-4ec0-ada8-5854b44fb955",
            'anon_project_specific_user_id': 'b75c864b-a002-466c-989f-16f63d5a6b18',
            'status': 'active',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        }
        body = json.dumps(up_json)

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)

        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(up_json)
        expected_body['modified'] = up_json['created']

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body, result_json)

        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('already exists' in result_json['message'])
        )

    def test_05_create_user_projects_api_with_defaults(self):
        expected_status = HTTPStatus.CREATED
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'project_id': "5907275b-6d75-4ec0-ada8-5854b44fb955"
        }
        body = json.dumps(up_json)

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        self.new_uuid_test_and_remove(result_json)
        self.uuid_test_and_remove(result_json, 'anon_project_specific_user_id')
        self.now_datetime_test_and_remove(result_json, 'created')
        self.now_datetime_test_and_remove(result_json, 'modified')
        self.value_test_and_remove(result_json, 'status', expected_value='active')

        self.assertDictEqual(up_json, result_json)

    def test_06_create_user_projects_api_invalid_uuid(self):
        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'id': '9620089b-e9a4-46fd-bb78-091c8449d77z',
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa21",
            'status': 'A'
        }
        body = json.dumps(up_json)

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('invalid' in result_json['message'])
        )

    def test_07_create_user_projects_api_user_not_exists(self):
        expected_status = HTTPStatus.NOT_FOUND
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa21",
            'status': 'active'
        }
        body = json.dumps(up_json)

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('does not exist' in result_json['message'])
        )

    def test_08_create_user_projects_api_project_not_exists(self):
        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa22",
            'status': 'active'
        }
        body = json.dumps(up_json)

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('integrity error' in result_json['message'])
        )

    def test_09_create_user_projects_api_if_not_exists(self):
        # todo: this test depends on test_04_create_user_projects_api_ok_and_duplicate; move to a different test class to setup/tear down independently
        user_id = "35224bd5-f8a8-41f6-8502-f96e12d6ddde"
        project_id = "5907275b-6d75-4ec0-ada8-5854b44fb955"
        result = create_user_project_if_not_exists(user_id, project_id, None)

        # should return id and anon_project_specific_user_id of user_project created in test 4
        self.assertEqual(['id', 'anon_project_specific_user_id'], list(result.keys()))
        self.assertEqual('9620089b-e9a4-46fd-bb78-091c8449d777', result['id'])

    def test_10_create_user_projects_api_missing_params(self):
        expected_status = HTTPStatus.BAD_REQUEST
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516"
        }
        body = json.dumps(up_json)

        result = test_post(create_user_project_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('parameter' in result_json) and
            ('project_id' in result_json['parameter'])
        )
        self.assertTrue(
            ('message' in result_json) and
            ('mandatory data missing' in result_json['message'])
        )
