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

from unittest import TestCase
from dateutil import parser
from api.common.utilities import set_running_unit_tests, now_with_tz
from api.common.notifications import NotificationStatus, NotificationAttributes, delete_all_notifications, get_notifications

TIME_TOLERANCE_SECONDS = 10
DELETE_TEST_DATA = True


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

    def test_01_post_registration(self):
        from api.common.notification_send import notify_new_user_registration

        user_id = "fae88a51-0053-4ba7-b74e-f68b31e82785"
        user_email = 'sw.test@email.co.uk'
        user_json = {
            "id": user_id,
            "created": "2019-05-26T17:46:56+01:00",
            "email": user_email,
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "country_code": "GB",
            "country_name": "United Kingdom",
            "avatar_string": "SW",
            "status": "new"}

        notify_new_user_registration(user_json, None)

        notifications = get_notifications()
        self.assertEqual(len(notifications), 1)

        notification = notifications[0]
        self.assertEqual(notification['id'], user_id)
        self.assertEqual(notification['type'], 'user-registration')
        self.assertEqual(notification['label'], user_email)
        self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.NEW.value)
        self.assertEqual(notification['details']['email'], user_email)

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        created_datetime = parser.parse(notification['created'])
        difference = abs(now - created_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_02_post_signup(self):
        from api.common.notification_send import notify_new_task_signup

        ut_id = "9620089b-e9a4-46fd-bb78-091c8449d777"
        user_id = '35224bd5-f8a8-41f6-8502-f96e12d6ddde'
        ut_json = {
            'user_id': user_id,
            'project_task_id': 'c92c8289-3590-4a85-b699-98bc8171ccde',
            'user_project_id': '5ee37b14-7d20-478f-8500-6a00cb15e345',
            'status': 'active',
            'consented': '2019-05-26 18:16:56.087895+01',
            'id': ut_id,
            'created': '2018-06-13 14:15:16.171819+00'
        }
        notify_new_task_signup(ut_json, None)

        notifications = get_notifications()
        self.assertEqual(len(notifications), 2)

        notification = notifications[1]
        self.assertEqual(notification['id'], ut_id)
        self.assertEqual(notification['type'], 'task-signup')
        self.assertEqual(notification['label'], user_id)
        self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.NEW.value)
        self.assertEqual(notification['details']['id'], ut_id)

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        created_datetime = parser.parse(notification['created'])
        difference = abs(now - created_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_03_fail_processing(self):
        from api.common.notifications import mark_notification_failure
        notifications = get_notifications('type', ['user-registration'])

        self.assertEqual(len(notifications), 1)

        notification = notifications[0]
        test_error_message = 'test_03_fail_processing - 01'
        mark_notification_failure(notification, test_error_message, None)

        # read it and check
        notifications = get_notifications('type', ['user-registration'])
        notification = notifications[0]
        self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.RETRYING.value)
        self.assertEqual(notification[NotificationAttributes.FAIL_COUNT.value], '1')
        self.assertEqual(notification[NotificationAttributes.ERROR_MESSAGE.value], test_error_message)

        mark_notification_failure(notification, test_error_message, None)
        test_error_message = 'test_03_fail_processing - DLQ'
        mark_notification_failure(notification, test_error_message, None)

        # read it and check
        notifications = get_notifications('type', ['user-registration'])
        notification = notifications[0]
        self.assertEqual(notification[NotificationAttributes.STATUS.value], NotificationStatus.DLQ.value)
        self.assertEqual(notification[NotificationAttributes.FAIL_COUNT.value], '3')
        self.assertEqual(notification[NotificationAttributes.ERROR_MESSAGE.value], test_error_message)


