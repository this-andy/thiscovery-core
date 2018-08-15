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
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.users_user')


    @classmethod
    def tearDownClass(self):
        self.conn.close()
        os.unsetenv("TEST_DSN")
        self.postgresql.stop()


    def test_get_user_id_exists(self):
        from api.user import get_user_id
        user_uuid = '23e38ff4-1483-408a-ad58-d08cb5a34037'
        result = get_user_id(user_uuid, new_correlation_id())
        self.assertEqual(4, result)


    def test_get_user_id_not_exists(self):
        from api.user import get_user_id
        user_uuid = '23e38ff4-1483-408a-ad58-d08cb5a34038'
        result = get_user_id(user_uuid, new_correlation_id())
        self.assertIsNone(result)


    def test_get_user_by_uuid_api_exists(self):
        from api.user import get_user_by_uuid_api
        path_parameters = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34037"}
        event = {'pathParameters': path_parameters}

        expected_status = 200
        expected_body = [{"username": "user01", "name": "User01", "first_name": "fn1", "last_name": "LN1", "email": "user01@emailaddress.co.uk", "uuid": "23e38ff4-1483-408a-ad58-d08cb5a34037"}]

        result = get_user_by_uuid_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_get_user_by_uuid_api_not_exists(self):
        from api.user import get_user_by_uuid_api
        path_parameters = {'id': "23e38ff4-1483-408a-ad58-d08cb5a34038"}
        event = {'pathParameters': path_parameters}

        expected_status = 404

        result = get_user_by_uuid_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'user does not exist')


    def test_get_user_by_uuid_api_bad_uuid(self):
        from api.user import get_user_by_uuid_api
        path_parameters = {'id': "b4308c90-f8cc-49f2-b40b-16e7c4aebb6Z"}
        event = {'pathParameters': path_parameters}

        expected_status = 400

        result = get_user_by_uuid_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)


    def test_get_user_email_exists(self):
        from api.user import get_user_by_email_api

        querystring_parameters = {'email': 'user03@emailaddress.co.uk'}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = 200
        expected_body = [{"username": "user03", "name": "User03", "first_name": "fn3", "last_name": "LN3", "email": "user03@emailaddress.co.uk", "uuid": "e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41"}]

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
            {'op': 'replace', 'path': 'first_name', 'value': 'simon'},
            {'op': 'replace', 'path': 'last_name', 'value': 'smith'},
            {'op': 'replace', 'path': '/email', 'value': 'simon.smith@dancingbear.com'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': '8e385316-5827-4c72-8d4b-af5c57ff4679'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)

        # now check database values...
        from api.user import get_user_by_uuid_api
        path_parameters = {'id': "8e385316-5827-4c72-8d4b-af5c57ff4679"}
        event = {'pathParameters': path_parameters}

        expected_body = [{
            "username": "user02",
            "name": "User02",
            "first_name": "simon",
            "last_name": "smith",
            "email": "simon.smith@dancingbear.com",
            "uuid": "8e385316-5827-4c72-8d4b-af5c57ff4679"}]

        result = get_user_by_uuid_api(event, None)
        result_json = json.loads(result['body'])

        self.assertDictEqual(result_json[0], expected_body[0])


    def test_patch_user_api_user_not_exists(self):
        from api.user import patch_user_api

        expected_status = 404
        user_jsonpatch = [
            {'op': 'replace', 'path': 'first_name', 'value': 'simon'},
            {'op': 'replace', 'path': 'last_name', 'value': 'smith'},
            {'op': 'replace', 'path': '/email', 'value': 'simon.smith@dancingbear.com'}]
        event = {'body': json.dumps(user_jsonpatch)}
        event['pathParameters'] = {'id': '8e385316-5827-4c72-8d4b-af5c57ff4670'}

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
        event['pathParameters'] = {'id': '8e385316-5827-4c72-8d4b-af5c57ff4679'}

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
        event['pathParameters'] = {'id': '8e385316-5827-4c72-8d4b-af5c57ff4679'}

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
        event['pathParameters'] = {'id': '8e385316-5827-4c72-8d4b-af5c57ff4679'}

        result = patch_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(result_status, expected_status)
        self.assertTrue('message' in result_json and result_json['message'].endswith('not found in jsonpatch'))