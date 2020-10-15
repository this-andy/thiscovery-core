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

import thiscovery_lib.utilities as utils
from common.pg_utilities import execute_query, execute_non_query
from common.sql_queries import LIST_USER_PROJECTS_SQL, GET_EXISTING_USER_PROJECT_ID_SQL, CREATE_USER_PROJECT_SQL
from user import get_user_by_id
# from utils import validate_uuid


STATUS_CHOICES = (
    'active',
    'complete',
    'withdrawn',
)
DEFAULT_STATUS = 'active'

# this line is only here to prevent PyCharm from marking these global variables as unresolved; they are reassigned in create_user_project function below
anon_project_specific_user_id, created, status = None, None, None


def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise utils.DetailedValueError('invalid user_project status', errorjson)


def list_user_projects(user_id, correlation_id):

    try:
        user_id = utils.validate_uuid(user_id)
    except utils.DetailedValueError:
        raise

    # check that user exists
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)

    return execute_query(LIST_USER_PROJECTS_SQL, (str(user_id),), correlation_id)


@utils.lambda_wrapper
@utils.api_error_handler
def list_user_projects_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    params = event['queryStringParameters']
    user_id = params['user_id']  # all public id are uuids
    logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(list_user_projects(user_id, correlation_id))
    }


def get_existing_user_project_id(user_id, project_id, correlation_id):
    return execute_query(GET_EXISTING_USER_PROJECT_ID_SQL, (str(project_id), str(user_id)), correlation_id)


def create_user_project(up_json, correlation_id, do_nothing_if_exists=False):
    """
    Inserts new UserProject row in thiscovery db

    Args:
        up_json: must contain user_id and project_id; may optionally include id, created, status, anon_project_specific_user_id
        correlation_id:
        do_nothing_if_exists:

    Returns:
    """
    # extract mandatory data from json
    try:
        user_id = utils.validate_uuid(up_json['user_id'])    # all public id are uuids
        project_id = utils.validate_uuid(up_json['project_id'])
    except utils.DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('mandatory data missing', errorjson) from err

    # now process optional json data
    optional_fields_name_default_and_validator = [
        ('anon_project_specific_user_id', str(uuid.uuid4()), utils.validate_uuid),
        ('created', str(utils.now_with_tz()), utils.validate_utc_datetime),
        ('status', DEFAULT_STATUS, validate_status),
    ]
    for variable_name, default_value, validating_func in optional_fields_name_default_and_validator:
        if variable_name in up_json:
            try:
                globals()[variable_name] = validating_func(up_json[variable_name])  # https://stackoverflow.com/a/4687672
            except utils.DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            globals()[variable_name] = default_value

    # id shadows builtin function, so treat if separately (using globals() approach above would overwrite that function)
    if 'id' in up_json:
        try:
            id = utils.validate_uuid(up_json['id'])
        except utils.DetailedValueError as err:
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
            raise utils.DuplicateInsertError('user_project already exists', errorjson)

    # lookup user id (needed for insert) for user uuid (supplied in json)
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)

    execute_non_query(CREATE_USER_PROJECT_SQL, (id, created, created, user_id, project_id, status, anon_project_specific_user_id), correlation_id)

    new_user_project = {
        'id': id,
        'created': created,
        'modified': created,
        'user_id': user_id,
        'project_id': project_id,
        'status': status,
        'anon_project_specific_user_id': anon_project_specific_user_id,
    }

    return new_user_project


@utils.lambda_wrapper
@utils.api_error_handler
def create_user_project_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    up_json = json.loads(event['body'])
    logger.info('API call', extra={'up_json': up_json, 'correlation_id': correlation_id, 'event': event})
    new_user_project = create_user_project(up_json, correlation_id)
    return {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_project)}


def create_user_project_if_not_exists(user_id, project_id, correlation_id=None):
    up_json = {
        'user_id': user_id,
        'project_id': project_id,
        'status': 'active'
    }
    return create_user_project(up_json, correlation_id, True)
