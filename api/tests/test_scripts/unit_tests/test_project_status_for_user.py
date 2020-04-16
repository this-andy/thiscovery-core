#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#

import json
from http import HTTPStatus

import testing_utilities as test_utils
from api.common.dev_config import UNIT_TEST_NAMESPACE
from api.endpoints.project import get_project_status_for_user_api, get_project_status_for_external_user_api
from testing_utilities import test_get

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'
VIEW_SQL_FOLDER = '../../local/database-view-sql/'
TEST_ENV = UNIT_TEST_NAMESPACE[1:-1]

ENTITY_BASE_URL = 'project-user-status'

PSFU_IDS = [
    "6b95e66d-1ff8-453a-88ce-ae0dc4b21df9",
    "11220597-137d-4452-888d-053f27a78355",
    "a099d03b-11e3-424c-9e97-d1c095f9823b",
    "7c18c259-ace6-4f48-9206-93cd15501348",
    "5907275b-6d75-4ec0-ada8-5854b44fb955",
    "ce36d4d9-d3d3-493f-98e4-04f4b29ccf49",
    "183c23a1-76a7-46c3-8277-501f0740939d",
    "2d03957f-ca35-4f6d-8ec6-1b05ee7d279c",
]


class ProjectTaskTestResult:

    def __init__(self, task_is_visible, user_is_signedup, signup_available, user_task_status, task_provider_name, url):
        self.task_is_visible = task_is_visible
        self.user_is_signedup = user_is_signedup
        self.signup_available = signup_available
        self.user_task_status = user_task_status
        self.task_provider_name = task_provider_name
        self.url = url


