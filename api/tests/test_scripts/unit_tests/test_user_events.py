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
import unittest
from http import HTTPStatus
from pprint import pprint
from thiscovery_dev_tools import testing_tools as test_tools

import api.endpoints.common.notifications as notif
import api.endpoints.user as u
import api.tests.test_data.auth0_test_events as td
from api.endpoints.common.eb_utilities import EventbridgeClient, ThiscoveryEvent

# region test users
TEST_USER_01_JSON = {
    "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
    "email": "altha@email.co.uk",
    "first_name": "Altha",
    "last_name": "Alcorn",
    "country_code": "GB",
}


# endregion


class TestUserEvents(test_tools.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        notif.delete_all_notifications()

    def test_record_user_login_ok(self):
        user_json = TEST_USER_01_JSON
        u.record_user_login_event(td.SUCCESSFUL_LOGIN, None)
        notifications = notif.get_notifications()
        self.assertEqual(1, len(notifications))

        notification = notifications[0]
        self.assertEqual('user-login', notification['type'])
        self.assertEqual(user_json['email'], notification['label'])
        self.assertEqual(notif.NotificationStatus.NEW.value, notification[notif.NotificationAttributes.STATUS.value])
        self.assertEqual(user_json['email'], notification['details']['email'])
        self.assertEqual(user_json['id'], notification['details']['id'])
        self.now_datetime_test_and_remove(notification, 'created', tolerance=5)
