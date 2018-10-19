import os
import json
import testing.postgresql
import uuid
from dateutil import parser
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id, now_with_tz

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
        run_sql_script_file(TEST_SQL_FOLDER + 'projecttask_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_task_create.sql', correlation_id)
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask')
        insert_data_from_csv(self.cursor, self.conn, TEST_DATA_FOLDER + 'user_task_data.csv', 'public.projects_usertask')


    @classmethod
    def tearDownClass(self):
        self.conn.close()
        os.unsetenv("TEST_DSN")
        self.postgresql.stop()


    def test_1_list_user_tasks_api_ok(self):
        pass
        from api.user_task import list_user_tasks_api

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_gmt = [
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
             'user_project_status': None, 'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
             'task_description': 'Systematic review for CTG monitoring', 'user_task_id': 'dd8d4003-bb8e-4cb8-af7f-7c82816a5ff4',
             'created': '2018-08-17T12:10:57.827727+00:00', 'modified': '2018-08-17T12:10:57.883217+00:00', 'status': None, 'consented': None},
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '8fdb6137-e196-4c17-8091-7a0d370fadba',
             'user_project_status': None, 'project_task_id': '6f1c63e2-fbe8-4d24-8680-c68a30b407e3',
             'task_description': 'Systematic review for ambulance bag', 'user_task_id': 'a3313e72-3532-482f-af5e-d31b0fa8efd6',
             'created': '2018-08-17T12:10:58.104983+00:00', 'modified': '2018-08-17T12:10:58.170637+00:00', 'status': None, 'consented': None},
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
             'user_project_status': None, 'project_task_id': '4ee70544-6797-4e21-8cec-5653c8d5b234',
             'task_description': 'Midwife assessment for CTG monitoring', 'user_task_id': '70083082-1ffd-4e45-a8a7-364f4214af12',
             'created': '2018-08-17T12:10:58.228041+00:00', 'modified': '2018-08-17T12:10:58.263516+00:00', 'status': None, 'consented': None},
        ]
        expected_body_bst = [
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
             'user_project_status': None, 'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
             'task_description': 'Systematic review for CTG monitoring', 'user_task_id': 'dd8d4003-bb8e-4cb8-af7f-7c82816a5ff4',
             'created': '2018-08-17T13:10:57.827727+01:00', 'modified': '2018-08-17T13:10:57.883217+01:00', 'status': 'active', 'consented': None},
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '8fdb6137-e196-4c17-8091-7a0d370fadba',
             'user_project_status': None, 'project_task_id': '6f1c63e2-fbe8-4d24-8680-c68a30b407e3',
             'task_description': 'Systematic review for ambulance bag', 'user_task_id': 'a3313e72-3532-482f-af5e-d31b0fa8efd6',
             'created': '2018-08-17T13:10:58.104983+01:00', 'modified': '2018-08-17T13:10:58.170637+01:00', 'status': 'complete', 'consented': None},
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
             'user_project_status': None, 'project_task_id': '4ee70544-6797-4e21-8cec-5653c8d5b234',
             'task_description': 'Midwife assessment for CTG monitoring', 'user_task_id': '70083082-1ffd-4e45-a8a7-364f4214af12',
             'created': '2018-08-17T13:10:58.228041+01:00', 'modified': '2018-08-17T13:10:58.263516+01:00', 'status': 'active', 'consented': None},
        ]
        expected_body = expected_body_bst

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_tasks_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        for actual, expected in zip(result_json,expected_body):
            self.assertDictEqual(actual, expected)
        # self.assertDictEqual(result_json[1], expected_body[1])


    def test_2_list_user_tasks_api_user_not_exists(self):
        from api.user_project import list_user_projects_api

        expected_status = 404

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e3'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_3_list_user_tasks_api_no_results(self):
        from api.user_project import list_user_projects_api

        expected_status = 200
        expected_body = []

        querystring_parameters = {'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(result_json, expected_body)


    def test_4_create_user_task_api_ok_and_duplicate(self):
        from api.user_task import create_user_task_api

        expected_status = 201
        ut_json = {
            'user_project_id': "8fdb6137-e196-4c17-8091-7a0d370fadba",
            'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
            'status': 'active',
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
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_5_create_user_task_api_with_defaults(self):
        from api.user_task import create_user_task_api

        expected_status = 201
        ut_json = {
            'user_project_id': "9645cd24-cfb8-432d-80c6-9e06fb49aff5",
            'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
            'status': 'complete',
            'consented': '2018-07-19 16:16:56.087895+01',
        }
        event = {'body': json.dumps(ut_json)}
        result = create_user_task_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        id = result_json['id']
        del result_json['id']

        created = result_json['created']
        del result_json['created']

        modified = result_json['modified']
        del result_json['modified']

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, result_json)

        # now check individual data items
        self.assertTrue(uuid.UUID(id).version == 4)

        result_datetime = parser.parse(created)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, 10)

        result_datetime = parser.parse(modified)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, 10)


    def test_6_create_user_task_api_task_not_exists(self):
        from api.user_task import create_user_task_api

        expected_status = 400
        ut_json = {
            'user_project_id': 'a55c9adc-bc5a-4e1b-be4b-e68db1a01c43',
            'project_task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf019',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01'
        }
        event = {'body': json.dumps(ut_json)}
        result = create_user_task_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'integrity error' in result_json['message'])


    def test_7_create_user_task_api_user_project_not_exists(self):
        from api.user_task import create_user_task_api

        expected_status = 400
        ut_json = {
            'user_project_id': 'a55c9adc-bc5a-4e1b-be4b-e68db1a01c44',
            'project_task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf018',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01'
        }
        event = {'body': json.dumps(ut_json)}
        result = create_user_task_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'integrity error' in result_json['message'])

