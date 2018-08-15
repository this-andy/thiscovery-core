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
        run_sql_script_file(TEST_SQL_FOLDER + 'task_create.sql', correlation_id)

        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'task_data.csv', 'public.projects_task')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    def test_list_projects_api(self):
        from api.project import list_projects_api

        expected_status = 200
        # todo figure out how do do this properly!
        expected_body_bst = [
            {"id": "21c0779a-5fc2-4b72-8a88-0ba31456b562", "name": "Test project No 1", "short_name": "testproj01",
                "created": "2018-05-15T16:03:25.516512+01:00", "modified": "2018-05-15T16:03:25.516554+01:00", "status": None,
                "tasks": [
                    {"id": "36362f97-c5a2-47ec-9492-3c34e18dca36", "description": "SR for 1", "created": "2018-06-14T15:15:05.283843+01:00",
                        "modified": "2018-06-14T15:15:05.283868+01:00", "task_type_id": "e1706e9b-e7f1-4a7a-bba9-7b9aeb7400e0", "status": None}
                ]},
            {"id": "a37331cb-ebb9-4457-b67b-8ce83ae1a24f", "name": "Test project No 2", "short_name": "testproj02",
                "created": "2018-05-15T16:04:37.508621+01:00", "modified": "2018-05-15T16:04:37.508644+01:00", "status": None,
                "tasks": [
                    {"id": "08de83b9-1da7-4ae2-b59f-1f1725ac02e8", "description": "photo for 2", "created": "2018-06-14T15:15:22.103509+01:00",
                        "modified": "2018-06-14T15:15:22.103569+01:00", "task_type_id": "69f2645b-e1a2-45d5-a77b-279db2ba50a5", "status": None},
                    {"id": "ebd5f57b-e77c-4f26-9ae4-b65cdabaf018", "description": "delphi for 2", "created": "2018-06-14T15:15:33.099432+01:00",
                        "modified": "2018-06-14T15:15:33.099455+01:00", "task_type_id": "73a60ef7-85c7-473d-a081-dd0dd4984718", "status": None}
                ]},
            ]
        # expected_body_bst = [
        #     {"id": "21c0779a-5fc2-4b72-8a88-0ba31456b562", "name": "Test project No 1", "short_name": "testproj01", "created": "2018-05-15T16:03:25.516512+01:00", "modified": "2018-05-15T16:03:25.516554+01:00", "status": None},
        #     {"id": "a37331cb-ebb9-4457-b67b-8ce83ae1a24f", "name": "Test project No 2", "short_name": "testproj02", "created": "2018-05-15T16:04:37.508621+01:00", "modified": "2018-05-15T16:04:37.508644+01:00", "status": None}]
        expected_body = expected_body_bst
        result = list_projects_api(None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(result_json[0], expected_body[0])
        self.assertDictEqual(result_json[1], expected_body[1])