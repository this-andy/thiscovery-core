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
from pprint import pprint

import api.endpoints.notification_process as np
import api.endpoints.user_task as ut
import thiscovery_dev_tools.testing_tools as test_tools

from thiscovery_lib.dynamodb_utilities import Dynamodb
from api.local.dev_config import UNIT_TEST_NAMESPACE
from api.endpoints.common.hubspot import HubSpotClient, TASK_SIGNUP_TLE_TYPE_NAME
from api.endpoints.common.notifications import get_notifications, NotificationStatus, NotificationType, \
    NotificationAttributes
from api.endpoints.user import create_user_api
from api.endpoints.user_task import list_user_tasks_api, create_user_task_api
from api.endpoints.user_project import list_user_projects_api
from thiscovery_dev_tools.testing_tools import test_get, test_post

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
        "anon_user_task_id": "e63ebc2e-5c75-445a-892f-9bf7b1a58c8d",
        "task_provider_name": "Qualtrics",
        "url": f"https://www.qualtrics.com"
               f"?user_id=851f7b34-f76c-49de-a382-7e4089b744e2"
               f"&first_name=Bernard"
               f"&user_task_id=615ff0e6-0b41-4870-b9db-527345d1d9e5"
               f"&external_task_id=ext-3a"
               f"&env={TEST_ENV}",
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
        "anon_user_task_id": "935eb145-9f20-47b0-9efa-2d73ebb3fd6a",
        "task_provider_name": "Cochrane",
        "url": f"http://crowd.cochrane.org/index.html"
               f"?user_id=851f7b34-f76c-49de-a382-7e4089b744e2"
               f"&first_name=Bernard"
               f"&user_task_id=3c7978a8-c618-4e39-9ca9-7073faafeb56"
               f"&external_task_id=ext-5a"
               f"&env={TEST_ENV}",
}
# endregion


