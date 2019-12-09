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
import time
from http import HTTPStatus

if 'api.endpoints' in __name__:
    from .common.utilities import ObjectDoesNotExistError, DetailedValueError, get_correlation_id, get_logger, error_as_response_body, get_start_time, \
        get_elapsed_ms, obfuscate_data
else:
    from common.utilities import ObjectDoesNotExistError, DetailedValueError, get_correlation_id, get_logger, error_as_response_body, get_start_time, \
        get_elapsed_ms, obfuscate_data


def ping(event, context):
    start_time = get_start_time()
    logger = get_logger()

    region = ''
    aws = ''

    try:
        region = os.environ['AWS_REGION']
        aws = os.environ['AWS_EXECUTION_ENV']
    except:
        pass

    # Hide potential sensitive data
    obfuscate_data(event, ('headers', 'x-api-key'))
    obfuscate_data(event, ('headers', 'X-Forwarded-For'))
    obfuscate_data(event, ('multiValueHeaders', 'x-api-key'))
    obfuscate_data(event, ('multiValueHeaders', 'X-Forwarded-For'))
    obfuscate_data(event, ('requestContext', 'identity'))
    obfuscate_data(event, ('requestContext', 'accountId'))

    body = {
        "message": "Response from THIS Institute citizen science API",
        "region": region,
        "aws": aws,
        "input": event
    }

    response = {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(body)
    }

    correlation_id = get_correlation_id(event)
    logger.info('API call', extra={'correlation_id': correlation_id, 'event': event, 'elapsed_ms': get_elapsed_ms(start_time)})

    return response


def raise_error_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    try:
        params = event['queryStringParameters']
        error_id = params['error_id']
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'error_id': error_id, 'correlation_id': correlation_id, 'event': event})

        errorjson = {'error_id': error_id, 'correlation_id': str(correlation_id)}
        msg = 'no error'

        if error_id == '4xx':
            msg = 'error triggered for testing purposes'
            raise ObjectDoesNotExistError(msg, errorjson)
        elif error_id == '5xx':
            msg = 'error triggered for testing purposes'
            raise Exception(msg)
        elif error_id == 'slow':
            msg = 'slow response triggered for testing purposes'
            time.sleep(2)  # this should trigger lambda duration alarm
        elif error_id == 'timeout':
            msg = 'timeout response triggered for testing purposes'
            time.sleep(10)  # this should trigger lambda timeout

        response = {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps(msg)
        }

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response


def sqs_send_api(event, context):
    message_json = json.loads(event['body'])
    message_text = message_json['text']
    message_attributes = message_json['attributes']

    sqs_send(message_text, message_attributes)


def sqs_send_example():
    logger = get_logger()

    message_body = (
            'Information about current NY Times fiction bestseller for '
            'week of 12/11/2016.'
        )
    message_attributes = {
            'Title': {
                'DataType': 'String',
                'StringValue': 'The Whistler'
            },
            'Author': {
                'DataType': 'String',
                'StringValue': 'John Grisham'
            },
            'WeeksOn': {
                'DataType': 'Number',
                'StringValue': '6'
            }
        }
    result = sqs_send(message_body, message_attributes)

    logger.info('sqs_send_example', extra={'result': str(result)})

    return result


