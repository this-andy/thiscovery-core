import os
import json
import testing.postgresql
from unittest import TestCase
from api.pg_utilities import _get_connection, run_sql_script_file, insert_data_from_csv
from api.utilities import new_correlation_id

TEST_SQL_FOLDER = './test_sql/'
TEST_DATA_FOLDER = './test_data/'


class ProjectTaskTestResult:

    def __init__(self, task_is_visible, user_is_signedup, signup_available, user_task_status):
        self.task_is_visible = task_is_visible
        self.user_is_signedup = user_is_signedup
        self.signup_available = signup_available
        self.user_task_status = user_task_status


class TestProjectStatusForUser(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.postgresql = testing.postgresql.Postgresql(port=7654)

        # setup environment variable for get_connection to use
        os.environ["TEST_DSN"] = str(cls.postgresql.dsn())

        cls.conn = _get_connection()
        cls.cursor = cls.conn.cursor()

        correlation_id = new_correlation_id()
        run_sql_script_file(TEST_SQL_FOLDER + 'usergroup_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'tasktype_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'projecttask_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'usergroupmembership_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'projectgroupvisibility_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'projecttaskgroupvisibility_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_project_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'user_task_create.sql', correlation_id)

        run_sql_script_file(TEST_SQL_FOLDER + 'view_project_group_users_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'view_project_testgroup_users_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'view_projecttask_group_users_create.sql', correlation_id)
        run_sql_script_file(TEST_SQL_FOLDER + 'view_projecttask_testgroup_users_create.sql', correlation_id)

        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'project_data_PSFU.csv', 'public.projects_project')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projecttask_data_PSFU.csv', 'public.projects_projecttask')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projectgroupvisibility_data.csv', 'public.projects_projectgroupvisibility')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'projecttaskgroupvisibility_data.csv', 'public.projects_projecttaskgroupvisibility')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'user_data_PSFU.csv', 'public.projects_user')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'usergroupmembership_data.csv', 'public.projects_usergroupmembership')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'userproject_PSFU.csv', 'public.projects_userproject')
        insert_data_from_csv(cls.cursor, cls.conn, TEST_DATA_FOLDER + 'usertask_PSFU.csv', 'public.projects_usertask')


    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        os.unsetenv("TEST_DSN")
        cls.postgresql.stop()


    # def test_setup(self):
    #     pass


    def check_project_status_for_single_user(self, user_id, expected_results):
        from api.project import get_project_status_for_user_api

        querystring_parameters = {'user_id': user_id}
        event = {'queryStringParameters': querystring_parameters}

        expected_status = 200

        result = get_project_status_for_user_api(event, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)

        expected_project_visiblities = expected_results['project_visibility']
        for (project_result, expected_project_is_visible) in zip(result_json, expected_project_visiblities):
            print(user_id, expected_project_is_visible, project_result['project_is_visible'])
            self.assertEqual(expected_project_is_visible, project_result['project_is_visible'])
            for (task) in project_result['tasks']:
                task_desc = task['description']
                # print(task)
                expected_task_result = expected_results.get(task_desc)
                if expected_task_result is None:
                    self.assertFalse(task['task_is_visible'])
                    self.assertFalse(task['user_is_signedup'])
                    self.assertFalse(task['signup_available'])
                    self.assertIsNone(task['user_task_status'])
                else:
                    # print(expected_task_result)
                    self.assertEqual(task['task_is_visible'], expected_task_result.task_is_visible, user_id + ":" + task_desc + ":task_is_visible")
                    self.assertEqual(task['user_is_signedup'], expected_task_result.user_is_signedup, user_id + ":" + task_desc + ":user_is_signedup")
                    self.assertEqual(task['signup_available'], expected_task_result.signup_available, user_id + ":" + task_desc + ":signup_available")
                    self.assertEqual(task['user_task_status'], expected_task_result.user_task_status, user_id + ":" + task_desc + ":user_task_status")


    def test_user_a_project_status(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'  # altha@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, False, True, False]
        expected_results['PSFU-05-A']= ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-05-C']= ProjectTaskTestResult(True, False, False, None)
        expected_results['PSFU-07-A']= ProjectTaskTestResult(True, True, False, 'complete')
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_b_project_status(self):
        user_id = '851f7b34-f76c-49de-a382-7e4089b744e2'  # bernie@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, False, True, False]
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, False, True, None)
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, True, False, 'complete')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None)
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_c_project_status(self):
        user_id = '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'  # clive@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None)
        expected_results['PSFU-05-B'] = ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None)
        expected_results['PSFU-06-A'] = ProjectTaskTestResult(True, True, False, 'complete')
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None)
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_d_project_status(self):
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'  # delia@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, False, True, None)
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, True, False, 'complete')
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None)
        expected_results['PSFU-05-B'] = ProjectTaskTestResult(True, False, True, None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None)
        expected_results['PSFU-06-A'] = ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-06-B'] = ProjectTaskTestResult(True, True, False, 'complete')
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None)
        expected_results['PSFU-08-A'] = ProjectTaskTestResult(True, True, False, 'complete')
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_e_project_status(self):
        user_id = '1cbe9aad-b29f-46b5-920e-b4c496d42515'  # eddie@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, True, True, True]
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None)
        expected_results['PSFU-06-B'] = ProjectTaskTestResult(True, True, False, 'active')
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, True, False, 'complete')
        expected_results['PSFU-08-A'] = ProjectTaskTestResult(True, False, False, None)
        self.check_project_status_for_single_user(user_id, expected_results)
