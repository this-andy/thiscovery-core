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
import thiscovery_dev_tools.testing_tools as test_tools
from http import HTTPStatus

import api.endpoints.notification_process as np
import api.endpoints.user as u
import api.endpoints.common.hubspot as hs
import thiscovery_lib.notifications as notific
import thiscovery_lib.utilities as utils
import testing_utilities as test_utils

from api.local.dev_config import TIMEZONE_IS_BST

TIME_TOLERANCE_SECONDS = 10

ENTITY_BASE_URL = 'v1/user'

# region expected results
if TIMEZONE_IS_BST:
    tz_hour = "13"
    tz_offset = "01:00"
else:
    tz_hour = "12"
    tz_offset = "00:00"

EXPECTED_USER = {
    "id": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
    "created": f"2018-08-17T{tz_hour}:10:56.798192+{tz_offset}",
    "modified": f"2018-08-17T{tz_hour}:10:56.833885+{tz_offset}",
    "email": "altha@email.co.uk",
    "title": "Mrs",
    "first_name": "Altha",
    "last_name": "Alcorn",
    "country_code": "GB",
    "country_name": "United Kingdom",
    "auth0_id": None,
    "crm_id": None,
    "status": None,
    "avatar_string": "AA",
}
# endregion


class TestUserSignin(test_utils.DbTestCase):
    maxDiff = None
    delete_notifications = True

    def test_01_user_sign_in(self):
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}

        expected_status = HTTPStatus.OK

        result = test_tools.test_get(u.get_user_by_id_api, ENTITY_BASE_URL, path_parameters=path_parameters)
        approximate_login_time = utils.now_with_tz()
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        # test results returned from api call
        self.assertEqual(expected_status, result_status)
        self.assertDictEqual(EXPECTED_USER, result_json)

        # check that login notification exists
        notifications = notific.get_notifications('type', [notific.NotificationType.USER_LOGIN.value])
        self.assertEqual(1, len(notifications))  # should be only one
        notification = notifications[0]
        notification_id = notification['id']
        self.assertEqual('user-login', notification['type'])
        self.assertEqual(EXPECTED_USER['email'], notification['label'])
        self.assertEqual(EXPECTED_USER['id'], notification['details']['user_id'])
        self.assertEqual(EXPECTED_USER['email'], notification['details']['email'])
        self.assertEqual('new', notification['processing_status'])

        # call process notifications and check notification was processed
        np.process_notifications(event=None, context=None)
        notifications = notific.get_notifications('id', notification_id)
        notification = notifications[0]  # should be only one
        self.assertEqual(notific.NotificationStatus.PROCESSED.value, notification[notific.NotificationAttributes.STATUS.value])

        # check that login timestamp was updated in hubspot
        hs_client = hs.HubSpotClient()
        contact = hs_client.get_hubspot_contact_by_email(EXPECTED_USER['email'])
        login_time = contact['properties']['thiscovery_last_login_date']['value']
        login_time_delta = abs(approximate_login_time - hs.hubspot_timestamp_to_datetime(login_time))
        self.assertLess(login_time_delta.seconds, TIME_TOLERANCE_SECONDS)
