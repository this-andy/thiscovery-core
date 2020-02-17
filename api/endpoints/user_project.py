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

import uuid
import json
from http import HTTPStatus

import common.utilities as utils
from common.pg_utilities import execute_query, execute_non_query
from common.sql_queries import LIST_USER_PROJECTS_SQL, GET_EXISTING_USER_PROJECT_ID_SQL, CREATE_USER_PROJECT_SQL
from common.utilities import ObjectDoesNotExistError, DuplicateInsertError, DetailedIntegrityError, DetailedValueError, \
    validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz, get_start_time, get_elapsed_ms, \
    triggered_by_heartbeat, validate_uuid
from user import get_user_by_id
# from utils import validate_uuid


STATUS_CHOICES = (
    'active',
    'complete',
    'withdrawn',
)
DEFAULT_STATUS = 'active'

# this line is only here to prevent PyCharm from marking these global variables as unresolved; they are reassigned in create_user_project function below
ext_user_project_id, created, status = None, None, None

def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise DetailedValueError('invalid user_project status', errorjson)

def list_user_projects(user_id, correlation_id):

    try:
        user_id = validate_uuid(user_id)
    except DetailedValueError:
        raise

    # check that user exists
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    return execute_query(LIST_USER_PROJECTS_SQL, (str(user_id),), correlation_id)


@utils.time_execution
def list_user_projects_api(event, context):
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        params = event['queryStringParameters']
        user_id = params['user_id']  # all public id are uuids
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})

        response = {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps(list_user_projects(user_id, correlation_id))
        }

    except ObjectDoesNotExistError as err:
        logger.error(err.as_response_body())
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except DetailedValueError as err:
        logger.error(err.as_response_body())
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    return response


def get_existing_user_project_id(user_id, project_id, correlation_id):
    return execute_query(GET_EXISTING_USER_PROJECT_ID_SQL, (str(project_id), str(user_id)), correlation_id)


def create_user_project(up_json, correlation_id, do_nothing_if_exists=False):
    """
    Inserts new UserProject row in thiscovery db

    Args:
        up_json: must contain user_id and project_id; may optionally include id, created, status, ext_user_project_id
        correlation_id:
        do_nothing_if_exists:

    Returns:
    """
    # extract mandatory data from json
    try:
        user_id = validate_uuid(up_json['user_id'])    # all public id are uuids
        project_id = validate_uuid(up_json['project_id'])
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise DetailedValueError('mandatory data missing', errorjson) from err

    # now process optional json data
    optional_fields_name_default_and_validator = [
        ('ext_user_project_id', str(uuid.uuid4()), validate_uuid),
        ('created', str(now_with_tz()), validate_utc_datetime),
        ('status', DEFAULT_STATUS, validate_status),
    ]
    for variable_name, default_value, validating_func in optional_fields_name_default_and_validator:
        if variable_name in up_json:
            try:
                globals()[variable_name] = validating_func(up_json[variable_name])  # https://stackoverflow.com/a/4687672
            except DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            globals()[variable_name] = default_value

    # id shadows builtin function, so treat if separately (using globals() approach above would overwrite that function)
    if 'id' in up_json:
        try:
            id = validate_uuid(up_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    # check external account does not already exist
    existing = get_existing_user_project_id(user_id, project_id, correlation_id)
    if len(existing) > 0:
        if do_nothing_if_exists:
            return existing[0]
        else:
            errorjson = {'user_id': user_id, 'project_id': project_id, 'correlation_id': str(correlation_id)}
            raise DuplicateInsertError('user_project already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    execute_non_query(CREATE_USER_PROJECT_SQL, (id, created, created, user_id, project_id, status, ext_user_project_id), correlation_id)

    new_user_project = {
        'id': id,
        'created': created,
        'modified': created,
        'user_id': user_id,
        'project_id': project_id,
        'status': status,
        'ext_user_project_id': ext_user_project_id,
    }

    return new_user_project


@utils.time_execution
def create_user_project_api(event, context):
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        up_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'up_json': up_json, 'correlation_id': correlation_id, 'event': event})

        new_user_project = create_user_project(up_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_project)}

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


def create_user_project_if_not_exists(user_id, project_id, correlation_id):
    up_json = {
        'user_id': user_id,
        'project_id': project_id,
        'status': 'active'
    }
    return create_user_project(up_json, correlation_id, True)
