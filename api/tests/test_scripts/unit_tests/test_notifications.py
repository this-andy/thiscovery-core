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
import copy
import os

from datetime import timedelta
from http import HTTPStatus
from thiscovery_lib.dynamodb_utilities import Dynamodb

import api.endpoints.notification_process as np
import common.notifications as notific
import common.notification_send as notific_send
import thiscovery_lib.utilities as utils

from common.hubspot import HubSpotClient
from common.notifications import NotificationStatus, NotificationAttributes, NotificationType, delete_all_notifications, get_notifications, \
    mark_notification_failure
from common.notification_send import notify_new_user_registration, notify_new_task_signup, notify_user_login, new_transactional_email_notification
from thiscovery_lib.utilities import get_country_name, DetailedValueError
from test_transactional_email import test_email_dict


TIME_TOLERANCE_SECONDS = 10

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

def create_transactional_email_notification():
    new_transactional_email_notification(email_dict=test_email_dict)
# endregion


class TestNotifications(test_utils.DbTestCase):
    delete_notifications = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ddb_client = Dynamodb()
        cls.hs_client = HubSpotClient()
        user_data_csv = os.path.join(test_utils.TEST_DATA_FOLDER, 'user_data_PSFU.csv')
        test_utils.post_sample_users_to_crm(user_data_csv, cls.hs_client)

    def setUp(self):
        """
        Deletes all notifications before each test is run to ensure tests are independent
        """
        delete_all_notifications()

    def clear_notification_queue_setup(self, notification_type_value, target_status, modified_datetime):
        """
        Creates a registration notification in ddb and updates its status to target_status and modified field to modified_datetime

        Args:
            notification_type_value: The NotificationType.<VARIABLE>.value of notification to work with
            target_status (str): The "status" field of the created notification will be set to this value
            modified_datetime (datetime): The "modified" field of the created notification will be set to this value

        Returns:
            Tuple: (Id of created notification, list of notificatioins deleted by clear_notification_queue)
        """
        handlers_map = {
            NotificationType.USER_REGISTRATION.value: {
                'create_notification_function': create_registration_notification
            },
            NotificationType.TRANSACTIONAL_EMAIL.value: {
                'create_notification_function': create_transactional_email_notification
            }
        }

        create_notification_function = handlers_map[notification_type_value]['create_notification_function']
        create_notification_function()
        notification = get_notifications(NotificationAttributes.TYPE.value, [notification_type_value])[0]
        self.ddb_client.update_item(
            table_name=notific.NOTIFICATION_TABLE_NAME,
            key=notification['id'],
            name_value_pairs={
                'modified': modified_datetime.isoformat(),
                NotificationAttributes.STATUS.value: target_status,
            }
        )
        return (
            notification['id'],
            np.clear_notification_queue(dict(), None)
        )

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
        self.now_datetime_test_and_remove(notification, 'created', tolerance=TIME_TOLERANCE_SECONDS)

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
        self.now_datetime_test_and_remove(notification, 'created', tolerance=TIME_TOLERANCE_SECONDS)

    def test_04_process_signup(self):
        """
        Tests processing of task signup notifications
        """
        create_task_signup_notification()
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_task_signup(notification)
        self.assertEqual(HTTPStatus.NO_CONTENT, posting_result)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])

    def test_05_process_signup_with_expired_token(self):
        expired_token = self.hs_client.get_expired_token_from_database()
        self.hs_client.save_token(expired_token)
        create_task_signup_notification()
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_task_signup(notification)
        self.assertEqual(HTTPStatus.NO_CONTENT, posting_result)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])
        notification = get_notifications()[0]
        self.assertEqual(NotificationStatus.PROCESSED.value, notification[NotificationAttributes.STATUS.value])

    def test_06_post_login(self):
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

    def test_07_process_login(self):
        """
        Tests notification_process.process_user_login
        """
        create_login_notification(TEST_USER_02_JSON)
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_user_login(notification)
        self.assertEqual(HTTPStatus.NO_CONTENT, posting_result)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])

    def test_08_process_login_with_expired_token(self):
        """
        Tests notification_process.process_user_login with an expired HubSpot token
        """
        expired_token = self.hs_client.get_expired_token_from_database()
        self.hs_client.save_token(expired_token)
        create_login_notification(TEST_USER_02_JSON)
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_user_login(notification)
        self.assertEqual(HTTPStatus.NO_CONTENT, posting_result)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])
        notification = get_notifications()[0]
        self.assertEqual(NotificationStatus.PROCESSED.value, notification[NotificationAttributes.STATUS.value])

    def test_09_fail_post_login_invalid_data(self):
        """
        Ensures notification_send.notify_user_login fails if notification body does not include login_datetime
        """
        with self.assertRaises(AssertionError):
            create_login_notification()

    def test_10_fail_processing(self):
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

    def test_11_clear_notification_queue_deletes_old_notification(self):
        eight_days_ago = utils.now_with_tz() - timedelta(days=8)
        notification_id, deleted_notifications = self.clear_notification_queue_setup(
            notification_type_value=NotificationType.USER_REGISTRATION.value,
            target_status=NotificationStatus.PROCESSED.value,
            modified_datetime=eight_days_ago,
        )
        self.assertEqual(1, len(deleted_notifications))
        self.assertEqual(notification_id, deleted_notifications[0]['id'])

    def test_12_clear_notification_queue_leaves_recent_notification_untouched(self):
        six_days_ago = utils.now_with_tz() - timedelta(days=6)
        notification_id, deleted_notifications = self.clear_notification_queue_setup(
            notification_type_value=NotificationType.USER_REGISTRATION.value,
            target_status=NotificationStatus.PROCESSED.value,
            modified_datetime=six_days_ago,
        )
        self.assertTrue(notification_id)
        self.assertEqual(0, len(deleted_notifications))

    def test_13_clear_notification_queue_leaves_dlq_notifications_untouched(self):
        eight_days_ago = utils.now_with_tz() - timedelta(days=8)
        notification_id, deleted_notifications = self.clear_notification_queue_setup(
            notification_type_value=NotificationType.USER_REGISTRATION.value,
            target_status=NotificationStatus.DLQ.value,
            modified_datetime=eight_days_ago,
        )
        self.assertTrue(notification_id)
        self.assertEqual(0, len(deleted_notifications))

    def test_14_post_transactional_email(self):
        email_dict = test_email_dict
        notific_send.new_transactional_email_notification(email_dict=email_dict)
        notifications = get_notifications('type', [NotificationType.TRANSACTIONAL_EMAIL.value])
        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        self.assertEqual(f"{email_dict['template_name']}_{email_dict['to_recipient_id']}", notification['label'])
        self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(NotificationType.TRANSACTIONAL_EMAIL.value, notification[NotificationAttributes.TYPE.value])
        for i in email_dict.keys():
            self.assertEqual(email_dict[i], notification['details'][i])

    def test_15_process_transactional_email(self):
        email_dict = copy.deepcopy(test_email_dict)
        email_dict["to_recipient_id"] = 'dceac123-03a7-4e29-ab5a-739e347b374d'
        notific_send.new_transactional_email_notification(email_dict=email_dict)
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_transactional_email(notification, mock_server=True)
        self.assertEqual(HTTPStatus.OK, posting_result.status_code)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])

    def test_16_clear_notification_queue_leaves_transactional_email_notifications_untouched(self):
        eight_days_ago = utils.now_with_tz() - timedelta(days=8)
        notification_id, deleted_notifications = self.clear_notification_queue_setup(
            notification_type_value=NotificationType.TRANSACTIONAL_EMAIL.value,
            target_status=NotificationStatus.PROCESSED.value,
            modified_datetime=eight_days_ago,
        )
        self.assertTrue(notification_id)
        self.assertEqual(0, len(deleted_notifications))

    def test_17_post_transactional_email_by_email(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict["to_recipient_id"]
        email_dict["to_recipient_email"] = 'recipient@email.com'
        notific_send.new_transactional_email_notification(email_dict=email_dict)
        notifications = get_notifications('type', [NotificationType.TRANSACTIONAL_EMAIL.value])
        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        self.assertEqual(f"{email_dict['template_name']}_{email_dict['to_recipient_email']}", notification['label'])
        self.assertEqual(NotificationStatus.NEW.value, notification[NotificationAttributes.STATUS.value])
        self.assertEqual(NotificationType.TRANSACTIONAL_EMAIL.value, notification[NotificationAttributes.TYPE.value])
        for i in email_dict.keys():
            self.assertEqual(email_dict[i], notification['details'][i])

    def test_18_process_transactional_email_by_email(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict["to_recipient_id"]
        email_dict["to_recipient_email"] = 'recipient@email.com'
        notific_send.new_transactional_email_notification(email_dict=email_dict)
        notification = get_notifications()[0]
        posting_result, marking_result = np.process_transactional_email(notification, mock_server=True)
        self.assertEqual(HTTPStatus.OK, posting_result.status_code)
        self.assertEqual(HTTPStatus.OK, marking_result['ResponseMetadata']['HTTPStatusCode'])
