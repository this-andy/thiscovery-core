import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'


class TestProject(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(cls.postgresql.dsn())

        cls.conn = _get_connection()
        cls.cursor = cls.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'tasktype_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'projecttask_create.sql', correlation_id)

        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    def test_1_list_projects_api(self):
        from api.project import list_projects_api

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_bst = [
            {"id": "3ffc498f-8add-4448-b452-4fc7f463aa21", "name": "CTG Monitoring", "short_name": "CTG Monitoring",
             "created": "2018-08-17T13:10:56.084487+01:00", "modified": "2018-08-17T13:10:56.119612+01:00", "status": None,
             "tasks": [
                 {"id": "c92c8289-3590-4a85-b699-98bc8171ccde", "description": "Systematic review for CTG monitoring", "created": "2018-08-17T13:10:56.98669+01:00",
                  "modified": "2018-08-17T13:10:57.023286+01:00", "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "status": None},
                 {"id": "4ee70544-6797-4e21-8cec-5653c8d5b234", "description": "Midwife assessment for CTG monitoring", "created": "2018-08-17T13:10:57.074321+01:00",
                  "modified": "2018-08-17T13:10:57.111495+01:00", "task_type_id": "d92d9935-cb9e-4422-9dbb-65c3423599b1", "status": None}]},
            {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment", "short_name": "Ambulance equipment",
             "created": "2018-08-17T13:10:56.173198+01:00", "modified": "2018-08-17T13:10:56.209544+01:00", "status": None,
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag", "created": "2018-08-17T13:10:57.162016+01:00",
                  "modified": "2018-08-17T13:10:57.198223+01:00", "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "status": None},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment", "created": "2018-08-17T13:10:57.275273+01:00",
                  "modified": "2018-08-17T13:10:57.311031+01:00", "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "status": None}]
             }]

        expected_body = expected_body_bst
        result = list_projects_api(None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])
        self.assertDictEqual(result_json[1], expected_body[1])


    def test_2_get_project_api_exists(self):
        from api.project import get_project_api

        path_parameters = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceecd"}
        event = {'pathParameters': path_parameters}

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_bst = [
            {"id": "0c137d9d-e087-448b-ba8d-24141b6ceecd", "name": "Ambulance equipment", "short_name": "Ambulance equipment",
             "created": "2018-08-17T13:10:56.173198+01:00", "modified": "2018-08-17T13:10:56.209544+01:00", "status": None,
             "tasks": [
                 {"id": "6f1c63e2-fbe8-4d24-8680-c68a30b407e3", "description": "Systematic review for ambulance bag",
                  "created": "2018-08-17T13:10:57.162016+01:00", "modified": "2018-08-17T13:10:57.198223+01:00",
                  "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6", "status": None},
                 {"id": "f3316529-e073-435e-b5c7-053da4127e96", "description": "Photos of ambulance equipment",
                  "created": "2018-08-17T13:10:57.275273+01:00", "modified": "2018-08-17T13:10:57.311031+01:00",
                  "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f", "status": None}
             ]}
        ]

        expected_body = expected_body_bst
        result = get_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])


    def test_3_get_project_api_not_exists(self):
        from api.project import get_project_api

        path_parameters = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceece"}
        event = {'pathParameters': path_parameters}

        expected_status = 404
        # todo figure out how do do this properly!

        result = get_project_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('message' in result_json and result_json['message'] == 'project does not exist')
