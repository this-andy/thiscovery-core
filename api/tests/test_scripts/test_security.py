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

import api.endpoints.misc as m
import api.endpoints.notification_process as np
import api.endpoints.project as p
import api.endpoints.user as u
import common.utilities as utils
import testing_utilities as test_utils


class TestApiEndpoints(test_utils.BaseTestCase):
    blank_api_key = ''
    invalid_api_key = '3c907908-44a7-490a-9661-3866b3732d22'
    logger = utils.get_logger()

    @classmethod
    def setUpClass(cls):
        os.environ['TEST_ON_AWS'] = 'true'

    def _common_assertion(self, expected_status, request_verb, local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None):
        for key in [self.blank_api_key, self.invalid_api_key]:
            self.logger.info(f'Key: {key}')
            result = test_utils._test_request(request_verb, local_method, aws_url, path_parameters=path_parameters,
                                              querystring_parameters=querystring_parameters, request_body=request_body, aws_api_key=key)
            result_status = result['statusCode']
            self.assertEqual(expected_status, result_status)

    def check_api_is_restricted(self, request_verb, local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None):
        expected_status = HTTPStatus.FORBIDDEN
        self._common_assertion(expected_status, request_verb, local_method, aws_url, path_parameters=path_parameters,
                               querystring_parameters=querystring_parameters, request_body=request_body)

    def check_api_is_public(self, request_verb, local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None):
        expected_status = HTTPStatus.OK
        self._common_assertion(expected_status, request_verb, local_method, aws_url, path_parameters=path_parameters,
                               querystring_parameters=querystring_parameters, request_body=request_body)


class TestUserApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/user'

    def test_01_get_user_by_uuid_api_requires_valid_key(self):
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        self.check_api_is_restricted('GET', u.get_user_by_id_api, self.ENTITY_BASE_URL, path_parameters=path_parameters)

    def test_02_get_user_email_api_requires_valid_key(self):
        querystring_parameters = {'email': 'altha@email.co.uk'}
        self.check_api_is_restricted('GET', u.get_user_by_id_api, 'v1/user', querystring_parameters=querystring_parameters)

    def test_03_patch_user_api_requires_valid_key(self):
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        body = json.dumps([{'op': 'replace', 'path': '/first_name', 'value': 'simon'}])
        self.check_api_is_restricted('PATCH', u.patch_user_api, self.ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)

    def test_04_create_user_api_requires_valid_key(self):
        user_id = '48e30e54-b4fc-4303-963f-2943dda2b139'
        user_email = 'sw@email.co.uk'
        user_json = {
            "id": user_id,
            "created": "2018-08-21T11:16:56+01:00",
            "email": user_email,
            "email_address_verified": False,
            "title": "Mr",
            "first_name": "Steven",
            "last_name": "Walcorn",
            "auth0_id": "1234abcd",
            "country_code": "GB",
            "crm_id": None,
            "status": "new"}
        body = json.dumps(user_json)
        self.check_api_is_restricted('POST', u.create_user_api, self.ENTITY_BASE_URL, request_body=body)


class TestProjectApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'project'

    def test_05_list_projects_api_requires_valid_key(self):
        self.check_api_is_restricted('GET', p.list_projects_api, f'v1/{self.ENTITY_BASE_URL}')

    def test_06_get_project_api_requires_valid_key(self):
        path_parameters = {'id': "a099d03b-11e3-424c-9e97-d1c095f9823b"}
        self.check_api_is_restricted('GET', p.get_project_api, f'v1/{self.ENTITY_BASE_URL}', path_parameters=path_parameters)


class TestMiscApiEndpoints(TestApiEndpoints):

    def test_01_ping_is_public(self):
        self.check_api_is_public('GET', m.ping, 'v1/ping')
