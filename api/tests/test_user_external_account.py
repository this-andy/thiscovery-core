import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'

class TestUserExternalAccount(TestCase):


    @classmethod
    def setUpClass(self):
        self.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(self.postgresql.dsn())

        self.conn = _get_connection()
        self.cursor = self.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'external_system_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_external_account_create.sql', correlation_id)
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.users_user')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_external_account_data.csv', 'public.projects_userexternalaccount')


    @classmethod
    def tearDownClass(self):
        self.conn.close()
        os.unsetenv("TEST_DSN")
        self.postgresql.stop()


    def test_create_user_external_account_api_ok_and_duplicate(self):
        from api.user_external_account import create_user_external_account_api

        expected_status = 201
        uea_json = {
            'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64ef4',
            'user_id': '8e385316-5827-4c72-8d4b-af5c57ff4679',
            'external_user_id': 'cc02',
            'status': 'A',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        }
        event = {'body': json.dumps(uea_json)}
        result = create_user_external_account_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(uea_json)
        expected_body['modified'] = '2018-06-13 14:15:16.171819+00'

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, expected_body)

        # now check we can't insert same record again...
        expected_status = 409
        result = create_user_external_account_api(event, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)


    def test_create_user_external_account_api_user_not_exists(self):
        from api.user_external_account import create_user_external_account_api

        expected_status = 400
        uea_json = {
            'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64ef4',
            'user_id': '8e385316-5827-4c72-8d4b-af5c57ff4670',
            'external_user_id': 'cc02',
            'status': 'A'
        }
        event = {'body': json.dumps(uea_json)}
        result = create_user_external_account_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)


    def test_create_user_external_account_api_ext_sys_not_exists(self):
        from api.user_external_account import create_user_external_account_api

        expected_status = 400
        uea_json = {
            'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64ef5',
            'user_id': '8e385316-5827-4c72-8d4b-af5c57ff4679',
            'external_user_id': 'cc02',
            'status': 'A'
        }
        event = {'body': json.dumps(uea_json)}
        result = create_user_external_account_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)


    def test_create_user_external_account_api_bad_user_uuid(self):
        from api.user_external_account import create_user_external_account_api

        expected_status = 400
        uea_json = {
            'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64ef4',
            'user_id': '8e385316-5827-4c72-8d4b-af5c57ff4670z',
            'external_user_id': 'cc02',
            'status': 'A'
        }
        event = {'body': json.dumps(uea_json)}
        result = create_user_external_account_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)


    def test_create_user_external_account_api_bad_ext_sys_uuid(self):
        from api.user_external_account import create_user_external_account_api

        expected_status = 400
        uea_json = {
            'external_system_id': '4a7ceb98-888c-4e38-8803-4a25ddf64efz',
            'user_id': '8e385316-5827-4c72-8d4b-af5c57ff46709',
            'external_user_id': 'cc02',
            'status': 'A'
        }
        event = {'body': json.dumps(uea_json)}
        result = create_user_external_account_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(expected_status, result_status)