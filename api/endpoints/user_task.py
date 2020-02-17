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

from common.pg_utilities import execute_query, execute_non_query
from common.sql_queries import GET_USER_TASK_SQL, UPDATE_USER_TASK_PROGRESS_INFO_SQL, LIST_USER_TASKS_SQL, CHECK_IF_USER_TASK_EXISTS_SQL, \
    CREATE_USER_TASK_SQL
from common.utilities import DuplicateInsertError, ObjectDoesNotExistError, DetailedValueError, DetailedIntegrityError, \
    validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz, get_start_time, get_elapsed_ms, \
    triggered_by_heartbeat, validate_uuid, non_prod_env_url_param, create_url_params
from user import get_user_by_id
from project import get_project_task
from user_project import create_user_project_if_not_exists
from common.notification_send import notify_new_task_signup


STATUS_CHOICES = (
    'active',
    'complete',
    'withdrawn',
)
DEFAULT_STATUS = 'active'

# this line is only here to prevent PyCharm from marking these global variables as unresolved; they are reassigned in create_user_project function below
ext_user_task_id, created, status = None, None, None


def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise DetailedValueError('invalid user_task status', errorjson)


def get_user_task(ut_id, correlation_id):
    result = execute_query(GET_USER_TASK_SQL, (str(ut_id),), correlation_id)
    return result


def filter_user_tasks_by_project_task_id(user_id, project_task_id, correlation_id=None):
    """
    Returns user_task related to user_id and project_task_id or None
    """
    result = [t for t in list_user_tasks(user_id, correlation_id) if t['project_task_id'] == project_task_id]
    if result:
        return result[0]
    return None


def list_user_tasks(user_id, correlation_id):

    try:
        user_id = validate_uuid(user_id)
    except DetailedValueError:
        raise

    # check that user exists
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    return execute_query(LIST_USER_TASKS_SQL, (str(user_id),), correlation_id)


def list_user_tasks_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        params = event['queryStringParameters']
        user_id = params['user_id']
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id})

        response = {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps(list_user_tasks(user_id, correlation_id))
        }

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response',
                extra={'response': response, 'correlation_id': correlation_id, 'event': event, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response


def check_if_user_task_exists(user_id, project_task_id, correlation_id):
    return execute_query(CHECK_IF_USER_TASK_EXISTS_SQL, (str(user_id), str(project_task_id)), correlation_id, False)


def create_user_task(ut_json, correlation_id):
    """
    Inserts new UserTask row in thiscovery db

    Args:
        ut_json: must contain user_id, project_task_id and consented; may optionally include id, created, status, ext_user_task_id
        correlation_id:

    Returns:
    """
    # extract mandatory data from json
    try:
        user_id = validate_uuid(ut_json['user_id'])
        project_task_id = validate_uuid(ut_json['project_task_id'])
        consented = validate_utc_datetime(ut_json['consented'])
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise DetailedValueError('mandatory data missing', errorjson) from err

    # now process optional json data
    optional_fields_name_default_and_validator = [
        ('ext_user_task_id', str(uuid.uuid4()), validate_uuid),
        ('created', str(now_with_tz()), validate_utc_datetime),
        ('status', DEFAULT_STATUS, validate_status),
    ]
    for variable_name, default_value, validating_func in optional_fields_name_default_and_validator:
        if variable_name in ut_json:
            try:
                globals()[variable_name] = validating_func(ut_json[variable_name])  # https://stackoverflow.com/a/4687672
            except DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            globals()[variable_name] = default_value

    # id shadows builtin function, so treat if separately (using globals() approach above would overwrite that function)
    if 'id' in ut_json:
        try:
            id = validate_uuid(ut_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    # get corresponding project_task...
    project_task = get_project_task(project_task_id, correlation_id)
    try:
        project_id = project_task[0]['project_id']
        base_url = project_task[0]['base_url']
        task_provider_name = project_task[0]['task_provider_name']
        external_task_id = project_task[0]['external_task_id']
    except:
        errorjson = {'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise DetailedIntegrityError('project_task does not exist', errorjson)

    # create_user_external_account_if_not_exists(user_id, project_task['external_system_id'], correlation_id)

    user_project = create_user_project_if_not_exists(user_id, project_id, correlation_id)
    user_project_id = user_project['id']

    # check external account does not already exist
    existing = check_if_user_task_exists(user_id, project_task_id, correlation_id)
    # if int(existing[0][0]) > 0:
    if len(existing) > 0:
        errorjson = {'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_task already exists', errorjson)

    execute_non_query(CREATE_USER_TASK_SQL, (id, created, created, user_project_id, project_task_id, status, consented, ext_user_task_id), correlation_id)

    url = base_url + create_url_params(user_id, id, external_task_id) + non_prod_env_url_param()

    new_user_task = {
        'id': id,
        'created': created,
        'modified': created,
        'user_id': user_id,
        'user_project_id': user_project_id,
        'project_task_id': project_task_id,
        'task_provider_name': task_provider_name,
        'url': url,
        'status': status,
        'consented': consented,
        'ext_user_task_id': ext_user_task_id,
    }

    notify_new_task_signup(new_user_task, correlation_id)

    return new_user_task


def create_user_task_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        ut_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'ut_json': ut_json, 'correlation_id': correlation_id})

        new_user_task = create_user_task(ut_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_task)}

    except DuplicateInsertError as err:
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except (DetailedIntegrityError, DetailedValueError) as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        error_msg = ex.args[0]
        logger.error(error_msg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(error_msg, correlation_id)}

    logger.info('API response',
                extra={'response': response, 'correlation_id': correlation_id, 'event': event, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response
