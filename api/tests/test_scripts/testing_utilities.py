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

from requests import get, post, patch
from api.common.utilities import get_secret

TEST_ON_AWS = False


def test_get(local_method, aws_url, path_parameters, querystring_parameters, correlation_id):
    if TEST_ON_AWS:
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        else:
            url = aws_url
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
    full_url = 'https://test-api.thiscovery.org/v1/' + url
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
    full_url = 'https://test-api.thiscovery.org/v1/' + url
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
    full_url = 'https://test-api.thiscovery.org/v1/' + url
    headers = {'Content-Type': 'application/json', 'x-api-key': aws_api_key}
    try:
        response = patch(full_url, data=request_body, headers=headers)
        return {'statusCode': response.status_code, 'body': response.text}
    except Exception as err:
        raise err