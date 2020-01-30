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
import os

from dateutil import parser
from http import HTTPStatus
from unittest import TestCase
from time import sleep

import api.endpoints.notification_process as np
import testing_utilities as test_utils
import common.pg_utilities as pg_utils

from common.hubspot import HubSpotClient
from common.notifications import NotificationStatus, NotificationAttributes, NotificationType, delete_all_notifications, get_notifications, \
    mark_notification_failure
from common.notification_send import notify_new_user_registration, notify_new_task_signup, notify_user_login
from common.utilities import set_running_unit_tests, now_with_tz, get_country_name, DetailedValueError


TIME_TOLERANCE_SECONDS = 10
DELETE_TEST_DATA = True

TEST_DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'test_data')

# region test users
TEST_USER_01_JSON = {
        "id": "fae88a51-0053-4ba7-b74e-f68b31e82785",
        "created": "2019-05-26T17:46:56+01:00",
        "email": "sw.test@email.co.uk",
        "first_name": "Steven",
        "last_name": "Walcorn",
        "auth0_id": "1234abcd",
        "country_code": "GB",
        "country_name": "United Kingdom",
        "avatar_string": "SW",
        "status": "new"
}

TEST_USER_02_JSON = {
    **TEST_USER_01_JSON,
    **{"login_datetime": "2019-12-05T17:48:56+01:00"},
}

TEST_USER_03_JSON = {
        "id": "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
        "created": "2018-08-17 12:10:56.70011+00",
        "email": "delia@email.co.uk",
        "first_name": "Delia",
        "last_name": "Davies",
        "country_code": "US",
        "country_name": get_country_name("US"),
        "status": "new"
}
# endregion


# region helper functions
def create_registration_notification(user_json=TEST_USER_01_JSON):
    notify_new_user_registration(user_json, None)
    return user_json


def create_task_signup_notification(ut_id="c2712f2a-6ca6-4987-888f-19625668c887",
                                    user_id='35224bd5-f8a8-41f6-8502-f96e12d6ddde'):
    ut_json = {
        'user_id': user_id,
        'project_task_id': '99c155d1-9241-4185-af81-04819a406557',
        'user_project_id': 'cddf188a-e1e4-40c6-af02-2450594be0a3',
        'status': 'active',
        'consented': '2019-05-26 18:16:56.087895+01',
        'id': ut_id,
        'created': '2018-06-13 14:15:16.171819+00'
    }
    notify_new_task_signup(ut_json, None)
    return ut_json


def create_login_notification(user_json=TEST_USER_01_JSON):
    notify_user_login(user_json, None)
    return user_json
# endregion


def clear_database():
    pg_utils.truncate_table('public.projects_usertask')
    pg_utils.truncate_table('public.projects_projecttask')
    pg_utils.truncate_table('public.projects_tasktype')
    pg_utils.truncate_table('public.projects_userproject')
    pg_utils.truncate_table('public.projects_externalsystem')
    pg_utils.truncate_table('public.projects_project')
    pg_utils.truncate_table('public.projects_user')
    pg_utils.truncate_table('public.projects_usergroup')
    pg_utils.truncate_table('public.projects_usertask')
    delete_all_notifications()


