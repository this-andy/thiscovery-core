import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'


class TestProjectStatusForUser(TestCase):

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
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'usergroup_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'usergroupmembership_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'projectgroupvisibility_create.sql', correlation_id)

        run_sql_script_file(TEST_SQL_FOLDER + 'view_project_group_users_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'view_project_testgroup_users_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'view_projecttask_group_users_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'view_projecttask_testgroup_users_create.sql', correlation_id)

        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data_PSFU.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projecttask_data_PSFU.csv', 'public.projects_projecttask')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projectgroupvisibility_data.csv', 'public.projects_projectgroupvisibility')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projecttaskgroupvisibility_data.csv', 'public.projects_projecttaskgroupvisibility')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_data_PSFU.csv', 'public.projects_user')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'usergroupmembership_data.csv', 'public.projects_usergroupmembership')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    def check_project_status_for_single_user(self, user_id, expected_is_visible):
        from api.project import get_project_status_for_user_api

        querystring_parameters = {'user_id': user_id}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = 200

        result = get_project_status_for_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)

        for (result, expected) in zip(result_json, expected_is_visible):
            print(user_id, expected, result['is_visible'])
            self.assertEqual(expected, result['is_visible'])


    def test_t_list_projects_api(self):
        from api.project import get_project_status_for_user_api

        querystring_parameters = {'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'} # altha@email.addr
        event = {'queryStringParameters': querystring_parameters}

        expected_status = 200
        expected_is_visible = [False, False, False, True, False, True, False]

        result = get_project_status_for_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)

        for (result, expected) in zip(result_json, expected_is_visible):
            print(result['is_visible'], expected)
            self.assertEqual(result['is_visible'], expected)


    def test_user_a_project_status(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'  # altha@email.addr
        expected_is_visible = [False, False, False, True, False, True, False]
        self.check_project_status_for_single_user(user_id, expected_is_visible)


    def test_user_b_project_status(self):
        user_id = '851f7b34-f76c-49de-a382-7e4089b744e2'  # bernie@email.addr
        expected_is_visible = [False, True, True, True, False, True, False]
        self.check_project_status_for_single_user(user_id, expected_is_visible)


    def test_user_c_project_status(self):
        user_id = '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'  # clive@email.addr
        expected_is_visible = [False, True, True, True, True, True, True]
        self.check_project_status_for_single_user(user_id, expected_is_visible)


    def test_user_d_project_status(self):
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'  # delia@email.addr
        expected_is_visible = [False, True, True, True, True, True, True]
        self.check_project_status_for_single_user(user_id, expected_is_visible)


    def test_user_e_project_status(self):
        user_id = '1cbe9aad-b29f-46b5-920e-b4c496d42515'  # eddie@email.addr
        expected_is_visible = [False, False, False, True, True, True, True]
        self.check_project_status_for_single_user(user_id, expected_is_visible)