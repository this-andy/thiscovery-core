import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'

class TestUserProject(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(cls.postgresql.dsn())

        cls.conn = _get_connection()
        cls.cursor = cls.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_project_create.sql', correlation_id)
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.users_user')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    def test_list_user_projects_api_ok(self):
        from api.user_project import list_user_projects_api

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_gmt = [
            {'id': '226435d7-e36a-4b0b-a0bd-63e0216cbc0b', 'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41',
             'project_id': 'a37331cb-ebb9-4457-b67b-8ce83ae1a24f', 'created': '2018-07-01T14:58:21.558716+00:00',
             'modified': '2018-07-01T14:58:21.558739+00:00', 'status': None}]
        expected_body_bst = [
            {'id': '226435d7-e36a-4b0b-a0bd-63e0216cbc0b', 'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41',
             'project_id': 'a37331cb-ebb9-4457-b67b-8ce83ae1a24f', 'created': '2018-07-01T15:58:21.558716+01:00',
             'modified': '2018-07-01T15:58:21.558739+01:00', 'status': None}]
        expected_body = expected_body_bst

        querystring_parameters = {'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_list_user_projects_api_user_not_exists(self):
        from api.user_project import list_user_projects_api

        expected_status = 404

        querystring_parameters = {'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b42'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'user does not exist')


    def test_list_user_projects_api_no_results(self) :
        from api.user_project import list_user_projects_api

        expected_status = 200
        expected_body = []

        querystring_parameters = {'user_id': 'b4308c90-f8cc-49f2-b40b-16e7c4aebb6b'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(result_json, expected_body)


    def test_create_user_projects_api_ok_and_duplicate(self):
        from api.user_project import create_user_project_api

        expected_status = 201
        up_json = {
            'user_id': "23e38ff4-1483-408a-ad58-d08cb5a34037",
            'project_id': "a37331cb-ebb9-4457-b67b-8ce83ae1a24f",
            'status': 'A',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(up_json)
        expected_body['modified'] = up_json['created']

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, expected_body)

        # now check we can't insert same record again...
        expected_status = 409
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)


    def test_create_user_projects_api_user_not_exists(self):
        from api.user_project import create_user_project_api

        expected_status = 400
        up_json = {
            'user_id': "23e38ff4-1483-408a-ad58-d08cb5a34038",
            'project_id': "a37331cb-ebb9-4457-b67b-8ce83ae1a24f",
            'status': 'A'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)


    def test_create_user_projects_api_project_not_exists(self):
        from api.user_project import create_user_project_api

        expected_status = 400
        up_json = {
            'user_id': "23e38ff4-1483-408a-ad58-d08cb5a34037",
            'project_id': "a37331cb-ebb9-4457-b67b-8ce83ae1a240",
            'status': 'A'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)