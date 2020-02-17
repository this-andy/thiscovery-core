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

import http
import json

import api.endpoints.project as p
import testing_utilities as test_utils


class TestAlarms(test_utils.BaseTestCase):
    """
    When testing on AWS, but not locally, each of the tests below should cause one error notification to be displayed by Epsagon
    """

    def test_alarm_in_get_project_status_for_user_api(self):
        expected_status = http.HTTPStatus.INTERNAL_SERVER_ERROR
        querystring_parameters = {'user_id': '760f4e4d-4a3b-4671-8ceb-129d81f9d9ca'}
        result = test_utils.test_get(p.get_project_status_for_user_api, 'v1/project-user-status', querystring_parameters=querystring_parameters)
        result_status = result['statusCode']
        self.assertEqual(expected_status, result_status)
        self.assertEqual('Deliberate error raised to test error handling', json.loads(result['body'])['error'])
