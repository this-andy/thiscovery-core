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
from unittest import TestCase
from api.tests.test_scripts.testing_utilities import test_get
from api.common.dev_config import TEST_ON_AWS


class TestUserExternalAccount(TestCase):

    def test_01_ping(self):
        if TEST_ON_AWS:  # this test does not make sense to run locally
            from api.endpoints.misc import ping

            expected_status = HTTPStatus.OK

            result = test_get(ping, 'ping', None, None, None)
            result_status = result['statusCode']
            result_json = json.loads(result['body'])

            self.assertEqual(expected_status, result_status)
            self.assertEqual('Response from THIS Institute citizen science API', result_json['message'])
            self.assertEqual('eu-west-1', result_json['region'])
