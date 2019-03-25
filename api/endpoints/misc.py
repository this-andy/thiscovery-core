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
    from .common.utilities import ObjectDoesNotExistError, DetailedValueError, \
        get_correlation_id, get_logger, error_as_response_body, get_start_time, get_elapsed_ms
else:
    from common.utilities import ObjectDoesNotExistError, DetailedValueError, \
        get_correlation_id, get_logger, error_as_response_body, get_start_time, get_elapsed_ms


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


if __name__ == "__main__":
    # result = ping(None, None)

    error_id = 'none'
    # error_id = '4xx'
    # error_id = '5xx'
    # error_id = 'slow'
    # error_id = 'timeout'

    qsp = {'error_id': error_id}
    ev = {'queryStringParameters': qsp}
    result = raise_error_api(ev, None)

    print(result)
