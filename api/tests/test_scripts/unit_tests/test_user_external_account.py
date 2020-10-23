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

from thiscovery_dev_tools.testing_tools import test_post


TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'
DELETE_TEST_DATA = True

ENTITY_BASE_URL = 'v1/userexternalaccount'


class TestUserExternalAccount(test_utils.DbTestCase):

    def test_01_create_user_external_account_api_ok_and_duplicate(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.CREATED
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'external_user_id': 'cc02',
            'status': 'active',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(uea_json)
        expected_body['modified'] = '2018-06-13 14:15:16.171819+00'

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body, result_json)

        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT
        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)

        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_02_create_user_external_account_api_with_defaults(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.CREATED
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'external_user_id': 'abc74'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        self.new_uuid_test_and_remove(result_json)
        self.now_datetime_test_and_remove(result_json, 'created')
        self.now_datetime_test_and_remove(result_json, 'modified')
        self.value_test_and_remove(result_json, 'status', expected_value='active')

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(uea_json, result_json)


    def test_03_create_user_external_account_api_user_not_exists(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.NOT_FOUND
        uea_json = {
            'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64ef4',
            'user_id': '8e385316-5827-4c72-8d4b-af5c57ff4670',
            'external_user_id': 'cc02',
            'status': 'active'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_04_create_user_external_account_api_ext_sys_not_exists(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.BAD_REQUEST
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d9",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'external_user_id': 'cc02'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'integrity error' in result_json['message'])


    def test_05_create_user_external_account_api_bad_user_uuid(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.BAD_REQUEST
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6dddm",
            'external_user_id': 'cc02',
            'status': 'active'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])


    def test_06_create_user_external_account_api_bad_ext_sys_uuid(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.BAD_REQUEST
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4dm",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'external_user_id': 'cc02',
            'status': 'active'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])


    def test_07_create_user_external_account_api_bad_created_date(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.BAD_REQUEST
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'external_user_id': 'cc02',
            'status': 'active',
            'created': '2018-26-23 14:15:16.171819+00'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('datetime' in result_json)
        self.assertTrue('message' in result_json and 'datetime' in result_json['message'])


    def test_08_create_user_external_account_api_bad_status(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.BAD_REQUEST
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'external_user_id': 'cc02',
            'status': 'rubbish'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('status' in result_json)
        self.assertTrue('message' in result_json and 'status' in result_json['message'])


    def test_09_create_user_external_account_api_missing_params(self):
        from api.endpoints.user_external_account import create_user_external_account_api

        expected_status = HTTPStatus.BAD_REQUEST
        uea_json = {
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'external_user_id': 'cc02'
        }
        body = json.dumps(uea_json)

        result = test_post(create_user_external_account_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('parameter' in result_json and 'user_id' in result_json['parameter'])
        self.assertTrue('message' in result_json and 'mandatory data missing' in result_json['message'])


    # def test_10_get_or_create_user_external_account_get(self):
    #     from api.endpoints.user_external_account import get_or_create_user_external_account
    #
    #     external_system_id = 'e056e0bf-8d24-487e-a57b-4e812b40c4d8'
    #     user_id = '851f7b34-f76c-49de-a382-7e4089b744e2'
    #
    #     result = get_or_create_user_external_account(user_id, external_system_id, None)
    #     # returns id of existing record
    #     self.assertEqual("3686f075-1da1-401d-8329-10da0ccf3258", result)


    # def test_11_get_or_create_user_external_account_create(self):
    #     from api.endpoints.user_external_account import get_or_create_user_external_account
    #
    #     external_system_id = 'e056e0bf-8d24-487e-a57b-4e812b40c4d8'
    #     user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'
    #
    #     result = get_or_create_user_external_account(user_id, external_system_id, None)
    #     # returns new record
    #     self.assertNotEqual("3686f075-1da1-401d-8329-10da0ccf3258", result['id'])
    #
    #     self.assertEqual("e056e0bf-8d24-487e-a57b-4e812b40c4d8", result['external_system_id'])
    #     self.assertEqual("35224bd5-f8a8-41f6-8502-f96e12d6ddde", result['user_id'])
    #     self.assertEqual("active", result['status'])
    #
    #     result_datetime = parser.parse(result['created'])
    #     difference = abs(now_with_tz() - result_datetime)
    #     self.assertLess(difference.seconds, 10)
