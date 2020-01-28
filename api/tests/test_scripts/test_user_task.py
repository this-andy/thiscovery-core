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
from api.common.dev_config import TIMEZONE_IS_BST, UNIT_TEST_NAMESPACE
from api.common.hubspot import HubSpotClient, TASK_SIGNUP_TLE_TYPE_NAME
from api.common.notifications import delete_all_notifications, get_notifications, NotificationStatus, NotificationType, \
    NotificationAttributes
from api.common.pg_utilities import insert_data_from_csv_multiple, truncate_table_multiple
from api.common.utilities import now_with_tz, set_running_unit_tests
from api.endpoints.user import create_user_api
from api.endpoints.user_task import list_user_tasks_api, create_user_task_api
from api.endpoints.user_project import list_user_projects_api
from api.tests.test_scripts.testing_utilities import test_get, test_post, test_patch


TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'
DELETE_TEST_DATA = True

ENTITY_BASE_URL = 'v1/usertask'
USER_BASE_URL = 'v1/user'
TEST_ENV = UNIT_TEST_NAMESPACE[1:-1]

# region expected bodies setup
if TIMEZONE_IS_BST:
    tz_hour = "13"
    tz_offset = "01:00"
else:
    tz_hour = "12"
    tz_offset = "00:00"

USER_TASK_01_EXPECTED_BODY = {
    'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
    'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
    'user_project_status': None,
    'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
    'task_description': 'Systematic review for CTG monitoring',
    'user_task_id': 'dd8d4003-bb8e-4cb8-af7f-7c82816a5ff4',
    'created': f'2018-08-17T{tz_hour}:10:57.827727+{tz_offset}',
    'modified': f'2018-08-17T{tz_hour}:10:57.883217+{tz_offset}',
    'status': 'active',
    'consented': None,
    'progress_info': None,
}

USER_TASK_02_EXPECTED_BODY = {
    'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
    'user_project_id': '8fdb6137-e196-4c17-8091-7a0d370fadba',
    'user_project_status': None,
    'project_task_id': '6f1c63e2-fbe8-4d24-8680-c68a30b407e3',
    'task_description': 'Systematic review for ambulance bag',
    'user_task_id': 'a3313e72-3532-482f-af5e-d31b0fa8efd6',
    'created': f'2018-08-17T{tz_hour}:10:58.104983+{tz_offset}',
    'modified': f'2018-08-17T{tz_hour}:10:58.170637+{tz_offset}',
    'status': 'complete',
    'consented': None,
    'progress_info': None,
}

USER_TASK_03_EXPECTED_BODY = {
    'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2',
    'user_project_id': '3fd54ed7-d25c-40ba-9005-4c4da1321748',
    'user_project_status': None,
    'project_task_id': '4ee70544-6797-4e21-8cec-5653c8d5b234',
    'task_description': 'Midwife assessment for CTG monitoring',
    'user_task_id': '70083082-1ffd-4e45-a8a7-364f4214af12',
    'created': f'2018-08-17T{tz_hour}:10:58.228041+{tz_offset}',
    'modified': f'2018-08-17T{tz_hour}:10:58.263516+{tz_offset}',
    'status': 'active',
    'consented': None,
    'progress_info': None,
}
# endregion


def clear_database():
    truncate_table_multiple(
        'public.projects_usertask',
        'public.projects_projecttask',
        'public.projects_tasktype',
        'public.projects_userproject',
        'public.projects_externalsystem',
        'public.projects_project',
        'public.projects_user',
        'public.projects_usergroup',
    )
    delete_all_notifications()


