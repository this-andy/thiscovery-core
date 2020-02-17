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
import uuid
from http import HTTPStatus

import common.utilities as utils
from common.pg_utilities import execute_query, execute_non_query
from common.sql_queries import CHECK_USER_ID_AND_EXTERNAL_ACCOUNT_SQL, CREATE_USER_EXTERNAL_ACCOUNT_SQL
from common.utilities import ObjectDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
    validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz, get_start_time, get_elapsed_ms, \
    triggered_by_heartbeat, validate_uuid
from user import get_user_by_id
# from utils import validate_uuid


STATUS_CHOICES = (
    'active',
    'closed',
)
DEFAULT_STATUS = 'active'


def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise DetailedValueError('invalid user_external_account status', errorjson)


def check_user_id_and_external_account(user_id, external_system_id, correlation_id):
    return execute_query(CHECK_USER_ID_AND_EXTERNAL_ACCOUNT_SQL, (str(user_id), str(external_system_id)), correlation_id)


def create_user_external_account(uea_json, correlation_id):
    # json MUST contain: external_system_id, user_id, external_user_id
    # json may OPTIONALLY include: id, created, status

    # extract mandatory data from json
    try:
        external_system_id = validate_uuid(uea_json['external_system_id'])
        user_id = validate_uuid(uea_json['user_id'])
        external_user_id = uea_json['external_user_id']
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise DetailedValueError('mandatory data missing', errorjson) from err

    # now process optional json data
    if 'id' in uea_json:
        try:
            id = validate_uuid(uea_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in uea_json:
        try:
            created = validate_utc_datetime(uea_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    if 'status' in uea_json:
        try:
            status = validate_status(uea_json['status'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        status = DEFAULT_STATUS

    # check external account does not already exist
    existing = check_user_id_and_external_account(user_id, external_system_id, correlation_id)
    if len(existing) > 0:
        errorjson = {'user_id': user_id, 'external_system_id': external_system_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_external_account already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    existing_user = get_user_by_id(user_id, correlation_id)
    if len(existing_user) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    execute_non_query(CREATE_USER_EXTERNAL_ACCOUNT_SQL, (id, created, created, external_system_id, user_id, external_user_id, status), correlation_id)

    new_user_external_account = {
        'id': id,
        'created': created,
        'modified': created,
        'external_system_id': external_system_id,
        'user_id': user_id,
        'external_user_id': external_user_id,
        'status': status,
    }

    return new_user_external_account


@utils.time_execution
def create_user_external_account_api(event, context):
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        uea_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'uea_json': uea_json, 'correlation_id': correlation_id, 'event': event})

        new_user_external_account = create_user_external_account(uea_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_external_account)}

    except DuplicateInsertError as err:
        logger.error(err.as_response_body())
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except (ObjectDoesNotExistError, DetailedIntegrityError, DetailedValueError) as err:
        logger.error(err.as_response_body())
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    return response


def get_or_create_user_external_account(user_id, external_system_id, correlation_id):
    # to do - add automated tests for this if ever used

    raise Exception('This method needs to be reviewed before use - see TP ')
    existing = check_user_id_and_external_account(user_id, external_system_id, correlation_id)
    if len(existing) > 0:
        # already exists - return id
        return existing[0]['id']
    else:
        # if not then call external system to get id and create record
        external_user_id = get_user_id_from_external_system(external_system_id, user_id, correlation_id)

        # if call to external system fails then return 503
        # todo - implement this
        # if success then create local record of info
        uea_json = {
            'external_system_id': external_system_id,
            'user_id': user_id,
            'external_user_id': external_user_id
        }
        user_external_account = create_user_external_account(uea_json, correlation_id)
        return user_external_account


def get_user_id_from_external_system(external_system_id, user_id, correlation_id):
    return None
