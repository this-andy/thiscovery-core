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
import uuid
from http import HTTPStatus
from dateutil import parser
from datetime import timedelta
import testing.postgresql
from unittest import TestCase
from api.common.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv, truncate_table
from api.common.utilities import new_correlation_id, now_with_tz

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'
TIME_TOLERANCE_SECONDS = 10

TEST_ON_AWS = True  # set to False for local testing

class TestUser(TestCase):

    @classmethod
    def setUpClass(self):
        if not TEST_ON_AWS:
            self.postgresql = testing.postgresql.Postgresql(port=7654)

            # setup environment variable for get_connection to use
            os.environ["TEST_DSN"] = str(self.postgresql.dsn())

            self.conn = _get_connection()
            self.cursor = self.conn.cursor()

            correlation_id = new_correlation_id()
            run_sql_script_file(TEST_SQL_FOLDER + 'entity_update_create.sql', correlation_id)
            run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)

        insert_data_from_csv(TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')


    @classmethod
    def tearDownClass(self):
        if TEST_ON_AWS:
            truncate_table('public.projects_user')
            truncate_table('public.projects_entityupdate')
        else:
            self.conn.close()
            os.unsetenv("TEST_DSN")
            self.postgresql.stop()


    def test_get_user_by_uuid_api_exists(self):
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        event = {'pathParameters': path_parameters}

        expected_status = HTTPStatus.OK
        expected_body_bst = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T13:10:56.798192+01:00",
            "modified": "2018-08-17T13:10:56.833885+01:00",
            "email": "altha@email.addr",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "auth0_id": None,
            "status": None
        }

        expected_body_gmt = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T12:10:56.798192+00:00",
            "modified": "2018-08-17T12:10:56.833885+00:00",
            "email": "altha@email.addr",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "auth0_id": None,
            "status": None
        }

        expected_body = expected_body_gmt

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json, expected_body)


    def test_get_user_by_uuid_api_not_exists(self):
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34038"}
        event = {'pathParameters': path_parameters}

        expected_status = HTTPStatus.NOT_FOUND

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_get_user_by_uuid_api_bad_uuid(self):
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': "b4308c90-f8cc-49f2-b40b-16e7c4aebb6Z"}
        event = {'pathParameters': path_parameters}

        expected_status = HTTPStatus.BAD_REQUEST

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])


    def test_get_user_email_exists(self):
        from api.endpoints.user import get_user_by_email_api

        querystring_parameters = {'email': 'altha@email.addr'}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = HTTPStatus.OK

        expected_body_bst = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T13:10:56.798192+01:00",
            "modified": "2018-08-17T13:10:56.833885+01:00",
            "email": "altha@email.addr",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "auth0_id": None,
            "status": None
        }

        expected_body_gmt = {
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T12:10:56.798192+00:00",
            "modified": "2018-08-17T12:10:56.833885+00:00",
            "email": "altha@email.addr",
            "email_address_verified": False,
            "title": "Mrs",
            "first_name": "Altha",
            "last_name": "Alcorn",
            "auth0_id": None,
            "status": None
        }

        expected_body = expected_body_gmt

        result = get_user_by_email_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json, expected_body)


    def test_get_user_email_not_exists(self):
        from api.endpoints.user import get_user_by_email_api

        querystring_parameters = {'email': 'not.andy@thisinstitute.cam.ac.uk'}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = HTTPStatus.NOT_FOUND

        result = get_user_by_email_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_patch_user_api_ok(self):
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
        ]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': user_id}

        result = patch_user_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)

        # now check database values...
        from api.endpoints.user import get_user_by_id_api
        path_parameters = {'id': user_id}
        event = {'pathParameters': path_parameters}

        expected_body_bst = {
            "id": user_id,
            "created": "2018-08-17T13:10:56.798192+01:00",
            "email": "simon.smith@dancingbear.com",
            "email_address_verified": True,
            "title": "Sir",
            "first_name": "simon",
            "last_name": "smith",
            "auth0_id": "new-auth0-id",
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
            "status": "singing"
        }

        expected_body = expected_body_gmt

        result = get_user_by_id_api(event, None)
        result_json = json.loads(result['body'])

        # will test modified separately so extract it from dictionary here
        result_modified = result_json['modified']
        del result_json['modified']

        # check the rest of the result excluding modified
        self.assertDictEqual(result_json, expected_body)

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
                {"op": "replace", "path": "/email", "value": "altha@email.addr"},
                {"op": "replace", "path": "/email_address_verified", "value": False}
            ]
            self.assertCountEqual(expected_json_reverse_patch,result_json_reverse_patch)

            # and finally check what's left
            expected_body = {
                'entity_name': 'user',
                'entity_id': user_id,
            }
            self.assertDictEqual(expected_body, last_entity_update)


    def test_patch_user_api_user_not_exists(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.NOT_FOUND
        user_jsonpatch = [
            {'op': 'replace', 'path': '/title', 'value': 'Sir'},
            {'op': 'replace', 'path': '/first_name', 'value': 'simon'},
        ]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdd'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_patch_user_api_bad_attribute(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'op': 'replace', 'path': '/non-existent-attribute', 'value': 'simon'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'invalid jsonpatch')


    def test_patch_user_api_bad_operation(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'op': 'non-existent-operation', 'path': '/first_name', 'value': 'simon'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'] == 'invalid jsonpatch')


    def test_patch_user_api_bad_jsonpatch(self):
        from api.endpoints.user import patch_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_jsonpatch = [{'this': 'is', 'not': '/a', 'valid': 'jsonpatch'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and result_json['message'].endswith('invalid jsonpatch'))


    def test_create_user_api_ok_and_duplicate(self):
        from api.endpoints.user import create_user_api

        expected_status = HTTPStatus.CREATED
        user_json = {
            "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
            "created": "2018-08-21T11:16:56+01:00",
            "email": "sw@email.addr",
            "email_address_verified": False,
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "status": "new"}
        event = {'body': json.dumps(user_json)}
        result = create_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(user_json)
        expected_body['modified'] = user_json['created']

        email_verification_token = result_json['email_verification_token']
        del result_json['email_verification_token']

        email_verification_expiry = result_json['email_verification_expiry']
        del result_json['email_verification_expiry']

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json, expected_body)

        self.assertTrue(uuid.UUID(email_verification_token).version == 4)

        result_datetime = parser.parse(email_verification_expiry)
        difference = abs(result_datetime - now_with_tz() - timedelta(hours=24))
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT
        result = create_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_create_user_api_with_defaults(self):
        from api.endpoints.user import create_user_api

        expected_status = HTTPStatus.CREATED
        user_json = {
            "email": "hh@email.addr",
            "title": "Mr",
            "first_name": "Harry",
            "last_name": "Hippie",
            "status": "new"}
        event = {'body': json.dumps(user_json)}
        result = create_user_api(event, None)
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

        email_verification_token = result_json['email_verification_token']
        del result_json['email_verification_token']

        email_verification_expiry = result_json['email_verification_expiry']
        del result_json['email_verification_expiry']

        self.assertEqual(expected_status, result_status)
        # first check what's left in returned data
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
        self.assertTrue(uuid.UUID(email_verification_token).version == 4)

        result_datetime = parser.parse(email_verification_expiry)
        difference = abs(result_datetime - now_with_tz() - timedelta(hours=24))
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)


    def test_create_user_api_bad_uuid(self):
        from api.endpoints.user import create_user_api

        expected_status = HTTPStatus.BAD_REQUEST
        user_json = {
            "id": "48e30e54-b4fc-4303-963f-2943dda2b13m",
            "created": "2018-08-21T11:16:56+01:00",
            "email": "sw@email.addr",
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "status": "new"}
        event = {'body': json.dumps(user_json)}
        result = create_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])


    def test_timezone(self):
        from api.common.pg_utilities import execute_query
        sql = 'Select NOW()'
        result =  execute_query(sql, None, 'abc')
        return result


