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
from datetime import timedelta
from jsonpatch import JsonPatch, JsonPatchException

import common.utilities as utils
from common.pg_utilities import execute_query, execute_jsonpatch, execute_non_query, new_correlation_id
from common.sql_queries import BASE_USER_SELECT_SQL, GET_USER_BY_EXT_USER_PROJECT_ID_SQL, CREATE_USER_SQL, VALIDATE_USER_EMAIL_SQL
from common.utilities import get_correlation_id, get_logger, DetailedValueError, DuplicateInsertError, ObjectDoesNotExistError, \
    PatchInvalidJsonError, PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, error_as_response_body, validate_utc_datetime, \
    now_with_tz, get_start_time, get_elapsed_ms, triggered_by_heartbeat, get_country_name, append_country_name_to_list, append_country_name, validate_uuid
from common.entity_update import EntityUpdate
# from utils import validate_uuid
from common.notification_send import notify_new_user_registration, notify_user_login


def validate_status(s):
    return s


def append_avatar_to_list(user_list):
    for user in user_list:
        append_avatar(user)
    return user_list


def append_avatar(user):
    try:
        first_name = user['first_name']
        last_name = user['last_name']
        if len(first_name) == 0:
            avatar_string = last_name[0:2]
        elif len(last_name) == 0:
            avatar_string = first_name[0:2]
        else:
            avatar_string = first_name[0] + last_name[0]
    except:
        avatar_string = '??'
    user['avatar_string'] = avatar_string
    return user


def append_calculated_properties_to_list(user_list):
    user_list = append_country_name_to_list(user_list)
    user_list = append_avatar_to_list(user_list)
    return user_list


def append_calculated_properties(user):
    append_country_name(user)
    append_avatar(user)
    return user


def get_user_by_ext_user_project_id(ext_user_project_id, correlation_id=None):
    try:
        ext_user_project_id = validate_uuid(ext_user_project_id)
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    user_json = execute_query(GET_USER_BY_EXT_USER_PROJECT_ID_SQL, (str(ext_user_project_id),), correlation_id)

    return append_calculated_properties_to_list(user_json)


def get_user_by_id(user_id, correlation_id=None):

    try:
        user_id = validate_uuid(user_id)
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    sql_where_clause = " WHERE id = %s"

    user_json = execute_query(BASE_USER_SELECT_SQL + sql_where_clause, (str(user_id),), correlation_id)

    return append_calculated_properties_to_list(user_json)


def get_user_by_id_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        correlation_id = get_correlation_id(event)
        user_id = event['pathParameters']['id']
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})

        result = get_user_by_id(user_id, correlation_id)

        if len(result) > 0:
            user_json = result[0]
            response = {"statusCode": HTTPStatus.OK, "body": json.dumps(user_json)}

            login_info = {
                'email': user_json['email'],
                'user_id': user_id,
                'login_datetime': str(now_with_tz())
            }
            notify_user_login(login_info, correlation_id)

        else:
            errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

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


def get_user_by_email(user_email, correlation_id):

    sql_where_clause = " WHERE email = %s"

    user_json = execute_query(BASE_USER_SELECT_SQL + sql_where_clause, (str(user_email),), correlation_id)

    return append_calculated_properties_to_list(user_json)


@utils.time_execution
def get_user_by_email_api(event, context):
    """
    Handler for Lambda function supporting the /v1/user API endpoint. Supports retrieval of user info by email or ext_user_project_id

    Args:
        event (dict): event['queryStringParameters'] may contain either an 'email' or 'ext_user_project_id' parameter, but not both.
        context:

    Returns:
    """
    logger = get_logger()
    correlation_id = None
    logger.info('debugging', extra={'event': event})

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        correlation_id = get_correlation_id(event)
        parameters = event['queryStringParameters']

        if not parameters:  # e.g. parameters is None or an empty dict
            errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
            raise DetailedValueError('This endpoint requires one query parameter (email or ext_user_project_id); none were found', errorjson)
        else:
            user_email = parameters.get('email')
            ext_user_project_id = parameters.get('ext_user_project_id')

        if user_email and ext_user_project_id:
            errorjson = {'user_email': user_email, 'ext_user_project_id': ext_user_project_id, 'correlation_id': str(correlation_id)}
            raise DetailedValueError('Please query by either email or ext_user_project_id, but not both', errorjson)
        elif user_email:
            logger.info('API call', extra={'user_email': user_email, 'correlation_id': correlation_id, 'event': event})
            result = get_user_by_email(user_email, correlation_id)
        elif ext_user_project_id:
            logger.info('API call', extra={'ext_user_project_id': ext_user_project_id, 'correlation_id': correlation_id, 'event': event})
            result = get_user_by_ext_user_project_id(ext_user_project_id, correlation_id)
        else:
            errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
            raise DetailedValueError('Query parameters invalid', errorjson)

        if len(result) > 0:
            response = {"statusCode": HTTPStatus.OK, "body": json.dumps(result[0])}
        else:
            errorjson = {'user_email': user_email, 'ext_user_project_id': ext_user_project_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    return response


def patch_user(id_to_update, patch_json, modified_time=now_with_tz(), correlation_id=new_correlation_id()):
    """

    Args:
        id_to_update:
        patch_json:
        modified_time:
        correlation_id:

    Returns:
        Total number of rows updated in RDS database

    """
    mappings = {
        'email': {'table_name': 'public.projects_user', 'column_name': 'email'},
        'email_address_verified': {'table_name': 'public.projects_user', 'column_name': 'email_address_verified'},
        'title': {'table_name': 'public.projects_user', 'column_name': 'title'},
        'first_name': {'table_name': 'public.projects_user', 'column_name': 'first_name'},
        'last_name': {'table_name': 'public.projects_user', 'column_name': 'last_name'},
        'auth0_id': {'table_name': 'public.projects_user', 'column_name': 'auth0_id'},
        'status': {'table_name': 'public.projects_user', 'column_name': 'status'},
        'country_code': {'table_name': 'public.projects_user', 'column_name': 'country_code'},
        'crm_id': {'table_name': 'public.projects_user', 'column_name': 'crm_id'},
    }

    id_column = 'id'

    return execute_jsonpatch(id_column, id_to_update, mappings, patch_json, modified_time, correlation_id)


def create_user_entity_update(user_id, user_jsonpatch, modified, correlation_id):
    try:
        original_user_list = get_user_by_id(user_id, correlation_id)
        original_user = original_user_list[0]
        return EntityUpdate('user', original_user, user_jsonpatch, modified, correlation_id)
    except IndexError as ex:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)
    except JsonPatchException as ex:
        errorjson = {'user_jsonpatch': user_jsonpatch.to_string(), 'correlation_id': str(correlation_id)}
        raise PatchInvalidJsonError('invalid jsonpatch', errorjson)


