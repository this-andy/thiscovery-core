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
import thiscovery_dev_tools.testing_tools as test_tools
from http import HTTPStatus
from thiscovery_lib.utilities import DetailedValueError, ObjectDoesNotExistError, DuplicateInsertError

from api.endpoints.user_group_membership import UserGroupMembership, create_user_group_membership_api

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'

ENTITY_BASE_URL = 'v1/usergroupmembership'


class TestUserGroupMembership(test_utils.DbTestCase):

    def test_01_user_group_membership_create_from_json_basic_ok(self):
        ugm_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        ugm = UserGroupMembership.from_json(ugm_json, None)
        ugm_dict = ugm.to_dict()
        self.new_uuid_test_and_remove(ugm_dict)
        self.now_datetime_test_and_remove(ugm_dict, 'created')
        self.now_datetime_test_and_remove(ugm_dict, 'modified')
        self.assertDictEqual(ugm_json, ugm_dict)

    def test_02_user_group_membership_create_from_json_full_ok(self):
        ugm_json = {
            "id": "11110edd-5fa4-461c-b57c-aaf6b16f6822",
            "created": "2019-08-17 12:26:09.023588+01:00",
            "modified": "2019-09-17 12:26:09.023665+01:00",
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        ugm = UserGroupMembership.from_json(ugm_json, None)
        ugm_dict = ugm.to_dict()
        self.assertDictEqual(ugm_json, ugm_dict)

    def test_03_user_group_membership_create_from_json_invalid_uuid(self):
        ugm_json = {
            'user_id': 'NOT A UUID!',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        with self.assertRaises(DetailedValueError) as context:
            UserGroupMembership.from_json(ugm_json, None)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('invalid uuid', err_msg)

    def test_04_user_group_membership_create_from_json_missing_uuid(self):
        ugm_json = {
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        with self.assertRaises(DetailedValueError) as context:
            UserGroupMembership.from_json(ugm_json, None)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('missing', err_msg)

    def test_05_user_group_membership_new_from_json_ok(self):
        ugm_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        ugm = UserGroupMembership.new_from_json(ugm_json, None)
        ugm_dict = ugm.to_dict()
        self.new_uuid_test_and_remove(ugm_dict)
        self.now_datetime_test_and_remove(ugm_dict, 'created')
        self.now_datetime_test_and_remove(ugm_dict, 'modified')
        self.assertDictEqual(ugm_json, ugm_dict)

    def test_06_user_group_membership_new_from_json_url_code_ok(self):
        ugm_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'url_code': 'g2_code',
        }
        ugm = UserGroupMembership.new_from_json(ugm_json, None)
        ugm_dict = ugm.to_dict()
        self.new_uuid_test_and_remove(ugm_dict)
        self.now_datetime_test_and_remove(ugm_dict, 'created')
        self.now_datetime_test_and_remove(ugm_dict, 'modified')
        # replace url_code with uuid for testing output
        del ugm_json['url_code']
        ugm_json['user_group_id'] = '03719e6a-f85d-492b-be0f-03ab1927014d'
        self.assertDictEqual(ugm_json, ugm_dict)

    def test_07_user_group_membership_new_from_json_url_code_not_exists(self):
        ugm_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'url_code': 'non-existent_code',
        }
        with self.assertRaises(ObjectDoesNotExistError) as context:
            UserGroupMembership.new_from_json(ugm_json, None)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('url_code does not exist', err_msg)

    def test_08_user_group_membership_new_from_json_no_user(self):
        ugm_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdd',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        with self.assertRaises(ObjectDoesNotExistError) as context:
            UserGroupMembership.new_from_json(ugm_json, None)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('user does not exist', err_msg)

    def test_09_user_group_membership_new_from_json_no_user_group(self):
        ugm_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb5',
        }
        with self.assertRaises(ObjectDoesNotExistError) as context:
            UserGroupMembership.new_from_json(ugm_json, None)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('user group does not exist', err_msg)

    def test_10_user_group_membership_new_from_json_already_exists(self):
        ugm_json = {
            'user_id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        with self.assertRaises(DuplicateInsertError) as context:
            UserGroupMembership.new_from_json(ugm_json, None)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('user group membership already exists', err_msg)

    def test_11_create_user_group_membership_api_ok_and_duplicate(self):
        expected_status = HTTPStatus.CREATED
        ugm_json = {
            'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        }
        body = json.dumps(ugm_json)
        result = test_tools.test_post(create_user_group_membership_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        # # modified is not part of body supplied but is returned
        expected_body = dict.copy(ugm_json)

        self.new_uuid_test_and_remove(result_json)
        self.now_datetime_test_and_remove(result_json, 'created')
        self.now_datetime_test_and_remove(result_json, 'modified')

        self.assertEqual(expected_status, result_status, 'Return status incorrect')
        self.assertDictEqual(expected_body, result_json, 'Return body incorrect')

        # now check we can't insert same record again...
        expected_status = HTTPStatus.NO_CONTENT
        result = test_tools.test_post(create_user_group_membership_api, ENTITY_BASE_URL, None, body, None)

        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)
