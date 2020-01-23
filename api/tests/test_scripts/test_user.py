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
import uuid
from http import HTTPStatus
from dateutil import parser
from time import sleep
from unittest import TestCase
from api.common.hubspot import HubSpotClient
from api.common.pg_utilities import insert_data_from_csv, truncate_table
from api.common.utilities import new_correlation_id, now_with_tz, set_running_unit_tests
from api.common.notifications import delete_all_notifications, get_notifications, NotificationStatus, \
    NotificationAttributes
from api.common.dev_config import TIMEZONE_IS_BST
from api.endpoints.user import create_user_api, get_user_by_id_api
from api.tests.test_scripts.testing_utilities import test_get, test_post, test_patch


TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'
TIME_TOLERANCE_SECONDS = 15
DELETE_TEST_DATA = True

ENTITY_BASE_URL = 'user'


class TestUser(TestCase):

    @classmethod
    def setUpClass(self):
        set_running_unit_tests(True)

        truncate_table('public.projects_user')
        truncate_table('public.projects_entityupdate')

        insert_data_from_csv(TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')

    @classmethod
    def tearDownClass(self):
        if DELETE_TEST_DATA:
            truncate_table('public.projects_user')
            truncate_table('public.projects_entityupdate')
            delete_all_notifications()

        set_running_unit_tests(False)

    def test_01_get_user_by_uuid_api_exists(self):
        """
        Tests:
            - we can retrieve an user by querying their ID
            - the login notification triggered by api.endpoints.user.get_user_by_id works
        """
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}

        expected_status = HTTPStatus.OK

        if TIMEZONE_IS_BST:
            tz_hour = "13"
            tz_offset = "01:00"
        else:
            tz_hour = "12"
            tz_offset = "00:00"

        expected_body = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T{}:10:56.798192+{}".format(tz_hour, tz_offset),
            "modified": "2018-08-17T{}:10:56.833885+{}".format(tz_hour, tz_offset),
            "email": "altha@email.co.uk",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "country_code": "FR",
            "country_name": "France",
            "auth0_id": None,
            "crm_id": None,
            "status": None,
            "avatar_string": "AA",
        }

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body, result_json)

        # check that login notification exists
        # notifications = get_notifications('type', ['user-login'])
        # notification = notifications[0]  # should be only one
        # self.assertEqual('user-login', notification['type'])
        # self.assertEqual(expected_body['email'], notification['label'])
        # self.assertEqual(expected_body['id'], notification['details']['user_id'])
        # self.assertEqual(expected_body['email'], notification['details']['email'])


    def test_02_get_user_by_uuid_api_not_exists(self):
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34038"}

        expected_status = HTTPStatus.NOT_FOUND

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_03_get_user_by_uuid_api_bad_uuid(self):
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': "b4308c90-f8cc-49f2-b40b-16e7c4aebb6Z"}

        expected_status = HTTPStatus.BAD_REQUEST

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])

    def test_04_get_user_email_exists(self):
        from api.endpoints.user import get_user_by_email_api

        querystring_parameters = {'email': 'altha@email.co.uk'}

        expected_status = HTTPStatus.OK

        expected_body_bst = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T13:10:56.798192+01:00",
            "modified": "2018-08-17T13:10:56.833885+01:00",
            "email": "altha@email.co.uk",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "country_code": "FR",
            "country_name": "France",
            "auth0_id": None,
            "crm_id": None,
            "avatar_string": "AA",
            "status": None
        }

        expected_body_gmt = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T12:10:56.798192+00:00",
            "modified": "2018-08-17T12:10:56.833885+00:00",
            "email": "altha@email.co.uk",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "country_code": "FR",
            "country_name": "France",
            "auth0_id": None,
            "crm_id": None,
            "avatar_string": "AA",
            "status": None
        }
        expected_body = expected_body_gmt

        result = test_get(get_user_by_email_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json, expected_body)

    def test_05_get_user_email_not_exists(self):
        from api.endpoints.user import get_user_by_email_api

        querystring_parameters = {'email': 'not.andy@thisinstitute.cam.ac.uk'}
        expected_status = HTTPStatus.NOT_FOUND

        result = test_get(get_user_by_email_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_06_patch_user_api_ok(self):
        from api.endpoints.user import patch_user_api
        from api.common.entity_update import EntityUpdate

        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'

        expected_status = HTTPStatus.NO_CONTENT
        user_jsonpatch = [
            {'op': 'replace', 'path': '/title', 'value': 'Sir'},
            {'op': 'replace', 'path': '/first_name', 'value': 'simon'},
            {'op': 'replace', 'path': '/last_name', 'value': 'smith'},
            {'op': 'replace', 'path': '/email', 'value': 'simon.smith@dancingbear.com'},
            {'op': 'replace', 'path': '/email_address_verified', 'value': 'true'},
            {'op': 'replace', 'path': '/auth0_id', 'value': 'new-auth0-id'},
            {'op': 'replace', 'path': '/status', 'value': 'singing'},
            {'op': 'replace', 'path': '/country_code', 'value': 'GB-SCT'},
        ]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': user_id}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters, body, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)

        # now check database values...
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': user_id}

        expected_body_bst = {
            "id": user_id,
            "created": "2018-08-17T13:10:56.798192+01:00",
            "email": "simon.smith@dancingbear.com",
            "email_address_verified": True,
            "title": "Sir",
            "first_name": "simon",
            "last_name": "smith",
            "auth0_id": "new-auth0-id",
            "country_code": "IT",
            "country_name": "Italy",
            "crm_id": None,
            "avatar_string": "ss",
            "status": "singing"
        }

        expected_body_gmt = {
            "id": user_id,
            "created": "2018-08-17T12:10:56.798192+00:00",
            "email": "simon.smith@dancingbear.com",
            "email_address_verified": True,
            "title": "Sir",
            "first_name": "simon",
            "last_name": "smith",
            "auth0_id": "new-auth0-id",
            "country_code": "GB-SCT",
            "country_name": "United Kingdom - Scotland",
            "crm_id": None,
            "avatar_string": "ss",
            "status": "singing"
        }

        expected_body = expected_body_gmt

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters, None, None)
        result_json = json.loads(result['body'])

        # will test modified separately so extract it from dictionary here
        result_modified = result_json['modified']
        del result_json['modified']

        # check the rest of the result excluding modified
        self.assertDictEqual(expected_body, result_json)

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        result_modified_datetime = parser.parse(result_modified)
        difference = abs(now - result_modified_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

        # now check that we have a corresponding entity update record
        entity_updates = EntityUpdate.get_entity_updates_for_entity('user', user_id, new_correlation_id())
        self.assertTrue(len(entity_updates) > 0, 'No entity update record found')
        if len(entity_updates) > 0:
            # get most recent update record
            last_entity_update = entity_updates[-1]
            # remove and store data items to be tested individually
            result_created = last_entity_update['created']
            del last_entity_update['created']
            result_json_reverse_patch = last_entity_update['json_reverse_patch']
            del last_entity_update['json_reverse_patch']
            result_json_patch = last_entity_update['json_patch']
            del last_entity_update['json_patch']

            # now remove from returned value those things we don't want to test
            del last_entity_update['id']
            del last_entity_update['modified']

            # check created datetime - allow up to TIME_TOLERANCE_SECONDS difference
            result_created_datetime = parser.parse(result_created)
            difference = abs(now - result_created_datetime)
            self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

            # check jsonpatch - compare as lists in case order different
            result_json_patch = json.loads(result_json_patch)
            self.assertCountEqual(user_jsonpatch, result_json_patch)

            # need to compare list objects not strings as elements may be in different order
            result_json_reverse_patch = json.loads(result_json_reverse_patch)
            expected_json_reverse_patch = [
                {"op": "replace", "path": "/first_name", "value": "Altha"},
                {"op": "replace", "path": "/auth0_id", "value": None},
                {"op": "replace", "path": "/title", "value": "Mrs"},
                {"op": "replace", "path": "/last_name", "value": "Alcorn"},
                {"op": "replace", "path": "/status", "value": None},
                {"op": "replace", "path": "/email", "value": "altha@email.co.uk"},
                {"op": "replace", "path": "/email_address_verified", "value": False},
                {"op": "replace", "path": "/country_code", "value": "FR"},
            ]
            self.assertCountEqual(expected_json_reverse_patch, result_json_reverse_patch)

            # and finally check what's left
            expected_body = {
                'entity_name': 'user',
                'entity_id': user_id,
            }
            self.assertDictEqual(expected_body, last_entity_update)

    def test_07_patch_user_api_user_not_exists(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.NOT_FOUND
        user_jsonpatch = [
            {'op': 'replace', 'path': '/title', 'value': 'Sir'},
            {'op': 'replace', 'path': '/first_name', 'value': 'simon'},
        ]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdd'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_08_patch_user_api_bad_attribute(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'op': 'replace', 'path': '/non-existent-attribute', 'value': 'simon'}]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'invalid jsonpatch')

    def test_09_patch_user_api_bad_operation(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'op': 'non-existent-operation', 'path': '/first_name', 'value': 'simon'}]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'invalid jsonpatch')

    def test_10_patch_user_api_bad_jsonpatch(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'this': 'is', 'not': '/a', 'valid': 'jsonpatch'}]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'].endswith('invalid jsonpatch'))

    def test_11_create_user_api_ok_and_duplicate(self):
        expected_status = HTTPStatus.CREATED
        user_id = '48e30e54-b4fc-4303-963f-2943dda2b139'
        user_email = 'sw@email.co.uk'
        user_json = {
            "id": user_id,
            "created": "2018-08-21T11:16:56+01:00",
            "email": user_email,
            "email_address_verified": False,
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "country_code": "GB",
            "crm_id": None,
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(user_json)
        expected_body['modified'] = user_json['created']
        expected_body['country_name'] = 'United Kingdom'
        expected_body['avatar_string'] = 'SW'
        # expected_body['avatar_image_url'] = ''

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body, result_json)

        # check that notification message exists
        notifications = get_notifications('type', ['user-registration'])
        notification = notifications[0]  # should be only one
        self.assertEqual(user_id, notification['id'])
        self.assertEqual('user-registration', notification['type'])
        self.assertEqual(user_email, notification['label'])
        # self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.NEW.value)
        self.assertEqual(user_email, notification['details']['email'])

        # check user now has crm (hubspot) id
        sleep(10)
        result = test_get(get_user_by_id_api, 'user', {'id': user_id}, None, None)
        result_json = json.loads(result['body'])
        self.assertIsNotNone(result_json['crm_id'])

        # and check that hubspot has thiscovery id
        hs_client = HubSpotClient()
        contact = hs_client.get_hubspot_contact_by_id(result_json['crm_id'], None)
        thiscovery_id = hs_client.get_contact_property(contact, 'thiscovery_id')
        self.assertEqual(thiscovery_id, user_id)

        # check that notification message has been processewd
        notifications = get_notifications('type', ['user-registration'])
        notification = notifications[0]  # should be only one
        self.assertEqual(user_id, notification['id'])
        self.assertEqual(NotificationStatus.PROCESSED.value, notification[NotificationAttributes.STATUS.value])

        # duplicate checking...
        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT
        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)

        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])

    def test_12_create_user_api_with_defaults(self):
        from api.endpoints.user import create_user_api

        expected_status = HTTPStatus.CREATED
        user_json = {
            "email": "hh@email.co.uk",
            "first_name": "Harry",
            "last_name": "Hippie",
            "country_code": "GB",
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        id = result_json['id']
        del result_json['id']

        created = result_json['created']
        del result_json['created']

        modified = result_json['modified']
        del result_json['modified']

        auth0_id = result_json['auth0_id']
        del result_json['auth0_id']

        email_address_verified = result_json['email_address_verified']
        del result_json['email_address_verified']

        # email_verification_token = result_json['email_verification_token']
        # del result_json['email_verification_token']
        #
        # email_verification_expiry = result_json['email_verification_expiry']
        # del result_json['email_verification_expiry']

        self.assertEqual(expected_status, result_status)
        # first check what's left in returned data
        user_json['country_name'] = 'United Kingdom'
        user_json['avatar_string'] = "HH"
        user_json['crm_id'] = None
        user_json['title'] = None

        self.assertDictEqual(result_json, user_json)

        # now check individual data items
        self.assertTrue(uuid.UUID(id).version == 4)

        result_datetime = parser.parse(created)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

        result_datetime = parser.parse(modified)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

        self.assertIsNone(auth0_id)
        self.assertFalse(email_address_verified)
        # self.assertTrue(uuid.UUID(email_verification_token).version == 4)
        #
        # result_datetime = parser.parse(email_verification_expiry)
        # difference = abs(result_datetime - now_with_tz() - timedelta(hours=24))
        # self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_13_create_user_api_bad_uuid(self):
        from api.endpoints.user import create_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_json = {
            "id": "48e30e54-b4fc-4303-963f-2943dda2b13m",
            "created": "2018-08-21T11:16:56+01:00",
            "email": "sw@email.co.uk",
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "country_code": "GB",
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])

    def test_14_user_email_unique_constraint(self):
        """
        Tests unique constraint on email field in user database table
        """
        from api.endpoints.user import create_user_api

        # create an user
        expected_status = HTTPStatus.BAD_REQUEST
        user_json = {
            "email": "sid@email.co.uk",
            "first_name": "Sidney",
            "last_name": "Silva",
            "country_code": "PT",
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        expected_message = 'Database integrity error'
        expected_error = 'duplicate key value violates unique constraint "email_index"\nDETAIL:  Key ' \
                         '(lower(email::text))=(sid@email.co.uk) already exists.\n'
        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_message, result_json['message'])
        self.assertEqual(expected_error, result_json['error'])

    def test_15_user_email_unique_constraint_is_case_insensitive(self):
        """
        Tests that unique constraint on email field in user database table is case insensitive
        """
        from api.endpoints.user import create_user_api

        # create an user
        expected_status = HTTPStatus.BAD_REQUEST
        user_json = {
            "email": "SID@email.co.uk",
            "first_name": "Sidney",
            "last_name": "Silva",
            "country_code": "PT",
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        expected_message = 'Database integrity error'
        expected_error = 'duplicate key value violates unique constraint "email_index"\nDETAIL:  Key ' \
                         '(lower(email::text))=(sid@email.co.uk) already exists.\n'
        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_message, result_json['message'])
        self.assertEqual(expected_error, result_json['error'])

    # def test_16_timezone(self):
    #     from api.common.pg_utilities import execute_query
    #     sql = 'Select NOW()'
    #     result =  execute_query(sql, None, 'abc')
    #     return result