class TestUserTask(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        clear_database()

        insert_data_from_csv_multiple(
            (TEST_DATA_FOLDER + 'usergroup_data.csv', 'public.projects_usergroup'),
            (TEST_DATA_FOLDER + 'user_data.csv', 'public.projects_user'),
            (TEST_DATA_FOLDER + 'project_data.csv', 'public.projects_project'),
            (TEST_DATA_FOLDER + 'external_system_data.csv', 'public.projects_externalsystem'),
            (TEST_DATA_FOLDER + 'user_project_data.csv', 'public.projects_userproject'),
            (TEST_DATA_FOLDER + 'tasktype_data.csv', 'public.projects_tasktype'),
            (TEST_DATA_FOLDER + 'projecttask_data.csv', 'public.projects_projecttask'),
            (TEST_DATA_FOLDER + 'user_task_data.csv', 'public.projects_usertask'),
        )

    @classmethod
    def tearDownClass(self):
        if DELETE_TEST_DATA:
            clear_database()

        set_running_unit_tests(False)

    def test_1_list_user_tasks_api_ok(self):
        expected_status = HTTPStatus.OK
        expected_body = [USER_TASK_01_EXPECTED_BODY, USER_TASK_02_EXPECTED_BODY, USER_TASK_03_EXPECTED_BODY]
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}

        result = test_get(list_user_tasks_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        for actual, expected in zip(result_json, expected_body):
            self.assertDictEqual(expected, actual)
        # self.assertDictEqual(expected_body[1], result_json[1])

    def test_2_list_user_tasks_api_user_not_exists(self):
        expected_status = HTTPStatus.NOT_FOUND

        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e3'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('does not exist' in result_json['message'])
        )

    def test_3_list_user_tasks_api_no_results(self):
        expected_status = HTTPStatus.OK
        expected_body = []

        querystring_parameters = {'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_body, result_json)

    def test_4_create_user_task_api_ok_and_duplicate(self):
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

        result = test_post(create_user_api, USER_BASE_URL, None, body, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

        expected_status = HTTPStatus.CREATED
        ut_id = '9620089b-e9a4-46fd-bb78-091c8449d777'
        ut_json = {
            'user_id': user_id,
            'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
            'ext_user_task_id': '78a1ccd7-dee5-49b2-ad5c-8bf4afb3cf93',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01',
            'id': ut_id,
            'created': '2018-06-13 14:15:16.171819+00'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # these properties are returned but not in ut_json, so test separately
        user_project_id = result_json['user_project_id']
        del result_json['user_project_id']
        task_provider_name = result_json['task_provider_name']
        del result_json['task_provider_name']
        url = result_json['url']
        del result_json['url']

        # modified is not part of body supplied but is returned
        expected_body = dict.copy(ut_json)
        expected_body['modified'] = ut_json['created']

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body, result_json)

        self.assertEqual('Cochrane', task_provider_name)
        self.assertEqual(f'http://crowd.cochrane.org/index.html?user_id={user_id}&user_task_id={ut_id}'
                         f'&external_task_id=1234&env={TEST_ENV}', url)

        # check that notification message exists
        notifications = get_notifications('type', [NotificationType.TASK_SIGNUP.value])
        notification = notifications[0]  # should be only one
        self.assertEqual(ut_id, notification['id'])
        self.assertEqual(NotificationType.TASK_SIGNUP.value, notification['type'])
        # self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])

        # check user now has sign-up timeline event
        hs_client = HubSpotClient()
        sleep(10)
        tle_type_id = hs_client.get_timeline_event_type_id(TASK_SIGNUP_TLE_TYPE_NAME, None)
        result = hs_client.get_timeline_event(tle_type_id, ut_id, None)
        self.assertEqual(ut_id, result['id'])
        notification_details = notification['details']
        self.assertEqual(notification_details['project_task_id'], result['task_id'])
        self.assertEqual('CONTACT', result['objectType'])
        self.assertEqual('CTG Monitoring', result['project_name'])

        # check that notification message has been processewd
        notifications = get_notifications('type', [NotificationType.TASK_SIGNUP.value])
        notification = notifications[0]  # should be only one
        self.assertEqual(ut_id, notification['id'])
        self.assertEqual(NotificationStatus.PROCESSED.value, notification[NotificationAttributes.STATUS.value])

        # duplicate checking...
        # now check we can't insert same record again...
        expected_status = HTTPStatus.CONFLICT

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('already exists' in result_json['message'])
        )

    def test_5_create_user_task_api_with_defaults(self):
        expected_status = HTTPStatus.CREATED
        user_id = "851f7b34-f76c-49de-a382-7e4089b744e2"
        ut_json = {
            'user_id': user_id,
            'project_task_id': 'f3316529-e073-435e-b5c7-053da4127e96',
            'consented': '2018-07-19 16:16:56.087895+01'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        ut_id = result_json['id']
        del result_json['id']

        created = result_json['created']
        del result_json['created']

        modified = result_json['modified']
        del result_json['modified']

        status = result_json['status']
        del result_json['status']

        task_provider_name = result_json['task_provider_name']
        del result_json['task_provider_name']

        url = result_json['url']
        del result_json['url']

        user_project_id = result_json['user_project_id']
        del result_json['user_project_id']

        ext_user_task_id = result_json['ext_user_task_id']
        del result_json['ext_user_task_id']

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(ut_json, result_json)

        # now check individual data items
        self.assertTrue(uuid.UUID(ut_id).version == 4)
        self.assertTrue(uuid.UUID(ext_user_task_id).version == 4)
        self.assertEqual('Qualtrics', task_provider_name)
        self.assertEqual(f'https://www.qualtrics.com?user_id={user_id}&user_task_id={ut_id}'
                         f'&external_task_id=8e368360-a708-4336-8feb-a8903fde0210&env={TEST_ENV}', url)

        result_datetime = parser.parse(created)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, 10)

        result_datetime = parser.parse(modified)
        difference = abs(now_with_tz() - result_datetime)
        self.assertLess(difference.seconds, 10)

        self.assertEqual('active', status)
        self.assertEqual('8fdb6137-e196-4c17-8091-7a0d370fadba', user_project_id)

    def test_6_create_user_task_api_invalid_status(self):
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
        self.assertTrue(
            ('message' in result_json) and
            ('invalid user_task status' in result_json['message'])
        )

    def test_7_create_user_task_api_task_not_exists(self):
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
        self.assertTrue(
            ('message' in result_json) and
            ('project_task' in result_json['message'])
        )

    def test_8_create_user_task_api_task_missing_params(self):
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
        self.assertTrue(
            ('parameter' in result_json) and
            ('project_task_id' in result_json['parameter'])
        )
        self.assertTrue(
            ('message' in result_json) and
            ('mandatory data missing' in result_json['message'])
        )
