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

import uuid
from dateutil import parser
from requests import get, post, patch
from api.common.utilities import get_secret, now_with_tz, get_logger
from api.common.dev_config import TEST_ON_AWS, AWS_TEST_API


def test_get(local_method, aws_url, path_parameters, querystring_parameters, correlation_id):
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