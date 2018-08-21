import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

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
        self.assertTrue('message' in result_json and result_json['message'] == 'user does not exist')


    def test_get_user_by_uuid_api_bad_uuid(self):
        from api.user import get_user_by_id_api
        path_parameters = {'id': "b4308c90-f8cc-49f2-b40b-16e7c4aebb6Z"}
        event = {'pathParameters': path_parameters}

        expected_status = 400

        result = get_user_by_id_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)


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
        self.assertTrue('message' in result_json and result_json['message'] == 'user does not exist')


    def test_patch_user_api_ok(self):
        from api.user import patch_user_api

        expected_status = 204
        user_jsonpatch = [
            {'op': 'replace', 'path': 'title', 'value': 'Sir'},
            {'op': 'replace', 'path': 'first_name', 'value': 'simon'},
            {'op': 'replace', 'path': 'last_name', 'value': 'smith'},
            {'op': 'replace', 'path': '/email', 'value': 'simon.smith@dancingbear.com'},
            {'op': 'replace', 'path': 'auth0_id', 'value': 'new-auth0-id'},
            {'op': 'replace', 'path': 'status', 'value': 'singing'},
        ]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)

        # now check database values...
        from api.user import get_user_by_id_api
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        event = {'pathParameters': path_parameters}

        expected_body = [{
            "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            "created": "2018-08-17T13:10:56.798192+01:00",
            "modified": "2018-08-17T13:10:56.833885+01:00",
            "email": "simon.smith@dancingbear.com",
            "title": "Sir",
            "first_name": "simon",
            "last_name": "smith",
            "auth0_id": "new-auth0-id",
            "status": "singing"
        }]

        result = get_user_by_id_api(event, None)
        result_json = json.loads(result['body'])

        self.assertDictEqual(result_json[0], expected_body[0])


    def test_patch_user_api_user_not_exists(self):
        from api.user import patch_user_api

        expected_status = 404
        user_jsonpatch = [
            {'op': 'replace', 'path': 'title', 'value': 'Sir'},
            {'op': 'replace', 'path': 'first_name', 'value': 'simon'},
        ]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdd'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(result_status, expected_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'user does not exist')


    def test_patch_user_api_bad_attribute(self):
        from api.user import patch_user_api

        expected_status = 400
        user_jsonpatch = [{'op': 'replace', 'path': 'non-existent-attribute', 'value': 'simon'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(result_status, expected_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'Patch attribute not recognised')


    def test_patch_user_api_bad_operation(self):
        from api.user import patch_user_api

        expected_status = 400
        user_jsonpatch = [{'op': 'non-existent-operation', 'path': 'first_name', 'value': 'simon'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(result_status, expected_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'Patch operation not currently supported')


    def test_patch_user_api_bad_jsonpatch(self):
        from api.user import patch_user_api

        expected_status = 400
        user_jsonpatch = [{'this': 'is', 'not': 'a', 'valid': 'jsonpatch'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(result_status, expected_status)
        self.assertTrue('message' in result_json and result_json['message'].endswith('not found in jsonpatch'))


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

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, expected_body)

        # now check we can't insert same record again...
        expected_status = 409
        result = create_user_api(event, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)


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

        self.assertEqual(result_status, expected_status)
