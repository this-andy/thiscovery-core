import os
import json
from dateutil import parser
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id, now_with_tz

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'

class TestUser(TestCase):

    @classmethod
    def setUpClass(self):
        self.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(self.postgresql.dsn())

        self.conn = _get_connection()
        self.cursor = self.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'entity_update_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')


    @classmethod
    def tearDownClass(self):
        self.conn.close()
        os.unsetenv("TEST_DSN")
        self.postgresql.stop()


    def test_get_user_by_uuid_api_exists(self):
        from api.user import get_user_by_id_api
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        event = {'pathParameters': path_parameters}

        expected_status = 200
        expected_body = [{
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
        }]

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_get_user_by_uuid_api_not_exists(self):
        from api.user import get_user_by_id_api
        path_parameters = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34038"}
        event = {'pathParameters': path_parameters}

        expected_status = 404

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_get_user_by_uuid_api_bad_uuid(self):
        from api.user import get_user_by_id_api
        path_parameters = {'id': "b4308c90-f8cc-49f2-b40b-16e7c4aebb6Z"}
        event = {'pathParameters': path_parameters}

        expected_status = 400

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('uuid' in result_json)
        self.assertTrue('message' in result_json and 'uuid' in result_json['message'])


    def test_get_user_email_exists(self):
        from api.user import get_user_by_email_api

        querystring_parameters = {'email': 'altha@email.addr'}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = 200
        expected_body = [{
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
        }]

        result = get_user_by_email_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_get_user_email_not_exists(self):
        from api.user import get_user_by_email_api

        querystring_parameters = {'email': 'not.andy@thisinstitute.cam.ac.uk'}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = 404

        result = get_user_by_email_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_patch_user_api_ok(self):
        from api.user import patch_user_api
        from api.entity_update import EntityUpdate
        from jsonpatch import JsonPatch

        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'

        expected_status = 204
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
        from api.user import get_user_by_id_api
        path_parameters = {'id': user_id}
        event = {'pathParameters': path_parameters}

        expected_body = [{
            "id": user_id,
            "created": "2018-08-17T13:10:56.798192+01:00",
            "email": "simon.smith@dancingbear.com",
            "email_address_verified": True,
            "title": "Sir",
            "first_name": "simon",
            "last_name": "smith",
            "auth0_id": "new-auth0-id",
            "status": "singing"
        }]

        result = get_user_by_id_api(event, None)
        result_json = json.loads(result['body'])

        # will test modified separately so extract it from dictionary here
        result_modified = result_json[0]['modified']
        del result_json[0]['modified']

        # check the rest of the result excluding modified
        self.assertDictEqual(result_json[0], expected_body[0])

        # now check modified datetime - allow up to 10 seconds difference
        now = now_with_tz()
        result_modified_datetime = parser.parse(result_modified)
        difference = abs(now - result_modified_datetime)
        self.assertLess(difference.seconds, 10)

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

            # check created datetime - allow up to 10 seconds difference
            result_created_datetime = parser.parse(result_created)
            difference = abs(now - result_created_datetime)
            self.assertLess(difference.seconds, 10)

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
        from api.user import patch_user_api

        expected_status = 404
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
        from api.user import patch_user_api

        expected_status = 400
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
        from api.user import patch_user_api

        expected_status = 400
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
        from api.user import patch_user_api

        expected_status = 400
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
        from api.user import create_user_api

        expected_status = 201
        user_json = {
            "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
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

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(user_json)
        expected_body['modified'] = user_json['created']

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json, expected_body)

        # now check we can't insert same record again...
        expected_status = 409
        result = create_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_create_user_api_bad_uuid(self):
        from api.user import create_user_api

        expected_status = 400
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
        from api.pg_utilities import execute_query
        sql = 'Select NOW()'
        result =  execute_query(sql, 'abc')
        return result


