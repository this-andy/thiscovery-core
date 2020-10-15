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

import thiscovery_lib.utilities as utils


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
@utils.api_error_handler
def raise_error_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

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

    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(msg)
    }


def call_raise_error_on_prod_and_staging(event, context):
    api_base = {
        utils.PRODUCTION_ENV_NAME: 'https://api.thiscovery.org/',
        utils.STAGING_ENV_NAME: f'https://{utils.STAGING_ENV_NAME}-api.thiscovery.org/',
    }
    env_name = utils.namespace2name(utils.get_aws_namespace())
    if env_name in [utils.PRODUCTION_ENV_NAME, utils.STAGING_ENV_NAME]:
        utils.aws_post('v1/raise-error', api_base[env_name], params='error_id=5xx')
        message = f'{env_name} is either {utils.PRODUCTION_ENV_NAME} or {utils.STAGING_ENV_NAME}; called raise-error API endpoint'
    else:
        message = f'{env_name} is not {utils.PRODUCTION_ENV_NAME} nor {utils.STAGING_ENV_NAME}; exiting without raising an error'
    return message


@utils.lambda_wrapper
@utils.api_error_handler
def log_request_api(event, context):
    logger = event['logger']

    # params = event['queryStringParameters']
    # body = event['body']
    logger.info('API call', extra={'event': event})
    return {
        "statusCode": HTTPStatus.OK,
    }