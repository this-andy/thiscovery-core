import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'

class TestUserTask(TestCase):

    @classmethod
    def setUpClass(self):
        self.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(self.postgresql.dsn())

        self.conn = _get_connection()
        self.cursor = self.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'tasktype_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'task_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_task_create.sql', correlation_id)
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.users_user')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'task_data.csv', 'public.projects_task')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_task_data.csv', 'public.projects_usertask')


    @classmethod
    def tearDownClass(self):
        self.conn.close()
        os.unsetenv("TEST_DSN")
        self.postgresql.stop()


    def test_list_user_tasks_api_ok(self):
        pass
        from api.user_task import list_user_tasks_api

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_gmt = [
            {'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41', 'user_project_id': '226435d7-e36a-4b0b-a0bd-63e0216cbc0b', 'user_project_status': None,
             'task_id': '08de83b9-1da7-4ae2-b59f-1f1725ac02e8', 'task_description': 'photo for 2', 'user_task_id': '851df9ed-62c9-48f8-8dcf-a60a30d67a19',
             'created': '2018-07-01T14:59:22.139052+00:00', 'modified': '2018-07-01T14:59:22.139076+00:00', 'status': None, 'consented': '2018-07-01T14:59:20+00:00'}]
        expected_body_bst = [
            {'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41', 'user_project_id': '226435d7-e36a-4b0b-a0bd-63e0216cbc0b', 'user_project_status': None,
             'task_id': '08de83b9-1da7-4ae2-b59f-1f1725ac02e8', 'task_description': 'photo for 2', 'user_task_id': '851df9ed-62c9-48f8-8dcf-a60a30d67a19',
             'created': '2018-07-01T15:59:22.139052+01:00', 'modified': '2018-07-01T15:59:22.139076+01:00', 'status': None, 'consented': '2018-07-01T15:59:20+01:00'}]
        expected_body = expected_body_bst

        querystring_parameters = {'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b41'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_tasks_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_list_user_tasks_api_user_not_exists(self):
        from api.user_project import list_user_projects_api

        expected_status = 404

        querystring_parameters = {'user_id': 'e8d6b60f-9b99-4dfa-89d4-2ec7b2038b42'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'user does not exist')


    def test_list_user_tasks_api_no_results(self):
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


    def test_create_user_task_api_ok_and_duplicate(self):
        from api.user_task import create_user_task_api

        expected_status = 201
        ut_json = {
            'user_project_id': 'a55c9adc-bc5a-4e1b-be4b-e68db1a01c43',
            'task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf018',
            'status': 'A',
            'consented': '2018-06-12 16:16:56.087895+01',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        }
        event = {'body': json.dumps(ut_json)}
        result = create_user_task_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(ut_json)
        expected_body['modified'] = ut_json['created']

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, expected_body)

        # now check we can't insert same record again...
        expected_status = 409
        result = create_user_task_api(event, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)


    def test_create_user_task_api_task_not_exists(self):
        from api.user_task import create_user_task_api

        expected_status = 400
        ut_json = {
            'user_project_id': 'a55c9adc-bc5a-4e1b-be4b-e68db1a01c43',
            'task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf019',
            'status': 'A',
            'consented': '2018-06-12 16:16:56.087895+01'
        }
        event = {'body': json.dumps(ut_json)}
        result = create_user_task_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)


    def test_create_user_task_api_user_project_not_exists(self):
        from api.user_task import create_user_task_api

        expected_status = 400
        ut_json = {
            'user_project_id': 'a55c9adc-bc5a-4e1b-be4b-e68db1a01c44',
            'task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf018',
            'status': 'A',
            'consented': '2018-06-12 16:16:56.087895+01'
        }
        event = {'body': json.dumps(ut_json)}
        result = create_user_task_api(event, None)
        result_status = result['statusCode']

        self.assertEqual(result_status, expected_status)
