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
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    def test_1_list_user_projects_api_ok(self):
        from api.user_project import list_user_projects_api

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_gmt = [
            {'id': '3fd54ed7-d25c-40ba-9005-4c4da1321748', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '3ffc498f-8add-4448-b452-4fc7f463aa21', 'created': '2018-08-17T12:10:57.362814+00:00',
             'modified': '2018-08-17T12:10:57.401109+00:00', 'status': None},
            {'id': '8fdb6137-e196-4c17-8091-7a0d370fadba', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '0c137d9d-e087-448b-ba8d-24141b6ceecd', 'created': '2018-08-17T12:10:57.648741+00:00',
             'modified': '2018-08-17T12:10:57.683971+00:00', 'status': None}
        ]
        expected_body_bst = [
            {'id': '3fd54ed7-d25c-40ba-9005-4c4da1321748', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '3ffc498f-8add-4448-b452-4fc7f463aa21', 'created': '2018-08-17T13:10:57.362814+01:00',
             'modified': '2018-08-17T13:10:57.401109+01:00', 'status': None},
            {'id': '8fdb6137-e196-4c17-8091-7a0d370fadba', 'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
             'project_id': '0c137d9d-e087-448b-ba8d-24141b6ceecd', 'created': '2018-08-17T13:10:57.648741+01:00',
             'modified': '2018-08-17T13:10:57.683971+01:00', 'status': None}
        ]
        expected_body = expected_body_bst

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        event = {'queryStringParameters': querystring_parameters}
        result = list_user_projects_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_2_list_user_projects_api_user_not_exists(self):
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


    def test_3_list_user_projects_api_no_results(self) :
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


    def test_4_create_user_projects_api_ok_and_duplicate(self):
        from api.user_project import create_user_project_api

        expected_status = 201
        up_json = {
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'project_id': "0c137d9d-e087-448b-ba8d-24141b6ceecd",
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
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_5_create_user_projects_api_with_defaults(self):
        from api.user_project import create_user_project_api

        expected_status = 201
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'project_id': "0c137d9d-e087-448b-ba8d-24141b6ceecd",
            'status': 'new',
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
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


    def test_6_create_user_projects_api_user_not_exists(self):
        from api.user_project import create_user_project_api

        expected_status = 400
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42516",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa21",
            'status': 'A'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_7_create_user_projects_api_project_not_exists(self):
        from api.user_project import create_user_project_api

        expected_status = 400
        up_json = {
            'user_id': "1cbe9aad-b29f-46b5-920e-b4c496d42515",
            'project_id': "3ffc498f-8add-4448-b452-4fc7f463aa22",
            'status': 'A'
        }
        event = {'body': json.dumps(up_json)}
        result = create_user_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'integrity error' in result_json['message'])
