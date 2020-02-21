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

import common.utilities as utils


@utils.lambda_wrapper
def ping(event, context):

    del event['logger']
    region = ''
    aws = ''

    try:
        region = os.environ['AWS_REGION']
        aws = os.environ['AWS_EXECUTION_ENV']
    except:
        pass

    # Hide potential sensitive data
    utils.obfuscate_data(event, ('headers', 'x-api-key'))
    utils.obfuscate_data(event, ('headers', 'X-Forwarded-For'))
    utils.obfuscate_data(event, ('multiValueHeaders', 'x-api-key'))
    utils.obfuscate_data(event, ('multiValueHeaders', 'X-Forwarded-For'))
    utils.obfuscate_data(event, ('requestContext', 'identity'))
    utils.obfuscate_data(event, ('requestContext', 'accountId'))

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

    return response


@utils.lambda_wrapper
def raise_error_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    try:
        params = event['queryStringParameters']
        error_id = params['error_id']
        logger.info('API call', extra={'error_id': error_id, 'correlation_id': correlation_id, 'event': event})

        errorjson = {'error_id': error_id, 'correlation_id': str(correlation_id)}
        msg = 'no error'

        if error_id == '4xx':
            msg = 'error triggered for testing purposes'
            raise utils.ObjectDoesNotExistError(msg, errorjson)
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

    except utils.ObjectDoesNotExistError as err:
        logger.error(err.as_response_body(correlation_id=correlation_id))
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body(correlation_id=correlation_id)}

    except utils.DetailedValueError as err:
        logger.error(err.as_response_body(correlation_id=correlation_id))
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body(correlation_id=correlation_id)}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": utils.error_as_response_body(errorMsg, correlation_id)}

    return response
