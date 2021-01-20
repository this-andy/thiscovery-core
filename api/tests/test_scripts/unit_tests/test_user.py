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
import unittest
from http import HTTPStatus

import api.endpoints.notification_process as np
import api.endpoints.user as u

from api.endpoints.user import get_user_by_id_api, get_user_by_email_api, patch_user_api, create_user_api
from thiscovery_dev_tools.testing_tools import test_get, test_post, test_patch
from api.local.dev_config import TIMEZONE_IS_BST
from api.endpoints.common.entity_update import EntityUpdate
from api.endpoints.common.hubspot import HubSpotClient
from thiscovery_lib.notifications import get_notifications, NotificationStatus, \
    NotificationAttributes
from thiscovery_lib.utilities import new_correlation_id

TIME_TOLERANCE_SECONDS = 15

ENTITY_BASE_URL = 'v1/user'

# region expected results
if TIMEZONE_IS_BST:
    tz_hour = "13"
    tz_offset = "01:00"
else:
    tz_hour = "12"
    tz_offset = "00:00"

EXPECTED_USER = {
    "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
    "created": f"2018-08-17T{tz_hour}:10:56.798192+{tz_offset}",
    "modified": f"2018-08-17T{tz_hour}:10:56.833885+{tz_offset}",
    "email": "altha@email.co.uk",
    "title": "Mrs",
    "first_name": "Altha",
    "last_name": "Alcorn",
    "country_code": "GB",
    "country_name": "United Kingdom",
    "auth0_id": None,
    "crm_id": None,
    "status": None,
    "has_demo_project": False,
    "has_live_project": False,
    "avatar_string": "AA",
}


# endregion


