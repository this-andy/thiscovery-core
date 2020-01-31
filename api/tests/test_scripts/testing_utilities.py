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
import uuid
from dateutil import parser

import api.endpoints.user as user
from common.hubspot import HubSpotClient
from api.common.utilities import get_secret, now_with_tz, get_logger, get_country_name
from api.common.dev_config import TEST_ON_AWS, AWS_TEST_API


def _aws_request(method, url, params=None, data=None):
    full_url = AWS_TEST_API + url
    headers = {'Content-Type': 'application/json', 'x-api-key': get_secret('aws-connection')['aws-api-key']}
    try:
        response = requests.request(
            method=method,
            url=full_url,
            params=params,
            headers=headers,
            data=data,
        )
        return {'statusCode': response.status_code, 'body': response.text}
    except Exception as err:
        raise err


def aws_get(url, params):
    return _aws_request(method='GET', url=url, params=params)


def aws_post(url, request_body):
    return _aws_request(method='POST', url=url, data=request_body)


def aws_patch(url, request_body):
    return _aws_request(method='PATCH', url=url, data=request_body)


def _test_request(request_method, local_method, aws_url, path_parameters=None, querystring_parameters=None, request_body=None, correlation_id=None):
    logger = get_logger()

    test_on_aws = os.environ.get('TEST_ON_AWS')
    if test_on_aws is None:
        test_on_aws = TEST_ON_AWS
    elif test_on_aws.lower() == 'false':
        test_on_aws = False

    if test_on_aws:
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
        logger.info(f'Url passed to _aws_request: {url}', extra={'path_parameters': path_parameters, 'querystring_parameters': querystring_parameters})
        return _aws_request(method=request_method, url=url, params=querystring_parameters, data=request_body)
    else:
        event = {}
        if path_parameters is not None:
            event['pathParameters'] = path_parameters
        if querystring_parameters is not None:
            event['queryStringParameters'] = querystring_parameters
        if request_body is not None:
            event['body'] = request_body
        return local_method(event, correlation_id)


def test_get(local_method, aws_url, path_parameters, querystring_parameters, correlation_id=None):
    return _test_request('GET', local_method, aws_url, path_parameters=path_parameters,
                         querystring_parameters=querystring_parameters, correlation_id=correlation_id)


def test_post(local_method, aws_url, path_parameters, request_body, correlation_id):
    return _test_request('POST', local_method, aws_url, path_parameters=path_parameters, request_body=request_body, correlation_id=correlation_id)


def test_patch(local_method, aws_url, path_parameters, request_body, correlation_id):
    return _test_request('PATCH', local_method, aws_url, path_parameters=path_parameters, request_body=request_body, correlation_id=correlation_id)


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