class TestProjectStatusForUser(test_utils.DbTestCase):

    def check_project_status_for_single_user_base(self, parameter_name, parameter_value, expected_results,
                                                  target_function=get_project_status_for_user_api, base_url=f'v1/{ENTITY_BASE_URL}'):
        querystring_parameters = {parameter_name: parameter_value}
        # event = {'queryStringParameters': querystring_parameters}

        expected_status = HTTPStatus.OK

        # result = get_project_status_for_user_api(event, None)
        result = test_get(target_function, base_url, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)

        # keep only results for project rows in original PSFU dataset
        result_json = [x for x in result_json if x['id'] in PSFU_IDS]

        expected_project_visiblities = expected_results['project_visibility']
        for (project_result, expected_project_is_visible) in zip(result_json, expected_project_visiblities):
            # print(querystring_parameters, expected_project_is_visible, project_result['project_is_visible'])
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
                    self.assertIsNone(task['url'])
                else:
                    # print(expected_task_result)
                    self.assertEqual(expected_task_result.task_is_visible, task['task_is_visible'], parameter_value + ":" + task_desc + ":task_is_visible")
                    self.assertEqual(expected_task_result.user_is_signedup, task['user_is_signedup'], parameter_value + ":" + task_desc + ":user_is_signedup")
                    self.assertEqual(expected_task_result.signup_available, task['signup_available'], parameter_value + ":" + task_desc + ":signup_available")
                    self.assertEqual(expected_task_result.user_task_status, task['user_task_status'], parameter_value + ":" + task_desc + ":user_task_status")
                    self.assertEqual(expected_task_result.url, task['url'], parameter_value + ":" + task_desc + ":url")
                    self.assertEqual(expected_task_result.task_provider_name, task['task_provider_name'], parameter_value + ":" + task_desc + ":task_provider_name")

    def check_project_status_for_single_user(self, user_id, expected_results):
        self.check_project_status_for_single_user_base('user_id', user_id, expected_results)

    def check_project_status_for_single_external_user(self, user_id, expected_results):
        self.check_project_status_for_single_user_base('user_id', user_id, expected_results,
                                                       target_function=get_project_status_for_external_user_api,
                                                       base_url='v2/project-user-status')

    def test_project_status_invalid_user_id(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebd'
        querystring_parameters = {'user_id': user_id}
        result = test_get(get_project_status_for_user_api, f'v1/{ENTITY_BASE_URL}', None, querystring_parameters, None)
        expected_status = HTTPStatus.BAD_REQUEST
        self.assertEqual(expected_status, result['statusCode'])

    def test_user_a_project_status(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'  # altha@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, False, True, False]
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Cochrane',
                        'http://crowd.cochrane.org/index.html?user_id='+ user_id +
                        f'&user_task_id=ceb30e82-de0f-4009-940d-778dace69ec9&external_task_id=ext-5a&env={TEST_ENV}')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-05-E'] = ProjectTaskTestResult(
            task_is_visible=False,
            user_is_signedup=False,
            signup_available=False,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=f5a0830f-136a-4661-b428-d6b334948d88&external_task_id=ext-7a&env={TEST_ENV}')
        self.check_project_status_for_single_user(user_id, expected_results)

    def test_external_user_a_project_status(self):
        """
        Same as test_user_a_project_status, but returned url is different: uses ext_user_project_id rather than user_id. Notice that because
        ext_user_project_id is project-specific, two different identifiers are used
        (one associated with project 5907275b-6d75-4ec0-ada8-5854b44fb955 (FSFU-05-A) and another with project
        183c23a1-76a7-46c3-8277-501f0740939d (FSFU-07-A)
        """
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'  # altha@email.addr
        ext_user_project_id_one = '1a03cb39-b669-44bb-a69e-98e6a521d758'  # altha@email.addr; project: 5907275b-6d75-4ec0-ada8-5854b44fb955
        ext_user_project_id_two = '2c8bba57-58a9-4ac7-98e8-beb34f0692c1'  # altha@email.addr; project: 183c23a1-76a7-46c3-8277-501f0740939d
        expected_results = dict()
        expected_results['project_visibility'] = [False, False, False, True, False, True, False]
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Cochrane',
                        f'http://crowd.cochrane.org/index.html?ext_user_project_id={ext_user_project_id_one}'
                        f'&ext_user_task_id=f7894c6b-0391-4061-8f97-89b674cb61e3&external_task_id=ext-5a&env={TEST_ENV}')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(
            task_is_visible=True, user_is_signedup=True, signup_available=False, user_task_status='complete', task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com?ext_user_project_id={ext_user_project_id_two}&ext_user_task_id=e18f7ecb-1f0f-4acb-bacc-274ac01feb76'
                f'&external_task_id=ext-7a&env={TEST_ENV}')
        self.check_project_status_for_single_external_user(user_id, expected_results)

    def test_user_b_project_status(self):
        user_id = '851f7b34-f76c-49de-a382-7e4089b744e2'  # bernie@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, False, True, False]
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=615ff0e6-0b41-4870-b9db-527345d1d9e5&external_task_id=ext-3a&env={TEST_ENV}')
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Cochrane',
                        'http://crowd.cochrane.org/index.html?user_id='+ user_id +
                        f'&user_task_id=3c7978a8-c618-4e39-9ca9-7073faafeb56&external_task_id=ext-5a&env={TEST_ENV}')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_c_project_status(self):
        user_id = '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'  # clive@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=dad64b2c-8315-4ec4-9824-5e2fdffc11e5&external_task_id=ext-3a&env={TEST_ENV}')
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=bededae9-c983-4346-a1d3-13ea5a9d0781&external_task_id=ext-4a&env={TEST_ENV}')
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-B'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=8bb74086-657e-4276-bad2-6285c6ede0fd&external_task_id=ext-5b&env={TEST_ENV}')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-06-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Cochrane',
                        'http://crowd.cochrane.org/index.html?user_id='+ user_id +
                        f'&user_task_id=d4a47805-fbec-4e43-938c-94af7214326d&external_task_id=ext-6a&env={TEST_ENV}')
        # expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Qualtrics',
                        'https://www.qualtrics.com?user_id=' + user_id +
                        f'&user_task_id=72d0a70b-5eb4-4fc6-8712-995976f8a896&external_task_id=ext-7a&env={TEST_ENV}')
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_d_project_status(self):
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'  # delia@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=cbe926a1-e502-443d-b527-774589fa875a&external_task_id=ext-4a&env={TEST_ENV}')
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-B'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-06-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Cochrane',
                        'http://crowd.cochrane.org/index.html?user_id='+ user_id +
                        f'&user_task_id=ade342a2-a1ec-49fb-ab0f-2f81357cbced&external_task_id=ext-6a&env={TEST_ENV}')
        expected_results['PSFU-06-B'] = ProjectTaskTestResult(True, True, False, 'complete', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=010d3058-d329-448a-b155-4e574e9e2e57&external_task_id=ext-6b&env={TEST_ENV}')
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-08-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Cochrane',
                        'http://crowd.cochrane.org/index.html?user_id='+ user_id +
                        f'&user_task_id=c2712f2a-6ca6-4987-888f-19625668c887&external_task_id=ext-8a&env={TEST_ENV}')
        self.check_project_status_for_single_user(user_id, expected_results)


    def test_user_e_project_status(self):
        user_id = '1cbe9aad-b29f-46b5-920e-b4c496d42515'  # eddie@email.addr
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, True, True, True]
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-06-B'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=183a6c83-1328-4aea-8c24-6d587b1ded27&external_task_id=ext-6b&env={TEST_ENV}')
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Qualtrics',
                        'https://www.qualtrics.com?user_id='+ user_id +
                        f'&user_task_id=ef012f6a-f4b6-4dff-b243-f929f9d9fabb&external_task_id=ext-7a&env={TEST_ENV}')
        expected_results['PSFU-08-A'] = ProjectTaskTestResult(True, False, False, None, 'Cochrane', None)
        self.check_project_status_for_single_user(user_id, expected_results)