def patch_user_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        correlation_id = get_correlation_id(event)
        # get info supplied to api call
        user_id = event['pathParameters']['id']
        user_jsonpatch = JsonPatch.from_string(event['body'])

        logger.info('API call', extra={'user_id': user_id, 'user_jsonpatch': user_jsonpatch, 'correlation_id': correlation_id, 'event': event})

        modified_time = now_with_tz()

        # create an audit record of update, inc 'undo' patch
        entity_update = create_user_entity_update(user_id, user_jsonpatch, modified_time, correlation_id)

        patch_user(user_id, user_jsonpatch, modified_time, correlation_id)

        response = {"statusCode": HTTPStatus.NO_CONTENT, "body": json.dumps('')}

        # on successful update save audit record
        entity_update.save()

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except (PatchAttributeNotRecognisedError, PatchOperationNotSupportedError, PatchInvalidJsonError, DetailedValueError) as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'elapsed_ms': get_elapsed_ms(start_time)})

    return response


# User create JSON should look like this:
#   {
#     "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
#     "created": "2018-08-21T11:16:56+01:00",
#     "email": "sw@email.addr",
#     "title": "Mr",
#     "first_name": "Steven",
#     "last_name": "Walcorn",
#     "auth0_id": "1234abcd",
#     "status": "new"
#   }

def create_user(user_json, correlation_id):
    # json MUST contain: email, first_name, last_name, status
    # json may OPTIONALLY include: id, title, created, auth0_id
    # note that users will always be created with email_address_verified = false

    # extract mandatory data from json
    try:
        email = user_json['email']
        first_name = user_json['first_name']
        last_name = user_json['last_name']
        status = validate_status(user_json['status'])
        country_code = user_json['country_code']
        get_country_name(country_code)
        # looking up the name is a way of validating the code - an invalid code will raise an error
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err


    # now process optional json data
    if 'id' in user_json:
        try:
            id = validate_uuid(user_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in user_json:
        try:
            created = validate_utc_datetime(user_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    if 'auth0_id' in user_json:
        auth0_id = user_json['auth0_id']
    else:
        auth0_id = None

    if 'title' in user_json:
        title = user_json['title']
    else:
        title = None

    # set up default values
    email_address_verified = False
    email_verification_token = str(uuid.uuid4())
    email_verification_expiry = str(now_with_tz() + timedelta(hours=24))

    existing_user = get_user_by_id(id, correlation_id)
    if len(existing_user) > 0:
        errorjson = {'id': id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user already exists', errorjson)



    params = (id, created, created, email, email_address_verified, email_verification_token, email_verification_expiry, title, first_name, last_name, country_code, auth0_id, status)
    execute_non_query(CREATE_USER_SQL, params, correlation_id)

    new_user = {
        'id': id,
        'created': created,
        'modified': created,        
        'email': email,
        'email_address_verified': email_address_verified,
        'title': title,
        'first_name': first_name,
        'last_name': last_name,
        'auth0_id': auth0_id,
        'crm_id': None,
        'country_code': country_code,
        'status': status,
    }

    new_user = append_calculated_properties(new_user)

    try:
        notify_new_user_registration(new_user, correlation_id)
    except Exception as ex:
        raise ex

    return new_user


def create_user_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        user_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_json': user_json, 'correlation_id': correlation_id, 'event': event})

        new_user = create_user(user_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user)}

    except DuplicateInsertError as err:
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response


def validate_user_email(user_id, email_verification_token_to_check, correlation_id):
    result = execute_query(VALIDATE_USER_EMAIL_SQL, (str(user_id),), correlation_id)
