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
from http import HTTPStatus
from unittest import TestCase
from api.tests.test_scripts.testing_utilities import test_get
from api.common.dev_config import TEST_ON_AWS
from api.common.utilities import set_running_unit_tests


class TestUserExternalAccount(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_01_ping(self):
        from api.endpoints.misc import ping

        expected_status = HTTPStatus.OK

        test_on_aws = os.environ.get('TEST_ON_AWS')
        if test_on_aws is None:
            test_on_aws = TEST_ON_AWS
        elif test_on_aws.lower() == 'false':
            test_on_aws = False

        if test_on_aws:
            expected_region = 'eu-west-1'
        else:
            expected_region = ''

        result = test_get(ping, 'v1/ping', None, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual('Response from THIS Institute citizen science API', result_json['message'])
        self.assertEqual(expected_region, result_json['region'])
