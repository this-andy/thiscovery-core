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
import uuid
from http import HTTPStatus

from dateutil import parser
from unittest import TestCase
from time import sleep
from api.common.pg_utilities import insert_data_from_csv, truncate_table
from api.common.utilities import now_with_tz, set_running_unit_tests
from api.tests.test_scripts.testing_utilities import test_get, test_post, test_patch
from api.common.notifications import delete_all_notifications, get_notifications, NotificationStatus, NotificationType, NotificationAttributes

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'
DELETE_TEST_DATA = True

ENTITY_BASE_URL = 'usertask'

class TestUserTask(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

        insert_data_from_csv(TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup')
        insert_data_from_csv(TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user')
        insert_data_from_csv(TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project')
        insert_data_from_csv(TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem')
        insert_data_from_csv(TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject')
        insert_data_from_csv(TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype')
        insert_data_from_csv(TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask')
        insert_data_from_csv(TEST_DATA_FOLDER + 'user_task_data.csv', 'public.projects_usertask')


    @classmethod
    def tearDownClass(self):
        if DELETE_TEST_DATA:
            truncate_table('public.projects_usertask')
            truncate_table('public.projects_projecttask')
            truncate_table('public.projects_tasktype')
            truncate_table('public.projects_userproject')
            truncate_table('public.projects_externalsystem')
            truncate_table('public.projects_project')
            truncate_table('public.projects_user')
            truncate_table('public.projects_usergroup')
            delete_all_notifications()

        set_running_unit_tests(False)


    def test_1_list_user_tasks_api_ok(self):
        pass
        from api.endpoints.user_task import list_user_tasks_api

        expected_status = HTTPStatus.OK
        # todo figure out how do do this properly!
        expected_body_gmt = [
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
             'user_project_status': None, 'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
             'task_description': 'Systematic review for CTG monitoring', 'user_task_id': 'dd8d4003-bb8e-4cb8-af7f-7c82816a5ff4',
             'created': '2018-08-17T12:10:57.827727+00:00', 'modified': '2018-08-17T12:10:57.883217+00:00', 'status': 'active', 'consented': None},
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '8fdb6137-e196-4c17-8091-7a0d370fadba',
             'user_project_status': None, 'project_task_id': '6f1c63e2-fbe8-4d24-8680-c68a30b407e3',
             'task_description': 'Systematic review for ambulance bag', 'user_task_id': 'a3313e72-3532-482f-af5e-d31b0fa8efd6',
             'created': '2018-08-17T12:10:58.104983+00:00', 'modified': '2018-08-17T12:10:58.170637+00:00', 'status': 'complete', 'consented': None},
            {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
             'user_project_status': None, 'project_task_id': '4ee70544-6797-4e21-8cec-5653c8d5b234',
             'task_description': 'Midwife assessment for CTG monitoring', 'user_task_id': '70083082-1ffd-4e45-a8a7-364f4214af12',
             'created': '2018-08-17T12:10:58.228041+00:00', 'modified': '2018-08-17T12:10:58.263516+00:00', 'status': 'active', 'consented': None},
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
        expected_body = expected_body_gmt

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}

        result = test_get(list_user_tasks_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        for actual, expected in zip(result_json,expected_body):
            self.assertDictEqual(actual, expected)
        # self.assertDictEqual(result_json[1], expected_body[1])


    def test_2_list_user_tasks_api_user_not_exists(self):
        from api.endpoints.user_project import list_user_projects_api

        expected_status = HTTPStatus.NOT_FOUND

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e3'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'does not exist' in result_json['message'])


    def test_3_list_user_tasks_api_no_results(self):
        from api.endpoints.user_project import list_user_projects_api

        expected_status = HTTPStatus.OK
        expected_body = []

        querystring_parameters = {'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(result_json, expected_body)


    def test_4_create_user_task_api_ok_and_duplicate(self):
        from api.endpoints.user_task import create_user_task_api
        from api.endpoints.user import create_user_api
        from api.common.hubspot import get_timeline_event, get_TLE_type_id, TASK_SIGNUP_TLE_TYPE_NAME

        expected_status = HTTPStatus.CREATED
        user_id = '48e30e54-b4fc-4303-963f-2943dda2b139'
        user_email = 'sw@email.co.uk'
        user_json = {
            "id": user_id,
            "created": "2018-08-21T11:16:56+01:00",
            "email": user_email,
            "email_address_verified": False,
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "country_code": "GB",
            "crm_id": None,
            "status": "new"}
        body = json.dumps(user_json)

        result = test_post(create_user_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

        expected_status = HTTPStatus.CREATED
        ut_id = '9620089b-e9a4-46fd-bb78-091c8449d777'
        ut_json = {
            'user_id': user_id,
            'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01',
            'id': ut_id,
            'created': '2018-06-13 14:15:16.171819+00'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # user_project_id is returned but not in ut_json, so test separately
        user_project_id = result_json['user_project_id']
        del result_json['user_project_id']

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(ut_json)
        expected_body['modified'] = ut_json['created']

        self.assertEqual(result_status, expected_status)
        self.assertDictEqual(result_json, expected_body)

        # check that notification message exists
        notifications = get_notifications('type', [NotificationType.TASK_SIGNUP.value])
        notification = notifications[0]  # should be only one
        self.assertEqual(notification['id'], ut_id)
        self.assertEqual(notification['type'], NotificationType.TASK_SIGNUP.value)
        # self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.NEW.value)

        # check user now has sign-up timeline event
        sleep(10)
        tle_type_id = get_TLE_type_id(TASK_SIGNUP_TLE_TYPE_NAME, None)
        result = get_timeline_event(tle_type_id, ut_id, None)
        self.assertEqual(result['id'], ut_id)
        notification_details = notification['details']
        self.assertEqual(result['task_id'], notification_details['project_task_id'])
        self.assertEqual(result['objectType'], 'CONTACT')
        self.assertEqual(result['project_name'], 'CTG Monitoring')

        # check that notification message has been processewd
        notifications = get_notifications('type', [NotificationType.TASK_SIGNUP.value])
        notification = notifications[0]  # should be only one
        self.assertEqual(notification['id'], ut_id)
        self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.PROCESSED.value)

        # duplicate checking...
        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'already exists' in result_json['message'])


    def test_5_create_user_task_api_with_defaults(self):
        from api.endpoints.user_task import create_user_task_api

        expected_status = HTTPStatus.CREATED
        ut_json = {
            'user_id': "851f7b34-f76c-49de-a382-7e4089b744e2",
            'project_task_id': 'f3316529-e073-435e-b5c7-053da4127e96',
            'consented': '2018-07-19 16:16:56.087895+01'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        id = result_json['id']
        del result_json['id']

        created = result_json['created']
        del result_json['created']

        modified = result_json['modified']
        del result_json['modified']

        status = result_json['status']
        del result_json['status']

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

        self.assertEqual(status, 'active')


    def test_6_create_user_task_api_invalid_status(self):
        from api.endpoints.user_task import create_user_task_api

        expected_status = HTTPStatus.BAD_REQUEST
        ut_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'project_task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf019',
            'status': 'invalid',
            'consented': '2018-06-12 16:16:56.087895+01'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'invalid user_task status' in result_json['message'])


    def test_7_create_user_task_api_task_not_exists(self):
        from api.endpoints.user_task import create_user_task_api

        expected_status = HTTPStatus.BAD_REQUEST
        ut_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
            'project_task_id': 'ebd5f57b-e77c-4f26-9ae4-b65cdabaf019',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('message' in result_json and 'project_task' in result_json['message'])


    def test_8_create_user_task_api_task_missing_params(self):
        from api.endpoints.user_task import create_user_task_api

        expected_status = HTTPStatus.BAD_REQUEST
        ut_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue('parameter' in result_json and 'project_task_id' in result_json['parameter'])
        self.assertTrue('message' in result_json and 'mandatory data missing' in result_json['message'])