class TestUser(test_utils.DbTestCase):
    maxDiff = None
    delete_notifications = True

    def test_01_get_user_by_uuid_api_exists(self):
        """
        Tests:
            - we can retrieve an user by querying their user_id (using path parameter ?id=)
            - the login notification triggered by api.endpoints.user.get_user_by_id works
        """
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}

        expected_status = HTTPStatus.OK

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters=path_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(EXPECTED_USER, result_json)

    def test_02_get_user_by_anon_project_specific_user_id_api_exists(self):
        """
        Tests:
            - we can retrieve an user by querying by anon_project_specific_user_id
        """
        query_parameters = {'anon_project_specific_user_id': "2c8bba57-58a9-4ac7-98e8-beb34f0692c1"}

        expected_status = HTTPStatus.OK

        result = test_get(u.get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters=query_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(EXPECTED_USER, result_json)

    def test_03_get_user_by_anon_project_specific_user_id_api_not_exists(self):
        query_parameters = {'anon_project_specific_user_id': "7da7a740-f6b0-4177-809b-5e2852605ff2"}

        expected_status = HTTPStatus.NOT_FOUND

        result = test_get(u.get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters=query_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_04_get_user_by_email_api_takes_one_and_only_one_querystring_parameter(self):
        expected_status = HTTPStatus.BAD_REQUEST
        result = test_get(u.get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters={})
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('This endpoint requires one query parameter (email or anon_project_specific_user_id); none were found' in result_json['message'])
        )

        query_parameters = {
            'anon_project_specific_user_id': "2c8bba57-58a9-4ac7-98e8-beb34f0692c1",
            'email': 'altha@email.co.uk',
        }
        result = test_get(u.get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters=query_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('Please query by either email or anon_project_specific_user_id, but not both' in result_json['message'])
        )

    def test_05_get_user_by_uuid_api_not_exists(self):
        path_parameters = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34038"}

        expected_status = HTTPStatus.NOT_FOUND

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters=path_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_06_get_user_by_uuid_api_bad_uuid(self):
        path_parameters = {'id': "b4308c90-f8cc-49f2-b40b-16e7c4aebb6Z"}

        expected_status = HTTPStatus.BAD_REQUEST

        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters=path_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])

    def test_07_get_user_email_exists(self):
        querystring_parameters = {'email': 'altha@email.co.uk'}

        expected_status = HTTPStatus.OK

        result = test_get(get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(EXPECTED_USER, result_json)

    def test_08_get_user_email_is_case_insensitive(self):
        querystring_parameters = {'email': 'Altha@email.co.uk'}

        expected_status = HTTPStatus.OK

        result = test_get(get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(EXPECTED_USER, result_json)

    def test_09_get_user_email_not_exists(self):
        querystring_parameters = {'email': 'not.andy@thisinstitute.cam.ac.uk'}
        expected_status = HTTPStatus.NOT_FOUND

        result = test_get(get_user_by_email_api, ENTITY_BASE_URL, querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_10_list_users_by_project_ok(self):
        project_id = '183c23a1-76a7-46c3-8277-501f0740939d'  # PSFU 7
        expected_users = [
            {'anon_project_specific_user_id': '1406c523-6d12-4510-a745-271ddd9ad3e2',
             'email': 'eddie@email.co.uk',
             'first_name': 'Eddie',
             'last_name': 'Eagleton',
             'project_id': '183c23a1-76a7-46c3-8277-501f0740939d',
             'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515'},
            {'anon_project_specific_user_id': '2c8bba57-58a9-4ac7-98e8-beb34f0692c1',
             'email': 'altha@email.co.uk',
             'first_name': 'Altha',
             'last_name': 'Alcorn',
             'project_id': '183c23a1-76a7-46c3-8277-501f0740939d',
             'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'},
            {'anon_project_specific_user_id': '82ca200e-66d6-455d-95bc-617f974bcb26',
             'email': 'clive@email.co.uk',
             'first_name': 'Clive',
             'last_name': 'Cresswell',
             'project_id': '183c23a1-76a7-46c3-8277-501f0740939d',
             'user_id': '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'},
        ]
        result = test_get(
            local_method=u.list_users_by_project_api,
            aws_url='v1/list-project-users',
            querystring_parameters={'project_id': project_id},
        )
        users = json.loads(result['body'])
        self.assertCountEqual(expected_users, users)

    def test_11_patch_user_api_user_not_exists(self):
        expected_status = HTTPStatus.NOT_FOUND
        user_jsonpatch = [
            {'op': 'replace', 'path': '/title', 'value': 'Sir'},
            {'op': 'replace', 'path': '/first_name', 'value': 'simon'},
        ]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdd'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])

    def test_12_patch_user_api_bad_attribute(self):
        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'op': 'replace', 'path': '/non-existent-attribute', 'value': 'simon'}]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'invalid jsonpatch')

    def test_13_patch_user_api_bad_operation(self):
        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'op': 'non-existent-operation', 'path': '/first_name', 'value': 'simon'}]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'invalid jsonpatch')

    def test_14_patch_user_api_bad_jsonpatch(self):
        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'this': 'is', 'not': '/a', 'valid': 'jsonpatch'}]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'].endswith('invalid jsonpatch'))

    def test_15_create_user_api_ok_and_duplicate(self):
        expected_status = HTTPStatus.CREATED
        user_id = '48e30e54-b4fc-4303-963f-2943dda2b139'
        user_email = 'sw@email.co.uk'
        user_json = {
            "id": user_id,
            "created": "2018-08-21T11:16:56+01:00",
            "email": user_email,
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "country_code": "GB",
            "crm_id": None,
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=body)
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

        np.process_notifications(event=None, context=None)
        # check user now has crm (hubspot) id
        # sleep(10)
        result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters={'id': user_id})
        result_json = json.loads(result['body'])
        self.assertIsNotNone(result_json['crm_id'])

        # and check that hubspot has thiscovery id
        hs_client = HubSpotClient()
        contact = hs_client.get_hubspot_contact_by_id(result_json['crm_id'])
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
        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=body)

        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])

    def test_16_create_user_api_with_defaults(self):
        expected_status = HTTPStatus.CREATED
        user_json = {
            "email": "hh@email.co.uk",
            "first_name": "Harry",
            "last_name": "Hippie",
            "country_code": "GB",
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        self.new_uuid_test_and_remove(result_json)
        self.now_datetime_test_and_remove(result_json, 'created')
        self.now_datetime_test_and_remove(result_json, 'modified')

        auth0_id = result_json['auth0_id']
        del result_json['auth0_id']

        self.assertEqual(expected_status, result_status)
        # first check what's left in returned data
        user_json['country_name'] = 'United Kingdom'
        user_json['avatar_string'] = "HH"
        user_json['crm_id'] = None
        user_json['title'] = None

        self.assertDictEqual(result_json, user_json)

        # now check individual data items
        self.assertIsNone(auth0_id)
        #
        # result_datetime = parser.parse(email_verification_expiry)
        # difference = abs(result_datetime - now_with_tz() - timedelta(hours=24))
        # self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_17_create_user_api_bad_uuid(self):
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

        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])

    def test_18_user_email_unique_constraint(self):
        """
        Tests unique constraint on email field in user database table
        """
        # create an user
        expected_status = HTTPStatus.BAD_REQUEST
        user_json = {
            "email": "clive@email.co.uk",
            "first_name": "Sidney",
            "last_name": "Silva",
            "country_code": "PT",
            "status": "new"}

        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=json.dumps(user_json))
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        expected_message = 'Database integrity error'
        expected_error = 'duplicate key value violates unique constraint "email_index"\nDETAIL:  Key ' \
                         '(lower(email::text))=(clive@email.co.uk) already exists.\n'
        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_message, result_json['message'])
        self.assertEqual(expected_error, result_json['error'])

        # now make sure the unique contraint is case insensitive
        user_json['email'] = "CLIVE@email.co.uk"
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_message, result_json['message'])
        self.assertEqual(expected_error, result_json['error'])

    def test_19_create_user_email_case_conversion(self):
        expected_status = HTTPStatus.CREATED
        user_id = 'bb918e21-5f8f-4472-94da-34064d941f2d'
        user_email = 'HerculePoirot@email.co.uk'
        user_json = {
            "id": user_id,
            "created": "2020-06-21T11:20:56+01:00",
            "email": user_email,
            "title": "Mr",
            "first_name": "Hercule",
            "last_name": "Poirot",
            "auth0_id": "1234abcd",
            "country_code": "BE",
            "crm_id": None,
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, request_body=body)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        self.assertEqual(expected_status, result_status)
        self.assertEqual(user_email.lower(), result_json['email'])

    def test_20_patch_user_api_ok(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'

        expected_status = HTTPStatus.NO_CONTENT
        user_jsonpatch = [
            {'op': 'replace', 'path': '/title', 'value': 'Sir'},
            {'op': 'replace', 'path': '/first_name', 'value': 'simon'},
            {'op': 'replace', 'path': '/last_name', 'value': 'smith'},
            {'op': 'replace', 'path': '/email', 'value': 'simon.smith@dancingbear.com'},
            {'op': 'replace', 'path': '/auth0_id', 'value': 'new-auth0-id'},
            {'op': 'replace', 'path': '/status', 'value': 'singing'},
            {'op': 'replace', 'path': '/country_code', 'value': 'GB-SCT'},
        ]
        body = json.dumps(user_jsonpatch)
        path_parameters = {'id': user_id}

        result = test_patch(patch_user_api, ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)
        # now check database values...
        path_parameters = {'id': user_id}

        expected_body = {
            "id": user_id,
            "created": f"2018-08-17T{tz_hour}:10:56.798192+{tz_offset}",
            "email": "simon.smith@dancingbear.com",
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

        result = test_get(u.get_user_by_id_api, ENTITY_BASE_URL, path_parameters=path_parameters)
        result_json = json.loads(result['body'])

        # will test modified separately so extract it from dictionary here
        self.now_datetime_test_and_remove(result_json, 'modified', tolerance=TIME_TOLERANCE_SECONDS)

        # now check that we have a corresponding entity update record
        entity_updates = EntityUpdate.get_entity_updates_for_entity('user', user_id, new_correlation_id())
        self.assertTrue(len(entity_updates) > 0, 'No entity update record found')
        if len(entity_updates) > 0:
            # get most recent update record
            last_entity_update = entity_updates[-1]

            # remove from returned value those things we don't want to test
            self.remove_dict_items_to_be_ignored_by_tests(last_entity_update, ['id', 'modified'])

            # remove and store data items to be tested individually
            # check created datetime - allow up to TIME_TOLERANCE_SECONDS difference
            self.now_datetime_test_and_remove(last_entity_update, 'created', tolerance=TIME_TOLERANCE_SECONDS)

            result_json_reverse_patch = last_entity_update['json_reverse_patch']
            del last_entity_update['json_reverse_patch']
            result_json_patch = last_entity_update['json_patch']
            del last_entity_update['json_patch']

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
                {"op": "replace", "path": "/country_code", "value": "GB"},
            ]
            self.assertCountEqual(expected_json_reverse_patch, result_json_reverse_patch)

            # and finally check what's left
            expected_body = {
                'entity_name': 'user',
                'entity_id': user_id,
            }
            self.assertDictEqual(expected_body, last_entity_update)

    @unittest.skip
    def test_21_users_demo_flag_ok(self):
        # todo: add new user(s) to test_data with distinct combinations of these flags
        expected_results = [
            {
                'user_id': "851f7b34-f76c-49de-a382-7e4089b744e2",  # bernie@email.co.uk
                'has_demo_project': True,
                'has_live_project': True,
            },
            {
                'user_id': "8518c7ed-1df4-45e9-8dc4-d49b57ae0663",  # clive@email.co.uk
                'has_demo_project': True,
                'has_live_project': True,
            },
        ]
        for expected_result in expected_results:
            path_parameters = {
                'id': expected_result['user_id']
            }

            expected_status = HTTPStatus.OK

            result = test_get(get_user_by_id_api, ENTITY_BASE_URL, path_parameters=path_parameters)
            result_status = result['statusCode']
            result_json = json.loads(result['body'])

            # test results returned from api call
            self.assertEqual(expected_status, result_status)
            for flag in ['has_demo_project', 'has_live_project']:
                self.assertEqual(expected_result[flag], result_json[flag])
