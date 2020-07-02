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
import yaml
from http import HTTPStatus

import api.endpoints.misc as m
import api.endpoints.project as p
import api.endpoints.user as u
import api.endpoints.user_external_account as uea
import api.endpoints.user_group_membership as ugm
import api.endpoints.user_project as up
import api.endpoints.user_task as ut
import common.utilities as utils
import testing_utilities as test_utils


class TestApiEndpoints(test_utils.AlwaysOnAwsTestCase):
    blank_api_key = ''
    invalid_api_key = '3c907908-44a7-490a-9661-3866b3732d22'
    logger = utils.get_logger()

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
        self.check_api_is_restricted('GET', u.get_user_by_id_api, self.ENTITY_BASE_URL, querystring_parameters=querystring_parameters)

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

    def test_07_get_project_statuses_api_requires_valid_key(self):
        querystring_parameters = {'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc'}
        version_mapping = {
            'v1': p.get_project_status_for_user_api,
            'v2': p.get_project_status_for_external_user_api,
        }
        for api_version, handler_function in version_mapping.items():
            self.check_api_is_restricted('GET', handler_function, f'{api_version}/project-user-status', querystring_parameters=querystring_parameters)


class TestMiscApiEndpoints(TestApiEndpoints):

    def test_08_ping_is_public(self):
        self.check_api_is_public('GET', m.ping, 'v1/ping')

    def test_09_raiseerror_is_public(self):
        querystring_parameters = {'error_id': '200'}
        self.check_api_is_public('POST', m.raise_error_api, 'v1/raise-error', querystring_parameters=querystring_parameters)


class TestUserGroupMembershipApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/usergroupmembership'

    def test_10_create_user_group_membership_api_requires_valid_key(self):
        body = json.dumps({
            'user_id': '1cbe9aad-b29f-46b5-920e-b4c496d42515',
            'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
        })
        self.check_api_is_restricted('POST', ugm.create_user_group_membership_api, self.ENTITY_BASE_URL, request_body=body)


class TestUserProjectApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/userproject'

    def test_11_list_user_projects_api_requires_valid_key(self):
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        self.check_api_is_restricted('GET', up.list_user_projects_api, self.ENTITY_BASE_URL, querystring_parameters=querystring_parameters)

    def test_12_create_user_projects_api_requires_valid_key(self):
        body = json.dumps({
            'user_id': "35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            'project_id': "5907275b-6d75-4ec0-ada8-5854b44fb955",
            'anon_project_specific_user_id': 'b75c864b-a002-466c-989f-16f63d5a6b18',
            'status': 'active',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        })
        self.check_api_is_restricted('POST', up.create_user_project_api, self.ENTITY_BASE_URL, request_body=body)


class TestUserTaskApiEndpoints(TestApiEndpoints):
    ENTITY_BASE_URL = 'v1/usertask'

    def test_13_list_user_tasks_api_requires_valid_key(self):
        querystring_parameters = {'user_id': '851f7b34-f76c-49de-a382-7e4089b744e2'}
        self.check_api_is_restricted('GET', ut.list_user_tasks_api, self.ENTITY_BASE_URL, querystring_parameters=querystring_parameters)

    def test_14_create_user_task_api_requires_valid_key(self):
        body = json.dumps({
            'user_id': '48e30e54-b4fc-4303-963f-2943dda2b139',
            'project_task_id': '6cf2f34e-e73f-40b1-99a1-d06c1f24381a',
            'ext_user_task_id': '78a1ccd7-dee5-49b2-ad5c-8bf4afb3cf93',
            'status': 'active',
            'consented': '2018-06-12 16:16:56.087895+01',
            'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
            'created': '2018-06-13 14:15:16.171819+00'
        })
        self.check_api_is_restricted('POST', ut.create_user_task_api, self.ENTITY_BASE_URL, request_body=body)

    def test_17_set_user_task_completed_api_requires_valid_key(self):
        querystring_parameters = {
            "user_task_id": "615ff0e6-0b41-4870-b9db-527345d1d9e5"
        }
        self.check_api_is_restricted('PUT', ut.set_user_task_completed_api, "v1/user-task-completed", querystring_parameters=querystring_parameters)


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
        self.check_api_is_restricted('POST', uea.create_user_external_account_api, self.ENTITY_BASE_URL, request_body=body)


# region yaml constructors for stackery tags
class GetAtt(yaml.YAMLObject):
    yaml_tag = '!GetAtt'

    def __init__(self, val):
        self.val = val

    @classmethod
    def from_yaml(cls, loader, node):
        return cls(node.value)


class Sub(GetAtt):
    yaml_tag = '!Sub'


class Select(GetAtt):
    yaml_tag = '!Select'


class Ref(GetAtt):
    yaml_tag = '!Ref'
# endregion


class TestSecurityOfEndpointsDefinedInTemplateYaml(test_utils.BaseTestCase):
    public_endpoints = [
        ('/v1/ping', 'get'),
        ('/v1/raise-error', 'post'),
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        template_file = os.path.join(test_utils.BASE_FOLDER, 'template.yaml')
        with open(template_file) as f:
            cls.t_dict = yaml.load(f, Loader=yaml.Loader)

    def test_16_defined_endpoints_are_secure(self):
        endpoint_counter = 0
        api_paths = self.t_dict['Resources']['CoreAPI']['Properties']['DefinitionBody']['paths']
        for url, value in api_paths.items():
            for verb in ['delete', 'get', 'head', 'patch', 'post', 'put']:
                endpoint_config = value.get(verb)
                if endpoint_config:
                    endpoint_counter += 1
                    self.logger.info(f'Found endpoint {verb.upper()} {url} in template.yaml. Checking if it is secure',
                                     extra={'endpoint_config': endpoint_config})
                    if (url, verb) in self.public_endpoints:
                        self.assertIsNone(endpoint_config.get('security'))
                    else:
                        self.assertEqual([{'api_key': []}], endpoint_config.get('security'))
        self.logger.info(f'The configuration of {endpoint_counter} endpoints in template.yaml is as expected')