if __name__ == "__main__":
    # ev = {
    #     "resource": "/v1/ping",
    #     "path": "/v1/ping",
    #     "httpMethod": "GET",
    #     "headers": {
    #         "Accept": "*/*",
    #         "accept-encoding": "gzip, deflate",
    #         "cache-control": "no-cache",
    #         "Host": "dev-api.thiscovery.org",
    #         "Postman-Token": "4522af16-c8aa-49b8-aae2-db2320e8a44b",
    #         "User-Agent": "PostmanRuntime/7.4.0",
    #         "X-Amzn-Trace-Id": "Root=1-5c98eead-5a16e9b022c4b0e834876ca0",
    #         "x-api-key": "test-ApSCXlbiB1uMhX3sg7XxgN2Aai3uW5OLPU0",
    #         "X-Forwarded-For": "192.168.100.57",
    #         "X-Forwarded-Port": "443",
    #         "X-Forwarded-Proto": "https"
    #     },
    #     "multiValueHeaders": {
    #         "Accept": [
    #             "*/*"
    #         ],
    #         "accept-encoding": [
    #             "gzip, deflate"
    #         ],
    #         "cache-control": [
    #             "no-cache"
    #         ],
    #         "Host": [
    #             "dev-api.thiscovery.org"
    #         ],
    #         "Postman-Token": [
    #             "4522af16-c8aa-49b8-aae2-db2320e8a44b"
    #         ],
    #         "User-Agent": [
    #             "PostmanRuntime/7.4.0"
    #         ],
    #         "X-Amzn-Trace-Id": [
    #             "Root=1-5c98eead-5a16e9b022c4b0e834876ca0"
    #         ],
    #         "x-api-key": [
    #             "test-ApSCXlbiB1uMhX3sg7XxgN2Aai3uW5OLPU0"
    #         ],
    #         "X-Forwarded-For": [
    #             "192.168.100.57"
    #         ],
    #         "X-Forwarded-Port": [
    #             "443"
    #         ],
    #         "X-Forwarded-Proto": [
    #             "https"
    #         ]
    #     },
    #     "queryStringParameters": None,
    #     "multiValueQueryStringParameters": None,
    #     "pathParameters": None,
    #     "stageVariables": None,
    #     "requestContext": {
    #         "resourceId": "mm6l6n",
    #         "resourcePath": "/v1/ping",
    #         "httpMethod": "GET",
    #         "extendedRequestId": "XGo7KHBDjoEFapA=",
    #         "requestTime": "25/Mar/2019:15:07:25 +0000",
    #         "path": "/v1/ping",
    #         "accountId": "1234567890",
    #         "protocol": "HTTP/1.1",
    #         "stage": "dev",
    #         "domainPrefix": "dev-api",
    #         "requestTimeEpoch": 1553526445814,
    #         "requestId": "b306299f-4f0f-11e9-a8c6-19f48fc11706",
    #         "identity": {
    #             "cognitoIdentityPoolId": None,
    #             "cognitoIdentityId": None,
    #             "apiKey": "test-ApSCXlbiB1uMhX3sg7XxgN2Aai3uW5OLPU0",
    #             "cognitoAuthenticationType": None,
    #             "userArn": None,
    #             "apiKeyId": "ujtgn3be02",
    #             "userAgent": "PostmanRuntime/7.4.0",
    #             "accountId": None,
    #             "caller": None,
    #             "sourceIp": "192.168.100.57",
    #             "accessKey": None,
    #             "cognitoAuthenticationProvider": None,
    #             "user": None
    #         },
    #         "domainName": "dev-api.thiscovery.org",
    #         "apiId": "3dquxzv0a3"
    #     },
    #     "body": None,
    #     "isBase64Encoded": False
    # }
    #
    # obfuscate_data(ev, ('headers', 'x-api-key'))
    # obfuscate_data(ev, ('headers', 'X-Forwarded-For'))
    # obfuscate_data(ev, ('multiValueHeaders', 'x-api-key'))
    # obfuscate_data(ev, ('multiValueHeaders', 'X-Forwarded-For'))
    # obfuscate_data(ev, ('requestContext', 'identity'))
    #
    # print(ev)
    # result = ping(ev, None)

    # error_id = 'none'
    # error_id = '4xx'
    # error_id = '5xx'
    # error_id = 'slow'
    # error_id = 'timeout'

    # qsp = {'error_id': error_id}
    # ev = {'queryStringParameters': qsp}
    # result = raise_error_api(ev, None)

    # print(result)

    result = sqs_send_example()
    print(result)