class TestNotifications(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        clear_database()
        user_data_csv = os.path.join(TEST_DATA_FOLDER, 'user_data_PSFU.csv')

        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'usergroup_data.csv'), 'public.projects_usergroup')
        pg_utils.insert_data_from_csv(user_data_csv, 'public.projects_user')
        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'project_data_PSFU.csv'), 'public.projects_project')
        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'external_system_data.csv'), 'public.projects_externalsystem')
        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'userproject_PSFU.csv'), 'public.projects_userproject')
        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'tasktype_data.csv'), 'public.projects_tasktype')
        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'projecttask_data_PSFU.csv'), 'public.projects_projecttask')
        pg_utils.insert_data_from_csv(os.path.join(TEST_DATA_FOLDER, 'usertask_PSFU.csv'), 'public.projects_usertask')

        hs_client = HubSpotClient()
        test_utils.post_sample_users_to_crm(user_data_csv, hs_client)

    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            clear_database()

        set_running_unit_tests(False)

    def setUp(self):
        """
        Deletes all notifications before each test is run to ensure tests are independent
        """
        delete_all_notifications()

    def test_01_post_registration(self):
        """
        Tests the notification process associated with a new registration
        """
        user_json = create_registration_notification()
        notifications = get_notifications()
        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        self.assertEqual(user_json['id'], notification['id'])
        self.assertEqual('user-registration', notification['type'])
        self.assertEqual(user_json['email'], notification['label'])
        self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(user_json['email'], notification['details']['email'])

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        created_datetime = parser.parse(notification['created'])
        difference = abs(now - created_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_02_process_registration(self):
        """
        Tests processing of registration notifications. Also tests that notification content has not been altered by updates made during processing
        """
        self.maxDiff = None
        create_registration_notification(user_json=TEST_USER_03_JSON)
        notification = get_notifications()[0]
        number_of_updated_rows_in_db, marking_result = np.process_user_registration(notification)
        self.assertGreaterEqual(1, number_of_updated_rows_in_db)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])
        # now check that notification contents are still the same
        updated_notification = get_notifications()[0]
        self.assertEqual(notification['details'], updated_notification['details'])

    def test_03_post_signup(self):
        """
        Tests the notification process associated with a new task signup
        """
        ut_json = create_task_signup_notification()
        notifications = get_notifications()
        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        self.assertEqual(ut_json['id'], notification['id'])
        self.assertEqual('task-signup', notification['type'])
        self.assertEqual(ut_json['user_id'], notification['label'])
        self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(ut_json['id'], notification['details']['id'])

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        created_datetime = parser.parse(notification['created'])
        difference = abs(now - created_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_04_process_signup(self):
        """
        Tests processing of task signup notifications
        """
        create_task_signup_notification()
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_task_signup(notification)
        self.assertEqual(HTTPStatus.NO_CONTENT, posting_result)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])

    def test_05_post_login(self):
        """
        Tests processing of user login notifications
        """
        user_json = create_login_notification(TEST_USER_02_JSON)
        notifications = get_notifications('type', [NotificationType.USER_LOGIN.value])
        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        self.assertEqual(user_json['email'], notification['label'])
        self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(NotificationType.USER_LOGIN.value, notification[NotificationAttributes.TYPE.value])
        for i in user_json.keys():
            self.assertEqual(user_json[i], notification['details'][i])

    def test_06_process_login(self):
        """
        Tests notification_process.process_user_login
        """
        create_login_notification(TEST_USER_02_JSON)
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_user_login(notification)
        self.assertEqual(HTTPStatus.NO_CONTENT, posting_result)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])

    def test_07_fail_post_login_invalid_data(self):
        """
        Ensures notification_send.notify_user_login fails if notification body does not include login_datetime
        """
        with self.assertRaises(AssertionError):
            create_login_notification()

    def test_08_fail_processing(self):
        """
        Tests function notifications.mark_notification_failure
        """
        # TODO: This test only works if MAX_RETRIES == 2 (defined in api/endpoints/common/notifications.py:25); adapt it to work with any value
        create_registration_notification()
        notifications = get_notifications('type', [NotificationType.USER_REGISTRATION.value])

        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        test_error_message = 'test_03_fail_processing - 01'
        mark_notification_failure(notification, test_error_message, None)

        # read it and check
        notifications = get_notifications('type', [NotificationType.USER_REGISTRATION.value])
        notification = notifications[0]
        self.assertEqual(NotificationStatus.RETRYING.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(1, notification[NotificationAttributes.FAIL_COUNT.value])
        self.assertEqual(test_error_message, notification[NotificationAttributes.ERROR_MESSAGE.value])

        mark_notification_failure(notification, test_error_message, None)
        test_error_message = 'test_03_fail_processing - DLQ'

        with self.assertRaises(DetailedValueError) as context:
            mark_notification_failure(notification, test_error_message, None)

        err = context.exception
        err_msg = err.args[0]
        self.assertEqual('Notification processing failed', err_msg)

        # read it and check
        notifications = get_notifications('type', [NotificationType.USER_REGISTRATION.value])
        notification = notifications[0]
        self.assertEqual(NotificationStatus.DLQ.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(3, notification[NotificationAttributes.FAIL_COUNT.value])
        self.assertEqual(test_error_message, notification[NotificationAttributes.ERROR_MESSAGE.value])
