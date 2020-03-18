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

import api.endpoints.notification_process as np

import testing_utilities as test_utils
from api.common.dev_config import UNIT_TEST_NAMESPACE
from api.common.hubspot import HubSpotClient, TASK_SIGNUP_TLE_TYPE_NAME
from api.common.notifications import get_notifications, NotificationStatus, NotificationType, \
    NotificationAttributes
from api.endpoints.user import create_user_api
from api.endpoints.user_task import list_user_tasks_api, create_user_task_api
from api.endpoints.user_project import list_user_projects_api
from testing_utilities import test_get, test_post

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'

ENTITY_BASE_URL = 'v1/usertask'
USER_BASE_URL = 'v1/user'
TEST_ENV = UNIT_TEST_NAMESPACE[1:-1]

# region expected bodies setup
USER_TASK_01_EXPECTED_BODY = {
        "user_id": "851f7b34-f76c-49de-a382-7e4089b744e2",
        "user_project_id": "000aa7fd-759b-4a8e-9fa8-f2457108e16f",
        "user_project_status": None,
        "project_task_id": "07af2fbe-5cd1-447f-bae1-3a2f8de82829",
        "task_description": "PSFU-03-A",
        "user_task_id": "615ff0e6-0b41-4870-b9db-527345d1d9e5",
        "created": f"2018-11-06T12:48:46.46246+00:00",
        "modified": f"2018-11-06T12:48:46.462483+00:00",
        "status": "active",
        "consented": f"2018-11-06T12:48:40+00:00",
        "progress_info": None,
}

USER_TASK_02_EXPECTED_BODY = {
        "user_id": "851f7b34-f76c-49de-a382-7e4089b744e2",
        "user_project_id": "53320854-72f1-491a-b562-d84c252f4252",
        "user_project_status": None,
        "project_task_id": "6cf2f34e-e73f-40b1-99a1-d06c1f24381a",
        "task_description": "PSFU-05-A",
        "user_task_id": "3c7978a8-c618-4e39-9ca9-7073faafeb56",
        "created": f"2018-11-06T13:02:04.793202+00:00",
        "modified": f"2018-11-06T13:02:04.793225+00:00",
        "status": "complete",
        "consented": f"2018-11-06T13:02:02+00:00",
        "progress_info": None,
}
# endregion


class TestUserTask(test_utils.DbTestCase):
    delete_notifications = True

    def test_1_list_user_tasks_api_ok(self):
        expected_status = HTTPStatus.OK
        expected_body = [USER_TASK_01_EXPECTED_BODY, USER_TASK_02_EXPECTED_BODY]
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

        querystring_parameters = {'user_id': 'dceac123-03a7-4e29-ab5a-739e347b374d'}

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
            'project_task_id': '6cf2f34e-e73f-40b1-99a1-d06c1f24381a',
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
                         f'&external_task_id=ext-5a&env={TEST_ENV}', url)

        # check that notification message exists
        notifications = get_notifications('type', [NotificationType.TASK_SIGNUP.value])
        notification = notifications[0]  # should be only one
        self.assertEqual(ut_id, notification['id'])
        self.assertEqual(NotificationType.TASK_SIGNUP.value, notification['type'])
        # self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])

        # process notification
        np.process_notifications(event=None, context=None)

        # check user now has sign-up timeline event
        hs_client = HubSpotClient()
        # sleep(10)
        tle_type_id = hs_client.get_timeline_event_type_id(TASK_SIGNUP_TLE_TYPE_NAME, None)
        result = hs_client.get_timeline_event(tle_type_id, ut_id, None)
        self.assertEqual(ut_id, result['id'])
        notification_details = notification['details']
        self.assertEqual(notification_details['project_task_id'], result['task_id'])
        self.assertEqual('CONTACT', result['objectType'])
        self.assertEqual('PSFU-05-pub-act', result['project_name'])

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
        user_id = "8518c7ed-1df4-45e9-8dc4-d49b57ae0663"
        ut_json = {
            'user_id': user_id,
            'project_task_id': '683598e8-435f-4052-a417-f0f6d808373a',
            'consented': '2018-07-19 16:16:56.087895+01'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # now remove from returned object those that weren't in input json and test separately
        ut_id = self.new_uuid_test_and_remove(result_json)
        self.uuid_test_and_remove(result_json, 'ext_user_task_id')
        self.now_datetime_test_and_remove(result_json, 'created')
        self.now_datetime_test_and_remove(result_json, 'modified')

        status = result_json['status']
        del result_json['status']

        task_provider_name = result_json['task_provider_name']
        del result_json['task_provider_name']

        url = result_json['url']
        del result_json['url']

        user_project_id = result_json['user_project_id']
        del result_json['user_project_id']

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(ut_json, result_json)

        # now check individual data items
        self.assertEqual('Qualtrics', task_provider_name)
        self.assertEqual(f'https://www.qualtrics.com?user_id={user_id}&user_task_id={ut_id}'
                         f'&external_task_id=ext-6b&env={TEST_ENV}', url)

        self.assertEqual('active', status)
        self.assertEqual('ddf0750a-758e-47de-aef3-055d0af41d3d', user_project_id)

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
