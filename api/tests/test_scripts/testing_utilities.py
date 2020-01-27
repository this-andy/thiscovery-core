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
import uuid
from dateutil import parser
from requests import get, post, patch
from unittest import TestCase

import api.endpoints.user as user
import common.pg_utilities as pg_utils
from common.dev_config import TEST_ON_AWS, AWS_TEST_API
from common.hubspot import HubSpotClient
from common.notifications import delete_all_notifications
from common.pg_utilities import truncate_table_multiple
from common.utilities import get_secret, now_with_tz, get_logger, get_country_name, set_running_unit_tests

TEST_DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'test_data')


class DbTestCase(TestCase):
    delete_test_data = False
    delete_notifications = False

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.clear_test_data()
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
        set_running_unit_tests(False)

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
        if cls.delete_notifications:
            delete_all_notifications()



def test_get(local_method, aws_url, path_parameters=None, querystring_parameters=None, correlation_id=None):
    logger = get_logger()
    if TEST_ON_AWS:
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
        logger.info(f'Url passed to aws_get: {url}', extra={'path_parameters': path_parameters, 'querystring_parameters': querystring_parameters})
        return aws_get(url, querystring_parameters, correlation_id)
    else:
        if path_parameters is not None:
            event = {'pathParameters': path_parameters}
        elif querystring_parameters is not None:
            event = {'queryStringParameters': querystring_parameters}
        else:
            event = None
        return local_method(event, correlation_id)


def aws_get(url, params, correlation_id):
    aws_connection = get_secret('aws-connection')
    aws_api_key = aws_connection['aws-api-key']
    full_url = AWS_TEST_API + url
    headers = {'Content-Type': 'application/json', 'x-api-key': aws_api_key}
    try:
        response = get(full_url, params=params, headers=headers)
        return {'statusCode': response.status_code, 'body': response.text}
    except Exception as err:
        raise err


def test_post(local_method, aws_url, path_parameters, request_body, correlation_id):
    if TEST_ON_AWS:
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
        return aws_post(url, request_body, correlation_id)
    else:
        event = {}
        if path_parameters is not None:
            event['pathParameters'] = path_parameters
        if request_body is not None:
            event['body'] = request_body
        return local_method(event, correlation_id)


def aws_post(url, request_body, correlation_id):
    aws_connection = get_secret('aws-connection')
    aws_api_key = aws_connection['aws-api-key']
    full_url = AWS_TEST_API + url
    headers = {'Content-Type': 'application/json', 'x-api-key': aws_api_key}
    try:
        response = post(full_url, data=request_body, headers=headers)
        return {'statusCode': response.status_code, 'body': response.text}
    except Exception as err:
        raise err


def test_patch(local_method, aws_url, path_parameters, request_body, correlation_id):
    if TEST_ON_AWS:
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
        return aws_patch(url, request_body, correlation_id)
    else:
        event = {}
        if path_parameters is not None:
            event['pathParameters'] = path_parameters
        if request_body is not None:
            event['body'] = request_body
        return local_method(event, correlation_id)


def aws_patch(url, request_body, correlation_id):
    aws_connection = get_secret('aws-connection')
    aws_api_key = aws_connection['aws-api-key']
    full_url = AWS_TEST_API + url
    headers = {'Content-Type': 'application/json', 'x-api-key': aws_api_key}
    try:
        response = patch(full_url, data=request_body, headers=headers)
        return {'statusCode': response.status_code, 'body': response.text}
    except Exception as err:
        raise err


def test_and_remove_now_datetime(test_case, entity_json, datetime_attribute_name, tolerance=10):
    datetime_string = entity_json[datetime_attribute_name]
    del entity_json[datetime_attribute_name]

    # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
    now = now_with_tz()
    datetime_value = parser.parse(datetime_string)
    difference = abs(now - datetime_value)
    test_case.assertLess(difference.seconds, tolerance)


def test_and_remove_new_uuid(test_case, entity_json):
    try:
        id = entity_json['id']
        del entity_json['id']
        test_case.assertTrue(uuid.UUID(id).version == 4)
    except KeyError:
        test_case.assertTrue(False, 'id missing')


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
                "country_code": row[12],
                "country_name": get_country_name(row[12]),
                "avatar_string": f'{row[5][0].upper()}{row[6][0].upper()}',
                "status": "new"
            }

            hubspot_id, _ = hs_client.post_new_user_to_crm(user_json, correlation_id=None)
            user_jsonpatch = [
                {'op': 'replace', 'path': '/crm_id', 'value': str(hubspot_id)},
            ]
            user.patch_user(user_json['id'], user_jsonpatch, now_with_tz(), correlation_id=None)


def clear_test_data(delete_notifications=False):
    """
    Clears all PostgreSQL database tables used by the test suite. Optionally deletes all notifications in AWS Dynamodb.

    Args:
        delete_notifications (bool): False by default. If set to True, notifications in Dynamodb are also deleted.
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
    if delete_notifications:
        delete_all_notifications()
