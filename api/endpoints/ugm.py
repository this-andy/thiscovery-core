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
from http import HTTPStatus

print ('name:' + __name__)
if 'api.endpoints' in __name__:
    from .common.utilities import get_correlation_id, get_logger, error_as_response_body, ObjectDoesNotExistError, get_start_time, get_elapsed_ms, \
        triggered_by_heartbeat, DetailedValueError, DuplicateInsertError
    from .user_group_membership import UserGroupMembership
    from .user import get_user_by_id
else:
    from common.utilities import get_correlation_id, get_logger, error_as_response_body, ObjectDoesNotExistError, get_start_time, get_elapsed_ms, \
        triggered_by_heartbeat, DetailedValueError, DuplicateInsertError
    logger = get_logger()
    logger.info('name:' + __name__)
    try:
        from user_group_membership import UserGroupMembership
        from user import get_user_by_id
    except Exception as ex:
        error_msg = ex.args[0]
        logger.error(error_msg, extra={'correlation_id': ''})
#

def create_user_group_membership_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None
    #
    # if triggered_by_heartbeat(event):
    #     logger.info('API call (heartbeat)', extra={'event': event})
    #     return

    try:
        ugm_json = json.loads(event['body'])
        # correlation_id = get_correlation_id(event)
        # logger.info('API call', extra={'ugm_json': ugm_json, 'correlation_id': correlation_id, 'event': event})
        #
        # ugm = UserGroupMembership.new_from_json(ugm_json, correlation_id)
        # response = {"statusCode": HTTPStatus.CREATED, "body": ugm.to_json()}
        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps({"test": "value"})}

    # except DuplicateInsertError as err:
    #     response = {"statusCode": HTTPStatus.NO_CONTENT, "body": err.as_response_body()}

    # except ObjectDoesNotExistError as err:
    #     response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    # except DetailedValueError as err:
    #     response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        error_msg = ex.args[0]
        # logger.error(error_msg, extra={'correlation_id': correlation_id})
        # response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(error_msg, correlation_id)}
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": '{"error": "value"}'}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response

