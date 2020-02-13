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
import os
import uuid
from http import HTTPStatus
from dateutil import parser
from time import sleep

import api.endpoints.notification_process as np
import api.endpoints.user as u
import common.pg_utilities as pg_utils
import testing_utilities as test_utils

from api.endpoints.user import get_user_by_id_api, get_user_by_email_api, patch_user_api, create_user_api
from api.tests.test_scripts.testing_utilities import test_get, test_post, test_patch
from common.dev_config import TIMEZONE_IS_BST
from common.entity_update import EntityUpdate
from common.hubspot import HubSpotClient
from common.notifications import delete_all_notifications, get_notifications, NotificationStatus, \
    NotificationAttributes
from common.utilities import new_correlation_id, now_with_tz, set_running_unit_tests


class TestApiEndpoints(test_utils.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['TEST_ON_AWS'] = 'true'

    def test_01_get_user_by_uuid_api_exists(self):
        invalid_api_key = '3c907908-44a7-490a-9661-3866b3732d22'
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}

        # expected_status = HTTPStatus.OK

        result = test_get(get_user_by_id_api, 'v1/user', path_parameters=path_parameters, aws_api_key=invalid_api_key)
        print(result)
        # result_status = result['statusCode']
        # result_json = json.loads(result['body'])
        #
        # # test results returned from api call
        # self.assertEqual(expected_status, result_status)
        # self.assertDictEqual(EXPECTED_USER, result_json)