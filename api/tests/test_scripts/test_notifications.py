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

from dateutil import parser
from http import HTTPStatus
from unittest import TestCase
from time import sleep

import api.endpoints.notification_process as np
from api.common.hubspot import HubSpotClient
from api.common.notifications import NotificationStatus, NotificationAttributes, NotificationType, delete_all_notifications, get_notifications
from api.common.notification_send import notify_new_user_registration, notify_new_task_signup, notify_user_login
from api.common.utilities import set_running_unit_tests, now_with_tz, get_country_name

TIME_TOLERANCE_SECONDS = 10
DELETE_TEST_DATA = True


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

#
# def create_task_signup_notification(ut_id="ceb30e82-de0f-4009-940d-778dace69ec9",
#                                     user_id='d1070e81-557e-40eb-a7ba-b951ddb7ebdc'):
#     ut_json = {
#         'user_id': user_id,
#         'project_task_id': '5907275b-6d75-4ec0-ada8-5854b44fb955',
#         'user_project_id': '0910e15a-4bc3-4f5f-a8f5-e092afe90eb6',
#         'status': 'active',
#         'consented': '2019-05-26 18:16:56.087895+01',
#         'id': ut_id,
#         'created': '2018-06-13 14:15:16.171819+00'
#     }
#     notify_new_task_signup(ut_json, None)
#     return ut_json
#
#
# def create_task_signup_notification(ut_id="9620089b-e9a4-46fd-bb78-091c8449d777",
#                                     user_id='35224bd5-f8a8-41f6-8502-f96e12d6ddde'):
#     ut_json = {
#         'user_id': user_id,
#         'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
#         'user_project_id': '5ee37b14-7d20-478f-8500-6a00cb15e345',
#         'status': 'active',
#         'consented': '2019-05-26 18:16:56.087895+01',
#         'id': ut_id,
#         'created': '2018-06-13 14:15:16.171819+00'
#     }
#     notify_new_task_signup(ut_json, None)
#     return ut_json


def create_login_notification(user_json=TEST_USER_01_JSON):
    notify_user_login(user_json, None)
    return user_json
# endregion


class TestNotifications(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        delete_all_notifications()

    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            delete_all_notifications()
        set_running_unit_tests(False)

    def setUp(self):
        """
        Deletes all notifications before each test is run to ensure tests are independent
        """
        delete_all_notifications()

    def test_01_post_registration(self):
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
        pass

    def test_03_post_signup(self):
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
        from api.common.notifications import mark_notification_failure
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
        self.assertEqual('1', notification[NotificationAttributes.FAIL_COUNT.value])
        self.assertEqual(test_error_message, notification[NotificationAttributes.ERROR_MESSAGE.value])

        mark_notification_failure(notification, test_error_message, None)
        test_error_message = 'test_03_fail_processing - DLQ'
        mark_notification_failure(notification, test_error_message, None)

        # read it and check

        notifications = get_notifications('type', [NotificationType.USER_REGISTRATION.value])
        notification = notifications[0]
        self.assertEqual(NotificationStatus.DLQ.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual('3', notification[NotificationAttributes.FAIL_COUNT.value])
        self.assertEqual(test_error_message, notification[NotificationAttributes.ERROR_MESSAGE.value])
