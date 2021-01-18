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
import testing_utilities as test_utils  # this should be the first import; it sets env variables
import json
from http import HTTPStatus
from thiscovery_dev_tools.testing_tools import test_get

import api.endpoints.user as u
from api.local.dev_config import UNIT_TEST_NAMESPACE
from api.endpoints.project import get_project_status_for_user_api  # , get_project_status_for_external_user_api


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
    "8f2d0ca3-11c0-408c-970c-5ffb71fc0278",
    "c140336f-4d6e-4f5e-aeaf-b4a764d649f6",
    "5072aa27-6160-4dbc-888d-6e608a4fc63b",
    "cb327169-4cfa-434d-8867-57c9add2d03d",
    "8b0c6514-d800-4157-8f75-54a7204b5762",
    "1d6b31aa-0ecf-4afd-b7b7-a41fc4f01167",
    "e55b9093-fe9d-4a8c-86be-caf2789d20df",
    "751e2e2a-1614-4e61-9350-2d7161b8010c",
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

    def check_project_status_for_single_user(self, user_id, expected_results, target_function=get_project_status_for_user_api,
                                             base_url=f'v1/{ENTITY_BASE_URL}', original_psfu_dataset_only=True, demo=None):
        querystring_parameters = {
            'user_id': user_id
        }
        if demo is not None:
            querystring_parameters.update({'demo': demo})

        expected_status = HTTPStatus.OK

        # result = get_project_status_for_user_api(event, None)
        result = test_get(target_function, base_url, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)

        # keep only results for project rows in original PSFU dataset
        if original_psfu_dataset_only:
            result_json = [x for x in result_json if x['id'] in PSFU_IDS]

        expected_project_visiblities = expected_results['project_visibility']
        for (project_result, expected_project_is_visible) in zip(result_json, expected_project_visiblities):
            try:
                self.assertEqual(expected_project_is_visible, project_result['project_is_visible'])
            except AssertionError:
                print(project_result['short_name'])
                print(querystring_parameters, expected_project_is_visible, project_result['project_is_visible'])
                raise
            for (task) in project_result['tasks']:
                task_desc = task['description']
                # print(task_desc)
                expected_task_result = expected_results.get(task_desc)
                if expected_task_result is None:
                    self.assertFalse(task['task_is_visible'])
                    self.assertFalse(task['user_is_signedup'])
                    self.assertFalse(task['signup_available'])
                    self.assertIsNone(task['user_task_status'])
                    self.assertIsNone(task['url'])
                else:
                    # print(expected_task_result)
                    self.assertEqual(expected_task_result.task_is_visible, task['task_is_visible'], user_id + ":" + task_desc + ":task_is_visible")
                    self.assertEqual(expected_task_result.user_is_signedup, task['user_is_signedup'], user_id + ":" + task_desc + ":user_is_signedup")
                    self.assertEqual(expected_task_result.signup_available, task['signup_available'], user_id + ":" + task_desc + ":signup_available")
                    self.assertEqual(expected_task_result.user_task_status, task['user_task_status'], user_id + ":" + task_desc + ":user_task_status")
                    self.assertEqual(expected_task_result.url, task['url'], user_id + ":" + task_desc + ":url")
                    self.assertEqual(expected_task_result.task_provider_name, task['task_provider_name'],
                                     user_id + ":" + task_desc + ":task_provider_name")

    def test_project_status_invalid_user_id(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebd'
        querystring_parameters = {
            'user_id': user_id
        }
        result = test_get(get_project_status_for_user_api, f'v1/{ENTITY_BASE_URL}', None, querystring_parameters, None)
        expected_status = HTTPStatus.BAD_REQUEST
        self.assertEqual(expected_status, result['statusCode'])

    def test_project_status_nonexistent_user(self):
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6dddf'
        querystring_parameters = {
            'user_id': user_id
        }
        result = test_get(get_project_status_for_user_api, f'v1/{ENTITY_BASE_URL}', None, querystring_parameters, None)
        expected_status = HTTPStatus.NOT_FOUND
        self.assertEqual(expected_status, result['statusCode'])

    def test_user_a_project_status(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'  # altha@email.addr
        first_name = 'Altha'
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, False, True, False]  # visibilities of projects 2-8; project 1 filtered out by API
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=ceb30e82-de0f-4009-940d-778dace69ec9'
                f'&external_task_id=ext-5a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=f5a0830f-136a-4661-b428-d6b334948d88'
                f'&external_task_id=ext-7a'
                f'&env={TEST_ENV}'
        )
        self.check_project_status_for_single_user(user_id, expected_results)

    def test_user_a_demo_project_status(self):
        user_id = 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'  # altha@email.addr
        first_name = 'Altha'
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, False, True, False]  # visibilities of projects 10-16; project 9 filtered out by API
        expected_results['PSFU-13-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=cbae4d7a-26d7-4bdb-aa41-0611044d7fc6'
                f'&external_task_id=ext-13a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-13-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-15-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=c5a931fb-2337-439c-8ec1-419a5e82d00d'
                f'&external_task_id=ext-15a'
                f'&env={TEST_ENV}'
        )
        self.check_project_status_for_single_user(user_id, expected_results, demo=True)

    def test_user_b_project_status(self):
        user_id = '851f7b34-f76c-49de-a382-7e4089b744e2'  # bernie@email.addr
        first_name = 'Bernard'
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, False]  # visibilities of projects 2-8; project 1 filtered out by API
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                                                              'https://www.qualtrics.com?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=615ff0e6-0b41-4870-b9db-527345d1d9e5&external_task_id=ext-3a&env={TEST_ENV}')
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Cochrane',
                                                              'http://crowd.cochrane.org/index.html?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=3c7978a8-c618-4e39-9ca9-7073faafeb56&external_task_id=ext-5a&env={TEST_ENV}')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-05-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-05-E'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-06-C'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-06-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        self.check_project_status_for_single_user(user_id, expected_results)

    def test_user_b_demo_project_status(self):
        user_id = '851f7b34-f76c-49de-a382-7e4089b744e2'  # bernie@email.addr
        first_name = 'Bernard'
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, False]  # visibilities of projects 10-16; project 9 filtered out by API
        expected_results['PSFU-11-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=d56a4a7b-ff40-40ab-8b66-f0801f3a8b38'
                f'&external_task_id=ext-11a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-12-A'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-13-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=2e550c4f-1a1f-4c9c-a642-82f0e7bf411d'
                f'&external_task_id=ext-13a'
                f'&env={TEST_ENV}')
        expected_results['PSFU-13-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-13-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-13-E'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-14-C'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-14-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-15-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        self.check_project_status_for_single_user(user_id, expected_results, demo=True)

    def test_user_c_project_status(self):
        user_id = '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'  # clive@email.addr
        first_name = 'Clive'
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]  # visibilities of projects 2-8; project 1 filtered out by API
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                                                              'https://www.qualtrics.com?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=dad64b2c-8315-4ec4-9824-5e2fdffc11e5&external_task_id=ext-3a&env={TEST_ENV}')
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                                                              'https://www.qualtrics.com?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=bededae9-c983-4346-a1d3-13ea5a9d0781&external_task_id=ext-4a&env={TEST_ENV}')
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-B'] = ProjectTaskTestResult(True, True, False, 'active', 'Qualtrics',
                                                              'https://www.qualtrics.com?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=8bb74086-657e-4276-bad2-6285c6ede0fd&external_task_id=ext-5b&env={TEST_ENV}')
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-05-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-05-E'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-06-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Cochrane',
                                                              'http://crowd.cochrane.org/index.html?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=d4a47805-fbec-4e43-938c-94af7214326d&external_task_id=ext-6a&env={TEST_ENV}')
        expected_results['PSFU-06-C'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-06-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        # expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, True, False, 'complete', 'Qualtrics',
                                                              'https://www.qualtrics.com?user_id=' + user_id + f'&first_name={first_name}' +
                                                              f'&user_task_id=72d0a70b-5eb4-4fc6-8712-995976f8a896&external_task_id=ext-7a&env={TEST_ENV}')
        self.check_project_status_for_single_user(user_id, expected_results)

    def test_user_c_demo_project_status(self):
        user_id = '8518c7ed-1df4-45e9-8dc4-d49b57ae0663'  # clive@email.addr
        first_name = 'Clive'
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]  # visibilities of projects 10-16; project 9 filtered out by API
        expected_results['PSFU-11-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=f6cb3969-a8a5-4b3f-bc70-beeb0fa35fc3'
                f'&external_task_id=ext-11a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-12-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=03bdaa5e-7954-4390-a506-549337ffd988'
                f'&external_task_id=ext-12a'
                f'&env={TEST_ENV}')
        expected_results['PSFU-13-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-13-B'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=356f09bb-6ceb-468e-af95-a4e45bd7b1fe'
                f'&external_task_id=ext-13b'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-13-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-13-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-13-E'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-14-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=18586b87-3a5a-4fa3-960d-4e2bae9bf53e'
                f'&external_task_id=ext-14a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-14-C'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-14-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-15-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=1fd03d79-bdb5-4fd3-832e-b32229ca8867'
                f'&external_task_id=ext-15a'
                f'&env={TEST_ENV}'
        )
        self.check_project_status_for_single_user(user_id, expected_results, demo=True)

    def test_user_d_project_status(self):
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'  # delia@email.addr
        first_name = 'Delia'
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]  # visibilities of projects 2-8; project 1 filtered out by API
        expected_results['PSFU-03-A'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-04-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=cbe926a1-e502-443d-b527-774589fa875a'
                f'&external_task_id=ext-4a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-B'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-05-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-05-E'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-06-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=ade342a2-a1ec-49fb-ab0f-2f81357cbced'
                f'&external_task_id=ext-6a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-06-B'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?anon_project_specific_user_id=922d2b14-554f-42b5-bd20-d024b5ac7214'
                f'&first_name={first_name}'
                f'&anon_user_task_id=993aaecf-3d6f-414f-bd44-d4c8390057c8'
                f'&project_task_id=683598e8-435f-4052-a417-f0f6d808373a'
                f'&external_task_id=ext-6b'
                f'&env={TEST_ENV}')
        expected_results['PSFU-06-C'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-06-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-08-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=c2712f2a-6ca6-4987-888f-19625668c887'
                f'&external_task_id=ext-8a'
                f'&env={TEST_ENV}'
        )
        self.check_project_status_for_single_user(user_id, expected_results)

    def test_user_d_demo_project_status(self):
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'  # delia@email.addr
        first_name = 'Delia'
        expected_results = {}
        expected_results['project_visibility'] = [False, True, True, True, True, True, True]  # visibilities of projects 10-16; project 9 filtered out by API
        expected_results['PSFU-11-A'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-12-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=a35d4f1e-f383-494c-8c55-28dc3b93e5f0'
                f'&external_task_id=ext-12a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-13-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-13-B'] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results['PSFU-13-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-13-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-13-E'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-14-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=7f693409-3fbd-4978-8b5c-977a08bd74af'
                f'&external_task_id=ext-14a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-14-B'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?anon_project_specific_user_id=8807653f-fb24-493e-a9fc-9201c114980c'
                f'&first_name={first_name}'
                f'&anon_user_task_id=b6805a9f-09fc-47d6-b13b-8331f9a9adb3'
                f'&project_task_id=8e0fb129-f6b6-4b6b-a01a-cfdb14f8fec8'
                f'&external_task_id=ext-14b'
                f'&env={TEST_ENV}')
        expected_results['PSFU-14-C'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-14-D'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=False,
            signup_available=True,
            user_task_status=None,
            task_provider_name='Qualtrics',
            url=None
        )
        expected_results['PSFU-15-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-16-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Cochrane',
            url=f'http://crowd.cochrane.org/index.html'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=9d689f8b-1db4-4685-bb32-fc229f26af52'
                f'&external_task_id=ext-16a'
                f'&env={TEST_ENV}'
        )
        self.check_project_status_for_single_user(user_id, expected_results, demo=True)

    def test_user_e_project_status(self):
        user_id = '1cbe9aad-b29f-46b5-920e-b4c496d42515'  # eddie@email.addr
        first_name = 'Eddie'
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, True, True, True]  # visibilities of projects 2-8; project 1 filtered out by API
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-06-B'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?anon_project_specific_user_id=a7a8e630-cb7e-4421-a9b2-b8bad0298267'
                f'&first_name={first_name}'
                f'&anon_user_task_id=4a7a29e8-2869-469f-a922-5e9ff5af4583'
                f'&project_task_id=683598e8-435f-4052-a417-f0f6d808373a'
                f'&external_task_id=ext-6b'
                f'&env={TEST_ENV}')
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=ef012f6a-f4b6-4dff-b243-f929f9d9fabb'
                f'&external_task_id=ext-7a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-08-A'] = ProjectTaskTestResult(True, False, False, None, 'Cochrane', None)
        self.check_project_status_for_single_user(user_id, expected_results)

    def test_user_e_demo_project_status(self):
        user_id = '1cbe9aad-b29f-46b5-920e-b4c496d42515'  # eddie@email.addr
        first_name = 'Eddie'
        expected_results = {}
        expected_results['project_visibility'] = [False, False, False, True, True, True, True]  # visibilities of projects 10-16; project 9 filtered out by API
        expected_results['PSFU-13-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-13-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-14-B'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?anon_project_specific_user_id=29aca87c-e0f9-44c2-b97e-22cbe842a908'
                f'&first_name={first_name}'
                f'&anon_user_task_id=fb92e1f0-e756-47db-ab5c-232c3618999a'
                f'&project_task_id=8e0fb129-f6b6-4b6b-a01a-cfdb14f8fec8'
                f'&external_task_id=ext-14b'
                f'&env={TEST_ENV}')
        expected_results['PSFU-15-A'] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='complete',
            task_provider_name='Qualtrics',
            url=f'https://www.qualtrics.com'
                f'?user_id={user_id}'
                f'&first_name={first_name}'
                f'&user_task_id=2edf9b93-8bc3-4b07-8e81-535592253598'
                f'&external_task_id=ext-15a'
                f'&env={TEST_ENV}'
        )
        expected_results['PSFU-16-A'] = ProjectTaskTestResult(True, False, False, None, 'Cochrane', None)
        self.check_project_status_for_single_user(user_id, expected_results, demo=True)

    def test_user_g_project_status(self):
        user_id = 'e067ed7b-bc98-454f-9c5e-573e2da5705c'  # glenda
        first_name = 'Glenda'
        expected_results = {}
        expected_results['project_visibility'] = [True, False, False, False, True, False, True, False]  # visibilities of projects 9, 2-8; project 1 filtered out by API
        expected_results["Systematic review for CTG monitoring"] = ProjectTaskTestResult(True, False, False, None, 'Cochrane', None)
        expected_results["Midwife assessment for CTG monitoring"] = ProjectTaskTestResult(True, False, True, None, 'Qualtrics', None)
        expected_results["Patient interviews"] = ProjectTaskTestResult(
            task_is_visible=True,
            user_is_signedup=True,
            signup_available=False,
            user_task_status='active',
            task_provider_name='Qualtrics',
            url=f"https://www.qualtrics.com"
                f"?anon_project_specific_user_id=cc694281-91a1-4bad-b46f-9b69e71503bb"
                f"&first_name={first_name}"
                f"&anon_user_task_id=3dfa1080-9b00-401a-a620-30273046b29e"
                f"&project_task_id=387166e6-99fd-4c98-84a5-3908f942dcb3"
                f"&external_task_id=5678"
                f"&last_name=Gupta"
                f"&email=glenda@email.co.uk"
                f"&env={TEST_ENV}")
        expected_results['PSFU-05-A'] = ProjectTaskTestResult(True, False, True, None, 'Cochrane', None)
        expected_results['PSFU-05-C'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        expected_results['PSFU-07-A'] = ProjectTaskTestResult(True, False, False, None, 'Qualtrics', None)
        self.check_project_status_for_single_user(user_id, expected_results, original_psfu_dataset_only=False)


class TestGetProjectStatusForUserFunction(test_utils.DbTestCase):
    user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = u.get_user_by_id(cls.user_id)[0]

    def test_user_specific_task_url_ok(self):
        result = test_get(
            get_project_status_for_user_api,
            f'v1/{ENTITY_BASE_URL}',
            querystring_parameters={
                'user_id': self.user_id
            }
        )
        expected_status = HTTPStatus.OK
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)
        result_json = json.loads(result['body'])
        expected_task_results = {
            '4ee70544-6797-4e21-8cec-5653c8d5b234': {
                'url': f'www.specific-user-task.co.uk'
                       f'?anon_project_specific_user_id=e132c198-06d3-4200-a6c0-cc3bc7991828'
                       f'&first_name={self.user["first_name"]}'
                       f'&anon_user_task_id=47e98896-33b4-4401-b667-da95db9122a2'
                       f'&project_task_id=4ee70544-6797-4e21-8cec-5653c8d5b234'
                       f'&external_task_id=5678'
                       f'&env={TEST_ENV}',
            }
        }
        for project in result_json:
            for task in project['tasks']:
                expected_fields = expected_task_results.get(task['id'])
                if expected_fields:
                    for k, v in expected_fields.items():
                        self.assertEqual(v, task[k])