class TestUserTask(test_utils.DbTestCase):
    delete_notifications = True
    maxDiff = None

    def test_01_list_user_tasks_api_ok(self):
        expected_status = HTTPStatus.OK
        expected_body = [USER_TASK_01_EXPECTED_BODY, USER_TASK_02_EXPECTED_BODY]
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}

        result = test_get(list_user_tasks_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        for actual, expected in zip(result_json, expected_body):
            self.assertDictEqual(expected, actual)

    def test_02_list_user_tasks_api_ok_with_project_task_id(self):
        expected_status = HTTPStatus.OK
        # expected_body = [USER_TASK_02_EXPECTED_BODY]
        expected_body = USER_TASK_02_EXPECTED_BODY
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'project_task_id': '6cf2f34e-e73f-40b1-99a1-d06c1f24381a'}

        result = test_get(list_user_tasks_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(expected_body, result_json)
        # for actual, expected in zip(result_json, expected_body):
        #     self.assertDictEqual(expected, actual)

    def test_03_list_user_tasks_api_project_task_not_exists(self):
        expected_status = HTTPStatus.OK
        expected_body = list()
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2', 'project_task_id': 'aa5092b1-b098-42d7-8c62-21493dfe37f3'}

        result = test_get(list_user_tasks_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_body, result_json)

    def test_04_list_user_tasks_api_user_not_exists(self):
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

    def test_05_list_user_tasks_api_no_results(self):
        expected_status = HTTPStatus.OK
        expected_body = []

        querystring_parameters = {'user_id': 'dceac123-03a7-4e29-ab5a-739e347b374d'}

        result = test_get(list_user_projects_api, ENTITY_BASE_URL, None, querystring_parameters, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(expected_body, result_json)

    def test_06_create_user_task_api_ok_and_duplicate(self):
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
            'anon_user_task_id': '78a1ccd7-dee5-49b2-ad5c-8bf4afb3cf93',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01',
            'id': ut_id,
            'created': '2018-06-13 14:15:16.171819+00'
        }
        body = json.dumps(ut_json)

        self.logger.debug('Creating user task for the first time')
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
        expected_url = f'http://crowd.cochrane.org/index.html' \
                       f'?user_id={user_id}' \
                       f'&first_name={user_json["first_name"]}' \
                       f'&user_task_id={ut_id}' \
                       f'&external_task_id=ext-5a' \
                       f'&env={TEST_ENV}'
        self.assertEqual(expected_url, url)

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
        tle_type_id = hs_client.get_timeline_event_type_id(TASK_SIGNUP_TLE_TYPE_NAME, correlation_id=None)
        result = hs_client.get_timeline_event(tle_type_id, ut_id)
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

        self.logger.debug('Attempting to create user task for the second time')
        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertTrue('correlation_id' in result_json)
        self.assertTrue(
            ('message' in result_json) and
            ('already exists' in result_json['message'])
        )

    def test_07_create_user_task_api_with_defaults(self):
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
        anon_user_task_id = self.uuid_test_and_remove(result_json, 'anon_user_task_id')
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
        expected_url = f'https://www.qualtrics.com' \
                       f'?anon_project_specific_user_id=7e6e4bca-4f0b-4f71-8660-790c1baf3b11' \
                       f'&first_name=Clive' \
                       f'&anon_user_task_id={anon_user_task_id}' \
                       f'&project_task_id=683598e8-435f-4052-a417-f0f6d808373a' \
                       f'&external_task_id=ext-6b' \
                       f'&env={TEST_ENV}'
        self.assertEqual(expected_url, url)

        self.assertEqual('active', status)
        self.assertEqual('ddf0750a-758e-47de-aef3-055d0af41d3d', user_project_id)

    def test_08_create_user_task_api_invalid_status(self):
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

    def test_09_create_user_task_api_task_not_exists(self):
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

    def test_10_create_user_task_api_task_missing_params(self):
        expected_status = HTTPStatus.BAD_REQUEST
        ut_json = {
            'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'
        }
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])
        pprint(result_json)
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

    def test_11_set_user_task_status_to_complete_ok(self):
        expected_status = HTTPStatus.NO_CONTENT
        querystring_parameters = {
            "user_task_id": "615ff0e6-0b41-4870-b9db-527345d1d9e5"
        }
        result = test_tools.test_put(ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

        updated_ut = ut.get_user_task(querystring_parameters['user_task_id'])[0]
        self.assertEqual('complete', updated_ut['status'])
        self.now_datetime_test_and_remove(updated_ut, 'modified')

    def test_12_set_user_task_status_to_complete_ut_non_existent(self):
        expected_status = HTTPStatus.NOT_FOUND
        querystring_parameters = {
            "user_task_id": "144b1536-ce5c-4def-bd30-05a361976a90"
        }
        result = test_tools.test_put(ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

    def test_13_set_user_task_status_to_complete_ut_id_not_passed(self):
        expected_status = HTTPStatus.BAD_REQUEST
        querystring_parameters = {
            "invalid_parameter": "615ff0e6-0b41-4870-b9db-527345d1d9e5"
        }
        result = test_tools.test_put(ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

    def test_14_set_user_task_status_to_complete_anon_ut_id_ok(self):
        expected_status = HTTPStatus.NO_CONTENT
        querystring_parameters = {
            "anon_user_task_id": "00a461f3-7a28-4ed3-940c-c977f55654e3"  # ut_id dad64b2c-8315-4ec4-9824-5e2fdffc11e5
        }
        result = test_tools.test_put(ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

        updated_ut = ut.get_user_task('dad64b2c-8315-4ec4-9824-5e2fdffc11e5')[0]
        self.assertEqual('complete', updated_ut['status'])
        self.now_datetime_test_and_remove(updated_ut, 'modified')

    def test_15_set_user_task_status_to_complete_anon_ut_non_existent(self):
        expected_status = HTTPStatus.NOT_FOUND
        querystring_parameters = {
            "anon_user_task_id": "144b1536-ce5c-4def-bd30-05a361976a90"
        }
        result = test_tools.test_put(ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

    def test_16_set_user_task_status_to_complete_fail_both_ids_passed(self):
        expected_status = HTTPStatus.BAD_REQUEST
        querystring_parameters = {
            "user_task_id": "615ff0e6-0b41-4870-b9db-527345d1d9e5",
            "anon_user_task_id": "e63ebc2e-5c75-445a-892f-9bf7b1a58c8d",
        }
        result = test_tools.test_put(ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)


class TestUserTaskSpecificUrl(test_utils.DbTestCase):
    delete_notifications = True
    maxDiff = None
    base_user_specific_url = "https://test.user.specific.url.com/jfe/form/SV_25DkdHUUWqrSrSB?Q_DL=3eVFs4Y9PkNlUoq_25&Q_CHL=gl"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb = Dynamodb()
        cls.add_test_specific_urls_to_ddb()

    @classmethod
    def add_test_specific_urls_to_ddb(cls):
        project_task_id = '4ee70544-6797-4e21-8cec-5653c8d5b234'  # user_specific_url = True
        user_ids = [
            "8518c7ed-1df4-45e9-8dc4-d49b57ae0663",
        ]
        for user_id in user_ids:
            cls.ddb.put_item(
                table_name="UserSpecificUrls",
                key=f"{project_task_id}_{user_id}",
                item_type='user_specific_url',
                item_details=None,
                item={
                    'user_id': user_id,
                    'project_task_id': project_task_id,
                    'user_specific_url': cls.base_user_specific_url,
                    'details_provenance': 'unittest suite',
                    'status': 'new',
                },
                update_allowed=True,
            )

    def test_14_create_user_task_api_ok_with_specific_url(self):
        user_id = "8518c7ed-1df4-45e9-8dc4-d49b57ae0663"
        ut_json = {
            'user_id': user_id,
            'project_task_id': '4ee70544-6797-4e21-8cec-5653c8d5b234',
            'consented': '2018-07-19 16:16:56.087895+01',
            'anon_user_task_id': '6fc8cf2d-78d2-4c51-be16-e41e4235fcc9',
        }

        expected_status = HTTPStatus.CREATED
        body = json.dumps(ut_json)

        result = test_post(create_user_task_api, ENTITY_BASE_URL, None, body, None)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)

        result_json = json.loads(result['body'])
        url = result_json['url']
        expected_url = f'{self.base_user_specific_url}' \
                       f'&anon_project_specific_user_id=87b8f9a8-2400-4259-a8d9-a2f0b16d9ea1' \
                       f'&first_name=Clive' \
                       f'&anon_user_task_id=6fc8cf2d-78d2-4c51-be16-e41e4235fcc9' \
                       f'&project_task_id=4ee70544-6797-4e21-8cec-5653c8d5b234' \
                       f'&external_task_id=5678' \
                       f'&env={TEST_ENV}'
        self.assertEqual(expected_url, url)

    def test_15_clear_user_tasks_for_project_task_id_ok(self):
        project_task_id = "f60d5204-57c1-437f-a085-1943ad9d174f"
        deleted_row_count = ut.clear_user_tasks_for_project_task_id(project_task_id)
        self.assertEqual(2, deleted_row_count)
