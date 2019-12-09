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

if 'api.endpoints' in __name__:
    from .common.pg_utilities import execute_query, execute_non_query
    from .common.utilities import ObjectDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
        validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz, get_start_time, get_elapsed_ms, \
        triggered_by_heartbeat, validate_uuid
    from .user import get_user_by_id
    # from .utils import validate_uuid

else:
    from common.pg_utilities import execute_query, execute_non_query
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

    base_sql = '''
      SELECT 
        id
      FROM public.projects_userexternalaccount
      WHERE
        user_id = %s AND external_system_id = %s
    '''

    return execute_query(base_sql, (str(user_id), str(external_system_id)), correlation_id)


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

    sql = '''INSERT INTO public.projects_userexternalaccount (
            id,
            created,
            modified,
            external_system_id,
            user_id,
            external_user_id,
            status
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s );'''

    execute_non_query(sql, (id, created, created, external_system_id, user_id, external_user_id, status), correlation_id)

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


def create_user_external_account_api(event, context):
    start_time = get_start_time()
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
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except (ObjectDoesNotExistError, DetailedIntegrityError, DetailedValueError) as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'elapsed_ms': get_elapsed_ms(start_time)})
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


if __name__ == "__main__":
    uea_json = {
        'external_system_id': 'e056e0bf-8d24-487e-a57b-4e812b40c4d8',
        'user_id': '35224bd5-f8a8-41f6-8502-f96e12d6ddde',
        'external_user_id': 'cc02'
        # 'status': 'active',
        # 'id': '9620089b-e9a4-46fd-bb78-091c8449d777',
        # 'created': '2018-06-13 14:15:16.171819+00'
    }
    correlation_id = None
    print(create_user_external_account(uea_json, correlation_id))

    # ev = {'body': json.dumps(uea_json)}
    # print(create_user_external_account_api(ev, None))

    # print (check_user_id_and_external_account('35224bd5-f8a8-41f6-8502-f96e12d6ddde', 'e056e0bf-8d24-487e-a57b-4e812b40c4d8', correlation_id))

    # print(validate_status('active'))
