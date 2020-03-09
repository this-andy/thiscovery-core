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

import csv
import os
import requests
import unittest
import uuid
from dateutil import parser

import api.endpoints.user as user
import common.pg_utilities as pg_utils
import common.utilities as utils
from common.dev_config import TEST_ON_AWS, AWS_TEST_API
from common.hubspot import HubSpotClient
from common.notifications import delete_all_notifications
from common.pg_utilities import truncate_table_multiple


BASE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..')  # thiscovery-core/
TEST_DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'test_data')


def tests_running_on_aws():
    """
    Checks if tests are calling AWS API endpoints
    """
    test_on_aws = os.environ.get('TEST_ON_AWS')
    if test_on_aws is None:
        test_on_aws = TEST_ON_AWS
    elif test_on_aws.lower() == 'false':
        test_on_aws = False
    return test_on_aws


class BaseTestCase(unittest.TestCase):
    """
    Subclass of unittest.TestCase with methods frequently used in Thiscovery testing.
    """
    # ssm_client = utils.SsmClient()
    secrets_client = utils.SecretsManager()

    @classmethod
    def setUpClass(cls):
        utils.set_running_unit_tests(True)
        # cls.ssm_client.put_parameter('running-tests', 'true', prefix='/thiscovery/')
        cls.secrets_client.create_or_update_secret('runtime-parameters', {'running-tests': 'true'})
        cls.logger = utils.get_logger()

    @classmethod
    def tearDownClass(cls):
        # cls.ssm_client.put_parameter('running-tests', 'false', prefix='/thiscovery/')
        cls.secrets_client.create_or_update_secret('runtime-parameters', {'running-tests': 'false'})
        utils.set_running_unit_tests(False)

    def value_test_and_remove(self, entity_dict, attribute_name, expected_value):
        actual_value = entity_dict[attribute_name]
        del entity_dict[attribute_name]
        self.assertEqual(expected_value, actual_value)
        return actual_value

    def now_datetime_test_and_remove(self, entity_dict, datetime_attribute_name, tolerance=10):
        datetime_string = entity_dict[datetime_attribute_name]
        del entity_dict[datetime_attribute_name]
        now = utils.now_with_tz()
        datetime_value = parser.parse(datetime_string)
        difference = abs(now - datetime_value)
        self.assertLess(difference.seconds, tolerance)
        return datetime_string

    def uuid_test_and_remove(self, entity_dict, uuid_attribute_name):
        uuid_value = entity_dict[uuid_attribute_name]
        del entity_dict[uuid_attribute_name]
        self.assertTrue(uuid.UUID(uuid_value).version == 4)
        return uuid_value

    def new_uuid_test_and_remove(self, entity_dict):
        try:
            uuid_value = self.uuid_test_and_remove(entity_dict, 'id')
            return uuid_value
        except KeyError:
            self.assertTrue(False, 'id missing')

    @staticmethod
    def remove_dict_items_to_be_ignored_by_tests(entity_dict, list_of_keys):
        for key in list_of_keys:
            del entity_dict[key]


@unittest.skipIf(not tests_running_on_aws(), "Testing are using local methods and this test only makes sense if calling an AWS API endpoint")
class AlwaysOnAwsTestCase(BaseTestCase):
    """
    Skips tests if tests are running locally
    """
    pass


