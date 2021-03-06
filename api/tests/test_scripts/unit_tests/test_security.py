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
import os
import yaml

from thiscovery_dev_tools.testing_tools import TestApiEndpoints, TestSecurityOfEndpointsDefinedInTemplateYaml


import api.endpoints.misc as m
import api.endpoints.project as p
import api.endpoints.user as u
import api.endpoints.user_external_account as uea
import api.endpoints.user_group_membership as ugm
import api.endpoints.user_project as up
import api.endpoints.user_task as ut


class TestUserApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/user'

    def test_01_get_user_by_uuid_api_requires_valid_key(self):
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        self.check_api_is_restricted('GET', self.ENTITY_BASE_URL, path_parameters=path_parameters)

    def test_02_get_user_email_api_requires_valid_key(self):
        querystring_parameters = {'email': 'altha@email.co.uk'}
        self.check_api_is_restricted('GET', self.ENTITY_BASE_URL, querystring_parameters=querystring_parameters)

    def test_03_patch_user_api_requires_valid_key(self):
        path_parameters = {'id': "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"}
        body = json.dumps([{'op': 'replace', 'path': '/first_name', 'value': 'simon'}])
        self.check_api_is_restricted('PATCH', self.ENTITY_BASE_URL, path_parameters=path_parameters, request_body=body)

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
        self.check_api_is_restricted('POST', self.ENTITY_BASE_URL, request_body=body)


class TestProjectApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'project'

    def test_05_list_projects_api_requires_valid_key(self):
        self.check_api_is_restricted('GET', f'v1/{self.ENTITY_BASE_URL}')

    def test_06_get_project_api_requires_valid_key(self):
        path_parameters = {'id': "a099d03b-11e3-424c-9e97-d1c095f9823b"}
        self.check_api_is_restricted('GET', f'v1/{self.ENTITY_BASE_URL}', path_parameters=path_parameters)

    def test_07_get_project_statuses_api_requires_valid_key(self):
        querystring_parameters = {'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}
        self.check_api_is_restricted('GET', 'v1/project-user-status', querystring_parameters=querystring_parameters)


class TestMiscApiEndpoints(TestApiEndpoints):

    def test_08_ping_is_public(self):
        self.check_api_is_public('GET', 'v1/ping')

    def test_09_raiseerror_is_public(self):
        querystring_parameters = {'error_id': '200'}
        self.check_api_is_public('POST', 'v1/raise-error', querystring_parameters=querystring_parameters)


class TestUserGroupMembershipApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/usergroupmembership'

    def test_10_create_user_group_membership_api_requires_valid_key(self):
        body = json.dumps({
            'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        })
        self.check_api_is_restricted('POST', self.ENTITY_BASE_URL, request_body=body)


class TestUserProjectApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/userproject'

    def test_11_list_user_projects_api_requires_valid_key(self):
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        self.check_api_is_restricted('GET', self.ENTITY_BASE_URL, querystring_parameters=querystring_parameters)

    def test_12_create_user_projects_api_requires_valid_key(self):
        body = json.dumps({
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'project_id': "5907275b-6d75-4ec0-ada8-5854b44fb955",
            'anon_project_specific_user_id': 'b75c864b-a002-466c-989f-16f63d5a6b18',
            'status': 'active',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        })
        self.check_api_is_restricted('POST', self.ENTITY_BASE_URL, request_body=body)


class TestUserTaskApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/usertask'

    def test_13_list_user_tasks_api_requires_valid_key(self):
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        self.check_api_is_restricted('GET', self.ENTITY_BASE_URL, querystring_parameters=querystring_parameters)

    def test_14_create_user_task_api_requires_valid_key(self):
        body = json.dumps({
            'user_id': '48e30e54-b4fc-4303-963f-2943dda2b139',
            'project_task_id': '6cf2f34e-e73f-40b1-99a1-d06c1f24381a',
            'anon_user_task_id': '78a1ccd7-dee5-49b2-ad5c-8bf4afb3cf93',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        })
        self.check_api_is_restricted('POST', self.ENTITY_BASE_URL, request_body=body)

    def test_17_set_user_task_completed_api_requires_valid_key(self):
        querystring_parameters = {
            "user_task_id": "615ff0e6-0b41-4870-b9db-527345d1d9e5"
        }
        self.check_api_is_restricted('PUT', "v1/user-task-completed", querystring_parameters=querystring_parameters)


class TestUserExternalAccountApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/userexternalaccount'

    def test_15_create_user_external_account_api_requires_valid_key(self):
        body = json.dumps({
            'external_system_id': "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'external_user_id': 'cc02',
            'status': 'active',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        })
        self.check_api_is_restricted('POST', self.ENTITY_BASE_URL, request_body=body)


class TestTemplate(TestSecurityOfEndpointsDefinedInTemplateYaml):
    public_endpoints = [
        ('/v1/ping', 'get'),
        ('/v1/raise-error', 'post'),
        ('/v1/log-request', 'post'),
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass(
            template_file_path=os.path.join(test_utils.BASE_FOLDER, 'template.yaml')
        )

    def test_16_defined_endpoints_are_secure(self):
        self.check_defined_endpoints_are_secure()
