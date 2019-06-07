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

from urllib.request import urlopen, Request, HTTPError
from http import HTTPStatus
from api.common.utilities import get_secret

TEST_ON_AWS = True

def test_get(local_method, aws_url, path_parameters, querystring_parameters, correlation_id):
    if TEST_ON_AWS:
        if path_parameters is not None:
            url = aws_url + '/' + path_parameters['id']
        elif querystring_parameters is not None:
            query_string = ''
            for param_name, param_value in querystring_parameters.items():
                if query_string == '':
                    query_string = '?'
                else:
                    query_string += ','
                query_string += param_name + '=' + param_value
            url = aws_url + '/' + query_string
        else:
            url = aws_url
        return aws_get(url, correlation_id)
    else:
        if path_parameters is not None:
            event = {'pathParameters': path_parameters}
        if querystring_parameters is not None:
            event = {'queryStringParameters': querystring_parameters}
        return local_method(event, correlation_id)


def aws_get(url, correlation_id):
    aws_connection = get_secret('aws-connection')
    aws_api_key = aws_connection['aws-api-key']
    full_url = 'https://test-api.thiscovery.org/v1/' + url
    headers = {'Content-Type': 'application/json', 'x-api-key': aws_api_key}
    try:
        req = Request(full_url, headers=headers)
        response = urlopen(req)
        return {'statusCode': response.status, 'body': response.read()}
    except HTTPError as err:
        if err.code == HTTPStatus.NOT_FOUND:
            return {'statusCode': HTTPStatus.NOT_FOUND, 'body': ''}
        else:
            raise err
    except Exception as err:
        raise err