class DbTestCase(BaseTestCase):
    delete_test_data = False
    delete_notifications = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clear_test_data()
        delete_all_notifications()
        pg_utils.insert_data_from_csv_multiple(
            (os.path.join(TEST_DATA_FOLDER, 'usergroup_data.csv'), 'public.projects_usergroup'),
            (os.path.join(TEST_DATA_FOLDER, 'project_data_PSFU.csv'), 'public.projects_project'),
            (os.path.join(TEST_DATA_FOLDER, 'tasktype_data.csv'), 'public.projects_tasktype'),
            (os.path.join(TEST_DATA_FOLDER, 'external_system_data.csv'), 'public.projects_externalsystem'),
            (os.path.join(TEST_DATA_FOLDER, 'projecttask_data_PSFU.csv'), 'public.projects_projecttask'),
            (os.path.join(TEST_DATA_FOLDER, 'projectgroupvisibility_data.csv'), 'public.projects_projectgroupvisibility'),
            (os.path.join(TEST_DATA_FOLDER, 'projecttaskgroupvisibility_data.csv'), 'public.projects_projecttaskgroupvisibility'),
            (os.path.join(TEST_DATA_FOLDER, 'user_data_PSFU.csv'), 'public.projects_user'),
            (os.path.join(TEST_DATA_FOLDER, 'usergroupmembership_data.csv'), 'public.projects_usergroupmembership'),
            (os.path.join(TEST_DATA_FOLDER, 'userproject_PSFU.csv'), 'public.projects_userproject'),
            (os.path.join(TEST_DATA_FOLDER, 'usertask_PSFU.csv'), 'public.projects_usertask'),
        )

    @classmethod
    def tearDownClass(cls):
        if cls.delete_test_data:
            cls.clear_test_data()
        if cls.delete_notifications:
            delete_all_notifications()
        super().tearDownClass()

    @classmethod
    def clear_test_data(cls):
        """
        Clears all PostgreSQL database tables used by the test suite. Optionally deletes all notifications in AWS Dynamodb if cls.delete_notifications == True.
        """
        truncate_table_multiple(
            'public.projects_entityupdate',
            'public.projects_usertask',
            'public.projects_userproject',
            'public.projects_usergroupmembership',
            'public.projects_user',
            'public.projects_projecttaskgroupvisibility',
            'public.projects_projectgroupvisibility',
            'public.projects_projecttask',
            'public.projects_externalsystem',
            'public.projects_tasktype',
            'public.projects_project',
            'public.projects_usergroup',
            'public.projects_userexternalaccount',
        )


def _aws_request(method, url, params=None, data=None, aws_api_key=None):
    return utils.aws_request(method, url, AWS_TEST_API, params=params, data=data, aws_api_key=aws_api_key)


def aws_get(url, params):
    return _aws_request(method='GET', url=url, params=params)


def aws_post(url, request_body):
    return _aws_request(method='POST', url=url, data=request_body)


def aws_patch(url, request_body):
    return _aws_request(method='PATCH', url=url, data=request_body)


def _test_request(request_method, local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None, aws_api_key=None,
                  correlation_id=None):
    logger = utils.get_logger()

    if tests_running_on_aws():
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
        logger.info(f'Url passed to _aws_request: {url}', extra={'path_parameters': path_parameters, 'querystring_parameters': querystring_parameters})
        return _aws_request(method=request_method, url=url, params=querystring_parameters, data=request_body, aws_api_key=aws_api_key)
    else:
        event = {}
        if path_parameters is not None:
            event['pathParameters'] = path_parameters
        if querystring_parameters is not None:
            event['queryStringParameters'] = querystring_parameters
        if request_body is not None:
            event['body'] = request_body
        return local_method(event, correlation_id)


def test_get(local_method, aws_url, path_parameters=None, querystring_parameters=None, aws_api_key=None, correlation_id=None):
    return _test_request('GET', local_method, aws_url, path_parameters=path_parameters,
                         querystring_parameters=querystring_parameters, aws_api_key=aws_api_key, correlation_id=correlation_id)


def test_post(local_method, aws_url, path_parameters=None, request_body=None, correlation_id=None):
    return _test_request('POST', local_method, aws_url, path_parameters=path_parameters, request_body=request_body, correlation_id=correlation_id)


def test_patch(local_method, aws_url, path_parameters=None, request_body=None, correlation_id=None):
    return _test_request('PATCH', local_method, aws_url, path_parameters=path_parameters, request_body=request_body, correlation_id=correlation_id)


def post_sample_users_to_crm(user_test_data_csv, hs_client=HubSpotClient()):
    with open(user_test_data_csv) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            user_json = {
                "id": row[0],
                "created": row[1],
                "email": row[3],
                "first_name": row[5],
                "last_name": row[6],
                "country_code": row[9],
                "country_name": utils.get_country_name(row[9]),
                "avatar_string": f'{row[5][0].upper()}{row[6][0].upper()}',
                "status": "new"
            }

            hubspot_id, _ = hs_client.post_new_user_to_crm(user_json, correlation_id=None)
            user_jsonpatch = [
                {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
            ]
            user.patch_user(user_json['id'], user_jsonpatch, utils.now_with_tz(), correlation_id=None)
